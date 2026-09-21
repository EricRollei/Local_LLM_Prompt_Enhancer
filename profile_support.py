"""
Platform-profile support shared by the nodes.

One place for: the profile library, the cache folder for vendor rewriter prompts, the dropdown
lists, and the single call that turns an idea into a platform prompt through the existing
LLMBackend.

Dropdown rule: a node's platform list is its ORIGINAL list, in its original order, with profile
ids it did not know appended after it. ComfyUI stores a dropdown's value as text, so appending
never disturbs a saved workflow; the original order is kept anyway so the menus look as they did.

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .core.profiles import (
    MODE_AUTO,
    MODES,
    Profile,
    ProfileLibrary,
    RunFacts,
    check,
    get_library,
    negative_prompt,
    plan_rewrite,
    to_legacy_config,
)

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(PACKAGE_DIR, "cache")

OFFICIAL_PROMPT_CHOICES = list(MODES)
TASK_CHOICES = ["auto", "t2i", "edit", "t2v", "i2v", "flf2v", "ref2v"]
MODALITY_ORDER = ("image", "edit", "video")


def library() -> ProfileLibrary:
    return get_library()


def get_profile(profile_id: str) -> Optional[Profile]:
    try:
        return library().get(profile_id)
    except Exception as error:  # a broken profile folder must never stop a node from loading
        print(f"[Prompt Profiles] could not load profiles: {error}")
        return None


def profile_ids(modalities: Sequence[str] = MODALITY_ORDER) -> List[str]:
    """Profile ids grouped by modality (image, edit, video), alphabetical inside each group."""
    ordered: List[str] = []
    try:
        for modality in modalities:
            ordered.extend(sorted(library().ids(modality=modality)))
    except Exception as error:
        print(f"[Prompt Profiles] could not list profiles: {error}")
    return ordered


LEGACY_NODE_EXCLUDED_STYLES = ("json", "fields")


def extended_choices(original: Iterable[str], modalities: Sequence[str],
                     exclude_styles: Sequence[str] = LEGACY_NODE_EXCLUDED_STYLES) -> List[str]:
    """
    A node's original dropdown list with the profile ids it did not have appended after it.
    JSON and named-field formats are left out: the older nodes post-process the LLM's answer as
    plain text (keyword appends, density padding), which would corrupt them. Those formats are
    served by the Platform Prompt Rewriter node.
    """
    choices = list(original)
    for profile_id in profile_ids(modalities):
        if profile_id in choices:
            continue
        profile = get_profile(profile_id)
        if profile is None or profile.caption_style in exclude_styles:
            continue
        choices.append(profile_id)
    return choices


def legacy_config(profile_id: str, task: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """platforms.py-shaped dict for a profile, or None when there is no such profile."""
    profile = get_profile(profile_id)
    if profile is None:
        return None
    return to_legacy_config(profile, task)


def legacy_negative(profile_id: str, custom_negatives: Optional[Sequence[str]] = None) -> Optional[str]:
    profile = get_profile(profile_id)
    if profile is None:
        return None
    return negative_prompt(profile, custom_negatives)


# ---- the video expander nodes -------------------------------------------------------------------
WAN_TARGET = "wan22_video"          # selecting this keeps the nodes' original Wan 2.2 behaviour, untouched
DEFAULT_VIDEO_TARGET = "minimax_h3"
DEFAULT_CLIP_SECONDS = 6.0

# Where inside a model's own length range each detail tier sits (fractions of low..high).
TIER_FRACTIONS = {
    "basic": (0.0, 0.35),
    "enhanced": (0.25, 0.65),
    "advanced": (0.55, 0.9),
    "cinematic": (0.8, 1.0),
}


def video_target_choices() -> List[str]:
    """Video profile ids: the default first, Wan 2.2 second, the rest alphabetical. Values are stored as text."""
    ids = []
    for profile_id in profile_ids(("video",)):
        profile = get_profile(profile_id)
        if profile is not None and any(task in profile.tasks for task in ("t2v", "i2v")):   # not video-edit-only profiles
            ids.append(profile_id)
    head = [profile_id for profile_id in (DEFAULT_VIDEO_TARGET, WAN_TARGET) if profile_id in ids]
    choices = head + [profile_id for profile_id in ids if profile_id not in head]
    return choices or [WAN_TARGET]


def video_target_inputs() -> Dict[str, Any]:
    """Optional inputs appended to the three video nodes. Append-only: never insert these before an existing input."""
    choices = video_target_choices()
    default = DEFAULT_VIDEO_TARGET if DEFAULT_VIDEO_TARGET in choices else choices[0]
    return {
        "target_model": (choices, {
            "default": default,
            "tooltip": (
                "The video model the prompt is written for.\n"
                "wan22_video = this node's original behaviour, unchanged: Wan 2.2 tiers and shot structure.\n"
                "Any other model: the prompt is built from that model's profile (profiles/video/<id>.yaml) - its format,\n"
                "length, camera vocabulary, sound and dialogue rules - together with this node's preset, aesthetic\n"
                "controls and creativity settings. The tier then sets how long the prompt is inside the model's own range.\n"
                "MiniMax H3 prompts come out as its three named fields, not as a paragraph."
            ),
        }),
        "duration_seconds": ("FLOAT", {
            "default": DEFAULT_CLIP_SECONDS, "min": 0.0, "max": 60.0, "step": 0.5,
            "tooltip": (
                "Length of the clip you will generate. 0 = not stated. Ignored for wan22_video.\n"
                "Models with timed shots and sound (MiniMax H3, Seedance, Kling, Veo) need it: the timeline and the\n"
                "amount of action and dialogue are fitted to it. Set it to the same value as your sampler."
            ),
        }),
    }


def tier_word_range(profile: Profile, task: str, tier: str, duration_seconds: float = 0.0) -> "tuple[int, int]":
    """
    Length for one run of a video node. A model that states words per second gets its length from the clip
    length (the tier cannot sensibly override that); otherwise the tier picks a band inside the model's range.
    """
    if duration_seconds and profile.words_per_second[1] > 0:
        return profile.words_for_run(task, duration_seconds)
    low, high = profile.words_for(task)
    start, end = TIER_FRACTIONS.get(tier, TIER_FRACTIONS["enhanced"])
    span = max(0, high - low)
    return int(low + span * start), max(int(low + span * end), int(low + span * start) + 1)


def append_terms(prompt: str, terms: Sequence[str], profile: Optional[Profile]) -> "tuple[str, List[str]]":
    """
    Add required terms (LoRA triggers, verbatim picks) the LLM dropped. Returns (prompt, terms that could NOT be added).
    Prose and tag prompts take them at the end. Named-field prompts take them at the end of the FIRST field, because
    text after the last field would land in the music or sound field. JSON is left alone: the caller warns instead.
    """
    style = profile.caption_style if profile is not None else "prose"
    if style == "fields" and prompt:
        prompt = _lift_stray_terms(prompt, terms)
        prompt = _strip_terms_after_first_field(prompt, terms)
    missing = [term for term in terms if term and term.lower() not in (prompt or "").lower()]
    if not missing:
        return prompt, []
    if style == "json":
        return prompt, missing
    addition = ", ".join(missing)
    if style == "fields":
        import re
        labels = list(re.finditer(r"(?m)^[a-z_]{4,}:", prompt))
        if len(labels) >= 2:
            cut = labels[1].start()
            head = prompt[:cut].rstrip()
            return f"{head} {addition}\n\n{prompt[cut:]}", []
        # fewer than two field names: the answer is not in the field format anyway, so the end is as good as anywhere
    separator = ", " if style == "tags" else " "
    return f"{prompt.rstrip()}{separator}{addition}", []


def _lift_stray_terms(prompt: str, terms: Sequence[str]) -> str:
    """
    Field formats: an LLM told to include a trigger word often drops it on a line of its own after the last
    field, where the video model reads it as part of the music field. Such lines (nothing but required terms)
    are removed here; append_terms then puts the terms at the end of the first field.
    """
    import re
    wanted = {term.strip().lower() for term in terms if term and term.strip()}
    if not wanted:
        return prompt
    kept = []
    for line in prompt.split("\n"):
        parts = [part.strip().lower() for part in re.split(r"[,;]", line) if part.strip()]
        if parts and all(part in wanted for part in parts):
            continue
        kept.append(line)
    return "\n".join(kept).rstrip()


def _strip_terms_after_first_field(prompt: str, terms: Sequence[str]) -> str:
    """
    Field formats: a required term only counts inside the FIRST field (the visual description). A term the LLM
    tucked into a later field (seen live: at the end of non_diegetic_music) is removed from there, so that
    append_terms sees it as missing and places it at the end of the first field.
    """
    import re
    labels = list(re.finditer(r"(?m)^[a-z_]{4,}:", prompt))
    if len(labels) < 2:
        return prompt
    cut = labels[1].start()
    head, tail = prompt[:cut], prompt[cut:]
    for term in terms:
        term = (term or "").strip()
        if not term or term.lower() in head.lower():
            continue
        tail = re.sub(r"[ \t]*[,;]?[ \t]*(?<![\w-])" + re.escape(term) + r"(?![\w-])", "", tail, flags=re.I)
    return head + tail


def add_required_terms(prompt: str, keywords: Sequence[str], resolution: Any, target_model: str) -> "tuple[str, List[str]]":
    """
    Profile-path replacement for the video nodes' two "append what the LLM dropped" steps (positive keywords and
    verbatim wildcard picks), which would otherwise put text after the last field of a structured prompt.
    Returns (prompt, warnings).
    """
    from .wildcard_support import enforce_verbatim

    _unused, verbatim_missing = enforce_verbatim(prompt, resolution)
    wanted = [term for term in keywords if term] + [term for term in verbatim_missing if term not in keywords]
    repaired, not_added = append_terms(prompt, wanted, get_profile(target_model))
    warnings = []
    if not_added:
        warnings.append("required terms missing from the answer and NOT added, to keep the format valid: " + ", ".join(not_added))
    return repaired, warnings


def target_report_lines(breakdown: Dict[str, Any]) -> List[str]:
    """Lines for a video node's breakdown output describing the target model and what its checker found."""
    if not breakdown or not breakdown.get("target_model"):
        return []
    lines = [f"Target model: {breakdown.get('target_name') or breakdown['target_model']}  ({breakdown['target_model']}, task {breakdown.get('target_task', '?')})"]
    if breakdown.get("target_format"):
        low, high = breakdown.get("target_words") or (0, 0)
        lines.append(f"Format: {breakdown['target_format']}  |  length asked for: {low}-{high} words  |  instructions: {breakdown.get('target_base', '')}")
    if breakdown.get("target_api_note"):
        lines.append(f"API: {breakdown['target_api_note']}")
    lines.extend(f"Note: {note}" for note in breakdown.get("target_notes") or [])
    lines.extend(f"WARNING: {warning}" for warning in breakdown.get("target_warnings") or [])
    return lines


