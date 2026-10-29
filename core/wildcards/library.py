"""
Wildcard library: finds, loads and indexes wildcard files from one or more folders.

File formats
    .txt            one entry per line. `# comment` lines and blank lines are skipped.
                    Optional weight prefix:  3::a very common entry
                    Key = path relative to the search folder, without extension:
                    wildcards/style/painters.txt  ->  __style/painters__
    .yaml / .yml    nested mappings. The KEYS form the wildcard path, the file name does
    .json           not (same convention as Dynamic Prompts and Impact Pack), so
                    `objects: {kitchen: [...]}` is __objects/kitchen__.
                    A leaf is a list. Each item is either a string, or a mapping:
                        - text: a cast-iron skillet
                          tags: [metal, kitchen, handheld, heavy]
                          weight: 2
                    A leaf that is a single string counts as a one-item list.
                    Tags are what tag queries (__objects[metal AND handheld]__) search.

Folder layout inside a search folder
    <pack>/...          ordinary packs
    _nsfw/<pack>/...    NSFW lists, rated explicit. Indexed, but only visible to a run at that level.
                        _nsfw/suggestive/<pack>/..., _nsfw/nudity/<pack>/... rate a folder lower.
                        Inside that run they answer to their name without the _nsfw/ prefix.
    _generated/...      lists written by the tools themselves. Always searched.
    _prompts/<pack>/... whole prompts, one per line. Indexed as their own area: a file answers ONLY to
                        prompts/<pack>/.../<file> (and __prompts/<folder>/*__ or __prompts/<folder>__ to every
                        file in a folder). Bare names, ordinary globs and the Composer's buttons never see them.
                        _prompts/_nsfw/... is rated like _nsfw/ and answers to prompts/<pack>/...
    _anything_else/     any other top-level folder starting with "_" is skipped
                        (_duplicates, _quarantine, _cleanup, ...).
    Skipped at any depth: __MACOSX, .git and other VCS folders, macOS "._" fork files.

NSFW levels (NSFW_LEVELS: off, suggestive, nudity, explicit)
    A run has a level (a node's nsfw setting); it uses lists and entries rated at that level or lower.
    off is SFW: it leaves out suggestive content too. Ratings are word matches, no model:
      list   its folder (_nsfw/ = explicit), its name below the pack folder (lingerie/underwear/bikini ->
             suggestive, nude/naked/topless -> nudity, nsfw/sex/porn/fetish -> explicit), or the user's
             override in _catalog_user.yaml (lists: <key>: nsfw: <level>). A list above the run's level
             does not exist for lookup, globs or tag queries.
      entry  its words (nsfw_word_tier, with exemptions such as "Garter Snake" or "nude pumps"), or the
             user's override in _catalog_user.yaml (lists: <key>: ratings: {entry: level}, or the
             top-level ratings: {entry: level} for every list).

Content filter (on by default)
    Entries that pair minor-related words with sexual words are dropped at load time in
    every folder: a plain word match on each entry, no model involved. `blocked_entries`
    counts them. content_filter=False (config.json "wildcards": {"content_filter": false})
    turns it off. prompt_block_reason() is the same test on a whole finished prompt, with explicit
    sexual terms only (nudity words alone do not count there); the engine re-rolls or blanks a
    prompt it fails (engine.process).

Violence filter (per run, off by default)
    A node's violence_filter setting (VIOLENCE_LEVELS: off, no gore, no gore or violent acts, no
    violence or weapons) makes the resolver skip entries whose words, or whose list's name, fall in
    that tier or a lower one. A word match (violence_tier / violence_name_tier), no model.

LoRA tags
    <lora:...> tags inside entries are removed at load time unless strip_lora=False
    (config.json "wildcards": {"strip_lora": false}). `stripped_lora_tags` counts them.

Several folders
    Search folders are ordered, highest priority first. When the same wildcard key exists in
    more than one folder, the FIRST folder that has it wins and the others are ignored for
    that key. So a pack in models/wildcards overrides a list that ships with this package,
    the same way ComfyUI model folders behave. Pass merge_roots=True to pool them instead.

Lookup (all case-insensitive), pool_mode "scoped" (default)
    exact           __style/painters__
    glob            __colors*__   __artists/**__   __**/pose__   (fnmatch; the explicit way to pool)
    same pack       a reference inside a pack's own list resolves inside that pack first:
                    randomPortrait/.../template.txt using __wildcards/quality__ finds
                    randomPortrait/wildcards/quality before anything else
    depth-agnostic  __painters__ also finds style/painters when no exact key exists.
                    When lists of that name exist in several packs, ONE pack is used
                    (the calling pack, else the highest-priority folder, else the shortest
                    path) and a warning names the alternatives. Lists of different packs
                    are never mixed by accident.
    folder          __materials__ stands for everything under materials/ (same one-pack rule)
    relocated pack  __look/styles__ also finds theLookWildcards_v10/styles: packs are written
                    for a folder name ("look") that rarely survives unzipping. Accepted only
                    when the folder that holds "styles" has the expected name INSIDE its own
                    name, and exactly one such folder exists. Otherwise nothing is guessed.
    pool_mode "legacy" restores the old behaviour: depth-agnostic and folder matches pool
    every pack.

Loading is lazy for .txt (read on first use) and eager for YAML/JSON (their keys are
only known after reading). Files are re-read when their mtime changes; the folder
scan itself is repeated at most every RESCAN_SECONDS.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import fnmatch
import json
import os
import functools
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from .boolean_expr import BooleanExpressionError, compile_expression, evaluate

try:
    import yaml  # PyYAML ships with ComfyUI
except ImportError:  # pragma: no cover
    yaml = None

RESCAN_SECONDS = 10.0
TEXT_EXTENSIONS = (".txt",)
STRUCTURED_EXTENSIONS = (".yaml", ".yml", ".json")

POOL_SCOPED = "scoped"
POOL_LEGACY = "legacy"
POOL_MODES = (POOL_SCOPED, POOL_LEGACY)

NSFW_FOLDER = "_nsfw"
GENERATED_FOLDER = "_generated"
PROMPTS_FOLDER = "_prompts"
_SEARCHED_UNDERSCORE_FOLDERS = {NSFW_FOLDER, GENERATED_FOLDER, PROMPTS_FOLDER}
_SKIPPED_FOLDERS = {"__macosx", ".git", ".svn", ".hg", "__pycache__"}
_NSFW_PREFIX = NSFW_FOLDER + "/"
_PROMPTS_PREFIX = PROMPTS_FOLDER + "/"
PROMPTS_NAME = "prompts"                  # the name the _prompts/ area answers to: prompts/<pack>/<file>
_PROMPTS_NAME_PREFIX = PROMPTS_NAME + "/"

_WEIGHT_PREFIX = re.compile(r"^\s*(\d+(?:\.\d+)?)::")
_HEX_COLOUR = re.compile(r"#[0-9A-Fa-f]{3,8}\b")
_LORA_TAG = re.compile(r"<lora:[^>]*>", re.IGNORECASE)
_LORA_SCARS = re.compile(r"^[\s,]+|[\s,]+$|(?<=,)\s*,")

# (List names are rated by _NAME_TIERS / nsfw_name_tier below.)
# Content filter: an entry matching BOTH patterns is never loaded.
_MINOR_TERMS = re.compile(
    r"\b(loli|lolis|shota|child|children|kid|kids|toddler|infant|underage|preteen|pre-teen|little girl|"
    r"little boy|young girl|young boy|schoolgirl|elementary school|middle school|"
    r"(?:1[0-7]|[1-9]) ?(?:yo|y/o|years? old)|teen|teens|teenage|teenager)\b",
    re.IGNORECASE,
)
_SEXUAL_TERMS = re.compile(
    r"\b(sex|sexual|fuck\w*|cum|cumshot|cock|dick|penis|pussy|vagina|anal|blowjob|fellatio|cunnilingus|"
    r"penetrat\w*|orgasm\w*|masturbat\w*|nipples?|genital\w*|porn\w*|nsfw|hentai|lewd|nude|naked|topless|"
    r"bottomless|panties|erotic|creampie|spread legs|pubic)\b",
    re.IGNORECASE,
)


# Phrases where a minor word names a thing, not a person ("child's pose", "a children's book"); taken
# out before the minor test so they alone never block an adult entry.
_MINOR_EXEMPT = re.compile(
    r"\bchild'?s pose\b|\bwinged infants?\b|\binfant (?:jesus|christ)\b|\bchristian child\b|"
    r"\bchildren'?s (?:books?|snacks?|toys?|menus?|sections?|stor(?:y|ies)|shows?|tv|television|drawings?|"
    r"illustrations?|songs?|library|hospital|museum|theatre|theater|cartoons?|games?)\b",
    re.IGNORECASE,
)


def is_blocked_entry(text: str) -> bool:
    """True for an entry the content filter removes (minor-related and sexual terms together)."""
    if not _SEXUAL_TERMS.search(text):
        return False
    return bool(_MINOR_TERMS.search(_MINOR_EXEMPT.sub(" ", text)))


# The same minor test on a whole finished prompt, where terms from different pills meet. Narrower on the
# sexual side: explicit terms only, so nudity next to a child word (putti, a nude study near "mother and
# child") passes; nude / naked / topless / bottomless / nipples are not in this list.
_EXPLICIT_TERMS = re.compile(
    r"\b(sex|sexual|fuck\w*|cum|cumshot|cock|dick|penis|pussy|vagina|anal|blowjob|fellatio|cunnilingus|"
    r"penetrat\w*|orgasm\w*|masturbat\w*|genital\w*|porn\w*|nsfw|hentai|lewd|panties|erotic|creampie|"
    r"spread legs|pubic)\b",
    re.IGNORECASE,
)


def prompt_block_reason(text: str) -> str:
    """
    '' when a finished prompt is fine; else why the content filter blocks it ('"teen" with "erotic"').
    A word match, no model: a minor term and an explicit sexual term anywhere in the same prompt.
    """
    if not text:
        return ""
    sexual = _EXPLICIT_TERMS.search(text)
    if not sexual:
        return ""
    minor = _MINOR_TERMS.search(_MINOR_EXEMPT.sub(" ", text))
    return f'"{minor.group(0)}" with "{sexual.group(0)}"' if minor else ""


# Violence filter: a node's violence_filter setting, one of VIOLENCE_LEVELS. Each level blocks its own
# tier and every tier before it: 1 gore and torture, 2 violent acts, 3 weapons and combat. Entries are
# matched by words (no model); lists whose NAME says the tier are hidden as well.
VIOLENCE_LEVELS = ("off", "no gore", "no gore or violent acts", "no violence or weapons")
_VIOLENCE_GORE = re.compile(
    r"\b(gore|gory|guro|gruesome|grisly|dismember\w*|decapitat\w*|beheaded|"
    r"severed (?:head|heads|limbs?|arms?|legs?|hands?|fingers?)|mutilat\w*|disembowel\w*|eviscerat\w*|"
    r"entrails|innards|intestines|guts spill\w*|flayed|skinned alive|impaled|tortur\w*|corpses?|cadavers?|"
    r"dead bod(?:y|ies)|rotting flesh|mangled|butchered|(?:open|gaping|bleeding|bloody|stab|gunshot|bullet) wounds?|"
    r"covered in blood|blood[- ]?(?:soaked|stained|splatter\w*|spatter\w*|spray\w*|drenched|smeared|dripping)|"
    r"pools? of blood|bloodbath|bloodied|bleeding (?:out|profusely)|exposed (?:bone|organs|brain))\b",
    re.IGNORECASE,
)
_VIOLENCE_ACTS = re.compile(
    r"\b(murder\w*|kill(?:ing|ed|s)? (?:a|an|the|him|her|them|someone|people|man|woman)|slaughter\w*|massacre\w*|"
    r"execut(?:ion|ed|ing)|stabb(?:ing|ed)|shot (?:dead|in the|through)|shooting (?:at|someone|a man|a woman|people)|"
    r"gunned down|strangl\w*|beat(?:ing|en) (?:up|to death|someone|him|her)|lynching|lynched|hanged|"
    r"assault(?:ing|ed)|mauled|bludgeon\w*|war crimes?|genocide|suicide|self[- ]harm|"
    r"drowning (?:someone|him|her)|choking (?:someone|him|her))\b",
    re.IGNORECASE,
)
_VIOLENCE_WEAPONS = re.compile(
    r"\b(guns?|gunfire|rifles?|pistols?|handguns?|revolvers?|shotguns?|machine ?guns?|submachine guns?|firearms?|"
    r"sniper\w*|ammunition|ammo|bullets?|grenades?|bombs?|explosives?|missiles?|rocket launchers?|bazookas?|"
    r"artillery|swords?|katanas?|daggers?|knives|knife|blades?|machetes?|axes?|battle ?axes?|spears?|halberds?|"
    r"maces?|crossbows?|bows? and arrows?|weapons?|weaponry|armed|combat|battles?|battlefields?|battlegrounds?|"
    r"warfare|war|firefights?|gunfights?|shootouts?|sword ?fight\w*)\b",
    re.IGNORECASE,
)
_VIOLENCE_NAMES = (
    re.compile(r"(?<![a-z])(gore|guro|torture|snuff|gruesome|corpses?)(?![a-z])"),
    re.compile(r"(?<![a-z])(violence|violent|murders?|killings?|executions?|massacres?)(?![a-z])"),
    re.compile(r"(?<![a-z])(weapons?|guns?|firearms?|swords?|knives|blades|combat|warfare)(?![a-z])"),
)


def violence_level(value) -> int:
    """A node's violence_filter value (name or number) as 0 (off) .. 3."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, min(3, value))
    text = str(value or "").strip().lower()
    if text in VIOLENCE_LEVELS:
        return VIOLENCE_LEVELS.index(text)
    return int(text) if text.isdigit() and int(text) <= 3 else 0


