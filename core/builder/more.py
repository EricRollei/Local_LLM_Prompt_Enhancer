"""
"More lists": the usable lists no slot button offers, sorted into prompt sections and grouped by
the words in their paths, so every list is reachable from its section without a button of its own.

A list is usable when the catalog read it as words, phrases or tags (not whole prompts or
templates) with 3+ entries. Its section comes from the catalog's facet, or failing that from
words in its path; its group is the most common path word among the section's lists that it has.

No ComfyUI dependency.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence

USABLE_KINDS = ("atoms", "phrases", "tags")
MIN_GROUP = 3                 # smaller groups go to "Other"
MAX_LISTS_PER_GROUP = 300

# The catalog's facet (catalog.facet_for) -> prompt section.
FACET_SECTION = {
    "wardrobe": "subject", "appearance": "subject", "subject": "subject", "expression": "subject",
    "creature": "subject",
    "pose_action": "action",
    "architecture": "setting", "setting": "setting", "nature": "setting", "era_culture": "setting",
    "object_material": "setting",
    "lighting": "lighting",
    "style_artist": "style", "color_mood": "style", "concept": "style",
    "camera": "camera",
}

# For lists the catalog gave no facet: the first path word that names a section.
_WORD_SECTION = [
    ("subject", "hair face eye eyes body skin cloth clothing clothes outfit outfits dress wear attire garment makeup "
                "character characters person people girl woman man costume fashion accessory accessories jewelry "
                "species race creature creatures monster"),
    ("action", "pose poses action actions gesture activity activities interaction"),
    ("setting", "place places location locations room rooms environment environments landscape building buildings "
                "city world nature forest weather season food plant plants flower vehicle vehicles era scene scenes "
                "interior architecture background backgrounds object objects item items"),
    ("lighting", "light lights lighting atmosphere atmo mood"),
    ("style", "style styles art artist artists painter render rendering color colour colors texture "
              "material materials theme themes aesthetic aesthetics palette palettes"),
    ("format", "medium mediums format formats illustration illustrations poster posters genre genres"),
    ("composition", "composition compositions shot shots perspective perspectives view views framing layout"),
    ("camera", "camera cameras angle angles lens lenses aperture bokeh focus exposure photo photography film"),
    ("text", "font fonts typography lettering typeface typefaces"),
]
WORD_SECTION: Dict[str, str] = {word: section for section, words in _WORD_SECTION for word in words.split()}

_NOISE = set("""the and of for with a an wildcards wildcard wc random misc other others all general custom main base
list lists txt yaml sfw nsfw new old extra full simple basic prompt prompts tag tags type types common standard
regular default collection pack module part parts level detail details sdxl flux pony illustrious v1 v2 v3 v4
female male women woman men man girl girls boy unisex fem adj adjective adjectives word words verb verbs noun nouns
themed any sfw nsfw cops cha dcw nodetail core""".split())   # cops_: a pack family's file prefix
UNSORTED = "_unsorted"                         # sections value asking for the lists with no clear section
_WORDS = re.compile(r"[a-z]+")
_CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")


def path_tiers(key: str) -> List[List[str]]:
    """
    Meaningful words of a key below its pack folder, by distance from the leaf: [leaf words,
    parent folder words, words further up]. Plural s dropped; words that are part of the pack's
    own name ('sdvn' in sdvnwildcards_v10/wc-sdvn/...) left out, so groups name content, not packs.
    """
    parts = key.split("/")
    pack = _CAMEL.sub(" ", parts[0]).lower() if len(parts) > 1 else ""
    parts = parts[1:] if len(parts) > 1 else parts
    seen: set = set()
    tiers: List[List[str]] = [[], [], []]
    for depth, part in enumerate(reversed(parts)):
        tier = tiers[min(depth, 2)]
        for word in _WORDS.findall(_CAMEL.sub(" ", part).lower()):
            if len(word) < 3 or word in _NOISE or re.fullmatch(r"v\d+", word) or (pack and word in pack):
                continue
            if len(word) > 4 and word.endswith("s") and not word.endswith("ss"):
                word = word[:-1]
            if word not in seen:
                seen.add(word)
                tier.append(word)
    return tiers


def path_words(key: str) -> List[str]:
    """Meaningful words of a key below its pack folder, leaf words first (see path_tiers)."""
    return [word for tier in path_tiers(key) for word in tier]


def _word_section(words: Iterable[str]) -> Optional[str]:
    for word in words:
        if word in WORD_SECTION:
            return WORD_SECTION[word]
        if word + "s" in WORD_SECTION:
            return WORD_SECTION[word + "s"]
    return None


def section_of(key: str, facet: str) -> Optional[str]:
    """The list's own name or folder first ('.../places/...' is Setting), then the catalog's facet, then any path word."""
    tiers = path_tiers(key)
    return (_word_section(tiers[0] + tiers[1]) or FACET_SECTION.get(facet)
            or _word_section(tiers[2]))


@dataclass
class MoreGroup:
    word: str
    label: str
    keys: List[str] = field(default_factory=list)


def group_lists(keys: Sequence[str]) -> List[MoreGroup]:
    """
    Group keys by a shared path word: the most common of the leaf's own words that 3+ lists share,
    else of the parent folder's, else of any; lists with none go to 'Other'.
    """
    tiers_of = {key: path_tiers(key) for key in keys}
    counts = Counter(word for tiers in tiers_of.values() for tier in tiers for word in tier)
    groups: Dict[str, MoreGroup] = {}
    for key in keys:
        best = ""
        for tier in tiers_of[key]:
            shared = [word for word in tier if counts[word] >= MIN_GROUP]
            if shared:
                best = max(shared, key=lambda w: (counts[w], -tier.index(w)))
                break
        group = groups.get(best)
        if group is None:
            group = groups[best] = MoreGroup(word=best, label=best.replace("_", " ").title() if best else "Other")
        group.keys.append(key)
    ordered = sorted((g for g in groups.values() if g.word), key=lambda g: (-len(g.keys), g.word))
    if "" in groups:
        ordered.append(groups[""])
    return ordered


def more_lists(unassigned: Iterable[str], sections: Sequence[str], row_of: Callable[[str], object]) -> Dict:
    """
    The unassigned keys for these sections, grouped. row_of(key) -> the catalog row (with kind,
    entries, facet, signature, quality) or None. Lists with identical content keep their best copy.
    """
    wanted = set(sections)
    want_unsorted = UNSORTED in wanted
    chosen: Dict[str, object] = {}
    by_signature: Dict[str, str] = {}
    skipped = unsorted = 0
    for key in unassigned:
        row = row_of(key)
        if row is None or getattr(row, "kind", "") not in USABLE_KINDS or getattr(row, "entries", 0) < 3:
            skipped += 1
            continue
        section = section_of(key, getattr(row, "facet", "") or "")
        if section is None:
            unsorted += 1
            if not want_unsorted:
                continue
        elif section not in wanted:
            continue
        signature = getattr(row, "signature", "") or key
        twin = by_signature.get(signature)
        if twin is not None:
            if getattr(row, "quality", 0) > getattr(chosen[twin], "quality", 0):
                del chosen[twin]
                chosen[key] = row
                by_signature[signature] = key
            continue
        by_signature[signature] = key
        chosen[key] = row
    groups = group_lists(sorted(chosen))
    for group in groups:
        group.keys.sort(key=lambda k: (-getattr(chosen[k], "quality", 0), k))
    return {"groups": groups, "rows": chosen, "total": len(chosen), "skipped": skipped, "unsorted": unsorted}