CAPTION_PROMPTS = {
    "start": (
        "Describe this image as the FIRST FRAME of a video, for someone who cannot see it. Cover: each subject "
        "(appearance, clothing, pose, where they look), the setting, the light (source, direction, colour), the "
        "composition and camera angle. Literal and objective, 60-120 words, one paragraph. Do not guess what "
        "happens next and do not comment on quality."
    ),
    "end": (
        "Describe this image as the LAST FRAME of a video, for someone who cannot see it. Cover: each subject "
        "(appearance, clothing, pose), the setting, the light, the composition and camera angle. Literal and "
        "objective, 60-120 words, one paragraph."
    ),
    "edit": (
        "Describe this image for an editor who will change one thing in it. Name every distinct subject and object "
        "with the attributes that identify it (colour, material, position in frame), the background, the light and "
        "any visible text, quoted exactly. Literal and objective, 60-120 words, one paragraph."
    ),
}


def caption_image_tensor(image: Any, purpose: str, backend: str, endpoint: str, model: str,
                         temperature: float = 0.3) -> "tuple[str, str]":
    """
    (caption, note) for a ComfyUI IMAGE tensor, through the same LLMBackend the node talks to.
    Never raises. An empty caption comes with a note saying why (no vision model loaded, call failed).
    """
    try:
        import io

        import numpy as np
        from PIL import Image

        from .llm_backend import LLMBackend

        array = image[0].detach().cpu().numpy()
        array = (np.clip(array, 0, 1) * 255).astype(np.uint8)
        if array.ndim == 2:
            array = np.stack([array] * 3, -1)
        buffer = io.BytesIO()
        Image.fromarray(array[..., :3]).save(buffer, format="PNG")

        llm = LLMBackend(backend, endpoint, model or None, temperature)
        if not llm.supports_images():
            return "", (f"the {purpose} image was ignored: the loaded model is not vision-capable. Load a vision model "
                        f"(for example a Qwen3-VL) or wire a caption into the description input instead")
        response = llm.caption_image(buffer.getvalue(), label=f"{purpose} frame",
                                     prompt=CAPTION_PROMPTS.get(purpose, CAPTION_PROMPTS["start"]))
        if response.get("success") and (response.get("caption") or "").strip():
            return response["caption"].strip(), f"the {purpose} image was captioned by the LLM backend"
        return "", f"the {purpose} image could not be captioned: {response.get('error', 'no caption returned')}"
    except Exception as error:
        return "", f"the {purpose} image could not be captioned: {error}"


