"""
On-disk cache of phrase vectors, one SQLite file per embedder.

Embedding is the slow part, so every phrase is embedded once per embedder and kept:
    <cache_dir>/vectors_<embedder name>.sqlite      table vectors(text_hash PRIMARY KEY, vector BLOB float16)

Lookups are lazy: only the phrases a run actually needs (the siblings of the lists it used)
are embedded, so a 126,000-entry library costs nothing until a list is touched, and a list
is only ever embedded once.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
from typing import Dict, List

import numpy as np

from .embedders import Embedder


def _text_hash(text: str) -> str:
    return hashlib.sha1(text.strip().lower().encode("utf-8")).hexdigest()


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


class VectorCache:
    def __init__(self, embedder: Embedder, cache_dir: str):
        self.embedder = embedder
        os.makedirs(cache_dir, exist_ok=True)
        self.path = os.path.join(cache_dir, f"vectors_{_safe_name(embedder.name)}.sqlite")
        self._memory: Dict[str, np.ndarray] = {}
        self.embedded_this_session = 0
        with self._connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS vectors (text_hash TEXT PRIMARY KEY, vector BLOB NOT NULL)")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=30)

    def vectors(self, texts: List[str]) -> np.ndarray:
        """Float32 [len(texts), dim], L2-normalised, in the order given. Embeds only what is missing."""
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)
        hashes = [_text_hash(text) for text in texts]

        missing_from_memory = [h for h in dict.fromkeys(hashes) if h not in self._memory]
        if missing_from_memory:
            with self._connect() as connection:
                for start in range(0, len(missing_from_memory), 500):
                    chunk = missing_from_memory[start:start + 500]
                    marks = ",".join("?" * len(chunk))
                    for text_hash, blob in connection.execute(
                            f"SELECT text_hash, vector FROM vectors WHERE text_hash IN ({marks})", chunk):
                        self._memory[text_hash] = np.frombuffer(blob, dtype=np.float16).astype(np.float32)

        to_embed: Dict[str, str] = {}
        for text_hash, text in zip(hashes, texts):
            if text_hash not in self._memory and text_hash not in to_embed:
                to_embed[text_hash] = text
        if to_embed:
            new_vectors = self.embedder.encode(list(to_embed.values()))
            rows = []
            for text_hash, vector in zip(to_embed.keys(), new_vectors):
                # Keep in memory exactly what goes to disk (float16), so a ranking computed in the session
                # that embedded a list is identical to the one computed from the cache after a restart.
                stored = vector.astype(np.float16)
                self._memory[text_hash] = stored.astype(np.float32)
                rows.append((text_hash, stored.tobytes()))
            with self._connect() as connection:
                connection.executemany("INSERT OR REPLACE INTO vectors (text_hash, vector) VALUES (?, ?)", rows)
            self.embedded_this_session += len(rows)

        return np.stack([self._memory[text_hash] for text_hash in hashes], axis=0)

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM vectors").fetchone()[0])
