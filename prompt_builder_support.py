"""
Prompt builders inside ComfyUI: builder definitions, the node base class, and the HTTP routes the
composer widget (web/prompt_builder.js) talks to.

Builder definitions (see core/builder/slots.py for the format):
    <package>/builders/*.yaml         shipped (character.yaml)
    <package>/builders_user/*.yaml    yours; a file with the same id replaces the shipped one
    <package>/builders_user/my_buttons.yaml   your own buttons ("+ Button" / Find ☆), shared by all builders
    <package>/builders_user/templates/*.json  your saved templates (a whole composer), shared by all builders
    <package>/builders/templates/*.json        shipped starter templates (read-only), offered alongside yours

Routes, all GET except preview (nsfw=off|suggestive|nudity|explicit is the node's nsfw level;
violence=0-3 is the node's violence_filter level on starter, slot, slot_counts, find, more and preview):
    /eric_prompt_builder/builders                          builder definitions for the widget
    /eric_prompt_builder/starter?builder=character         a starter composer state, lists filled in
    /eric_prompt_builder/slot?builder=&slot=&nsfw=         the lists behind one slot button
    /eric_prompt_builder/list?key=&q=&offset=&limit=&nsfw= the entries of one list
    /eric_prompt_builder/platforms                         platform ids and their section order
    /eric_prompt_builder/find?q=&nsfw=&gender=&names=      lists for the Find box (names=1: key words only,
                                                           what a category button would use)
    POST /eric_prompt_builder/buttons                      {action: save|delete, button|id} -> my_buttons.yaml
    /eric_prompt_builder/templates                         your saved templates (name, builder, sections, ...)
    /eric_prompt_builder/template?file=&nsfw=              one template, plus the list keys this library lacks
    POST /eric_prompt_builder/templates                    {action: save|delete, name|file, builder, platform, composer}
    /eric_prompt_builder/more?builder=&sections=&nsfw=     usable lists no button offers, grouped by path words
    POST /eric_prompt_builder/merge/preview                {builder, slot, keys, nsfw} -> folded rows, most-shared first
    POST /eric_prompt_builder/merge/save                   {builder, slot, name, entries, sources, hide_sources,
                                                           overwrite, nsfw} -> <root>/mine/<slot>/<name>.txt
    POST /eric_prompt_builder/preview                      {builder, composer, seed, platform, nsfw, violence}
                                                           -> what the node would output for that seed

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

import asyncio
import json
import os
import re
import threading
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple

from .core.builder import (DEFAULT_ORDER, LAYOUT_FILE, OPTIONAL_SECTIONS, kinds_of, layout_hide, layout_move, read_layout,
                           write_layout, more_lists, merge_entries, merged_key, merged_path, pick_root, slot_words, write_merged,
                           MY_BUTTONS_FILE, SECTION_LABELS, SECTIONS, BuilderDef, ComposerState, PromptSections,
                           SlotMatcher, button_id, clean_button, join_sections, load_builders, order_sections,
                           read_buttons, section_label, section_order, section_seed_offset, write_buttons)
from .profile_support import get_profile, profile_ids
from .core.wildcards import NSFW_LEVELS, nsfw_level, prompt_block_reason, violence_level
from .core.wildcards.record import is_filter_note
from .wildcard_support import WILDCARD_NSFW_INPUT, WILDCARD_VIOLENCE_INPUT, get_wildcard_engine
from .core.wildcards.library import nsfw_folder_tier, strip_nsfw_prefix

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILDER_DIRS = [os.path.join(PACKAGE_DIR, "builders"), os.path.join(PACKAGE_DIR, "builders_user")]
MY_BUTTONS_PATH = os.path.join(PACKAGE_DIR, "builders_user", MY_BUTTONS_FILE)
LAYOUT_PATH = os.path.join(PACKAGE_DIR, "builders_user", LAYOUT_FILE)
SCENE_ONLY_NOTE = ("NO SUBJECT - the user chose a scene only (a landscape, an empty set or plate). "
                   "Do not add a person, animal or other main subject.")
TEMPLATES_DIR = os.path.join(PACKAGE_DIR, "builders_user", "templates")
SHIPPED_TEMPLATES_DIR = os.path.join(PACKAGE_DIR, "builders", "templates")
STARTER_PREFIX = "starter:"   # marks a read-only shipped starter in the file id the widget sends back
_TEMPLATE_FILE = re.compile(r"[^a-z0-9_\-]+")
GENERIC_PLATFORM = "generic"
DEFAULT_PLATFORM = "krea2"
ROUTE = "/eric_prompt_builder"
LIST_PAGE_MAX = 500
_STARTER_SLOT = re.compile(r"\{([a-z0-9_]+)\}")
# "auburn hair" + typed "hair" -> "auburn hair hair": a doubled word of 3+ letters is collapsed.
_DOUBLED_WORD = re.compile(r"\b([A-Za-z]{3,})(\s+\1\b)+", re.IGNORECASE)
# Booru-style entries (arms_behind_back) read as words in a phrase.
_TAG_UNDERSCORE = re.compile(r"(?<=[A-Za-z])_(?=[A-Za-z])")

_builders_cache: Tuple[float, Dict[str, BuilderDef]] = (-1.0, {})
_matchers: Dict[int, SlotMatcher] = {}
_ROUTE_LOCK = threading.Lock()      # route work runs in a thread pool; one at a time over the shared library


# ----------------------------------------------------------------------------- definitions
def _builder_dirs_mtime() -> float:
    newest = 0.0
    for folder in BUILDER_DIRS:
        if os.path.isdir(folder):
            newest = max(newest, os.path.getmtime(folder))
            for name in os.listdir(folder):
                if name.lower().endswith((".yaml", ".yml")):
                    newest = max(newest, os.path.getmtime(os.path.join(folder, name)))
    return newest


def get_builders() -> Dict[str, BuilderDef]:
    """All builder definitions, re-read when a YAML file changes."""
    global _builders_cache
    stamp = _builder_dirs_mtime()
    if stamp != _builders_cache[0]:
        _builders_cache = (stamp, load_builders(BUILDER_DIRS, MY_BUTTONS_PATH, LAYOUT_PATH))
        for matcher in _matchers.values():   # a button edited in place keeps its id; drop its old lists
            matcher.clear()
    return _builders_cache[1]


def get_builder(builder_id: str) -> Optional[BuilderDef]:
    return get_builders().get(builder_id)


def get_matcher() -> SlotMatcher:
    library = get_wildcard_engine().library
    matcher = _matchers.get(id(library))
    if matcher is None:
        matcher = SlotMatcher(library)
        _matchers[id(library)] = matcher
    return matcher


def platform_choices() -> List[str]:
    return [GENERIC_PLATFORM] + profile_ids(("image", "video"))


def platform_order(platform: str) -> List[str]:
    if not platform or platform == GENERIC_PLATFORM:
        return list(DEFAULT_ORDER)
    profile = get_profile(platform)
    return section_order(profile.structure if profile else "")


def node_order(own: List[str], platform: str) -> List[str]:
    """The node's own section order (dragged in the panel) first, then the platform's for the rest."""
    base = platform_order(platform)
    own = [section for section in (own or []) if section in SECTIONS]
    return own + [section for section in base if section not in own]


# ----------------------------------------------------------------------------- composer state
def starter_state(builder: BuilderDef, nsfw="off", violence: int = 0) -> Dict[str, Any]:
    """Composer state from each part's `starter` line; each {slot} gets that slot's first list."""
    matcher = get_matcher()
    tokens: Dict[str, Dict[str, Any]] = {}
    parts: Dict[str, List[Dict[str, Any]]] = {}
    next_id = 1
    for part in builder.parts:
        if part.optional:
            continue                      # Text and other optional sections start absent ("+ Section")
        segments: List[Dict[str, Any]] = []
        position = 0
        for match in _STARTER_SLOT.finditer(part.starter):
            slot = builder.slot(match.group(1))
            if slot is None:
                continue
            segments.append({"t": "text", "v": part.starter[position:match.start()].strip()})
            lists = matcher.lists_for(builder, slot, nsfw, violence=violence)
            tokens[str(next_id)] = {"slot": slot.id, "key": lists[0].key if lists else "", "mode": "random",
                                    "picks": [], "count": 1, "keep": "meaning"}
            segments.append({"t": "tok", "id": next_id})
            next_id += 1
            position = match.end()
        segments.append({"t": "text", "v": part.starter[position:].strip()})
        parts[part.section] = segments
    return {"v": 1, "parts": parts, "tokens": tokens, "next": next_id, "locks": {}, "fill": {}}


FILL_HEADING = "SECTIONS TO WRITE"


def fill_block(builder: BuilderDef, sections: List[str]) -> str:
    """Instruction for the LLM rewriter: write the sections the user left empty on purpose."""
    if not sections:
        return ""
    lines = [f"{FILL_HEADING} - the user left these for you. Write each in a few words that suit the rest of the prompt:"]
    for section in sections:
        part = builder.part(section)
        hint = part.hint if part and part.hint else section_label(section).lower()
        lines.append(f"  * {section_label(section)}: {hint}")
    return "\n".join(lines)


CONTENT_REROLLS = 6      # seeds tried when the whole assembled prompt fails the content filter


def build(builder: BuilderDef, composer: str, seed: int, platform: str, nsfw,
          upstream: Any = None, violence: int = 0) -> Dict[str, Any]:
    """
    What a builder node outputs. Shared by the node and the preview route, so the preview is
    exactly what a run with the same seed gives.

    violence: the node's violence_filter level (0-3); picks in that tier or a lower one are skipped.
    Content filter (config.json "content_filter", on by default): each section is checked by the
    engine, and the assembled text here, since a minor term and an explicit term can come from
    different sections. A failing roll is re-rolled with derived seeds when the picks caused it, and
    blanked (report says why) when the typed text did or no re-roll passes.
    """
    result = _build_once(builder, composer, seed, platform, nsfw, upstream, violence)
    if not get_wildcard_engine().library.content_filter:
        return result
    reason = prompt_block_reason(result["text"])
    if not reason:
        return result
    if not prompt_block_reason(result["template"]):
        for attempt in range(1, CONTENT_REROLLS + 1):
            retry = _build_once(builder, composer, (int(seed) + attempt * 7919) % 0x7FFFFFFF, platform,
                                nsfw, upstream, violence)
            if not prompt_block_reason(retry["text"]):
                note = f"content filter: seed {seed} picked {reason}; re-rolled to seed {retry['seed']}"
                retry["warnings"].append(note)
                retry["report"] = f"FILTER: {note}\n" + retry["report"]
                return retry
    note = (f"content filter: prompt blocked ({reason}); set \"content_filter\": false in config.json "
            f"to turn the filter off")
    result.update({"bundle": PromptSections.coerce(upstream), "text": "", "llm_instructions": "",
                   "own_sections": {}, "picks": {}, "blocked": reason})
    result["warnings"].append(note)
    result["report"] = f"FILTER: {note}\n" + result["report"]
    return result


def _build_once(builder: BuilderDef, composer: str, seed: int, platform: str, nsfw,
                upstream: Any = None, violence: int = 0) -> Dict[str, Any]:
    """One roll of build(): each section from seed + its offset, or from the seed it is locked at."""
    if not (composer or "").strip():
        composer = json.dumps(starter_state(builder, nsfw, violence))
    state = ComposerState.from_json(composer)
    templates = state.templates()
    scene_sections = [section for section in state.parts if state.scene_only(section)]
    for section in scene_sections:
        templates.pop(section, None)       # Scene only: the subject is left out on purpose
    engine = get_wildcard_engine()

    resolved: Dict[str, str] = {}
    warnings: List[str] = list(state.errors)
    instruction_blocks: List[str] = []
    picks: Dict[str, str] = {}
    summaries: List[str] = []
    seeds: Dict[str, int] = {}
    token_syntax = {token_id: token.syntax() for token_id, token in state.tokens.items()}
    all_sections = list(dict.fromkeys(list(state.parts) + list(templates)))
    for section in all_sections:
        seeds[section] = state.locks.get(section, int(seed) + section_seed_offset(section))
    for section in order_sections(templates, SECTIONS):
        resolution = engine.process(templates[section], seed=seeds[section], legacy=False, nsfw=nsfw,
                                    violence=violence)
        resolved[section] = _DOUBLED_WORD.sub(r"\1", _TAG_UNDERSCORE.sub(" ", resolution.text.strip()))
        warnings.extend(f"{section_label(section)}: {warning}" for warning in resolution.warnings)
        block = resolution.format_for_llm()
        if block:
            instruction_blocks.append(block)
        locked = " (locked)" if section in state.locks else ""
        summary = "\n".join(line for line in resolution.summary().splitlines() if not line.startswith("FILTER: "))
        summaries.append(f"{section_label(section)}{locked}: {summary}")
        for slot in resolution.top_level_slots():
            for token_id, syntax in token_syntax.items():
                if syntax and slot.source == syntax and token_id not in picks:
                    picks[token_id] = slot.value
                    break

    order = node_order(state.order, platform)
    to_fill = [section for section in order_sections(state.fill, order)
               if state.fill.get(section) and not resolved.get(section, "").strip() and section not in scene_sections]
    block = fill_block(builder, to_fill)
    if block:
        instruction_blocks.append(block)
    if scene_sections:
        instruction_blocks.append(SCENE_ONLY_NOTE)
        summaries.append("Scene only: no subject")
        summaries.append("Left for the LLM to write: " + ", ".join(section_label(s) for s in to_fill)
                         + " (connect llm_instructions to the rewriter's wildcard_instructions)")

    bundle = PromptSections.coerce(upstream).merged_with(
        resolved, templates, "\n\n".join(instruction_blocks), builder.label, nsfw=nsfw_level(nsfw))
    return {
        "bundle": bundle,
        "text": join_sections(bundle.sections, order),
        "template": join_sections(bundle.templates, order),
        "llm_instructions": bundle.instructions_text(),
        "own_sections": resolved,
        "own_templates": templates,
        "picks": picks,
        "seeds": seeds,
        "to_fill": to_fill,
        "warnings": warnings,
        "order": order,
        "report": "\n".join([f"FILTER: {w}" for w in warnings if is_filter_note(w)] + summaries
                             + [f"warning: {w}" for w in warnings
                                if not is_filter_note(w) and not any(w in s for s in summaries)]),
        "seed": int(seed),
        "blocked": "",
    }


# ----------------------------------------------------------------------------- node base
class PromptBuilderNode:
    """
    Base for builder nodes. A subclass sets BUILDER_ID; the widget and the slot lists come from
    builders/<BUILDER_ID>.yaml. The composer widget is drawn by web/prompt_builder.js and saved
    as JSON in the `composer` input.
    """
    BUILDER_ID = ""
    CATEGORY = "Eric Prompt Enhancers/Wildcard Composers"
    FUNCTION = "run"
    RETURN_TYPES = ("PROMPT_SECTIONS", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("sections", "text", "llm_instructions", "template", "report")
    OUTPUT_TOOLTIPS = (
        "Every section filled so far (this builder and the ones before it). Connect to the next builder.",
        "All sections as one prompt, in the platform's order. Connect to a Platform Prompt Rewriter's idea for LLM polish, or use as is.",
        "Which picks were random and how to keep them (Meaning / Exact / Loose). Connect to the rewriter's wildcard_instructions.",
        "The same prompt as wildcard syntax, unresolved. Useful to save, or to let another node roll it.",
        "What was picked, and any warnings.",
    )

    @classmethod
    def INPUT_TYPES(cls):
        choices = platform_choices()
        default_platform = DEFAULT_PLATFORM if DEFAULT_PLATFORM in choices else GENERIC_PLATFORM
        return {
            "required": {
                "composer": ("STRING", {
                    "default": "", "multiline": False, "eric_builder": cls.BUILDER_ID,
                    "tooltip": "Composer state (JSON), edited with the builder panel on the node. Empty = the starter phrase.",
                }),
                "platform": (choices, {
                    "default": default_platform,
                    "tooltip": "Target model. Sets the order sections are joined in the `text` output (from the profile's structure line).",
                }),
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 0x7FFFFFFF, "control_after_generate": True,
                    "tooltip": "Same seed + same composer + same wildcard files = same picks.",
                }),
            },
            "optional": {
                "sections": ("PROMPT_SECTIONS", {
                    "tooltip": "Sections from a builder earlier in the chain. This builder adds its own to them.",
                }),
                # New inputs are only ever APPENDED below this line, so saved workflows keep their widget order.
                "nsfw": WILDCARD_NSFW_INPUT,
                "violence_filter": WILDCARD_VIOLENCE_INPUT,
            },
        }

    def run(self, composer: str, platform: str, seed: int, sections: Any = None, nsfw="off",
            violence_filter: str = "off"):
        builder = get_builder(self.BUILDER_ID)
        if builder is None:
            message = f"builder definition '{self.BUILDER_ID}' not found in {BUILDER_DIRS}"
            return (PromptSections.coerce(sections), "", "", "", message)
        try:
            result = build(builder, composer, seed, platform, nsfw, upstream=sections,
                           violence=violence_level(violence_filter))
        except Exception as error:  # never break the graph over a prompt
            traceback.print_exc()
            return (PromptSections.coerce(sections), "", "", "", f"{builder.label} error: {error}")
        print(f"[{builder.label}] {result['text'][:120]}")
        return (result["bundle"], result["text"], result["llm_instructions"], result["template"], result["report"])


# ----------------------------------------------------------------------------- routes
def _flag(value: Optional[str]) -> bool:
    return str(value or "").lower() in ("1", "true", "yes", "on")


def _level(value: Any) -> int:
    """An nsfw level from a query string or JSON body (a NSFW_LEVELS name, or 0-3)."""
    return nsfw_level(value)


def _violence(value: Any) -> int:
    """A violence level from a query string or JSON body (0-3, or a VIOLENCE_LEVELS name)."""
    return violence_level(value)


def _builder_payload(builder: BuilderDef) -> Dict[str, Any]:
    return {
        "id": builder.id,
        "label": builder.label,
        "description": builder.description,
        "parts": [{"section": part.section, "label": part.label, "slots": part.slot_sections,
                   "multi": part.multi, "hint": part.hint, "optional": part.optional} for part in builder.parts],
        "slots": [{"id": slot.id, "label": slot.label, "tooltip": slot.tooltip, "section": slot.section,
                   "group": slot.group, "custom": slot.custom, "lists": slot.lists if slot.custom else [],
                   "search": slot.search if slot.custom else "", "kinds": kinds_of(slot), "hidden": slot.hidden}
                  for slot in builder.slots],
    }


def _list_payload(info) -> Dict[str, Any]:
    return {"key": info.key, "count": info.count, "pinned": info.pinned, "also": info.also[:8],
            "length": info.length_class, "quality": info.quality, "stars": info.stars,
            "dialect": info.dialect, "display": info.display, "nsfw": info.nsfw, "gender": info.gender}


def _entry_payload(library, curation, key: str, entry, dropped, level: int, folder: bool = False) -> Dict[str, Any]:
    """
    One entry for the list viewer: its rating, whether you set it, and whether this level leaves it out.
    folder: the viewer shows a whole folder of lists; the entry's own list decides drops and ratings ("list").
    """
    source = strip_nsfw_prefix(entry.key) if entry.key else key
    if folder:
        key = source
        dropped = curation.dropped(source) if curation is not None else set()
    rating = library.entry_rating(entry)
    override = curation.entry_rating(key, entry.text) if curation is not None else None
    return {"text": entry.text, "weight": entry.weight, "dropped": entry.text.strip().casefold() in dropped,
            "rating": rating, "rated_by_you": override is not None, "above": rating > level, "list": source}


PROMPTS_ROOT = "prompts"          # the name the _prompts/ folder answers to (core/wildcards/library.py)
PROMPT_BROWSE_MAX = 400           # files listed per folder (counting a file's prompts loads it)
PROMPT_SEARCH_MAX = 200


def prompt_browse(folder: str = PROMPTS_ROOT, query: str = "", nsfw="off") -> Dict[str, Any]:
    """
    The Prompt line's browser over _prompts/: one folder's subfolders (with how many files are under each) and
    files (with their prompt counts), or with `query` the files whose path has every word, from any folder.
    """
    library = get_wildcard_engine().library
    names = library.prompt_names(nsfw)

    def row(name: str, shown: str) -> Dict[str, Any]:
        return {"key": name, "name": shown, "count": len(library.entries_of(name, nsfw)),
                "nsfw": library.list_rating(name)}

    words = [word for word in (query or "").lower().split() if word]
    if words:
        found = [name for name in names if all(word in name for word in words)]
        return {"folder": PROMPTS_ROOT, "query": query, "here": len(found), "folders": [],
                "lists": [row(name, name[len(PROMPTS_ROOT) + 1:]) for name in found[:PROMPT_SEARCH_MAX]],
                "more": max(0, len(found) - PROMPT_SEARCH_MAX)}
    prefix = (folder or PROMPTS_ROOT).strip().strip("/").lower().replace("\\", "/")
    if prefix != PROMPTS_ROOT and not prefix.startswith(PROMPTS_ROOT + "/"):
        prefix = PROMPTS_ROOT
    start = prefix + "/"
    folders: Dict[str, int] = {}
    direct: List[str] = []
    here = 0
    for name in names:
        if not name.startswith(start):
            continue
        here += 1
        rest = name[len(start):]
        if "/" in rest:
            first = rest.split("/", 1)[0]
            folders[first] = folders.get(first, 0) + 1
        else:
            direct.append(name)
    return {"folder": prefix, "query": "", "here": here,
            "folders": [{"key": start + name, "name": name, "lists": count} for name, count in sorted(folders.items())],
            "lists": [row(name, name[len(start):]) for name in direct[:PROMPT_BROWSE_MAX]],
            "more": max(0, len(direct) - PROMPT_BROWSE_MAX)}


FIND_LIMIT_MAX = 400              # lists one Find returns (the slot matcher reads at most FIND_MAX_CANDIDATES)


def find_lists(query: str, nsfw="off", gender: str = "", names_only: bool = False,
               limit: int = 40, violence: int = 0) -> List[Any]:
    """The Find box: lists whose key has every word, then (unless names_only) the catalog's hits on entries."""
    engine = get_wildcard_engine()
    also: List[str] = []
    if not names_only and engine.catalog is not None:
        try:
            # Every word must be there (in the name, a sample entry or the facet): an any-word
            # fallback floods the box with lists that merely contain "female".
            also = [row.key for row in engine.catalog.search(query, 120, any_word=False)]
        except Exception as error:   # the catalog is a bonus here
            print(f"[Wildcard Composer] catalog search skipped: {error}")
    return get_matcher().find(query, nsfw, gender, also=also, limit=limit, violence=violence)