@dataclass
class RewriteResult:
    ok: bool
    prompt: str = ""
    negative: str = ""
    task: str = ""
    base: str = ""
    system_prompt: str = ""
    user_prompt: str = ""
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    error: str = ""
    word_range: tuple = (0, 0)       # the length this run asked for; (0, 0) = the profile's standing range

    def report(self, profile: Optional[Profile]) -> str:
        lines: List[str] = []
        if profile is not None:
            low, high = self.word_range if self.word_range[1] else profile.words_for(self.task or profile.default_task())
            lines.append(f"{profile.name}  |  task: {self.task}  |  format: {profile.caption_style}  |  target: {low}-{high} words")
            negative_text = {"yes": "used", "no": "none - this model has no negative prompt",
                             "ignored": "ignored - distilled, runs without CFG",
                             "inline": "none as a field - exclusions are written into the prompt"}.get(profile.negative, profile.negative)
            lines.append(f"negative prompt: {negative_text}" + (f"  ({profile.negative_note})" if profile.negative_note else ""))
            if profile.confidence != "high":
                lines.append(f"profile confidence: {profile.confidence} (facts checked {profile.checked})")
            if profile.api_note:
                lines.append(f"API: {profile.api_note}")
        if self.error:
            lines.append(f"ERROR: {self.error}")
        if self.prompt:
            lines.append(f"result: {len(self.prompt.split())} words, {len(self.prompt)} characters")
        lines.extend(f"note: {note}" for note in self.notes)
        lines.extend(f"WARNING: {warning}" for warning in self.warnings)
        return "\n".join(lines)


