"""
The CRITIC half of the surreal engine: judge the generator's candidates against explicit criteria, keep one,
and say it as plain physical fact. Most generated material is thrown away; that is the method, not a waste.

Two critics share the same checks:
  code critic   seeded, offline, instant. Filters out cliches and picks by score. Cannot bind THE SUBJECT to the
                idea's actual subject or carry out a procedure; it leaves both to the LLM that writes the prompt.
  LLM critic    one call. Names the subject, lists its ordinary attributes, rejects candidates whose affinity
                cannot be said in one short clause, carries out procedure modes, and writes the premise, a
                restatement, a Magritte-style title and counter-terms. This module only builds the messages and
                parses the answer; the caller owns the LLM.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from .generators import SECOND_OPERATIONS, Candidate
from .vocabulary import BAN_LIST, BAN_LIST_FOR_PROMPT, CHARGES, OPERATIONS, SUBJECT_TOKEN

EXPLAINING = re.compile(r"\b(symboli[sz]\w*|represent\w*|metaphor\w*|signif\w*|allegor\w*|evok\w*|as if in a dream|meaning of)\b", re.I)
MAX_PREMISE_WORDS = 70
MAX_AFFINITY_WORDS = 22


def violations(text: str, is_procedure: bool = False) -> List[str]:
    """Why a premise is not acceptable. Empty list = acceptable. A procedure is instructions, so it may be long."""
    problems: List[str] = []
    lowered = (text or "").lower()
    banned = [term for term in BAN_LIST if re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", lowered)]
    if banned:
        problems.append("ban-list: " + ", ".join(sorted(set(banned))))
    if EXPLAINING.search(text or ""):
        problems.append("explains itself (" + EXPLAINING.search(text).group(0) + "); the image must pose the question and refuse the answer")
    if not is_procedure and len(re.findall(r"\S+", text or "")) > MAX_PREMISE_WORDS:
        problems.append(f"longer than {MAX_PREMISE_WORDS} words; a premise is one or two plain sentences")
    return problems


def code_choose(candidates: Sequence[Candidate], rng: random.Random, count: int = 1) -> Tuple[List[Candidate], List[str]]:
    """Seeded choice by score among acceptable candidates. For count 2 the second is an atmosphere-level operation."""
    notes: List[str] = []
    acceptable = []
    for candidate in candidates:
        found = violations(candidate.premise or candidate.procedure, is_procedure=not candidate.premise)
        if found:
            notes.append(f"rejected ({'; '.join(found)}): {candidate.line()[:90]}")
        else:
            acceptable.append(candidate)
    if not acceptable:
        return [], notes
    ranked = sorted(acceptable, key=lambda candidate: -candidate.score)[:6]
    first = rng.choices(ranked, weights=[candidate.score ** 2 for candidate in ranked], k=1)[0]
    chosen = [first]
    if count >= 2:
        seconds = [candidate for candidate in acceptable if candidate.operation in SECOND_OPERATIONS
                   and candidate.operation != first.operation and candidate.premise]
        if seconds and OPERATIONS[first.operation].impossible:
            chosen.append(rng.choice(seconds))
        else:
            notes.append("count 2 asked for, one operation used: no second operation can read as the same event here")
    return chosen, notes


# ---- LLM critic ---------------------------------------------------------------------------------------
CRITIC_SYSTEM = f"""You are the critic half of a surrealist working method. A generator has produced candidate premises by procedure and by chance. Your job is the one Magritte, Ernst and Uelsmann did after the accident: read, select ONE, and finish it with full craft. Most candidates are to be thrown away.

What makes a premise work:
- ONE impossibility held against an otherwise completely credible, ordinary world. (Two only when asked, and only if they read as one event.)
- Affinity beats distance. The best premise joins two things that are far apart and yet secretly bound - by shape, function, material, life stage, container and contained, or a word - as the egg is bound to the birdcage. If the bond cannot be said in one short clause, reject the candidate.
- It acts on the actual subject of the user's idea, never on something the idea does not contain, and never replaces the idea.
- It is stated as plain physical fact, present tense, the way a police report would state it. No adjectives of strangeness.
- It poses a question and refuses the answer: no explanation, no symbolism, no moral.
- It has a stake: it serves the emotional charge you are given. An anomaly with no stake reads as a gimmick.
- Never: {BAN_LIST_FOR_PROMPT}.
- Candidates marked "nothing impossible" are a full mode (Atget, Crewdson, Man Ray): do not add an impossibility to them.

Steps:
1. Name the main subject of the idea in a few words, and list its ordinary attributes: material, scale, habitat, function, what it always comes with.
2. For each candidate decide keep or reject, with a reason of a few words. A candidate that is a PROCEDURE is carried out by you, here, and then judged like the others.
3. Choose the best. Replace "{SUBJECT_TOKEN}" with the real subject. You may sharpen a candidate (a better partner with a truer affinity, a more exact placement) but not change its operation.
4. Write the premise, a restatement of the same fact in different words, a title in Magritte's manner (it names a problem and never describes the picture), and up to five short "normal" counter-terms that an image model would drift back to (for a fur teacup: porcelain teacup, ceramic cup).

