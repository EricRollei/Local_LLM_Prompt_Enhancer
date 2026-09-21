"""
Prompt Database Backend
SQLite-based storage and retrieval for prompts with full-text search.

Author: Eric Hiss (GitHub: EricRollei)
"""

import sqlite3
import os
import json
import csv
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Database file lives next to this module
DB_PATH = os.path.join(os.path.dirname(__file__), "prompt_database.db")

# Platforms matching platforms.py keys
PLATFORMS = [
    "any",
    "flux",
    "flux_kontex",
    "pixart_sigma",
    "aura_flow",
    "noobai",
    "kolors",
    "hunyuan_image",
    "qwen_image",
    "qwen_image_edit",
    "sd_xl",
    "pony",
    "illustrious",
    "chroma",
    "wan_image",
    "wan_video",
    "alice_t2v",
    "other",
]


def _with_profile_platforms(names):
    """The list above, unchanged and in order, plus every platform profile id it does not have yet."""
    try:
        from .profile_support import profile_ids
        return list(names) + [profile_id for profile_id in profile_ids() if profile_id not in names]
    except Exception as error:  # the database must work even if the profiles folder is missing
        print(f"[Prompt Database] platform profiles unavailable, using the built-in list: {error}")
        return list(names)


PLATFORMS = _with_profile_platforms(PLATFORMS)

CATEGORIES = [
    "any",
    "character",
    "landscape",
    "architecture",
    "abstract",
    "portrait",
    "action",
    "still_life",
    "fantasy",
    "sci_fi",
    "horror",
    "romantic",
    "cinematic",
    "product",
    "concept_art",
    "photography",
    "animation",
    "other",
]


