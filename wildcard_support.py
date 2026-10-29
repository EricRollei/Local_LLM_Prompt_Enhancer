"""
Wildcard support shared by every enhancer node.

One place for: the two optional inputs every node appends, the seed convention,
the IS_CHANGED rule, the prompt-database provider, and the call into core/wildcards.

Where wildcard packs live (highest priority first; the first folder that has a key wins):
    1. a node's extra_paths input
    2. ComfyUI/models/wildcards                 the shared home for packs - drop them here
    3. any `wildcards:` entry in extra_model_paths.yaml, e.g. A:/Models/wildcards
    4. "wildcard_paths" in this package's config.json
    5. this package's own wildcards/ folder     the lists that ship with the nodes

Inside any of those folders (see core/wildcards/library.py):
    _nsfw/<pack>/...     NSFW lists (explicit), used only when a node's nsfw input is explicit
    _generated/...       lists written by the tools, always searched
    _other/              any other top-level folder starting with "_" is ignored
                         (_duplicates, _quarantine, ...)

Seed convention (wildcard_seed input):
    -1      fresh roll on every run (the node is never cached by ComfyUI)
    >= 0    reproducible: same seed + same wildcard files = same picks

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

import os
import random
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .core.wildcards import NSFW_LEVELS, VIOLENCE_LEVELS, Resolution, WildcardEngine, get_engine, prompt_block_reason

DB_CANDIDATE_LIMIT = 200

WILDCARD_SEED_INPUT = ("INT", {
    "default": -1,
    "min": -1,
    "max": 0x7FFFFFFF,
    "tooltip": (
        "Seed for wildcards: __name__, {a|b|c}, __objects[tag AND tag]__.\n"
        "-1 = fresh roll every run. 0 or more = reproducible picks."
    ),
})

WILDCARD_LLM_BLOCK_INPUT = ("BOOLEAN", {
    "default": True,
    "tooltip": (
        "Tell the LLM which elements were picked at random so it keeps them:\n"
        "concepts keep their meaning, __=verbatim__ picks stay word for word.\n"
        "Off = the LLM only sees the resolved text."
    ),
})


WILDCARD_INSTRUCTIONS_INPUT = ("STRING", {
    "forceInput": True,
    "tooltip": (
        "Connect the llm_instructions output of a Wildcard Processor or Semantic Variation node here\n"
        "when the wildcards were resolved before this node. The LLM is then told which elements were\n"
        "picked at random, and verbatim picks are checked in its answer, exactly as if this node had\n"
        "resolved them itself."
    ),
})


def comfy_wildcard_dirs() -> List[str]:
    """
    ComfyUI's wildcard folders: models/wildcards first, then whatever extra_model_paths.yaml
    registers under `wildcards:`. models/wildcards is registered with folder_paths under the
    name "wildcards" so other tools that ask ComfyUI for that folder find the same place.
    Only folders that exist are returned. Outside ComfyUI this returns [].
    """
    try:
        import folder_paths
    except ImportError:
        return []

    default_dir = os.path.join(folder_paths.models_dir, "wildcards")
    try:
        folder_paths.add_model_folder_path("wildcards", default_dir)
    except Exception:
        pass

    ordered: List[str] = [default_dir]
    try:
        ordered.extend(folder_paths.get_folder_paths("wildcards"))
    except Exception:
        pass

    existing: List[str] = []
    for path in ordered:
        absolute = os.path.abspath(path)
        if os.path.isdir(absolute) and absolute not in existing:
            existing.append(absolute)
    return existing


WILDCARD_NSFW_INPUT = (list(NSFW_LEVELS), {
    "default": NSFW_LEVELS[0],
    "tooltip": (
        "How far wildcard picks may go (a word match on each entry and on list names, no model).\n"
        "off = SFW: no suggestive, nude or explicit lists or entries\n"
        "suggestive = also lingerie, bikinis, sexy, seductive ...\n"
        "nudity = also nude, naked, topless ...\n"
        "explicit = everything, including lists under _nsfw/\n"
        "Fix a wrong rating in _catalog_user.yaml (nsfw: on a list, ratings: on entries). Entries pairing\n"
        "minor-related and sexual terms are removed at every level (config.json \"content_filter\")."
    ),
})

WILDCARD_VIOLENCE_INPUT = (list(VIOLENCE_LEVELS), {
    "default": VIOLENCE_LEVELS[0],
    "tooltip": (
        "Hold back violent wildcard picks (a word match on each entry and on list names, no model).\n"
        "off = nothing held back\n"
        "no gore = blood and gore, torture, mutilation, corpses\n"
        "no gore or violent acts = also murder, execution, stabbing, strangling, suicide ...\n"
        "no violence or weapons = also guns, swords, knives, bombs, battle, war\n"
        "Only wildcard picks are filtered; text you type is left as is."
    ),
})


def wildcard_nsfw_input() -> Dict[str, Any]:
    """
    The nsfw and violence_filter inputs (violence_filter after nsfw). Kept apart from wildcard_optional_inputs() on purpose: nodes append it at the
    very END of their optional section, after anything added since, so saved widget order is unchanged.
    """
    return {"nsfw": WILDCARD_NSFW_INPUT, "violence_filter": WILDCARD_VIOLENCE_INPUT}


CATALOG_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "catalogs")


def get_wildcard_engine(extra_paths: Optional[Iterable[str]] = None) -> WildcardEngine:
    """
    The engine every node uses: node extra paths, then ComfyUI's wildcard folders, config, shipped lists.
    The catalog and the user's curation (_catalog_user.yaml) are attached on first use; the catalog of
    new or changed lists is built in a background thread (config.json "wildcards": {"catalog": false} = off).
    """
    engine = get_engine(extra_paths, host_paths=comfy_wildcard_dirs())
    engine.enable_curation(CATALOG_CACHE_DIR)
    return engine


def wildcard_optional_inputs() -> Dict[str, Any]:
    """The inputs a node appends at the END of its 'optional' section, in this order."""
    return {
        "wildcard_seed": WILDCARD_SEED_INPUT,
        "wildcard_llm_block": WILDCARD_LLM_BLOCK_INPUT,
        "wildcard_instructions": WILDCARD_INSTRUCTIONS_INPUT,
    }


def normalise_seed(wildcard_seed: Optional[int], offset: int = 0) -> Optional[int]:
    """-1 / None -> None (fresh roll). Otherwise seed + offset, so variation N differs from variation 0."""
    if wildcard_seed is None:
        return None
    try:
        value = int(wildcard_seed)
    except (TypeError, ValueError):
        return None
    if value < 0:
        return None
    return value + int(offset)


def is_changed_token(wildcard_seed: Optional[int]) -> Any:
    """
    Value for a node's IS_CHANGED. A fresh-roll seed must defeat ComfyUI's cache, or the
    wildcards would never re-roll while the other inputs stay the same.
    """
    if normalise_seed(wildcard_seed) is None:
        return float(time.time())
    return int(wildcard_seed)


def database_provider(argument: str, text_so_far: str, rng: random.Random) -> Optional[str]:
    """
    __db:query__ -> one prompt from the prompt database matching the FTS query.
    Candidates come back in a stable order and are picked with the run's own RNG, so the
    draw is reproducible for a given seed (SQLite's RANDOM() would not be).
    """
    from .prompt_database import PromptDatabase

    results, _total = PromptDatabase().search(query=argument, limit=DB_CANDIDATE_LIMIT, order_by="oldest")
    texts = [row.get("prompt_text", "").strip() for row in results if row.get("prompt_text")]
    if not texts:
        return None
    return rng.choice(texts)


def resolve_wildcards(text: str, seed: Optional[int] = None, legacy: bool = True,
                      upstream_instructions: str = "", nsfw: str = "off",
                      violence_filter: str = "off") -> Resolution:
    """
    Resolve wildcard syntax in `text`. Never raises: on any failure the text comes back
    unchanged with a warning, so a prompt problem cannot break a workflow.

    upstream_instructions: the llm_instructions text of a Wildcard Processor or Semantic Variation
    node that resolved wildcards earlier in the graph. It travels on the Resolution, so llm_block()
    and enforce_verbatim() treat those picks like this node's own.

    nsfw: the node's nsfw input (NSFW_LEVELS); lists and entries rated above it are left out.
    violence_filter: the node's violence_filter input (VIOLENCE_LEVELS).
    """
    try:
        resolution = get_wildcard_engine().process(
            text or "",
            seed=seed,
            legacy=legacy,
            providers={"db": database_provider},
            nsfw=nsfw,
            violence=violence_filter,
        )
    except Exception as error:  # pragma: no cover - defensive
        resolution = Resolution(text=text or "", seed=seed)
        resolution.warnings.append(f"wildcard engine failed, text passed through: {error}")
    resolution.upstream_instructions = (upstream_instructions or "").strip()
    return resolution


def screen_output(text: str, where: str = "") -> Tuple[str, str]:
    """
    The content filter on a finished prompt that did not come from the wildcard engine (an LLM's
    rewrite). Returns (text, note): ('', why) when it pairs a minor term with an explicit sexual
    term, else (text, ''). Put the note at the top of the node's report (lead_with_filter_notes).
    Off when config.json "wildcards": {"content_filter": false}.
    """
    if not text or not get_wildcard_engine().library.content_filter:
        return text, ""
    reason = prompt_block_reason(text)
    if not reason:
        return text, ""
    note = (f"content filter: {where or 'prompt'} blocked ({reason}); "
            f"set \"content_filter\": false in config.json to turn the filter off")
    print(f"[video_prompter] {note}")
    return "", note


def filter_notes_of(resolution: Optional[Resolution], *extra: str) -> List[str]:
    """What the content and violence filters did in this run: the resolution's filter notes, then `extra`."""
    notes = list(resolution.filter_notes()) if resolution is not None else []
    return notes + [note for note in extra if note]


def lead_with_filter_notes(report: str, notes: Iterable[str]) -> str:
    """The report with one 'FILTER: ...' line per note at the very top (duplicates dropped)."""
    unique = list(dict.fromkeys(note for note in notes if note))
    if not unique:
        return report
    head = "\n".join(f"FILTER: {note}" for note in unique)
    return f"{head}\n{report}" if report else head


def items_from_instructions(instructions: str, heading: str) -> List[str]:
    """The bullet items listed under one heading ('Concepts', 'Verbatim', 'Inspiration') of an llm_instructions block."""
    found: List[str] = []
    inside = False
    for line in (instructions or "").splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            inside = stripped.lower().startswith(heading.lower())
            continue
        if inside:
            value = stripped[2:].strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
            if value and value not in found:
                found.append(value)
    return found


def verbatim_from_instructions(instructions: str) -> List[str]:
    """The quoted strings listed under the 'Verbatim' heading of an llm_instructions block."""
    return items_from_instructions(instructions, "Verbatim")


def concepts_from_instructions(instructions: str) -> List[str]:
    """The phrases listed under the 'Concepts' heading of an llm_instructions block."""
    return items_from_instructions(instructions, "Concepts")


def llm_block(resolution: Optional[Resolution], enabled: bool = True) -> str:
    """The selected-elements instruction block, or '' when disabled or nothing was picked."""
    if not enabled or resolution is None:
        return ""
    blocks = [resolution.format_for_llm(), getattr(resolution, "upstream_instructions", "")]
    return "\n\n".join(block for block in blocks if block)


def enforce_verbatim(text: str, resolution: Optional[Resolution]) -> Tuple[str, List[str]]:
    """
    Survival check for verbatim picks (__=name__, {=a|b}): LoRA triggers and names must be in
    the LLM's output word for word. Any that went missing are appended, the same way the nodes
    already treat missing positive keywords. Returns (text, list of strings that had to be added).
    """
    if resolution is None or not text:
        return text, []
    lowered = text.lower()
    wanted = [slot.value for slot in resolution.slots_by_binding("verbatim")]
    for value in verbatim_from_instructions(getattr(resolution, "upstream_instructions", "")):
        if value not in wanted:
            wanted.append(value)
    missing = [value for value in wanted if value.lower() not in lowered]
    if missing:
        text = f"{text.rstrip()} {', '.join(missing)}"
    return text, missing


def report_lines(resolution: Optional[Resolution]) -> str:
    """Short text for a node's status / breakdown output. '' when no wildcard was used."""
    if resolution is None:
        return ""
    upstream = "Wildcards resolved upstream: instructions received." if getattr(resolution, "upstream_instructions", "") else ""
    if not (resolution.top_level_slots() or resolution.warnings):
        return upstream
    # Filter notes are left out here: nodes put them at the top of their report (lead_with_filter_notes).
    own = "Wildcards: " + "\n".join(line for line in resolution.summary().splitlines() if not line.startswith("FILTER: "))
    return f"{own}\n{upstream}" if upstream else own