def save_button(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Add or replace one of your buttons in my_buttons.yaml. Returns the saved button."""
    button = clean_button(raw)
    if button is None:
        raise ValueError("a button needs a label and a list or search words")
    if button["section"] not in SECTIONS:
        raise ValueError(f"unknown section '{button['section']}'")
    buttons = read_buttons(MY_BUTTONS_PATH)
    builtin = {slot.id for builder in get_builders().values() for slot in builder.slots if not slot.custom}
    if button["id"] and not button["id"].startswith("my_"):
        button["id"] = ""
    at = next((i for i, b in enumerate(buttons) if b["id"] == button["id"]), -1) if button["id"] else -1
    if at >= 0:
        buttons[at] = button
    else:
        button["id"] = button_id(button["label"], builtin | {b["id"] for b in buttons})
        buttons.append(button)
    write_buttons(MY_BUTTONS_PATH, buttons)
    return button


def delete_button(button_key: str) -> bool:
    buttons = read_buttons(MY_BUTTONS_PATH)
    kept = [b for b in buttons if b["id"] != button_key]
    if len(kept) == len(buttons):
        return False
    write_buttons(MY_BUTTONS_PATH, kept)
    return True


# ----------------------------------------------------------------------------- more lists
MORE_MAX_LISTS = 300


def more_payload(builder_id: str, sections: List[str], nsfw="off", violence: int = 0) -> Dict[str, Any]:
    """The usable lists no button of the builder offers, for these sections, grouped by path words."""
    from .core.builder.slots import gender_of
    builder = get_builder(builder_id)
    if builder is None:
        raise ValueError("unknown builder")
    engine = get_wildcard_engine()
    if engine.catalog is None:
        return {"groups": [], "total": 0, "note": "the wildcard catalog is off (config.json wildcards.catalog)"}
    matcher = get_matcher()
    unassigned = matcher.unassigned(builder, nsfw, violence)
    def row_of(key: str):
        # An _nsfw/ list answers to its name without the prefix; the catalog keeps the real key.
        return engine.catalog.row(key) or next(
            (row for row in (engine.catalog.row(real) for real in engine.library.real_keys(key)) if row is not None), None)

    result = more_lists(unassigned, [s for s in sections if s in SECTIONS or s == "_unsorted"], row_of)

    def payload(key: str) -> Dict[str, Any]:
        row = result["rows"][key]
        words = getattr(row, "median_words", 0) or 0
        return {"key": key, "count": row.entries, "display": row.display, "quality": row.quality,
                "dialect": row.dialect, "length": "short" if words <= 4 else "medium" if words <= 8 else "long",
                "nsfw": engine.library.list_rating(key), "gender": gender_of(key), "stars": 0}

    return {
        "total": result["total"], "unsorted": result["unsorted"], "skipped": result["skipped"],
        "groups": [{"word": g.word, "label": g.label, "count": len(g.keys),
                    "lists": [payload(k) for k in g.keys[:MORE_MAX_LISTS]]} for g in result["groups"]],
    }


# ----------------------------------------------------------------------------- merging lists
MERGE_MAX_LISTS = 300


def _slot_or_error(builder_id: str, slot_id: str):
    builder = get_builder(builder_id)
    slot = builder.slot(slot_id) if builder else None
    if slot is None:
        raise ValueError("unknown builder or slot")
    return builder, slot


def merge_preview(builder_id: str, slot_id: str, keys: List[str], nsfw="off") -> Dict[str, Any]:
    """The chosen lists folded into one: rows most-shared first, with counts for the dialog."""
    _builder, slot = _slot_or_error(builder_id, slot_id)
    keys = [str(key).strip().lower() for key in keys if str(key).strip()][:MERGE_MAX_LISTS]
    library = get_wildcard_engine().library
    texts = [[entry.text for entry in library.entries_of(key, nsfw=nsfw)] for key in keys]
    rows = merge_entries(texts, slot_words(slot.label, slot.id))
    return {
        "keys": keys,
        "entries": sum(len(t) for t in texts),
        "sizes": [len(t) for t in texts],
        "rows": [row.to_dict() for row in rows],
        "shared": sum(1 for row in rows if row.lists >= 2),
    }


def merge_save(builder_id: str, slot_id: str, name: str, entries: List[str], sources: List[str],
               hide_sources: bool = False, overwrite: bool = False) -> Dict[str, Any]:
    """Save a merged list under mine/<slot>/ in the folder most sources come from; optionally hide the sources."""
    _builder, slot = _slot_or_error(builder_id, slot_id)
    engine = get_wildcard_engine()
    library = engine.library
    key_roots: Dict[str, str] = {}
    for root, files in library.catalog_sources().items():
        for _relative, (_path, keys) in files.items():
            for key in keys:
                key_roots.setdefault(key, root)
    roots = [next((key_roots[real] for real in [key] + library.real_keys(key) if real in key_roots), None)
             for key in sources]
    shipped = os.path.join(PACKAGE_DIR, "wildcards")
    root = pick_root(roots, library.search_paths, avoid=shipped)
    if root is None:
        raise ValueError("no wildcard folder to save into")
    path = merged_path(root, slot.id, name)
    count = write_merged(path, entries, sources, slot.label, overwrite=overwrite)
    library.refresh(force=True)
    hidden = []
    curation = library.curation
    if hide_sources and curation is not None:
        for key in sources:
            try:
                curation.update(key, hidden=True)
                hidden.append(key)
            except Exception as error:   # a key the curation can't place: leave it visible
                print(f"[Wildcard Composer] could not hide {key}: {error}")
    get_matcher().clear()
    return {"key": merged_key(slot.id, name), "path": path, "count": count, "hidden": hidden}


# ----------------------------------------------------------------------------- templates
def template_file(name: str) -> str:
    """'Noir portrait #2' -> 'noir_portrait_2.json' (letters, digits, _ and - only)."""
    slug = _TEMPLATE_FILE.sub("_", (name or "").strip().lower()).strip("_-")[:80]
    if not slug:
        raise ValueError("a template needs a name")
    return slug + ".json"


def _template_path(file_name: str) -> str:
    if not file_name or os.path.basename(file_name) != file_name or not file_name.endswith(".json"):
        raise ValueError(f"bad template file '{file_name}'")
    return os.path.join(TEMPLATES_DIR, file_name)


def _shipped_template_path(file_name: str) -> str:
    if not file_name or os.path.basename(file_name) != file_name or not file_name.endswith(".json"):
        raise ValueError(f"bad template file '{file_name}'")
    return os.path.join(SHIPPED_TEMPLATES_DIR, file_name)


def _template_summary(file_name: str, data: Dict[str, Any], starter: bool = False) -> Dict[str, Any]:
    composer = data.get("composer") or {}
    parts = composer.get("parts") or {}
    used = [section for section, segs in parts.items()
            if any(seg.get("t") == "tok" or str(seg.get("v", "")).strip() for seg in segs or [])]
    return {"file": (STARTER_PREFIX + file_name) if starter else file_name,
            "name": data.get("name") or file_name[:-5], "builder": data.get("builder", ""),
            "platform": data.get("platform", ""), "saved": data.get("saved", ""), "sections": used,
            "pills": len(composer.get("tokens") or {}), "starter": starter}


def list_templates() -> List[Dict[str, Any]]:
    """Every saved template and shipped starter, your own first, then the starters."""
    found = []
    for folder, starter in ((TEMPLATES_DIR, False), (SHIPPED_TEMPLATES_DIR, True)):
        if not os.path.isdir(folder):
            continue
        for file_name in sorted(os.listdir(folder)):
            if not file_name.endswith(".json"):
                continue
            try:
                with open(os.path.join(folder, file_name), "r", encoding="utf-8") as handle:
                    found.append(_template_summary(file_name, json.load(handle), starter))
            except Exception as error:   # one broken file must not hide the others
                print(f"[Wildcard Composer] skipped template {file_name}: {error}")
    return sorted(found, key=lambda item: (item["starter"], item["name"].casefold()))


def read_template(file_name: str, nsfw="off") -> Dict[str, Any]:
    """A saved template, and which of its lists this library doesn't have (those pills show red)."""
    starter = file_name.startswith(STARTER_PREFIX)
    base = file_name[len(STARTER_PREFIX):] if starter else file_name
    path = _shipped_template_path(base) if starter else _template_path(base)
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    composer = data.get("composer") or {}
    keys = {str(token.get("key", "")).strip().lower() for token in (composer.get("tokens") or {}).values()
            if isinstance(token, dict) and token.get("key")}
    known = set(get_wildcard_engine().library.visible_keys(nsfw, include_prompts=True)) if keys else set()
    return dict(data, file=file_name, missing=sorted(keys - known), starter=starter)


def save_template(name: str, builder_id: str, composer: Any, platform: str = "", overwrite: bool = False) -> Dict[str, Any]:
    """
    Save a whole composer as builders_user/templates/<name>.json. Locks are left out (a template
    loads free to re-roll); everything else is kept: text, pills with their lists, modes, picks,
    counts and keep, extra subjects, the Woman / Man choice, LLM fills, and the platform.
    """
    if isinstance(composer, str):
        composer = json.loads(composer or "{}")
    if not isinstance(composer, dict) or not isinstance(composer.get("parts"), dict):
        raise ValueError("nothing to save: the composer is empty")
    file_name = template_file(name)
    path = _template_path(file_name)
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(f"a template called '{name}' already exists")
    state = {k: v for k, v in composer.items() if k not in ("locks", "template")}
    state["locks"] = {}
    data = {"v": 1, "name": name.strip(), "builder": builder_id, "platform": platform,
            "saved": time.strftime("%Y-%m-%d %H:%M"), "composer": state}
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1, ensure_ascii=False)
    os.replace(temp, path)
    return _template_summary(file_name, data)