def rewrite_for_platform(
    idea: str,
    profile_id: str,
    *,
    task: str = "auto",
    backend: str = "lm_studio",
    endpoint: str = "http://localhost:1234/v1",
    model: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    facts: Optional[RunFacts] = None,
    official_mode: str = MODE_AUTO,
    extra_system: str = "",
    custom_negatives: Optional[Sequence[str]] = None,
    llm: Any = None,
) -> RewriteResult:
    """
    One idea -> one platform prompt. Fail-soft: when the LLM cannot be reached the original idea
    comes back as the prompt with ok=False, so a workflow keeps running.
    `llm` lets a caller (or a test) pass an object with send_prompt(system, user, max_tokens).
    """
    profile = get_profile(profile_id)
    if profile is None:
        return RewriteResult(ok=False, prompt=idea, error=f"no platform profile named '{profile_id}'")

    plan = plan_rewrite(
        profile, idea, task=None if task == "auto" else task, facts=facts,
        cache_dir=CACHE_DIR, official_mode=official_mode, extra_system=extra_system,
    )
    result = RewriteResult(
        ok=False, task=plan.task, base=plan.base, system_prompt=plan.system, user_prompt=plan.user,
        notes=list(plan.notes), negative=negative_prompt(profile, custom_negatives),
        word_range=profile.words_for_run(plan.task, (facts or RunFacts()).duration_seconds, (facts or RunFacts()).length_words),
    )

    try:
        if llm is None:
            from .llm_backend import LLMBackend
            llm = LLMBackend(backend, endpoint, model or None, temperature)
        response = llm.send_prompt(plan.system, plan.user, max_tokens=max_tokens)
    except Exception as error:
        result.prompt = idea
        result.error = f"LLM backend error: {error}. The idea was passed through unchanged."
        return result

    if not response.get("success"):
        result.prompt = idea
        result.error = f"{response.get('error', 'LLM call failed')}. The idea was passed through unchanged."
        return result

    text, warnings = check(response.get("response", ""), profile, plan.task, word_range=result.word_range)
    if not text:
        result.prompt = idea
        result.warnings = warnings
        result.error = "the LLM returned nothing usable. The idea was passed through unchanged."
        return result

    result.ok = True
    result.prompt = text
    result.warnings = warnings
    return result
