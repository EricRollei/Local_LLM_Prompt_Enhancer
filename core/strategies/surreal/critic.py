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
from .lint import lint_render
from .vocabulary import (
    BAN_LIST, BAN_LIST_FOR_PROMPT, BANNED_TITLES, CHARGES, OPERATIONS, RUBRIC, SOFT_BAN_FOR_PROMPT, SUBJECT_TOKEN,
    TITLE_STRATEGIES,
)

EXPLAINING = re.compile(r"\b(symboli[sz]\w*|represent\w*|metaphor\w*|signif\w*|allegor\w*|evok\w*|as if in a dream|meaning of)\b", re.I)
# A text-to-image model cannot condition on absence. A premise whose anomaly is stated to be unseeable has
# nothing in it to render: "pulling strings from their hands, invisible to the viewer" produces two women in a
# garden. This is not about strangeness, it is about whether there are pixels to put it in.
# "no visible source" is deliberately NOT here: a pool of light whose lamp is out of frame is fully renderable.
UNRENDERABLE = re.compile(
    r"\b(invisible|unseen|imperceptible|undetectable|intangible|immaterial"
    r"|cann?o?t be seen|can'?t be seen|never be seen|impossible to see|not visible to"
    r"|as if never (?:there|been|happened)|leaves no (?:trace|mark|sign))\b", re.I)
MAX_PREMISE_WORDS = 70
MAX_AFFINITY_WORDS = 22
MAX_LAW_WORDS = 45