class PromptDatabase:
    """SQLite prompt database with FTS5 full-text search."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._ensure_db()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _ensure_db(self):
        """Create tables if they don't exist."""
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS prompts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_text     TEXT    NOT NULL,
                negative_prompt TEXT    DEFAULT '',
                category        TEXT    DEFAULT 'any',
                platform        TEXT    DEFAULT 'any',
                tags            TEXT    DEFAULT '',
                rating          INTEGER DEFAULT 0,
                source          TEXT    DEFAULT 'manual',
                notes           TEXT    DEFAULT '',
                favorite        INTEGER DEFAULT 0,
                created_at      TEXT    NOT NULL,
                updated_at      TEXT    NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category);
            CREATE INDEX IF NOT EXISTS idx_prompts_platform ON prompts(platform);
            CREATE INDEX IF NOT EXISTS idx_prompts_rating   ON prompts(rating);
            CREATE INDEX IF NOT EXISTS idx_prompts_favorite ON prompts(favorite);
        """)

        # FTS5 virtual table for fast keyword search
        # Check whether it already exists before creating
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='prompts_fts'"
        ).fetchone()
        if row is None:
            conn.execute("""
                CREATE VIRTUAL TABLE prompts_fts USING fts5(
                    prompt_text,
                    negative_prompt,
                    tags,
                    notes,
                    content='prompts',
                    content_rowid='id'
                );
            """)
            # Populate FTS from any pre-existing rows
            conn.execute("""
                INSERT INTO prompts_fts(rowid, prompt_text, negative_prompt, tags, notes)
                SELECT id, prompt_text, negative_prompt, tags, notes FROM prompts;
            """)

        # Triggers to keep FTS in sync
        conn.executescript("""
            CREATE TRIGGER IF NOT EXISTS prompts_ai AFTER INSERT ON prompts BEGIN
                INSERT INTO prompts_fts(rowid, prompt_text, negative_prompt, tags, notes)
                VALUES (new.id, new.prompt_text, new.negative_prompt, new.tags, new.notes);
            END;

            CREATE TRIGGER IF NOT EXISTS prompts_ad AFTER DELETE ON prompts BEGIN
                INSERT INTO prompts_fts(prompts_fts, rowid, prompt_text, negative_prompt, tags, notes)
                VALUES ('delete', old.id, old.prompt_text, old.negative_prompt, old.tags, old.notes);
            END;

            CREATE TRIGGER IF NOT EXISTS prompts_au AFTER UPDATE ON prompts BEGIN
                INSERT INTO prompts_fts(prompts_fts, rowid, prompt_text, negative_prompt, tags, notes)
                VALUES ('delete', old.id, old.prompt_text, old.negative_prompt, old.tags, old.notes);
                INSERT INTO prompts_fts(rowid, prompt_text, negative_prompt, tags, notes)
                VALUES (new.id, new.prompt_text, new.negative_prompt, new.tags, new.notes);
            END;
        """)

        conn.commit()

    def _connect(self) -> sqlite3.Connection:
        """Return the persistent connection (create if needed)."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save_prompt(
        self,
        prompt_text: str,
        negative_prompt: str = "",
        category: str = "any",
        platform: str = "any",
        tags: str = "",
        rating: int = 0,
        source: str = "manual",
        notes: str = "",
        favorite: bool = False,
    ) -> int:
        """Insert a prompt and return its id."""
        now = datetime.now().isoformat(timespec="seconds")
        conn = self._connect()
        cur = conn.execute(
            """INSERT INTO prompts
               (prompt_text, negative_prompt, category, platform,
                tags, rating, source, notes, favorite, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                prompt_text.strip(),
                negative_prompt.strip(),
                category,
                platform,
                tags.strip(),
                max(0, min(5, rating)),
                source,
                notes.strip(),
                int(favorite),
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid

    def update_prompt(self, prompt_id: int, **fields) -> bool:
        """Update specified fields on a prompt row."""
        allowed = {
            "prompt_text", "negative_prompt", "category", "platform",
            "tags", "rating", "source", "notes", "favorite",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False
        updates["updated_at"] = datetime.now().isoformat(timespec="seconds")
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [prompt_id]
        conn = self._connect()
        conn.execute(f"UPDATE prompts SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return True

    def delete_prompt(self, prompt_id: int) -> bool:
        """Delete a prompt by id."""
        conn = self._connect()
        cur = conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        conn.commit()
        return cur.rowcount > 0

    def get_prompt(self, prompt_id: int) -> Optional[Dict]:
        """Get a single prompt by id."""
        conn = self._connect()
        row = conn.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,)).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str = "",
        category: str = "any",
        platform: str = "any",
        min_rating: int = 0,
        favorites_only: bool = False,
        tags_filter: str = "",
        limit: int = 20,
        offset: int = 0,
        order_by: str = "newest",
    ) -> Tuple[List[Dict], int]:
        """
        Search prompts.  Returns (results, total_count).

        query: FTS5 keyword search (supports AND, OR, NOT, "phrases")
        category / platform: filter or 'any' for all
        min_rating: 0-5
        tags_filter: comma-separated tags – all must be present
        order_by: newest | oldest | rating | random
        """
        conditions = []
        params: list = []
        use_fts = bool(query.strip())

        if use_fts:
            # Sanitise the user query for FTS5
            safe_query = self._sanitise_fts_query(query)
            conditions.append("p.id IN (SELECT rowid FROM prompts_fts WHERE prompts_fts MATCH ?)")
            params.append(safe_query)

        if category and category != "any":
            conditions.append("p.category = ?")
            params.append(category)

        if platform and platform != "any":
            conditions.append("p.platform = ?")
            params.append(platform)

        if min_rating > 0:
            conditions.append("p.rating >= ?")
            params.append(min_rating)

        if favorites_only:
            conditions.append("p.favorite = 1")

        if tags_filter.strip():
            for tag in [t.strip().lower() for t in tags_filter.split(",") if t.strip()]:
                conditions.append("LOWER(p.tags) LIKE ?")
                params.append(f"%{tag}%")

        where = " AND ".join(conditions) if conditions else "1=1"

        order_map = {
            "newest": "p.created_at DESC",
            "oldest": "p.created_at ASC",
            "rating": "p.rating DESC, p.created_at DESC",
            "random": "RANDOM()",
        }
        order = order_map.get(order_by, "p.created_at DESC")

        conn = self._connect()
        # Count
        count_row = conn.execute(
            f"SELECT COUNT(*) FROM prompts p WHERE {where}", params
        ).fetchone()
        total = count_row[0] if count_row else 0

        # Results
        rows = conn.execute(
            f"SELECT p.* FROM prompts p WHERE {where} ORDER BY {order} LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

        results = [dict(r) for r in rows]
        return results, total

    @staticmethod
    def _sanitise_fts_query(raw: str) -> str:
        """
        Turn a user-typed search string into a valid FTS5 query.
        Wraps each word with quotes and joins with OR so partial phrases
        are forgiving. Quoted phrases from the user are kept intact.
        """
        # Preserve user-quoted phrases
        phrases = re.findall(r'"([^"]+)"', raw)
        remainder = re.sub(r'"[^"]*"', '', raw)
        tokens = [t.strip() for t in remainder.split() if t.strip()]
        parts = [f'"{p}"' for p in phrases]
        parts += [f'"{t}"' for t in tokens]
        return " OR ".join(parts) if parts else '""'

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def import_from_text_file(
        self,
        file_path: str,
        category: str = "any",
        platform: str = "any",
        tags: str = "",
        delimiter: str = "newline",
        skip_duplicates: bool = True,
    ) -> Tuple[int, int, List[str]]:
        """
        Import prompts from a text file.

        delimiter:
          'newline'  – one prompt per line
          'double_newline' – prompts separated by blank lines
          'paragraph' – same as double_newline

        Returns (imported_count, skipped_count, errors)
        """
        if not os.path.isfile(file_path):
            return 0, 0, [f"File not found: {file_path}"]

        errors: List[str] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return 0, 0, [f"Error reading file: {e}"]

        if delimiter in ("double_newline", "paragraph"):
            raw_prompts = re.split(r"\n\s*\n", content)
        else:
            raw_prompts = content.splitlines()

        prompts = [p.strip() for p in raw_prompts if p.strip()]
        return self._bulk_insert(prompts, category, platform, tags, "import_txt", skip_duplicates, errors)

    def import_from_csv(
        self,
        file_path: str,
        category: str = "any",
        platform: str = "any",
        tags: str = "",
        skip_duplicates: bool = True,
    ) -> Tuple[int, int, List[str]]:
        """
        Import from CSV.  Expected columns (header row required):
          prompt_text (required), negative_prompt, category, platform, tags, rating, notes
        Missing columns use defaults.
        """
        if not os.path.isfile(file_path):
            return 0, 0, [f"File not found: {file_path}"]

        errors: List[str] = []
        imported = 0
        skipped = 0

        try:
            with open(file_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    text = (row.get("prompt_text") or "").strip()
                    if not text:
                        errors.append(f"Row {row_num}: empty prompt_text, skipped")
                        skipped += 1
                        continue

                    if skip_duplicates and self._exists(text):
                        skipped += 1
                        continue

                    self.save_prompt(
                        prompt_text=text,
                        negative_prompt=(row.get("negative_prompt") or "").strip(),
                        category=row.get("category", category).strip() or category,
                        platform=row.get("platform", platform).strip() or platform,
                        tags=row.get("tags", tags).strip() or tags,
                        rating=int(row.get("rating", 0) or 0),
                        source="import_csv",
                        notes=(row.get("notes") or "").strip(),
                    )
                    imported += 1
        except Exception as e:
            errors.append(f"CSV parse error: {e}")

        return imported, skipped, errors

    def import_from_json(
        self,
        file_path: str,
        category: str = "any",
        platform: str = "any",
        tags: str = "",
        skip_duplicates: bool = True,
    ) -> Tuple[int, int, List[str]]:
        """
        Import from JSON.  Expects either:
          - A JSON array of strings (plain prompts)
          - A JSON array of objects with at least {"prompt_text": "..."}
        """
        if not os.path.isfile(file_path):
            return 0, 0, [f"File not found: {file_path}"]

        errors: List[str] = []
        imported = 0
        skipped = 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return 0, 0, [f"JSON parse error: {e}"]

        if not isinstance(data, list):
            return 0, 0, ["JSON root must be an array"]

        for i, item in enumerate(data):
            if isinstance(item, str):
                text = item.strip()
                neg = ""
                item_cat = category
                item_plat = platform
                item_tags = tags
                item_rating = 0
                item_notes = ""
            elif isinstance(item, dict):
                text = (item.get("prompt_text") or item.get("prompt") or "").strip()
                neg = (item.get("negative_prompt") or "").strip()
                item_cat = (item.get("category") or category).strip()
                item_plat = (item.get("platform") or platform).strip()
                item_tags = (item.get("tags") or tags).strip()
                item_rating = int(item.get("rating", 0) or 0)
                item_notes = (item.get("notes") or "").strip()
            else:
                errors.append(f"Item {i}: unexpected type {type(item).__name__}, skipped")
                skipped += 1
                continue

            if not text:
                skipped += 1
                continue

            if skip_duplicates and self._exists(text):
                skipped += 1
                continue

            self.save_prompt(
                prompt_text=text,
                negative_prompt=neg,
                category=item_cat,
                platform=item_plat,
                tags=item_tags,
                rating=item_rating,
                source="import_json",
                notes=item_notes,
            )
            imported += 1

        return imported, skipped, errors

    # ------------------------------------------------------------------
    # Stats / helpers
    # ------------------------------------------------------------------

    def stats(self) -> Dict:
        """Return summary statistics about the database."""
        conn = self._connect()
        total = conn.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
        favorites = conn.execute("SELECT COUNT(*) FROM prompts WHERE favorite=1").fetchone()[0]
        by_cat = {
            r[0]: r[1]
            for r in conn.execute(
                "SELECT category, COUNT(*) FROM prompts GROUP BY category ORDER BY COUNT(*) DESC"
            ).fetchall()
        }
        by_plat = {
            r[0]: r[1]
            for r in conn.execute(
                "SELECT platform, COUNT(*) FROM prompts GROUP BY platform ORDER BY COUNT(*) DESC"
            ).fetchall()
        }
        return {
            "total_prompts": total,
            "favorites": favorites,
            "by_category": by_cat,
            "by_platform": by_plat,
        }

    def _exists(self, prompt_text: str) -> bool:
        """Check if exact prompt_text already present."""
        conn = self._connect()
        row = conn.execute(
            "SELECT 1 FROM prompts WHERE prompt_text = ? LIMIT 1",
            (prompt_text.strip(),),
        ).fetchone()
        return row is not None

    def _bulk_insert(
        self,
        prompts: List[str],
        category: str,
        platform: str,
        tags: str,
        source: str,
        skip_duplicates: bool,
        errors: List[str],
    ) -> Tuple[int, int, List[str]]:
        """Insert a list of plain-text prompts."""
        imported = 0
        skipped = 0
        for text in prompts:
            if skip_duplicates and self._exists(text):
                skipped += 1
                continue
            try:
                self.save_prompt(
                    prompt_text=text,
                    category=category,
                    platform=platform,
                    tags=tags,
                    source=source,
                )
                imported += 1
            except Exception as e:
                errors.append(f"Insert error: {e}")
                skipped += 1
        return imported, skipped, errors

    def export_to_json(self, file_path: str, **search_kwargs) -> int:
        """Export search results (or everything) to a JSON file."""
        results, _ = self.search(limit=999999, **search_kwargs)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        return len(results)

    def export_to_txt(self, file_path: str, **search_kwargs) -> int:
        """Export prompt texts to a plain text file, one per line."""
        results, _ = self.search(limit=999999, **search_kwargs)
        with open(file_path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(r["prompt_text"] + "\n")
        return len(results)
