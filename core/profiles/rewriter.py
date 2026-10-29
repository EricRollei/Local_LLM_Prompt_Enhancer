"""
Builds the LLM's instructions from a platform profile. No LLM call happens here.

Two bases for the system prompt:
    built-in   generated from the profile's fields (format, length, structure, rules, avoid, ...).
               Always available, works offline.
    official   the vendor's own rewriter prompt (official.py), with the profile's short tailoring
               and an output contract appended. Used when the profile names one and it is reachable.

In both cases the same blocks can be appended by the caller: the wildcard selected-elements
block, a creative-strategy block (surreal, later), and per-run facts (duration, aspect ratio,
a description of the start image).

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .official import MODE_AUTO, OfficialResult, load_official
from .schema import Profile

VIDEO_TASK_LABELS = {"edit": "video editing (instruction applied to an existing clip)"}

TASK_LABELS = {
    "t2i": "text-to-image",
    "edit": "image editing (instruction)",
    "t2v": "text-to-video",
    "i2v": "image-to-video (the start frame is given)",
    "flf2v": "first-and-last-frame video",
    "ref2v": "reference-to-video",
}

STYLE_DESCRIPTIONS = {
    "prose": (
        "Write natural-language prose: full sentences in one cohesive paragraph unless told otherwise. "
        "No keyword lists, no bullet points, no headings."
    ),
    "tags": (
        "Write a comma-separated tag list, not sentences. Most important tags first."
    ),
    "tags_prose": (
        "Write the required tags first, then natural-language description. Tags are comma separated; "
        "the description is plain sentences or descriptive phrases."
    ),
    "instruction": (
        "Write an edit instruction, not a description of a finished picture: say what changes, then say "
        "what must stay the same. Imperative voice. Short."
    ),
    "json": (
        "Output one valid JSON object and nothing else: no code fences, no comments, no text before or after. "
        "Follow the key names and key order of the template exactly."
    ),
    "fields": (
        "Output the named fields of the template, in the template's order, each as `name:` followed by its "
        "content. Field names are part of the model's input format: never rename, translate, reorder or drop them."
    ),
    "bracket_prose": (
        "Write natural-language prose. Camera moves go in square-bracket commands placed right after the "
        "clause they apply to; only the listed commands exist."
    ),
}

BOILERPLATE_EXAMPLES = "masterpiece, best quality, highly detailed, ultra detailed, 8k, 4k, UHD, award-winning, stunning, trending on artstation"


@dataclass
class RunFacts:
    """Per-run facts the rewriter should know. Everything is optional."""
    duration_seconds: float = 0.0
    aspect_ratio: str = ""
    image_description: str = ""        # what the start / source image shows (i2v, edit)
    end_image_description: str = ""    # flf2v
    dialogue: str = ""                 # exact spoken lines the user wants, if any
    audio: str = "auto"                # auto | off  (off = write no sound cues even if the model has audio)
    language: str = ""                 # force the prompt language; "" = the profile's first language
    extra_instructions: str = ""       # free text from the user to the rewriter
    length_words: tuple = (0, 0)       # (low, high) set by the caller, e.g. from a detail tier; (0, 0) = the profile decides


@dataclass
class RewritePlan:
    system: str
    user: str
    task: str
    base: str                                  # "official" | "built-in"
    notes: List[str] = field(default_factory=list)


def _bullets(items: List[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _language_name(code: str) -> str:
    return {"en": "English", "zh": "Chinese", "ja": "Japanese", "ko": "Korean"}.get(code, code)


def run_word_range(profile: Profile, task: str, facts: "RunFacts") -> tuple:
    return profile.words_for_run(task, facts.duration_seconds, facts.length_words)


def _token_limit_line(profile: Profile) -> str:
    """The budget the LLM is told: the encoder limit minus headroom for template tokens and for
    LoRA trigger words appended after the rewrite (token_budget.budget_for). 2026-10-08."""
    from .token_budget import budget_for
    limit, target = budget_for(profile)
    return (f"Hard limit: {target} tokens (about {int(target * 0.72)} English words). The model's text "
            f"encoder reads {limit} tokens and silently cuts off the rest; the remaining room is reserved "
            f"for LoRA trigger words added after your answer. Put the most important content first.")


def _length_block(profile: Profile, task: str, facts: Optional["RunFacts"] = None) -> str:
    low, high = run_word_range(profile, task, facts) if facts is not None else profile.words_for(task)
    unit = "tags" if profile.caption_style == "tags" else "words"
    lines = [f"Aim for {low}-{high} {unit}. Shorter than {low} is too thin; longer than {high} wastes the model's attention."]
    if profile.max_tokens:
        lines.append(_token_limit_line(profile))
    if profile.max_chars:
        lines.append(f"Hard limit: {profile.max_chars} characters including spaces.")
    return "\n".join(lines)


def _quality_block(profile: Profile) -> str:
    if profile.quality_tokens == "forbid":
        reader = "a language model" if profile.encoder_family == "llm" else "a text encoder trained on natural captions"
        return (
            f"Do NOT add quality boilerplate ({BOILERPLATE_EXAMPLES}). This model reads prompts with {reader}; "
            f"such tokens carry no information for it and pull results toward a generic stock look. "
            f"Get quality from specifics instead: light source and direction, lens, materials, surface detail."
        )
    if profile.quality_tokens in ("help", "required"):
        parts = []
        if profile.prefix:
            must = "MUST begin" if profile.quality_tokens == "required" else "should begin"
            parts.append(f"The prompt {must} with exactly: {profile.prefix}")
        elif profile.suffix:
            must = "MUST end" if profile.quality_tokens == "required" else "should end"
            parts.append(
                f"The prompt {must} with exactly: {profile.suffix}\n"
                "These quality tags go LAST, after every other tag - this model was trained with them near the end, "
                "not at the start."
            )
        elif profile.quality_token_list:
            parts.append(f"Quality tags this model was trained on (use a few, at the start): {', '.join(profile.quality_token_list)}")
        return "\n".join(parts)
    return "Quality boilerplate is not needed; spend the words on the scene."


def _text_block(profile: Profile) -> str:
    if profile.quoted_text == "none":
        return "This model renders text poorly: avoid asking for readable text; if the user insists, keep it to one short word."
    quote = '"double quotes"' if profile.quoted_text == "double" else "'single quotes'"
    # The first sentence matters: small models read a section about text as an invitation to add some, and put
    # signs and plaques into pictures that asked for none ("Next Bus: 12 minutes", seen live 2026-09-21).
    return (
        "Put text in the picture ONLY when the user's idea asks for it; otherwise write none - no signs, labels, "
        "plaques or captions of your own. "
        f"Text the user does ask for goes in {quote}, exactly as the user wrote it - never translated, "
        f"corrected or paraphrased - with where it sits and what it looks like (surface, font style, colour, size)."
    )


def _negative_block(profile: Profile) -> str:
    if profile.negative == "yes":
        return (
            "A separate negative prompt exists for this model, so the positive prompt describes only what IS there. "
            "Do not write 'no X' or 'without X' in it."
        )
    if profile.negative == "inline":
        return (
            "There is no separate negative prompt for this model, and its maker endorses writing exclusions into the "
            "prompt itself. Describe what IS there first; then, only for things the user explicitly does not want, add a "
            "few short exclusions at the very end, in the wording the rules below give. Invent no exclusions of your own."
        )
    reason = "it is distilled and runs without CFG" if profile.negative == "ignored" else "it has no negative prompt"
    return (
        f"There is no usable negative prompt for this model ({reason}). Never write 'no X', 'without X' or "
        f"'avoid X' - naming a thing tends to summon it. Turn every exclusion into a positive description "
        f"of what is there instead ('no glasses' -> 'clear face, eyes visible')."
    )


SPEECH_HINT = re.compile(
    r"[\"\u201c\u201d]|\b(?:say|says|said|saying|tell|tells|told|ask|asks|asked|repl(?:y|ies|ied)|answer(?:s|ed)?|whisper\w*|shout\w*|"
    r"yell\w*|scream\w*|mutter\w*|murmur\w*|announce\w*|sing|sings|singing|sang|song|lyrics?|rap|raps|rapping|narrat\w*|"
    r"voice-?over|voiceover|monologue|dialogue|dialog|speech|speak\w*|spoke|talk\w*|convers\w*|interview\w*|chant\w*|call(?:s|ed)? out)\b",
    re.I,
)


def idea_involves_speech(idea: str) -> bool:
    """A cheap, explainable test: quotation marks, or a verb of speaking or singing, anywhere in the user's text."""
    return bool(SPEECH_HINT.search(idea or ""))