@functools.lru_cache(maxsize=262144)
def violence_tier(text: str) -> int:
    """0 = no violence words; 1 gore / torture; 2 violent acts; 3 weapons / combat (the most severe wins)."""
    if _VIOLENCE_GORE.search(text):
        return 1
    if _VIOLENCE_ACTS.search(text):
        return 2
    if _VIOLENCE_WEAPONS.search(text):
        return 3
    return 0


@functools.lru_cache(maxsize=65536)
def violence_name_tier(key: str) -> int:
    """The tier a list's NAME says (the path below the pack, as is_nsfw_name reads it), 0 = none."""
    below = key.split("/", 1)[1] if "/" in key else key
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", below).lower().replace("_", " ").replace("-", " ")
    for tier, pattern in enumerate(_VIOLENCE_NAMES, start=1):
        if pattern.search(spaced):
            return tier
    return 0


def violence_blocked(text: str, key: str, level: int) -> bool:
    """True when a node with this violence_filter level must skip the entry (its words or its list's name)."""
    if level <= 0:
        return False
    name_tier = violence_name_tier(key) if key else 0
    if name_tier and name_tier <= level:
        return True
    tier = violence_tier(text)
    return bool(tier) and tier <= level


# NSFW levels: what a run may use. Lists and entries are rated 0..3; a run at level N uses those rated N or
# lower. Same levels as the LoRA cards and the LoRA Suggester. off is SFW and leaves out suggestive content too.
NSFW_LEVELS = ("off", "suggestive", "nudity", "explicit")
NSFW_OFF, NSFW_SUGGESTIVE, NSFW_NUDITY, NSFW_EXPLICIT = 0, 1, 2, 3
_LEVEL_ALIASES = {"sfw": 0, "safe": 0, "none": 0, "false": 0, "no": 0, "nsfw": 3, "true": 3, "yes": 3, "nude": 2}


