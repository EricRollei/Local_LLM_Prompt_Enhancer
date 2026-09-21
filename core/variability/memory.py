"""
Repulsion memory: remembers what was generated recently so new output can steer away from it.

One SQLite file, <cache_dir>/variability_memory.sqlite, table outputs(id, created, embedder, text, vector).
Vectors from different embedders are never compared with each other.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Optional

import numpy as np

KEEP_PER_EMBEDDER = 1000


class RepulsionMemory:
    def __init__(self, cache_dir: str):
        os.makedirs(cache_dir, exist_ok=True)
        self.path = os.path.join(cache_dir, "variability_memory.sqlite")
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS outputs ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, created REAL NOT NULL, embedder TEXT NOT NULL, "
                "text TEXT NOT NULL, vector BLOB NOT NULL)"
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_outputs_embedder ON outputs(embedder, id)")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=30)

    def recent_vectors(self, embedder_name: str, last: int) -> Optional[np.ndarray]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT vector FROM outputs WHERE embedder = ? ORDER BY id DESC LIMIT ?", (embedder_name, int(last))
            ).fetchall()
        if not rows:
            return None
        return np.stack([np.frombuffer(row[0], dtype=np.float16).astype(np.float32) for row in rows], axis=0)

    def remember(self, embedder_name: str, text: str, vector: np.ndarray) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO outputs (created, embedder, text, vector) VALUES (?, ?, ?, ?)",
                (time.time(), embedder_name, text, vector.astype(np.float16).tobytes()),
            )
            connection.execute(
                "DELETE FROM outputs WHERE embedder = ? AND id NOT IN ("
                "SELECT id FROM outputs WHERE embedder = ? ORDER BY id DESC LIMIT ?)",
                (embedder_name, embedder_name, KEEP_PER_EMBEDDER),
            )

    def count(self, embedder_name: str) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM outputs WHERE embedder = ?", (embedder_name,)).fetchone()[0])

    def clear(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM outputs")
