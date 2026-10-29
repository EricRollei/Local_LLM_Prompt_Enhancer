"""
Builder definitions: which slot buttons a builder node shows, and which wildcard lists back each slot.

A builder is one YAML file (builders/prompt.yaml and builders/character.yaml ship with the
package; files in builders_user/ with the same id replace them):

    id: prompt
    label: Wildcard Prompt Composer
    parts:                               # one composer line per prompt section
      - section: subject
        label: Subject
        multi: true                      # "+ Subject" adds subject_2, subject_3 ...
        hint: who or what the picture is about
        starter: "a {age} {occupation} with {hair_color} hair"
        slots: [subject, action]         # optional: which sections' buttons this part shows
    slots:
      - section: subject                 # buttons shown for that section
        slots:
          - id: hair_color
            label: Hair color
            match: ['hair_?colou?rs?']   # regexes, full match on a list's leaf name
            avoid: ['fantasy']           # regexes, searched in the whole key
            lists: ['mypack/best']       # optional: pinned lists, shown first
            folders: ['names?']          # optional: regexes searched in the list's folder path;
                                         #   every list in a matching folder counts (after `match`)
            search: 'famous buildings'   # optional: words that must all appear in the key
                                         #   (see key_has_terms); what "My buttons" categories use

    id: character
    extends: prompt                      # takes prompt's slots for the sections its parts show
    parts: [{section: subject, slots: [subject, action], starter: "..."}]

In `starter`, {slot_id} places a wildcard pill for that slot; everything else is text.

Your own buttons live in builders_user/my_buttons.yaml (made by the panel's "+ Button"; shared by
every builder, shown under "My buttons" in their section):

    buttons:
      - id: my_black_names
        label: Black names
        section: subject
        lists: [blackamericanfemalefirstnames_v10/black_female_names]
      - id: my_famous_buildings
        label: Famous buildings
        section: setting
        search: famous buildings

Until the wildcard catalog (dev/WILDCARD_CATALOG_SPEC.md, P2) ranks lists by quality, a slot's
lists are found by name: every visible list whose leaf name (the last path segment, lower case,
with pack prefixes such as cops_wc_ or cyber_ removed) fully matches one of the slot's `match`
patterns. Your stars rank first, then earlier patterns, then the catalog's quality score (short,
clean prose entries read best between typed words), then bigger lists. Hidden lists are left out. Lists with identical content (the same
file copied into several packs) are shown once.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from ..wildcards.library import NSFW_OFF, nsfw_level, violence_name_tier

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML ships with ComfyUI
    yaml = None

# Pack-specific prefixes seen in real libraries; removed before matching a leaf name.
_LEAF_PREFIX = re.compile(r"^(?:cops_(?:bp_)?(?:male_|female_)?wc_?|cyber_|bk_|rd_|fg3_|vc_|wc_|tr_)")
_SEPARATORS = re.compile(r"[\s\-.]+")

# Lists never offered by a slot, whatever their name (lists rated above the run's nsfw level are already hidden).
_ALWAYS_AVOID = re.compile(r"lora")
# Also left out of runs at nsfw off by name (lists rated by folder / name / content are already invisible to them).
_SFW_AVOID = re.compile(r"e621|nsfw|panties|no_bottom|nud(e|ity)|topless|lingerie")

GENDERS = ("female", "male")
_TOKENS = re.compile(r"[a-z]+")
_FEMALE_WORDS = {"female", "females", "women", "womens", "woman", "girl", "girls", "fem", "feminine", "lady",
                 "ladies"}
_MALE_WORDS = {"male", "males", "men", "mens", "man", "boy", "boys", "guy", "guys", "masculine", "gentleman",
               "gentlemen"}


def gender_of(key: str) -> str:
    """'female', 'male' or '' (neutral or both) from the words in a list's key."""
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key).lower()
    tokens = _TOKENS.findall(spaced)
    female = any(t in _FEMALE_WORDS or t.startswith(("female", "women", "woman", "girl")) for t in tokens)
    male = any(t in _MALE_WORDS or t.startswith(("male", "guy")) or (t.startswith("men") and len(t) <= 4)
               for t in tokens)
    if female and not male:
        return "female"
    if male and not female:
        return "male"
    return ""