def _audio_block(profile: Profile, facts: RunFacts, idea: str = "") -> str:
    if profile.modality != "video":
        return ""
    if not profile.audio:
        return (
            "This model is SILENT. Write no sound, music or dialogue cues - they waste tokens. A person may be "
            "described as talking or singing, as visible motion only."
        )
    if facts.audio == "off":
        return "The user wants no sound design: follow the format's rule for silence and write no dialogue."
    lines = ["This model generates the soundtrack from the prompt. Sound is part of the job, not an afterthought."]
    if facts.dialogue.strip():
        lines.append(
            "Spoken lines supplied by the user (use them word for word, in this order, never translated or "
            f"reworded, and invent no others):\n{facts.dialogue.strip()}"
        )
    elif idea and not idea_involves_speech(idea):
        # Small local models invent a line of dialogue or a voiceover whenever the format shows them how. Be blunt.
        lines.append(
            "Nobody speaks or sings in the user's idea, so this prompt has NO dialogue, NO voiceover and NO lyrics: "
            "do not invent a spoken line. Ambient sound, action sound and (where the format has it) music only."
        )
    else:
        lines.append("Invent dialogue only if the user's idea involves someone speaking or singing; otherwise none.")
    return "\n".join(lines)


def _facts_block(profile: Profile, task: str, facts: RunFacts) -> str:
    lines: List[str] = []
    if facts.duration_seconds and profile.modality == "video":
        lines.append(
            f"Clip length: {facts.duration_seconds:g} seconds. Everything described must be able to happen in that "
            f"time - no more action than fits, and no dead air either."
        )
    if facts.aspect_ratio:
        lines.append(f"Aspect ratio: {facts.aspect_ratio}. Compose for that frame shape.")
    if facts.image_description.strip():
        role = "source image to be edited" if task == "edit" else "start frame"
        lines.append(f"What the {role} shows (given, not to be contradicted):\n{facts.image_description.strip()}")
    if facts.end_image_description.strip():
        lines.append(f"What the END frame shows (the clip must arrive here):\n{facts.end_image_description.strip()}")
    if facts.extra_instructions.strip():
        lines.append(f"Extra direction from the user for this run:\n{facts.extra_instructions.strip()}")
    return "\n\n".join(lines)


