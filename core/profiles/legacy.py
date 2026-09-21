"""
Bridge from profiles to the dictionary shape the older nodes read through platforms.py.

The Text-to-Image and Image-to-Image nodes were written against platforms.PLATFORMS: a dict per
platform with keys such as prompt_style, max_words, quality_emphasis, preferences, avoid. This
module renders a Profile into that same shape, so those nodes pick up corrected facts and new
platforms without being rewritten. Two keys are new and optional for the consumer:

    format_instructions   a ready-made text block that replaces the node's hard-coded
                          "FLUX-SPECIFIC INSTRUCTIONS" style sections
    min_words             lower bound of the target length (the nodes used to derive one from
                          max_words, which overshoots for short-prompt models such as FLUX.2 klein)

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .rewriter import STYLE_DESCRIPTIONS, _negative_block, _quality_block, _text_block
from .schema import Profile

LEGACY_STYLE_NAMES = {
    "prose": "natural_detailed",
    "tags": "booru_detailed",
    "tags_prose": "natural_detailed",
    "instruction": "edit_focused",
    "json": "structured_json",
    "fields": "structured_fields",
    "bracket_prose": "natural_detailed",
}


def format_instructions(profile: Profile, task: str) -> str:
    lines: List[str] = [f"{profile.name.upper()} FORMAT (follow exactly):", STYLE_DESCRIPTIONS[profile.caption_style]]
    structure = profile.for_task(task, "structure", "")
    if structure:
        lines.append(f"Structure: {structure}")
    if profile.max_tokens:
        lines.append(f"Hard limit: {profile.max_tokens} tokens (about {int(profile.max_tokens * 0.72)} words); most important content first.")
    lines.append(_quality_block(profile))
    lines.append(_text_block(profile))
    lines.append(_negative_block(profile))
    if profile.hex_colors:
        lines.append("Hex colour codes are understood: bind each to an object and announce it with 'color' or 'hex'.")
    if not profile.weights:
        lines.append("No (word:1.2) weight syntax.")
    template = profile.for_task(task, "output_template", "")
    if template:
        lines.append("Template:\n" + template)
    return "\n".join(f"- {line}" if index else line for index, line in enumerate(lines)) + "\n"


def to_legacy_config(profile: Profile, task: Optional[str] = None) -> Dict[str, Any]:
    resolved_task = profile.resolve_task(task)
    low, high = profile.words_for(resolved_task)
    legacy = profile.legacy
    unit = "tags" if profile.caption_style == "tags" else "words"
    quality_emphasis = profile.quality_tokens in ("help", "required")

    config: Dict[str, Any] = {
        "name": profile.name,
        "description": profile.summary or f"{profile.developer} {profile.modality} model",
        "prompt_style": legacy.get("prompt_style", LEGACY_STYLE_NAMES[profile.caption_style]),
        "optimal_length": legacy.get("optimal_length", f"{low}-{high} {unit}"),
        "max_words": high,
        "min_words": low,
        "max_tokens": legacy.get("llm_max_tokens", max(120, int(high * 1.5))),
        "quality_emphasis": quality_emphasis,
        "length_guidance": legacy.get("length_guidance", f"Aim for {low}-{high} {unit}."),
        "detail_expectation": legacy.get(
            "detail_expectation",
            "Concrete, observable detail: subject, setting, light source and direction, materials, composition.",
        ),
        "supports": list(legacy.get("supports", [])),
        "preferences": list(profile.for_task(resolved_task, "rules", profile.rules) or []),
        "quality_tokens": list(profile.quality_token_list) if quality_emphasis else [],
        "avoid": list(profile.avoid),
        "format_instructions": format_instructions(profile, resolved_task),
        "negative_supported": profile.negative == "yes",
        "negative_default": profile.negative_default,
        "profile_id": profile.id,
    }
    if profile.prefix and profile.quality_tokens == "required":
        config["required_positive"] = [token.strip() for token in profile.prefix.split(",") if token.strip()]
    if profile.suffix and profile.quality_tokens == "required":
        config["required_positive"] = [token.strip() for token in profile.suffix.split(",") if token.strip()]
        config["required_position"] = "end"
    for key in ("required_negative", "technical_terms", "edit_templates"):
        if key in legacy:
            config[key] = legacy[key]
    return config


def negative_prompt(profile: Profile, custom_negatives: Optional[Sequence[str]] = None) -> str:
    """
    The negative prompt to hand on. For a model that cannot use one (no negative field, or
    distilled and run without CFG) the stock default is left out - sending boilerplate there only
    misleads - but keywords the user typed are still passed through, in case their workflow runs
    a base checkpoint with CFG.
    """
    custom = [str(item).strip() for item in (custom_negatives or []) if str(item).strip()]
    if profile.negative != "yes":
        return ", ".join(custom)
    parts = [profile.negative_default] if profile.negative_default else []
    return ", ".join(parts + custom)
