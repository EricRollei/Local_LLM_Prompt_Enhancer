"""
Semantic Variation Node

Makes controlled variations of a wildcard prompt. A plain re-roll replaces every random pick
with an unrelated one. This node starts from the picks `seed` would make and moves each one to
a SEMANTIC NEIGHBOUR inside its own list: a little for most slots, a lot for a few.

    variation 0        the plain seeded prompt, nothing moved
    variation 1, 2...  different variations of that same prompt, each reproducible
    strength           how far every slot drifts: 0.1 = nearest 1% of its list, 0.5 = a quarter of the way out,
                       0.7 = halfway, 1.0 = the far end of the list
    far_jumps          how many slots jump (far_strength) instead of drifting
    avoid_recent       build several candidates and keep the one least like what you generated lately

Slots are the wildcard constructs in the text: __name__, __objects[tag AND tag]__, {a|b|c}.
Fixed words in the prompt are not touched. Feed `text` and `llm_instructions` to an enhancer
node or straight to a text encoder.

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

import traceback
from typing import Tuple

from .core.variability import VariationSettings
from .core.wildcards import split_paths
from .variability_support import (
    EMBEDDER_CHOICES, available_embedders, direction_choices, get_embedder, get_variator,
)
from .wildcard_support import database_provider


class SemanticVariation:
    """Vary a wildcard prompt by moving each random pick to a semantic neighbour."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "__person__, __gestures__, beside __objects/**__ in __spaces/**__. __light/setups__.",
                    "tooltip": "Prompt with wildcard syntax. Every __name__, tag query and {a|b|c} is a slot that can be varied.",
                }),
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                    "tooltip": "Seed for the BASE picks. Keep it fixed and change `variation` to explore around one prompt.",
                }),
                "variation": ("INT", {
                    "default": 1, "min": 0, "max": 0xFFFFFFFF,
                    "tooltip": "0 = the base prompt untouched. 1, 2, 3... = different variations of it, each reproducible.",
                }),
                "strength": ("FLOAT", {
                    "default": 0.35, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "How far every slot drifts within its list. 0.1 = nearest few, 0.5 = a quarter of the way out, 0.7 = halfway, 1.0 = far end.",
                }),
                "far_jumps": ("INT", {
                    "default": 0, "min": 0, "max": 16,
                    "tooltip": "How many slots jump with far_strength instead of drifting. Which ones is decided by `variation`.",
                }),
                "far_strength": ("FLOAT", {
                    "default": 0.9, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "Strength used for the slots that jump.",
                }),
                "embedder": (EMBEDDER_CHOICES, {
                    "default": "auto",
                    "tooltip": (
                        "What 'similar' means. auto = connected clip, else Qwen3-VL-Embedding, else open_clip.\n"
                        "qwen3vl: similar in meaning and look. openclip / graph_clip: similar in look.\n"
                        "sentence: similar in meaning. lexical: spelling only (no model)."
                    ),
                }),
                "avoid_recent": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Make several candidate variations and keep the one least similar to recently generated prompts.",
                }),
            },
            "optional": {
                "clip": ("CLIP", {
                    "tooltip": "Optional. A CLIP with a pooled output (CLIP-L/G). Used as the embedder when `embedder` is auto or graph_clip.",
                }),
                "legacy_syntax": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Also accept the v1 forms {animal} and {label:a|b|c}.",
                }),
                "extra_paths": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Extra wildcard folders, one per line, highest priority. ComfyUI/models/wildcards is always searched.",
                }),
                # New inputs are only ever APPENDED below this line, so saved workflows keep their widget order.
                "direction": (direction_choices(), {
                    "default": "none",
                    "tooltip": (
                        "Lean every move along a named axis, e.g. ordinary_to_uncanny or new_to_decayed.\n"
                        "Axes are example phrases in variability/directions.yaml; add your own in directions_user.yaml.\n"
                        "strength still decides how far a slot may go; this decides which way."
                    ),
                }),
                "direction_amount": ("FLOAT", {
                    "default": 0.0, "min": -3.0, "max": 3.0, "step": 0.1,
                    "tooltip": (
                        "0 = no lean. Above 0 leans toward the axis's `to` side (uncanny, decayed, ...),\n"
                        "below 0 toward its `from` side. 1.0 is a clear lean, 2-3 lets the axis dominate.\n"
                        "The report shows each slot's lean so you can see whether an axis bites on a given list."
                    ),
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("text", "llm_instructions", "base_text", "report")
    FUNCTION = "vary"
    CATEGORY = "Eric Prompt Enhancers"

    @classmethod
    def IS_CHANGED(cls, avoid_recent=False, **kwargs):
        """With avoid_recent on, the result depends on the memory, so the node must not be cached."""
        if avoid_recent:
            import time
            return float(time.time())
        return ""

    def vary(self, text, seed, variation, strength, far_jumps, far_strength, embedder, avoid_recent,
             clip=None, legacy_syntax=True, extra_paths="", direction="none", direction_amount=0.0) -> Tuple[str, str, str, str]:
        try:
            chosen_embedder, notes = get_embedder(embedder, clip)
            variator = get_variator(chosen_embedder, split_paths(extra_paths))
            settings = VariationSettings(
                variation=int(variation), strength=float(strength), far_jumps=int(far_jumps),
                far_strength=float(far_strength), avoid_recent=bool(avoid_recent),
                direction=str(direction or "none"), direction_amount=float(direction_amount or 0.0),
            )
            result = variator.vary(
                text, int(seed), settings,
                legacy=bool(legacy_syntax), providers={"db": database_provider},
            )
            result.notes = notes + result.notes
            report = result.report()
            if result.resolution.warnings:
                report += "\n" + "\n".join("warning: " + warning for warning in result.resolution.warnings)
            if chosen_embedder.name.startswith("lexical"):
                found = available_embedders(clip)
                report += "\nembedders available here: " + ", ".join(f"{name} ({where})" for name, where in found.items())
            return (result.resolution.text, result.resolution.format_for_llm(), result.base_text, report)
        except Exception as error:  # never break the graph over a prompt
            traceback.print_exc()
            return (text, "", text, f"Semantic Variation error, text passed through unchanged: {error}")