# Keys the wildcard grammar can reference as __key__ (see core/wildcards/parser.py).
_REFERENCEABLE = re.compile(r"[a-z0-9][a-z0-9_\-/. ]*")

MIN_ENTRIES = 3
MAX_LISTS_PER_SLOT = 250
FIND_MAX_CANDIDATES = 400
MY_BUTTONS_FILE = "my_buttons.yaml"
MY_BUTTONS_GROUP = "My buttons"
_KEY_TOKENS = re.compile(r"[a-z0-9]+")


def search_terms(text: str) -> List[str]:
    return [term for term in _KEY_TOKENS.findall((text or "").lower()) if term]


def key_has_terms(key: str, terms: Sequence[str]) -> bool:
    """
    True when every term is in the key (folders included). A term of 4+ letters may sit inside a
    word ('names' finds peoplenamemegalist ... via 'name'), a shorter one must start a word; a
    trailing plural s is optional. Gender words ('female', 'men') match lists named for that gender,
    so 'male' does not find female lists.
    """
    if not terms:
        return False
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key).lower()
    tokens = _KEY_TOKENS.findall(spaced)
    gender = None
    for term in terms:
        if term in _FEMALE_WORDS or term in _MALE_WORDS:
            wanted = "female" if term in _FEMALE_WORDS else "male"
            gender = gender_of(key) if gender is None else gender
            if gender != wanted:
                return False
            continue
        stems = {term, term[:-1]} if len(term) > 3 and term.endswith("s") else {term}
        if not any((token.startswith(stem) or (len(stem) >= 4 and stem in token)) for token in tokens for stem in stems):
            return False
    return True


@dataclass
class SlotDef:
    id: str
    label: str
    match: List[str] = field(default_factory=list)
    avoid: List[str] = field(default_factory=list)
    lists: List[str] = field(default_factory=list)
    section: str = "subject"           # which prompt section's palette shows this slot
    tooltip: str = ""
    group: str = ""                    # palette heading (Person, Clothing, ...)
    folders: List[str] = field(default_factory=list)  # regexes searched in the folder part of a key
    search: str = ""                   # words that must all be in the key (key_has_terms)
    custom: bool = False               # from my_buttons.yaml
    kinds: List[str] = field(default_factory=list)  # subject types it serves (person, animal ...); [] = see kinds_of
    hidden: bool = False               # hidden by your button layout (shown in Arrange mode)

    def __post_init__(self) -> None:
        self._match = [re.compile(pattern, re.IGNORECASE) for pattern in self.match]
        self._avoid = [re.compile(pattern, re.IGNORECASE) for pattern in self.avoid]
        self._folders = [re.compile(pattern, re.IGNORECASE) for pattern in self.folders]
        self._terms = search_terms(self.search)

    def _avoided(self, key: str, nsfw) -> bool:
        return bool(_ALWAYS_AVOID.search(key) or any(pattern.search(key) for pattern in self._avoid)
                    or (nsfw_level(nsfw) == NSFW_OFF and _SFW_AVOID.search(key)))

    def leaf_rank(self, key: str, nsfw="explicit") -> Optional[int]:
        """Index of the first `match` pattern the key's own name fully matches, or None."""
        if not self._match or self._avoided(key, nsfw):
            return None
        leaf = leaf_name(key)
        for index, pattern in enumerate(self._match):
            if pattern.fullmatch(leaf):
                return index
        return None

    def match_rank(self, key: str, nsfw="off", folder_ok: bool = False) -> Optional[int]:
        """
        Rank of the key for this slot, or None: its own name against `match` (0, 1, ...), then
        `search` words, then `folders`, then (folder_ok: the name itself says nothing any slot knows,
        like 'basemodel/eye-color/brown') its folder names against `match`.
        """
        if self._avoided(key, nsfw):
            return None
        leaf = leaf_name(key)
        for index, pattern in enumerate(self._match):
            if pattern.fullmatch(leaf):
                return index
        if self._terms and key_has_terms(key, self._terms):
            return len(self._match)
        folder = key.rsplit("/", 1)[0] if "/" in key else ""
        if folder and any(pattern.search(folder) for pattern in self._folders):
            return len(self._match) + 1
        if folder_ok and self._match:
            for parent in parent_names(key):
                if any(pattern.fullmatch(parent) for pattern in self._match):
                    return len(self._match) + 2
        return None


