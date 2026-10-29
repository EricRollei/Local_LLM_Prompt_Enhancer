"""
Wildcard review: a small local web server (this machine only) for paging through the wildcard lists of
A:\\Models\\wildcards and deciding Keep / Dump / Same as / Unsure, with the AI judge's opinion pre-filled
(dev/wildcard_judge.py, table `judgements` of _triage.sqlite). Built like the LoRA card editor.

    python tools/wildcard_review/server.py            then open http://127.0.0.1:8766
    (or run tools/wildcard_review/wildcard_review.bat)
    python tools/wildcard_review/server.py --undo tools/wildcard_review/manifests/<manifest>.json

Decisions are saved as you click, to the `reviews` table of A:\\Models\\wildcards\\_triage.sqlite. Nothing touches
the wildcard files or _catalog_user.yaml until you press Apply (preview first). Apply does, per list:
    dump        hidden: true                       (gone from buttons, globs and bare names; __exact/name__ still works)
    same as     hidden: true, same_as: <the better list>
    keep        hidden removed; slot: <Composer buttons>; nsfw: <level> (each only when you set it)
                rename (when you ticked it): a .txt list is renamed in its folder; a list inside a YAML / JSON file is
                written out as <folder>/<new name>.txt and the old key is hidden (the pack file is not edited). Its
                settings, buttons and review follow it, and the old name stays an alias (aliases: in
                _catalog_user.yaml), so saved workflows and templates keep working.
    unsure      nothing
"Move dumped files" (preview first) moves whole dumped .txt files, and YAML / JSON files whose every list you
dumped, to A:\\Models\\wildcards\\_dumped\\<same path> (a folder the engine skips). Dumped keys inside files that
also hold kept lists stay hidden. Renames and moves write a manifest in tools/wildcard_review/manifests (--undo).

Your own Composer buttons (builders_user/my_buttons.yaml) are offered next to the shipped ones, and "+ new button"
makes one (label + section) with the list on it. A list can sit on several buttons.

Endpoints (JSON unless noted)
    GET  /                          the page (review.html)
    GET  /api/meta                  facets, Composer buttons by section, counts, library state
    GET  /api/queue?order=&facet=&verdict=&status=&source=&q=
    GET  /api/list?key=&seed=       one list: catalog row, judge, your review, a sample of entries, similar lists
    GET  /api/entries?key=&q=&offset=&limit=
    GET  /api/page?keys=k1,k2,...   rows for the grid view (samples only, fast)
    POST /api/review                {key, decision, same_as?, button?, name?, nsfw?, note?}   (button: ids, comma-joined)
    POST /api/review_many           {items: [{key, decision}]}
    POST /api/button                {label, section, key?}   -> a new button in my_buttons.yaml (with that list on it)
    GET  /api/apply_preview         what Apply would write and rename
    POST /api/apply                 write _catalog_user.yaml, do the renames
    GET  /api/dump_preview          what "Move dumped files" would move
    POST /api/dump_move             move them to _dumped

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import json
import os
import random
import re
import shutil
import sqlite3
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, PACKAGE)
from core.wildcards import library as L                    # noqa: E402
from core.wildcards.curation import UserOverlay            # noqa: E402
from core.builder.slots import button_id, clean_button, read_buttons, write_buttons   # noqa: E402
from core.builder.layout import layout_move, read_layout, write_layout                # noqa: E402
from core.builder.merge import fold_key, merge_entries, merged_key, merged_name, merged_path, write_merged   # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

# WCR_ROOT / WCR_BUTTONS / WCR_MANIFESTS let the checks (dev/verify_wildcard_review.py) run on a temporary library.
LIBRARY_ROOT = os.environ.get("WCR_ROOT", r"A:\Models\wildcards")
TRIAGE = os.path.join(LIBRARY_ROOT, "_triage.sqlite")
BUILDERS = os.path.join(PACKAGE, "builders", "prompt.yaml")
MY_BUTTONS = os.environ.get("WCR_BUTTONS", os.path.join(PACKAGE, "builders_user", "my_buttons.yaml"))
MANIFESTS = os.environ.get("WCR_MANIFESTS", os.path.join(HERE, "manifests"))
LAYOUT = os.environ.get("WCR_LAYOUT", os.path.join(PACKAGE, "builders_user", "button_layout.yaml"))
MERGE_PREVIEW_MAX = 4000              # rows the merge preview sends (the merge itself uses every entry)
DUMPED_FOLDER = "_dumped"
STRUCTURED = (".yaml", ".yml", ".json")
PORT = 8766
SAMPLE = 36
DECISIONS = ("keep", "dump", "same", "unsure", "merge")
MY_GROUP = "My buttons"

REVIEWS = """
CREATE TABLE IF NOT EXISTS reviews (
    key TEXT PRIMARY KEY, decision TEXT, same_as TEXT, button TEXT, name TEXT, nsfw TEXT, note TEXT,
    how TEXT, decided_at TEXT, applied_at TEXT
);
"""
# added 2026-10-06: where Move dumped put the file; the old key; a merge's partners (comma-joined), name, unticked
# entries (JSON list) and the merged list a source went into
EXTRA_COLUMNS = ("moved_to", "renamed_from", "merge_with", "merge_name", "merge_drop", "merged_into")

# -- the local LLM (LM Studio, OpenAI-compatible; the same server dev/wildcard_judge.py uses) -----------------------------
LLM_URL = os.environ.get("WCR_LLM", "http://localhost:1234/v1")
LLM_DEFAULT_MODEL = "qwen3-vl-8b-instruct-abliterated-v2.0"
JUNK_CHUNK = 120                     # lines per Suggest-junk request
JUNK_MAX = 1200                      # lines Suggest junk reads at most
GEN_BATCH = 40                       # new lines per generate request
NAMEY = re.compile(r"\b(artists?|painters?|photographers?|illustrators?|designers?|directors?|authors?|writers?|"
                   r"celebrit\w*|actors?|actress\w*|brands?|cit(y|ies)|towns?|villages?|landmarks?|streets?|"
                   r"restaurants?|people|persons?|names?|surnames?|characters?)\b", re.I)


def llm_models() -> List[str]:
    import requests
    response = requests.get(LLM_URL + "/models", timeout=6)
    response.raise_for_status()
    return [m.get("id") for m in response.json().get("data") or [] if m.get("id")]


def llm_json(model: str, system: str, user: str, schema: Dict[str, Any], max_tokens: int = 2000,
             temperature: float = 0.0) -> Dict[str, Any]:
    """One chat call that must answer with JSON matching `schema`."""
    import requests
    body = {"model": model or LLM_DEFAULT_MODEL, "temperature": temperature, "max_tokens": max_tokens,
            "response_format": {"type": "json_schema", "json_schema": {"name": "answer", "strict": True, "schema": schema}},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    response = requests.post(LLM_URL + "/chat/completions", json=body, timeout=600)
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"] or ""
    text = re.sub(r"(?s)<think>.*?</think>", "", text).strip()
    try:
        return json.loads(text)
    except ValueError:
        found = re.search(r"(?s)\{.*\}", text)
        if found:
            return json.loads(found.group(0))
        raise ValueError(f"the model did not answer with JSON: {text[:200]}")


JUNK_SYSTEM = """You clean wildcard lists for an image-prompt tool. A wildcard list holds interchangeable values of ONE kind
(hair colours, castles, film stocks ...); the tool picks one at random. You are told what the list is meant to hold and
shown its numbered lines. Most lines fit. Return the numbers of the lines that clearly do NOT belong: a different kind of
thing, garbage or fragments, prompt tags or weights, instructions, URLs, empty filler. Unusual but valid members of the
kind DO belong. When in doubt, leave a line out of your answer. If every line fits, return an empty list."""

GEN_SYSTEM = """You write wildcard lists for an image-prompt tool. A wildcard list holds interchangeable values of ONE kind;
the tool picks one at random and puts it into an image prompt, so every item must work on its own in a sentence like
"a photo of ..., <item>". Write NEW items of exactly the kind described, in the same form and length as the examples:
varied, concrete, visual, no duplicates or near-duplicates of the examples or of each other, no numbering, no
explanations. Only real, well-known names when the list is of real people, places or brands; never invent them."""

STYLES = {"words": "a single word or a two-word name", "short": "a short phrase of two to five words",
          "descriptive": "a descriptive phrase of six to fifteen words"}


# Lists the review covers: the judged candidates, plus the 5-7 entry and NSFW lists judged with --extra.
SOURCE_SQL = """
case when t.stage1_bucket = 'candidate' then 'candidate'
     when t.stage1_bucket = 'nsfw' then 'nsfw'
     else 'small' end
