"""
Wildcard catalog: a generated index of every list in a library (spec: dev/WILDCARD_CATALOG_SPEC.md, P2).

One SQLite file per search folder, `<folder>/_catalog.sqlite` (or the package cache when the folder
is not writable or is the package's own wildcards/ folder). It describes lists; it never replaces
them. Delete it and it is rebuilt.

Per list it stores what the builders and the engine need to rank and gate lists:
    kind        atoms | phrases | prompts | template | tags
    dialect     prose | tags | mixed        (booru_style_tags vs words)
    entries, median words / characters, duplicate share inside the list
    nsfw        sfw | suggestive | explicit, and where that came from (folder | name | content)
    signature   hash of the entry set: identical lists in different packs share it (dup_of)
    quality     0..1, ordering only, never access (see quality_score)
    facet       a coarse topic (appearance, wardrobe, setting, lighting, camera, ...)
    samples     8 entries spread across the list
    display     "Hair Colors · Mrweaz"

Updating is incremental: only files whose (mtime, size) changed are analysed again. The analysis
uses the entries exactly as the library serves them (LoRA tags stripped, content filter applied).

No ComfyUI dependency. `CatalogSet.update(library)` is safe to run in a background thread: it only
reads the library.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import statistics
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

SCHEMA_VERSION = "2"      # bump when the analysis changes: catalogs rebuild themselves
CATALOG_FILE = "_catalog.sqlite"
SAMPLE_COUNT = 8
ANALYSE_CAP = 3000           # entries looked at per list for the statistics (all are counted and hashed)

# -- content rates (same vocabulary as dev/wildcard_audit.py and wildcard_cleanup.py) ----------------
_EXPLICIT = re.compile(
    r"\b(sex|sexual|fuck\w*|cum\w*|cock|dick|penis|pussy|vagina|anal|blowjob|fellatio|cunnilingus|penetrat\w*|"
    r"orgasm\w*|masturbat\w*|nipples?|genital\w*|porn\w*|nsfw|hentai|bdsm|bondage|ejaculat\w*|erect\w*|"
    r"missionary|doggystyle|cowgirl|spread legs|creampie|dildo|vibrator|threesome|gangbang)\b", re.I)
_SUGGEST = re.compile(
    r"\b(nude|naked|topless|lingerie|panties|thong|bra|see-through|sheer|sexy|seductive|cleavage|erotic|"
    r"sensual|busty|braless|undress\w*|stripper|boudoir|fetish|latex|g-string)\b", re.I)
EXPLICIT_RATE = 0.08         # explicit words per entry -> explicit
SUGGEST_EXPLICIT_RATE = 0.5  # suggestive words per entry -> explicit
SUGGEST_RATE = 0.15          # suggestive words per entry -> suggestive

_WILDREF = re.compile(r"__[\w\-/*. ]+__")
_WEIGHTED = re.compile(r"\([^()]+:\s*\d*\.?\d+\)")
_BOORU = re.compile(r"^[a-z0-9]+(?:_[a-z0-9()']+)+$")
_BOILERPLATE = re.compile(
    r"\b(masterpiece|best quality|high quality|highres|absurdres|ultra[- ]detailed|8k|4k|uhd|"
    r"trending on artstation|award[- ]winning|score_\d)\b", re.I)
_MOJIBAKE = re.compile(r"Ã.|â€|Â |�")
_CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯]")

# -- display names -----------------------------------------------------------------------------------
_NOISE = re.compile(r"(_v\d+[\w.]*$|v\d+fixed$|\s*\(\d+\)$|wildcards?|^wc[-_]|^!+)", re.I)
_LEAF_PREFIX = re.compile(r"^(?:cops_(?:bp_)?(?:male_|female_)?wc[-_]?|cyber_|bk_|rd_|fg3_|vc_|tr_)", re.I)

# -- facets: keyword rules on the key; first rule that matches wins --------------------------------
FACETS = ("subject", "appearance", "wardrobe", "pose_action", "expression", "setting", "architecture",
          "nature", "creature", "object_material", "lighting", "camera", "style_artist", "color_mood",
          "era_culture", "concept", "prompt_template")
_FACET_RULES: List[Tuple[str, re.Pattern]] = [(facet, re.compile(pattern, re.I)) for facet, pattern in (
    ("camera", r"camera|lens|angle|shot|framing|composition|focal|aperture|depth.of.field|bokeh"),
    ("lighting", r"light(?!ning)|lighting|shadow|illuminat|golden.hour|glow"),
    ("expression", r"expression|emotion|mood(?!.*colou?r)|facial|smile|feeling"),
    ("pose_action", r"pose|action|gesture|posture|activit|interaction|movement(?!s?$)|dance"),
    ("wardrobe", r"cloth|outfit|wear|dress|shirt|top|bottom|pants|skirt|shoe|boot|hat|jacket|coat|costume|"
                 r"uniform|lingerie|swimsuit|accessor|jewel|glove|sock|stocking|attire|fashion"),
    ("appearance", r"hair|eye|face|skin|body|makeup|nose|lip|beard|freckle|tattoo|age|ethnic|race|"
                   r"nationalit|physique|build|figure|complexion"),
    ("subject", r"person|people|character|occupation|profession|job|role|archetype|subject|name|gender|"
                r"girl|boy|woman|man|men|women"),
    ("creature", r"animal|creature|monster|beast|bird|fish|insect|dragon|species|pet|dog|cat"),
    ("architecture", r"architect|building|interior|room|house|castle|city|street|structure"),
    ("nature", r"landscape|nature|forest|mountain|ocean|sea|river|flower|plant|tree|weather|season|sky|biome"),
    ("setting", r"location|place|setting|scene|background|environment|world|planet|travel"),
    ("style_artist", r"artist|style|medium|movement|painter|photographer|illustrat|render|aesthetic|genre|film"),
    ("color_mood", r"colou?r|palette|tone|hue|grading|atmosphere|vibe"),
    ("era_culture", r"era|decade|century|period|histor|culture|myth|religio|medieval|victorian|\d0s"),
    ("object_material", r"object|item|material|fabric|texture|metal|wood|food|drink|weapon|tool|vehicle|prop"),
    ("concept", r"concept|idea|theme|abstract|adjective|adj|noun|verb|word"),
)]


def display_name(key: str) -> str:
    """'mrweazsfwildcardssfw_v30glamour/hair_colors' -> 'Hair Colors · Mrweazsf Glamour'."""
    parts = [part for part in key.split("/") if part]
    if not parts:
        return key

    def clean(segment: str) -> str:
        segment = _LEAF_PREFIX.sub("", segment)
        segment = _NOISE.sub(" ", segment)
        segment = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", segment)
        segment = re.sub(r"[_\-]+", " ", segment)
        return re.sub(r"\s+", " ", segment).strip().title()

    leaf = clean(parts[-1]) or parts[-1]
    if len(parts) == 1:
        return leaf
    pack = clean(parts[0]) or parts[0]
    return f"{leaf} · {pack}"


def facet_for(key: str) -> Tuple[str, float]:
    """(facet, confidence). Rules look at the leaf first, then the whole key."""
    leaf = key.rsplit("/", 1)[-1]
    for text, confidence in ((leaf, 0.9), (key, 0.6)):
        for facet, pattern in _FACET_RULES:
            if pattern.search(text):
                return facet, confidence
    return "", 0.0


def entry_signature(texts: Iterable[str]) -> str:
    """Same set of entries (case-insensitive) -> same signature, whatever the order or file."""
    digest = hashlib.sha1()
    for text in sorted({text.strip().casefold() for text in texts if text.strip()}):
        digest.update(text.encode("utf-8", "replace"))
        digest.update(b"\n")
    return digest.hexdigest()


def _share(texts: Sequence[str], pattern: re.Pattern) -> float:
    return sum(1 for text in texts if pattern.search(text)) / len(texts) if texts else 0.0


def _rate(texts: Sequence[str], pattern: re.Pattern) -> float:
    return sum(len(pattern.findall(text)) for text in texts) / len(texts) if texts else 0.0


def _stratified(texts: Sequence[str], count: int = SAMPLE_COUNT) -> List[str]:
    if len(texts) <= count:
        return list(texts)
    step = len(texts) / count
    return [texts[int(index * step + step / 2)] for index in range(count)]


def _band(value: float, points: Sequence[Tuple[float, float]]) -> float:
    """Piecewise-linear lookup: points are (x, score) sorted by x."""
    if value <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if value <= x1:
            return y0 + (y1 - y0) * (value - x0) / (x1 - x0)
    return points[-1][1]


def quality_score(stats: Dict) -> float:
    """
    0..1, ordering only: uniqueness, entry length that fits between typed words, and cleanliness
    (weight syntax, quality boilerplate, mojibake, other scripts), scaled by list size.
    Templates and full prompts are scored by size and cleanliness only.
    """
    size = _band(stats["entries"], [(0, 0.0), (3, 0.2), (10, 0.6), (20, 1.0), (5000, 1.0), (50000, 0.7), (200000, 0.4)])
    unique = max(0.0, 1.0 - 2.0 * stats["dupe_share"])
    if stats["kind"] in ("template", "prompts"):
        fit = 0.6
    else:
        fit = _band(stats["median_words"], [(1, 1.0), (6, 1.0), (10, 0.75), (18, 0.45), (30, 0.2), (60, 0.1)])
    dirt = (0.6 * stats["weights_share"] + 1.0 * stats["boilerplate_share"] + 1.5 * stats["mojibake_share"]
            + 0.5 * stats["cjk_share"])
    clean = max(0.0, 1.0 - dirt)
    # Size scales the rest: a clean two-item list is still a poor source of variety.
    return round((0.2 * unique + 0.4 * fit + 0.4 * clean) * (0.4 + 0.6 * size), 4)


def analyse(key: str, texts: Sequence[str], folder_nsfw: bool = False, name_nsfw: bool = False) -> Dict:
    """Statistics and derived fields for one list. `texts` = entries as the library serves them."""
    count = len(texts)
    sample = list(texts[:ANALYSE_CAP])
    words = [len(text.split()) for text in sample] or [0]
    chars = [len(text) for text in sample] or [0]
    median_words = int(statistics.median(words))
    median_chars = int(statistics.median(chars))
    stats = {
        "entries": count,
        "median_words": median_words,
        "median_chars": median_chars,
        "dupe_share": round(1 - len({t.casefold() for t in sample}) / len(sample), 4) if sample else 0.0,
        "refs_share": round(_share(sample, _WILDREF), 4),
        "weights_share": round(_share(sample, _WEIGHTED), 4),
        "booru_share": round(_share(sample, _BOORU), 4),
        "boilerplate_share": round(_share(sample, _BOILERPLATE), 4),
        "mojibake_share": round(_share(sample, _MOJIBAKE), 4),
        "cjk_share": round(_share(sample, _CJK), 4),
        "explicit_rate": round(_rate(sample, _EXPLICIT), 4),
        "suggest_rate": round(_rate(sample, _SUGGEST), 4),
    }
    comma_heavy = _share(sample, re.compile(r"(?:[^,]*,){4}"))
    if count == 0:
        kind = "empty"
    elif stats["refs_share"] >= 0.3:
        kind = "template"
    elif median_chars >= 140 or (comma_heavy >= 0.5 and median_chars >= 60):
        kind = "prompts"
    elif stats["booru_share"] >= 0.5:
        kind = "tags"
    elif median_words >= 7:
        kind = "phrases"
    else:
        kind = "atoms"
    stats["kind"] = kind
    stats["dialect"] = "tags" if stats["booru_share"] >= 0.5 else "mixed" if stats["booru_share"] >= 0.15 else "prose"

    if folder_nsfw:
        nsfw, source = "explicit", "folder"
    elif name_nsfw:
        nsfw, source = "explicit", "name"
    elif stats["explicit_rate"] >= EXPLICIT_RATE or stats["suggest_rate"] >= SUGGEST_EXPLICIT_RATE:
        nsfw, source = "explicit", "content"
    elif stats["suggest_rate"] >= SUGGEST_RATE:
        nsfw, source = "suggestive", "content"
    else:
        nsfw, source = "sfw", ""
    stats["nsfw"], stats["nsfw_source"] = nsfw, source
    stats["quality"] = quality_score(stats)
    leaf = key.rsplit("/", 1)[-1]
    if len(leaf) > 60 or re.search(r"[,<>{}\[\]()]", leaf):
        # A YAML "key" that is really a prompt (packs that map prompts to prompts): not a usable list name.
        stats["quality"] = round(stats["quality"] * 0.2, 4)
    stats["signature"] = entry_signature(texts)
    stats["facet"], stats["facet_confidence"] = facet_for(key)
    stats["samples"] = _stratified(sample)
    stats["display"] = display_name(key)
    return stats


# ----------------------------------------------------------------------------- rows
@dataclass
class ListRow:
    key: str
    root: str
    file: str
    display: str
    kind: str
    dialect: str
    entries: int
    median_words: int
    nsfw: str
    nsfw_source: str
    quality: float
    facet: str
    signature: str
    samples: List[str] = field(default_factory=list)
    dup_of: str = ""

    def to_dict(self) -> Dict:
        return {
            "key": self.key, "display": self.display, "kind": self.kind, "dialect": self.dialect,
            "entries": self.entries, "median_words": self.median_words, "nsfw": self.nsfw,
            "nsfw_source": self.nsfw_source, "quality": self.quality, "facet": self.facet,
            "samples": self.samples, "dup_of": self.dup_of, "root": self.root,
        }


_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, mtime REAL, size INTEGER, status TEXT);
CREATE TABLE IF NOT EXISTS lists (
    key TEXT PRIMARY KEY, file TEXT, pack TEXT, display TEXT, kind TEXT, dialect TEXT,
    entries INTEGER, median_words INTEGER, median_chars INTEGER, dupe_share REAL, refs_share REAL,
    weights_share REAL, booru_share REAL, boilerplate_share REAL, mojibake_share REAL, cjk_share REAL,
    explicit_rate REAL, suggest_rate REAL, nsfw TEXT, nsfw_source TEXT, quality REAL,
    facet TEXT, facet_confidence REAL, signature TEXT, samples TEXT
);
CREATE INDEX IF NOT EXISTS lists_file ON lists(file);
CREATE INDEX IF NOT EXISTS lists_signature ON lists(signature);
CREATE VIRTUAL TABLE IF NOT EXISTS lists_fts USING fts5(key, display, facet, samples);
"""
_LIST_COLUMNS = ("key", "file", "pack", "display", "kind", "dialect", "entries", "median_words", "median_chars",
                 "dupe_share", "refs_share", "weights_share", "booru_share", "boilerplate_share", "mojibake_share",
                 "cjk_share", "explicit_rate", "suggest_rate", "nsfw", "nsfw_source", "quality", "facet",
                 "facet_confidence", "signature", "samples")


