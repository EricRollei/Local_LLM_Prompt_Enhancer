"""
Platform profile: everything the rewriter needs to know about one target model, as data.

A profile is one YAML file in profiles/. Adding a platform means adding a file, not editing a node.
Every field below is optional in the file except id, name, modality, tasks and caption_style;
missing fields take the defaults shown here.

Field reference (the YAML keys are the attribute names):

    id                  stable key, used as the dropdown value. Never rename one that has shipped.
    name                display name
    developer           who makes the model
    summary             one line: what the model is and how it likes to be prompted
    modality            image | edit | video            (audio, music, speech arrive in Phase 4)
    tasks               which of these the model does: t2i, edit, t2v, i2v, flf2v, ref2v
    encoder             text encoder, as a fact for the notes ("umT5-XXL", "Qwen3-VL-4B")
    encoder_family      clip | t5 | llm                 (decides whether keyword soup or prose works)
    caption_style       prose | tags | tags_prose | instruction | json | fields | bracket_prose
    languages           prompt languages the model was trained on, best first
    target_words        [low, high] word range the rewriter aims for
    max_tokens          hard token limit of the text encoder (0 = not documented)
    max_chars           hard character limit of a hosted API (0 = none)
    negative            yes | no | ignored              (ignored = distilled, CFG off, field has no effect)
    negative_default    the negative prompt to output when negative == yes
    negative_note       when the answer depends on the checkpoint (base vs turbo)
    quality_tokens      forbid | neutral | help | required
    quality_token_list  the tokens, where they help
    prefix              text the prompt must start with (score tags, quality tags)
    quoted_text         double | single | none          how text to be rendered is marked
    weights             true when (word:1.2) syntax is understood by the usual UI for this model
    hex_colors          true when #RRGGBB codes are understood
    audio               true when the model generates sound from the prompt
    structure           the vendor's prompt formula, one or two lines
    rules               do's, as imperative sentences for the LLM
    avoid               don'ts
    camera              camera vocabulary the model is known to respond to
    task_rules          per-task overrides: {i2v: {target_words, first_line, structure, rules, avoid, output_template}}
    output_template     literal skeleton for fields / json styles
    validator           name of a check in validate.py run on the LLM's answer
    official            vendor-published rewriter prompts: list of {task, url, format, variable, language, drop_lines, preamble, note}
    tailoring           short additive text appended AFTER an official prompt. Keep it small and log why in PLATFORM_NOTES.md.
    sources             [{url, supports, confidence}]
    checked             date the facts were last verified
    confidence          high | medium | low              (how good the sources are)
    extends             id of a profile to inherit from (deep merge; lists are replaced, not appended)
    legacy              values handed to the older nodes through platforms.py (prompt_style, length_guidance, ...)
    hidden              true = loadable by id but not offered in dropdowns

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

MODALITIES = ("image", "edit", "video")
TASKS = ("t2i", "edit", "t2v", "i2v", "flf2v", "ref2v")
CAPTION_STYLES = ("prose", "tags", "tags_prose", "instruction", "json", "fields", "bracket_prose")
ENCODER_FAMILIES = ("clip", "t5", "llm", "")
# yes = a separate negative prompt works | no = none, and naming unwanted things backfires | ignored = distilled, no CFG
# inline = no separate field, but the vendor endorses short exclusions written into the prompt (GPT Image, Seedance, Kling)
NEGATIVE_MODES = ("yes", "no", "ignored", "inline")
QUALITY_MODES = ("forbid", "neutral", "help", "required")
QUOTE_MODES = ("double", "single", "none")
OFFICIAL_FORMATS = ("text", "python_var", "sections")

REQUIRED_KEYS = ("id", "name", "modality", "tasks", "caption_style")


@dataclass
class OfficialPrompt:
    task: str                       # which task this prompt rewrites for; "*" = every task
    url: str
    format: str = "text"            # text: whole file | python_var: a string assigned in a .py | sections: [SYSTEM]/[USER] file
    variable: str = ""              # python_var: the variable name; sections: the section name (default "system")
    language: str = "en"            # language the INSTRUCTIONS are written in
    drop_lines: List[str] = field(default_factory=list)   # regexes; matching lines are removed, and that is logged
    preamble: str = ""              # placed BEFORE the vendor text; for files that are writing guides rather than system prompts
    note: str = ""


@dataclass
class Profile:
    id: str
    name: str
    modality: str
    tasks: List[str]
    caption_style: str
    developer: str = ""
    summary: str = ""
    encoder: str = ""
    encoder_family: str = ""
    languages: List[str] = field(default_factory=lambda: ["en"])
    target_words: Tuple[int, int] = (60, 150)
    words_per_second: Tuple[int, int] = (0, 0)   # video: words of prompt per second of clip; (0, 0) = not known
    max_tokens: int = 0
    max_chars: int = 0
    negative: str = "no"
    negative_default: str = ""
    negative_note: str = ""
    quality_tokens: str = "neutral"
    quality_token_list: List[str] = field(default_factory=list)
    prefix: str = ""
    suffix: str = ""                # quality tags that belong at the END of the prompt (Illustrious); same idea as prefix
    quoted_text: str = "double"
    weights: bool = False
    hex_colors: bool = False
    audio: bool = False
    structure: str = ""
    rules: List[str] = field(default_factory=list)
    avoid: List[str] = field(default_factory=list)
    camera: List[str] = field(default_factory=list)
    task_rules: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    output_template: str = ""
    validator: str = ""
    official: List[OfficialPrompt] = field(default_factory=list)
    tailoring: str = ""
    api_note: str = ""              # hosted models: what to set in the API call (vendor rewriting off, which field takes the prompt)
    sources: List[Dict[str, str]] = field(default_factory=list)
    checked: str = ""
    confidence: str = "medium"
    extends: str = ""
    legacy: Dict[str, Any] = field(default_factory=dict)
    hidden: bool = False
    origin: str = ""                # file the profile was read from

    # -- task-aware accessors ------------------------------------------------------------
    def default_task(self) -> str:
        return self.tasks[0] if self.tasks else "t2i"

    def resolve_task(self, task: Optional[str]) -> str:
        """'auto' / unknown / unsupported -> the profile's first task."""
        if task and task in self.tasks:
            return task
        return self.default_task()

    def for_task(self, task: str, key: str, default: Any = None) -> Any:
        """A per-task override if task_rules has one, else the profile-level value."""
        override = self.task_rules.get(task, {})
        if key in override and override[key] not in (None, "", []):
            return override[key]
        value = getattr(self, key, default)
        return default if value in (None, "") else value

    def words_for(self, task: str) -> Tuple[int, int]:
        low, high = self.for_task(task, "target_words", self.target_words)
        return int(low), int(high)

    def words_for_run(self, task: str, duration_seconds: float = 0.0,
                      override: Optional[Tuple[int, int]] = None) -> Tuple[int, int]:
        """
        The length target for one run. An explicit override wins; else, for a video profile that states
        words_per_second, the clip length decides (never above the profile's upper bound); else words_for.
        """
        if override and override[1] > 0:
            return int(override[0]), int(override[1])
        low, high = self.words_for(task)
        per_low, per_high = self.words_per_second
        if duration_seconds and per_high > 0:
            run_high = min(high, int(per_high * duration_seconds))
            run_low = int(per_low * duration_seconds)
            if run_low >= run_high:                 # a long clip that hits the upper bound
                run_low = int(run_high * 0.8)
            return max(1, run_low), max(2, run_high)
        return low, high

    def official_for(self, task: str) -> Optional[OfficialPrompt]:
        for entry in self.official:
            if entry.task == task:
                return entry
        for entry in self.official:
            if entry.task == "*":
                return entry
        return None


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _word_range(value: Any, fallback: Tuple[int, int]) -> Tuple[int, int]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        low, high = int(value[0]), int(value[1])
        return (min(low, high), max(low, high))
    if isinstance(value, (int, float)) and value > 0:
        return (max(1, int(value * 0.6)), int(value))
    return fallback


