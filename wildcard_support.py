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

from .core.wildcards import Resolution, WildcardEngine, get_engine

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


def get_wildcard_engine(extra_paths: Optional[Iterable[str]] = None) -> WildcardEngine:
    """The engine every node uses: node extra paths, then ComfyUI's wildcard folders, config, shipped lists."""
    return get_engine(extra_paths, host_paths=comfy_wildcard_dirs())


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
                      upstream_instructions: str = "") -> Resolution:
    """
    Resolve wildcard syntax in `text`. Never raises: on any failure the text comes back
    unchanged with a warning, so a prompt problem cannot break a workflow.

    upstream_instructions: the llm_instructions text of a Wildcard Processor or Semantic Variation
    node that resolved wildcards earlier in the graph. It travels on the Resolution, so llm_block()
    and enforce_verbatim() treat those picks like this node's own.
    """
    try:
        resolution = get_wildcard_engine().process(
            text or "",
            seed=seed,
            legacy=legacy,
            providers={"db": database_provider},
        )
    except Exception as error:  # pragma: no cover - defensive
        resolution = Resolution(text=text or "", seed=seed)
        resolution.warnings.append(f"wildcard engine failed, text passed through: {error}")
    resolution.upstream_instructions = (upstream_instructions or "").strip()
    return resolution


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
    own = "Wildcards: " + resolution.summary()
    return f"{own}\n{upstream}" if upstream else own