def _contract(profile: Profile) -> str:
    wrapper = {
        "json": "Output the JSON object only.",
        "fields": "Output the fields only.",
    }.get(profile.caption_style, "Output the final prompt only.")
    return (
        f"{wrapper} No preamble, no label such as 'Prompt:', no explanation, no markdown, no alternatives, "
        f"no reasoning in the answer.\n"
        "Stay faithful: every subject, count, action, colour, named thing and spatial relation the user gave must "
        "survive. Add detail that serves the idea; never swap the idea for a different one, and never refuse or "
        "lecture - if something cannot be written in this format, write the closest faithful version.\n"
        "If the user's text is already detailed, polish and reformat it rather than inflating it."
    )


def _references_block(profile: Profile, task: str) -> str:
    """Models with a reference-to-video mode show reference tags in their rules; outside that mode, forbid them."""
    if profile.modality == "video" and "ref2v" in profile.tasks and task != "ref2v":
        supplied = {"i2v": "only the start frame", "flf2v": "only the first and last frame"}.get(task, "NO reference files")
        exception = " A fixed first line required by the format above is the one exception." if task in ("i2v", "flf2v") else ""
        return (
            f"This run supplies {supplied}. Write no asset bindings and no reference tags or labels "
            "(@Image1, @image_1, <IMAGE_REF_0>, <IMAGE_1>, 'Image 1', 'Video 1', <Subject 1> ...) for anything else: "
            f"describe it in words.{exception}"
        )
    return ""


