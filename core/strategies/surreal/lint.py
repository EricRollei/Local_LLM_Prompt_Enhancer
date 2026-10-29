"""
The renderability linter: grammar a text-to-image model cannot draw.

An image model's text encoder keeps nouns and attributes and loses roles, counterfactuals and negation. So a
sentence that describes a SUBSTITUTION ("where the teacup should be there are boots instead") hands the encoder
both objects, and the picture comes back with the teacup. A sentence that claims an ATTITUDE ("nobody notices",
"unnoticed by those around him") has no pixels at all; it only spends tokens. The live run of 2026-09-21 shows
both: a teacup premise rendered with an extra coffee mug and a "ghostly" teacup, a stone premise rendered as a
man holding a stone with "completely unnoticed by those around him" appended.

Two uses:
  lint_render(text)               problems with a premise as the image model would read it (critic and generators)
  lint_prompt(prompt, suppress)   the finished platform prompt: attention claims are removed, the rest is reported

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import re
from typing import List, Sequence, Tuple

# A substitution or a pretence described instead of shown. "instead" alone is NOT here: "casts its shadow toward
# the light instead of away from it" names a direction, not an object, and renders well enough.
SUBSTITUTION = re.compile(
    r"\b(?:should\s+(?:be|stand|sit|rest|lie)"
    r"|would\s+(?:normally\s+|usually\s+|ordinarily\s+)?(?:be|stand|sit|rest|lie)"
    r"|in\s+place\s+of"
    r"|instead\s+of\s+(?:the|a|an|his|her|its|their)\b"
    r"|there\s+(?:is|are)\b[^.;]{0,80}?\binstead\b"
    r"|as\s+if|as\s+though"
    r"|treats?\s+(?:it|them|this|these)\s+as"
    r"|takes?\s+(?:it|them)\s+for"
    r"|mistaken\s+for)\b",
    re.I,
)

# In a FINISHED prompt, 'as if' / 'as though' is usually atmosphere ("as if time has paused"), not a pretence about
# an object, so the prompt-level check uses this narrower pattern; premises are held to the strict one above.
SUBSTITUTION_IN_PROMPT = re.compile(
    r"\b(?:should\s+(?:be|stand|sit|rest|lie)"
    r"|in\s+place\s+of"
    r"|instead\s+of\s+(?:the|a|an|his|her|its|their)\b"
    r"|there\s+(?:is|are)\b[^.;]{0,80}?\binstead\b"
    r"|treats?\s+(?:it|them|this|these)\s+as)\b",
    re.I,
)

# An attitude of the people in the picture toward the anomaly. Unrenderable, and the rewriter transcribes it
# (live 2026-10-01: "The woman remains unaware of the unusual sight beside her", "The man remains unfazed").
ATTENTION = re.compile(
    r"(?:\b(?:nobody|no\s+one|no-one|none\s+of\s+them|no\s+passer-?by|no\s+person)\b[^.,;]{0,40}?"
    r"\b(?:notices?|noticing|pays?|paying|reacts?|reacting|acknowledges?|remarks?|looks?\s+at|seems?\s+to\s+(?:notice|mind|care))\b)"
    r"|\bunnoticed\b|\bunremarked\b|\bwithout\s+anyone\s+(?:noticing|reacting)\b"
    r"|\b(?:it|the\s+\w+)\s+(?:goes|go)\s+unnoticed\b"
    r"|\b(?:remains?|is|are|seems?|appears?|stays?)\s+(?:completely\s+|entirely\s+|quite\s+)?"
    r"(?:unaware|unfazed|oblivious|indifferent|unbothered|unperturbed|unconcerned)\b",
    re.I,
)

_CLAUSE_SPLIT = re.compile(r"(?<=[,;])\s+|(?<=[.!?])\s+")


def lint_render(text: str) -> List[str]:
    """Why this text, read by an image model, would not render its anomaly. Empty list = fine."""
    problems: List[str] = []
    found = SUBSTITUTION.search(text or "")
    if found:
        problems.append(f"describes a substitution or a pretence ('{found.group(0)}') instead of the result; the image model "
                        "draws both objects, or the original one")
    found = ATTENTION.search(text or "")
    if found:
        problems.append(f"claims an attitude ('{found.group(0)}') that has no pixels; show people doing ordinary things instead")
    return problems


def named_terms(prompt: str, suppress: Sequence[str]) -> List[str]:
    """Which of the things that must NOT appear are named in the prompt (whole-word, case-insensitive)."""
    lowered = (prompt or "").lower()
    found = []
    for term in suppress:
        term = (term or "").strip().lower()
        if term and re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", lowered):
            found.append(term)
    return found


def lint_prompt(prompt: str, suppress: Sequence[str] = ()) -> Tuple[str, List[str]]:
    """(prompt, warnings). Attention claims are removed clause by clause (safe: they carry no picture). Substitution
    grammar and suppressed names are only reported, because removing them could remove the anomaly with them."""
    warnings: List[str] = []
    if not (prompt or "").strip():
        return prompt, warnings
    pieces = _CLAUSE_SPLIT.split(prompt)
    kept, dropped = [], []
    for piece in pieces:
        if ATTENTION.search(piece):
            dropped.append(piece.strip())
            continue
        kept.append(piece)
    cleaned = prompt
    if dropped and kept:
        cleaned = " ".join(kept)
        cleaned = re.sub(r"\s*,\s*([.!?])", r"\1", cleaned)
        cleaned = re.sub(r"[,;]\s*$", ".", cleaned.strip())
        warnings.append("surreal: removed clause(s) claiming nobody notices (no pixels in that): "
                        + " / ".join(text[:60] for text in dropped[:3]))
    found = SUBSTITUTION_IN_PROMPT.search(cleaned)
    if found:
        warnings.append(f"surreal: the prompt describes a substitution ('{found.group(0)}'); the image model may draw the "
                        "original object too. Re-run, or use the two-stage outputs.")
    named = named_terms(cleaned, suppress)
    if named:
        warnings.append("surreal: the prompt names what the anomaly replaced (" + ", ".join(named) + "); the image model will "
                        "probably draw it. Re-run, or use the two-stage outputs.")
    return cleaned, warnings


SUPPRESS_MARKER = "Not in the picture - never name it, in any wording:"


def suppress_from_instructions(instructions: str) -> List[str]:
    """Read the suppress list back out of an instruction block (the rewriter receives only the block)."""
    for line in (instructions or "").splitlines():
        if SUPPRESS_MARKER in line:
            tail = line.split(SUPPRESS_MARKER, 1)[1]
            return [term.strip() for term in tail.split(";") if term.strip()]
    return []