@dataclass
class PartDef:
    section: str
    label: str
    starter: str = ""
    slots: List[str] = field(default_factory=list)   # sections whose slot buttons this part shows ([] = its own)
    multi: bool = False                                # "+ Subject" may add Subject 2, 3, ...
    hint: str = ""                                     # what goes here; also tells the LLM what to write when asked
    optional: bool = False                             # shown only when added with "+ Section" (Text)

    @property
    def slot_sections(self) -> List[str]:
        return self.slots or [self.section]


@dataclass
class BuilderDef:
    id: str
    label: str
    parts: List[PartDef]
    slots: List[SlotDef]
    description: str = ""
    origin: str = ""

    extends: str = ""

    def slot(self, slot_id: str) -> Optional[SlotDef]:
        for slot in self.slots:
            if slot.id == slot_id:
                return slot
        return None

    def part(self, section: str) -> Optional[PartDef]:
        """The part for a section; Subject 2, 3 ... ('subject_2') use the subject part."""
        base = base_section(section)
        for part in self.parts:
            if part.section == base:
                return part
        return None


def base_section(section: str) -> str:
    """'subject_2' -> 'subject'. Extra subjects share the subject section's slots and place in the order."""
    return re.sub(r"_\d+$", "", section or "")


@dataclass
class ListInfo:
    key: str
    count: int
    rank: int
    pinned: bool = False
    also: List[str] = field(default_factory=list)   # keys with identical content, folded into this one
    words: int = 0                                   # median words per entry: 1-4 short, 5-8 medium, more = long
    quality: float = -1.0                            # catalog quality 0..1 (-1 = not indexed yet)
    stars: int = 0                                   # the user's stars (0 = none)
    dialect: str = ""                                # prose | tags | mixed (from the catalog)
    display: str = ""
    nsfw: int = 0                                    # the list's rating 0..3 (library.NSFW_LEVELS)
    gender: str = ""                                 # female | male | '' (from the key's words)

    @property
    def order_score(self) -> float:
        """What ranks lists inside one match pattern: the catalog's quality (tag lists read worse
        between typed words), or, before the catalog is built, entry length alone."""
        if self.quality >= 0:
            return self.quality - (0.15 if self.dialect == "tags" else 0.05 if self.dialect == "mixed" else 0.0)
        return {"short": 0.8, "medium": 0.6, "long": 0.3}[self.length_class]

    @property
    def length_class(self) -> str:
        return "short" if self.words <= 4 else "medium" if self.words <= 8 else "long"


# Gender and rating words around a list name ("female_hair_colors", "poses_nsfw") don't change what
# the list is: they are stripped before matching (gender is judged separately, see gender_of).
_QUALIFIER_PREFIX = re.compile(r"^(?:(?:fe)?males?|(?:wo)?mens?|girls?|boys?|fem|n?sfw)_")
_QUALIFIER_SUFFIX = re.compile(r"_(?:(?:fe)?males?|(?:wo)?mens?|girls?|boys?|fem|n?sfw)$")


_NUMBER_PREFIX = re.compile(r"^\d+_+(?=[a-z])")       # "10-lighting" (The Loom's numbered folders)


