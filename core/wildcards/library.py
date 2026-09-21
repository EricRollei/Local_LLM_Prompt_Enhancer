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
                    Tags are what tag queries (__objects[metal AND handheld]__) search.

Several folders
    Search folders are ordered, highest priority first. When the same wildcard key exists in
    more than one folder, the FIRST folder that has it wins and the others are ignored for
    that key. So a pack in models/wildcards overrides a list that ships with this package,
    the same way ComfyUI model folders behave. Pass merge_roots=True to pool them instead.

Lookup (all case-insensitive)
    exact           __style/painters__
    glob            __colors*__   __artists/**__       (fnmatch over keys)
    depth-agnostic  __painters__ also finds style/painters when no exact key exists
    relocated pack  __look/styles__ also finds theLookWildcards_v10/styles: packs are written
                    for a folder name ("look") that rarely survives unzipping. Accepted only
                    when the folder that holds "styles" has the expected name INSIDE its own
                    name, and exactly one such folder exists. Otherwise nothing is guessed.

Loading is lazy for .txt (read on first use) and eager for YAML/JSON (their keys are
only known after reading). Files are re-read when their mtime changes; the folder
scan itself is repeated at most every RESCAN_SECONDS.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

from .boolean_expr import BooleanExpressionError, compile_expression, evaluate

try:
    import yaml  # PyYAML ships with ComfyUI
except ImportError:  # pragma: no cover
    yaml = None

RESCAN_SECONDS = 2.0
TEXT_EXTENSIONS = (".txt",)
STRUCTURED_EXTENSIONS = (".yaml", ".yml", ".json")

_WEIGHT_PREFIX = re.compile(r"^\s*(\d+(?:\.\d+)?)::")
_HEX_COLOUR = re.compile(r"#[0-9A-Fa-f]{3,8}\b")


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
    entries: List[Entry] = field(default_factory=list)


@dataclass
class _StructuredFile:
    path: str
    root_index: int = 0
    mtime: float = -1.0
    keys: Dict[str, List[Entry]] = field(default_factory=dict)


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


class WildcardLibrary:
    def __init__(self, search_paths: Iterable[str], merge_roots: bool = False):
        self.merge_roots = merge_roots
        self.search_paths: List[str] = []
        for path in search_paths:
            if path and os.path.isdir(path):
                absolute = os.path.abspath(path)
                if absolute not in self.search_paths:
                    self.search_paths.append(absolute)
        self._text_files: Dict[str, List[_TextFile]] = {}      # key -> files (several folders may share a key)
        self._structured_files: Dict[str, _StructuredFile] = {}  # path -> file
        self._last_scan = 0.0
        self.warnings: List[str] = []             # transient, reset by the engine before each run
        self.file_errors: Dict[str, str] = {}     # persistent: a broken file stays reported until it is fixed

    # -- scanning ---------------------------------------------------------------
    def refresh(self, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_scan < RESCAN_SECONDS:
            return
        self._last_scan = now

        seen_text: Dict[str, List[_TextFile]] = {}
        seen_structured: Dict[str, _StructuredFile] = {}

        for root_index, root in enumerate(self.search_paths):
            for folder, _subfolders, filenames in os.walk(root):
                for filename in sorted(filenames):
                    path = os.path.join(folder, filename)
                    extension = os.path.splitext(filename)[1].lower()
                    if extension in TEXT_EXTENSIONS:
                        relative = os.path.relpath(path, root)
                        key = normalise_key(os.path.splitext(relative)[0])
                        existing = self._find_text_file(key, path)
                        text_file = existing or _TextFile(path=path, key=key)
                        text_file.root_index = root_index
                        seen_text.setdefault(key, []).append(text_file)
                    elif extension in STRUCTURED_EXTENSIONS:
                        structured = self._structured_files.get(path) or _StructuredFile(path=path)
                        structured.root_index = root_index
                        self._load_structured_if_changed(structured)
                        seen_structured[path] = structured

        self._text_files = seen_text
        self._structured_files = seen_structured
        # Forget errors for files that no longer exist.
        for path in list(self.file_errors):
            if not os.path.exists(path):
                del self.file_errors[path]

    def all_warnings(self) -> List[str]:
        return list(self.file_errors.values()) + list(self.warnings)

    def _find_text_file(self, key: str, path: str) -> Optional[_TextFile]:
        for text_file in self._text_files.get(key, []):
            if text_file.path == path:
                return text_file
        return None

    # -- loading ----------------------------------------------------------------
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
                    entries.append(Entry(text=parsed[0], weight=parsed[1], origin=text_file.path, key=text_file.key))
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
        self._walk_structured(data, [], structured)

    def _walk_structured(self, data, key_parts: List[str], structured: _StructuredFile) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                self._walk_structured(value, key_parts + [str(key)], structured)
            return
        if isinstance(data, list) and key_parts:
            key = normalise_key("/".join(key_parts))
            origin = f"{structured.path}::{key}"
            entries = structured.keys.setdefault(key, [])
            for item in data:
                entry = self._entry_from_item(item, origin, key)
                if entry:
                    entries.append(entry)

    @staticmethod
    def _entry_from_item(item, origin: str, key: str) -> Optional[Entry]:
        if isinstance(item, str):
            parsed = parse_text_line(item)
            return Entry(text=parsed[0], weight=parsed[1], origin=origin, key=key) if parsed else None
        if isinstance(item, (int, float)):
            return Entry(text=str(item), origin=origin, key=key)
        if isinstance(item, dict) and item.get("text"):
            raw_tags = item.get("tags") or []
            if isinstance(raw_tags, str):
                raw_tags = [tag for tag in re.split(r"[,;]", raw_tags)]
            tags = frozenset(str(tag).strip().lower() for tag in raw_tags if str(tag).strip())
            try:
                weight = float(item.get("weight", 1.0))
            except (TypeError, ValueError):
                weight = 1.0
            return Entry(text=str(item["text"]).strip(), weight=weight, tags=tags, origin=origin, key=key)
        return None

    # -- lookup -----------------------------------------------------------------
    def all_keys(self) -> List[str]:
        self.refresh()
        keys = set(self._text_files.keys())
        for structured in self._structured_files.values():
            keys.update(structured.keys.keys())
        return sorted(keys)

    def has(self, name: str) -> bool:
        return bool(self._matching_keys(normalise_key(name)))

    def _matching_keys(self, key: str) -> List[str]:
        keys = self.all_keys()
        if not key:
            return []
        if any(char in key for char in "*?"):
            return [candidate for candidate in keys if fnmatch.fnmatchcase(candidate, key)]
        if key in keys:
            return [key]
        suffix = "/" + key
        deeper = [candidate for candidate in keys if candidate.endswith(suffix)]
        if deeper:
            return deeper
        # A folder name stands for everything inside it: __materials__ == __materials/**__
        # (only reached when no list of that exact name exists, so a real list always wins).
        inside = [candidate for candidate in keys
                  if candidate.startswith(key + "/") or ("/" + key + "/") in candidate]
        if inside:
            return inside
        if "/" not in key:
            return []
        # Relocated pack: the folder part of the reference does not exist under that name.
        expected_folder, last_segment = key.rsplit("/", 1)
        expected_folder = expected_folder.rsplit("/", 1)[-1]
        if len(expected_folder) < 3:
            return []
        relocated = [
            candidate for candidate in keys
            if candidate.endswith("/" + last_segment)
            and expected_folder in candidate.rsplit("/", 1)[0].rsplit("/", 1)[-1]
        ]
        return relocated if len(relocated) == 1 else []

    def _entries_for_key(self, key: str) -> List[Entry]:
        by_root: Dict[int, List[Entry]] = {}
        for text_file in self._text_files.get(key, []):
            self._load_text_if_changed(text_file)
            if text_file.entries:
                by_root.setdefault(text_file.root_index, []).extend(text_file.entries)
        for structured in self._structured_files.values():
            found = structured.keys.get(key)
            if found:
                by_root.setdefault(structured.root_index, []).extend(found)
        if not by_root:
            return []
        if self.merge_roots:
            return [entry for root_index in sorted(by_root) for entry in by_root[root_index]]
        return by_root[min(by_root)]  # highest-priority folder that has this key wins

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

    def lookup(self, name: str) -> List[Entry]:
        """All entries for a wildcard name (exact, glob, or depth-agnostic). Empty list when unknown."""
        entries: List[Entry] = []
        for key in self._matching_keys(normalise_key(name)):
            entries.extend(self._entries_for_key(key))
        return entries

    def query_tags(self, expression: str, scope: str = "") -> List[Entry]:
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
            candidates = self.lookup(scope if any(c in scope for c in "*?") else scope)
            if not candidates:
                candidates = self.lookup(scope.rstrip("/") + "/**")
        else:
            # Only structured files can carry tags; never force-load large .txt packs for a tag search.
            self.refresh()
            candidates = []
            for structured in self._structured_files.values():
                for key_entries in structured.keys.values():
                    candidates.extend(key_entries)

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

    def stats(self) -> Dict[str, int]:
        keys = self.all_keys()
        tagged = 0
        total = 0
        for key in keys:
            for entry in self._entries_for_key(key):
                total += 1
                if entry.tags:
                    tagged += 1
        return {"folders": len(self.search_paths), "wildcards": len(keys), "entries": total, "tagged_entries": tagged}