class RootCatalog:
    """The catalog of one search folder."""

    def __init__(self, root: str, db_path: str):
        self.root = root
        self.db_path = db_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._connect()

    def _connect(self) -> None:
        # Several processes may share one catalog (ComfyUI, a second ComfyUI, the dev scripts):
        # WAL lets readers work during a write, and a writer waits for the other instead of failing.
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False, timeout=60)
        try:
            self.connection.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError:
            pass
        try:
            self.connection.executescript(_SCHEMA)
            version = self.connection.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
        except sqlite3.DatabaseError:
            version = None
        if version is None or version[0] != SCHEMA_VERSION:
            # Generated data only: start again. Tables are dropped rather than the file deleted,
            # because another process may have it open.
            try:
                for table in ("lists_fts", "lists", "files", "meta"):
                    self.connection.execute(f"DROP TABLE IF EXISTS {table}")
                self.connection.executescript(_SCHEMA)
            except sqlite3.DatabaseError:
                self.connection.close()
                try:
                    os.remove(self.db_path)
                except OSError:
                    pass
                self.connection = sqlite3.connect(self.db_path, check_same_thread=False, timeout=60)
                self.connection.executescript(_SCHEMA)
            self.connection.execute("INSERT OR REPLACE INTO meta VALUES ('schema_version', ?)", (SCHEMA_VERSION,))
            self.connection.commit()

    def known_files(self) -> Dict[str, Tuple[float, int]]:
        with self._lock:
            return {row[0]: (row[1], row[2]) for row in self.connection.execute("SELECT path, mtime, size FROM files")}

    def replace_file(self, relative: str, mtime: float, size: int, analysed: Dict[str, Dict]) -> None:
        """Drop this file's rows and write the new analysis (key -> stats)."""
        with self._lock:
            cursor = self.connection.cursor()
            old_keys = [row[0] for row in cursor.execute("SELECT key FROM lists WHERE file=?", (relative,))]
            for key in old_keys:
                cursor.execute("DELETE FROM lists_fts WHERE key=?", (key,))
            cursor.execute("DELETE FROM lists WHERE file=?", (relative,))
            for key, stats in analysed.items():
                values = dict(stats, key=key, file=relative, pack=key.split("/", 1)[0] if "/" in key else "",
                              samples=json.dumps(stats["samples"], ensure_ascii=False))
                cursor.execute(f"INSERT OR REPLACE INTO lists ({','.join(_LIST_COLUMNS)}) VALUES "
                               f"({','.join('?' * len(_LIST_COLUMNS))})", [values[c] for c in _LIST_COLUMNS])
                cursor.execute("INSERT INTO lists_fts (key, display, facet, samples) VALUES (?, ?, ?, ?)",
                               (key, stats["display"], stats["facet"], " | ".join(stats["samples"])))
            cursor.execute("INSERT OR REPLACE INTO files VALUES (?, ?, ?, ?)", (relative, mtime, size, "ok"))

    def forget_files(self, relatives: Iterable[str]) -> None:
        with self._lock:
            cursor = self.connection.cursor()
            for relative in relatives:
                for (key,) in list(cursor.execute("SELECT key FROM lists WHERE file=?", (relative,))):
                    cursor.execute("DELETE FROM lists_fts WHERE key=?", (key,))
                cursor.execute("DELETE FROM lists WHERE file=?", (relative,))
                cursor.execute("DELETE FROM files WHERE path=?", (relative,))

    def commit(self, built_at: Optional[float] = None) -> None:
        with self._lock:
            if built_at is not None:
                self.connection.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)", (str(built_at),))
            self.connection.commit()

    def rows(self) -> List[ListRow]:
        with self._lock:
            result = []
            for row in self.connection.execute(
                    "SELECT key, file, display, kind, dialect, entries, median_words, nsfw, nsfw_source, quality, "
                    "facet, signature, samples FROM lists"):
                result.append(ListRow(key=row[0], root=self.root, file=row[1], display=row[2], kind=row[3],
                                      dialect=row[4], entries=row[5], median_words=row[6], nsfw=row[7],
                                      nsfw_source=row[8], quality=row[9], facet=row[10], signature=row[11],
                                      samples=json.loads(row[12] or "[]")))
            return result

    def search(self, query: str, limit: int = 50, any_word: bool = True) -> List[str]:
        """
        FTS keys, best first. Words are prefix-matched ('hair col' finds hair_colors). Lists that
        have every word come first, then (any_word) lists that have any of them.
        """
        terms = [re.sub(r"[^\w]", "", word) for word in query.split()]
        terms = [term for term in terms if term]
        if not terms:
            return []
        # Packs write decades as 80s, 1980s or eighties; search all of them.
        decades = {"1920s": "twenties", "1930s": "thirties", "1940s": "forties", "1950s": "fifties",
                   "1960s": "sixties", "1970s": "seventies", "1980s": "eighties", "1990s": "nineties"}
        expanded = []
        for term in terms:
            match = re.fullmatch(r"(?:19)?([2-9]0)s", term.lower())
            if match:
                full = "19" + match.group(1) + "s"
                expanded.append("(" + " OR ".join(f"{alt}*" for alt in (full, match.group(1) + "s", decades[full])) + ")")
            else:
                expanded.append(f"{term}*")
        found: List[str] = []
        expressions = [" AND ".join(expanded)]
        if len(expanded) > 1 and any_word:
            expressions.append(" OR ".join(expanded))
        with self._lock:
            for expression in expressions:
                try:
                    # The list's name counts far more than a word that happens to appear in its samples.
                    rows = self.connection.execute(
                        "SELECT key FROM lists_fts WHERE lists_fts MATCH ? "
                        "ORDER BY bm25(lists_fts, 8.0, 10.0, 3.0, 1.0) LIMIT ?", (expression, limit)).fetchall()
                except sqlite3.OperationalError:
                    continue
                for (key,) in rows:
                    if key not in found:
                        found.append(key)
                if len(found) >= limit:
                    break
        return found[:limit]

    def close(self) -> None:
        with self._lock:
            self.connection.close()


