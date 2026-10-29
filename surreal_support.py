"""
Surreal engine support shared by the nodes: builds the engine on the package's wildcard library (so the user's
packs and their iconography file take part), connects the prompt database as the personal archive, and offers
the one call the existing presets use.

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

import os
import random
import re
from typing import Any, Callable, List, Optional, Tuple

from .core.strategies.surreal import SurrealEngine, SurrealResult, SurrealSettings, SurrealSources, parse_critic
from .core.strategies.surreal.scene import parse_scene_inventory, scene_messages
from .wildcard_support import get_wildcard_engine

ARCHIVE_POOL = 200
ARCHIVE_WORDS = 28


def _archive(seed: int) -> Optional[Callable[[str, int], List[str]]]:
    """Fragments of the user's own saved prompts, or None when there is no database yet (never creates one)."""
    try:
        from .prompt_database import DB_PATH, PromptDatabase
        if not os.path.isfile(DB_PATH):
            return None
        rows, total = PromptDatabase().search(query="", limit=ARCHIVE_POOL, order_by="oldest")
        texts = [str(row.get("prompt_text") or "").strip() for row in rows]
        texts = [text for text in texts if len(text.split()) >= 6]
        if not texts:
            return None
    except Exception as error:
        print(f"[Surreal] prompt database not used as archive: {error}")
        return None
    rng = random.Random(seed)

    def fragments(idea: str, count: int) -> List[str]:
        picked = rng.sample(texts, min(count, len(texts)))
        return [" ".join(re.sub(r"\s+", " ", text).split()[:ARCHIVE_WORDS]).rstrip(",;:") for text in picked]

    return fragments


def get_surreal_engine(seed: int = 0, use_archive: bool = True) -> SurrealEngine:
    library = get_wildcard_engine().library
    return SurrealEngine(SurrealSources(lookup=library.lookup, archive=_archive(seed) if use_archive else None))


def idea_distance(idea: str, embedder_choice: str, clip: Any = None) -> Tuple[Optional[Callable[[str], float]], List[str]]:
    """(distance function or None, notes). distance(text) is 0..1: how far a phrase is from the idea in meaning."""
    if (embedder_choice or "none") == "none" or not (idea or "").strip():
        return None, []
    try:
        import numpy as np

        from .core.variability import VectorCache
        from .variability_support import CACHE_DIR, get_embedder
        embedder, notes = get_embedder(embedder_choice, clip)
        if embedder.name.startswith("lexical"):
            return None, notes + ["no semantic embedder available, so distance from the idea is not scored"]
        cache = VectorCache(embedder, CACHE_DIR)
        idea_vector = cache.vectors([idea])[0]

        def distance(text: str) -> float:
            vector = cache.vectors([text])[0]
            return float(min(1.0, max(0.0, 1.0 - float(np.dot(idea_vector, vector)))))

        return distance, notes + [f"distance from the idea scored with {embedder.describe()}"]
    except Exception as error:
        return None, [f"embedder unavailable ({error}); distance from the idea is not scored"]


def surreal_brief(idea: str, settings: SurrealSettings, seed: Optional[int] = None, *, llm: Any = None, max_tokens: int = 2200,
                  embedder: str = "none", clip: Any = None, use_archive: bool = True) -> SurrealResult:
    """
    One idea -> ordinary-scene inventory -> premise -> structured render plan -> instruction block. With `llm`
    (an object with send_prompt), the first call inventories the unchanged scene and the second is the critic.
    Either stage can fail independently; the code critic remains the fallback. Never raises.
    """
    try:
        if seed is None:
            seed = random.SystemRandom().randrange(0, 0x7FFFFFFF)
        engine = get_surreal_engine(seed, use_archive)
        distance, notes = idea_distance(idea, embedder, clip)
        inventory = None
        inventory_problems: List[str] = []
        if llm is not None:
            system, user = scene_messages(idea)
            try:
                response = llm.send_prompt(system, user, max_tokens=min(max_tokens, 1400))
                if response.get("success"):
                    inventory, inventory_problems = parse_scene_inventory(response.get("response", ""))
                else:
                    inventory_problems = [str(response.get("error") or "the scene inventory LLM call failed")]
            except Exception as error:
                inventory_problems = [f"scene inventory LLM backend error: {error}"]
        plan = engine.plan(idea, settings, seed, distance=distance, inventory=inventory)
        plan.notes.extend(notes)
        if inventory_problems:
            plan.notes.append("ordinary scene inventory not used: " + "; ".join(inventory_problems))
        verdict, problems = None, None
        if llm is not None and plan.candidates:
            system, user = engine.critic_messages(plan)
            try:
                response = llm.send_prompt(system, user, max_tokens=max_tokens)
                if response.get("success"):
                    verdict, problems = parse_critic(response.get("response", ""), plan.candidates)
                else:
                    problems = [str(response.get("error") or "the LLM call failed")]
            except Exception as error:
                problems = [f"LLM backend error: {error}"]
        return engine.finish(plan, verdict, problems)
    except Exception as error:      # a strategy must never break a workflow
        import traceback
        traceback.print_exc()
        return SurrealResult(text=idea or "", instructions="", why=f"Surreal engine error: {error}. The idea was passed through unchanged.", ok=False)


def preset_plan(idea: str, seed: Optional[int], medium: str) -> Tuple[str, str, str]:
    """For legacy preset surfaces: (compiled transformed idea, instruction block, one-line note)."""
    result = surreal_brief(idea, SurrealSettings(medium=medium), seed, llm=None, use_archive=True)
    if not result.ok or not result.instructions:
        return idea, "", "surreal engine produced nothing; the preset's style words were not replaced"
    operation = ", ".join(result.operations)
    return result.text, result.instructions, f"surreal engine: {operation}"


def preset_block(idea: str, seed: Optional[int], medium: str) -> Tuple[str, str]:
    """
    For the existing `surreal` preset / genre values of the older nodes: (instruction block, one-line note).
    Code critic only - those nodes make one LLM call and that call carries out the premise. ('', note) on failure.
    """
    _text, block, note = preset_plan(idea, seed, medium)
    return block, note
