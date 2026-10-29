"""
Raw material for the surreal generators, read through the wildcard library so that the user's own packs and
their personal iconography file take part (and win over the shipped lists, by the library's usual priority).

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, List, Optional, Sequence

from .vocabulary import DOMAIN_TAGS, FORM_TAGS, MATERIAL_TAGS, SCALE_TAGS


@dataclass(frozen=True)
class Item:
    """One list entry. Mirrors core.wildcards.Entry without importing it, so this package stays standalone."""
    text: str
    tags: FrozenSet[str] = frozenset()
    key: str = ""
    personal: bool = False      # came from the user's iconography file

    @property
    def form(self) -> FrozenSet[str]:
        return self.tags & FORM_TAGS

    @property
    def domains(self) -> FrozenSet[str]:
        return (self.tags & DOMAIN_TAGS) | frozenset(part for part in self.key.split("/")[1:2] if part)

    @property
    def materials(self) -> FrozenSet[str]:
        return self.tags & MATERIAL_TAGS

    @property
    def scale(self) -> str:
        for tag in SCALE_TAGS:
            if tag in self.tags:
                return tag
        return ""


Lookup = Callable[[str], Sequence[object]]      # name -> entries with .text, .tags, .key

LISTS = {
    "objects": "objects/**",
    "spaces": "spaces/**",
    "materials": "materials/**",
    "animals": "animal",
    "weather": "weather",
    "physics": "surreal/physics",
    "absences": "surreal/absences",
    "idioms": "surreal/idioms",
    "processes": "surreal/processes",
    "temporal": "surreal/temporal",
    "autonomy": "surreal/autonomy",
    "reversals": "surreal/reversals",
    "hour": "surreal/found_strange/hour",
    "emptiness": "surreal/found_strange/emptiness",
    "stillness": "surreal/found_strange/stillness",
    "light": "surreal/found_strange/light",
    "trace": "surreal/found_strange/trace",
    "mechanism": "surreal/machines/mechanism",
    "feedstock": "surreal/machines/feedstock",
    "product": "surreal/machines/product",
    "icon_objects": "iconography/objects",
    "icon_places": "iconography/places",
    "icon_motifs": "iconography/motifs",
}
PERSONAL = ("icon_objects", "icon_places", "icon_motifs")


@dataclass
class SurrealSources:
    lookup: Lookup
    archive: Optional[Callable[[str, int], List[str]]] = None    # (idea, how many) -> fragments from the prompt database
    _cache: Dict[str, List[Item]] = field(default_factory=dict)

    def items(self, name: str) -> List[Item]:
        if name not in self._cache:
            found: List[Item] = []
            try:
                entries = self.lookup(LISTS[name])
            except Exception:
                entries = []
            for entry in entries:
                text = str(getattr(entry, "text", "") or "").strip()
                if text:
                    found.append(Item(text=text, tags=frozenset(getattr(entry, "tags", ()) or ()),
                                      key=str(getattr(entry, "key", "") or ""), personal=name in PERSONAL))
            self._cache[name] = found
        return self._cache[name]

    def objects(self) -> List[Item]:
        """Personal objects first: the engine prefers the user's own vocabulary to stock."""
        return self.items("icon_objects") + self.items("objects")

    def has_personal(self) -> bool:
        return any(self.items(name) for name in PERSONAL)


# ---- which listed objects does the idea already mention? -------------------------------------------
_SPLIT_AT = re.compile(r"\s+(?:with|on|in|at|under|over|beside|and)\s+|,")
_GROUP_NOUNS = {"stack", "pair", "row", "set", "loaf", "length", "coil", "bundle", "box", "jar", "bowl", "sheet", "roll", "piece", "bunch"}


def head_noun(text: str) -> str:
    """'a porcelain teacup on its saucer' -> 'teacup'; 'a stack of white dinner plates' -> 'plates'."""
    segment = _SPLIT_AT.split(text.strip().lower(), maxsplit=1)[0]
    words = re.findall(r"[a-z][a-z'-]+", segment)
    if not words:
        return ""
    if " of " in f" {segment} ":
        before, after = segment.split(" of ", 1)
        before_words = re.findall(r"[a-z][a-z'-]+", before)
        if before_words and before_words[-1] in _GROUP_NOUNS:
            after_words = re.findall(r"[a-z][a-z'-]+", after)
            return after_words[-1] if after_words else before_words[-1]
        return before_words[-1] if before_words else words[-1]
    return words[-1]


def _singular(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("es") and len(word) > 4 and word[-3] in "sxz":
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def mentioned(idea: str, items: Sequence[Item]) -> List[Item]:
    """Listed objects whose head noun appears in the idea, longest head first (so 'teacup' beats 'cup')."""
    words = {_singular(word) for word in re.findall(r"[a-z][a-z'-]+", (idea or "").lower())}
    hits = []
    for item in items:
        head = _singular(head_noun(item.text))
        if len(head) >= 3 and head in words:
            hits.append((len(head), item))
    hits.sort(key=lambda pair: -pair[0])
    seen, ordered = set(), []
    for _length, item in hits:
        head = _singular(head_noun(item.text))
        if head not in seen:
            seen.add(head)
            ordered.append(item)
    return ordered


def bare(text: str) -> str:
    """'a copper kettle' -> 'copper kettle' (for 'the ...' phrasing)."""
    return re.sub(r"^(?:a|an|the|some)\s+", "", text.strip(), flags=re.I)
