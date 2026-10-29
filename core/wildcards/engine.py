"""
WildcardEngine: the one object the nodes talk to.

    engine = get_engine()                              # package wildcards/ + config.json paths
    result = engine.process("a __materials__ {cat|dog}", seed=42)
    result.text               -> final prompt text
    result.slots              -> what was picked, with bindings
    result.format_for_llm()   -> instruction block for the LLM rewriter

Search folders, highest priority first. When a wildcard key exists in several folders,
the first folder that has it wins (see library.py):
    1. extra paths passed by the caller           a node's extra_paths input
    2. host paths                                 ComfyUI's models/wildcards and any
                                                  `wildcards:` entry in extra_model_paths.yaml
                                                  (supplied by wildcard_support.py; the core
                                                  itself knows nothing about ComfyUI)
    3. "wildcard_paths" in <package>/config.json  any other folder of packs
    4. <package>/wildcards/                       lists that ship with the package

Options from config.json (all optional):
    "wildcard_paths": ["D:/more/packs"]         extra search folders (3. above)
    "wildcards": {
        "pool_mode": "scoped",                  "scoped" (default): a bare __name__ never mixes lists of
                                                different packs. "legacy": the old pool-everything lookup.
        "strip_lora": true,                     remove <lora:...> tags from entries at load time
        "content_filter": true,                 drop entries pairing minor words with sexual words
                                                (a word match at load time; false turns it off)
        "catalog": true                         index the lists (catalog.py) and honour the user's
                                                _catalog_user.yaml (curation.py): stars, hidden lists,
                                                dropped entries, content-detected NSFW
    }
Lists and entries rated above a run's nsfw level (library.NSFW_LEVELS) are invisible to process(..., nsfw=...).
See library.py for the folder rules and the content filter.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import json
import os
import random
from typing import Dict, Iterable, List, Optional, Tuple

import threading

from .catalog import CatalogSet
from .curation import Curation
from .library import POOL_MODES, POOL_SCOPED, WildcardLibrary, prompt_block_reason
from .record import Resolution
from .resolver import MODE_RANDOM, PickHook, ProviderCallable, Resolver, tidy

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILTIN_WILDCARD_DIR = os.path.join(PACKAGE_DIR, "wildcards")
CONFIG_PATH = os.path.join(PACKAGE_DIR, "config.json")
_SYSTEM_RANDOM = random.SystemRandom()      # OS entropy; does not read or advance the global random state


def configured_paths() -> List[str]:
    """Extra wildcard folders from config.json -> "wildcard_paths": ["D:/wildcards", ...]."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            paths = json.load(handle).get("wildcard_paths", [])
    except (OSError, ValueError):
        return []
    if isinstance(paths, str):
        paths = [paths]
    return [str(path) for path in paths if path]


def configured_options() -> Dict[str, object]:
    """The "wildcards" section of config.json, with defaults: pool_mode, strip_lora, catalog, content_filter."""
    options: Dict[str, object] = {"pool_mode": POOL_SCOPED, "strip_lora": True, "catalog": True, "content_filter": True}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            section = json.load(handle).get("wildcards", {})
    except (OSError, ValueError):
        return options
    if isinstance(section, dict):
        if section.get("pool_mode") in POOL_MODES:
            options["pool_mode"] = section["pool_mode"]
        if isinstance(section.get("strip_lora"), bool):
            options["strip_lora"] = section["strip_lora"]
        if isinstance(section.get("catalog"), bool):
            options["catalog"] = section["catalog"]
        if isinstance(section.get("content_filter"), bool):
            options["content_filter"] = section["content_filter"]
    return options


def split_paths(raw: str) -> List[str]:
    """Parse a node's extra_paths text: one folder per line, or separated by ';'."""
    parts: List[str] = []
    for line in (raw or "").replace(";", "\n").split("\n"):
        cleaned = line.strip().strip('"')
        if cleaned:
            parts.append(cleaned)
    return parts