def build_builtin_system(profile: Profile, task: str, facts: RunFacts, idea: str = "") -> str:
    language = facts.language or (profile.languages[0] if profile.languages else "en")
    sections: List[str] = []

    head = f"You write prompts for {profile.name}"
    if profile.developer:
        head += f" ({profile.developer})"
    label = VIDEO_TASK_LABELS.get(task) if profile.modality == "video" else None
    head += f". Task: {label or TASK_LABELS.get(task, task)}."
    if profile.summary:
        head += f"\n{profile.summary}"
    if profile.encoder:
        head += f"\nThe model reads the prompt with: {profile.encoder}."
    sections.append(head)

    sections.append("OUTPUT CONTRACT\n" + _contract(profile))

    format_lines = [STYLE_DESCRIPTIONS[profile.caption_style], f"Write the prompt in {_language_name(language)}."]
    first_line = profile.for_task(task, "first_line", "")
    if first_line:
        format_lines.append(f"The very first line must be exactly this, followed by one blank line:\n{first_line}")
    sections.append("FORMAT\n" + "\n".join(format_lines))

    sections.append("LENGTH\n" + _length_block(profile, task, facts))

    structure = profile.for_task(task, "structure", "")
    if structure:
        sections.append("STRUCTURE\n" + structure)

    template = profile.for_task(task, "output_template", "")
    if template:
        sections.append("TEMPLATE (copy the structure, replace the descriptions)\n" + template)

    task_specific = profile.task_rules.get(task, {})
    task_rule_list = [str(rule) for rule in (task_specific.get("rules") or [])]
    # Task rules come first. `replace_rules: true` in task_rules drops the profile-level rules for that task.
    rules = task_rule_list if task_specific.get("replace_rules") else task_rule_list + list(profile.rules)
    if rules:
        sections.append("RULES\n" + _bullets(rules))

    avoid = list(profile.avoid) + list(task_specific.get("avoid", []) or [])
    if avoid:
        sections.append("AVOID\n" + _bullets(avoid))

    if profile.camera and profile.modality == "video":
        sections.append("CAMERA VOCABULARY THIS MODEL RESPONDS TO\n" + ", ".join(profile.camera))

    if profile.modality != "video":
        sections.append("TEXT IN THE PICTURE\n" + _text_block(profile))
    if profile.hex_colors:
        sections.append(
            "COLOUR CODES\nHex codes are understood. When the user gives or implies exact colours, bind each code to "
            "an object and announce it with the word 'color' or 'hex': \"a scarf in color #C4725A\"."
        )
    if profile.weights:
        sections.append("WEIGHTS\n(word:1.2) emphasis syntax works here. Use it rarely, on at most two or three terms, between 1.1 and 1.4.")
    else:
        sections.append("WEIGHTS\nNo (word:1.2) weights, no [brackets] for emphasis - this model reads them as literal characters.")

    sections.append("QUALITY TOKENS\n" + _quality_block(profile))
    sections.append("NEGATIVES\n" + _negative_block(profile))

    audio = _audio_block(profile, facts, idea)
    if audio:
        sections.append("SOUND\n" + audio)

    references = _references_block(profile, task)
    if references:
        sections.append("REFERENCE FILES\n" + references)

    return "\n\n".join(section for section in sections if section.strip())


