"""
Platform Prompt Rewriter.

One idea in, one prompt out, written the way the chosen model wants to read it. Everything the
node knows about a model comes from a YAML profile in profiles/ (see core/profiles/schema.py):
format (prose, tags, edit instruction, JSON, MiniMax H3 fields, Hailuo bracket commands), target
length and hard limits, whether a negative prompt exists, whether quality tokens help or hurt,
how rendered text and dialogue are written, and - where the vendor publishes one - the vendor's
own rewriter prompt, downloaded once and cached.

The node is thin on purpose: resolve wildcards, build the instructions from the profile, call
the LLM through the package's LLMBackend, check the answer, report. If the LLM cannot be reached
the idea passes through unchanged and the report says why.

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

from .core.profiles import RunFacts
from .profile_support import (
    OFFICIAL_PROMPT_CHOICES,
    TASK_CHOICES,
    caption_image_tensor,
    get_profile,
    profile_ids,
    rewrite_for_platform,
)
from .wildcard_support import (
    enforce_verbatim,
    is_changed_token,
    llm_block,
    normalise_seed,
    report_lines,
    resolve_wildcards,
    filter_notes_of,
    lead_with_filter_notes,
    screen_output,
    wildcard_nsfw_input,
    wildcard_optional_inputs,
)

DEFAULT_PLATFORM = "krea2"


def _fit_final(prompt, profile, resolution, result):
    """Last budget check AFTER verbatim picks were re-added: trim the body, never the verbatim
    picks (LoRA triggers, names)."""
    try:
        from .core.profiles.token_budget import budget_for, counter_for, fit_to_budget
        from .wildcard_support import verbatim_from_instructions
        limit, target = budget_for(profile)
        if not limit:
            return prompt
        count, _how = counter_for(profile)
        n = count(prompt)
        if n <= target:
            return prompt
        protect = []
        if resolution is not None:
            protect = [slot.value for slot in resolution.slots_by_binding("verbatim")]
            protect += verbatim_from_instructions(getattr(resolution, "upstream_instructions", ""))
        fitted, n2, dropped = fit_to_budget(prompt, target, count, protect=protect)
        result.warnings.append(f"after re-adding verbatim picks: trimmed {n} -> {n2} tokens (target {target}), "
                               "verbatim picks kept" + (f"; removed: \"{dropped[0]}\"" if dropped else ""))
        return fitted
    except Exception as error:
        result.warnings.append(f"final token budget check failed ({error})")
        return prompt


def _platform_choices():
    choices = profile_ids()
    return choices or [DEFAULT_PLATFORM]


class PlatformPromptRewriter:
    CATEGORY = "Eric Prompt Enhancers"
    FUNCTION = "rewrite"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("prompt", "negative_prompt", "report", "system_prompt")

    @classmethod
    def INPUT_TYPES(cls):
        choices = _platform_choices()
        default_platform = DEFAULT_PLATFORM if DEFAULT_PLATFORM in choices else choices[0]
        return {
            "required": {
                "idea": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "What you want, in your own words. Wildcards work: __name__, {a|b|c}, __objects[metal AND handheld]__.",
                }),
                "platform": (choices, {
                    "default": default_platform,
                    "tooltip": (
                        "Target model. Listed as image models, then edit models, then video models.\n"
                        "Each entry is a YAML file in the package's profiles/ folder; put your own or edited\n"
                        "copies in profiles_user/ (same id = replaces the shipped one)."
                    ),
                }),
                "task": (TASK_CHOICES, {
                    "default": "auto",
                    "tooltip": (
                        "auto = the model's main task.\n"
                        "t2i text-to-image, edit = edit instruction, t2v text-to-video,\n"
                        "i2v image-to-video, flf2v first+last frame, ref2v reference-to-video.\n"
                        "A task the model does not have falls back to its main one (the report says so)."
                    ),
                }),
                "backend": (["lm_studio", "ollama", "qwen3_vl"], {"default": "lm_studio"}),
                "endpoint": ("STRING", {
                    "default": "http://localhost:1234/v1",
                    "tooltip": "LM Studio / Ollama base URL. For qwen3_vl, optionally a local model path.",
                }),
                "model": ("STRING", {"default": "", "tooltip": "Blank = whatever model is loaded."}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.05}),
                "max_tokens": ("INT", {
                    "default": 4096, "min": 256, "max": 32768,
                    "tooltip": "Room for the LLM's answer. Reasoning models and MiniMax H3 prompts need the most.",
                }),
                "official_prompt": (OFFICIAL_PROMPT_CHOICES, {
                    "default": "auto",
                    "tooltip": (
                        "Several labs publish the system prompt of their own prompt rewriter.\n"
                        "auto    = use it when the profile has one and it is not huge; downloaded once, then cached\n"
                        "on      = use it whatever its size (Qwen-Image's is ~35,000 characters)\n"
                        "off     = always use the rules written in the profile (works offline)\n"
                        "refresh = download it again, then behave like on"
                    ),
                }),
            },
            "optional": {
                "image_description": ("STRING", {
                    "forceInput": True,
                    "tooltip": "For i2v / edit: what the start or source image shows, from your own captioner. Used instead of captioning `image`.",
                }),
                "end_image_description": ("STRING", {
                    "forceInput": True,
                    "tooltip": "For flf2v: what the last frame shows. Used instead of captioning `end_image`.",
                }),
                "dialogue": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Exact spoken lines for models with sound, one per line, e.g.  Woman: I get off at the next station.\nUsed word for word. Empty = the rewriter invents speech only if your idea involves someone speaking.",
                }),
                "duration_seconds": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 60.0, "step": 0.5,
                    "tooltip": "Clip length for video models. 0 = not stated. The rewriter fits the action to it.",
                }),
                "aspect_ratio": ("STRING", {"default": "", "tooltip": "Optional, e.g. 16:9. The rewriter composes for it."}),
                "audio": (["auto", "off"], {
                    "default": "auto",
                    "tooltip": "auto = write sound, music and dialogue when the model generates audio. off = no sound design.",
                }),
                "language": (["auto", "en", "zh"], {
                    "default": "auto",
                    "tooltip": "Language of the prompt. auto = the model's first language (English for every shipped profile).",
                }),
                "extra_instructions": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Direction for the rewriter for this run, e.g. 'keep it under 60 words', 'night exterior, handheld'.",
                }),
                "negative_keywords": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated additions to the negative prompt. Passed through even for models that ignore negatives.",
                }),
                **wildcard_optional_inputs(),
                # Appended later. Sockets only (no widgets), but still added at the end: the rule is append-only.
                "image": ("IMAGE", {
                    "tooltip": (
                        "For i2v / edit / flf2v: the start or source image. It is captioned through the backend above,\n"
                        "which therefore needs a vision model loaded. A connected image_description wins over this."
                    ),
                }),
                "end_image": ("IMAGE", {"tooltip": "For flf2v: the last frame. Captioned like `image`."}),
                **wildcard_nsfw_input(),
                # Appended 2026-10-08 (append-only rule).
                "length_guard": (["retry+trim", "trim", "off"], {
                    "default": "retry+trim",
                    "tooltip": (
                        "Keeps the prompt inside the model's text-encoder limit (Krea 2: 512 tokens), with\n"
                        "headroom for LoRA trigger words added later - past the limit the encoder silently\n"
                        "drops the END, which is where triggers sit.\n"
                        "retry+trim = ask the LLM once for a tighter version, then trim at a sentence end\n"
                        "trim       = trim only (no extra LLM call)\n"
                        "off        = report only"
                    ),
                }),
            },
        }

    @classmethod
    def IS_CHANGED(cls, wildcard_seed=-1, **kwargs):
        """wildcard_seed = -1 means a fresh roll each run, which must defeat ComfyUI's cache."""
        return is_changed_token(wildcard_seed)

    def rewrite(self, idea, platform, task, backend, endpoint, model, temperature, max_tokens, official_prompt,
                image=None, end_image=None, image_description="", end_image_description="", dialogue="",
                duration_seconds=0.0, aspect_ratio="", audio="auto", language="auto", extra_instructions="",
                negative_keywords="", wildcard_seed=-1, wildcard_llm_block=True, wildcard_instructions="", nsfw="off",
                violence_filter="off", length_guard="retry+trim"):

        resolution = resolve_wildcards(idea or "", seed=normalise_seed(wildcard_seed), legacy=True,
                                       upstream_instructions=wildcard_instructions, nsfw=nsfw,
                                       violence_filter=violence_filter)
        resolved_idea = resolution.text

        if not resolved_idea.strip():
            return ("", "", "Empty idea - nothing to rewrite.", "")

        # Images: a description wired in by the user wins; otherwise caption through the same backend.
        profile_for_task = get_profile(platform)
        caption_notes = []
        has_start = image is not None or bool((image_description or "").strip())
        has_end = end_image is not None or bool((end_image_description or "").strip())
        if task == "auto" and profile_for_task is not None and has_start:
            # An image on the input says what the job is: first+last frame, image-to-video, or an edit.
            for candidate, wanted in (("flf2v", has_end), ("i2v", True), ("edit", True)):
                if wanted and candidate in profile_for_task.tasks:
                    task = candidate
                    caption_notes.append(f"task auto -> {candidate}, because an image is connected")
                    break
        resolved_task = profile_for_task.resolve_task(None if task == "auto" else task) if profile_for_task else task
        if image is not None and not (image_description or "").strip():
            purpose = "edit" if resolved_task == "edit" else "start"
            image_description, note = caption_image_tensor(image, purpose, backend, endpoint, model)
            caption_notes.append(note)
        if end_image is not None and not (end_image_description or "").strip():
            end_image_description, note = caption_image_tensor(end_image, "end", backend, endpoint, model)
            caption_notes.append(note)

        facts = RunFacts(
            duration_seconds=float(duration_seconds or 0.0),
            aspect_ratio=(aspect_ratio or "").strip(),
            image_description=image_description or "",
            end_image_description=end_image_description or "",
            dialogue=dialogue or "",
            audio=audio,
            language="" if language == "auto" else language,
            extra_instructions=extra_instructions or "",
        )
        custom_negatives = [part.strip() for part in (negative_keywords or "").split(",") if part.strip()]

        result = rewrite_for_platform(
            resolved_idea, platform, task=task, backend=backend, endpoint=endpoint, model=model,
            temperature=temperature, max_tokens=max_tokens, facts=facts, official_mode=official_prompt,
            extra_system=llm_block(resolution, wildcard_llm_block), custom_negatives=custom_negatives,
            length_guard=length_guard,
        )

        result.notes.extend(caption_notes)
        profile = profile_for_task
        prompt = result.prompt
        if result.ok:
            structured = profile is not None and profile.caption_style in ("json", "fields")
            repaired, missing = enforce_verbatim(prompt, resolution)
            if missing and structured:
                # Appending text to JSON or to named fields would break the format, so only report it.
                result.warnings.append("verbatim wildcard picks missing from the answer (not added, to keep the format valid): " + ", ".join(missing))
            elif missing:
                prompt = repaired
                result.notes.append("verbatim wildcard picks the LLM dropped were added back: " + ", ".join(missing))
            if not structured and length_guard != "off":
                prompt = _fit_final(prompt, profile, resolution, result)

        prompt, block_note = screen_output(prompt, "Platform Prompt Rewriter output")
        report = result.report(profile)
        wildcard_report = report_lines(resolution)
        if wildcard_report:
            report = f"{report}\n{wildcard_report}"
        report = lead_with_filter_notes(report, filter_notes_of(resolution, block_note))
        print(f"[Platform Prompt Rewriter] {platform}: {'ok' if result.ok else 'FAILED'} ({result.base or 'no plan'})")
        return (prompt, result.negative, report, result.system_prompt)