def nsfw_level(value) -> int:
    """A node's nsfw value (level name, 0-3, or a yes/no) as 0 (off) .. 3 (explicit)."""
    if isinstance(value, bool):
        return NSFW_EXPLICIT if value else NSFW_OFF
    if isinstance(value, int):
        return max(0, min(3, value))
    text = str(value or "").strip().lower()
    if text in NSFW_LEVELS:
        return NSFW_LEVELS.index(text)
    if text in _LEVEL_ALIASES:
        return _LEVEL_ALIASES[text]
    return int(text) if text.isdigit() and int(text) <= 3 else NSFW_OFF


# A list's NAME (the path below the pack folder, camelCase split, _ and - read as spaces). A pack called
# "SFWNSFW_bundle" is judged by its files, not its title. The most severe tier that matches wins.
_NAME_TIERS = (
    (NSFW_EXPLICIT, re.compile(
        r"nsfw|xxx|(?<![a-z])(sex|sexual|porn\w*|fetish\w*|bdsm|bondage|lewd|hentai|cum|cumplay|cumshot|pussy|"
        r"orgasm\w*|genitals?|sluts?|slutty|lapdance|ffm|mff|bukkake|anal|penis|vagina|e621|18 ?plus|18\+)(?![a-z])")),
    (NSFW_NUDITY, re.compile(r"(?<![a-z])(nude|nudes|naked|nudity|nudist|topless|nipples?|erotic\w*)(?![a-z])")),
    (NSFW_SUGGESTIVE, re.compile(
        r"(?<![a-z])(lingerie|underwear|panty|panties|bras?|bikinis?|negligees?|boudoir|pin ?ups?|sexy|"
        r"seductive|lust|lustful|lusty|garters?)(?![a-z])")),
)


@functools.lru_cache(maxsize=65536)
def nsfw_name_tier(relative_path: str) -> int:
    """The level a list's name says: the path below the pack folder, or the whole name of a loose file / YAML key."""
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", relative_path).lower()
    spaced = spaced.replace("_", " ").replace("-", " ").replace("\\", "/")
    spaced = _NSFW_EXEMPT.sub(" ", spaced)          # "nude makeup", "garter snake": the word means something else
    for tier, pattern in _NAME_TIERS:
        if pattern.search(spaced):
            return tier
    return NSFW_OFF


def nsfw_folder_tier(key: str) -> int:
    """_nsfw/<pack>/... = explicit; _nsfw/suggestive|nudity|explicit/<pack>/... = that level; elsewhere 0.
    The same below _prompts/ (_prompts/_nsfw/...)."""
    if key.startswith(_PROMPTS_PREFIX):
        key = key[len(_PROMPTS_PREFIX):]
    if not key.startswith(_NSFW_PREFIX):
        return NSFW_OFF
    first = key[len(_NSFW_PREFIX):].split("/", 1)[0]
    return NSFW_LEVELS.index(first) if first in NSFW_LEVELS[1:] else NSFW_EXPLICIT


def strip_nsfw_prefix(key: str) -> str:
    """
    The name a list answers to. An _nsfw/ list: without _nsfw/ (and without its level folder, if it has one).
    A _prompts/ file: prompts/ + the rest (and _prompts/_nsfw/x -> prompts/x).
    """
    if key.startswith(_PROMPTS_PREFIX):
        return _PROMPTS_NAME_PREFIX + strip_nsfw_prefix(key[len(_PROMPTS_PREFIX):])
    if not key.startswith(_NSFW_PREFIX):
        return key
    rest = key[len(_NSFW_PREFIX):]
    first, _, below = rest.partition("/")
    return below if first in NSFW_LEVELS[1:] and below else rest


def is_prompt_name(name: str) -> bool:
    """A lookup name in the prompt-file area (prompts/...), which answers only to names and globs starting prompts/."""
    return name == PROMPTS_NAME or name.startswith(_PROMPTS_NAME_PREFIX)


