"""
Recursive-descent parser for the wildcard grammar.

Grammar (Dynamic Prompts compatible, so existing wildcard packs work, plus extensions):

    __name__  __dir/name__  __colors*__  __artists/**__     file wildcards, globbing
    __name(season=winter)__                                 parameterized wildcard
    __name[metal AND NOT large]__   __[metal AND small]__   tag query (scoped / global)
    __db:surreal portrait__   __llm:an object that ...__    provider slots
    {a|b|c}   {a|{b|c}}                                     variants, nested
    {3::common|1::rare}                                     weights
    {2$$a|b|c}   {1-3$$ and $$a|b|c}   {2$$__flavours__}    multi-select, separator
    {-3$$a|b|c|d}   {2-$$a|b|c|d}                           open ranges: 1..3, 2..all
    ${x=!__animal__}  ${x=__animal__}  ${x}  ${x:default}   variables (immediate / deferred)
    [if night AND NOT rain : neon | sunlight]               conditionals
    # a comment line

Markers, placed right after the opening `{` or `__`, in any order:
    =  verbatim binding      ?  loose binding      ~  random sampler      @  cyclical sampler

Legacy (video_prompter v1) forms, enabled with legacy=True:
    {label:a|b|c}     labelled inline options; the label names the slot
    {animal}          handled in the resolver: a bare name that matches a wildcard file

Safety rules, because real prompts contain braces, hashes and underscores:
    - A `{...}` with a single option and no `$$` is NOT a variant. It is emitted
      literally, braces included. This keeps JSON prompts (Ideogram 4, FLUX.2) intact.
      (The resolver may still treat it as a legacy {category}.)
    - An unclosed `{`, `${` or `[if` is literal text.
    - `#` starts a comment only at the start of a line, and not when it is a hex
      colour such as #FFAA33.
    - A backslash escapes the next special character: \\{ \\} \\| \\_ \\$ \\[ \\] \\#
      (a backslash before anything else is ordinary text, so JSON escapes survive)

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .syntax_tree import (
    COUNT_ALL,
    BINDING_CONCEPT,
    BINDING_MARKERS,
    SAMPLER_DEFAULT,
    SAMPLER_MARKERS,
    Conditional,
    Node,
    Option,
    Provider,
    Sequence,
    Text,
    VariableAssign,
    VariableRef,
    Variant,
    Wildcard,
)

ESCAPABLE = "{}|_$[]#"

_HEX_COLOUR = re.compile(r"#[0-9A-Fa-f]{3,8}\b")
# N$$  N-M$$  -M$$ (lower bound defaults to 1)  N-$$ (upper bound defaults to "all options")
_COUNT_PREFIX = re.compile(r"\s*(?:(\d+)\s*(-)?\s*(\d+)?|(-)\s*(\d+))\s*\$\$")
_WEIGHT_PREFIX = re.compile(r"\s*(\d+(?:\.\d+)?)::")
_LEGACY_LABEL = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_ \-]{0,40}?)\s*:(?!:)")
_VARIABLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_MARKERS = re.compile(r"[=?~@]{0,2}")

# After the opening "__" and optional markers:
_PROVIDER = re.compile(r"(db|llm):([^\n]+?)__")
_WILDCARD = re.compile(
    r"([A-Za-z0-9*][A-Za-z0-9_\-/*. ]*?)?"   # name (optional when a tag query follows)
    r"(?:\(([^()\n]*)\))?"                   # (key=value, key=value)
    r"(?:\[([^\[\]\n]+)\])?"                 # [tag expression]
    r"__"
)
_CONDITIONAL_OPEN = re.compile(r"\[if\s+", re.IGNORECASE)
_JSON_OBJECT_OPEN = re.compile(r'\{\s*"[^"\n]*"\s*:')
# Placeholders the enhancer nodes insert to protect (keyword:1.5) emphasis from the LLM.
_RESERVED_NAME = re.compile(r"EMPHASIS_\d+$")


class _Backtrack(Exception):
    """Raised when a construct turns out to be unclosed; the caller emits it as literal text."""


def strip_comment_lines(text: str) -> str:
    """Remove `# comment` lines. A line starting with a hex colour is kept."""
    kept: List[str] = []
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("#") and not _HEX_COLOUR.match(stripped):
            continue
        kept.append(line)
    return "\n".join(kept)


def _split_markers(markers: str) -> Tuple[str, str]:
    binding = BINDING_CONCEPT
    sampler = SAMPLER_DEFAULT
    for marker in markers:
        if marker in BINDING_MARKERS:
            binding = BINDING_MARKERS[marker]
        elif marker in SAMPLER_MARKERS:
            sampler = SAMPLER_MARKERS[marker]
    return binding, sampler


def _parse_params(raw: Optional[str]) -> Dict[str, str]:
    params: Dict[str, str] = {}
    if not raw:
        return params
    for pair in raw.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            if key.strip():
                params[key.strip()] = value.strip()
    return params


class Parser:
    def __init__(self, text: str, legacy: bool = False):
        self.text = text
        self.length = len(text)
        self.position = 0
        self.legacy = legacy

    # -- public -----------------------------------------------------------------
    def parse(self) -> Sequence:
        sequence = self._parse_sequence(stops=())
        sequence.source = self.text
        return sequence

    # -- sequence ---------------------------------------------------------------
    def _parse_sequence(self, stops: Tuple[str, ...]) -> Sequence:
        parts: List[Node] = []
        buffer: List[str] = []

        def flush() -> None:
            if buffer:
                literal = "".join(buffer)
                parts.append(Text(source=literal, text=literal))
                buffer.clear()

        while self.position < self.length:
            char = self.text[self.position]

            if char == "\\" and self.position + 1 < self.length and self.text[self.position + 1] in ESCAPABLE:
                buffer.append(self.text[self.position + 1])
                self.position += 2
                continue

            if stops and any(self.text.startswith(stop, self.position) for stop in stops):
                break

            node = self._try_construct(char)
            if node is not None:
                flush()
                parts.append(node)
                continue

            buffer.append(char)
            self.position += 1

        flush()
        return Sequence(parts=parts)

    def _try_construct(self, char: str) -> Optional[Node]:
        """Try to parse a construct at the current position. On failure restore position, return None."""
        start = self.position
        try:
            if char == "$" and self.text.startswith("${", start):
                return self._parse_variable()
            if char == "{":
                if _JSON_OBJECT_OPEN.match(self.text, start):
                    return self._parse_json_object()
                return self._parse_variant()
            if char == "_" and self.text.startswith("__", start):
                return self._parse_wildcard()
            if char == "[" and _CONDITIONAL_OPEN.match(self.text, start):
                return self._parse_conditional()
        except _Backtrack:
            pass
        self.position = start
        return None

    # -- {"json": "object"} -----------------------------------------------------
    def _parse_json_object(self) -> Node:
        """
        A JSON object (Ideogram 4, FLUX.2 structured prompts) is not a variant: `|` inside it
        is ordinary text and the braces are kept. Constructs inside it still resolve, so
        {"subject": "a __animal__ made of {glass|brass}"} works.
        """
        start = self.position
        self.position += 1  # {
        inner = self._parse_sequence(stops=("}",))
        self._expect_close("}")
        parts: List[Node] = [Text(source="{", text="{")] + inner.parts + [Text(source="}", text="}")]
        return Sequence(source=self.text[start:self.position], parts=parts)

    # -- {variant} --------------------------------------------------------------
    def _parse_variant(self) -> Node:
        start = self.position
        self.position += 1  # {

        markers = _MARKERS.match(self.text, self.position).group(0)
        # A marker only counts if something other than '}' or '|' follows it, so "{=}" stays literal.
        binding, sampler = _split_markers(markers)
        self.position += len(markers)

        count_min, count_max, has_count, separator = 1, 1, False, ", "
        count_match = _COUNT_PREFIX.match(self.text, self.position)
        if count_match:
            has_count = True
            low, dash, high, open_low, only_high = count_match.groups()
            if open_low:                       # {-3$$...}  -> 1..3
                count_min, count_max = 1, int(only_high)
            elif dash and high is None:        # {2-$$...}  -> 2..all
                count_min, count_max = int(low), COUNT_ALL
            elif dash:                         # {1-3$$...}
                count_min, count_max = int(low), int(high)
            else:                              # {2$$...}
                count_min = count_max = int(low)
            if count_max != COUNT_ALL and count_max < count_min:
                count_min, count_max = count_max, count_min
            self.position = count_match.end()
            separator_end = self.text.find("$$", self.position)
            if separator_end != -1:
                candidate = self.text[self.position:separator_end]
                if not any(special in candidate for special in "{}|\n"):
                    separator = candidate
                    self.position = separator_end + 2

        label: Optional[str] = None
        if self.legacy and not has_count:
            label_match = _LEGACY_LABEL.match(self.text, self.position)
            if label_match:
                label = label_match.group(1).strip()
                self.position = label_match.end()

        options: List[Option] = []
        while True:
            weight = 1.0
            weight_match = _WEIGHT_PREFIX.match(self.text, self.position)
            if weight_match:
                weight = float(weight_match.group(1))
                self.position = weight_match.end()

            option_start = self.position
            body = self._parse_sequence(stops=("|", "}"))
            body.source = self.text[option_start:self.position].strip()
            options.append(Option(body=body, weight=weight))

            if self.position >= self.length:
                raise _Backtrack()
            if self.text[self.position] == "|":
                self.position += 1
                continue
            self.position += 1  # }
            break

        source = self.text[start:self.position]

        # Tidy option whitespace: "{ a | b }" means "a" or "b".
        for option in options:
            _strip_sequence(option.body)

        return Variant(
            source=source,
            options=options,
            count_min=count_min,
            count_max=count_max,
            has_count=has_count,
            separator=separator,
            sampler=sampler,
            binding=binding,
            label=label,
        )

    # -- __wildcard__ -----------------------------------------------------------
    def _parse_wildcard(self) -> Node:
        start = self.position
        cursor = start + 2

        markers = _MARKERS.match(self.text, cursor).group(0)
        binding, sampler = _split_markers(markers)
        cursor += len(markers)

        provider_match = _PROVIDER.match(self.text, cursor)
        if provider_match:
            self.position = provider_match.end()
            return Provider(
                source=self.text[start:self.position],
                kind=provider_match.group(1),
                argument=provider_match.group(2).strip(),
                binding=binding,
            )

        match = _WILDCARD.match(self.text, cursor)
        if not match:
            raise _Backtrack()
        name = (match.group(1) or "").strip()
        tag_expression = match.group(3)
        if not name and not tag_expression:
            raise _Backtrack()
        if _RESERVED_NAME.match(name):
            raise _Backtrack()

        self.position = match.end()
        return Wildcard(
            source=self.text[start:self.position],
            name=name,
            params=_parse_params(match.group(2)),
            tag_expression=tag_expression.strip() if tag_expression else None,
            sampler=sampler,
            binding=binding,
        )

    # -- ${variable} ------------------------------------------------------------
    def _parse_variable(self) -> Node:
        start = self.position
        self.position += 2  # ${
        name_match = _VARIABLE_NAME.match(self.text, self.position)
        if not name_match:
            raise _Backtrack()
        name = name_match.group(0)
        self.position = name_match.end()

        if self.position >= self.length:
            raise _Backtrack()
        char = self.text[self.position]

        if char == "}":
            self.position += 1
            return VariableRef(source=self.text[start:self.position], name=name)

        if char == ":":
            self.position += 1
            default = self._parse_sequence(stops=("}",))
            self._expect_close("}")
            return VariableRef(source=self.text[start:self.position], name=name, default=default)

        if char == "=":
            self.position += 1
            immediate = self.text.startswith("!", self.position)
            if immediate:
                self.position += 1
            value = self._parse_sequence(stops=("}",))
            self._expect_close("}")
            _strip_sequence(value)
            return VariableAssign(source=self.text[start:self.position], name=name, value=value, immediate=immediate)

        raise _Backtrack()

    # -- [if ...] ---------------------------------------------------------------
    def _parse_conditional(self) -> Node:
        start = self.position
        open_match = _CONDITIONAL_OPEN.match(self.text, self.position)
        self.position = open_match.end()

        colon = self.text.find(":", self.position)
        close = self.text.find("]", self.position)
        if colon == -1 or close == -1 or colon > close:
            raise _Backtrack()
        condition = self.text[self.position:colon].strip()
        if not condition:
            raise _Backtrack()
        self.position = colon + 1

        then_branch = self._parse_sequence(stops=("|", "]"))
        else_branch: Optional[Sequence] = None
        if self.position < self.length and self.text[self.position] == "|":
            self.position += 1
            else_branch = self._parse_sequence(stops=("]",))
        self._expect_close("]")

        _strip_sequence(then_branch)
        if else_branch is not None:
            _strip_sequence(else_branch)
        return Conditional(
            source=self.text[start:self.position],
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _expect_close(self, closer: str) -> None:
        if self.position >= self.length or self.text[self.position] != closer:
            raise _Backtrack()
        self.position += 1


def _strip_sequence(sequence: Sequence) -> None:
    """Trim leading whitespace of the first Text part and trailing whitespace of the last."""
    if not sequence.parts:
        return
    first = sequence.parts[0]
    if isinstance(first, Text):
        first.text = first.text.lstrip()
    last = sequence.parts[-1]
    if isinstance(last, Text):
        last.text = last.text.rstrip()
    sequence.parts = [part for part in sequence.parts if not (isinstance(part, Text) and part.text == "")]


def parse(text: str, legacy: bool = False) -> Sequence:
    """Parse prompt text into a syntax tree. Never raises on malformed input: bad constructs stay literal."""
    return Parser(strip_comment_lines(text), legacy=legacy).parse()
