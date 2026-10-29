"""
Token budget for platform prompts.

A text encoder silently drops whatever runs past its limit (Krea 2: 512 tokens incl. a 5-token
template suffix), and LoRA trigger words are usually appended AFTER the rewrite - so a long
answer loses exactly the words that matter most. This module counts tokens as the target
encoder will, decides the budget the rewriter should aim for, and trims an answer to fit at a
sentence / clause boundary while keeping protected terms (verbatim picks, triggers).

Counting:
  * profiles whose encoder is a Qwen model (Krea 2, Qwen-Image, Z-Image, ...) use a Qwen
    tokenizer that is ALREADY on disk - config.json "token_budget": {"tokenizer": path}, else the
    Hugging Face cache (local_files_only, never a download). Qwen2.5 / Qwen3 share one vocabulary.
  * anything else, or no tokenizer found: a conservative estimate (over-counts slightly, so a
    trim errs toward keeping the prompt inside the limit).

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

from __future__ import annotations

import json
import math
import os
import re
from typing import Callable, List, Optional, Sequence, Tuple

_PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CACHED_QWEN_REPOS = (
    "Qwen/Qwen3-VL-4B-Instruct", "Qwen/Qwen3-VL-8B-Instruct", "Qwen/Qwen3-VL-2B-Instruct",
    "Qwen/Qwen2.5-VL-7B-Instruct", "qwen/Qwen2.5-VL-7B-Instruct",
)
_STATE = {"qwen": None, "source": ""}     # None = not tried yet, False = unavailable

# Headroom kept free under the encoder limit: template tokens (Krea 2's suffix is 5) plus room for
# LoRA trigger words merged after the rewrite. 8% of the limit, at least 8 tokens.
RESERVE_FRACTION = 0.08
RESERVE_MIN = 8


def _config_tokenizer_path() -> str:
    try:
        with open(os.path.join(_PACKAGE_DIR, "config.json"), "r", encoding="utf-8") as handle:
            section = (json.load(handle) or {}).get("token_budget") or {}
        return str(section.get("tokenizer") or "")
    except Exception:
        return ""


def _qwen_tokenizer():
    if _STATE["qwen"] is not None:
        return _STATE["qwen"] or None
    try:
        from transformers import AutoTokenizer
    except Exception:
        _STATE["qwen"] = False
        return None
    candidates = []
    configured = _config_tokenizer_path()
    if configured:
        candidates.append((configured, False))
    candidates += [(repo, True) for repo in _CACHED_QWEN_REPOS]
    for source, cache_only in candidates:
        try:
            tok = AutoTokenizer.from_pretrained(source, local_files_only=cache_only) if cache_only \
                else AutoTokenizer.from_pretrained(source)
            _STATE["qwen"], _STATE["source"] = tok, source
            return tok
        except Exception:
            continue
    _STATE["qwen"] = False
    return None


def uses_qwen(profile) -> bool:
    return "qwen" in (getattr(profile, "encoder", "") or "").lower()


def estimate_tokens(text: str) -> int:
    """Conservative: the larger of 1.35 tokens per word and 1 token per 3.5 characters."""
    words = len(re.findall(r"\S+", text or ""))
    return int(math.ceil(max(words * 1.35, len(text or "") / 3.5)))


def counter_for(profile) -> Tuple[Callable[[str], int], str]:
    """(count_fn, label). label says how the count was made, for the report."""
    if uses_qwen(profile):
        tok = _qwen_tokenizer()
        if tok is not None:
            return (lambda text: len(tok(text or "", add_special_tokens=False).input_ids),
                    f"Qwen tokenizer ({os.path.basename(_STATE['source'].rstrip('/\\')) or _STATE['source']})")
    return estimate_tokens, "estimate"


def budget_for(profile) -> Tuple[int, int]:
    """(limit, target). target = limit minus headroom for template tokens and LoRA triggers.
    (0, 0) when the profile documents no limit."""
    limit = int(getattr(profile, "max_tokens", 0) or 0)
    if limit <= 0:
        return 0, 0
    reserve = max(RESERVE_MIN, int(round(limit * RESERVE_FRACTION)))
    return limit, max(16, limit - reserve)


def _join(body: str, extra: Sequence[str]) -> str:
    body = body.rstrip()
    if not extra:
        return body
    tail = ", ".join(extra)
    if not body:
        return tail
    body = body.rstrip(',;:').rstrip()
    return f"{body} {tail}" if body[-1:] in '.!?' else f"{body}, {tail}"


def fit_to_budget(text: str, budget: int, count: Callable[[str], int],
                  protect: Sequence[str] = ()) -> Tuple[str, int, List[str]]:
    """Trim `text` so count(result) <= budget, cutting the END of the body at the last sentence
    end (else clause end, else word) that fits. Every term in `protect` that the trim removed is
    re-appended. Returns (text, tokens, dropped_preview). Text already inside the budget comes
    back unchanged."""
    n = count(text)
    if budget <= 0 or n <= budget:
        return text, n, []
    protect = [p for p in (protect or []) if p and p.strip()]

    # 1) Prefer dropping whole sentences from just BEFORE the last one: prose prompts lead with the
    #    subject and end with medium / style / framing (Krea 2's own structure), so both ends matter.
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    if len(sentences) >= 3:
        keep = list(sentences)
        removed = []
        while len(keep) >= 3:
            removed.insert(0, keep.pop(-2))
            body = " ".join(keep)
            low = body.lower()
            candidate = _join(body, [p for p in protect if p.lower() not in low])
            m = count(candidate)
            if m <= budget:
                gone = " ".join(removed)
                return candidate, m, [gone[:80] + ("..." if len(gone) > 80 else "")]

    # 2) Fall back to cutting the end at the last sentence / clause / word that fits.
    words = list(re.finditer(r"\S+", text))
    if not words:
        return text, n, []

    def build(k):          # first k words + any protected terms they lost
        body = text[:words[k - 1].end()] if k > 0 else ""
        low = body.lower()
        lost = [p for p in protect if p.lower() not in low]
        return _join(body, lost)

    lo, hi = 0, len(words)                      # largest k with count(build(k)) <= budget
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if count(build(mid)) <= budget:
            lo = mid
        else:
            hi = mid - 1
    k = lo
    if k <= 0:
        out = build(0)
        return out, count(out), [text[:80]]
    end = words[k - 1].end()
    head = text[:end]
    cut = end
    for pattern in (r"[.!?](?=\s|$)", r"[,;:](?=\s|$)"):
        hits = [m.end() for m in re.finditer(pattern, head)]
        if hits and hits[-1] >= end * 0.6:
            cut = hits[-1]
            break
    body = text[:cut].rstrip()
    if body and body[-1] in ",;:":
        body = body[:-1].rstrip() + "."
    low = body.lower()
    out = _join(body, [p for p in protect if p.lower() not in low])
    dropped = text[cut:].strip()
    return out, count(out), [dropped[:80] + ("..." if len(dropped) > 80 else "")] if dropped else []