def leaf_name(key: str) -> str:
    leaf = key.rsplit("/", 1)[-1].lower()
    leaf = _SEPARATORS.sub("_", leaf).strip("_")
    leaf = _NUMBER_PREFIX.sub("", leaf)
    leaf = _LEAF_PREFIX.sub("", leaf)
    for _ in range(2):
        stripped = _QUALIFIER_SUFFIX.sub("", _QUALIFIER_PREFIX.sub("", leaf))
        if not stripped or stripped == leaf:
            break
        leaf = stripped
    return leaf


# Folder names that say nothing about the content ("female/", "general/", "v2/"): looked past.
_GENERIC_FOLDER = re.compile(r"(?:(?:fe)?males?|(?:wo)?mens?|girls?|boys?|unisex|n?sfw|general|base|basic|main|misc|"
                             r"others?|all|common|default|standard|regular|simple|extra|custom|v\d+|types?|\d+|\d*wildcards?(_\w+)?|"
                             r"collections?|packs?|lists?|misc_\w+)")


def parent_names(key: str, limit: int = 1) -> List[str]:
    """
    The nearest meaningful folder name(s) of a key, normalised like leaf names, nearest first:
    'basemodel/eye-color/brown' -> ['eye_color']; 'pack/10-lighting/female/soft' -> ['lighting'].
    The top folder (the pack) is never used. One level by default: further up, folders tend to
    name a whole scene ('locations/.../kneeling/fully_clothed'), not the list.
    """
    parts = key.split("/")[1:-1]
    found: List[str] = []
    for part in reversed(parts):
        name = leaf_name(part)
        if not name or _GENERIC_FOLDER.fullmatch(name):
            continue
        found.append(name)
        if len(found) >= limit:
            break
    return found


# ----------------------------------------------------------------------------- loading
def _as_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value if item is not None]


def _slot_from_dict(raw: Dict, default_section: str = "subject") -> Optional[SlotDef]:
    if not isinstance(raw, dict) or not raw.get("id"):
        return None
    return SlotDef(
        id=str(raw["id"]).strip(),
        label=str(raw.get("label") or raw["id"]).strip(),
        match=_as_list(raw.get("match")),
        avoid=_as_list(raw.get("avoid")),
        lists=[item.strip().replace("\\", "/").lower() for item in _as_list(raw.get("lists"))],
        section=str(raw.get("section", "") or default_section).strip(),
        tooltip=str(raw.get("tooltip", "") or "").strip(),
        group=str(raw.get("group", "") or "").strip(),
        folders=_as_list(raw.get("folders")),
        search=str(raw.get("search", "") or "").strip(),
        kinds=[kind.strip().lower() for kind in _as_list(raw.get("kinds")) if kind.strip()],
    )


def builder_from_dict(data: Dict, origin: str = "") -> BuilderDef:
    builder_id = str(data.get("id") or os.path.splitext(os.path.basename(origin))[0]).strip()
    parts = []
    for part in (data.get("parts") or [{"section": "subject", "label": "Subject"}]):
        if not isinstance(part, dict):
            continue
        section = str(part.get("section", "subject")).strip() or "subject"
        parts.append(PartDef(
            section=section,
            label=str(part.get("label") or section.title()).strip(),
            starter=str(part.get("starter", "") or ""),
            slots=_as_list(part.get("slots")),
            multi=bool(part.get("multi", False)),
            hint=str(part.get("hint", "") or "").strip(),
            optional=bool(part.get("optional", False)),
        ))
    slots: List[SlotDef] = []
    for group in data.get("slots") or []:
        # Either a flat list of slots, or {section: x, slots: [...]} groups.
        if isinstance(group, dict) and isinstance(group.get("slots"), list) and not group.get("id"):
            for raw in group["slots"]:
                slot = _slot_from_dict(raw, str(group.get("section", "subject")))
                if slot:
                    slots.append(slot)
        else:
            slot = _slot_from_dict(group)
            if slot:
                slots.append(slot)
    return BuilderDef(id=builder_id, label=str(data.get("label") or builder_id), parts=parts, slots=slots,
                      description=str(data.get("description", "") or "").strip(), origin=origin,
                      extends=str(data.get("extends", "") or "").strip())


