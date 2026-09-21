"""
Wildcard Processor Node

Resolves wildcard syntax in a prompt with no LLM involved. Use it on its own in front of
any text encoder, or in front of the prompt enhancer nodes: the `llm_instructions` output
tells an LLM rewriter which elements were chosen at random and how tightly to keep them.

Syntax (Dynamic Prompts compatible, existing wildcard packs work as they are):
    __animal__   __light/setups__   __camera/**__          file wildcards, folders, globs
    __objects[metal AND handheld]__   __[hollow AND antique]__   pick by tag
    {a|b|c}   {3::common|1::rare}   {2$$ and $$a|b|c}        variants, weights, multi-select
    ${who=!__person__} ... ${who}                            pick once, reuse
    [if rain : umbrella | sunhat]                            conditionals
    __db:red door__                                          draw from the prompt database
    __=name__  {=a|b}   exact words must survive an LLM rewrite
    __?name__  {?a|b}   inspiration only

Packs are read from ComfyUI/models/wildcards (and any `wildcards:` entry in
extra_model_paths.yaml), then from this package's own wildcards/ folder. When a name exists
in both, your pack wins. `extra_paths` (one folder per line) takes priority over everything.

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

import traceback
from typing import Tuple

from .core.wildcards import MODES, split_paths
from .wildcard_support import database_provider, get_wildcard_engine


class WildcardProcessor:
    """Resolve wildcards, variants, variables and tag queries in a prompt."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "__person__, __gestures__, beside __objects[hollow AND antique]__ in __spaces/**__. __light/setups__. __camera/lenses__.",
                    "tooltip": "Prompt with wildcard syntax. __name__ = file wildcard, {a|b} = variant, __objects[tag AND tag]__ = pick by tag.",
                }),
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                    "tooltip": "Same seed + same wildcard files = same text.",
                }),
                "mode": (list(MODES), {
                    "default": "random",
                    "tooltip": (
                        "random = weighted random picks decided by the seed.\n"
                        "combinatorial = no randomness: the `index` input walks through every possible combination in order."
                    ),
                }),
            },
            "optional": {
                "index": ("INT", {
                    "default": 0, "min": 0, "max": 0xFFFFFFFF,
                    "tooltip": (
                        "A counter, not a seed. Connect a number that goes up by one per run.\n"
                        "It selects which combination comes out when mode = combinatorial (wraps around at the end),\n"
                        "and it steps cyclical variants {@a|b|c} in either mode."
                    ),
                }),
                "legacy_syntax": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Also accept the v1 forms {animal} and {label:a|b|c}.",
                }),
                "use_prompt_database": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Let __db:query__ draw a matching prompt from the prompt database.",
                }),
                "extra_paths": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Extra wildcard folders, one per line, highest priority. ComfyUI/models/wildcards is always searched; this is for folders elsewhere.",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("text", "llm_instructions", "record_json", "report")
    FUNCTION = "process"
    CATEGORY = "Eric Prompt Enhancers"

    def process(
        self,
        text: str,
        seed: int,
        mode: str,
        index: int = 0,
        legacy_syntax: bool = True,
        use_prompt_database: bool = True,
        extra_paths: str = "",
    ) -> Tuple[str, str, str, str]:
        try:
            engine = get_wildcard_engine(split_paths(extra_paths))
            providers = {"db": database_provider} if use_prompt_database else {}
            resolution = engine.process(
                text,
                seed=int(seed),
                mode=mode,
                index=int(index),
                cycle_index=int(index),
                legacy=bool(legacy_syntax),
                providers=providers,
            )

            report_lines = [resolution.summary()]
            if resolution.mode == "combinatorial":
                report_lines.append(
                    f"combination {int(index) % max(1, resolution.combination_space) + 1} of {resolution.combination_space}"
                )
            report_lines.append("search folders: " + "; ".join(engine.library.search_paths))

            return (
                resolution.text,
                resolution.format_for_llm(),
                resolution.to_json(),
                "\n".join(report_lines),
            )
        except Exception as error:  # never break the graph over a prompt
            traceback.print_exc()
            return (text, "", "{}", f"Wildcard Processor error, text passed through unchanged: {error}")
