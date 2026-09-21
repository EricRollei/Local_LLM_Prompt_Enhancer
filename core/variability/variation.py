"""
Semantic variation of a wildcard prompt.

The idea (Eric's): keep the meaning of a prompt, but let most of its ideas drift a little and a
few of them jump, in embedding space - then let an LLM rewrite the result. A prompt is not one
vector, and single dimensions of a dense embedding mean nothing on their own, so the drift is
applied per SLOT: every wildcard or {a|b} choice in the prompt is a slot, its list is the set of
real phrases it may land on, and "decoding" a moved vector is simply choosing the list entry
that sits at the wanted distance. The output is always real language.

    base pass      resolve the prompt with `seed`            -> the picks a plain run would make
    varied pass    same seed, but each top-level pick is moved to a semantic neighbour in its own list
                   strength 0.1 = one of the nearest few ... 1.0 = one of the farthest few
                   `far_jumps` slots, chosen by the variation number, jump with `far_strength` instead
    avoid_recent   make several candidate variations, embed each whole prompt, keep the one least
                   similar to what was generated recently, and remember it

`variation` numbers are reproducible: same text + seed + variation + settings + lists + embedder
gives the same result (with avoid_recent on, the memory is part of the state by design).

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .directions import NONE, DirectionAxis
from .embedders import Embedder
from .memory import RepulsionMemory
from .moves import direction, leaning_pick, max_similarity, neighbour_pick
from .vector_cache import VectorCache


@dataclass
class VariationSettings:
    variation: int = 1            # 0 = the base prompt, untouched
    strength: float = 0.35        # drift applied to every slot
    far_jumps: int = 0            # how many slots jump instead of drifting
    far_strength: float = 0.9
    avoid_recent: bool = False
    attempts: int = 4             # candidate variations compared when avoid_recent is on
    recent_window: int = 50       # how many remembered outputs to steer away from
    max_candidates: int = 1500    # lists longer than this are sampled (stable sample, base always kept)
    direction: str = NONE         # name of a direction axis (variability/directions.yaml), or "none"
    direction_amount: float = 0.0 # > 0 leans every move toward the axis's `to` side, < 0 toward `from`


@dataclass
class SlotMove:
    source: str
    key: str
    base: str
    varied: str
    rank: int
    ranked: int
    cosine: float
    jumped: bool
    lean: Optional[float] = None  # movement along the direction axis; None when no direction was used


@dataclass
class VariationResult:
    resolution: Any                       # core.wildcards Resolution of the chosen variation
    base_text: str
    moves: List[SlotMove] = field(default_factory=list)
    embedder: str = ""
    attempts_tried: int = 1
    similarity_to_recent: Optional[float] = None
    newly_embedded: int = 0
    notes: List[str] = field(default_factory=list)

    def report(self) -> str:
        lines = [f"embedder: {self.embedder}"]
        if not self.moves:
            lines.append("no slots moved")
        for move in self.moves:
            tag = "JUMP " if move.jumped else "drift"
            name = move.key or move.source
            if move.base == move.varied:
                lines.append(f"  {tag} {name}: {move.base}  (unchanged)")
            else:
                lean = "" if move.lean is None else f", lean {move.lean:+.3f}"
                lines.append(f"  {tag} {name}: {move.base}  ->  {move.varied}   "
                             f"[neighbour {move.rank} of {move.ranked}, cos {move.cosine:.2f}{lean}]")
        if self.similarity_to_recent is not None:
            lines.append(f"avoid_recent: best of {self.attempts_tried} candidates, "
                         f"closest remembered output at cos {self.similarity_to_recent:.2f}")
        if self.newly_embedded:
            lines.append(f"embedded {self.newly_embedded} new phrases (cached for next time)")
        lines.extend(self.notes)
        return "\n".join(lines)


def _stable_subset(candidates: List[str], keep: List[int], limit: int) -> List[int]:
    """Indices of at most `limit` candidates: always `keep`, the rest chosen by text hash (stable across runs)."""
    if len(candidates) <= limit:
        return list(range(len(candidates)))
    by_hash = sorted(range(len(candidates)), key=lambda i: hashlib.md5(candidates[i].encode("utf-8")).hexdigest())
    chosen = list(dict.fromkeys(list(keep) + by_hash))[:limit]
    return sorted(chosen)


class SemanticVariator:
    def __init__(self, engine: Any, embedder: Embedder, cache_dir: str,
                 directions: Optional[Dict[str, DirectionAxis]] = None):
        self.engine = engine
        self.embedder = embedder
        self.cache = VectorCache(embedder, cache_dir)
        self.memory = RepulsionMemory(cache_dir)
        self.directions: Dict[str, DirectionAxis] = directions or {}
        self._direction_vectors: Dict[str, np.ndarray] = {}

    def direction_vector(self, name: str) -> Optional[np.ndarray]:
        """Unit vector of a named axis in this embedder's space, or None for "none" / unknown names."""
        if not name or name == NONE or name not in self.directions:
            return None
        if name not in self._direction_vectors:
            axis = self.directions[name]
            self._direction_vectors[name] = direction(self.cache.vectors(axis.end), self.cache.vectors(axis.start))
        return self._direction_vectors[name]

    # -- one varied pass -------------------------------------------------------------
    def _varied_pass(self, text: str, seed: Optional[int], settings: VariationSettings, attempt: int,
                     base_picks: List[Tuple[int, List[int]]], process_kwargs: Dict[str, Any]) -> Tuple[Any, List[SlotMove]]:
        variation_rng = random.Random(f"{seed}|{settings.variation}|{attempt}")
        slot_count = len(base_picks)
        jump_slots = set(variation_rng.sample(range(slot_count), min(max(0, settings.far_jumps), slot_count)))
        axis_vector = self.direction_vector(settings.direction) if settings.direction_amount else None
        moves: List[SlotMove] = []
        ordinal = {"value": -1}

        def hook(context):
            if context.depth != 0:
                return None
            ordinal["value"] += 1
            position = ordinal["value"]

            # Start from the BASE pass's pick for this slot, so an earlier slot that changed (and drew a
            # different amount of randomness) cannot knock later slots off their base picks.
            chosen = list(context.chosen)
            if position < len(base_picks):
                expected_count, expected_chosen = base_picks[position]
                if expected_count == len(context.candidates) and len(expected_chosen) == len(chosen):
                    chosen = list(expected_chosen)

            jumped = position in jump_slots
            strength = settings.far_strength if jumped else settings.strength
            if strength <= 0 or len(context.candidates) < 2:
                return chosen

            subset = _stable_subset(context.candidates, chosen, settings.max_candidates)
            vectors = self.cache.vectors([context.candidates[i] for i in subset])
            local = {original: row for row, original in enumerate(subset)}

            result: List[int] = []
            for base_index in chosen:
                taken = [local[i] for i in result] + [local[i] for i in chosen if i != base_index]
                lean: Optional[float] = None
                if axis_vector is not None:
                    picked_row, rank, ranked, cosine, lean = leaning_pick(
                        vectors, local[base_index], axis_vector, settings.direction_amount, strength,
                        variation_rng, exclude=taken)
                else:
                    picked_row, rank, ranked, cosine = neighbour_pick(
                        vectors, local[base_index], strength, variation_rng, exclude=taken)
                picked = subset[picked_row]
                result.append(picked)
                moves.append(SlotMove(
                    source=context.source, key=context.key,
                    base=context.candidates[base_index], varied=context.candidates[picked],
                    rank=rank, ranked=ranked, cosine=cosine, jumped=jumped, lean=lean,
                ))
            return result

        resolution = self.engine.process(text, seed=seed, pick_hook=hook, **process_kwargs)
        return resolution, moves

    # -- public ------------------------------------------------------------------------
    def vary(self, text: str, seed: Optional[int], settings: VariationSettings, **process_kwargs: Any) -> VariationResult:
        base_picks: List[Tuple[int, List[int]]] = []

        def recorder(context):
            if context.depth == 0:
                base_picks.append((len(context.candidates), list(context.chosen)))
            return None

        base = self.engine.process(text, seed=seed, pick_hook=recorder, **process_kwargs)
        result = VariationResult(resolution=base, base_text=base.text, embedder=self.embedder.describe())

        nothing_to_do = settings.variation == 0 or (settings.strength <= 0 and settings.far_jumps <= 0)
        if settings.direction and settings.direction != NONE and settings.direction_amount:
            if settings.direction in self.directions:
                axis = self.directions[settings.direction]
                side = "to" if settings.direction_amount > 0 else "from"
                result.notes.append(f"direction: {axis.name} ({axis.description}), amount {settings.direction_amount:+.2f} -> leaning toward its `{side}` side")
            else:
                result.notes.append(f"direction '{settings.direction}' is not defined in variability/directions.yaml; ignored")
        if nothing_to_do or not base_picks:
            if not base_picks:
                result.notes.append("the prompt has no wildcard or {a|b} slots, so there is nothing to vary")
            return result

        embedded_before = self.cache.embedded_this_session
        attempts = max(1, settings.attempts) if settings.avoid_recent else 1
        recent = self.memory.recent_vectors(self.embedder.name, settings.recent_window) if settings.avoid_recent else None

        best: Optional[Tuple[float, Any, List[SlotMove], Any]] = None
        for attempt in range(attempts):
            resolution, moves = self._varied_pass(text, seed, settings, attempt, base_picks, process_kwargs)
            if not settings.avoid_recent:
                best = (0.0, resolution, moves, None)
                break
            vector = self.cache.embedder.encode([resolution.text])[0]
            closeness = max_similarity(vector, recent)
            if best is None or closeness < best[0]:
                best = (closeness, resolution, moves, vector)

        closeness, resolution, moves, vector = best
        result.resolution = resolution
        result.moves = moves
        result.attempts_tried = attempts
        result.newly_embedded = self.cache.embedded_this_session - embedded_before
        if settings.avoid_recent:
            result.similarity_to_recent = closeness
            self.memory.remember(self.embedder.name, resolution.text, vector)
        return result