def _resolve_extends(builders: Dict[str, BuilderDef]) -> None:
    """A builder with `extends: other` gets the other's slots for the sections its parts show (its own slots win)."""
    for builder in builders.values():
        base = builders.get(builder.extends) if builder.extends else None
        if base is None or base is builder:
            continue
        wanted = {section for part in builder.parts for section in part.slot_sections}
        own = {slot.id for slot in builder.slots}
        inherited = [slot for slot in base.slots if slot.section in wanted and slot.id not in own]
        builder.slots = inherited + builder.slots
        for part in builder.parts:
            base_part = base.part(part.section)
            if base_part and not part.hint:
                part.hint = base_part.hint


# ----------------------------------------------------------------------------- my buttons
_BUTTON_ID = re.compile(r"[^a-z0-9_]+")


def button_id(label: str, taken: Iterable[str] = ()) -> str:
    """'Famous buildings' -> 'my_famous_buildings' (with _2, _3 ... when taken)."""
    base = "my_" + (_BUTTON_ID.sub("_", (label or "").lower()).strip("_") or "button")
    taken = set(taken)
    candidate, n = base, 2
    while candidate in taken:
        candidate, n = f"{base}_{n}", n + 1
    return candidate


def clean_button(raw: Dict) -> Optional[Dict]:
    """A my_buttons.yaml entry with only the fields it may have, or None when it has no label or lists/search."""
    if not isinstance(raw, dict):
        return None
    label = str(raw.get("label", "") or "").strip()
    lists = [item.strip().replace("\\", "/").lower() for item in _as_list(raw.get("lists")) if item.strip()]
    search = " ".join(search_terms(str(raw.get("search", "") or "")))
    if not label or not (lists or search):
        return None
    button = {"id": str(raw.get("id", "") or "").strip(), "label": label,
              "section": str(raw.get("section", "") or "subject").strip() or "subject"}
    if lists:
        button["lists"] = lists
    if search:
        button["search"] = search
    tooltip = str(raw.get("tooltip", "") or "").strip()
    if tooltip:
        button["tooltip"] = tooltip
    return button


def read_buttons(path: str) -> List[Dict]:
    """The entries of my_buttons.yaml (cleaned, ids filled in). A missing or broken file gives []."""
    if yaml is None or not path or not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except Exception as error:
        print(f"[Wildcard Composer] skipped {path}: {error}")
        return []
    raw_buttons = data.get("buttons") if isinstance(data, dict) else data
    buttons: List[Dict] = []
    for raw in raw_buttons or []:
        button = clean_button(raw)
        if button is None:
            continue
        if not button["id"] or button["id"] in {b["id"] for b in buttons}:
            button["id"] = button_id(button["label"], (b["id"] for b in buttons))
        buttons.append(button)
    return buttons


def write_buttons(path: str, buttons: List[Dict]) -> None:
    """Save my_buttons.yaml atomically (a temp file, then replace)."""
    if yaml is None:
        raise RuntimeError("PyYAML is not installed")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    header = ("# Your Wildcard Composer buttons. Made by the panel's \"+ Button\"; safe to edit by hand.\n"
              "# lists: exact list keys (shown first).  search: words that must all be in a list's key.\n")
    text = header + yaml.safe_dump({"buttons": buttons}, sort_keys=False, allow_unicode=True, width=120)
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(temp, path)


def button_slot(button: Dict) -> SlotDef:
    return SlotDef(id=button["id"], label=button["label"], lists=list(button.get("lists", [])),
                   search=button.get("search", ""), section=button.get("section", "subject"),
                   tooltip=button.get("tooltip", ""), group=MY_BUTTONS_GROUP, custom=True)


