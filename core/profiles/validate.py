"""
Checks and clean-up applied to the LLM's answer before it leaves the node.

clean_llm_output()   removes what local models add around the answer: <think> blocks, code fences,
                     "Prompt:" labels, the wrappers some vendor rewriters ask for (<recaption>,
                     {"Rewritten": ...}, {"revised_prompt": ...}).
check()              runs the profile's validator plus the checks every profile gets (length,
                     quality boilerplate, negations). It returns the text - repaired where a repair
                     is safe and mechanical - and a list of warnings. It never raises and never
                     throws the text away: a warning is information for the user, not a gate.

Validators (profile key `validator`):
    json              the answer must parse as a JSON object; output is re-serialised compactly
    ideogram_json     json + Ideogram 4 key order + uppercase hex
    h3_fields         MiniMax H3 base format: three named fields in order, [Shot 1] present, <d> tags balanced
    h3_ref_fields     MiniMax H3 reference format: six named sections in order
    hailuo_brackets   only the 15 documented camera commands, at most 3 per bracket
    tags              comma-separated, no sentences, prefix present
    edit_instruction  short, and says what stays the same

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from .schema import Profile

THINK_BLOCK = re.compile(r"<think>.*?</think>", re.S | re.I)
OPEN_THINK = re.compile(r"^.*?</think>", re.S | re.I)
WRAPPER_TAGS = ("recaption", "answer", "prompt", "output", "final")
LABEL_PREFIX = re.compile(
    r"^\s*(?:here(?:'s| is)[^\n:]*:|(?:final |enhanced |rewritten |revised |expanded )?prompt\s*:|output\s*:|rewritten\s*:)\s*",
    re.I,
)
JSON_TEXT_KEYS = ("revised_prompt", "rewritten_prompt", "Rewritten", "rewritten", "prompt", "rewritten_text")

BOILERPLATE = [
    "masterpiece", "best quality", "highly detailed", "ultra detailed", "ultra-detailed", "8k", "4k", "uhd",
    "award-winning", "award winning", "trending on artstation", "hyper realistic", "hyperrealistic",
    "ultra hd", "extremely detailed",
]
NEGATION = re.compile(r"\b(?:no|without|don't|do not|never|avoid)\s+\w+", re.I)

HAILUO_COMMANDS = {
    "truck left", "truck right", "pan left", "pan right", "push in", "pull out", "pedestal up",
    "pedestal down", "tilt up", "tilt down", "zoom in", "zoom out", "shake", "tracking shot", "static shot",
}
H3_BASE_FIELDS = ["integrated_multimodal_description", "overall_soundscape", "non_diegetic_music"]
H3_REF_FIELDS = ["subject_definitions", "summary", "retention_analysis", "detailed_description",
                 "overall_soundscape", "non_diegetic_music"]

IDEOGRAM_TOP = ["aspect_ratio", "high_level_description", "style_description", "compositional_deconstruction"]


# -- cleaning -----------------------------------------------------------------------------
def _strip_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def extract_json_object(text: str) -> Any:
    """First balanced {...} in the text, parsed. Raises ValueError when there is none."""
    text = _strip_fences(text)
    try:
        return json.loads(text)
    except ValueError:
        pass
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in the answer")
    depth, in_string, escaped = 0, False, False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:index + 1])
    raise ValueError("unbalanced JSON in the answer")


def clean_llm_output(text: str, keep_json: bool = False) -> str:
    """Strip reasoning, fences, labels and vendor wrappers. keep_json=True leaves a JSON answer alone."""
    cleaned = THINK_BLOCK.sub("", text or "")
    if "</think>" in cleaned.lower():                 # reasoning with no opening tag
        cleaned = OPEN_THINK.sub("", cleaned, count=1)
    cleaned = cleaned.strip()

    for tag in WRAPPER_TAGS:
        match = re.search(rf"<{tag}>(.*?)(?:</{tag}>|$)", cleaned, re.S | re.I)
        if match and match.group(1).strip():
            cleaned = match.group(1).strip()
            break

    cleaned = _strip_fences(cleaned)

    if not keep_json and cleaned.startswith("{"):
        try:
            parsed = extract_json_object(cleaned)
            if isinstance(parsed, dict):
                for key in JSON_TEXT_KEYS:
                    if isinstance(parsed.get(key), str) and parsed[key].strip():
                        cleaned = parsed[key].strip()
                        break
        except ValueError:
            pass

    cleaned = LABEL_PREFIX.sub("", cleaned, count=1).strip()
    if len(cleaned) > 1 and cleaned[0] == cleaned[-1] and cleaned[0] in "\"'" and cleaned.count(cleaned[0]) == 2:
        cleaned = cleaned[1:-1].strip()
    return cleaned


# -- validators ---------------------------------------------------------------------------
def _validate_json(text: str, profile: Profile, warnings: List[str]) -> str:
    try:
        parsed = extract_json_object(text)
    except ValueError as error:
        warnings.append(f"the answer is not valid JSON ({error}); passed through unchanged")
        return text
    if not isinstance(parsed, dict):
        warnings.append("the JSON answer is not an object; passed through unchanged")
        return text
    return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))


def _upper_hex(value: Any) -> Any:
    if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return value.upper()
    if isinstance(value, list):
        return [_upper_hex(item) for item in value]
    if isinstance(value, dict):
        return {key: _upper_hex(item) for key, item in value.items()}
    return value


def _validate_ideogram_json(text: str, profile: Profile, warnings: List[str]) -> str:
    try:
        parsed = extract_json_object(text)
    except ValueError as error:
        warnings.append(f"the answer is not valid JSON ({error}); passed through unchanged")
        return text
    if not isinstance(parsed, dict):
        warnings.append("the JSON answer is not an object; passed through unchanged")
        return text
    parsed = _upper_hex(parsed)
    ordered = {key: parsed[key] for key in IDEOGRAM_TOP if key in parsed}
    ordered.update({key: value for key, value in parsed.items() if key not in ordered})
    deconstruction = ordered.get("compositional_deconstruction")
    if not isinstance(deconstruction, dict):
        warnings.append("Ideogram JSON has no compositional_deconstruction (required)")
    else:
        if "background" not in deconstruction:
            warnings.append("Ideogram JSON: compositional_deconstruction.background is missing (required)")
        if not deconstruction.get("elements"):
            warnings.append("Ideogram JSON: compositional_deconstruction.elements is missing or empty")
    warnings.append("for Ideogram 4 the dedicated Ideogram Magic Prompt node does fuller key-order repair and bbox handling")
    return json.dumps(ordered, ensure_ascii=False, separators=(",", ":"))


def _field_positions(text: str, names: List[str]) -> Dict[str, int]:
    positions = {}
    for name in names:
        match = re.search(rf"(?m)^[ \t>*#-]*{re.escape(name)}[ \t]*:", text)
        if match:
            positions[name] = match.start()
    return positions


def _validate_fields(text: str, names: List[str], label: str, warnings: List[str]) -> str:
    # Local models like to decorate field names (**name:**, ## name:). The model wants them bare.
    for name in names:
        text = re.sub(rf"(?m)^[ \t>*#-]*\**{re.escape(name)}\**[ \t]*:\**[ \t]*", f"{name}: ", text)
    positions = _field_positions(text, names)
    missing = [name for name in names if name not in positions]
    if missing:
        warnings.append(f"{label}: missing field(s): {', '.join(missing)}")
    present = [name for name in names if name in positions]
    if [positions[name] for name in present] != sorted(positions[name] for name in present):
        warnings.append(f"{label}: fields are out of order; expected {' -> '.join(names)}")
    return text


def _check_h3_common(text: str, warnings: List[str]) -> None:
    if "[Shot 1]" not in text:
        warnings.append("H3: no [Shot 1] marker")
    if re.search(r"\[Shot 1\][^\[]{0,40}\bAt \d\d:\d\d", text):
        warnings.append("H3: [Shot 1] must not carry a timestamp")
    opened, closed = len(re.findall(r"<d>", text)), len(re.findall(r"</d>", text))
    if opened != closed:
        warnings.append(f"H3: unbalanced dialogue tags ({opened} <d> vs {closed} </d>)")
    for line in re.findall(r"<d>(.*?)</d>", text, re.S):
        if not re.match(r"\s*\[[A-Za-z]+\]", line):
            warnings.append("H3: a <d> line has no [Language] tag at its start")
            break
    if opened and not re.search(r"\(S\d(?:,S\d)*\)", text):
        warnings.append("H3: dialogue without a speaker id such as (S1)")
    if "\u2014" in text or "\u2013" in text:
        pass  # the official keyframe instruction lines contain an em dash, so dashes are legal here


def _validate_h3_fields(text: str, profile: Profile, warnings: List[str]) -> str:
    text = _validate_fields(text, H3_BASE_FIELDS, "H3", warnings)
    _check_h3_common(text, warnings)
    return text


def _validate_h3_ref_fields(text: str, profile: Profile, warnings: List[str]) -> str:
    text = _validate_fields(text, H3_REF_FIELDS, "H3 reference", warnings)
    _check_h3_common(text, warnings)
    return text


def _validate_hailuo(text: str, profile: Profile, warnings: List[str]) -> str:
    def repair(match: "re.Match[str]") -> str:
        commands = [part.strip() for part in match.group(1).split(",") if part.strip()]
        known = [command for command in commands if command.lower() in HAILUO_COMMANDS]
        unknown = [command for command in commands if command.lower() not in HAILUO_COMMANDS]
        if unknown:
            warnings.append(f"Hailuo: unknown camera command(s) removed: {', '.join(unknown)}")
        if len(known) > 3:
            warnings.append("Hailuo: more than 3 commands in one bracket; kept the first 3")
            known = known[:3]
        if not known:
            return ""
        return "[" + ",".join(command[0].upper() + command[1:].lower() for command in known) + "]"

    repaired = re.sub(r"\[([^\[\]]{1,80})\]", repair, text)
    return re.sub(r"[ \t]{2,}", " ", repaired).strip()


KLING_SHOT = re.compile(r"(?im)^\s*shot\s*(\d+)\b([^\n]*)")
KLING_SHOT_EXACT = re.compile(r"(?i)^\s*shot\s*\d+\s*,\s*\d+\s*,\s*\S.*;\s*$")


def _validate_kling_shots(text: str, profile: Profile, warnings: List[str]) -> str:
    """Kling's multi-shot form is 'shot n, seconds, words;'. Single-shot prose passes untouched."""
    shots = list(KLING_SHOT.finditer(text))
    if len(shots) < 2:
        return text
    lines = [line for line in text.split("\n") if re.match(r"(?i)^\s*shot\s*\d+\b", line)]
    inexact = [line for line in lines if not KLING_SHOT_EXACT.match(line)]
    if inexact:
        warnings.append("Kling multi-shot: lines are not in the exact form 'shot 1, 3, words;' (number, whole seconds, words, semicolon): "
                        + inexact[0].strip()[:60] + " ...")
    if len(shots) > 6:
        warnings.append(f"Kling multi-shot: {len(shots)} shots; the API accepts at most 6")
    longest = max((len(line) for line in lines), default=0)
    if longest > 512:
        warnings.append(f"Kling multi-shot: a shot is {longest} characters; the limit is 512 per shot")
    return text


