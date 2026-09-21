"""
Concept Survival Check.

Wildcard picks are concepts, not strings: the LLM rewriter may reword them as long as the meaning
survives. This node measures whether it did. Connect the prompt an enhancer produced and the
llm_instructions that went with it (from a Wildcard Processor or Semantic Variation node).

Two ways of judging, chosen with `method`:

    embedding   Cuts the prompt into windows of words and scores each concept against them in embedding
                space. Fast, no LLM. Measured with Qwen3-VL-Embedding-2B (dev/try_directions_and_survival.py):
                for THINGS, MATERIALS and PLACES it separates well - a faithful paraphrase scores about
                0.69-0.74, the same scene with the pick dropped 0.43-0.60. For RELATIONS and CONDITIONS
                ("lit only from below", "the weather is indoors") it does not: an embedding hears the
                topic, not who does what to whom, so window light scores as high as light from below.
    llm         Asks the LLM backend, concept by concept, whether the prompt states the idea and which
                words carry it. Slower, needs a model loaded, but it reads relations.
    both        The LLM decides; the embedding score is shown next to it. If the LLM call fails the
                embedding verdict is used.

Verbatim picks are always checked by exact match.

Outputs: a report, all_survived (BOOLEAN, for gating a retry), the missing items, and a JSON map of
concept -> carrying phrase, score and verdict.

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

import json
import traceback

from .core.variability import score_concepts
from .variability_support import EMBEDDER_CHOICES, get_embedder
from .wildcard_support import concepts_from_instructions, verbatim_from_instructions

DEFAULT_THRESHOLD = 0.62
METHODS = ["embedding", "llm", "both"]

JUDGE_SYSTEM = (
    "You check whether ideas survived a rewrite. You are given a PROMPT and a list of CONCEPTS. For each concept "
    "decide whether the prompt actually states that idea, in any wording. A related topic does not count: a pigeon "
    "is not a barn owl, light from a window is not light from below, rain outside is not rain indoors. "
    "Answer with JSON only, no other text, in this shape: "
    '{"results": [{"concept": "<the concept exactly as given>", "present": true, "phrase": "<the exact words from the prompt that carry it>"}]} '
    "Use present=false and an empty phrase when the idea is missing."
)


def judge_with_llm(prompt, concepts, backend, endpoint, model):
    """{concept: (present, phrase)} from the LLM backend, or None when the call or the JSON fails."""
    from .core.profiles.validate import clean_llm_output, extract_json_object
    from .llm_backend import LLMBackend

    numbered = "\n".join(f"{index}. {concept}" for index, concept in enumerate(concepts, 1))
    user = f"PROMPT:\n{prompt}\n\nCONCEPTS:\n{numbered}"
    llm = LLMBackend(backend, endpoint, model or None, 0.0)
    response = llm.send_prompt(JUDGE_SYSTEM, user, max_tokens=1500)
    if not response.get("success"):
        return None, response.get("error", "LLM call failed")
    try:
        parsed = extract_json_object(clean_llm_output(response.get("response", ""), keep_json=True))
        verdicts = {}
        for item in parsed.get("results", []):
            verdicts[str(item.get("concept", "")).strip().lower()] = (bool(item.get("present")), str(item.get("phrase", "") or ""))
        return verdicts, ""
    except Exception as error:
        return None, f"the judge's answer was not usable JSON ({error})"


class ConceptSurvivalCheck:
    CATEGORY = "Eric Prompt Enhancers"
    FUNCTION = "check"
    RETURN_TYPES = ("STRING", "BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = ("report", "all_survived", "missing", "carried_by_json")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"forceInput": True, "tooltip": "The rewritten prompt to check."}),
                "llm_instructions": ("STRING", {
                    "forceInput": True,
                    "tooltip": "The llm_instructions output of the Wildcard Processor or Semantic Variation node that made the picks.",
                }),
                "threshold": ("FLOAT", {
                    "default": DEFAULT_THRESHOLD, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": (
                        "Embedding method: a concept survived when its best-matching phrase scores at least this.\n"
                        "Measured with Qwen3-VL-Embedding-2B on things, materials and places: faithful paraphrase\n"
                        "0.69-0.74, same scene with the pick dropped 0.43-0.60, unrelated prompt 0.26-0.45.\n"
                        "Other embedders sit elsewhere: read the report, then set this."
                    ),
                }),
                "embedder": (EMBEDDER_CHOICES, {
                    "default": "auto",
                    "tooltip": "auto = connected clip, else Qwen3-VL-Embedding, else open_clip. lexical cannot judge meaning.",
                }),
            },
            "optional": {
                "clip": ("CLIP", {"tooltip": "Optional. Used as the embedder when `embedder` is auto or graph_clip."}),
                "method": (METHODS, {
                    "default": "embedding",
                    "tooltip": (
                        "embedding = fast, no LLM; reliable for things, materials and places, NOT for relations\n"
                        "            such as 'lit only from below' (an embedding hears the topic, not the relation).\n"
                        "llm       = ask the LLM backend whether each idea is stated; reads relations; needs a model loaded.\n"
                        "both      = the LLM decides, the embedding score is shown beside it."
                    ),
                }),
                "backend": (["lm_studio", "ollama", "qwen3_vl"], {"default": "lm_studio", "tooltip": "For method llm / both."}),
                "endpoint": ("STRING", {"default": "http://localhost:1234/v1", "tooltip": "For method llm / both."}),
                "model": ("STRING", {"default": "", "tooltip": "For method llm / both. Blank = whatever model is loaded."}),
            },
        }

    def check(self, prompt, llm_instructions, threshold, embedder, clip=None, method="embedding",
              backend="lm_studio", endpoint="http://localhost:1234/v1", model=""):
        try:
            concepts = concepts_from_instructions(llm_instructions)
            verbatim = verbatim_from_instructions(llm_instructions)
            if not concepts and not verbatim:
                return ("No concepts or verbatim picks in llm_instructions - nothing to check.", True, "", "{}")

            lines = []
            scores = []
            if concepts and method in ("embedding", "both"):
                chosen_embedder, notes = get_embedder(embedder, clip)
                scores = score_concepts(chosen_embedder, prompt or "", concepts, float(threshold))
                lines.append(f"embedder: {chosen_embedder.describe()}   threshold: {float(threshold):.2f}")
                if chosen_embedder.name.startswith("lexical"):
                    lines.append("WARNING: the lexical embedder compares spelling, not meaning. Concept scores here say little.")
                lines.extend(notes)
            by_concept = {score.concept: score for score in scores}

            verdicts = None
            if concepts and method in ("llm", "both"):
                verdicts, problem = judge_with_llm(prompt or "", concepts, backend, endpoint, model)
                if verdicts is None:
                    lines.append(f"LLM judge unavailable: {problem}" + ("; using the embedding verdict" if scores else ""))
                    if not scores:       # method = llm and it failed: fall back rather than report nothing
                        chosen_embedder, notes = get_embedder(embedder, clip)
                        scores = score_concepts(chosen_embedder, prompt or "", concepts, float(threshold))
                        by_concept = {score.concept: score for score in scores}
                        lines.append(f"fell back to embedder: {chosen_embedder.describe()}   threshold: {float(threshold):.2f}")

            carried_by = {}
            missing_concepts = []
            for concept in concepts:
                score = by_concept.get(concept)
                judged = verdicts.get(concept.strip().lower()) if verdicts else None
                if judged is not None:
                    survived, phrase, judge = judged[0], judged[1], "llm"
                elif score is not None:
                    survived, phrase, judge = score.survived, score.carried_by, "embedding"
                else:
                    survived, phrase, judge = False, "", "none"
                if not survived:
                    missing_concepts.append(concept)
                number = f"{score.score:.2f}" if score is not None else " -- "
                shown = f'"{phrase}"' if phrase else ("(nearest: \"" + score.carried_by + "\")" if score is not None and score.carried_by else "(nothing)")
                lines.append(f"  {'ok     ' if survived else 'MISSING'} {number}  [{judge}]  {concept}  <-  {shown}")
                carried_by[concept] = {"phrase": phrase, "score": round(score.score, 3) if score is not None else None,
                                       "survived": survived, "judged_by": judge}

            lowered = (prompt or "").lower()
            missing_verbatim = [value for value in verbatim if value.lower() not in lowered]
            for value in verbatim:
                lines.append(f"  {'MISSING' if value in missing_verbatim else 'ok     '} exact  \"{value}\"")

            missing = missing_concepts + missing_verbatim
            return ("\n".join(lines), not missing, ", ".join(missing), json.dumps(carried_by, ensure_ascii=False))
        except Exception as error:  # a check must never break the graph
            traceback.print_exc()
            return (f"Concept Survival Check error: {error}", True, "", "{}")
