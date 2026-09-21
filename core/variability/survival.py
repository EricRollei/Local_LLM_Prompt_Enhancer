"""
Concept survival: did the meaning of each randomly chosen concept make it through the LLM rewrite?

A concept-bound wildcard pick may be reworded freely ("rusty" -> "oxidised steel flaking orange at the
seams"), so a string search cannot check it. This does it in embedding space: the rewritten prompt
is cut into overlapping windows of words, every window and every concept is embedded, and a
concept's score is its best cosine against any window. The best window is reported too - that is
the phrase carrying the concept, or, when the score is low, the nearest the prompt comes to it.

Scores depend on the embedder, so the threshold is a setting, not a constant. Measured with
Qwen3-VL-Embedding-2B (dev/try_directions_and_survival.py), on things, materials and places: a faithful
paraphrase scores 0.69-0.74, the same scene with the pick dropped or normalised 0.43-0.60, an unrelated
prompt 0.26-0.45. Anything the prompt states word for word scores 1.0 without being embedded.

Known limit, also measured: relations and conditions ("lit only from below", "the weather is indoors")
do NOT separate - an embedding hears the topic, not the relation, so window light scores as high as
light from below. The Concept Survival Check node offers an LLM judge for those.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

import numpy as np

from .embedders import Embedder

WINDOW_SIZES = (4, 6, 10, 16, 24)   # words per window
MAX_WINDOWS = 1200


@dataclass
class ConceptScore:
    concept: str
    score: float
    carried_by: str
    survived: bool


def text_windows(text: str, min_words: int = 1) -> List[str]:
    """
    Clauses, sentences and sliding word windows of several sizes, de-duplicated, in reading order.
    min_words drops fragments shorter than that: very short fragments ("room with a") embed vaguely and
    score deceptively high against anything on the same topic.
    """
    flat = " ".join((text or "").split())
    if not flat:
        return []
    windows: List[str] = []
    seen = set()

    def add(candidate: str) -> None:
        cleaned = candidate.strip(" ,.;:-")
        if len(cleaned) > 2 and len(cleaned.split()) >= min_words and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            windows.append(cleaned)

    for sentence in re.split(r"(?<=[.!?;])\s+", flat):
        add(sentence)
        for clause in re.split(r",\s+", sentence):
            add(clause)
    words = flat.split(" ")
    for size in WINDOW_SIZES:
        if size < min_words or len(words) <= size:
            continue
        stride = max(1, size // 3)
        for start in range(0, len(words) - size + 1, stride):
            add(" ".join(words[start:start + size]))
    if not windows:
        add(flat) if len(flat.split()) >= 1 else None
        if not windows:
            windows.append(flat)
    return windows[:MAX_WINDOWS]


def score_concepts(embedder: Embedder, prompt: str, concepts: List[str], threshold: float) -> List[ConceptScore]:
    concepts = [concept for concept in concepts if concept and concept.strip()]
    if not concepts:
        return []
    lowered = " ".join((prompt or "").lower().split())
    # Compare like with like: a window is never shorter than the longest concept, and never under 4 words.
    longest = max(len(concept.split()) for concept in concepts)
    windows = text_windows(prompt, min_words=max(4, longest))

    results: List[ConceptScore] = []
    to_embed = [concept for concept in concepts if " ".join(concept.lower().split()) not in lowered]
    window_vectors = concept_vectors = None
    if to_embed and windows:
        window_vectors = embedder.encode(windows)
        concept_vectors = embedder.encode(to_embed)

    for concept in concepts:
        if concept not in to_embed:
            results.append(ConceptScore(concept, 1.0, concept, True))
            continue
        if window_vectors is None:
            results.append(ConceptScore(concept, 0.0, "", False))
            continue
        similarities = window_vectors @ concept_vectors[to_embed.index(concept)]
        best = int(np.argmax(similarities))
        score = float(similarities[best])
        results.append(ConceptScore(concept, score, windows[best], score >= threshold))
    return results
