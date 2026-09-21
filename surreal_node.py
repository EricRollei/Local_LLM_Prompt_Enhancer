"""
Surreal Premise.

Surreal as a working procedure instead of a style word. Image models regress toward the plausible: ask for
"surreal" and you get the average of everything tagged surreal. The surrealists who lasted worked differently -
a GENERATOR supplied material they could not have planned (chance, a rule, a stock of unrelated things, a
misperception) and a CRITIC then selected one thing and finished it with full craft. This node is that loop:

    idea -> generator modes (eight, from Magritte, Ernst, Dali, Varo, Uelsmann, Atget, Man Ray) -> candidates
         -> critic (an LLM, or seeded code) keeps ONE -> a premise stated as plain physical fact

Connect `text` to an enhancer's prompt input and `llm_instructions` to its `wildcard_instructions` input. The
enhancer then writes for its platform while protecting the premise. `why` shows every candidate and the
reasoning, so the choice can be judged. A Concept Survival Check on the enhancer's output (fed the same
llm_instructions) measures whether the anomaly survived the rewrite.

Two of the modes depict nothing impossible at all (found strange, process estrangement). That is on purpose.

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

from .core.strategies.surreal import (
    CHARGE_CHOICES, CHARGES, MODE_CHOICES, MODES, OPERATION_CHOICES, OPERATIONS, REGISTER_CHOICES, STRANGENESS_CHOICES,
    SurrealSettings,
)
from .surreal_support import surreal_brief
from .wildcard_support import is_changed_token, llm_block, normalise_seed, report_lines, resolve_wildcards

EMBEDDER_CHOICES = ["none", "auto", "qwen3vl", "openclip", "graph_clip", "sentence"]


def _mode_tooltip():
    lines = ["How candidates are generated. auto = two modes chosen by weight (strangeness shifts the weights)."]
    lines += [f"{mode.id}: {mode.what} ({mode.source})" for mode in MODES.values()]
    return "\n".join(lines)


def _operation_tooltip():
    lines = ["auto = the mode decides. Naming one forces the affinity search to use only that operation."]
    lines += [f"{name}: {OPERATIONS[name].what} ({OPERATIONS[name].lineage})" for name in OPERATION_CHOICES if name in OPERATIONS]
    return "\n".join(lines)


class SurrealPremise:
    CATEGORY = "Eric Prompt Enhancers"
    FUNCTION = "make"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("text", "llm_instructions", "why", "title", "negative_additions")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "idea": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Your subject and scene, in your own words. Keep it ordinary: the strangeness is this node's job.\nWildcards work here.",
                }),
                "mode": (MODE_CHOICES, {"default": "auto", "tooltip": _mode_tooltip()}),
                "operation": (OPERATION_CHOICES, {"default": "auto", "tooltip": _operation_tooltip()}),
                "count": ("INT", {
                    "default": 1, "min": 1, "max": 2,
                    "tooltip": (
                        "How many operations. 1 or 2, never more: one impossibility against a credible world is the whole effect,\n"
                        "and three read as a collage of effects. A second operation is always atmosphere-level (light, shadow,\n"
                        "time, absence) so that both read as one event."
                    ),
                }),
                "strangeness": (STRANGENESS_CHOICES, {
                    "default": "balanced",
                    "tooltip": "subtle = may need a second look (absence, light, found strange). overt = unmistakable (scale, inversion, fusion).",
                }),
                "register": (REGISTER_CHOICES, {
                    "default": "deadpan photographic",
                    "tooltip": "How the picture is rendered. The default is evidence: a photograph argues with its own impossibility.\nSome operations insist on their own register; the why output says when that happened.",
                }),
                "charge": (CHARGE_CHOICES, {
                    "default": "auto",
                    "tooltip": "The emotional source the anomaly serves. An anomaly with no stake in it reads as a gimmick.\nauto = drawn by seed. none = leave it out.\n" + "\n".join(f"{name}: {text}" for name, text in CHARGES.items() if text),
                }),
                "critic": (["llm", "code"], {
                    "default": "llm",
                    "tooltip": (
                        "llm  = one LLM call judges the candidates, binds the premise to your actual subject, carries out the\n"
                        "       procedure modes, and writes a restatement, a title and counter-terms. Falls back to code if it fails.\n"
                        "code = seeded, offline, instant. The premise may say THE SUBJECT; the enhancer's LLM resolves it."
                    ),
                }),
                "candidates": ("INT", {"default": 6, "min": 2, "max": 12, "tooltip": "How many candidates the critic chooses from. Most are meant to be thrown away."}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 0x7FFFFFFF, "tooltip": "-1 = a fresh roll each run (the why output shows the seed drawn). 0 or more = reproducible."}),
                "medium": (["image", "video"], {"default": "image", "tooltip": "video adds anomalies in TIME (reversed, slowed, looped, mismatched sound) and tells the enhancer the anomaly persists for the whole clip."}),
                "backend": (["lm_studio", "ollama", "qwen3_vl"], {"default": "lm_studio", "tooltip": "For critic = llm."}),
                "endpoint": ("STRING", {"default": "http://localhost:1234/v1", "tooltip": "For critic = llm. For qwen3_vl: a model folder or folder name, or leave as is."}),
                "model": ("STRING", {"default": "", "tooltip": "Blank = whatever model is loaded."}),
                "temperature": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 2.0, "step": 0.05}),
            },
            "optional": {
                "embedder": (EMBEDDER_CHOICES, {
                    "default": "none",
                    "tooltip": "Optional. With an embedding model, partners that are FAR from your idea in meaning score higher (distance is what\nmakes an affinity a shock). none = tags only, no model loaded.",
                }),
                "use_archive": ("BOOLEAN", {"default": True, "tooltip": "Let the archive-composite mode draw fragments from your prompt database as well as your iconography file."}),
                "clip": ("CLIP", {"tooltip": "Optional. Used as the embedder when `embedder` is auto or graph_clip."}),
                "wildcard_instructions": ("STRING", {"forceInput": True, "tooltip": "llm_instructions from a Wildcard Processor or Semantic Variation node upstream; passed on with this node's block."}),
            },
        }

    @classmethod
    def IS_CHANGED(cls, seed=-1, **kwargs):
        return is_changed_token(seed)

    def make(self, idea, mode, operation, count, strangeness, register, charge, critic, candidates, seed, medium,
             backend, endpoint, model, temperature, embedder="none", use_archive=True, clip=None, wildcard_instructions=""):
        run_seed = normalise_seed(seed)
        resolution = resolve_wildcards(idea or "", seed=run_seed, legacy=True, upstream_instructions=wildcard_instructions)
        resolved = resolution.text
        if not resolved.strip():
            return ("", (wildcard_instructions or ""), "Empty idea - nothing to do.", "", "")

        llm = None
        if critic == "llm":
            from .llm_backend import LLMBackend
            llm = LLMBackend(backend, endpoint, model or None, temperature)

        settings = SurrealSettings(mode=mode, operation=operation, count=int(count), register=register, charge=charge,
                                   strangeness=strangeness, medium=medium, candidates=int(candidates))
        result = surreal_brief(resolved, settings, run_seed if run_seed is not None else getattr(resolution, "seed", None),
                               llm=llm, embedder=embedder, clip=clip, use_archive=bool(use_archive))

        blocks = [result.instructions, llm_block(resolution, True)]
        instructions = "\n\n".join(block for block in blocks if block)
        why = result.why
        wildcard_report = report_lines(resolution)
        if wildcard_report:
            why = f"{why}\n{wildcard_report}"
        print(f"[Surreal Premise] {', '.join(result.operations) or 'nothing'}: {(result.premises or [''])[0][:100]}")
        return (result.text, instructions, why, result.title, result.negative_additions)
