"""
Boolean expressions over terms: `metal AND (small OR handheld) AND NOT modern`.

Used twice:
  - tag queries      __[metal AND NOT large]__     term -> "is this tag on the entry?"
  - conditionals     [if night AND NOT rain : a|b]  term -> "is this true in the run so far?"

Operators are UPPERCASE only (AND, OR, NOT, XOR) so that tags and values may
contain the ordinary words "and", "or", "not". Terms may be several words long
("dark wood"). Precedence: NOT > AND > XOR > OR. Parentheses group.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import re
from typing import Callable, List, Tuple, Union

_TOKEN_PATTERN = re.compile(r"\(|\)|\bAND\b|\bOR\b|\bNOT\b|\bXOR\b")

# Compiled form: nested tuples, e.g. ("and", ("term", "metal"), ("not", ("term", "large")))
Compiled = Union[Tuple[str, str], Tuple[str, "Compiled"], Tuple[str, "Compiled", "Compiled"]]


class BooleanExpressionError(ValueError):
    pass


def _tokenize(expression: str) -> List[str]:
    tokens: List[str] = []
    position = 0
    for match in _TOKEN_PATTERN.finditer(expression):
        term = expression[position:match.start()].strip()
        if term:
            tokens.append("TERM:" + term)
        tokens.append(match.group(0))
        position = match.end()
    tail = expression[position:].strip()
    if tail:
        tokens.append("TERM:" + tail)
    return tokens


class _Parser:
    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.index = 0

    def _peek(self) -> str:
        return self.tokens[self.index] if self.index < len(self.tokens) else ""

    def _take(self) -> str:
        token = self._peek()
        self.index += 1
        return token

    def parse(self) -> Compiled:
        if not self.tokens:
            raise BooleanExpressionError("empty expression")
        compiled = self._parse_or()
        if self.index < len(self.tokens):
            raise BooleanExpressionError(f"unexpected '{self._peek()}'")
        return compiled

    def _parse_or(self) -> Compiled:
        left = self._parse_xor()
        while self._peek() == "OR":
            self._take()
            left = ("or", left, self._parse_xor())
        return left

    def _parse_xor(self) -> Compiled:
        left = self._parse_and()
        while self._peek() == "XOR":
            self._take()
            left = ("xor", left, self._parse_and())
        return left

    def _parse_and(self) -> Compiled:
        left = self._parse_not()
        while self._peek() == "AND":
            self._take()
            left = ("and", left, self._parse_not())
        return left

    def _parse_not(self) -> Compiled:
        if self._peek() == "NOT":
            self._take()
            return ("not", self._parse_not())
        return self._parse_atom()

    def _parse_atom(self) -> Compiled:
        token = self._take()
        if token == "(":
            inner = self._parse_or()
            if self._take() != ")":
                raise BooleanExpressionError("missing ')'")
            return inner
        if token.startswith("TERM:"):
            return ("term", token[5:])
        raise BooleanExpressionError(f"expected a term, got '{token or 'end of expression'}'")


def compile_expression(expression: str) -> Compiled:
    """Parse once; evaluate many times with evaluate()."""
    return _Parser(_tokenize(expression)).parse()


def evaluate(compiled: Compiled, term_is_true: Callable[[str], bool]) -> bool:
    kind = compiled[0]
    if kind == "term":
        return bool(term_is_true(compiled[1]))
    if kind == "not":
        return not evaluate(compiled[1], term_is_true)
    left = evaluate(compiled[1], term_is_true)
    if kind == "and":
        return left and evaluate(compiled[2], term_is_true)
    if kind == "or":
        return left or evaluate(compiled[2], term_is_true)
    if kind == "xor":
        return left != evaluate(compiled[2], term_is_true)
    raise BooleanExpressionError(f"unknown node '{kind}'")


def terms_of(compiled: Compiled) -> List[str]:
    """All terms mentioned, for diagnostics."""
    if compiled[0] == "term":
        return [compiled[1]]
    found: List[str] = []
    for child in compiled[1:]:
        found.extend(terms_of(child))
    return found