def apply_buttons(builders: Dict[str, BuilderDef], buttons: List[Dict]) -> None:
    """Add your buttons to every builder whose parts show their section (after its own slots)."""
    for builder in builders.values():
        shown = {section for part in builder.parts for section in part.slot_sections}
        own = {slot.id for slot in builder.slots}
        builder.slots = [slot for slot in builder.slots if not slot.custom] + [
            button_slot(button) for button in buttons if button["section"] in shown and button["id"] not in own]


# Subject types (the Subject lane's type menu) and which subject buttons each shows.
SUBJECT_KINDS = ("person", "animal", "creature", "object", "vehicle", "food", "scene")
PERSON_GROUPS = ("Person", "Face & hair", "Clothing", "Accessories", "Makeup")


def kinds_of(slot: SlotDef) -> List[str]:
    """The subject types a subject button serves: its `kinds`, else person for the person groups, else all."""
    if slot.kinds:
        return list(slot.kinds)
    if slot.section == "subject" and slot.group in PERSON_GROUPS:
        return ["person"]
    return []


def load_builders(folders: Sequence[str], buttons_path: str = "", layout_path: str = "") -> Dict[str, BuilderDef]:
    """Read every *.yaml in the folders; a later folder's builder replaces an earlier one with the same id.
    buttons_path (my_buttons.yaml) adds your own buttons to every builder."""
    builders: Dict[str, BuilderDef] = {}
    if yaml is None:
        return builders
    for folder in folders:
        if not folder or not os.path.isdir(folder):
            continue
        for filename in sorted(os.listdir(folder)):
            if not filename.lower().endswith((".yaml", ".yml")) or filename.startswith(("_", ".")):
                continue
            if filename.lower() in (MY_BUTTONS_FILE, "button_layout.yaml"):
                continue
            path = os.path.join(folder, filename)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    data = yaml.safe_load(handle) or {}
                builder = builder_from_dict(data, origin=path)
            except Exception as error:  # a broken user file must not hide the others
                print(f"[Wildcard Composer] skipped {path}: {error}")
                continue
            builders[builder.id] = builder
    layout = None
    if layout_path:
        from .layout import apply_layout, read_layout
        layout = read_layout(layout_path)
        apply_layout(builders, layout)      # before extends, so a button moved into Subject reaches the Character Composer
    _resolve_extends(builders)
    if buttons_path:
        apply_buttons(builders, read_buttons(buttons_path))
    if layout is not None:
        apply_layout(builders, layout)      # again, for your own buttons and the inherited order
    return builders


# ----------------------------------------------------------------------------- matching lists
def _signature(texts: Iterable[str]) -> str:
    digest = hashlib.sha1()
    for text in sorted({text.strip().casefold() for text in texts}):
        digest.update(text.encode("utf-8", "replace"))
        digest.update(b"\n")
    return digest.hexdigest()


def slot_has_lists(matcher: "SlotMatcher", builder: "BuilderDef", slot: "SlotDef", nsfw="off") -> int:
    """How many lists back a slot (for hiding buttons that would have none)."""
    return len(matcher.lists_for(builder, slot, nsfw))


def _violence_hidden(key: str, violence: int) -> bool:
    """A list a node with this violence_filter level does not offer: its name is in that tier or a lower one."""
    if not violence:
        return False
    tier = violence_name_tier(key)
    return bool(tier) and tier <= violence