def _validate_tags(text: str, profile: Profile, warnings: List[str]) -> str:
    flat = " ".join(text.split())
    # A tag is a few words. A comma-free run of more than eight words is a sentence.
    long_segments = [segment for segment in re.split(r"[,;.!?]\s*", flat) if len(segment.split()) > 8]
    if long_segments:
        warnings.append("tag format expected, but the answer contains full sentences")
    if profile.negative == "yes":
        # "no glow, no mist" in a POSITIVE tag prompt summons glow and mist. Those belong in the negative prompt.
        tags = [tag.strip() for tag in flat.split(",")]
        negated = [tag for tag in tags if re.match(r"(?i)^(?:no|without|avoid|never)\s+\w", tag)]
        if negated:
            flat = ", ".join(tag for tag in tags if tag and tag not in negated)
            warnings.append(f"{len(negated)} 'no ...' tags removed from the positive prompt (they belong in the negative): "
                            + ", ".join(negated[:4]) + (" ..." if len(negated) > 4 else ""))
    return flat


# -- instruction leaks ----------------------------------------------------------------------
# A long instruction block stops being read as rules and starts being read as text to include.
# Observed in a real run: "the law of the garden holds: only patterned fabric may cross the boundary
# between a body and a wall" and "no symbolic objects, no emotional expression, no text or captions"
# arrived inside a positive Krea2 prompt, the second of those from the very line that forbids writing
# 'no X'. No amount of further instruction fixes this; removing the clauses mechanically does.
#
# The unit of removal is the CLAUSE, not the sentence: these leaks arrive as trailing comma- or
# dash-separated clauses inside an otherwise good sentence, and taking the whole sentence would cost
# real description.
INSTRUCTION_LEAK = re.compile(
    r"""(?ix)
    (?: the \s+ (?: law | rule ) \s+ (?: of \s+ the \s+ \w+ \s+ )? (?: holds | is | states | applies | governs ) )
  | (?: (?: which | that | it ) \s+ )? (?: obeys | follows | observes ) \s+ (?: this | the ) \s+ (?: law | rule )
  | (?: in \s+ (?: accordance | keeping ) \s+ with \s+ (?: this | the ) \s+ (?: law | rule ) )
  | (?: no \s+ (?: further | additional | other )? \s* symbolic \s+ \w+ )
  | (?: no \s+ (?: text | captions? | titles? | watermarks? | lettering | writing ) \b )
  | (?: no \s+ emotional \s+ (?: expression | melodrama | display ) )
  | (?: no \s+ (?: explanation | symbolism | moral | caption ) )
  | (?: exactly \s+ (?: one | ONE ) \s+ anomal )
  | (?: the \s+ (?: anomaly | premise | rupture | transformation \s+ rule ) \b )
  | (?: stated? \s+ as \s+ plain \s+ physical \s+ fact )
  | (?: (?: the \s+ way \s+ )? a \s+ (?: police \s+ )? report \s+ would )
  | (?: (?: image | diffusion ) \s+ model )
  | (?: (?: positive | negative ) \s+ prompt )
  | (?: register \s* : )
  | (?: THE \s+ SUBJECT )
  | (?: rigorously \s+ ordinary )
  | (?: never \s+ name \s+ the \s+ emotion )
  | (?: pose \s+ the \s+ question \s+ and \s+ refuse )
    """
)
# A clause that merely excludes something. In a positive prose prompt "no mist" summons mist, exactly as
# it does in a tag list, where _validate_tags has always removed it.
#
# [a-z] was wrong: it matched "no mist" but not "no 4K", "no 3D render" or "no 8M", which is precisely the
# form a repetition collapse takes. Anything that is not whitespace or a separator counts.
NEGATION_CLAUSE = re.compile(r"(?i)^\s*(?:and\s+|but\s+|with\s+)?(?:no|without)\s+[^\s,;]")
_DIGITS = re.compile(r"\d+")
_CLAUSE_SPLIT = re.compile(r"\s*(,|;|\s+[-–—]+\s+)\s*")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


