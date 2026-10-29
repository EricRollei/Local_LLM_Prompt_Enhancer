"""
Merging the lists behind a slot button into one list of your own.

Most downloaded packs share one core vocabulary ("black" hair is in 13 of 26 hair colour lists)
and add their own tail. merge_entries() folds near-identical entries across the chosen lists
("Black hair", "black", "black-haired" -> one row) and counts how many lists have each one, so
the shared core sorts first and the one-off tail can be pruned by eye. write_merged() saves the
kept entries as <root>/mine/<slot id>/<name>.txt; lists under mine/<slot id>/ are pinned first on
that slot's button (see slots.SlotMatcher).

No ComfyUI dependency.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import os
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set

MINE_FOLDER = "mine"

_WEIGHTED = re.compile(r"\(([^():]+):\s*[\d.]+\)")          # (auburn hair:1.2) -> auburn hair
_EDGE_PUNCT = re.compile(r"^[\s,.;:!]+|[\s,.;:!]+$")
_FOLD_PUNCT = re.compile(r"[^\w\s']+")
_SPACES = re.compile(r"\s+")
_WORD = re.compile(r"[a-z]+")
_NAME = re.compile(r"[^a-z0-9_\-]+")


def slot_words(*texts: str) -> Set[str]:
    """Words that only restate the slot ("hair", "eyes", "colour") and are ignored when folding."""
    words: Set[str] = set()
    for text in texts:
        for word in _WORD.findall((text or "").lower()):
            if len(word) < 3:
                continue
            stem = word[:-1] if word.endswith("s") and len(word) > 3 else word
            words.update({word, stem, stem + "s", stem + "ed", stem + "d"})
            if stem in ("color", "colour"):
                words.update({"color", "colour", "colors", "colours", "colored", "coloured"})
    return words


def clean_text(text: str) -> str:
    """How an entry is shown and saved: weights, underscores and stray edge punctuation removed."""
    text = _WEIGHTED.sub(r"\1", text or "")
    if "__" not in text:                                      # keep wildcard references intact
        text = re.sub(r"(?<=[A-Za-z])_(?=[A-Za-z])", " ", text)
    return _SPACES.sub(" ", _EDGE_PUNCT.sub("", text)).strip()


def fold_key(text: str, strip_words: Set[str] = frozenset()) -> str:
    """
    The identity of an entry for merging: lower case, punctuation and hyphens as spaces, slot words
    at either end dropped ('black-haired' -> 'black' for Hair color), a final plural s dropped.
    """
    if "__" in text or "{" in text:                           # wildcard syntax: only exact repeats fold
        return text.strip().lower()
    folded = _FOLD_PUNCT.sub(" ", clean_text(text).lower().replace("-", " "))
    words = _SPACES.sub(" ", folded).strip().split()
    while len(words) > 1 and words[-1] in strip_words:
        words.pop()
    while len(words) > 1 and words[0] in strip_words:
        words.pop(0)
    if words and len(words[-1]) > 3 and words[-1].endswith("s") and not words[-1].endswith("ss"):
        words[-1] = words[-1][:-1]
    return " ".join(words)


@dataclass
class MergedRow:
    text: str                                   # the most common spelling (shortest, then fewest capitals)
    fold: str
    sources: List[int] = field(default_factory=list)   # indexes into the source key list
    variants: List[str] = field(default_factory=list)  # other spellings folded into this row

    @property
    def lists(self) -> int:
        return len(self.sources)

    @property
    def words(self) -> int:
        return len(self.text.split())

    def to_dict(self) -> Dict:
        return {"text": self.text, "lists": self.lists, "sources": self.sources, "variants": self.variants[:6],
                "words": self.words}


def merge_entries(lists: Sequence[Iterable[str]], strip_words: Set[str] = frozenset()) -> List[MergedRow]:
    """
    One row per folded entry across the lists, most-shared first (then the order first seen).
    lists: the entry texts of each source list, in source order.
    """
    spellings: Dict[str, Counter] = {}
    sources: Dict[str, Set[int]] = {}
    order: Dict[str, int] = {}
    for index, texts in enumerate(lists):
        for raw in texts:
            text = clean_text(raw)
            if not text:
                continue
            key = fold_key(text, strip_words)
            if not key:
                continue
            spellings.setdefault(key, Counter())[text] += 1
            sources.setdefault(key, set()).add(index)
            order.setdefault(key, len(order))
    rows = []
    for key, counter in spellings.items():
        ranked = sorted(counter.items(), key=lambda item: (-item[1], len(item[0]), sum(c.isupper() for c in item[0]), item[0]))
        rows.append(MergedRow(text=ranked[0][0], fold=key, sources=sorted(sources[key]),
                              variants=[text for text, _count in ranked[1:]]))
    rows.sort(key=lambda row: (-row.lists, order[row.fold]))
    return rows


def merged_name(name: str) -> str:
    """'My Hair colours!' -> 'my_hair_colours' ('merged' when nothing is left)."""
    return _NAME.sub("_", (name or "").strip().lower()).strip("_-")[:60] or "merged"


def merged_path(root: str, slot_id: str, name: str) -> str:
    return os.path.join(root, MINE_FOLDER, merged_name(slot_id), merged_name(name) + ".txt")


def merged_key(slot_id: str, name: str) -> str:
    return f"{MINE_FOLDER}/{merged_name(slot_id)}/{merged_name(name)}"


def write_merged(path: str, entries: Sequence[str], sources: Sequence[str], slot_label: str = "",
                 overwrite: bool = False) -> int:
    """Write the kept entries (one per line) with a header naming the source lists. Returns the count."""
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(path)
    kept: List[str] = []
    seen: Set[str] = set()
    for entry in entries:
        text = clean_text(str(entry)).replace("\n", " ")
        if text and text.casefold() not in seen:
            seen.add(text.casefold())
            kept.append(text)
    if not kept:
        raise ValueError("nothing to save: every entry is unticked")
    header = [f"# Merged by the Wildcard Composer on {time.strftime('%Y-%m-%d')}"
              + (f" for the {slot_label} button" if slot_label else "") + f": {len(kept)} entries.",
              f"# From {len(sources)} lists (your own selection; check their licences before sharing):"]
    header += [f"#   {key}" for key in sources]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        handle.write("\n".join(header + kept) + "\n")
    os.replace(temp, path)
    return len(kept)


def pick_root(source_roots: Sequence[Optional[str]], search_paths: Sequence[str], avoid: str = "") -> Optional[str]:
    """
    Where a merged list goes: the wildcard folder most of its sources come from, never the
    package's own shipped folder (`avoid`) while another folder exists.
    """
    def allowed(root: str) -> bool:
        return not avoid or not os.path.normcase(os.path.abspath(root)).startswith(os.path.normcase(os.path.abspath(avoid)))
    counted = Counter(root for root in source_roots if root and allowed(root))
    if counted:
        return counted.most_common(1)[0][0]
    for root in search_paths:
        if allowed(root):
            return root
    return search_paths[0] if search_paths else None