def delete_template(file_name: str) -> bool:
    if file_name.startswith(STARTER_PREFIX):
        raise ValueError("starter templates are read-only")
    path = _template_path(file_name)
    if not os.path.exists(path):
        return False
    os.remove(path)
    return True


def register_routes() -> bool:
    """Attach the routes to ComfyUI's server. Returns False outside ComfyUI."""
    try:
        from aiohttp import web
        from server import PromptServer
    except Exception:
        return False
    routes = PromptServer.instance.routes

    def warm_up():
        """Scan the wildcard folders once in the background, so the first slot click is quick."""
        try:
            with _ROUTE_LOCK:
                get_wildcard_engine().library.visible_keys("off")
            # Count the lists behind every slot button once, so the panel opens with empty buttons hidden.
            matcher = get_matcher()
            for builder in get_builders().values():
                for slot in builder.slots:
                    with _ROUTE_LOCK:
                        matcher.lists_for(builder, slot, False)
        except Exception as error:
            print(f"[Wildcard Composer] warm-up skipped: {error}")
    threading.Thread(target=warm_up, name="prompt-builder-warmup", daemon=True).start()

    async def off_loop(function, *args):
        """File scans and list loading can take seconds on a big library; keep them off the server loop."""
        def locked():
            with _ROUTE_LOCK:
                return function(*args)
        return await asyncio.get_running_loop().run_in_executor(None, locked)

    def fail(error: Exception, status: int = 500):
        traceback.print_exc()
        return web.json_response({"error": str(error)}, status=status)

    @routes.get(ROUTE + "/builders")
    async def builders_route(request):
        try:
            return web.json_response({"builders": [_builder_payload(b) for b in get_builders().values()],
                                      "sections": {s: SECTION_LABELS[s] for s in SECTIONS},
                                      "default_order": list(DEFAULT_ORDER), "optional": list(OPTIONAL_SECTIONS)})
        except Exception as error:
            return fail(error)

    @routes.get(ROUTE + "/starter")
    async def starter_route(request):
        try:
            builder = get_builder(request.query.get("builder", ""))
            if builder is None:
                return web.json_response({"error": "unknown builder"}, status=404)
            return web.json_response(await off_loop(starter_state, builder, _level(request.query.get("nsfw")),
                                                    _violence(request.query.get("violence"))))
        except Exception as error:
            return fail(error)

    @routes.get(ROUTE + "/slot")
    async def slot_route(request):
        try:
            builder = get_builder(request.query.get("builder", ""))
            slot = builder.slot(request.query.get("slot", "")) if builder else None
            if slot is None:
                return web.json_response({"error": "unknown builder or slot"}, status=404)
            started = time.time()
            lists = await off_loop(get_matcher().lists_for, builder, slot, _level(request.query.get("nsfw")),
                                   request.query.get("gender", ""), _violence(request.query.get("violence")))
            return web.json_response({
                "slot": slot.id, "label": slot.label, "seconds": round(time.time() - started, 3),
                "lists": [_list_payload(info) for info in lists],
            })
        except Exception as error:
            return fail(error)

    @routes.get(ROUTE + "/slot_counts")
    async def slot_counts_route(request):
        """
        ?builder=&nsfw= -> {counts: {slot id: number of lists}, nsfw_only: [ids]}. The panel hides
        built-in buttons with none, and (at nsfw off) your own buttons whose lists are all rated above off.
        """
        try:
            builder = get_builder(request.query.get("builder", ""))
            if builder is None:
                return web.json_response({"error": "unknown builder"}, status=404)
            nsfw = _level(request.query.get("nsfw"))
            violence = _violence(request.query.get("violence"))
            matcher = get_matcher()
            counts = await off_loop(lambda: {slot.id: len(matcher.lists_for(builder, slot, nsfw, violence=violence))
                                             for slot in builder.slots})
            nsfw_only = [] if nsfw else await off_loop(lambda: [
                slot.id for slot in builder.slots
                if slot.custom and counts.get(slot.id) == 0 and matcher.lists_for(builder, slot, "explicit", violence=violence)])
            return web.json_response({"counts": counts, "nsfw_only": nsfw_only})
        except Exception as error:
            return fail(error)

    @routes.get(ROUTE + "/list")
    async def list_route(request):
        try:
            key = request.query.get("key", "").strip()
            query = request.query.get("q", "").strip().casefold()
            offset = max(0, int(request.query.get("offset", 0) or 0))
            limit = max(1, min(LIST_PAGE_MAX, int(request.query.get("limit", 200) or 200)))
            library = get_wildcard_engine().library
            level = _level(request.query.get("nsfw"))
            # Every entry, rated: the viewer shows what this level leaves out and lets you fix a rating.
            entries = await off_loop(lambda: library.entries_of(key, "explicit", include_dropped=True))
            folder_files = 0
            if not entries and key.startswith("prompts/"):
                # A whole prompt folder (prompts/<pack>/<theme>/* or the folder's name): every file in it. Each entry
                # keeps its own file, so drops and ratings set here go to that file.
                names = await off_loop(lambda: library._matching_names(key, "explicit", warn=False))
                folder_files = len(names)
                entries = await off_loop(lambda: [entry for name in names
                                                  for entry in library.entries_of(name, "explicit", include_dropped=True)])
            curation = library.curation
            dropped = curation.dropped(key) if curation is not None else set()
            matched = [entry for entry in entries if not query or query in entry.text.casefold()]
            row = curation.catalog.row(key) if curation is not None and curation.catalog is not None else None
            return web.json_response({
                "key": key, "total": len(entries), "matched": len(matched), "offset": offset,
                "stars": curation.stars(key) if curation is not None else 0,
                "hidden": curation.hidden(key) if curation is not None else False,
                "catalog": row.to_dict() if row is not None else None,
                "nsfw": level, "list_rating": library.list_rating(key),
                "list_override": str((curation._entry(key).get("nsfw", "") if curation is not None else "") or ""),
                # Under an _nsfw folder the folder's level wins (the rating box is shown locked at it).
                "rating_locked": max((nsfw_folder_tier(real) for real in library.real_keys(key)), default=0),
                "folder": bool(folder_files), "files": folder_files,
                "entries": [_entry_payload(library, curation, key, entry, dropped, level, folder=bool(folder_files))
                            for entry in matched[offset:offset + limit]],
            })
        except Exception as error:
            return fail(error)

    @routes.get(ROUTE + "/prompts")
    async def prompts_route(request):
        """?folder=prompts/<pack>&q=words&nsfw= -> the Prompt line's browser: folders and prompt files."""
        try:
            folder = request.query.get("folder", PROMPTS_ROOT)
            query = request.query.get("q", "")
            nsfw = _level(request.query.get("nsfw"))
            return web.json_response(await off_loop(prompt_browse, folder, query, nsfw))
        except Exception as error:
            return fail(error)

    @routes.get(ROUTE + "/find")
    async def find_route(request):
        """?q=words&nsfw=&gender=&names=1&limit= -> lists for the Find box (same fields as /slot)."""
        try:
            query = request.query.get("q", "").strip()
            limit = max(1, min(FIND_LIMIT_MAX, int(request.query.get("limit", 40) or 40)))
            started = time.time()
            lists = await off_loop(find_lists, query, _level(request.query.get("nsfw")),
                                   request.query.get("gender", ""), _flag(request.query.get("names")), limit,
                                   _violence(request.query.get("violence")))
            # capped: more lists have these words than were read or returned (the box says "N+").
            capped = len(lists) >= limit or bool(getattr(get_matcher(), "last_truncated", False))
            return web.json_response({"q": query, "seconds": round(time.time() - started, 3), "capped": capped,
                                      "lists": [_list_payload(info) for info in lists]})
        except Exception as error:
            return fail(error)

    @routes.post(ROUTE + "/buttons")
    async def buttons_route(request):
        """{action: 'save', button: {id?, label, section, lists?, search?}} or {action: 'delete', id}."""
        try:
            data = await request.json()
            action = str(data.get("action", "save"))
            if action == "delete":
                removed = await off_loop(delete_button, str(data.get("id", "")))
                return web.json_response({"deleted": removed}, status=200 if removed else 404)
            button = await off_loop(save_button, data.get("button") or {})
            return web.json_response({"button": button})
        except ValueError as error:
            return web.json_response({"error": str(error)}, status=400)
        except Exception as error:
            return fail(error)

    @routes.get(ROUTE + "/more")
    async def more_route(request):
        """?builder=&sections=subject,action&nsfw= -> lists no button offers, grouped."""
        try:
            sections = [s.strip() for s in request.query.get("sections", "").split(",") if s.strip()]
            started = time.time()
            data = await off_loop(more_payload, request.query.get("builder", ""), sections, _level(request.query.get("nsfw")),
                                  _violence(request.query.get("violence")))
            data["seconds"] = round(time.time() - started, 2)
            return web.json_response(data)
        except ValueError as error:
            return web.json_response({"error": str(error)}, status=400)
        except Exception as error:
            return fail(error)

    @routes.post(ROUTE + "/layout")
    async def layout_route(request):
        """
        Your button layout (builders_user/button_layout.yaml), for every node:
        {action: 'move', slot, section?, group?, before?, section_ids?} | {action: 'hide', slot, hidden}
        | {action: 'reset'}
        """
        try:
            data = await request.json()
            action = str(data.get("action", ""))
            slot_id = str(data.get("slot", ""))

            def change():
                if action == "reset":
                    if os.path.exists(LAYOUT_PATH):
                        os.remove(LAYOUT_PATH)
                    return {"reset": True}
                layout = read_layout(LAYOUT_PATH)
                if not slot_id:
                    raise ValueError("no slot")
                if action == "move":
                    section = data.get("section")
                    if section and section not in SECTIONS:
                        raise ValueError(f"unknown section '{section}'")
                    group = data.get("group")
                    layout = layout_move(layout, slot_id, section or None, None if group is None else str(group),
                                         data.get("before") or None, data.get("section_ids"))
                elif action == "hide":
                    layout = layout_hide(layout, slot_id, bool(data.get("hidden", True)))
                else:
                    raise ValueError(f"unknown action '{action}'")
                write_layout(LAYOUT_PATH, layout)
                return {"layout": layout}
            return web.json_response(await off_loop(change))
        except ValueError as error:
            return web.json_response({"error": str(error)}, status=400)
        except Exception as error:
            return fail(error)

    @routes.post(ROUTE + "/merge/preview")
    async def merge_preview_route(request):
        try:
            data = await request.json()
            result = await off_loop(merge_preview, str(data.get("builder", "")), str(data.get("slot", "")),
                                    list(data.get("keys") or []), _level(data.get("nsfw")))
            return web.json_response(result)
        except ValueError as error:
            return web.json_response({"error": str(error)}, status=400)
        except Exception as error:
            return fail(error)

    @routes.post(ROUTE + "/merge/save")
    async def merge_save_route(request):
        try:
            data = await request.json()
            result = await off_loop(merge_save, str(data.get("builder", "")), str(data.get("slot", "")),
                                    str(data.get("name", "")), list(data.get("entries") or []),
                                    list(data.get("sources") or []), bool(data.get("hide_sources")),
                                    bool(data.get("overwrite")))
            return web.json_response(result)
        except FileExistsError:
            return web.json_response({"error": "a merged list with that name exists", "exists": True}, status=409)
        except ValueError as error:
            return web.json_response({"error": str(error)}, status=400)
        except Exception as error:
            return fail(error)

    @routes.get(ROUTE + "/templates")
    async def templates_route(request):
        try:
            return web.json_response({"templates": await off_loop(list_templates)})
        except Exception as error:
            return fail(error)

    @routes.get(ROUTE + "/template")
    async def template_route(request):
        try:
            data = await off_loop(read_template, request.query.get("file", ""), _level(request.query.get("nsfw")))
            return web.json_response(data)
        except FileNotFoundError:
            return web.json_response({"error": "no such template"}, status=404)
        except ValueError as error:
            return web.json_response({"error": str(error)}, status=400)
        except Exception as error:
            return fail(error)

    @routes.post(ROUTE + "/templates")
    async def templates_post_route(request):
        """{action: 'save', name, builder, platform, composer, overwrite?} or {action: 'delete', file}."""
        try:
            data = await request.json()
            if str(data.get("action", "save")) == "delete":
                removed = await off_loop(delete_template, str(data.get("file", "")))
                return web.json_response({"deleted": removed}, status=200 if removed else 404)
            saved = await off_loop(save_template, str(data.get("name", "")), str(data.get("builder", "")),
                                   data.get("composer"), str(data.get("platform", "")), bool(data.get("overwrite")))
            return web.json_response({"template": saved})
        except FileExistsError as error:
            return web.json_response({"error": str(error), "exists": True}, status=409)
        except ValueError as error:
            return web.json_response({"error": str(error)}, status=400)
        except Exception as error:
            return fail(error)

    @routes.get(ROUTE + "/platforms")
    async def platforms_route(request):
        try:
            payload = []
            for platform in platform_choices():
                profile = None if platform == GENERIC_PLATFORM else get_profile(platform)
                payload.append({
                    "id": platform,
                    "label": getattr(profile, "name", "") or platform,
                    "order": platform_order(platform),
                    "structure": getattr(profile, "structure", "") if profile else "",
                    "target_words": list(getattr(profile, "target_words", ()) or ()) if profile else [],
                })
            return web.json_response({"platforms": payload})
        except Exception as error:
            return fail(error)

    @routes.post(ROUTE + "/preview")
    async def preview_route(request):
        try:
            data = await request.json()
            builder = get_builder(str(data.get("builder", "")))
            if builder is None:
                return web.json_response({"error": "unknown builder"}, status=404)
            composer = data.get("composer", "")
            if not isinstance(composer, str):
                composer = json.dumps(composer)
            result = await off_loop(build, builder, composer, int(data.get("seed", 0) or 0),
                                    str(data.get("platform", "")), _level(data.get("nsfw", "off")),
                                    None, _violence(data.get("violence", 0)))
            return web.json_response({
                "blocked": result.get("blocked", ""),
                "text": result["text"], "template": result["template"], "sections": result["own_sections"],
                "templates": result["own_templates"], "picks": result["picks"], "warnings": result["warnings"],
                "order": result["order"], "seeds": result["seeds"], "to_fill": result["to_fill"],
            })
        except Exception as error:
            return fail(error)

    @routes.post(ROUTE + "/rate")
    async def rate_route(request):
        """
        {key, stars?, hidden?, nsfw?, name?, drop?, undrop?, rate?} -> the key's new settings in _catalog_user.yaml.
        nsfw: the list's level ('' = back to its folder / name rating); rate: {text, level} for one entry ('' clears).
        """
        try:
            data = await request.json()
            key = str(data.get("key", "")).strip().lower()
            curation = get_wildcard_engine().library.curation
            if not key or curation is None:
                return web.json_response({"error": "no key, or curation is off"}, status=400)
            changes = {name: data[name] for name in ("stars", "hidden", "nsfw", "name", "drop", "undrop", "rate") if name in data}
            entry = await off_loop(lambda: curation.update(key, **changes))
            return web.json_response({"key": key, "settings": entry})
        except KeyError as error:
            return web.json_response({"error": str(error)}, status=404)
        except Exception as error:
            return fail(error)

    @routes.get(ROUTE + "/catalog/status")
    async def catalog_status_route(request):
        engine = get_wildcard_engine()
        catalog = engine.catalog
        if catalog is None:
            return web.json_response({"state": "off"})
        rows = catalog.rows()
        return web.json_response(dict(catalog.status, lists=len(rows),
                                      files={root: c.db_path for root, c in catalog.catalogs.items()}))

    @routes.post(ROUTE + "/catalog/rebuild")
    async def catalog_rebuild_route(request):
        engine = get_wildcard_engine()
        if engine.catalog is None:
            return web.json_response({"state": "off"})
        threading.Thread(target=engine.update_catalog, name="wildcard-catalog", daemon=True).start()
        return web.json_response({"state": "started"})

    @routes.get(ROUTE + "/catalog/search")
    async def catalog_search_route(request):
        """?q=words&facet=&nsfw=0&limit=50 -> lists by name and sample entries, best first."""
        try:
            engine = get_wildcard_engine()
            if engine.catalog is None:
                return web.json_response({"lists": []})
            query = request.query.get("q", "")
            facet = request.query.get("facet", "")
            nsfw = _level(request.query.get("nsfw"))
            limit = max(1, min(200, int(request.query.get("limit", 50) or 50)))
            visible = set(engine.library.visible_keys(nsfw))
            curation = engine.library.curation
            rows = [row for row in engine.catalog.search(query, limit * 4)
                    if row.key in visible and (not facet or row.facet == facet) and not curation.hidden(row.key)]
            # Text relevance first, nudged by stars and quality.
            order = {row.key: index for index, row in enumerate(rows)}
            rows.sort(key=lambda row: order[row.key] - 20 * curation.score(row.key))
            return web.json_response({"lists": [dict(row.to_dict(), stars=curation.stars(row.key)) for row in rows[:limit]]})
        except Exception as error:
            return fail(error)

    return True