REPEAT_LIMIT = 3          # the same clause SHAPE more than three times is a model looping, not a description


def strip_instruction_leaks(text: str, drop_negations: bool = True) -> Tuple[str, List[str], List[str], int]:
    """(cleaned, leaked clauses, negation clauses, repeated clauses dropped).

    drop_negations defaults to True and should stay true for every positive prompt. It was first gated on the
    model HAVING a negative prompt, on the reasoning that there was otherwise nowhere to move the exclusion
    to - which is backwards. 'no mist' summons mist whether or not the model offers a negative field; with
    nowhere to move it, the right answer is still to delete it."""
    leaked: List[str] = []
    negated: List[str] = []
    repeats = 0
    shapes: Dict[str, int] = {}
    kept_sentences: List[str] = []
    for sentence in _SENTENCE_SPLIT.split(text):
        if not sentence.strip():
            continue
        pieces = _CLAUSE_SPLIT.split(sentence)
        # pieces alternates clause, separator, clause, ...
        clauses = pieces[0::2]
        separators = pieces[1::2]
        keep_clause, keep_separator = [], []
        for index, clause in enumerate(clauses):
            bare = clause.strip()
            if not bare:
                continue
            if INSTRUCTION_LEAK.search(bare):
                leaked.append(bare)
                continue
            if drop_negations and NEGATION_CLAUSE.match(bare):
                negated.append(bare)
                continue
            # Repetition collapse: "no 4K, no 8K, no 16K ..." for twelve thousand characters. Digits are
            # normalised away so the whole run reduces to one shape, and only the first few are kept.
            shape = _DIGITS.sub("#", bare.lower())
            shapes[shape] = shapes.get(shape, 0) + 1
            if shapes[shape] > REPEAT_LIMIT:
                repeats += 1
                continue
            keep_clause.append(bare)
            keep_separator.append(separators[index] if index < len(separators) else "")
        if not keep_clause:
            continue
        rebuilt = ""
        for index, clause in enumerate(keep_clause):
            rebuilt += clause
            if index < len(keep_clause) - 1:
                separator = keep_separator[index].strip()
                rebuilt += "; " if separator == ";" else ", "
        kept_sentences.append(rebuilt)
    cleaned = " ".join(kept_sentences)
    # A dropped final clause can leave a dangling comma or a doubled full stop.
    cleaned = re.sub(r"\s*,\s*([.!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s*,\s*$", "", cleaned.strip())
    cleaned = re.sub(r"([.!?])\1+", r"\1", cleaned)
    # Only close a sentence that was one to begin with: a tag list must not gain a full stop.
    if cleaned and text.rstrip().endswith((".", "!", "?")) and not cleaned.endswith((".", "!", "?", '"')):
        cleaned += "."
    return cleaned, leaked, negated, repeats