class WildcardEngine:
    def __init__(self, extra_paths: Optional[Iterable[str]] = None, include_builtin: bool = True,
                 include_configured: bool = True, host_paths: Optional[Iterable[str]] = None,
                 merge_roots: bool = False, pool_mode: Optional[str] = None,
                 strip_lora: Optional[bool] = None, content_filter: Optional[bool] = None):
        paths: List[str] = list(extra_paths or [])
        paths.extend(host_paths or [])
        if include_configured:
            paths.extend(configured_paths())
        if include_builtin:
            paths.append(BUILTIN_WILDCARD_DIR)
        options = configured_options() if include_configured else {"pool_mode": POOL_SCOPED, "strip_lora": True,
                                                                    "content_filter": True}
        self.library = WildcardLibrary(
            paths, merge_roots=merge_roots,
            pool_mode=pool_mode if pool_mode is not None else str(options["pool_mode"]),
            strip_lora=strip_lora if strip_lora is not None else bool(options["strip_lora"]),
            content_filter=content_filter if content_filter is not None else bool(options.get("content_filter", True)),
        )
        self.catalog = None
        self.curation = None
        self.catalog_enabled = bool(options.get("catalog", True))
        self._catalog_thread: Optional[threading.Thread] = None

    # -- catalog and curation ------------------------------------------------------------
    def enable_curation(self, fallback_dir: str, build_in_background: bool = True) -> None:
        """
        Attach the catalog (catalog.py) and the user's curation (curation.py) to the library.
        Existing catalog files are read at once; new or changed lists are analysed in a background
        thread when build_in_background, else call update_catalog() yourself. Idempotent.
        """
        if self.curation is not None or not self.catalog_enabled:
            return
        builtin = os.path.normcase(os.path.abspath(BUILTIN_WILDCARD_DIR))
        try:
            self.catalog = CatalogSet(
                self.library, fallback_dir,
                in_root_catalog=lambda root: os.path.normcase(os.path.abspath(root)) != builtin,
            )
        except Exception as error:  # no catalog: curation still works from the overlay files
            print(f"[wildcards] catalog unavailable: {error}")
            self.catalog = None
        self.curation = Curation(self.library, self.catalog)
        self.library.curation = self.curation
        if build_in_background and self.catalog is not None:
            self._catalog_thread = threading.Thread(target=self.update_catalog, name="wildcard-catalog", daemon=True)
            self._catalog_thread.start()

    def update_catalog(self) -> Dict:
        if self.catalog is None:
            return {"state": "off"}
        status = self.catalog.update()
        if status.get("state") == "ready" and status.get("changed_files"):
            print(f"[wildcards] catalog: {status['changed_files']} file(s) indexed in {status['seconds']} s")
        elif status.get("state") == "error":
            print(f"[wildcards] catalog update failed: {status.get('error')}")
        return status

    def process(
        self,
        text: str,
        seed: Optional[int] = None,
        mode: str = MODE_RANDOM,
        index: int = 0,
        cycle_index: int = 0,
        legacy: bool = False,
        providers: Optional[Dict[str, ProviderCallable]] = None,
        variables: Optional[Dict[str, str]] = None,
        cleanup: bool = True,
        pick_hook: Optional[PickHook] = None,
        nsfw="off",
        violence=0,
    ) -> Resolution:
        """
        Resolve every wildcard construct in `text`. Never raises on malformed prompts or
        broken wildcard files: problems become warnings and the offending text is kept as is.
        nsfw: the run's level (library.NSFW_LEVELS name or 0-3): lists and entries rated above it are left out;
            a reference with nothing left at that level is dropped (the report says so).
        violence: the node's violence_filter (library.VIOLENCE_LEVELS name or 0-3); entries in that
            tier or a lower one are skipped.
        With the content filter on, a result that pairs a minor term with an explicit sexual term
        (library.prompt_block_reason) is re-rolled with derived seeds when the picks caused it, and
        blanked (resolution.blocked says why) when the typed text did or no re-roll passes.
        """
        if not text:
            return Resolution(text=text or "", seed=seed, mode=mode)

        # No seed given = a fresh roll. The engine draws the seed itself (from the OS, never from the
        # global `random` module) and records it, so a roll you like can be repeated by typing it in.
        fresh_roll = seed is None
        if fresh_roll:
            seed = _SYSTEM_RANDOM.randrange(0, 0x7FFFFFFF)

        self.library.warnings = []
        self.library.refresh()

        def run(run_seed: int) -> Resolution:
            resolver = Resolver(
                self.library, seed=run_seed, mode=mode, index=index, cycle_index=cycle_index,
                legacy=legacy, providers=providers, variables=variables, pick_hook=pick_hook,
                nsfw=nsfw, violence=violence,
            )
            result = resolver.resolve_text(text)
            result.fresh_roll = fresh_roll
            if cleanup:
                result.text = tidy(result.text)
            return result

        resolution = run(seed)
        if not self.library.content_filter:
            return resolution
        reason = prompt_block_reason(resolution.text)
        if not reason:
            return resolution
        if not prompt_block_reason(text):              # the picks made it, not the typed text: re-roll
            for attempt in range(1, CONTENT_REROLLS + 1):
                retry = run((seed + attempt * 7919) % 0x7FFFFFFF)
                if not prompt_block_reason(retry.text):
                    retry.warnings.append(f"content filter: seed {seed} picked {reason}; re-rolled to seed {retry.seed}")
                    return retry
        return blocked_resolution(resolution, reason)


CONTENT_REROLLS = 6      # derived seeds tried before a prompt the content filter fails is blanked


def blocked_resolution(resolution: Resolution, reason: str) -> Resolution:
    """The prompt blanked by the content filter: empty text, the reason in .blocked and in the warnings."""
    resolution.text = ""
    resolution.blocked = reason
    resolution.warnings.append(f"content filter: prompt blocked ({reason}); set \"content_filter\": false "
                               f"in config.json to turn the filter off")
    return resolution


_ENGINES: Dict[Tuple[str, ...], WildcardEngine] = {}


def get_engine(extra_paths: Optional[Iterable[str]] = None,
               host_paths: Optional[Iterable[str]] = None) -> WildcardEngine:
    """Shared engine per set of paths, so file caches survive between node executions."""
    extra = tuple(os.path.abspath(path) for path in (extra_paths or []))
    host = tuple(os.path.abspath(path) for path in (host_paths or []))
    key = extra + ("|",) + host
    engine = _ENGINES.get(key)
    if engine is None:
        engine = WildcardEngine(extra_paths=list(extra), host_paths=list(host))
        _ENGINES[key] = engine
    return engine