def violations(text: str, is_procedure: bool = False) -> List[str]:
    """Why a premise is not acceptable. Empty list = acceptable. A procedure is instructions, so it may be long."""
    problems: List[str] = []
    lowered = (text or "").lower()
    banned = [term for term in BAN_LIST if re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", lowered)]
    if banned:
        problems.append("ban-list: " + ", ".join(sorted(set(banned))))
    if EXPLAINING.search(text or ""):
        problems.append("explains itself (" + EXPLAINING.search(text).group(0) + "); the image must pose the question and refuse the answer")
    unrenderable = UNRENDERABLE.search(text or "")
    if unrenderable:
        problems.append(f"the anomaly is described as unseeable ('{unrenderable.group(0)}'); an image model has nothing to "
                        "render and the picture comes back ordinary")
    if not is_procedure and len(re.findall(r"\S+", text or "")) > MAX_PREMISE_WORDS:
        problems.append(f"longer than {MAX_PREMISE_WORDS} words; a premise is one or two plain sentences")
    return problems


def code_choose(candidates: Sequence[Candidate], rng: random.Random, count: int = 1) -> Tuple[List[Candidate], List[str]]:
    """Seeded choice by score among acceptable candidates. For count 2 the second is an atmosphere-level operation."""
    notes: List[str] = []
    acceptable = []
    for candidate in candidates:
        found = violations(candidate.premise or candidate.procedure, is_procedure=not candidate.premise)
        if candidate.premise:
            found += lint_render(candidate.rendered())     # what the image model will actually be given
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
            notes.append("the code critic cannot check that the second operation obeys the first one's law; the LLM critic can")
        else:
            notes.append("count 2 asked for, one operation used: no second operation can read as the same event here")
    return chosen, notes


# ---- LLM critic ---------------------------------------------------------------------------------------
_RUBRIC_LINES = "\n".join(f"- {name}: {text}" for name, text in RUBRIC.items())
_TITLE_LINES = "\n".join(f"- {name}: {text}" for name, text in TITLE_STRATEGIES.items())

CRITIC_SYSTEM = f"""You are the critic half of a surrealist working method. A generator has produced candidate premises by procedure and by chance. Your job is the one Magritte, Ernst and Uelsmann did after the accident: read, select ONE, and finish it with full craft. Most candidates are to be thrown away.

What makes a premise work:
- ONE impossibility held against an otherwise completely credible, ordinary world. (Two only when asked, and only if they read as one event.)
- Affinity beats distance. The best premise joins two things that are far apart and yet secretly bound - by shape, function, material, life stage, container and contained, or a word - as the egg is bound to the birdcage. If the bond cannot be said in one short clause, reject the candidate.
- It acts on the actual subject of the user's idea, never on something the idea does not contain, and never replaces the idea.
- It is stated as plain physical fact, present tense, the way a police report would state it. No adjectives of strangeness.
- It poses a question and refuses the answer: no explanation, no symbolism, no moral.
- It has a stake: it serves the emotional charge you are given. An anomaly with no stake reads as a gimmick.
- It can be PHOTOGRAPHED. This premise becomes a prompt for an image model, and an image model cannot render an absence, a negation, a thing stated to be invisible, or a claim about what caused something. It can only render what is present in the frame. So the anomaly must leave a positive mark that a viewer could point at. "Strings that are invisible to the viewer" is not a picture; a taut cord disappearing into a hedge is. "Nothing in the room acknowledges it" is not a picture; the untouched cup and the turned-away face are. Reject any candidate whose anomaly you cannot describe as something seen.
- It is written as the RESULT, never as the change. An image model's text encoder keeps the nouns and loses the grammar: "where the teacup should be there are boots instead" gives it a teacup AND boots, and it draws the teacup. Write only what the camera sees ("a pair of worn work boots stands on the saucer beside her book"), never name what was replaced or removed, never write should / would / instead of / in place of / as if / treats it as, and never say that nobody notices - show people doing ordinary things instead.
- It is unmistakable at a glance. Deadpan is not the same as subtle: the anomaly is large in the frame, central, sharply lit, and touches the ordinary world (a shadow, a reflection, weight, wear). A premise that is strange only to someone who knows the story - a man holding a smooth stone - renders as an ordinary photograph.
- It obeys a LAW. The rupture is not an exception to the world; it is evidence of a rule the world in this picture follows. A law says what may change, what may not, and how the change behaves - "only patterned fabric can cross the boundary between a body and a wall", "whatever the missing person touched has gained weight". A picture whose anomaly obeys no law reads as random; this is the single most common failure.
- Never: {BAN_LIST_FOR_PROMPT}.
- Use sparingly: {SOFT_BAN_FOR_PROMPT}.
- Candidates marked "nothing impossible" are a full mode (Atget, Crewdson, Man Ray): do not add an impossibility to them. Their law governs light, hour, emptiness and process instead.

Steps:
1. Name the main subject of the idea in a few words, and list its ordinary attributes: material, scale, habitat, function, what it always comes with.
2. For each candidate decide keep or reject, with a reason of a few words. A candidate that is a PROCEDURE is carried out by you, here, and then judged like the others.
3. Choose the best. Replace "{SUBJECT_TOKEN}" with the real subject. You may sharpen a candidate (a better partner with a truer affinity, a more exact placement) but not change its operation.
4. Write the LAW this picture obeys: one sentence, under {MAX_LAW_WORDS} words, stating what may change and what may not. You are given a suggested law; keep it only if it genuinely governs the premise you chose, and otherwise write your own. If two operations were asked for, the second must be an instance of the same law.
5. Write premise_draft: the premise as one or two plain sentences.
6. Score premise_draft on each rubric dimension from 0 to 4:
{_RUBRIC_LINES}
7. Name the LOWEST-scoring dimension as "weakest", say in a few words the one change that would raise it ("repair"), and then write "premise" as premise_draft with that one repair applied. Change nothing else. If nothing needs repair, repeat premise_draft unchanged and say so.
8. Write "visible": in one clause, what a viewer literally SEES in this picture that they would not see in an ordinary photograph of the same scene. Name a thing, a surface, an edge, a shadow or a light. If the only honest answer is that nothing looks different, go back to step 3 and choose a different candidate.
8b. Write "render": the premise as the image model must receive it - the RESULT only, one or two sentences, the anomaly first and large in the frame, with one line of physical evidence (its shadow, its weight, its texture up close). Never name what was replaced, removed or missing; never should / would / instead / in place of / as if; never that nobody notices. List in "suppress" the things the anomaly replaced or removed, which must not be named anywhere in the prompt (often none: []).
8c. Convert the decision into a structured render plan:
   - "target": the entity whose object, material, scale or behaviour changes.
   - "replacement": the new object, material or borrowed behaviour, or empty when there is none.
   - "preserve": the visible properties and unrelated scene facts that must survive.
   - "visual_evidence": two to four POSITIVE things visible in the finished image that prove the anomaly exists. Include contact, shadow, reflection, weight, texture, continuity, an exposed surface or a known-size reference as appropriate.
   - "forbidden_interpretations": the two most likely ordinary pictures an image model would retreat to.
   - "composition": anomaly_scale ("dominant"), placement, frame_share ("at least one third"), and scale_reference when useful.
   - "preserved_scene": the FINAL ordinary context after the transformation. Keep the subject, action, setting, light and viewpoint, but REMOVE every entity named in "suppress" and every ordinary property that the anomaly replaces. This is not the original scene and must not contradict "render".
8d. Write "scene": the same picture as an ORDINARY photograph, with no anomaly at all, in one or two sentences - the subject, the place, the light. And "edit": ONE imperative instruction for an image-editing model that turns that ordinary picture into this one ("Replace the teacup on the saucer with a pair of worn leather work boots at the same size, in the same light. Keep everything else unchanged."). If no single edit can do it (a law of light or time across the whole frame, nothing impossible, a double image), write "edit": "".
9. Write a restatement of the same fact in different words; choose a title strategy and write the title by it; and give up to five short counter-terms - the ordinary things an image model will drift back to INSTEAD of your anomaly, drawn from THIS premise and its subject, never from the examples in these instructions.

Title strategies - pick exactly one and name it:
{_TITLE_LINES}
A title never describes what is visible, and is never "Dream", "Untitled", "Reverie" or anything containing the word surreal.

Answer with JSON only, no other text, and in this key order:
{{"subject": "...", "attributes": ["...", "..."], "judgements": [{{"n": 1, "keep": false, "reason": "..."}}], "chosen": 2, "operation": "...", "affinity": "one short clause", "law": "one sentence: what may change, what may not", "premise_draft": "one or two plain sentences", "scores": {{"reality_anchor": 0, "rupture": 0, "psychic_pressure": 0, "transformation_rule": 0, "formal_unity": 0, "ambiguity": 0, "residual_power": 0, "visibility": 0}}, "weakest": "...", "repair": "a few words", "premise": "premise_draft with that one repair applied", "visible": "one clause: what a viewer sees that is different", "render": "the result only, as the image model reads it", "target": "...", "replacement": "...", "preserve": ["..."], "visual_evidence": ["..."], "forbidden_interpretations": ["..."], "composition": {{"anomaly_scale": "dominant", "placement": "central", "frame_share": "at least one third", "scale_reference": "..."}}, "preserved_scene": "final ordinary context with removed entities omitted", "suppress": [], "suppress_properties": [], "scene": "the ordinary picture, no anomaly", "edit": "one imperative edit, or empty", "restatement": "the same fact in other words", "title_strategy": "...", "title": "...", "counter_terms": ["...", "..."]}}"""


@dataclass
class Verdict:
    subject: str = ""
    chosen_index: int = -1              # index into the candidate list, -1 = the critic wrote its own
    operation: str = ""
    affinity: str = ""
    law: str = ""                       # the transformation rule the picture obeys
    premise: str = ""
    visible: str = ""                   # what a viewer sees that is different: the anomaly as pixels
    restatement: str = ""
    title: str = ""
    title_strategy: str = ""
    counter_terms: List[str] = field(default_factory=list)
    judgements: List[str] = field(default_factory=list)
    scores: dict = field(default_factory=dict)      # rubric dimension -> 0..4
    weakest: str = ""                   # the dimension the critic revised for
    repair: str = ""                    # what it changed, in a few words
    render: str = ""                    # the premise as the image model reads it: the result only (lint.py)
    suppress: List[str] = field(default_factory=list)   # what the anomaly replaced: never named in the prompt
    scene: str = ""                     # the ordinary picture, no anomaly (two-stage, stage 1)
    edit: str = ""                      # one imperative edit that adds the anomaly (two-stage, stage 2)
    target: str = ""                    # entity changed by the selected operation
    replacement: str = ""               # replacement object, material or borrowed behaviour
    preserve: List[str] = field(default_factory=list)
    visual_evidence: List[str] = field(default_factory=list)
    forbidden_interpretations: List[str] = field(default_factory=list)
    composition: dict = field(default_factory=dict)
    preserved_scene: str = ""           # final context after removed/replaced facts are omitted
    suppress_properties: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)      # parts of the answer that were dropped, and why