# An ENTRY's words. A word match, no model; the most severe tier that matches wins. Phrases where a rated word
# names something else are taken out first (_NSFW_EXEMPT, and _NSFW_EXEMPT_NAMES case-sensitively for names).
# These lists are for rating only; the content filter (_SEXUAL_TERMS / _EXPLICIT_TERMS) is separate.
_NSFW_WORDS = (
    (NSFW_EXPLICIT, re.compile(
        r"\b(sex|sexual|sex acts?|having sex|fuck\w*|cum|cumshot|cock|cocks|dick|dicks|penis|penises|pussy|vagina|"
        r"anal|blowjob|fellatio|cunnilingus|orgasm\w*|masturbat\w*|genital\w*|porn\w*|nsfw|hentai|lewd|creampie|"
        r"spread legs|bukkake|ejaculat\w*|erections?|intercourse|penetrated|penetration|xxx)\b", re.IGNORECASE)),
    (NSFW_NUDITY, re.compile(
        r"\b(nude|nudes|naked|nudity|nudist|topless|bottomless|nipples?|areolae?|areolas|bare[- ]breasted|"
        r"bare breasts?|exposed breasts?|breasts exposed|naked breasts?|full[- ]frontal|unclothed|undressed|"
        r"skinny[- ]dipping|pubic hair|erotic\w*|in the buff|au naturel)\b", re.IGNORECASE)),
    (NSFW_SUGGESTIVE, re.compile(
        r"\b(lingerie|negligees?|bikinis?|thongs?|g-strings?|bras?|panties|panty|garters?|garter belts?|"
        r"cleavage|sexy|seductive\w*|sultry|provocative\w*|pin-?ups?|boudoir|lap ?dances?|strippers?|striptease|"
        r"see-through|wet t-shirt|underwear|skimpy|busty|upskirt|downblouse|bedroom eyes|lustful|lusty|"
        r"lust|sensual\w*|scantily(?: clad)?)\b", re.IGNORECASE)),
)
_NSFW_EXEMPT = re.compile(
    r"\bgarter snakes?\b|\bbikini atoll\b|\bnaked mole[- ]rats?\b|\bnaked eye\b|\bnaked flames?\b|"
    r"\bnaked (?:truth|branches|trees?|bulbs?|light ?bulbs?|lightbulbs?|steel|blades?|ambition|singularity)\b|"
    r"\bbottomless (?:pits?|chasms?|abyss|depths?|wells?|void|oceans?|seas?|cups?|mugs?|brunch|mimosas?|holes?|"
    r"gorges?|caverns?|lakes?|darkness)\b|"
    r"\bnude[- ](?:colou?red|toned?|tones|shades?|pumps?|heels?|flats?|shoes?|sandals?|boots?|lipstick|lips?|"
    r"lip gloss|makeup|eyeshadow|nails?|nail polish|polish|palette|beige|mesh|leather|suede|stockings|tights|"
    r"pantyhose|blush|pink)\b|\b(?:in |a )?nude (?:colou?r|tones?)\b|"
    r"\bchristmas stockings?\b|\bstocking stuffers?\b|\bcum laude\b|\bmagna cum\b|\bsumma cum\b|"
    r"\bcock(?:'s)?[- ]?(?:crow\w*|fight\w*|a[- ]doodle\w*)\b|\bcocks? crow\w*\b|\bweather ?cock\b",
    re.IGNORECASE,
)
_NSFW_EXEMPT_NAMES = re.compile(r"\b(?:[A-Z]\.|[A-Z][a-z]+) Dick\b|\bDick [A-Z][a-z]+\b|\bMoby[- ]Dick\b")


@functools.lru_cache(maxsize=262144)
def nsfw_word_tier(text: str) -> int:
    """The level an entry's words say: 0 none, 1 suggestive, 2 nudity, 3 explicit."""
    cleaned = _NSFW_EXEMPT.sub(" ", _NSFW_EXEMPT_NAMES.sub(" ", text))
    for tier, pattern in _NSFW_WORDS:
        if pattern.search(cleaned):
            return tier
    return NSFW_OFF


@dataclass(frozen=True)
class Entry:
    text: str
    weight: float = 1.0
    tags: FrozenSet[str] = frozenset()
    origin: str = ""      # "<file path>" or "<file path>::key/path"
    key: str = ""         # wildcard key this entry belongs to


@dataclass
class _TextFile:
    path: str
    key: str
    root_index: int = 0
    mtime: float = -1.0
    nsfw: int = 0              # rating by folder / name, 0..3 (NSFW_LEVELS)
    entries: List[Entry] = field(default_factory=list)


@dataclass
class _StructuredFile:
    path: str
    root_index: int = 0
    mtime: float = -1.0
    nsfw: int = 0                                             # rating of the whole file by folder / name, 0..3
    keys: Dict[str, List[Entry]] = field(default_factory=dict)
    nsfw_keys: Dict[str, int] = field(default_factory=dict)   # key -> rating by its own name (rated keys only)
    prefix: List[str] = field(default_factory=list)   # under _prompts/: the file's folder, put before its keys
    stem: str = ""                                    # under _prompts/: the file name, for a file that is one list


@dataclass
class _View:
    """Lookup names visible to one kind of run (SFW or NSFW-allowed), rebuilt after each rescan."""
    names: List[str]                    # sorted lookup names
    name_set: Set[str]
    real: Dict[str, List[str]]          # lookup name -> real keys (an _nsfw/ key answers to its unprefixed name)
    by_leaf: Dict[str, List[str]]       # last path segment -> lookup names
    root_of: Dict[str, int]             # lookup name -> best (lowest) root index
    rating: Dict[str, int] = field(default_factory=dict)   # lookup name -> its list rating, 0..3
    hidden: Set[str] = field(default_factory=set)   # hidden by the user: exact names only
    visible: Optional["_View"] = None                # this view without the hidden names (None = no hidden)
    prompts: List[str] = field(default_factory=list)       # prompt files (prompts/...): NOT in names / by_leaf
    prompt_set: Set[str] = field(default_factory=set)


def _visible_only(view: "_View") -> "_View":
    """The view without the names the user hid (they keep answering to their exact name)."""
    names = [name for name in view.names if name not in view.hidden]
    by_leaf: Dict[str, List[str]] = {}
    for name in names:
        by_leaf.setdefault(name.rsplit("/", 1)[-1], []).append(name)
    prompts = [name for name in view.prompts if name not in view.hidden]
    return _View(names=names, name_set=set(names), real=view.real, by_leaf=by_leaf, root_of=view.root_of,
                 rating=view.rating, prompts=prompts, prompt_set=set(prompts))


def read_text_file(path: str) -> str:
    """
    Read a pack file. Most are UTF-8 (with or without BOM); older packs saved from Windows
    editors are cp1252. Decoding as cp1252 never fails, so nothing is lost to U+FFFD marks.
    """
    with open(path, "rb") as handle:
        raw = handle.read()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def normalise_key(name: str) -> str:
    return name.strip().replace("\\", "/").strip("/").lower()


def parse_text_line(line: str) -> Optional[Tuple[str, float]]:
    """Return (text, weight) for an entry line, or None for blank and comment lines."""
    stripped = line.strip()
    if not stripped:
        return None
    if stripped.startswith("#") and not _HEX_COLOUR.match(stripped):
        return None
    weight = 1.0
    match = _WEIGHT_PREFIX.match(stripped)
    if match:
        weight = float(match.group(1))
        stripped = stripped[match.end():].strip()
        if not stripped:
            return None
    return stripped, weight