def profile_from_dict(data: Dict[str, Any], origin: str = "") -> Tuple[Optional[Profile], List[str]]:
    """Build a Profile from parsed YAML. Returns (profile or None, problems). Never raises on bad data."""
    problems: List[str] = []
    label = data.get("id") or origin or "profile"

    missing = [key for key in REQUIRED_KEYS if not data.get(key)]
    if missing:
        return None, [f"{label}: missing required key(s): {', '.join(missing)}"]

    def checked_enum(key: str, allowed: Tuple[str, ...], default: str) -> str:
        raw_value = data.get(key, default)
        if isinstance(raw_value, bool):          # YAML reads a bare yes / no as a boolean
            raw_value = "yes" if raw_value else "no"
        value = str(raw_value or default)
        if value not in allowed:
            problems.append(f"{label}: {key}='{value}' is not one of {', '.join(a for a in allowed if a)}; using '{default}'")
            return default
        return value

    tasks = [str(task) for task in _as_list(data.get("tasks"))]
    unknown_tasks = [task for task in tasks if task not in TASKS]
    if unknown_tasks:
        problems.append(f"{label}: unknown task(s) {', '.join(unknown_tasks)} ignored")
        tasks = [task for task in tasks if task in TASKS]
    if not tasks:
        return None, problems + [f"{label}: no valid task left"]

    official: List[OfficialPrompt] = []
    for entry in _as_list(data.get("official")):
        if not isinstance(entry, dict) or not entry.get("url"):
            problems.append(f"{label}: an 'official' entry has no url and was skipped")
            continue
        prompt_format = str(entry.get("format", "text"))
        if prompt_format not in OFFICIAL_FORMATS:
            problems.append(f"{label}: official format '{prompt_format}' unknown, entry skipped")
            continue
        official.append(OfficialPrompt(
            task=str(entry.get("task", "*")),
            url=str(entry["url"]),
            format=prompt_format,
            variable=str(entry.get("variable", "")),
            language=str(entry.get("language", "en")),
            drop_lines=[str(pattern) for pattern in _as_list(entry.get("drop_lines"))],
            preamble=str(entry.get("preamble", "")).strip(),
            note=str(entry.get("note", "")),
        ))

    task_rules: Dict[str, Dict[str, Any]] = {}
    for task, overrides in (data.get("task_rules") or {}).items():
        if task not in TASKS or not isinstance(overrides, dict):
            problems.append(f"{label}: task_rules entry '{task}' ignored")
            continue
        cleaned = dict(overrides)
        if "target_words" in cleaned:
            cleaned["target_words"] = _word_range(cleaned["target_words"], (60, 150))
        task_rules[task] = cleaned

    profile = Profile(
        id=str(data["id"]),
        name=str(data["name"]),
        modality=checked_enum("modality", MODALITIES, "image"),
        tasks=tasks,
        caption_style=checked_enum("caption_style", CAPTION_STYLES, "prose"),
        developer=str(data.get("developer", "")),
        summary=str(data.get("summary", "")).strip(),
        encoder=str(data.get("encoder", "")),
        encoder_family=checked_enum("encoder_family", ENCODER_FAMILIES, ""),
        languages=[str(item) for item in _as_list(data.get("languages"))] or ["en"],
        target_words=_word_range(data.get("target_words"), (60, 150)),
        words_per_second=_word_range(data.get("words_per_second"), (0, 0)),
        max_tokens=int(data.get("max_tokens", 0) or 0),
        max_chars=int(data.get("max_chars", 0) or 0),
        negative=checked_enum("negative", NEGATIVE_MODES, "no"),
        negative_default=str(data.get("negative_default", "")).strip(),
        negative_note=str(data.get("negative_note", "")).strip(),
        quality_tokens=checked_enum("quality_tokens", QUALITY_MODES, "neutral"),
        quality_token_list=[str(item) for item in _as_list(data.get("quality_token_list"))],
        prefix=str(data.get("prefix", "")).strip(),
        suffix=str(data.get("suffix", "")).strip(),
        quoted_text=checked_enum("quoted_text", QUOTE_MODES, "double"),
        weights=bool(data.get("weights", False)),
        hex_colors=bool(data.get("hex_colors", False)),
        audio=bool(data.get("audio", False)),
        structure=str(data.get("structure", "")).strip(),
        rules=[str(item) for item in _as_list(data.get("rules"))],
        avoid=[str(item) for item in _as_list(data.get("avoid"))],
        camera=[str(item) for item in _as_list(data.get("camera"))],
        task_rules=task_rules,
        output_template=str(data.get("output_template", "")).rstrip(),
        validator=str(data.get("validator", "")),
        official=official,
        tailoring=str(data.get("tailoring", "")).strip(),
        api_note=str(data.get("api_note", "")).strip(),
        sources=[dict(item) for item in _as_list(data.get("sources")) if isinstance(item, dict)],
        checked=str(data.get("checked", "")),
        confidence=str(data.get("confidence", "medium")),
        extends=str(data.get("extends", "")),
        legacy=dict(data.get("legacy") or {}),
        hidden=bool(data.get("hidden", False)),
        origin=origin,
    )
    return profile, problems
