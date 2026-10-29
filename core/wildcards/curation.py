"""
Curation: the catalog's automatic judgement plus the user's own, in one object the library asks.

The user's judgement lives in `_catalog_user.yaml` in each search folder, written by the list viewer
(stars, hide, drop) and fine to edit by hand. The indexer never touches it.

    lists:
      "mrweazsfwildcardssfw_v30glamour/hair_colors":
        stars: 5                  # 1..5; ranks lists (slot buttons, ambiguous names)
        name: "Hair colours, long"
      "cushyswildcard_v6/pose":
        hidden: true              # never picked by a bare name, glob or slot; __exact/key__ still works
        slot: hair_color          # offered on this Composer button (set in the wildcard review), whatever its name
      "thegenesisenginea_v10/the genesis engine/camera":
        nsfw: off                 # the list's level, overrides folder/name/catalog (off | suggestive | nudity | explicit)
        ratings: {lace boyshorts: off}   # one entry's level in this list (overrides its words)
      "thepromptbuilder_v21ponyillustrious/face_expression":
        drop: [Sarcasm, Smug]     # these entries are never picked (case-insensitive)
    favorites: []
    ratings:                      # an entry's level in every list (overrides its words)
      Naked Mole Rat: off

What the library asks (see WildcardLibrary.curation):
    hidden(key)   dropped(key)   nsfw_rating(key) -> 0..3 / None   entry_rating(key, text) -> 0..3 / None
    score(key) -> 0..1   version

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import os
import tempfile
import threading
import time
from typing import Dict, List, Optional, Set

from .library import NSFW_EXPLICIT, NSFW_LEVELS, nsfw_level, strip_nsfw_prefix

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

OVERLAY_FILE = "_catalog_user.yaml"
RECHECK_SECONDS = 2.0      # how often hand edits to the overlay files are looked for
_HEADER = (
    "# Your curation of the wildcard lists in this folder: stars, hidden lists, dropped entries.\n"
    "# Written by the Wildcard Composer's list viewer; safe to edit by hand. See docs/PROMPT_BUILDER_GUIDE.md.\n"
)


class UserOverlay:
    """_catalog_user.yaml of one folder. Re-read when the file changes on disk."""

    def __init__(self, root: str):
        self.root = root
        self.path = os.path.join(root, OVERLAY_FILE)
        self.data: Dict = {"lists": {}, "favorites": [], "ratings": {}}
        self._mtime = None
        self.error = ""
        self.reload_if_changed()

    def reload_if_changed(self) -> bool:
        try:
            mtime = os.path.getmtime(self.path)
        except OSError:
            mtime = None
        if mtime == self._mtime:
            return False
        self._mtime = mtime
        data: Dict = {}
        if mtime is not None and yaml is not None:
            try:
                with open(self.path, "r", encoding="utf-8") as handle:
                    data = yaml.safe_load(handle) or {}
                self.error = ""
            except Exception as error:      # a hand-edit typo must not break wildcard runs
                self.error = f"{self.path}: {error}"
                data = {}
        lists = data.get("lists") if isinstance(data, dict) else None
        ratings = data.get("ratings") if isinstance(data, dict) else None
        aliases = data.get("aliases") if isinstance(data, dict) else None
        self.data = {
            "lists": {str(k).strip().lower(): (v if isinstance(v, dict) else {}) for k, v in (lists or {}).items()},
            "favorites": [str(k).lower() for k in (data.get("favorites") or [])] if isinstance(data, dict) else [],
            "ratings": {str(k).strip(): v for k, v in ratings.items() if str(k).strip()} if isinstance(ratings, dict) else {},
            # old name -> new name, written when the wildcard review renames a list
            "aliases": {str(k).strip().lower(): str(v).strip().lower() for k, v in aliases.items() if str(k).strip() and str(v).strip()}
            if isinstance(aliases, dict) else {},
        }
        return True

    def list(self, key: str) -> Dict:
        return self.data["lists"].get(key, {})

    def save(self) -> None:
        if yaml is None:
            raise RuntimeError("PyYAML is not installed")
        lists = {key: value for key, value in sorted(self.data["lists"].items()) if value}
        payload = {"lists": lists, "favorites": self.data.get("favorites", [])}
        if self.data.get("ratings"):
            payload["ratings"] = dict(sorted(self.data["ratings"].items(), key=lambda item: item[0].casefold()))
        if self.data.get("aliases"):
            payload["aliases"] = dict(sorted(self.data["aliases"].items()))
        text = _HEADER + yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120)
        directory = os.path.dirname(self.path)
        handle, temporary = tempfile.mkstemp(prefix="_catalog_user.", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as out:
                out.write(text)
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)
        self._mtime = os.path.getmtime(self.path)


class Curation:
    """
    catalog: a CatalogSet (or None). overlays are created for every search folder of the library.
    `version` changes whenever an answer may change, so the library rebuilds its cached views.
    """

    def __init__(self, library, catalog=None):
        self.library = library
        self.catalog = catalog
        self.overlays: Dict[str, UserOverlay] = {root: UserOverlay(root) for root in library.search_paths}
        self._lock = threading.Lock()
        self._own_version = 0
        self._dropped_cache: Dict[str, Set[str]] = {}
        self._ratings_cache: Dict[str, Dict[str, int]] = {}     # key ("" = every list) -> {casefolded text: level}
        self._slot_cache: Optional[Dict[str, List[str]]] = None  # Composer button id -> keys you assigned to it
        self._last_check = 0.0

    # -- bookkeeping ----------------------------------------------------------------
    @property
    def version(self) -> int:
        changed = False
        now = time.time()
        if now - self._last_check >= RECHECK_SECONDS:
            self._last_check = now
            for overlay in self.overlays.values():
                changed = overlay.reload_if_changed() or changed
        if changed:
            self._own_version += 1
            self._dropped_cache = {}
            self._ratings_cache = {}
            self._slot_cache = None
            self._alias_cache = None
        return self._own_version * 1_000_003 + (self.catalog.version if self.catalog is not None else 0)

    def _entry(self, key: str) -> Dict:
        """
        The user's settings for a key: the highest-priority folder that says anything wins. The list viewer saves
        under the name a list answers to (pack/x for _nsfw/pack/x, prompts/x for _prompts/x); the library asks with
        the real key. Both spellings find the same settings.
        """
        self.version        # picks up hand edits (checked at most every RECHECK_SECONDS)
        spellings = [key]
        name = strip_nsfw_prefix(key)
        if name != key:
            spellings.append(name)
        for spelling in spellings:
            for root in self.library.search_paths:
                overlay = self.overlays.get(root)
                if overlay is not None:
                    found = overlay.list(spelling)
                    if found:
                        return found
        return {}

    def _row(self, key: str):
        return self.catalog.row(key) if self.catalog is not None else None

    # -- what the library asks --------------------------------------------------------
    def hidden(self, key: str) -> bool:
        return bool(self._entry(key).get("hidden"))

    def dropped(self, key: str) -> Set[str]:
        cached = self._dropped_cache.get(key)
        if cached is None:
            cached = {str(item).strip().casefold() for item in (self._entry(key).get("drop") or []) if str(item).strip()}
            self._dropped_cache[key] = cached
        return cached

    def nsfw_rating(self, key: str) -> Optional[int]:
        """
        A list's level 0..3 when the user or the catalog says: the user's nsfw: <level> wins; the catalog rates a
        list explicit by its content. None = no opinion (the folder / name rules decide).
        """
        user = self._entry(key).get("nsfw", "")
        if isinstance(user, bool) or str(user or "").strip():
            return nsfw_level(user)
        row = self._row(key)
        if row is not None and row.nsfw == "explicit" and row.nsfw_source == "content":
            return NSFW_EXPLICIT
        return None

    def entry_rating(self, key: str, text: str) -> Optional[int]:
        """An entry's level when the user set one: in this list's ratings, else the top-level ratings. None = its words decide."""
        folded = text.strip().casefold()
        own = self._ratings_for(key)
        if folded in own:
            return own[folded]
        every = self._ratings_for("")
        return every.get(folded)

    def _ratings_for(self, key: str) -> Dict[str, int]:
        self.version        # picks up hand edits
        cached = self._ratings_cache.get(key)
        if cached is not None:
            return cached
        if key:
            raw = self._entry(key).get("ratings") or {}
            merged = {str(t).strip().casefold(): nsfw_level(v) for t, v in raw.items()} if isinstance(raw, dict) else {}
        else:
            merged = {}
            for root in reversed(self.library.search_paths):        # the highest-priority folder wins
                overlay = self.overlays.get(root)
                if overlay is not None:
                    merged.update({str(t).strip().casefold(): nsfw_level(v) for t, v in overlay.data.get("ratings", {}).items()})
        self._ratings_cache[key] = merged
        return merged

    def slot_keys(self, slot_id: str) -> List[str]:
        """Keys you assigned to a Composer button (`slot:` in _catalog_user.yaml, highest-priority folder first)."""
        self.version        # picks up hand edits
        if self._slot_cache is None:
            by_slot: Dict[str, List[str]] = {}
            for root in self.library.search_paths:
                overlay = self.overlays.get(root)
                if overlay is None:
                    continue
                for key, settings in overlay.data.get("lists", {}).items():
                    slots = settings.get("slot") or []
                    for slot in ([slots] if isinstance(slots, str) else slots):     # one button id, or several
                        slot = str(slot or "").strip()
                        if slot and not settings.get("hidden") and key not in by_slot.get(slot, []):
                            by_slot.setdefault(slot, []).append(key)
            self._slot_cache = by_slot
        return list(self._slot_cache.get(slot_id, []))

    def alias_of(self, name: str) -> Optional[str]:
        """The new name of a list the wildcard review renamed (aliases: in _catalog_user.yaml), else None."""
        self.version        # picks up hand edits
        cache = getattr(self, "_alias_cache", None)
        if cache is None:
            cache = {}
            for root in reversed(self.library.search_paths):        # the highest-priority folder wins
                overlay = self.overlays.get(root)
                if overlay is not None:
                    cache.update(overlay.data.get("aliases") or {})
            self._alias_cache = cache
        return cache.get(name)

    def stars(self, key: str) -> int:
        try:
            return max(0, min(5, int(self._entry(key).get("stars", 0) or 0)))
        except (TypeError, ValueError):
            return 0

    def quality(self, key: str) -> float:
        row = self._row(key)
        return row.quality if row is not None else 0.5

    def score(self, key: str) -> float:
        """0..1 for ordering: the user's stars when given, else the catalog's quality."""
        stars = self.stars(key)
        if stars:
            return 0.5 + stars / 10.0     # any starred list outranks unstarred ones (quality <= 1 but ~0.9 max)
        return self.quality(key) * 0.5

    # -- what the list viewer changes ----------------------------------------------------
    def root_for_key(self, key: str) -> Optional[str]:
        """The folder whose list the engine uses for this key (where its curation belongs)."""
        sources = self.library.catalog_sources()
        # A name a list answers to (pack/x, prompts/x) is found through its real keys (_nsfw/pack/x, _prompts/x).
        wanted = [key] + [real for real in self.library.real_keys(key) if real != key]
        for root in self.library.search_paths:
            for _relative, (_path, keys) in sources.get(root, {}).items():
                if any(real in keys for real in wanted):
                    return root
        return None

    def update(self, key: str, root: Optional[str] = None, **changes) -> Dict:
        """
        Change the user's settings for a key and save that folder's _catalog_user.yaml.
        changes: stars (0 clears), hidden (bool), nsfw (a level name, '' clears), name (str),
                 drop (str, add), undrop (str, remove), rate ({"text": ..., "level": ...}; level '' clears).
        """
        with self._lock:
            root = root or self.root_for_key(key)
            if root is None or root not in self.overlays:
                raise KeyError(f"no folder holds '{key}'")
            overlay = self.overlays[root]
            overlay.reload_if_changed()
            entry = dict(overlay.list(key))
            if "stars" in changes:
                stars = int(changes["stars"] or 0)
                if stars:
                    entry["stars"] = max(1, min(5, stars))
                else:
                    entry.pop("stars", None)
            if "hidden" in changes:
                if changes["hidden"]:
                    entry["hidden"] = True
                else:
                    entry.pop("hidden", None)
            if "nsfw" in changes:
                if str(changes["nsfw"] or "").strip():
                    entry["nsfw"] = NSFW_LEVELS[nsfw_level(changes["nsfw"])]
                else:
                    entry.pop("nsfw", None)
            if changes.get("rate"):
                text = str(changes["rate"].get("text", "")).strip()
                ratings = {str(t): v for t, v in (entry.get("ratings") or {}).items() if str(t).casefold() != text.casefold()}
                if text and str(changes["rate"].get("level", "") or "").strip():
                    ratings[text] = NSFW_LEVELS[nsfw_level(changes["rate"]["level"])]
                if ratings:
                    entry["ratings"] = ratings
                else:
                    entry.pop("ratings", None)
            if "name" in changes:
                if changes["name"]:
                    entry["name"] = str(changes["name"])
                else:
                    entry.pop("name", None)
            drops: List[str] = list(entry.get("drop") or [])
            if changes.get("drop"):
                text = str(changes["drop"]).strip()
                if text and text.casefold() not in {d.casefold() for d in drops}:
                    drops.append(text)
            if changes.get("undrop"):
                text = str(changes["undrop"]).strip().casefold()
                drops = [d for d in drops if d.casefold() != text]
            if drops:
                entry["drop"] = drops
            else:
                entry.pop("drop", None)
            if entry:
                overlay.data["lists"][key] = entry
            else:
                overlay.data["lists"].pop(key, None)
            overlay.save()
            self._own_version += 1
            self._dropped_cache = {}
            self._ratings_cache = {}
            return entry