# Where a leak is worth hunting: free-running text. Structured formats (json, named fields, per-shot
# lines) are held in shape by their own validators, and splitting them on commas would damage them.
LEAK_CHECKED_STYLES = ("prose", "tags_prose", "tags", "instruction", "bracket_prose")

RUNAWAY_FACTOR = 2.5      # past this multiple of the profile's upper word bound the answer is broken, not long


def _truncate_words(text: str, limit: int) -> str:
    """Cut to `limit` words, preferring the last sentence end, then the last clause end, before that point."""
    words = re.findall(r"\S+", text)
    if len(words) <= limit:
        return text
    head = " ".join(words[:limit])
    for boundary in (r"[.!?](?=[^.!?]*$)", r"[,;](?=[^,;]*$)"):
        match = list(re.finditer(boundary, head))
        if match and match[-1].end() > len(head) * 0.5:
            return head[:match[-1].end()].rstrip(",; ").rstrip() + ("" if head[match[-1].start()] in ".!?" else ".")
    return head.rstrip(",; ") + "."


def _validate_edit(text: str, profile: Profile, warnings: List[str]) -> str:
    if not re.search(r"\b(keep|keeping|maintain|maintaining|preserv|unchanged|same|identical|stays?)\b", text, re.I):
        warnings.append("edit instruction does not say what must stay the same")
    return text


