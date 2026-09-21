"""
Semantic moves over a set of candidate phrases. Pure numpy, no model, no I/O.

All distances are RANK based, not raw cosine. Cosine ranges differ wildly between embedders
(CLIP text vectors sit at 0.6-0.95, sentence models at 0.1-0.8), so strength is defined over the
list's neighbour ranking, which keeps one dial meaningful whichever embedder is loaded.

The dial is quadratic: target rank = strength^2 of the way from nearest to farthest.
    0.1 -> the nearest 1%      0.35 -> ~12%      0.5 -> 25%      0.7 -> ~50%      1.0 -> the farthest
A linear dial wasted its low end: on a 2,000-entry list, 0.1 meant "neighbour number 200", which
is not near anything. Squaring gives fine control where it matters and still reaches the far end.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import random
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np

WINDOW = 4  # how many neighbours around the target rank a pick is drawn from


def ranked_neighbours(vectors: np.ndarray, base_index: int, exclude: Iterable[int] = ()) -> Tuple[List[int], np.ndarray]:
    """Indices of every other candidate, nearest first, and the full similarity row."""
    similarities = vectors @ vectors[base_index]
    blocked = set(exclude) | {base_index}
    order = [int(i) for i in np.argsort(-similarities) if int(i) not in blocked]
    return order, similarities


def neighbour_pick(vectors: np.ndarray, base_index: int, strength: float, rng: random.Random,
                   exclude: Iterable[int] = ()) -> Tuple[int, int, int, float]:
    """
    Move from `base_index` to a semantic neighbour.

    strength 0.0 -> stay; ~0.1 -> one of the nearest few; 0.5 -> a quarter of the way out; 1.0 -> one of the farthest few.
    Returns (picked index, its rank with 1 = nearest, number ranked, cosine to the base).
    """
    strength = max(0.0, min(1.0, float(strength)))
    order, similarities = ranked_neighbours(vectors, base_index, exclude)
    if strength <= 0.0 or not order:
        return base_index, 0, len(order), 1.0

    target = (strength ** 2) * (len(order) - 1)
    low = int(max(0, min(len(order) - WINDOW, round(target - (WINDOW - 1) / 2))))
    window = order[low:low + WINDOW] or order
    picked = window[rng.randrange(len(window))]
    return picked, order.index(picked) + 1, len(order), float(similarities[picked])


def farthest_point_select(vectors: np.ndarray, count: int, first: int = 0) -> List[int]:
    """Greedy max-min selection: a subset of `count` rows that are as mutually different as possible."""
    total = vectors.shape[0]
    if total == 0:
        return []
    count = max(1, min(count, total))
    chosen = [first]
    nearest = vectors @ vectors[first]           # similarity of each row to its closest chosen row
    while len(chosen) < count:
        masked = nearest.copy()
        masked[chosen] = np.inf
        next_index = int(np.argmin(masked))
        chosen.append(next_index)
        nearest = np.maximum(nearest, vectors @ vectors[next_index])
    return chosen


def max_similarity(vector: np.ndarray, others: Optional[np.ndarray]) -> float:
    """Highest cosine between `vector` and any row of `others`; 0.0 when there is nothing to compare to."""
    if others is None or others.size == 0:
        return 0.0
    return float(np.max(others @ vector))


def direction(positive: np.ndarray, negative: np.ndarray) -> np.ndarray:
    """Unit vector from the centroid of `negative` exemplars to the centroid of `positive` ones."""
    delta = positive.mean(axis=0) - negative.mean(axis=0)
    norm = float(np.linalg.norm(delta))
    return delta / norm if norm else delta


def direction_pick(vectors: np.ndarray, base_index: int, direction_vector: np.ndarray, amount: float,
                   exclude: Sequence[int] = ()) -> int:
    """Candidate nearest to base + amount * direction (e.g. ordinary -> uncanny), excluding the base itself."""
    target = vectors[base_index] + float(amount) * direction_vector
    norm = float(np.linalg.norm(target))
    if norm:
        target = target / norm
    scores = vectors @ target
    blocked = set(exclude) | {base_index}
    for index in np.argsort(-scores):
        if int(index) not in blocked:
            return int(index)
    return base_index


def leaning_pick(vectors: np.ndarray, base_index: int, direction_vector: np.ndarray, amount: float,
                 strength: float, rng: random.Random, exclude: Iterable[int] = ()) -> Tuple[int, int, int, float, float]:
    """
    A neighbour move with a lean. Every candidate is scored
        similarity to the base  +  amount * (how far it lies along the direction)
    and the pick is drawn from the best-scoring few. `strength` sets how many "few" is, on the same
    quadratic scale as neighbour_pick, so the two dials keep their meaning: strength = how far from
    the base a slot may go, amount = which way it leans (negative = toward the axis's `from` side).

    Returns (picked index, its plain-similarity rank with 1 = nearest, number ranked, cosine to the
    base, lean) where lean = how much further along the axis the pick lies than the base did.
    """
    order, similarities = ranked_neighbours(vectors, base_index, exclude)
    if not order:
        return base_index, 0, 0, 1.0, 0.0
    along = vectors @ direction_vector
    scores = similarities + float(amount) * along
    by_score = sorted(order, key=lambda index: -float(scores[index]))
    strength = max(0.0, min(1.0, float(strength)))
    pool_size = max(WINDOW, int(round((strength ** 2) * len(by_score))))
    pool = by_score[:pool_size]
    picked = pool[rng.randrange(len(pool))]
    lean = float(along[picked] - along[base_index])
    return picked, order.index(picked) + 1, len(order), float(similarities[picked]), lean