def build_official_system(profile: Profile, task: str, facts: RunFacts, official: OfficialResult, idea: str = "") -> str:
    text = official.text
    for placeholder in ("{prompt}", "{}", "{user_prompt}", "{original_prompt}", "{{original_prompt}}"):
        text = text.replace(placeholder, "(the user's text is in the next message)")

    additions: List[str] = ["OUTPUT CONTRACT\n" + _contract(profile)]
    low, high = run_word_range(profile, task, facts)
    if (low, high) != profile.words_for(task):
        # Only when this run asks for something other than the profile's standing range (a detail tier, or a
        # clip length on a model that states words per second); otherwise the vendor's own length advice stands.
        additions.append(f"LENGTH FOR THIS RUN\nAim for {low}-{high} words.")
    limit_lines = []
    if profile.max_tokens:
        limit_lines.append(_token_limit_line(profile))
    if profile.max_chars:
        limit_lines.append(f"Hard limit: {profile.max_chars} characters.")
    if limit_lines:
        additions.append("LIMITS\n" + "\n".join(limit_lines))
    language = facts.language or (profile.languages[0] if profile.languages else "en")
    additions.append(f"LANGUAGE\nWrite the final prompt in {_language_name(language)}, whatever language the instructions above are in.")
    first_line = profile.for_task(task, "first_line", "")
    if first_line:
        additions.append(f"FIRST LINE\nThe very first line must be exactly this, followed by one blank line:\n{first_line}")
    if profile.tailoring:
        additions.append("TAILORING\n" + profile.tailoring)
    audio = _audio_block(profile, facts, idea)
    if audio and profile.audio:
        additions.append("SOUND\n" + audio)
    references = _references_block(profile, task)
    if references:
        additions.append("REFERENCE FILES\n" + references)

    return (
        f"{text.strip()}\n\n"
        "=== ADDITIONAL REQUIREMENTS (these win over anything above that conflicts) ===\n\n"
        + "\n\n".join(additions)
    )


def build_user(idea: str, profile: Profile, task: str, facts: RunFacts, base: str) -> str:
    parts: List[str] = []
    if base == "official":
        # Vendor prompts expect the bare user text; per-run facts ride along, clearly separated.
        parts.append(idea.strip())
        facts_text = _facts_block(profile, task, facts)
        if facts_text:
            parts.append("---\nFacts for this run (context for you, not text to copy):\n" + facts_text)
        return "\n\n".join(parts)

    parts.append("USER IDEA\n" + idea.strip())
    facts_text = _facts_block(profile, task, facts)
    if facts_text:
        parts.append("FACTS FOR THIS RUN\n" + facts_text)
    parts.append(f"Write the {profile.name} prompt now.")
    return "\n\n".join(parts)


def plan_rewrite(profile: Profile, idea: str, task: Optional[str] = None, facts: Optional[RunFacts] = None,
                 cache_dir: str = "", official_mode: str = MODE_AUTO, extra_system: str = "") -> RewritePlan:
    """
    Everything needed for one LLM call.
    extra_system is appended last to the system prompt (wildcard block, strategy block).
    """
    facts = facts or RunFacts()
    resolved_task = profile.resolve_task(task)
    notes: List[str] = []
    if task and task not in ("auto", resolved_task):
        notes.append(f"{profile.name} does not do '{task}'; using '{resolved_task}'")

    official = OfficialResult()
    if cache_dir:
        official = load_official(profile, resolved_task, cache_dir, official_mode)
        notes.extend(official.notes)

    if official.used:
        system = build_official_system(profile, resolved_task, facts, official, idea)
        base = "official"
    else:
        system = build_builtin_system(profile, resolved_task, facts, idea)
        base = "built-in"
        if not official.notes:
            notes.append("base: built-in rules from the profile")

    if extra_system and extra_system.strip():
        system = f"{system}\n\n{extra_system.strip()}"

    user = build_user(idea, profile, resolved_task, facts, base)
    return RewritePlan(system=system, user=user, task=resolved_task, base=base, notes=notes)