VALIDATORS: Dict[str, Callable[[str, Profile, List[str]], str]] = {
    "json": _validate_json,
    "ideogram_json": _validate_ideogram_json,
    "h3_fields": _validate_h3_fields,
    "h3_ref_fields": _validate_h3_ref_fields,
    "hailuo_brackets": _validate_hailuo,
    "tags": _validate_tags,
    "kling_shots": _validate_kling_shots,
    "edit_instruction": _validate_edit,
}


# -- the one entry point --------------------------------------------------------------------
def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def check(text: str, profile: Profile, task: str, word_range: Optional[Tuple[int, int]] = None) -> Tuple[str, List[str]]:
    """word_range: the (low, high) this run asked for, when it differs from the profile's standing range."""
    warnings: List[str] = []
    is_json = profile.caption_style == "json"
    cleaned = clean_llm_output(text, keep_json=is_json)
    if not cleaned:
        return "", ["the LLM returned an empty answer"]

    validator_name = profile.for_task(task, "validator", profile.validator)
    validator = VALIDATORS.get(validator_name or "")
    if validator_name and validator is None:
        warnings.append(f"profile names an unknown validator '{validator_name}'")
    if validator is not None:
        try:
            cleaned = validator(cleaned, profile, warnings)
        except Exception as error:  # a validator bug must never cost the user their prompt
            warnings.append(f"validator '{validator_name}' failed ({error}); text passed through")

    # instruction leaks: the block was transcribed instead of obeyed. Mechanical, and independent of
    # any model choosing to co-operate.
    if profile.caption_style in LEAK_CHECKED_STYLES:
        try:
            repaired, leaked, negated, repeats = strip_instruction_leaks(cleaned)
            if repaired and (leaked or negated or repeats):
                cleaned = repaired
                if leaked:
                    warnings.append(f"{len(leaked)} clause(s) of the instruction block were copied into the prompt and have been "
                                    "removed: " + " / ".join(clause[:70] for clause in leaked[:3]) + (" ..." if len(leaked) > 3 else ""))
                if negated:
                    destination = "put them in the negative prompt" if profile.negative in ("yes", "inline") else \
                                  "this model has no negative prompt, so they are simply dropped"
                    warnings.append(f"{len(negated)} 'no ...' clause(s) removed from the positive prompt (they summon what they "
                                    f"exclude; {destination}): " + " / ".join(clause[:50] for clause in negated[:3])
                                    + (" ..." if len(negated) > 3 else ""))
                if repeats:
                    warnings.append(f"the model looped: {repeats} repeated clause(s) removed. A prompt that degenerates into a "
                                    "repeating pattern usually means the request was too long or too constrained for it.")
            elif (leaked or negated) and not repaired:
                warnings.append("the answer was almost entirely instruction text; it has been left alone for you to judge")
        except Exception as error:      # a guard bug must never cost the user their prompt
            warnings.append(f"instruction-leak guard failed ({error}); text passed through")

    # prefix: mechanical and safe to repair
    if profile.prefix and profile.quality_tokens == "required" and not is_json:
        if not cleaned.lower().startswith(profile.prefix.lower().rstrip(", ")):
            cleaned = f"{profile.prefix.rstrip(', ')}, {cleaned}"
            warnings.append("required prefix was missing and has been added")

    # suffix: the same repair at the other end. Tags already present anywhere are not repeated.
    if profile.suffix and profile.quality_tokens == "required" and not is_json:
        lowered = cleaned.lower()
        absent = [tag.strip() for tag in profile.suffix.split(",") if tag.strip() and tag.strip().lower() not in lowered]
        if absent:
            cleaned = f"{cleaned.rstrip().rstrip(',')}, {', '.join(absent)}"
            warnings.append("required closing quality tags were missing and have been added")

    first_line = profile.for_task(task, "first_line", "")
    if first_line and "S.SS" not in first_line and not cleaned.startswith(first_line):
        cleaned = f"{first_line}\n\n{cleaned}"
        warnings.append("required first line was missing and has been added")

    if not is_json:
        low, high = word_range if word_range and word_range[1] > 0 else profile.words_for(task)
        count = word_count(cleaned)
        # A runaway answer is not a long prompt, it is a broken one: a model that loops can emit thousands of
        # words, and everything past the model's own limit is discarded by the sampler anyway. Cut it at a
        # sentence boundary rather than handing the user twelve thousand characters of "no 4K, no 8K".
        if high and count > high * RUNAWAY_FACTOR:
            trimmed = _truncate_words(cleaned, int(high * RUNAWAY_FACTOR))
            warnings.append(f"runaway answer: {count} words for a {low}-{high} word target, cut to {word_count(trimmed)}. "
                            "The model almost certainly lost the thread; re-run before using this.")
            cleaned = trimmed
            count = word_count(cleaned)
        if count > high * 1.35:
            warnings.append(f"{count} words; the target for {profile.name} is {low}-{high}")
        elif count < low * 0.5:
            warnings.append(f"only {count} words; the target for {profile.name} is {low}-{high}")
        if profile.max_tokens and count > profile.max_tokens * 0.75:
            warnings.append(f"about {int(count / 0.72)} tokens, over the {profile.max_tokens}-token limit: the end will be cut off")
        if profile.max_chars and len(cleaned) > profile.max_chars:
            warnings.append(f"{len(cleaned)} characters, over the {profile.max_chars}-character limit")

        if profile.quality_tokens == "forbid":
            lowered = cleaned.lower()
            found = [token for token in BOILERPLATE if re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", lowered)]
            if found:
                warnings.append(f"quality boilerplate this model does not want: {', '.join(found)}")

        if profile.negative in ("no", "ignored") and profile.caption_style in ("prose", "bracket_prose"):
            negations = NEGATION.findall(cleaned)
            if len(negations) >= 2:
                warnings.append(
                    f"{len(negations)} negations ('{negations[0]}', ...) in a prompt for a model without a negative prompt"
                )
    return cleaned, warnings