"""


def _words(text: str) -> set:
    return {w for w in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(w) > 2}


def slug(name: str) -> str:
    """'Bird species (real)' -> 'bird_species_real': the file name a renamed list gets."""
    return re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")[:80]


def button_ids(value: Any) -> List[str]:
    """The review's button field: one id, several comma-joined, or a list."""
    items = value if isinstance(value, list) else str(value or "").split(",")
    return [str(item).strip() for item in items if str(item).strip()]


def _abs(file: str) -> str:
    return os.path.normpath(file if os.path.isabs(file) else os.path.join(LIBRARY_ROOT, file))


def _rel(path: str) -> str:
    return os.path.relpath(path, LIBRARY_ROOT).replace("\\", "/")


class Review:
    def __init__(self, load_library: bool = True):
        self.lock = threading.Lock()
        self.library: Optional[L.WildcardLibrary] = None
        self.library_state = "loading"
        with self.connect() as connection:
            connection.executescript(REVIEWS)
            have = {row[1] for row in connection.execute("pragma table_info(reviews)")}
            for column in EXTRA_COLUMNS:
                if column not in have:
                    connection.execute(f"alter table reviews add column {column} TEXT")
        self._rows: Optional[List[Dict[str, Any]]] = None
        self._rows_at = 0.0
        if load_library:
            threading.Thread(target=self._load_library, name="wildcard-review-library", daemon=True).start()
        else:
            self._load_library()

    # -- setup -------------------------------------------------------------------------------------------------------
    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(TRIAGE, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _load_library(self) -> None:
        try:
            started = time.time()
            library = L.WildcardLibrary([LIBRARY_ROOT])
            library.refresh(force=True)
            self.library = library
            self.library_state = f"ready ({time.time() - started:.0f} s)"
        except Exception as error:          # the page still works from the catalog samples
            self.library_state = f"failed: {error}"
        print(f"[review] library {self.library_state}")

    def _builder_yaml(self) -> Dict[str, Any]:
        if yaml is None:
            return {}
        try:
            with open(BUILDERS, "r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}
        except OSError:
            return {}

    def sections(self) -> List[Dict[str, Any]]:
        """The Composer's prompt sections (lines), in the builder's order, with the button headings each shows."""
        out = []
        for block in self.buttons():
            groups = []
            for button in block["buttons"]:
                if button["group"] and button["group"] not in groups:
                    groups.append(button["group"])
            if MY_GROUP not in groups:
                groups.insert(0, MY_GROUP)
            out.append({"section": block["section"], "label": block["label"], "groups": groups})
        listed = {s["section"] for s in out}
        for part in self._builder_yaml().get("parts") or []:
            if part.get("section") not in listed:
                out.append({"section": part.get("section"), "label": part.get("label", part.get("section")), "groups": [MY_GROUP]})
        return out

    def buttons(self) -> List[Dict[str, Any]]:
        """The Composer's buttons by section: your own (my_buttons.yaml, first) and the shipped ones (prompt.yaml)."""
        data = self._builder_yaml()
        labels = {part.get("section"): part.get("label", part.get("section")) for part in data.get("parts") or []}
        everything = [dict(id=b["id"], label=b["label"], group=MY_GROUP, mine=True, section=b.get("section"))
                      for b in read_buttons(MY_BUTTONS)]
        for block in data.get("slots") or []:
            everything += [dict(id=s.get("id"), label=s.get("label", s.get("id")), group=s.get("group", ""), mine=False,
                                section=block.get("section")) for s in block.get("slots") or []]
        try:
            moved = (read_layout(LAYOUT) or {}).get("moved") or {}      # your Arrange moves (section / heading)
        except Exception:
            moved = {}
        for button in everything:
            move = moved.get(button["id"]) or {}
            button["section"] = move.get("section") or button["section"]
            if "group" in move:
                button["group"] = move["group"] or (MY_GROUP if button["mine"] else "")
        out = []
        for section in list(labels) + sorted({b["section"] for b in everything} - set(labels)):
            own = [b for b in everything if b["section"] == section]
            if own:
                own.sort(key=lambda b: (b["group"] != MY_GROUP, ))   # yours first, the rest in their shipped order
                out.append({"section": section, "label": labels.get(section, section),
                            "buttons": [{k: b[k] for k in ("id", "label", "group", "mine")} for b in own]})
        return out

    def create_button(self, label: str, section: str, key: str = "", group: str = "") -> Dict[str, Any]:
        """A new button in my_buttons.yaml with this list on it, shown under `group` (a heading of that section)."""
        label = (label or "").strip()
        if not label:
            return {"ok": False, "error": "a button needs a label"}
        if section not in {s["section"] for s in self.sections()}:
            return {"ok": False, "error": f"unknown section '{section}'"}
        name = L.strip_nsfw_prefix(key) if key else ""
        raw = {"label": label, "section": section, "lists": [name] if name else [], "search": "" if name else label}
        button = clean_button(raw)
        if button is None:
            return {"ok": False, "error": "could not make that button"}
        buttons = read_buttons(MY_BUTTONS)
        taken = {b["id"] for b in buttons} | {s.get("id") for block in self._builder_yaml().get("slots") or []
                                               for s in block.get("slots") or []}
        button["id"] = button_id(label, taken)
        buttons.append(button)
        write_buttons(MY_BUTTONS, buttons)
        group = (group or "").strip()
        if group and group != MY_GROUP:
            # Under one of the section's headings: the same record the Composer's Arrange mode writes.
            write_layout(LAYOUT, layout_move(read_layout(LAYOUT), button["id"], section=section, group=group))
        return {"ok": True, "button": dict(button, group=group or MY_GROUP)}

    # -- data --------------------------------------------------------------------------------------------------------
    def rows(self, fresh: bool = False) -> List[Dict[str, Any]]:
        """Every list under review with its latest judgement and your review (cached a few seconds)."""
        with self.lock:
            if self._rows is not None and not fresh and time.time() - self._rows_at < 5:
                return self._rows
        sql = f"""
            select t.key, t.file, t.pack, t.display, t.kind, t.entries, t.nsfw as catalog_nsfw, t.facet as catalog_facet,
                   {SOURCE_SQL} as source,
                   j.model, j.dimension, j.facet, j.coherence, j.visual, j.slot_form, j.era_specific, j.verdict,
                   j.reason, j.confidence,
                   r.decision, r.same_as, r.button, r.name, r.nsfw as review_nsfw, r.how, r.decided_at, r.applied_at,
                   r.moved_to, r.renamed_from, r.merge_with, r.merge_name, r.merge_drop, r.merged_into
            from triage t
            join judgements j on j.key = t.key
                and j.judged_at = (select max(j2.judged_at) from judgements j2 where j2.key = t.key)
            left join reviews r on r.key = t.key
        """
        with self.connect() as connection:
            rows = [dict(row) for row in connection.execute(sql)]
        seen, unique = set(), []
        for row in rows:                       # two models judged the same list at the same minute: keep one
            if row["key"] not in seen:
                seen.add(row["key"])
                unique.append(row)
        with self.lock:
            self._rows, self._rows_at = unique, time.time()
        return unique

    def _forget_rows(self) -> None:
        with self.lock:
            self._rows = None

    def meta(self) -> Dict[str, Any]:
        rows = self.rows()
        facets: Dict[str, int] = {}
        decided: Dict[str, int] = {}
        hidden = moved = renamed = 0
        for row in rows:
            facets[row["facet"] or "(none)"] = facets.get(row["facet"] or "(none)", 0) + 1
            if row["decision"]:
                decided[row["decision"]] = decided.get(row["decision"], 0) + 1
            if row["decision"] in ("dump", "same", "merge") and row["applied_at"]:
                hidden += 1
            moved += bool(row["moved_to"])
            renamed += bool(row["renamed_from"])
        return {"total": len(rows), "decided": decided, "facets": sorted(facets.items()),
                "hidden": hidden, "moved": moved, "renamed": renamed,
                "sources": {s: sum(1 for r in rows if r["source"] == s) for s in ("candidate", "small", "nsfw")},
                "buttons": self.buttons(), "sections": self.sections(),
                "library": self.library_state, "levels": list(L.NSFW_LEVELS)}

    def queue(self, order: str, facet: str, verdict: str, status: str, source: str, query: str) -> List[Dict[str, Any]]:
        items = []
        wanted = (query or "").strip().lower()
        for row in self.rows():
            if facet and (row["facet"] or "(none)") != facet:
                continue
            if verdict and row["verdict"] != verdict:
                continue
            if source and row["source"] != source:
                continue
            if status == "todo" and row["decision"]:
                continue
            if status in DECISIONS and row["decision"] != status:
                continue
            if wanted and wanted not in row["key"] and wanted not in (row["dimension"] or "").lower():
                continue
            items.append({"key": row["key"], "dim": row["dimension"] or "", "facet": row["facet"] or "",
                          "verdict": row["verdict"] or "", "visual": row["visual"], "coherence": row["coherence"],
                          "entries": row["entries"], "source": row["source"], "decision": row["decision"] or "",
                          "pack": row["pack"] or "", "moved": bool(row["moved_to"]),
                          "hidden": row["decision"] in ("dump", "same", "merge") and bool(row["applied_at"])})
        if order == "junk":            # most likely junk first: judge says purge, then not visual, then incoherent
            items.sort(key=lambda i: (i["verdict"] != "purge", i["visual"] or 0, i["coherence"] or 0, i["key"]))
        elif order == "pack":
            items.sort(key=lambda i: (i["pack"], i["key"]))
        elif order == "size":
            items.sort(key=lambda i: (-(i["entries"] or 0), i["key"]))
        else:                          # facet, then what the lists are, so look-alikes sit together
            items.sort(key=lambda i: (i["facet"], i["dim"].lower(), i["key"]))
        return items

    def _entries(self, key: str) -> List[Any]:
        library = self.library
        if library is None:
            return []
        try:
            return library._entries_for_key(key, nsfw=L.NSFW_EXPLICIT, apply_drops=False)
        except Exception:
            return []

    def _samples(self, row: Dict[str, Any]) -> List[str]:
        with self.connect() as connection:
            found = connection.execute("select samples from triage where key = ?", (row["key"],)).fetchone()
        try:
            return [str(s) for s in json.loads((found["samples"] if found else None) or "[]")]
        except ValueError:
            return []

    def similar(self, row: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Lists that look like the same thing: same facet, shared words in what the judge says they are and in the name."""
        mine = _words(row["dimension"]) | _words(row["key"].rsplit("/", 1)[-1])
        if not mine:
            return []
        scored = []
        for other in self.rows():
            if other["key"] == row["key"] or other["facet"] != row["facet"]:
                continue
            theirs = _words(other["dimension"]) | _words(other["key"].rsplit("/", 1)[-1])
            shared = len(mine & theirs)
            if shared:
                scored.append((shared / len(mine | theirs), other))
        scored.sort(key=lambda pair: -pair[0])
        return [{"key": o["key"], "dim": o["dimension"], "entries": o["entries"], "decision": o["decision"] or "",
                 "verdict": o["verdict"]} for _s, o in scored[:limit]]

    def rename_target(self, key: str, file: str, name: str) -> Optional[Dict[str, Any]]:
        """What renaming this list to `name` does: {kind: rename|split, old, new, path, conflict}. None = no change."""
        new_leaf = slug(name)
        if not new_leaf or not file:
            return None
        path = _abs(file)
        if new_leaf == key.rsplit("/", 1)[-1]:
            return None
        target = os.path.join(os.path.dirname(path), new_leaf + ".txt")
        new_key = L.normalise_key(os.path.splitext(_rel(target))[0])
        kind = "rename" if path.lower().endswith(".txt") else "split"
        conflict = ""
        if os.path.exists(target):
            conflict = f"{_rel(target)} already exists"
        elif self.library is not None and self.library.real_keys(L.strip_nsfw_prefix(new_key)):
            conflict = f"a list called {L.strip_nsfw_prefix(new_key)} already exists"
        elif kind == "rename" and not os.path.exists(path):
            conflict = f"{_rel(path)} is not there (moved?)"
        return {"kind": kind, "old": key, "new": new_key, "path": _rel(target), "from": _rel(path), "conflict": conflict}

    def list_view(self, key: str, seed: int) -> Optional[Dict[str, Any]]:
        row = next((r for r in self.rows() if r["key"] == key), None)
        if row is None:
            return None
        entries = [] if row["moved_to"] else self._entries(key)
        library = self.library
        if entries:
            rng = random.Random(seed)
            shown = entries if len(entries) <= SAMPLE else [entries[i] for i in sorted(rng.sample(range(len(entries)), SAMPLE))]
            gone = self._dropped(key)
            sample = [{"text": e.text, "rating": library.entry_rating(e), "dropped": e.text.strip().casefold() in gone}
                      for e in shown]
            total = len(entries)
            rated = [0, 0, 0, 0]
            for entry in entries:
                rated[library.entry_rating(entry)] += 1
            list_rating = library._view(L.NSFW_EXPLICIT).rating.get(L.strip_nsfw_prefix(key), 0)
        else:
            sample = [{"text": t, "rating": L.nsfw_word_tier(t)} for t in self._samples(row)]
            total, rated, list_rating = row["entries"], None, None
        file = row["file"] or ""
        return {
            "key": key, "name": L.strip_nsfw_prefix(key), "file": _rel(_abs(file)) if file else "",
            "kind_of_file": "txt" if file.lower().endswith(".txt") else "structured",
            "pack": row["pack"], "kind": row["kind"], "entries": total, "source": row["source"],
            "catalog_nsfw": row["catalog_nsfw"], "list_rating": list_rating, "rated": rated,
            "judge": {k: row[k] for k in ("model", "dimension", "facet", "coherence", "visual", "slot_form",
                                          "era_specific", "verdict", "reason", "confidence")},
            "review": {k: row[k] for k in ("decision", "same_as", "button", "name", "review_nsfw", "decided_at",
                                           "applied_at", "moved_to", "renamed_from", "merge_with", "merge_name",
                                           "merge_drop", "merged_into")},
            "sample": sample, "from_library": bool(entries), "similar": self.similar(row),
        }

    def entries(self, key: str, query: str, offset: int, limit: int) -> Dict[str, Any]:
        entries = self._entries(key)
        wanted = (query or "").strip().casefold()
        matched = [e for e in entries if not wanted or wanted in e.text.casefold()]
        library = self.library
        gone = self._dropped(key)
        return {"total": len(entries), "matched": len(matched), "dropped": len(gone),
                "entries": [{"text": e.text, "rating": library.entry_rating(e) if library else 0,
                             "dropped": e.text.strip().casefold() in gone}
                            for e in matched[offset:offset + limit]]}

    # -- quick edits: drops (saved at once) ------------------------------------------------------------------------------
    def _overlay(self) -> UserOverlay:
        overlay = getattr(self, "_overlay_cache", None)
        if overlay is None:
            overlay = self._overlay_cache = UserOverlay(LIBRARY_ROOT)
        overlay.reload_if_changed()
        return overlay

    def _dropped(self, key: str) -> set:
        entry = self._overlay().list(L.strip_nsfw_prefix(key))
        return {str(t).strip().casefold() for t in entry.get("drop") or [] if str(t).strip()}

    def drop(self, key: str, texts: List[str], undrop: bool = False) -> Dict[str, Any]:
        """Drop (or bring back) lines of a list: _catalog_user.yaml drop:, saved now. The file is not edited."""
        name = L.strip_nsfw_prefix(key)
        with self.lock:
            overlay = self._overlay()
            entry = dict(overlay.list(name))
            drops = [str(t) for t in entry.get("drop") or []]
            folded = {t.strip().casefold() for t in drops}
            for text in texts:
                text = str(text).strip()
                if not text:
                    continue
                if undrop:
                    drops = [t for t in drops if t.strip().casefold() != text.casefold()]
                    folded.discard(text.casefold())
                elif text.casefold() not in folded:
                    drops.append(text)
                    folded.add(text.casefold())
            if drops:
                entry["drop"] = drops
            else:
                entry.pop("drop", None)
            if entry:
                overlay.data["lists"][name] = entry
            else:
                overlay.data["lists"].pop(name, None)
            overlay.save()
        return {"ok": True, "dropped": len(drops)}

    def drop_matching(self, key: str, pattern: str, regex: bool, do_it: bool) -> Dict[str, Any]:
        """The lines that have `pattern` (a word, or a regex); with do_it, drop them."""
        pattern = (pattern or "").strip()
        if not pattern:
            return {"ok": True, "matches": []}
        try:
            test = re.compile(pattern, re.I).search if regex else (lambda text: pattern.casefold() in text.casefold())
        except re.error as error:
            return {"ok": False, "error": f"bad pattern: {error}"}
        matches = [e.text for e in self._entries(key) if test(e.text)]
        if do_it and matches:
            self.drop(key, matches)
        return {"ok": True, "matches": matches[:500], "count": len(matches), "dropped": bool(do_it)}

    # -- the local LLM: Suggest junk, New list, Extend -------------------------------------------------------------------
    def suggest_junk(self, key: str, model: str) -> Dict[str, Any]:
        row = next((r for r in self.rows() if r["key"] == key), None)
        meant = (row or {}).get("dimension") or key.rsplit("/", 1)[-1].replace("_", " ")
        gone = self._dropped(key)
        texts = [e.text for e in self._entries(key) if e.text.strip().casefold() not in gone][:JUNK_MAX]
        schema = {"type": "object", "properties": {"off": {"type": "array", "items": {"type": "integer"}}},
                  "required": ["off"], "additionalProperties": False}
        flagged: List[str] = []
        for start in range(0, len(texts), JUNK_CHUNK):
            chunk = texts[start:start + JUNK_CHUNK]
            user = (f"The list is meant to hold: {meant}\nIts name: {key}\n\nLines:\n"
                    + "\n".join(f"{i + 1}. {t}" for i, t in enumerate(chunk)))
            answer = llm_json(model, JUNK_SYSTEM, user, schema, max_tokens=600)
            for number in answer.get("off") or []:
                if isinstance(number, int) and 1 <= number <= len(chunk):
                    flagged.append(chunk[number - 1])
        return {"ok": True, "flagged": flagged, "read": len(texts), "meant": meant}

    def generate(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """One batch of new lines for a list that is being made or extended; repeats are folded away."""
        name = str(body.get("name") or "").strip()
        description = str(body.get("description") or "").strip()
        samples = [str(s).strip() for s in body.get("samples") or [] if str(s).strip()]
        have = [str(s).strip() for s in body.get("have") or [] if str(s).strip()]
        style = STYLES.get(str(body.get("style") or "short"), STYLES["short"])
        count = max(5, min(80, int(body.get("count") or GEN_BATCH)))
        if not (description or samples or name):
            return {"ok": False, "error": "say what the list holds, or give a few samples"}
        shown_samples = samples[:25]
        already = (have + samples)[-150:]
        user = (f"List name: {name or '(none)'}\nWhat it holds: {description or '(see the examples)'}\n"
                f"Each item is {style}.\n\nExamples of the kind and form wanted:\n"
                + "\n".join(f"- {s}" for s in shown_samples)
                + ("\n\nAlready in the list, do not repeat or rephrase any of these:\n" + "\n".join(f"- {s}" for s in already)
                   if already else "")
                + f"\n\nWrite {count} NEW items.")
        schema = {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "string"}}},
                  "required": ["items"], "additionalProperties": False}
        answer = llm_json(str(body.get("model") or ""), GEN_SYSTEM, user, schema, max_tokens=60 * count + 200,
                          temperature=float(body.get("temperature") or 0.9))
        seen = {fold_key(s) for s in have + samples}
        fresh = []
        for item in answer.get("items") or []:
            text = re.sub(r"^\s*(?:[-*\u2022]|\d+[.)])\s*", "", str(item)).strip().strip('"').strip()
            fold = fold_key(text)
            if text and fold and fold not in seen and len(text) <= 300:
                seen.add(fold)
                fresh.append(text)
        warn = bool(NAMEY.search(f"{name} {description}"))
        return {"ok": True, "items": fresh, "asked": count, "warn_names": warn}

    def save_list(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Save a made or extended list to mine/<first button, else 'generated'>/<name>.txt and put it on its buttons."""
        entries = [str(e).strip() for e in body.get("entries") or [] if str(e).strip()]
        extend = str(body.get("extend") or "").strip()
        ids = button_ids(body.get("buttons"))
        name = str(body.get("name") or "").strip() or (extend.rsplit("/", 1)[-1] if extend else "")
        if not name:
            return {"ok": False, "error": "the list needs a name"}
        if extend:
            gone = self._dropped(extend)
            entries = [e.text for e in self._entries(extend) if e.text.strip().casefold() not in gone] + entries
        kept, seen = [], set()
        for text in entries:
            fold = fold_key(text)
            if fold and fold not in seen:
                seen.add(fold)
                kept.append(text.replace("\n", " "))
        if not kept:
            return {"ok": False, "error": "nothing to save"}
        slot = ids[0] if ids else "generated"
        path = merged_path(LIBRARY_ROOT, slot, name)
        if os.path.exists(path):
            return {"ok": False, "error": f"{_rel(path)} already exists: pick another name"}
        new_name = merged_key(slot, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(f"# Made in the wildcard review on {time.strftime('%Y-%m-%d')} with {body.get('model') or LLM_DEFAULT_MODEL}"
                         + (f", extending {extend}" if extend else "") + f": {len(kept)} entries.\n")
            if body.get("description"):
                handle.write(f"# {str(body.get('description')).strip()[:300]}\n")
            handle.write("\n".join(kept) + "\n")
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.lock:
            overlay = UserOverlay(LIBRARY_ROOT)
            settings = {}
            if ids:
                settings["slot"] = ids if len(ids) > 1 else ids[0]
            if body.get("nsfw"):
                settings["nsfw"] = str(body["nsfw"])
            if settings:
                overlay.data["lists"][new_name] = settings
            old_settings, partner_reviews = {}, {}
            if extend:
                source = L.strip_nsfw_prefix(extend)
                old_settings[source] = dict(overlay.list(source))
                hidden = dict(overlay.list(source), hidden=True, merged_into=new_name)
                hidden.pop("slot", None)
                overlay.data["lists"][source] = hidden
            overlay.save()
            if extend:
                with self.connect() as connection:
                    old = connection.execute("select * from reviews where key = ?", (extend,)).fetchone()
                    partner_reviews[extend] = dict(old) if old else None
                    connection.execute(
                        """insert into reviews (key, decision, same_as, how, decided_at, applied_at, merged_into)
                           values (?, 'same', ?, 'extend', ?, ?, ?)
                           on conflict(key) do update set decision='same', same_as=excluded.same_as, how='extend',
                               decided_at=excluded.decided_at, applied_at=excluded.applied_at, merged_into=excluded.merged_into""",
                        (extend, new_name, stamp, stamp, new_name))
        manifest = {"made": stamp, "root": LIBRARY_ROOT, "kind": "made", "renames": [], "moves": [],
                    "merges": [{"key": "", "with": [], "into": new_name, "path": _rel(path), "count": len(kept),
                                "old_settings": old_settings, "partner_reviews": partner_reviews}]}
        manifest_path = self._save_manifest(manifest)
        self._forget_rows()
        if self.library is not None:
            self.library.refresh(force=True)
        return {"ok": True, "key": new_name, "path": _rel(path), "count": len(kept), "manifest": manifest_path}

    def page(self, keys: List[str]) -> List[Dict[str, Any]]:
        by_key = {r["key"]: r for r in self.rows()}
        out = []
        with self.connect() as connection:
            for key in keys:
                row = by_key.get(key)
                if row is None:
                    continue
                found = connection.execute("select samples from triage where key = ?", (key,)).fetchone()
                try:
                    samples = json.loads((found["samples"] if found else None) or "[]")
                except ValueError:
                    samples = []
                out.append({"key": key, "dim": row["dimension"], "facet": row["facet"], "verdict": row["verdict"],
                            "reason": row["reason"], "visual": row["visual"], "coherence": row["coherence"],
                            "entries": row["entries"], "source": row["source"], "decision": row["decision"] or "",
                            "samples": [str(s)[:120] for s in samples[:10]]})
        return out

    # -- saving ------------------------------------------------------------------------------------------------------
    def save(self, body: Dict[str, Any], how: str = "card") -> Dict[str, Any]:
        key = str(body.get("key") or "")
        decision = str(body.get("decision") or "")
        if decision and decision not in DECISIONS:
            return {"ok": False, "error": f"unknown decision {decision}"}
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if "button" in body:
            body = dict(body, button=",".join(button_ids(body.get("button"))))
        with self.connect() as connection:
            if not connection.execute("select 1 from triage where key = ?", (key,)).fetchone():
                return {"ok": False, "error": "unknown list"}
            old = connection.execute("select * from reviews where key = ?", (key,)).fetchone()
            old = dict(old) if old else {}
            values = {name: (body[name] if name in body else old.get(name)) for name in ("same_as", "button", "name", "nsfw", "note")}
            if decision != "same":
                values["same_as"] = None
            merge = {"merge_with": ",".join(button_ids(body.get("merge_with"))) if "merge_with" in body else old.get("merge_with"),
                     "merge_name": body.get("merge_name", old.get("merge_name")),
                     "merge_drop": json.dumps(body["merge_drop"], ensure_ascii=False) if isinstance(body.get("merge_drop"), list)
                     else old.get("merge_drop")}
            if decision == "merge" and not merge["merge_with"]:
                return {"ok": False, "error": "a merge needs at least one other list"}
            connection.execute(
                """insert into reviews (key, decision, same_as, button, name, nsfw, note, how, decided_at, applied_at)
                   values (?,?,?,?,?,?,?,?,?,?)
                   on conflict(key) do update set decision=excluded.decision, same_as=excluded.same_as,
                       button=excluded.button, name=excluded.name, nsfw=excluded.nsfw, note=excluded.note,
                       how=excluded.how, decided_at=excluded.decided_at""",
                (key, decision or None, values["same_as"], values["button"] or None, values["name"] or None,
                 values["nsfw"] or None, values["note"] or None, how, stamp, old.get("applied_at")))
            connection.execute("update reviews set merge_with = ?, merge_name = ?, merge_drop = ? where key = ?",
                               (merge["merge_with"] or None, merge["merge_name"] or None, merge["merge_drop"] or None, key))
        self._forget_rows()
        return {"ok": True}

    def save_many(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        saved = 0
        for item in items:
            if self.save({"key": item.get("key"), "decision": item.get("decision")}, how="page").get("ok"):
                saved += 1
        return {"ok": True, "saved": saved}

    # -- apply -------------------------------------------------------------------------------------------------------
    def _decided(self, connection) -> List[Dict[str, Any]]:
        return [dict(row) for row in connection.execute(
            """select r.*, t.file from reviews r left join triage t on t.key = r.key
               where r.decision is not null and r.decision != 'unsure'""")]

    def _settings(self, row: Dict[str, Any]) -> Dict[str, Any]:
        settings: Dict[str, Any] = {}
        if row["decision"] == "merge":
            settings["hidden"] = True
            settings["merged_into"] = L.strip_nsfw_prefix(self._merge_target(row)["key"])
        elif row["decision"] in ("dump", "same"):
            settings["hidden"] = True
            if row["same_as"]:
                settings["same_as"] = L.strip_nsfw_prefix(row["same_as"])
        else:
            settings["hidden"] = False
            ids = button_ids(row["button"])
            if ids:
                settings["slot"] = ids if len(ids) > 1 else ids[0]
        if row["nsfw"]:
            settings["nsfw"] = row["nsfw"]
        return settings

    def _renames(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for row in rows:
            if row["decision"] == "keep" and row["name"]:
                target = self.rename_target(row["key"], row["file"] or "", row["name"])
                if target:
                    out.append(target)
        return out

    def plan(self) -> Dict[str, Any]:
        """What Apply would write for every reviewed list (only the settings each decision owns) and rename."""
        with self.connect() as connection:
            rows = self._decided(connection)
        changes = [{"key": r["key"], "name": L.strip_nsfw_prefix(r["key"]), "decision": r["decision"],
                    "settings": self._settings(r), "applied_at": r["applied_at"], "decided_at": r["decided_at"]}
                   for r in rows]
        counts: Dict[str, int] = {}
        for change in changes:
            counts[change["decision"]] = counts.get(change["decision"], 0) + 1
        pending = [c for c in changes if not c["applied_at"] or c["applied_at"] < c["decided_at"]]
        renames = self._renames(rows)
        merges = self._merges(rows)
        return {"counts": counts, "pending": len(pending), "total": len(changes), "changes": pending[:40],
                "renames": renames, "merges": merges, "file": os.path.join(LIBRARY_ROOT, "_catalog_user.yaml")}

    def apply(self) -> Dict[str, Any]:
        with self.connect() as connection:
            rows = self._decided(connection)
        planned = self._renames(rows)
        renames = [r for r in planned if not r["conflict"]]
        overlay = UserOverlay(LIBRARY_ROOT)
        overlay.reload_if_changed()
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        manifest = {"made": stamp, "root": LIBRARY_ROOT, "kind": "apply", "renames": [], "moves": [], "merges": []}
        done = self._do_renames(renames, overlay, manifest) if renames else []
        merged = self._do_merges(overlay, manifest, stamp)
        done = done + merged
        written = 0
        with self.connect() as connection:
            for row in self._decided(connection):           # again: renamed lists now carry their new keys
                name = L.strip_nsfw_prefix(row["key"])
                entry = dict(overlay.list(name))
                if row["decision"] == "merge":
                    entry["hidden"] = True
                    entry.pop("slot", None)
                    if row["merged_into"]:
                        entry["merged_into"] = L.strip_nsfw_prefix(row["merged_into"])
                elif row["decision"] in ("dump", "same"):
                    entry["hidden"] = True
                    if row["same_as"]:
                        entry["same_as"] = L.strip_nsfw_prefix(row["same_as"])
                    entry.pop("slot", None)
                else:
                    entry.pop("hidden", None)
                    entry.pop("same_as", None)
                    entry.pop("name", None)          # the old display-name field: renames replace it
                    ids = button_ids(row["button"])
                    if ids:
                        entry["slot"] = ids if len(ids) > 1 else ids[0]
                    else:
                        entry.pop("slot", None)
                if row["nsfw"]:
                    entry["nsfw"] = row["nsfw"]
                if entry:
                    overlay.data["lists"][name] = entry
                else:
                    overlay.data["lists"].pop(name, None)
                written += 1
            overlay.save()
            connection.execute("update reviews set applied_at = ? where decision is not null and decision != 'unsure'",
                               (stamp,))
        manifest_path = self._save_manifest(manifest) if done else ""
        self._forget_rows()
        if done and self.library is not None:
            self.library.refresh(force=True)
        return {"ok": True, "written": written, "file": overlay.path, "renamed": len(done) - len(merged),
                "merged": len(merged),
                "skipped": [r for r in planned if r["conflict"]], "manifest": manifest_path}

    def _do_renames(self, renames: List[Dict[str, Any]], overlay: UserOverlay, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rename .txt lists in place; write YAML / JSON keys out as their own .txt. Settings, buttons, review follow."""
        buttons = read_buttons(MY_BUTTONS)
        buttons_changed = False
        done = []
        for item in renames:
            old_key, new_key = item["old"], item["new"]
            old_name, new_name = L.strip_nsfw_prefix(old_key), L.strip_nsfw_prefix(new_key)
            source, target = _abs(item["from"]), _abs(item["path"])
            if item["kind"] == "rename":
                os.rename(source, target)
            else:
                entries = self._entries(old_key)
                if not entries:
                    continue
                with open(target, "w", encoding="utf-8") as handle:
                    for entry in entries:
                        weight = "" if abs(entry.weight - 1.0) < 1e-9 else f"{entry.weight:g}::"
                        handle.write(weight + entry.text.replace("\n", " ") + "\n")
            old_entry = dict(overlay.list(old_name))
            moved_settings = {k: v for k, v in old_entry.items() if k not in ("hidden", "moved_to", "name")}
            if moved_settings:
                overlay.data["lists"][new_name] = dict(overlay.list(new_name), **moved_settings)
            if item["kind"] == "rename":
                overlay.data["lists"].pop(old_name, None)
                overlay.data.setdefault("aliases", {})[old_name] = new_name
            else:
                overlay.data["lists"][old_name] = {"hidden": True, "moved_to": new_name}
            for button in buttons:
                if old_name in (button.get("lists") or []):
                    button["lists"] = [new_name if k == old_name else k for k in button["lists"]]
                    buttons_changed = True
            with self.connect() as connection:
                connection.execute("update triage set key = ?, file = ? where key = ?", (new_key, item["path"], old_key))
                connection.execute("update judgements set key = ? where key = ?", (new_key, old_key))
                connection.execute("update reviews set key = ?, renamed_from = ? where key = ?", (new_key, old_key, old_key))
            record = dict(item, old_settings=old_entry)
            manifest["renames"].append(record)
            done.append(record)
        if buttons_changed:
            write_buttons(MY_BUTTONS, buttons)
        return done

    # -- merging -----------------------------------------------------------------------------------------------------
    def merge_preview(self, key: str, partners: List[str]) -> Dict[str, Any]:
        """Every entry of this list and its partners, near-duplicates folded, shared ones first; which lists have each."""
        sources = [key] + [k for k in partners if k and k != key]
        lists = [[e.text for e in self._entries(k)] for k in sources]
        rows = merge_entries(lists)
        by_key = {r["key"]: r for r in self.rows()}
        return {"sources": [{"key": k, "dim": (by_key.get(k) or {}).get("dimension") or "", "entries": len(lists[i])}
                            for i, k in enumerate(sources)],
                "rows": [row.to_dict() for row in rows[:MERGE_PREVIEW_MAX]], "total": len(rows),
                "shared": sum(1 for row in rows if row.lists > 1)}

    def _merge_target(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Where a merge goes: mine/<first button, else 'review'>/<name>.txt."""
        ids = button_ids(row.get("button"))
        slot = ids[0] if ids else "review"
        name = row.get("merge_name") or (row.get("key") or "merged").rsplit("/", 1)[-1]
        return {"key": merged_key(slot, name), "path": merged_path(LIBRARY_ROOT, slot, name), "slot": slot,
                "name": merged_name(name)}

    def _merges(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for row in rows:
            if row["decision"] != "merge" or not row["merge_with"]:
                continue
            target = self._merge_target(row)
            done = bool(row.get("merged_into")) and row["merged_into"] == target["key"] and os.path.exists(target["path"])
            conflict = "" if done or not os.path.exists(target["path"]) else f"{_rel(target['path'])} already exists"
            out.append({"key": row["key"], "with": button_ids(row["merge_with"]), "into": target["key"],
                        "path": _rel(target["path"]), "done": done, "conflict": conflict,
                        "drop": len(json.loads(row["merge_drop"] or "[]"))})
        return out

    def _do_merges(self, overlay: UserOverlay, manifest: Dict[str, Any], stamp: str) -> List[Dict[str, Any]]:
        """Write each pending merge to mine/, hide its sources (merged_into), put it on its buttons."""
        with self.connect() as connection:
            rows = self._decided(connection)
        done = []
        for item in self._merges(rows):
            if item["done"] or item["conflict"]:
                continue
            row = next(r for r in rows if r["key"] == item["key"])
            target = self._merge_target(row)
            sources = [row["key"]] + item["with"]
            drop = {str(t).casefold() for t in json.loads(row["merge_drop"] or "[]")}
            merged = merge_entries([[e.text for e in self._entries(k)] for k in sources])
            kept = [r.text for r in merged if r.text.casefold() not in drop]
            try:
                count = write_merged(target["path"], kept, sources, slot_label=target["slot"])
            except (ValueError, FileExistsError):
                continue
            new_name = target["key"]
            old_settings = {}
            for source in sources:
                name = L.strip_nsfw_prefix(source)
                old_settings[name] = dict(overlay.list(name))
                entry = dict(overlay.list(name), hidden=True, merged_into=new_name)
                entry.pop("slot", None)
                overlay.data["lists"][name] = entry
            settings = {}
            ids = button_ids(row["button"])
            if ids:
                settings["slot"] = ids if len(ids) > 1 else ids[0]
            if row["nsfw"]:
                settings["nsfw"] = row["nsfw"]
            if settings:
                overlay.data["lists"][new_name] = dict(overlay.list(new_name), **settings)
            partner_reviews = {}
            with self.connect() as connection:
                for partner in item["with"]:
                    old = connection.execute("select * from reviews where key = ?", (partner,)).fetchone()
                    partner_reviews[partner] = dict(old) if old else None
                    if not connection.execute("select 1 from triage where key = ?", (partner,)).fetchone():
                        continue
                    connection.execute(
                        """insert into reviews (key, decision, same_as, how, decided_at, applied_at, merged_into)
                           values (?, 'same', ?, 'merge', ?, ?, ?)
                           on conflict(key) do update set decision='same', same_as=excluded.same_as, how='merge',
                               decided_at=excluded.decided_at, applied_at=excluded.applied_at, merged_into=excluded.merged_into""",
                        (partner, new_name, stamp, stamp, new_name))
                connection.execute("update reviews set merged_into = ? where key = ?", (new_name, row["key"]))
            record = {"key": row["key"], "with": item["with"], "into": new_name, "path": _rel(target["path"]),
                      "count": count, "old_settings": old_settings, "partner_reviews": partner_reviews}
            manifest["merges"].append(record)
            done.append(record)
        return done

    # -- moving dumped files -------------------------------------------------------------------------------------------
    @staticmethod
    def _file_keys(path: str) -> Optional[set]:
        """
        Every list key a YAML / JSON file holds, read from the file itself (the triage can be out of date: a key the
        review split out by a rename still sits in its file). None = the file could not be read (then it stays).
        """
        try:
            text = L.read_text_file(path)
            data = json.loads(text) if path.lower().endswith(".json") else (yaml.safe_load(text) if yaml else None)
        except Exception:
            return None
        found: set = set()

        def walk(node, parts):
            if isinstance(node, dict):
                for k, v in node.items():
                    walk(v, parts + [str(k)])
            elif parts and (isinstance(node, (list, str, int, float)) and not isinstance(node, bool)):
                found.add(L.normalise_key("/".join(parts)))
        walk(data, [])
        return found

    def dump_plan(self) -> Dict[str, Any]:
        with self.connect() as connection:
            rows = [dict(r) for r in connection.execute(
                """select r.key, t.file from reviews r join triage t on t.key = r.key
                   where r.decision = 'dump' and (r.moved_to is null or r.moved_to = '')""")]
        by_file: Dict[str, List[str]] = {}
        for row in rows:
            if row["file"]:
                by_file.setdefault(_abs(row["file"]), []).append(row["key"])
        moves, stay, missing = [], [], []
        for path, keys in sorted(by_file.items()):
            if not os.path.exists(path):
                missing.append(_rel(path))
                continue
            relative = _rel(path)
            target = os.path.join(LIBRARY_ROOT, DUMPED_FOLDER, *relative.split("/"))
            if path.lower().endswith(STRUCTURED):
                holds = self._file_keys(path)
                if not holds or not holds <= set(keys):
                    stay.append({"file": relative, "dumped": len(keys), "lists": len(holds or ())})
                    continue
            if os.path.exists(target):
                stay.append({"file": relative, "dumped": len(keys), "lists": len(keys), "why": "already in _dumped"})
                continue
            moves.append({"file": relative, "to": _rel(target), "keys": keys})
        return {"moves": moves, "stay": stay, "missing": missing, "folder": os.path.join(LIBRARY_ROOT, DUMPED_FOLDER)}

    def dump_move(self) -> Dict[str, Any]:
        plan = self.dump_plan()
        manifest = {"made": time.strftime("%Y-%m-%d %H:%M:%S"), "root": LIBRARY_ROOT, "kind": "dump_move",
                    "renames": [], "moves": []}
        path = ""
        for move in plan["moves"]:
            source, target = _abs(move["file"]), _abs(move["to"])
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.move(source, target)
            manifest["moves"].append(move)
            with self.connect() as connection:
                connection.executemany("update reviews set moved_to = ? where key = ?", [(move["to"], k) for k in move["keys"]])
            if len(manifest["moves"]) % 200 == 0:
                path = self._save_manifest(manifest, path)
        if manifest["moves"]:
            path = self._save_manifest(manifest, path)
        self._forget_rows()
        if manifest["moves"] and self.library is not None:
            self.library.refresh(force=True)
        return {"ok": True, "moved": len(manifest["moves"]), "stayed_hidden": len(plan["stay"]), "manifest": path}

    def _save_manifest(self, manifest: Dict[str, Any], path: str = "") -> str:
        os.makedirs(MANIFESTS, exist_ok=True)
        if not path:                     # a new manifest never replaces an older one (two Applies in one second)
            stem = os.path.join(MANIFESTS, f"{manifest['kind']}_{time.strftime('%Y%m%d_%H%M%S')}")
            path, n = stem + ".json", 1
            while os.path.exists(path):
                n += 1
                path = f"{stem}_{n}.json"
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=1, ensure_ascii=False)
        return path


def undo(manifest_path: str) -> None:
    """Put back what a manifest records: moved files, renamed lists (files, settings, aliases, buttons, review keys)."""
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    review = Review(load_library=False)
    back = 0
    for move in reversed(manifest.get("moves") or []):
        source, target = _abs(move["file"]), _abs(move["to"])
        if os.path.exists(target) and not os.path.exists(source):
            os.makedirs(os.path.dirname(source), exist_ok=True)
            shutil.move(target, source)
            back += 1
        with review.connect() as connection:
            connection.executemany("update reviews set moved_to = null where key = ?", [(k,) for k in move["keys"]])
    overlay = UserOverlay(LIBRARY_ROOT)
    overlay.reload_if_changed()
    buttons = read_buttons(MY_BUTTONS)
    for item in reversed(manifest.get("renames") or []):
        old_key, new_key = item["old"], item["new"]
        old_name, new_name = L.strip_nsfw_prefix(old_key), L.strip_nsfw_prefix(new_key)
        source, target = _abs(item["from"]), _abs(item["path"])
        if item["kind"] == "rename":
            if os.path.exists(target) and not os.path.exists(source):
                os.rename(target, source)
        elif os.path.exists(target):
            os.remove(target)
        overlay.data["lists"].pop(new_name, None)
        if item.get("old_settings"):
            overlay.data["lists"][old_name] = item["old_settings"]
        else:
            overlay.data["lists"].pop(old_name, None)
        (overlay.data.get("aliases") or {}).pop(old_name, None)
        for button in buttons:
            if new_name in (button.get("lists") or []):
                button["lists"] = [old_name if k == new_name else k for k in button["lists"]]
        with review.connect() as connection:
            connection.execute("update triage set key = ?, file = ? where key = ?", (old_key, item["from"], new_key))
            connection.execute("update judgements set key = ? where key = ?", (old_key, new_key))
            connection.execute("update reviews set key = ?, renamed_from = null where key = ?", (old_key, new_key))
        back += 1
    for item in reversed(manifest.get("merges") or []):
        path = _abs(item["path"])
        if os.path.exists(path):
            os.remove(path)
        overlay.data["lists"].pop(L.strip_nsfw_prefix(item["into"]), None)
        for name, settings in (item.get("old_settings") or {}).items():
            if settings:
                overlay.data["lists"][name] = settings
            else:
                overlay.data["lists"].pop(name, None)
        with review.connect() as connection:
            connection.execute("update reviews set merged_into = null, applied_at = null where key = ?", (item["key"],))
            for partner, old in (item.get("partner_reviews") or {}).items():
                if old is None:
                    connection.execute("delete from reviews where key = ?", (partner,))
                else:
                    columns = [c for c in old if c != "key"]
                    connection.execute(f"update reviews set {', '.join(c + ' = ?' for c in columns)} where key = ?",
                                       [old[c] for c in columns] + [partner])
        back += 1
    overlay.save()
    write_buttons(MY_BUTTONS, buttons)
    print(f"undone: {back} changes from {manifest_path}")


def make_handler(review: Review):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def _send(self, code: int, body: bytes, kind: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data: Any, code: int = 200) -> None:
            self._send(code, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self):
            url = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            try:
                if url.path == "/favicon.ico":
                    self._send(204, b"", "image/x-icon")
                elif url.path in ("/", "/index.html"):
                    with open(os.path.join(HERE, "review.html"), "rb") as handle:
                        self._send(200, handle.read(), "text/html; charset=utf-8")
                elif url.path == "/api/meta":
                    self._json(review.meta())
                elif url.path == "/api/queue":
                    self._json(review.queue(q.get("order", "facet"), q.get("facet", ""), q.get("verdict", ""),
                                            q.get("status", "todo"), q.get("source", ""), q.get("q", "")))
                elif url.path == "/api/list":
                    found = review.list_view(q.get("key", ""), int(q.get("seed", "0") or 0))
                    self._json(found if found else {"error": "not found"}, 200 if found else 404)
                elif url.path == "/api/entries":
                    self._json(review.entries(q.get("key", ""), q.get("q", ""), int(q.get("offset", 0) or 0),
                                              min(500, int(q.get("limit", 200) or 200))))
                elif url.path == "/api/page":
                    self._json(review.page([k for k in q.get("keys", "").split(",") if k]))
                elif url.path == "/api/apply_preview":
                    self._json(review.plan())
                elif url.path == "/api/dump_preview":
                    self._json(review.dump_plan())
                elif url.path == "/api/llm_models":
                    try:
                        self._json({"models": llm_models(), "default": LLM_DEFAULT_MODEL})
                    except Exception as error:
                        self._json({"models": [], "default": LLM_DEFAULT_MODEL, "error": f"LM Studio: {error}"})
                elif url.path == "/api/merge_preview":
                    self._json(review.merge_preview(q.get("key", ""), [k for k in q.get("with", "").split(",") if k]))
                else:
                    self._send(404, b"not found", "text/plain")
            except Exception as error:
                self._json({"error": f"{type(error).__name__}: {error}"}, 500)

        def do_POST(self):
            url = urlparse(self.path)
            try:
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length) or b"{}")
                if url.path == "/api/review":
                    self._json(review.save(body))
                elif url.path == "/api/review_many":
                    self._json(review.save_many(body.get("items") or []))
                elif url.path == "/api/button":
                    self._json(review.create_button(str(body.get("label", "")), str(body.get("section", "")),
                                                    str(body.get("key", "")), str(body.get("group", ""))))
                elif url.path == "/api/apply":
                    self._json(review.apply())
                elif url.path == "/api/dump_move":
                    self._json(review.dump_move())
                elif url.path == "/api/drop":
                    self._json(review.drop(str(body.get("key", "")), list(body.get("texts") or []), bool(body.get("undrop"))))
                elif url.path == "/api/drop_matching":
                    self._json(review.drop_matching(str(body.get("key", "")), str(body.get("pattern", "")),
                                                    bool(body.get("regex")), bool(body.get("drop"))))
                elif url.path == "/api/suggest_junk":
                    self._json(review.suggest_junk(str(body.get("key", "")), str(body.get("model", ""))))
                elif url.path == "/api/generate":
                    self._json(review.generate(body))
                elif url.path == "/api/save_list":
                    self._json(review.save_list(body))
                else:
                    self._send(404, b"not found", "text/plain")
            except Exception as error:
                self._json({"ok": False, "error": f"{type(error).__name__}: {error}"}, 500)

    return Handler


def serve(port: int = PORT, open_browser: bool = True) -> None:
    review = Review()
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(review))
    url = f"http://127.0.0.1:{port}/"
    print(f"[review] {url}   (Ctrl+C to stop)  triage: {TRIAGE}")
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo(sys.argv[sys.argv.index("--undo") + 1])
    else:
        serve(int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else PORT,
              open_browser="--no-browser" not in sys.argv)
