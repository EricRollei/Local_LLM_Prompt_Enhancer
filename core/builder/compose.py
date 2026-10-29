"""
Composer state -> wildcard template text, and prompt sections in platform order.

The builder widget stores its state as JSON in the node's hidden `composer` widget:

    {
      "v": 1,
      "parts": {
        "subject": [ {"t": "text", "v": "a"}, {"t": "tok", "id": 1}, {"t": "text", "v": "in typical uniform"} ]
      },
      "tokens": {
        "1": {"slot": "age", "key": "cyberrealistic_v10/cyberdelia/miscellaneous/cyber_age",
              "mode": "subset", "picks": ["young adult", "elderly"], "count": 1, "keep": "exact"}
      }
    }

mode   random   any entry of the list                     __key__
       fixed    always picks[0] (may be your own text)     {1$$value}
       subset   random among picks                         {a|b|c}
       exclude  random, never one of picks                 __key!{a|b}__
count  how many distinct picks, joined with " and "        {2$$ and $$...}
keep   how the LLM rewriter treats the pick (binding markers of the wildcard engine):
       meaning (default, wording may change), exact (=, kept word for word), loose (?, may be dropped)

Text between pills is used as typed, and may itself hold wildcard syntax ({red|blue}, __name__). Pieces are joined with single spaces and a space before
, . ; : ! ? is removed, so "a", pill, ", with" reads "a young adult, with".

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

MODES = ("random", "fixed", "subset", "exclude")
KEEP_MARKERS = {"meaning": "", "concept": "", "exact": "=", "verbatim": "=", "loose": "?"}
MAX_COUNT = 8
JOINER = " and "

# Canonical prompt sections. This tuple is the SEED order (section_seed_offset): new sections are
# only ever appended, so saved workflows keep re-rolling the same picks. See dev/PROMPT_TAXONOMY_SPEC.md.
SECTIONS = ("subject", "action", "setting", "lighting", "style", "camera", "format", "composition", "text", "prompt")
# The order sections are built and joined in when neither the node nor the platform says otherwise.
DEFAULT_ORDER = ("format", "prompt", "subject", "action", "setting", "lighting", "composition", "camera", "style", "text")
# Sections a node shows only when added ("+ Section").
OPTIONAL_SECTIONS = ("text", "prompt")
SECTION_LABELS = {
    "format": "Format", "subject": "Subject", "action": "Action", "setting": "Setting",
    "lighting": "Light & atmosphere", "composition": "Composition", "camera": "Camera",
    "style": "Style & finish", "text": "Text", "prompt": "Prompt",
}
# Words in a profile's `structure` line that name each section.
_SECTION_WORDS = {
    "prompt": r"full prompt|base prompt|prompt file",
    "format": r"format|image type|type of image|medium|intended use|use first|photograph of|poster|product shot",
    "subject": r"subjects?|who|character|entity",
    "action": r"actions?|pose|poses|motion|doing",
    "setting": r"setting|background|context|environment|location|scene|place",
    "lighting": r"light|lighting|atmosphere",
    "composition": r"composition|compositional|framing|layout|placement|viewpoint|shot size",
    "camera": r"camera|technical|lens|focal length|aperture|shot",
    "style": r"style|aesthetic|art ?style|finish|stylisation|stylization",
    "text": r"text|lettering|typography|wording",
}

_ESCAPE = re.compile(r"([{}|$\[\]#\\])")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?])")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")


def escape_literal(text: str) -> str:
    """Make typed text or a picked entry safe inside wildcard syntax."""
    escaped = _ESCAPE.sub(r"\\\1", text or "")
    return escaped.replace("__", "\\_\\_")


def join_pieces(pieces: Sequence[str]) -> str:
    joined = " ".join(piece.strip() for piece in pieces if piece and piece.strip())
    joined = _SPACE_BEFORE_PUNCT.sub(r"\1", joined)
    return _MULTI_SPACE.sub(" ", joined).strip()


@dataclass
class Token:
    id: str
    slot: str = ""
    key: str = ""
    mode: str = "random"
    picks: List[str] = field(default_factory=list)
    count: int = 1
    keep: str = "meaning"

    @classmethod
    def from_dict(cls, token_id: str, data: Dict[str, Any]) -> "Token":
        mode = str(data.get("mode", "random"))
        try:
            count = int(data.get("count", 1))
        except (TypeError, ValueError):
            count = 1
        return cls(
            id=str(token_id),
            slot=str(data.get("slot", "") or ""),
            key=str(data.get("key", "") or "").strip().strip("_").replace("\\", "/"),
            mode=mode if mode in MODES else "random",
            picks=[str(pick) for pick in (data.get("picks") or []) if str(pick).strip()],
            count=max(1, min(MAX_COUNT, count)),
            keep=str(data.get("keep", "meaning") or "meaning"),
        )

    @property
    def marker(self) -> str:
        return KEEP_MARKERS.get(self.keep, "")

    def syntax(self) -> str:
        """Wildcard-engine text for this pill. '' when it cannot produce anything."""
        marker = self.marker
        many = self.count > 1
        count_prefix = f"{self.count}$${JOINER}$$" if many else ""

        if self.mode == "fixed" and self.picks:
            return "{" + marker + "1$$" + escape_literal(self.picks[0]) + "}"
        if self.mode == "subset" and self.picks:
            options = "|".join(escape_literal(pick) for pick in self.picks)
            if not many and len(self.picks) == 1:
                return "{" + marker + "1$$" + options + "}"
            return "{" + marker + count_prefix + options + "}"
        if not self.key:
            return ""
        if self.mode == "exclude" and self.picks:
            # Exclusions cannot contain | { } or a newline (grammar limit); those picks are skipped.
            usable = [pick for pick in self.picks if not re.search(r"[|{}\n]", pick)]
            body = "__" + self.key + ("!{" + "|".join(usable) + "}" if usable else "") + "__"
        else:
            body = "__" + self.key + "__"
        if many:
            return "{" + marker + count_prefix + body + "}"
        return "__" + marker + body[2:] if marker else body


@dataclass
class ComposerState:
    parts: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    tokens: Dict[str, Token] = field(default_factory=dict)
    locks: Dict[str, int] = field(default_factory=dict)     # section -> the seed it is held at
    fill: Dict[str, bool] = field(default_factory=dict)     # section -> an empty section is written by the LLM
    order: List[str] = field(default_factory=list)          # the node's own section order ([] = the platform's)
    kinds: Dict[str, str] = field(default_factory=dict)     # subject section -> person | animal | ... | scene
    errors: List[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, raw: str) -> "ComposerState":
        state = cls()
        if not (raw or "").strip():
            return state
        try:
            data = json.loads(raw)
        except ValueError as error:
            # Not JSON: treat the whole thing as a plain subject template (hand-written or pasted).
            state.parts["subject"] = [{"t": "raw", "v": raw}]
            state.errors.append(f"composer is not JSON ({error}); used as plain text")
            return state
        if not isinstance(data, dict):
            state.errors.append("composer JSON is not an object; ignored")
            return state
        for token_id, token in (data.get("tokens") or {}).items():
            if isinstance(token, dict):
                state.tokens[str(token_id)] = Token.from_dict(str(token_id), token)
        for section, segments in (data.get("parts") or {}).items():
            if isinstance(segments, list):
                state.parts[str(section)] = [segment for segment in segments if isinstance(segment, dict)]
        for section, seed in (data.get("locks") or {}).items():
            try:
                state.locks[str(section)] = int(seed)
            except (TypeError, ValueError):
                state.errors.append(f"{section}: lock seed {seed!r} is not a number; ignored")
        state.fill = {str(section): True for section, on in (data.get("fill") or {}).items() if on}
        order = data.get("order") or []
        if isinstance(order, list):
            state.order = [str(section) for section in order if str(section) in SECTIONS]
        kinds = data.get("kinds") or {}
        if isinstance(kinds, dict):
            state.kinds = {str(section): str(kind) for section, kind in kinds.items() if kind}
        return state

    def scene_only(self, section: str) -> bool:
        """A subject section set to 'Scene only': deliberately no subject."""
        return base_section(section) == "subject" and self.kinds.get(section) == "scene"

    def templates(self) -> Dict[str, str]:
        """section -> wildcard template text."""
        out: Dict[str, str] = {}
        for section, segments in self.parts.items():
            pieces: List[str] = []
            for segment in segments:
                kind = segment.get("t")
                if kind in ("text", "raw"):
                    # Typed text keeps wildcard syntax working: {red|blue} or __name__ typed by hand still resolve.
                    pieces.append(str(segment.get("v", "")))
                elif kind == "tok":
                    token = self.tokens.get(str(segment.get("id")))
                    if token is None:
                        self.errors.append(f"{section}: pill {segment.get('id')} has no settings; skipped")
                        continue
                    syntax = token.syntax()
                    if not syntax:
                        self.errors.append(f"{section}: {token.slot or 'pill'} has no list chosen; skipped")
                        continue
                    pieces.append(syntax)
            text = join_pieces(pieces)
            if text:
                out[section] = text
        return out


# ----------------------------------------------------------------------------- platform order
def base_section(section: str) -> str:
    """'subject_2' -> 'subject'."""
    return re.sub(r"_\d+$", "", section or "")


def section_label(section: str) -> str:
    match = re.match(r"(.+)_(\d+)$", section or "")
    if match:
        return f"{SECTION_LABELS.get(match.group(1), match.group(1).title())} {match.group(2)}"
    return SECTION_LABELS.get(section, (section or "").title())


def section_seed_offset(section: str) -> int:
    """Each section rolls from seed + its offset, so re-rolling or locking one leaves the others alone."""
    base = base_section(section)
    index = SECTIONS.index(base) if base in SECTIONS else len(SECTIONS) + (sum(map(ord, base)) % 97)
    extra = re.search(r"_(\d+)$", section or "")
    return index + (100 * (int(extra.group(1)) - 1) if extra else 0)


def section_order(structure: str) -> List[str]:
    """
    Canonical sections in the order a profile's `structure` line mentions them. Sections the
    line does not mention follow in DEFAULT_ORDER. "" -> DEFAULT_ORDER.
    """
    lowered = (structure or "").lower()
    positions: List[Tuple[int, int, str]] = []
    for default_index, section in enumerate(DEFAULT_ORDER):
        match = re.search(r"\b(?:" + _SECTION_WORDS[section] + r")\b", lowered)
        position = match.start() if match else 10_000 + default_index
        positions.append((position, default_index, section))
    return [section for _pos, _index, section in sorted(positions)]


def order_sections(sections, order: Sequence[str]) -> List[str]:
    """
    The given section names in platform order. Subject 2, 3 ... follow their base section
    (Krea 2 keeps each subject with its own attributes); unknown sections go last.
    """
    names = list(sections)

    def key(name: str):
        base = base_section(name)
        position = list(order).index(base) if base in order else len(order)
        number = int(name.rsplit("_", 1)[1]) if name != base else 1
        return (position, number, name)

    return sorted(names, key=key)


def join_sections(sections: Dict[str, str], order: Sequence[str]) -> str:
    """Section texts in platform order (unknown sections last), comma-joined."""
    ordered = [section for section in order_sections(sections, order) if sections[section].strip()]
    return join_pieces([sections[section].strip().rstrip(",") + "," for section in ordered]).rstrip(",").strip()