Answer with JSON only, no other text:
{{"subject": "...", "attributes": ["...", "..."], "judgements": [{{"n": 1, "keep": false, "reason": "..."}}], "chosen": 2, "operation": "...", "affinity": "one short clause", "premise": "one or two plain sentences", "restatement": "the same fact in other words", "title": "...", "counter_terms": ["...", "..."]}}"""


@dataclass
class Verdict:
    subject: str = ""
    chosen_index: int = -1              # index into the candidate list, -1 = the critic wrote its own
    operation: str = ""
    affinity: str = ""
    premise: str = ""
    restatement: str = ""
    title: str = ""
    counter_terms: List[str] = field(default_factory=list)
    judgements: List[str] = field(default_factory=list)


def critic_messages(idea: str, candidates: Sequence[Candidate], count: int, charge: str, strangeness: str, medium: str) -> Tuple[str, str]:
    lines = []
    for number, candidate in enumerate(candidates, 1):
        kind = "PROCEDURE" if candidate.procedure and not candidate.premise else "premise"
        impossible = "" if OPERATIONS[candidate.operation].impossible else "  (nothing impossible)"
        bond = f"\n   affinity found by the generator: {candidate.affinity}" if candidate.affinity else ""
        personal = "\n   uses the user's own iconography: prefer it when it is as good as the others" if candidate.personal else ""
        lines.append(f"{number}. [{candidate.operation}{impossible}] {kind}: {candidate.premise or candidate.procedure}{bond}{personal}")
    charge_text = CHARGES.get(charge, "")
    user = (
        f"IDEA\n{idea.strip()}\n\nCANDIDATES\n" + "\n".join(lines) + "\n\n"
        f"OPERATIONS WANTED: {count}" + (" (the second must be atmosphere-level - light, shadow, time, absence - so that both read as one event)" if count >= 2 else "") + "\n"
        f"STRANGENESS: {strangeness} (subtle = a viewer may need a second look; overt = unmistakable at a glance)\n"
        f"MEDIUM: {medium}" + (" - an anomaly in TIME is available: reversed, slowed, looped, or sound that belongs to something else" if medium == "video" else "") + "\n"
        + (f"CHARGE: {charge_text}\n" if charge_text else "")
    )
    return CRITIC_SYSTEM, user


def _first_json_object(text: str) -> Optional[dict]:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S | re.I)
    text = re.sub(r"^.*?</think>", "", text, flags=re.S | re.I)
    start = text.find("{")
    while start != -1:
        depth, in_string, escaped = 0, False, False
        for position in range(start, len(text)):
            character = text[position]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
            elif character == '"':
                in_string = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    try:
                        parsed = json.loads(text[start:position + 1])
                        if isinstance(parsed, dict):
                            return parsed
                    except Exception:
                        pass
                    break
        start = text.find("{", start + 1)
    return None


def _too_different(first: str, second: str) -> bool:
    """True when two premises share few content words (the critic rewrote rather than kept)."""
    def words(text: str):
        return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in ("with", "that", "this", "there", "where", "everything", "same", "instead")}
    a, b = words(first), words(second)
    return bool(a and b) and len(a & b) < 0.25 * min(len(a), len(b))


def parse_critic(answer: str, candidates: Sequence[Candidate]) -> Tuple[Optional[Verdict], List[str]]:
    """(verdict, problems). verdict is None when the answer cannot be used; the caller then falls back to the code critic."""
    data = _first_json_object(answer)
    if data is None:
        return None, ["the critic's answer was not JSON"]
    premise = str(data.get("premise") or "").strip()
    if not premise:
        return None, ["the critic returned no premise"]
    problems = violations(premise)
    if SUBJECT_TOKEN in premise:
        problems.append(f"left {SUBJECT_TOKEN} unresolved")
    affinity = str(data.get("affinity") or "").strip()
    if affinity.lower().strip(". ") in ("one short clause", "a short clause", "affinity", "n/a", "none"):
        affinity = ""          # the model echoed the placeholder
    if len(affinity.split()) > MAX_AFFINITY_WORDS:
        problems.append("the affinity does not fit in one short clause")
    if problems:
        return None, problems
    try:
        chosen = int(data.get("chosen", 0)) - 1
    except (TypeError, ValueError):
        chosen = -1
    if not 0 <= chosen < len(candidates):
        chosen = -1
    operation = str(data.get("operation") or "").strip().lower().replace(" ", "_")
    if operation not in OPERATIONS:
        operation = candidates[chosen].operation if chosen >= 0 else "displacement"
    # A critic that wrote its own premise sometimes keeps a candidate's number: trust the words over the number.
    if chosen >= 0 and candidates[chosen].premise and _too_different(premise, candidates[chosen].premise):
        chosen = -1
    judgements = []
    for entry in data.get("judgements") or []:
        if isinstance(entry, dict):
            judgements.append(f"{entry.get('n', '?')}: {'keep' if entry.get('keep') else 'reject'} - {str(entry.get('reason', '')).strip()}")
    restatement = str(data.get("restatement") or "").strip()
    if violations(restatement):
        restatement = ""
    counter_terms = [str(term).strip() for term in (data.get("counter_terms") or []) if str(term).strip()][:5]
    return Verdict(subject=str(data.get("subject") or "").strip(), chosen_index=chosen, operation=operation, affinity=affinity,
                   premise=premise, restatement=restatement, title=str(data.get("title") or "").strip().strip('"'),
                   counter_terms=counter_terms, judgements=judgements), []