def critic_messages(idea: str, candidates: Sequence[Candidate], count: int, charge: str, strangeness: str, medium: str,
                    law: str = "", inventory: str = "") -> Tuple[str, str]:
    lines = []
    for number, candidate in enumerate(candidates, 1):
        kind = "PROCEDURE" if candidate.procedure and not candidate.premise else "premise"
        impossible = "" if OPERATIONS[candidate.operation].impossible else "  (nothing impossible)"
        bond = f"\n   affinity found by the generator: {candidate.affinity}" if candidate.affinity else ""
        personal = "\n   uses the user's own iconography: prefer it when it is as good as the others" if candidate.personal else ""
        implied = candidate.law_hint or OPERATIONS[candidate.operation].law
        rule = f"\n   the law this operation implies: {implied}" if implied else ""
        seen = OPERATIONS[candidate.operation].visible
        shows = f"\n   how this operation becomes visible: {seen}" if seen else ""
        lines.append(f"{number}. [{candidate.operation}{impossible}] {kind}: {candidate.premise or candidate.procedure}{bond}{rule}{shows}{personal}")
    charge_text = CHARGES.get(charge, "")
    user = (
        f"IDEA\n{idea.strip()}\n\n"
        + (f"ORDINARY SCENE INVENTORY\n{inventory}\n\n" if inventory else "")
        + "CANDIDATES\n" + "\n".join(lines) + "\n\n"
        f"OPERATIONS WANTED: {count}" + (" (the second must be atmosphere-level - light, shadow, time, absence - so that both read as one event, "
                                         "and it must be an instance of the same law)" if count >= 2 else "") + "\n"
        f"STRANGENESS: {strangeness} (subtle = a viewer may need a second look; overt = unmistakable at a glance)\n"
        f"MEDIUM: {medium}" + (" - an anomaly in TIME is available: reversed, slowed, looped, or sound that belongs to something else" if medium == "video" else "") + "\n"
        + (f"CHARGE: {charge_text}\n" if charge_text else "")
        + (f"SUGGESTED LAW (keep it only if it governs the premise you choose; otherwise write your own): {law}\n" if law else "")
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
    # The critic writes a draft, scores it, then rewrites it with one repair. Either may be missing on a small model.
    premise = str(data.get("premise") or "").strip()
    draft = str(data.get("premise_draft") or "").strip()
    if not premise:
        premise = draft
    if not premise:
        return None, ["the critic returned no premise"]
    if draft and violations(premise) and not violations(draft):
        premise = draft          # the repair introduced a problem the draft did not have
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
    scores, weakest = _scores(data)
    visible = str(data.get("visible") or "").strip().strip('"')
    # Refusals are checked BEFORE placeholders: "nothing looks different" is the critic telling us the truth,
    # not a template it forgot to fill in.
    blind = UNRENDERABLE.search(visible)
    if visible and (blind or re.match(r"(?i)\s*nothing\b", visible)):
        return None, [f"the critic says the anomaly is not visible ('{blind.group(0) if blind else 'nothing'}'); "
                      "an image model would return an ordinary picture"]
    if visible.lower().strip(". ").startswith(("one clause", "what a viewer", "n/a", "none")):
        visible = ""
    restatement = str(data.get("restatement") or "").strip()
    if violations(restatement) or lint_render(restatement):
        restatement = ""
    counter_terms = _clean_counter_terms(data.get("counter_terms"), premise, str(data.get("subject") or ""))
    render, scene, edit, suppress, notes = _clean_staging(data)
    if not render and lint_render(premise):
        notes.append("the premise is written as a change rather than a result (" + lint_render(premise)[0] + "); the "
                     "rewriter is told to write the result only")
    preserved_scene = re.sub(r"\s+", " ", str(data.get("preserved_scene") or "")).strip().strip('"')
    if len(preserved_scene.split()) > MAX_RENDER_WORDS or SUBJECT_TOKEN in preserved_scene:
        notes.append("the critic's preserved scene was not used (too long, or left THE SUBJECT unresolved)")
        preserved_scene = ""
    target = re.sub(r"\s+", " ", str(data.get("target") or "")).strip().strip('"')
    replacement = re.sub(r"\s+", " ", str(data.get("replacement") or "")).strip().strip('"')
    if len(target.split()) > 12:
        target = ""
    if len(replacement.split()) > 16:
        replacement = ""
    return Verdict(subject=str(data.get("subject") or "").strip(), chosen_index=chosen, operation=operation, affinity=affinity,
                   law=_clean_law(data.get("law")), premise=premise, visible=visible, restatement=restatement,
                   title=_clean_title(data.get("title")), title_strategy=_clean_strategy(data.get("title_strategy")),
                   counter_terms=counter_terms, judgements=judgements,
                   scores=scores, weakest=weakest, repair=str(data.get("repair") or "").strip(),
                   render=render, suppress=suppress, scene=scene, edit=edit,
                   target=target, replacement=replacement,
                   preserve=_clean_plan_list(data.get("preserve")),
                   visual_evidence=_clean_plan_list(data.get("visual_evidence")),
                   forbidden_interpretations=_clean_plan_list(data.get("forbidden_interpretations")),
                   composition=_clean_composition(data.get("composition")),
                   preserved_scene=preserved_scene,
                   suppress_properties=_clean_plan_list(data.get("suppress_properties")),
                   notes=notes), []


PLACEHOLDER_STARTS = ("the result only", "the ordinary picture", "one imperative", "one or two", "n/a", "none", "empty")
MAX_RENDER_WORDS = 80
MAX_EDIT_WORDS = 60


def _clean_staging(data: dict) -> Tuple[str, str, str, List[str], List[str]]:
    """(render, scene, edit, suppress, notes). Each part is dropped, with a note, rather than guessed at."""
    notes: List[str] = []

    def text(key: str) -> str:
        value = str(data.get(key) or "").strip().strip('"')
        return "" if value.lower().startswith(PLACEHOLDER_STARTS) else value

    render, scene, edit = text("render"), text("scene"), text("edit")
    if render:
        problems = violations(render) + lint_render(render)
        if SUBJECT_TOKEN in render:
            problems.append(f"left {SUBJECT_TOKEN} unresolved")
        if len(render.split()) > MAX_RENDER_WORDS:
            problems.append(f"longer than {MAX_RENDER_WORDS} words")
        if problems:
            notes.append("the critic's render was not used: " + "; ".join(problems))
            render = ""
    if scene and (len(scene.split()) > MAX_RENDER_WORDS or SUBJECT_TOKEN in scene):
        notes.append("the critic's ordinary-scene prompt was not used (too long, or left THE SUBJECT unresolved)")
        scene = ""
    if edit and (len(edit.split()) > MAX_EDIT_WORDS or SUBJECT_TOKEN in edit or violations(edit)):
        notes.append("the critic's edit instruction was not used (too long, unresolved, or on the ban-list)")
        edit = ""
    suppress: List[str] = []
    raw = data.get("suppress")
    if isinstance(raw, str):
        raw = [part for part in re.split(r"[;,]", raw)]
    for term in raw or []:
        term = str(term).strip().strip(".")
        # Live 2026-10-01 the critic also listed operation names and concepts ("taxonomy_error", "mineralogical
        # classification"): only plain object names can be drawn by mistake, so only those are kept.
        if (not term or len(term.split()) > 5 or term.lower() in ("none", "n/a") or term in suppress or "_" in term
                or term.lower().replace(" ", "_") in OPERATIONS or re.search(r"(?i)\b(classification|operation|law|premise)\b", term)):
            continue
        suppress.append(term)
    return render, scene, edit, suppress[:4], notes


def _clean_plan_list(value, limit: int = 8) -> List[str]:
    if not isinstance(value, list):
        return []
    kept = []
    for entry in value:
        text = re.sub(r"\s+", " ", str(entry or "")).strip().strip(".")
        if text and len(text.split()) <= 24 and text.lower() not in {item.lower() for item in kept}:
            kept.append(text)
    return kept[:limit]


def _clean_composition(value) -> dict:
    if not isinstance(value, dict):
        return {}
    cleaned = {}
    limits = {"anomaly_scale": 6, "placement": 12, "frame_share": 10, "scale_reference": 12}
    for key, word_limit in limits.items():
        text = re.sub(r"\s+", " ", str(value.get(key) or "")).strip().strip(".")
        if text and len(text.split()) <= word_limit:
            cleaned[key] = text
    return cleaned


def _clean_counter_terms(value, premise: str, subject: str) -> List[str]:
    """The ordinary things the image model will substitute for the anomaly - drawn from THIS scene.

    Weaker models copy the worked example out of the instructions instead: a garden premise came back with
    "porcelain teacup, ceramic cup, porcelain teacup, ceramic cup, porcelain teacup". A term earns its place
    only if it shares a content word with the premise or the subject, and duplicates are dropped."""
    words = set(re.findall(r"[a-z]{3,}", (premise + " " + subject).lower()))
    kept, seen = [], set()
    for term in (value or []):
        text = str(term).strip().strip(".,")
        key = text.lower()
        if not text or key in seen:
            continue
        # Related if any word of the term touches any word of the premise, either way round: "cup of tea"
        # belongs to a premise about a teacup, "porcelain teacup" does not belong to one about a garden.
        parts = re.findall(r"[a-z]{3,}", key)
        if words and parts and not any(part in word or word in part for part in parts for word in words):
            continue            # belongs to some other scene than this one
        seen.add(key)
        kept.append(text)
    return kept[:5]


def _clean_law(value) -> str:
    """A law is one plain sentence. Reject a placeholder echo, an over-long one, or one that explains itself."""
    law = str(value or "").strip().strip('"')
    if not law:
        return ""
    if law.lower().strip(". ").startswith(("one sentence", "what may change", "the law", "n/a", "none")):
        return ""
    if len(law.split()) > MAX_LAW_WORDS or violations(law):
        return ""
    return law


def _clean_title(value) -> str:
    title = str(value or "").strip().strip('"').strip()
    if not title:
        return ""
    stripped = re.sub(r"^(the|a|an)\s+", "", title.lower()).strip(" .!?")
    if stripped in BANNED_TITLES or any(word in stripped for word in ("surreal", "untitled")):
        return ""
    return title


def _clean_strategy(value) -> str:
    name = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    return name if name in TITLE_STRATEGIES else ""


def _scores(data: dict) -> Tuple[dict, str]:
    """(scores, weakest). Unknown keys and unparseable values are dropped rather than guessed at."""
    found = {}
    raw = data.get("scores")
    if isinstance(raw, dict):
        for name, value in raw.items():
            key = str(name).strip().lower().replace(" ", "_")
            if key in RUBRIC:
                try:
                    found[key] = max(0, min(4, int(float(value))))
                except (TypeError, ValueError):
                    continue
    weakest = str(data.get("weakest") or "").strip().lower().replace(" ", "_")
    if weakest not in RUBRIC:
        weakest = min(found, key=lambda key: found[key]) if found else ""
    return found, weakest