def catalog_path_for(root: str, fallback_dir: str, writable_root: bool = True) -> str:
    if writable_root:
        candidate = os.path.join(root, CATALOG_FILE)
        try:
            with open(candidate, "ab"):
                pass
            return candidate
        except OSError:
            pass
    digest = hashlib.sha1(os.path.normcase(os.path.abspath(root)).encode("utf-8")).hexdigest()[:16]
    return os.path.join(fallback_dir, f"catalog_{digest}.sqlite")


class CatalogSet:
    """
    Catalogs for every search folder of one WildcardLibrary, plus the merged in-memory view the
    engine and the builders read (`row(key)`), with duplicate detection across folders.

    in_root_catalog(root) decides whether a folder gets its catalog inside it (True) or in
    `fallback_dir` (the package's own wildcards/ folder uses the cache, so git stays clean).
    """

    def __init__(self, library, fallback_dir: str, in_root_catalog: Callable[[str], bool] = lambda root: True):
        self.library = library
        self.fallback_dir = fallback_dir
        self.in_root_catalog = in_root_catalog
        self.catalogs: Dict[str, RootCatalog] = {}
        self._rows: Dict[str, ListRow] = {}
        self.version = 0
        self.status = {"state": "idle", "done": 0, "total": 0, "seconds": 0.0, "changed_files": 0, "error": ""}
        self._update_lock = threading.Lock()
        self._open_catalogs()
        self._reload_rows()

    # -- setup --------------------------------------------------------------------
    def _open_catalogs(self) -> None:
        for root in self.library.search_paths:
            if root in self.catalogs:
                continue
            try:
                path = catalog_path_for(root, self.fallback_dir, self.in_root_catalog(root))
                self.catalogs[root] = RootCatalog(root, path)
            except (OSError, sqlite3.Error) as error:
                self.status["error"] = f"catalog for {root} unavailable: {error}"

    def _reload_rows(self) -> None:
        """Merged rows: for a key in several folders the highest-priority folder's row wins."""
        rows: Dict[str, ListRow] = {}
        for root in reversed(self.library.search_paths):
            catalog = self.catalogs.get(root)
            if catalog is None:
                continue
            for row in catalog.rows():
                rows[row.key] = row
        # Identical lists in different packs: the best-scored one is the original, the others point to it.
        by_signature: Dict[str, List[ListRow]] = {}
        for row in rows.values():
            if row.entries >= 3:
                by_signature.setdefault(row.signature, []).append(row)
        for group in by_signature.values():
            if len(group) < 2:
                continue
            group.sort(key=lambda r: (-r.quality, len(r.key), r.key))
            for duplicate in group[1:]:
                duplicate.dup_of = group[0].key
        self._rows = rows
        self.version += 1

    # -- reading ------------------------------------------------------------------
    def row(self, key: str) -> Optional[ListRow]:
        return self._rows.get(key)

    def rows(self) -> Dict[str, ListRow]:
        return self._rows

    def search(self, query: str, limit: int = 50, any_word: bool = True) -> List[ListRow]:
        found: List[ListRow] = []
        seen = set()
        for root in self.library.search_paths:
            catalog = self.catalogs.get(root)
            if catalog is None:
                continue
            for key in catalog.search(query, limit, any_word):
                row = self._rows.get(key)
                if row is not None and key not in seen:
                    seen.add(key)
                    found.append(row)
        return found[:limit]

    # -- building -----------------------------------------------------------------
    def update(self, progress: Optional[Callable[[Dict], None]] = None) -> Dict:
        """Analyse new and changed files; forget removed ones. Returns the status dict."""
        if not self._update_lock.acquire(blocking=False):
            return dict(self.status)          # another update is running
        started = time.time()
        try:
            self.status.update(state="scanning", done=0, total=0, changed_files=0, error="")
            self._open_catalogs()
            sources = self.library.catalog_sources()   # root -> {relative file: (abs path, [keys], folder_nsfw)}
            work: List[Tuple[RootCatalog, str, str, List[str], float, int]] = []
            for root, files in sources.items():
                catalog = self.catalogs.get(root)
                if catalog is None:
                    continue
                known = catalog.known_files()
                for relative, (path, keys) in files.items():
                    if relative.startswith("_prompts/"):
                        continue        # prompt files are browsed by folder, not ranked or searched as lists
                    try:
                        stat = os.stat(path)
                    except OSError:
                        continue
                    if known.get(relative) != (stat.st_mtime, stat.st_size):
                        work.append((catalog, relative, path, keys, stat.st_mtime, stat.st_size))
                removed = set(known) - set(files)
                if removed:
                    catalog.forget_files(removed)
            self.status.update(state="analysing", total=len(work))
            for index, (catalog, relative, path, keys, mtime, size) in enumerate(work, 1):
                analysed = {}
                for key in keys:
                    texts, folder_nsfw, name_nsfw = self.library.catalog_entries(catalog.root, key)
                    analysed[key] = analyse(key, texts, folder_nsfw=folder_nsfw, name_nsfw=name_nsfw)
                catalog.replace_file(relative, mtime, size, analysed)
                self.status["done"] = index
                if index % 50 == 0:
                    catalog.commit()      # short write transactions: other processes can write in between
                    if progress:
                        progress(dict(self.status))
            for catalog in self.catalogs.values():
                catalog.commit(built_at=time.time())
            self.status.update(changed_files=len(work))
            self._reload_rows()
            self.status.update(state="ready")
        except Exception as error:  # a catalog problem must never break wildcard runs
            self.status.update(state="error", error=str(error))
        finally:
            self.status["seconds"] = round(time.time() - started, 2)
            self._update_lock.release()
        return dict(self.status)

    def close(self) -> None:
        for catalog in self.catalogs.values():
            catalog.close()