def _synchronized(method):
    """Serialise library access: the catalog builds in a background thread while nodes resolve prompts."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapper


def pack_of(name: str) -> str:
    """The pack a lookup name belongs to: its first folder. A loose top-level list has pack ''."""
    return name.split("/", 1)[0] if "/" in name else ""


class WildcardLibrary:
    def __init__(self, search_paths: Iterable[str], merge_roots: bool = False,
                 pool_mode: str = POOL_SCOPED, strip_lora: bool = True,
                 content_filter: bool = True):
        self._lock = threading.RLock()
        self.merge_roots = merge_roots
        self.pool_mode = pool_mode if pool_mode in POOL_MODES else POOL_SCOPED
        self.strip_lora = bool(strip_lora)
        self.content_filter = bool(content_filter)
        self.search_paths: List[str] = []
        for path in search_paths:
            if path and os.path.isdir(path):
                absolute = os.path.abspath(path)
                if absolute not in self.search_paths:
                    self.search_paths.append(absolute)
        self._text_files: Dict[str, List[_TextFile]] = {}      # key -> files (several folders may share a key)
        self._structured_files: Dict[str, _StructuredFile] = {}  # path -> file
        self._last_scan = 0.0
        self._generation = 0                    # bumps whenever the set of keys may have changed
        self._views: Dict[int, Tuple[int, _View]] = {}     # nsfw level -> (stamp, view)
        self._match_cache: Dict[Tuple, List[str]] = {}
        self._match_cache_generation = -1
        self.warnings: List[str] = []             # transient, reset by the engine before each run
        self.file_errors: Dict[str, str] = {}     # persistent: a broken file stays reported until it is fixed
        self.blocked_entries = 0                  # entries removed by the content filter (cumulative)
        # Optional curation (catalog + the user's _catalog_user.yaml, see curation.py): hides lists from
        # name matching, drops entries, adds content-detected NSFW, and ranks packs for ambiguous names.
        self.curation = None
        self.stripped_lora_tags = 0               # <lora:...> tags removed from entries (cumulative)

    # -- scanning ---------------------------------------------------------------
    @_synchronized
    def refresh(self, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_scan < RESCAN_SECONDS:
            return
        self._last_scan = now

        seen_text: Dict[str, List[_TextFile]] = {}
        seen_structured: Dict[str, _StructuredFile] = {}

        for root_index, root in enumerate(self.search_paths):
            for folder, subfolders, filenames in os.walk(root):
                at_top = os.path.normcase(folder) == os.path.normcase(root)
                subfolders[:] = [
                    name for name in subfolders
                    if name.lower() not in _SKIPPED_FOLDERS
                    and not (at_top and name.startswith("_") and name.lower() not in _SEARCHED_UNDERSCORE_FOLDERS)
                ]
                for filename in sorted(filenames):
                    if filename.startswith("._") or (at_top and filename.lower().startswith("_catalog")):
                        continue    # macOS forks; the catalog and the user's curation file
                    path = os.path.join(folder, filename)
                    extension = os.path.splitext(filename)[1].lower()
                    if extension in TEXT_EXTENSIONS:
                        relative = os.path.relpath(path, root)
                        key = normalise_key(os.path.splitext(relative)[0])
                        existing = self._find_text_file(key, path)
                        text_file = existing or _TextFile(path=path, key=key)
                        text_file.root_index = root_index
                        text_file.nsfw = self._path_rating(key)
                        seen_text.setdefault(key, []).append(text_file)
                    elif extension in STRUCTURED_EXTENSIONS:
                        structured = self._structured_files.get(path) or _StructuredFile(path=path)
                        structured.root_index = root_index
                        relative = normalise_key(os.path.splitext(os.path.relpath(path, root))[0])
                        structured.nsfw = self._path_rating(relative)
                        if relative.startswith(_PROMPTS_PREFIX):
                            # Prompt files keep their folder in their names (prompts/<pack>/.../<key>).
                            structured.prefix = relative.split("/")[:-1]
                            structured.stem = relative.rsplit("/", 1)[-1]
                        self._load_structured_if_changed(structured)
                        seen_structured[path] = structured

        old_signature = (set(self._text_files), {p: (s.mtime, s.nsfw) for p, s in self._structured_files.items()},
                         {k: tuple((f.path, f.nsfw) for f in v) for k, v in self._text_files.items()})
        self._text_files = seen_text
        self._structured_files = seen_structured
        new_signature = (set(self._text_files), {p: (s.mtime, s.nsfw) for p, s in self._structured_files.items()},
                         {k: tuple((f.path, f.nsfw) for f in v) for k, v in self._text_files.items()})
        if new_signature != old_signature:
            self._generation += 1
        # Forget errors for files that no longer exist.
        for path in list(self.file_errors):
            if not os.path.exists(path):
                del self.file_errors[path]

    @staticmethod
    def _path_rating(key: str) -> int:
        """key: a normalised relative path. Under _nsfw/ -> its folder's level. Else rated by the name below the pack.
        _prompts/ files are rated the same way, by the path below _prompts/."""
        if key.startswith(_PROMPTS_PREFIX):
            key = key[len(_PROMPTS_PREFIX):]
        if key.startswith(_NSFW_PREFIX):
            return nsfw_folder_tier(key)
        below_pack = key.split("/", 1)[1] if "/" in key else key
        return nsfw_name_tier(below_pack)

    def all_warnings(self) -> List[str]:
        return list(self.file_errors.values()) + list(self.warnings)

    def _find_text_file(self, key: str, path: str) -> Optional[_TextFile]:
        for text_file in self._text_files.get(key, []):
            if text_file.path == path:
                return text_file
        return None

    # -- loading ----------------------------------------------------------------
    def _make_entry(self, text: str, weight: float, origin: str, key: str,
                    tags: FrozenSet[str] = frozenset()) -> Optional[Entry]:
        """One entry after the load-time rules: LoRA tags stripped, content filter applied."""
        if self.strip_lora and "<" in text:
            stripped, count = _LORA_TAG.subn("", text)
            if count:
                self.stripped_lora_tags += count
                text = re.sub(r"\s{2,}", " ", _LORA_SCARS.sub("", stripped)).strip()
                if not text:
                    return None
        if self.content_filter and is_blocked_entry(text):
            self.blocked_entries += 1
            return None
        return Entry(text=text, weight=weight, tags=tags, origin=origin, key=key)

    def _load_text_if_changed(self, text_file: _TextFile) -> None:
        try:
            mtime = os.path.getmtime(text_file.path)
        except OSError:
            text_file.entries = []
            return
        if mtime == text_file.mtime:
            return
        entries: List[Entry] = []
        try:
            for line in read_text_file(text_file.path).splitlines():
                parsed = parse_text_line(line)
                if parsed:
                    entry = self._make_entry(parsed[0], parsed[1], text_file.path, text_file.key)
                    if entry:
                        entries.append(entry)
            self.file_errors.pop(text_file.path, None)
        except OSError as error:
            self.file_errors[text_file.path] = f"could not read {text_file.path}: {error}"
        text_file.entries = entries
        text_file.mtime = mtime

    def _load_structured_if_changed(self, structured: _StructuredFile) -> None:
        try:
            mtime = os.path.getmtime(structured.path)
        except OSError:
            structured.keys = {}
            return
        if mtime == structured.mtime:
            return
        structured.mtime = mtime
        structured.keys = {}
        structured.nsfw_keys = {}
        try:
            content = read_text_file(structured.path)
            if structured.path.lower().endswith(".json"):
                data = json.loads(content)
            elif yaml is not None:
                data = yaml.safe_load(content)
            else:
                self.file_errors[structured.path] = f"PyYAML not installed, skipped {structured.path}"
                return
        except Exception as error:  # malformed user file must never break a run
            first_line = str(error).strip().split("\n")[0]
            self.file_errors[structured.path] = f"could not parse {structured.path}: {first_line}"
            return
        self.file_errors.pop(structured.path, None)
        if isinstance(data, dict) and "nodes" in data and "links" in data:
            return  # a ComfyUI workflow saved next to the packs, not a wildcard file
        if structured.prefix:
            start = list(structured.prefix) if isinstance(data, dict) else list(structured.prefix) + [structured.stem]
            self._walk_structured(data, start, structured)
        else:
            self._walk_structured(data, [], structured)
        structured.nsfw_keys = {key: tier for key in structured.keys if (tier := nsfw_name_tier(key))}

    def _walk_structured(self, data, key_parts: List[str], structured: _StructuredFile) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                self._walk_structured(value, key_parts + [str(key)], structured)
            return
        if not key_parts:
            return
        if isinstance(data, list):
            items = data
        elif isinstance(data, (str, int, float)) and not isinstance(data, bool):
            items = [data]          # a single string under a key counts as a one-item list
        else:
            return
        key = normalise_key("/".join(key_parts))
        origin = f"{structured.path}::{key}"
        entries = structured.keys.setdefault(key, [])
        for item in items:
            entry = self._entry_from_item(item, origin, key)
            if entry:
                entries.append(entry)

    def _entry_from_item(self, item, origin: str, key: str) -> Optional[Entry]:
        if isinstance(item, str):
            parsed = parse_text_line(item)
            return self._make_entry(parsed[0], parsed[1], origin, key) if parsed else None
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            return self._make_entry(str(item), 1.0, origin, key)
        if isinstance(item, dict) and item.get("text"):
            raw_tags = item.get("tags") or []
            if isinstance(raw_tags, str):
                raw_tags = [tag for tag in re.split(r"[,;]", raw_tags)]
            tags = frozenset(str(tag).strip().lower() for tag in raw_tags if str(tag).strip())
            try:
                weight = float(item.get("weight", 1.0))
            except (TypeError, ValueError):
                weight = 1.0
            return self._make_entry(str(item["text"]).strip(), weight, origin, key, tags=tags)
        return None

    # -- views ------------------------------------------------------------------
    def _structured_key_rating(self, structured: _StructuredFile, key: str) -> int:
        return max(structured.nsfw, structured.nsfw_keys.get(key, 0))

    @_synchronized
    def _view(self, nsfw=NSFW_OFF) -> _View:
        """The lookup names a run at this nsfw level can use (lists rated at that level or lower)."""
        level = nsfw_level(nsfw)
        self.refresh()
        stamp = (self._generation, self._curation_version())
        cached = self._views.get(level)
        if cached and cached[0] == stamp:
            return cached[1]

        sources: Dict[str, List[Tuple[int, int]]] = {}        # real key -> [(root_index, rating)]
        for key, text_files in self._text_files.items():
            for text_file in text_files:
                sources.setdefault(key, []).append((text_file.root_index, text_file.nsfw))
        for structured in self._structured_files.values():
            for key in structured.keys:
                sources.setdefault(key, []).append(
                    (structured.root_index, self._structured_key_rating(structured, key)))
        curation = self.curation
        if curation is not None:
            # The user's overlay can rate a list either way; the catalog marks lists explicit by content.
            for key, key_sources in sources.items():
                verdict = curation.nsfw_rating(key)
                if verdict is not None and nsfw_folder_tier(key) == NSFW_OFF:
                    sources[key] = [(root, verdict) for root, _rating in key_sources]

        real: Dict[str, List[str]] = {}
        root_of: Dict[str, int] = {}
        rating: Dict[str, int] = {}
        for key, key_sources in sources.items():
            allowed = [(root, rated) for root, rated in key_sources if rated <= level]
            if not allowed:
                continue
            name = strip_nsfw_prefix(key)
            real.setdefault(name, []).append(key)
            best_root = min(root for root, _rated in allowed)
            root_of[name] = min(root_of.get(name, best_root), best_root)
            lowest = min(rated for _root, rated in allowed)
            rating[name] = min(rating.get(name, lowest), lowest)

        everything = sorted(real)
        # Prompt files are their own area: kept out of names (bare names, globs, folder names, visible_keys).
        names = [name for name in everything if not is_prompt_name(name)]
        prompts = [name for name in everything if is_prompt_name(name)]
        by_leaf: Dict[str, List[str]] = {}
        for name in names:
            by_leaf.setdefault(name.rsplit("/", 1)[-1], []).append(name)
        hidden = {name for name in everything if curation is not None and curation.hidden(name)}
        view = _View(names=names, name_set=set(names), real=real, by_leaf=by_leaf, root_of=root_of,
                     rating=rating, hidden=hidden, prompts=prompts, prompt_set=set(prompts))
        if hidden:
            view.visible = _visible_only(view)
        self._views[level] = (stamp, view)
        return view

    def _curation_version(self) -> int:
        return self.curation.version if self.curation is not None else 0

    # -- lookup -----------------------------------------------------------------
    @_synchronized
    def all_keys(self) -> List[str]:
        """Every real key in the library, NSFW included (for reports and scans)."""
        self.refresh()
        keys = set(self._text_files.keys())
        for structured in self._structured_files.values():
            keys.update(structured.keys.keys())
        return sorted(keys)

    @_synchronized
    def visible_keys(self, nsfw=NSFW_OFF, include_prompts: bool = False) -> List[str]:
        """Lookup names a run at this nsfw level can use. Prompt files (prompts/...) only when include_prompts."""
        view = self._view(nsfw)
        return list(view.names) + (list(view.prompts) if include_prompts else [])

    @_synchronized
    def prompt_names(self, nsfw=NSFW_OFF, include_hidden: bool = False) -> List[str]:
        """The prompt files (prompts/<pack>/.../<file>) a run at this nsfw level can use, hidden ones left out."""
        view = self._view(nsfw)
        if include_hidden or view.visible is None:
            return list(view.prompts)
        return list(view.visible.prompts)

    @_synchronized
    def real_keys(self, name: str) -> List[str]:
        """The real keys behind a lookup name (an _nsfw/ list answers to its name without the prefix)."""
        return list(self._view(NSFW_EXPLICIT).real.get(normalise_key(name), []))

    @_synchronized
    def list_rating(self, name: str) -> int:
        """A lookup name's list rating 0..3 (NSFW_LEVELS); 0 for an unknown name."""
        return self._view(NSFW_EXPLICIT).rating.get(normalise_key(name), NSFW_OFF)

    def entry_rating(self, entry: Entry) -> int:
        """An entry's rating 0..3: the user's override (_catalog_user.yaml ratings) or its words."""
        if self.curation is not None:
            override = self.curation.entry_rating(entry.key, entry.text)
            if override is not None:
                return override
        return nsfw_word_tier(entry.text)

    @_synchronized
    def entries_of(self, name: str, nsfw=NSFW_OFF, include_dropped: bool = False) -> List[Entry]:
        """
        Entries of one lookup name exactly as visible_keys() lists it: no globbing, no pack
        scoping, no folder expansion. For browsers and builders that already know the list they want.
        include_dropped: also return the entries the user dropped (a list viewer shows them struck out).
        nsfw: entries rated above this level are left out (a list viewer asks with NSFW_EXPLICIT and shows ratings).
        """
        view = self._view(nsfw)
        entries: List[Entry] = []
        for real_key in view.real.get(normalise_key(name), []):
            entries.extend(self._entries_for_key(real_key, nsfw=nsfw, apply_drops=not include_dropped))
        return entries

    @property
    def generation(self) -> int:
        """Bumps whenever the set of keys may have changed (after refresh())."""
        self.refresh()
        return self._generation

    @_synchronized
    def has(self, name: str, nsfw=NSFW_OFF, context: str = "") -> bool:
        return bool(self._matching_names(normalise_key(name), nsfw, context, warn=False))

    def _pick_one_pack(self, candidates: List[str], view: _View, name: str, context: str, warn: bool) -> List[str]:
        """Scoped mode: keep the candidates of one pack only."""
        by_pack: Dict[str, List[str]] = {}
        for candidate in candidates:
            by_pack.setdefault(pack_of(candidate), []).append(candidate)
        if len(by_pack) == 1:
            return candidates
        context_pack = pack_of(context) if context else None
        if context_pack is not None and context_pack in by_pack:
            return by_pack[context_pack]

        curation = self.curation

        def rank(pack: str):
            members = by_pack[pack]
            score = max((curation.score(m) for m in members), default=0.0) if curation is not None else 0.0
            return (min(view.root_of.get(m, 0) for m in members), -score, min(m.count("/") for m in members), pack)

        packs = sorted(by_pack, key=rank)
        chosen = packs[0]
        if warn:
            others = ", ".join(p or "(top level)" for p in packs[1:6]) + (" ..." if len(packs) > 6 else "")
            self._warn_once(
                f"'__{name}__' matches lists in {len(packs)} packs; used '{chosen or '(top level)'}' "
                f"(also in: {others}). Write __{chosen + '/' if chosen else ''}...{name}__ to choose, "
                f"or __**/{name}__ to use all of them."
            )
        return by_pack[chosen]

    def _warn_once(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    def _matching_names(self, key: str, nsfw, context: str = "", warn: bool = True) -> List[str]:
        if not key:
            return []
        level = nsfw_level(nsfw)
        view = self._view(level)
        stamp = (self._generation, self._curation_version())
        if self._match_cache_generation != stamp:
            self._match_cache = {}
            self._match_cache_generation = stamp
        context_key = normalise_key(context) if context else ""
        context_key = strip_nsfw_prefix(context_key)
        cache_key = (key, level, pack_of(context_key) if context_key else None)
        if not warn and cache_key in self._match_cache:
            return self._match_cache[cache_key]
        found = self._match_names_uncached(key, view, context_key, warn)
        self._match_cache[cache_key] = found
        return found

    def _match_names_uncached(self, key: str, view: _View, context: str, warn: bool) -> List[str]:
        scoped = self.pool_mode == POOL_SCOPED
        if key not in view.name_set and key not in view.prompt_set and self.curation is not None:
            # A list the wildcard review renamed still answers to its old name (aliases: in _catalog_user.yaml).
            renamed = getattr(self.curation, "alias_of", lambda _name: None)(key)
            if renamed and (renamed in view.name_set or renamed in view.prompt_set):
                return [renamed]
        if is_prompt_name(key):
            # The prompt-file area answers only to its own names: exact, a glob, or a folder (= every file in it).
            if key in view.prompt_set:
                return [key]
            pool = (view.visible or view).prompts
            if any(char in key for char in "*?"):
                return [candidate for candidate in pool if fnmatch.fnmatchcase(candidate, key)]
            folder = key.rstrip("/") + "/"
            return [candidate for candidate in pool if candidate.startswith(folder)]
        if key in view.name_set:
            return [key]            # an exact name always works, hidden or not
        if view.visible is not None:
            view = view.visible
        if any(char in key for char in "*?"):
            return [candidate for candidate in view.names if fnmatch.fnmatchcase(candidate, key)]

        # Same pack first: a list inside a pack that refers to __x__ or __sub/x__ means its own pack's x.
        if scoped and context and "/" in context:
            own_pack = pack_of(context)
            in_pack = own_pack + "/" + key
            if in_pack in view.name_set:
                return [in_pack]
            suffix = "/" + key
            leaf = key.rsplit("/", 1)[-1]
            same = [c for c in view.by_leaf.get(leaf, []) if c.startswith(own_pack + "/") and c.endswith(suffix)]
            if same:
                return same

        # Depth-agnostic: __painters__ finds style/painters.
        suffix = "/" + key
        leaf = key.rsplit("/", 1)[-1]
        deeper = [candidate for candidate in view.by_leaf.get(leaf, []) if candidate.endswith(suffix)]
        if deeper:
            return self._pick_one_pack(deeper, view, key, context, warn) if scoped else deeper

        # A folder name stands for everything inside it: __materials__ == __materials/**__
        # (only reached when no list of that exact name exists, so a real list always wins).
        inside = [candidate for candidate in view.names
                  if candidate.startswith(key + "/") or ("/" + key + "/") in candidate]
        if inside:
            if not scoped:
                return inside
            top_level = [candidate for candidate in inside if candidate.startswith(key + "/")]
            if top_level:
                return top_level
            return self._pick_one_pack(inside, view, key, context, warn)

        if "/" not in key:
            return []
        # Relocated pack: the folder part of the reference does not exist under that name.
        expected_folder, last_segment = key.rsplit("/", 1)
        expected_folder = expected_folder.rsplit("/", 1)[-1]
        if len(expected_folder) < 3:
            return []
        relocated = [
            candidate for candidate in view.by_leaf.get(last_segment, [])
            if "/" in candidate and expected_folder in candidate.rsplit("/", 1)[0].rsplit("/", 1)[-1]
        ]
        return relocated if len(relocated) == 1 else []

    @_synchronized
    def _entries_for_key(self, key: str, nsfw=NSFW_EXPLICIT, apply_drops: bool = True) -> List[Entry]:
        """
        Entries of one REAL key at an nsfw level: sources of the key rated above it are left out, and so are
        entries rated above it (their words, or the user's override). An empty result means none qualify.
        """
        level = nsfw_level(nsfw)
        by_root: Dict[int, List[Entry]] = {}
        for text_file in self._text_files.get(key, []):
            if text_file.nsfw > level:
                continue
            self._load_text_if_changed(text_file)
            if text_file.entries:
                by_root.setdefault(text_file.root_index, []).extend(text_file.entries)
        for structured in self._structured_files.values():
            found = structured.keys.get(key)
            if found and self._structured_key_rating(structured, key) <= level:
                by_root.setdefault(structured.root_index, []).extend(found)
        if not by_root:
            return []
        if self.merge_roots:
            entries = [entry for root_index in sorted(by_root) for entry in by_root[root_index]]
        else:
            entries = by_root[min(by_root)]  # highest-priority folder that has this key wins
        dropped = self.curation.dropped(key) if (self.curation is not None and apply_drops) else None
        if dropped:
            kept = [entry for entry in entries if entry.text.strip().casefold() not in dropped]
            entries = kept or entries   # dropping every entry would silently kill the list; keep it whole
        if level < NSFW_EXPLICIT:
            entries = [entry for entry in entries if self.entry_rating(entry) <= level]
        return entries

    # -- catalog support (read-only; see catalog.py) --------------------------------
    @_synchronized
    def catalog_sources(self) -> Dict[str, Dict[str, Tuple[str, List[str]]]]:
        """root -> {file path relative to root: (absolute path, [real keys in that file])}."""
        self.refresh()
        out: Dict[str, Dict[str, Tuple[str, List[str]]]] = {root: {} for root in self.search_paths}
        for key, text_files in list(self._text_files.items()):
            for text_file in text_files:
                root = self.search_paths[text_file.root_index]
                relative = os.path.relpath(text_file.path, root).replace("\\", "/")
                out[root][relative] = (text_file.path, [key])
        for structured in list(self._structured_files.values()):
            root = self.search_paths[structured.root_index]
            relative = os.path.relpath(structured.path, root).replace("\\", "/")
            out[root][relative] = (structured.path, sorted(structured.keys))
        return out

    @_synchronized
    def catalog_entries(self, root: str, key: str) -> Tuple[List[str], bool, bool]:
        """
        (entry texts, under _nsfw/, NSFW by name) of one real key in ONE folder, before the
        user's dropped entries are removed.
        """
        root_index = self.search_paths.index(root)
        texts: List[str] = []
        folder_nsfw = key.startswith(_NSFW_PREFIX)
        name_nsfw = False           # rated explicit by its name (the catalog's "explicit by name")
        for text_file in self._text_files.get(key, []):
            if text_file.root_index == root_index:
                self._load_text_if_changed(text_file)
                texts.extend(entry.text for entry in text_file.entries)
                name_nsfw = name_nsfw or text_file.nsfw >= NSFW_EXPLICIT
        for structured in list(self._structured_files.values()):
            if structured.root_index == root_index and key in structured.keys:
                texts.extend(entry.text for entry in structured.keys[key])
                name_nsfw = name_nsfw or self._structured_key_rating(structured, key) >= NSFW_EXPLICIT
        return texts, folder_nsfw, name_nsfw and not folder_nsfw

    @_synchronized
    def shadowed_keys(self) -> Dict[str, List[str]]:
        """Keys that exist in more than one folder: {key: [winning folder, shadowed folder, ...]}."""
        self.refresh()
        roots_by_key: Dict[str, set] = {}
        for key, text_files in self._text_files.items():
            for text_file in text_files:
                roots_by_key.setdefault(key, set()).add(text_file.root_index)
        for structured in self._structured_files.values():
            for key in structured.keys:
                roots_by_key.setdefault(key, set()).add(structured.root_index)
        return {
            key: [self.search_paths[index] for index in sorted(indices)]
            for key, indices in sorted(roots_by_key.items()) if len(indices) > 1
        }

    @_synchronized
    def lookup(self, name: str, nsfw=NSFW_OFF, context: str = "") -> List[Entry]:
        """
        All entries for a wildcard name (exact, glob, same-pack, depth-agnostic). Empty list when unknown.
        context: the key of the list whose entry contains this reference, for same-pack resolution.
        nsfw: the run's level; lists and entries rated above it are left out.
        """
        view = self._view(nsfw)
        entries: List[Entry] = []
        for lookup_name in self._matching_names(normalise_key(name), nsfw, context):
            for real_key in view.real.get(lookup_name, []):
                entries.extend(self._entries_for_key(real_key, nsfw))
        return entries

    @_synchronized
    def query_tags(self, expression: str, scope: str = "", nsfw=NSFW_OFF, context: str = "") -> List[Entry]:
        """
        Entries whose tags satisfy a boolean expression. `scope` limits the search to a
        wildcard name / glob; with an empty scope every tagged entry in the library is searched.
        The entry's own key segments count as tags too, so objects/kitchen entries match `kitchen`.
        """
        try:
            compiled = compile_expression(expression)
        except BooleanExpressionError as error:
            self.warnings.append(f"bad tag expression [{expression}]: {error}")
            return []

        if scope:
            candidates = self.lookup(scope, nsfw, context)
            if not candidates:
                candidates = self.lookup(scope.rstrip("/") + "/**", nsfw, context)
        else:
            # Only structured files can carry tags; never force-load large .txt packs for a tag search.
            level = nsfw_level(nsfw)
            self.refresh()
            candidates = []
            for structured in self._structured_files.values():
                for key, key_entries in structured.keys.items():
                    if self._structured_key_rating(structured, key) <= level:
                        candidates.extend(entry for entry in key_entries
                                          if level >= NSFW_EXPLICIT or self.entry_rating(entry) <= level)

        matches: List[Entry] = []
        for entry in candidates:
            if not entry.tags and not scope:
                continue
            key_tags = set(entry.key.split("/"))
            tag_pool = entry.tags | key_tags

            def term_is_true(term: str, pool=tag_pool) -> bool:
                return term.strip().lower() in pool

            if evaluate(compiled, term_is_true):
                matches.append(entry)
        return matches

    @_synchronized
    def stats(self) -> Dict[str, int]:
        keys = self.all_keys()
        tagged = 0
        total = 0
        nsfw_keys = 0
        visible = set(self.visible_keys(NSFW_OFF, include_prompts=True))
        for key in keys:
            if key not in visible:
                nsfw_keys += 1
            for entry in self._entries_for_key(key):
                total += 1
                if entry.tags:
                    tagged += 1
        return {"folders": len(self.search_paths), "wildcards": len(keys), "entries": total,
                "tagged_entries": tagged, "nsfw_wildcards": nsfw_keys,
                "blocked_entries": self.blocked_entries, "stripped_lora_tags": self.stripped_lora_tags}