class SlotMatcher:
    """
    Finds the lists behind each slot in one WildcardLibrary. Results are cached per
    (builder, slot, nsfw level) until the library's key set changes.
    """

    def __init__(self, library):
        self.library = library
        self._cache: Dict[Tuple, Tuple[int, List[ListInfo]]] = {}
        self._claimed: Dict[str, Tuple[int, Set[str]]] = {}
        self._unassigned: Dict[Tuple, Tuple[Tuple[int, int], List[str]]] = {}

    def lists_for(self, builder: BuilderDef, slot: SlotDef, nsfw="off", gender: str = "",
                  violence: int = 0) -> List[ListInfo]:
        """
        The lists behind a slot, best first (cached until the library or your ratings change). gender 'female' / 'male' leaves out lists named for the
        other one and puts lists named for this one first (neutral lists follow). violence: a
        violence_filter level (0-3); lists whose name falls in that tier or a lower one are left out.
        """
        gender = gender if gender in GENDERS else ""
        curation = getattr(self.library, "curation", None)
        generation = (self.library.generation, curation.version if curation is not None else 0)
        cache_key = (builder.id, slot.id, nsfw_level(nsfw), gender, int(violence))
        cached = self._cache.get(cache_key)
        if cached and cached[0] == generation:
            return cached[1]
        found = self._collect(slot, nsfw, gender, claimed=self.claimed(builder),
                              violence=int(violence))[:MAX_LISTS_PER_SLOT]
        self._cache[cache_key] = (generation, found)
        return found

    def clear(self) -> None:
        self._cache.clear()
        self._claimed.clear()
        self._unassigned.clear()

    def claimed(self, builder: BuilderDef) -> Set[str]:
        """Keys whose own name some slot of the builder knows. Only the others are matched by folder."""
        generation = self.library.generation
        cached = self._claimed.get(builder.id)
        if cached and cached[0] == generation:
            return cached[1]
        slots = [slot for slot in builder.slots if slot._match]
        found = {key for key in self.library.visible_keys("explicit")
                 if any(slot.leaf_rank(key) is not None for slot in slots)}
        self._claimed[builder.id] = (generation, found)
        return found

    def unassigned(self, builder: BuilderDef, nsfw="off", violence: int = 0) -> List[str]:
        """Visible keys no slot button of the builder offers (for the panel's More lists)."""
        curation = getattr(self.library, "curation", None)
        generation = (self.library.generation, curation.version if curation is not None else 0)
        cache_key = (builder.id, nsfw_level(nsfw), int(violence))
        cached = self._unassigned.get(cache_key)
        if cached and cached[0] == generation:
            return cached[1]
        claimed = self.claimed(builder)
        found = []
        for key in self.library.visible_keys(nsfw):
            if "__" in key or not _REFERENCEABLE.fullmatch(key) or _ALWAYS_AVOID.search(key):
                continue
            if curation is not None and curation.hidden(key):
                continue
            if key in claimed or _violence_hidden(key, violence):
                continue
            if any(key in slot.lists or slot.match_rank(key, "explicit", folder_ok=True) is not None for slot in builder.slots):
                continue
            found.append(key)
        self._unassigned[cache_key] = (generation, found)
        return found

    def find(self, query: str, nsfw="off", gender: str = "", also: Sequence[str] = (),
             limit: int = 40, violence: int = 0) -> List[ListInfo]:
        """
        Lists for the panel's Find box: every list whose key has all the words (key_has_terms),
        then `also` (e.g. the catalog's full-text hits on entries), deduplicated and ranked like a slot.
        """
        slot = SlotDef(id="_find", label="", search=query)
        if not slot._terms:
            return []
        return self._collect(slot, nsfw, gender if gender in GENDERS else "", extra=also,
                             max_candidates=FIND_MAX_CANDIDATES, violence=int(violence))[:limit]

    def _collect(self, slot: SlotDef, nsfw, gender: str, extra: Sequence[str] = (),
                 max_candidates: int = 0, claimed: Optional[Set[str]] = None, violence: int = 0) -> List[ListInfo]:
        curation = getattr(self.library, "curation", None)
        visible = self.library.visible_keys(nsfw)
        if violence:
            visible = [key for key in visible if not _violence_hidden(key, violence)]
        visible_set = set(visible)
        # A button you pin to a prompt file (prompts/...) offers it; nothing else ever matches one.
        pinnable = visible_set | set(getattr(self.library, "prompt_names", lambda _n: [])(nsfw))
        candidates: List[Tuple[int, bool, str]] = []
        for key in slot.lists:
            if key in pinnable:
                candidates.append((-1, True, key))
        # Your merged lists for this slot (mine/<slot id>/<name>, see merge.py) are pinned too.
        mine = f"mine/{slot.id}/"
        if slot.id != "_find":
            listed = set(slot.lists)
            candidates.extend((-1, True, key) for key in visible if key.startswith(mine) and key not in listed)
            # Lists you assigned to this button in the wildcard review (_catalog_user.yaml slot:) are pinned next.
            if curation is not None and hasattr(curation, "slot_keys"):
                taken = {key for _rank, _pin, key in candidates}
                candidates.extend((-1, True, key) for key in curation.slot_keys(slot.id)
                                  if key in pinnable and key not in taken)
        pinned = {key for _rank, _pin, key in candidates}
        for key in visible:
            if key in pinned or "__" in key or not _REFERENCEABLE.fullmatch(key):
                continue
            if curation is not None and curation.hidden(key):
                continue
            if gender and gender_of(key) not in ("", gender):
                continue
            rank = slot.match_rank(key, nsfw, folder_ok=claimed is not None and key not in claimed)
            if rank is not None:
                candidates.append((rank, False, key))
        named = {key for _rank, _pin, key in candidates}
        extra_rank = len(slot.match) + 2
        for key in extra:
            if key in named or key not in visible_set or "__" in key or not _REFERENCEABLE.fullmatch(key):
                continue
            if _ALWAYS_AVOID.search(key) or (curation is not None and curation.hidden(key)):
                continue
            if gender and gender_of(key) not in ("", gender):
                continue
            named.add(key)
            candidates.append((extra_rank, False, key))
        # Whether this search read only its likeliest candidates (the Find box then says "N+ lists").
        self.last_truncated = bool(max_candidates and len(candidates) > max_candidates)
        if max_candidates and len(candidates) > max_candidates:
            # A broad Find ('hair') can name thousands of lists; read the likeliest ones only.
            candidates.sort(key=lambda item: (item[0], len(item[2])))
            candidates = candidates[:max_candidates]

        found: List[ListInfo] = []
        by_signature: Dict[str, ListInfo] = {}
        for rank, is_pinned, key in candidates:
            entries = self.library.entries_of(key, nsfw=nsfw)
            if len(entries) < MIN_ENTRIES and not is_pinned:
                continue
            signature = _signature(entry.text for entry in entries)
            twin = by_signature.get(signature)
            if twin is not None:
                # Same content in another pack: keep the shorter (usually top-level) key.
                if len(key) < len(twin.key) and not twin.pinned:
                    twin.also.append(twin.key)
                    twin.key = key
                else:
                    twin.also.append(key)
                twin.rank = min(twin.rank, rank)
                continue
            lengths = sorted(len(entry.text.split()) for entry in entries)
            info = ListInfo(key=key, count=len(entries), rank=rank, pinned=is_pinned,
                            words=lengths[len(lengths) // 2] if lengths else 0,
                            nsfw=self.library.list_rating(key), gender=gender_of(key))
            if curation is not None:
                info.stars = curation.stars(key)
                row = curation.catalog.row(key) if curation.catalog is not None else None
                if row is not None:
                    info.quality, info.dialect, info.display = row.quality, row.dialect, row.display
            by_signature[signature] = info
            found.append(info)

        # Pinned, then your stars, then the match pattern's rank, then quality (short, clean prose
        # entries read best between typed words), then size. Long or tag lists stay in the viewer.
        found.sort(key=lambda info: (not info.pinned, -info.stars, bool(gender) and info.gender != gender, info.rank,
                                     -round(info.order_score, 1), -min(info.count, 2000), info.key))
        return found
