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

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import json
import os
import random
from typing import Dict, Iterable, List, Optional, Tuple

from .library import WildcardLibrary
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
                 merge_roots: bool = False):
        paths: List[str] = list(extra_paths or [])
        paths.extend(host_paths or [])
        if include_configured:
            paths.extend(configured_paths())
        if include_builtin:
            paths.append(BUILTIN_WILDCARD_DIR)
        self.library = WildcardLibrary(paths, merge_roots=merge_roots)

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
    ) -> Resolution:
        """
        Resolve every wildcard construct in `text`. Never raises on malformed prompts or
        broken wildcard files: problems become warnings and the offending text is kept as is.
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
        resolver = Resolver(
            self.library, seed=seed, mode=mode, index=index, cycle_index=cycle_index,
            legacy=legacy, providers=providers, variables=variables, pick_hook=pick_hook,
        )
        resolution = resolver.resolve_text(text)
        resolution.fresh_roll = fresh_roll
        if cleanup:
            resolution.text = tidy(resolution.text)
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
