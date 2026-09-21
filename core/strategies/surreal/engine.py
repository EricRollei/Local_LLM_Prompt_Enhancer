"""
The surreal engine: generator -> critic -> brief.

    engine = SurrealEngine(sources)
    plan = engine.plan(idea, settings, seed)                 # candidates + the code critic's choice
    system, user = engine.critic_messages(plan)              # optional: ask an LLM to be the critic
    verdict, problems = parse_critic(answer, plan.candidates)
    result = engine.finish(plan, verdict)                    # text, instruction block, why, title

Nothing here calls an LLM or imports ComfyUI. The instruction block is written to travel through the
`wildcard_instructions` input every enhancer node already has: its "Concepts" heading is the one the Concept
Survival Check parses, so the anomaly's survival through a rewrite can be measured.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from .critic import Verdict, code_choose, critic_messages
from .generators import MODE_GENERATORS, Candidate, Context
from .sources import SurrealSources
from .vocabulary import (
    AUTO, CHARGES, MODE_WEIGHTS, MODES, NONE, OPERATIONS, REGISTERS, SUBJECT_TOKEN,
)

PAINTED_REGISTERS = ("academic oil", "metaphysical", "biomorphic", "collage")


@dataclass
class SurrealSettings:
    mode: str = AUTO
    operation: str = AUTO
    count: int = 1                       # 1 or 2, never more: see docs/SURREAL_GUIDE.md
    register: str = "deadpan photographic"
    charge: str = AUTO
    strangeness: str = "balanced"
    medium: str = "image"                # image | video
    candidates: int = 6                  # how many the critic gets to choose from


@dataclass
class SurrealPlan:
    idea: str
    settings: SurrealSettings
    seed: int
    modes: List[str]
    candidates: List[Candidate]
    chosen: List[Candidate]              # the code critic's choice; the fallback when there is no LLM verdict
    charge: str
    notes: List[str] = field(default_factory=list)


@dataclass
class SurrealResult:
    text: str
    instructions: str
    why: str
    title: str = ""
    negative_additions: str = ""
    premises: List[str] = field(default_factory=list)
    operations: List[str] = field(default_factory=list)
    ok: bool = True


class SurrealEngine:
    def __init__(self, sources: SurrealSources):
        self.sources = sources

    # ---- generator + code critic ---------------------------------------------------------------------
    def plan(self, idea: str, settings: SurrealSettings, seed: Optional[int] = None,
             distance: Optional[Callable[[str], float]] = None) -> SurrealPlan:
        if seed is None:
            seed = random.SystemRandom().randrange(0, 0x7FFFFFFF)
        rng = random.Random(seed)
        settings.count = 2 if int(settings.count or 1) >= 2 else 1
        context = Context(idea=idea or "", rng=rng, sources=self.sources, medium=settings.medium,
                          strangeness=settings.strangeness, distance=distance)
        notes: List[str] = []

        modes = self._modes(settings, rng, notes)
        candidates: List[Candidate] = []
        for mode in modes:
            produced = MODE_GENERATORS[mode](context, settings.operation)
            attempts = 0
            while len(produced) < 2 and attempts < 3 and mode not in ("problem",):      # one-per-call modes: draw again
                produced = produced + MODE_GENERATORS[mode](context, settings.operation)
                attempts += 1
            if not produced:
                notes.append(f"mode {mode} produced nothing (its lists are empty or missing)")
            candidates.extend(produced)
        if settings.count >= 2:     # make sure an atmosphere-level second operation is on the table
            for name in ("physics_negation", "absence"):
                candidates.extend(MODE_GENERATORS["affinity_search"](context, name)[:1])
        if not candidates:
            notes.append("no mode produced a candidate; falling back to the affinity search")
            candidates = MODE_GENERATORS["affinity_search"](context, AUTO)

        candidates = self._trim(candidates, max(2, int(settings.candidates or 6)), rng)
        chosen, critic_notes = code_choose(candidates, rng, settings.count)
        notes.extend(critic_notes)
        charge = settings.charge
        if charge == AUTO:
            charge = rng.choice([name for name in CHARGES if name != NONE])
        return SurrealPlan(idea=idea or "", settings=settings, seed=seed, modes=modes, candidates=candidates,
                           chosen=chosen, charge=charge, notes=notes)

    def _modes(self, settings: SurrealSettings, rng: random.Random, notes: List[str]) -> List[str]:
        if settings.operation != AUTO:
            if settings.mode not in (AUTO, "affinity_search"):
                notes.append(f"operation '{settings.operation}' was chosen, so the affinity search is used instead of mode '{settings.mode}'")
            return ["affinity_search"]
        if settings.mode != AUTO and settings.mode in MODES:
            if settings.mode == "archive_composite" and not (self.sources.has_personal() or self.sources.archive):
                notes.append("archive composite needs your iconography file or prompt database, and both are empty; using read the noise")
                return ["read_the_noise"]
            return [settings.mode]
        weights = dict(MODE_WEIGHTS.get(settings.strangeness, MODE_WEIGHTS["balanced"]))
        if not (self.sources.has_personal() or self.sources.archive):
            weights.pop("archive_composite", None)
        elif self.sources.has_personal():
            weights["archive_composite"] = weights.get("archive_composite", 1) * 2     # a personal vocabulary is preferred to stock
        names = list(weights)
        first = rng.choices(names, weights=[weights[name] for name in names], k=1)[0]
        modes = [first]
        if first != "affinity_search":
            modes.append("affinity_search")      # the critic always has object-level alternatives to weigh against
        else:
            others = [name for name in names if name != first]
            modes.append(rng.choices(others, weights=[weights[name] for name in others], k=1)[0])
        return modes

    @staticmethod
    def _trim(candidates: List[Candidate], limit: int, rng: random.Random) -> List[Candidate]:
        """Keep `limit` candidates: the best of each operation first, so the critic weighs different KINDS of idea."""
        seen_text, unique = set(), []
        for candidate in candidates:
            key = candidate.premise or candidate.procedure
            if key and key not in seen_text:
                seen_text.add(key)
                unique.append(candidate)
        by_score = sorted(unique, key=lambda candidate: (-candidate.score, rng.random()))
        kept, seen_operation = [], set()
        for candidate in by_score:
            if (candidate.mode, candidate.operation) not in seen_operation:
                seen_operation.add((candidate.mode, candidate.operation))
                kept.append(candidate)
        for candidate in by_score:
            if len(kept) >= limit:
                break
            if candidate not in kept:
                kept.append(candidate)
        return kept[:limit]

    # ---- LLM critic -------------------------------------------------------------------------------------
    def critic_messages(self, plan: SurrealPlan) -> Tuple[str, str]:
        return critic_messages(plan.idea, plan.candidates, plan.settings.count, plan.charge, plan.settings.strangeness, plan.settings.medium)

    # ---- brief ---------------------------------------------------------------------------------------------
    def finish(self, plan: SurrealPlan, verdict: Optional[Verdict] = None, critic_problems: Optional[List[str]] = None) -> SurrealResult:
        settings = plan.settings
        notes = list(plan.notes)
        if critic_problems:
            notes.append("LLM critic not used: " + "; ".join(critic_problems) + " - the code critic's choice stands")

        procedures: List[str] = []
        if verdict is not None:
            premises = [verdict.premise]
            operations = [verdict.operation]
            affinity, restatement, title = verdict.affinity, verdict.restatement, verdict.title
            register_hint = plan.candidates[verdict.chosen_index].register_hint if verdict.chosen_index >= 0 else ""
        else:
            if not plan.chosen:
                return SurrealResult(text=plan.idea, instructions="", ok=False,
                                     why="No acceptable candidate was produced; the idea is passed through unchanged.\n" + "\n".join(notes))
            premises = [candidate.premise for candidate in plan.chosen if candidate.premise]
            procedures = [candidate.procedure for candidate in plan.chosen if candidate.procedure and not candidate.premise]
            operations = [candidate.operation for candidate in plan.chosen]
            affinity = plan.chosen[0].affinity
            restatement, title = "", ""
            register_hint = plan.chosen[0].register_hint

        register = settings.register if settings.register in REGISTERS else "deadpan photographic"
        if register_hint and register_hint != register:
            photographic_only = "process_estrangement" in operations
            if register == "deadpan photographic" or (photographic_only and register in PAINTED_REGISTERS):
                notes.append(f"register '{register}' -> '{register_hint}': the chosen operation needs it")
                register = register_hint
        impossible = any(OPERATIONS[name].impossible for name in operations if name in OPERATIONS)

        text = self._text(plan.idea, premises, unresolved=verdict is None)
        instructions = self._instructions(premises, procedures, restatement, register, plan.charge, impossible, settings, unresolved=verdict is None)
        why = self._why(plan, verdict, operations, affinity, register, notes)
        negative = ", ".join(verdict.counter_terms) if verdict is not None else ""
        return SurrealResult(text=text, instructions=instructions, why=why, title=title, negative_additions=negative,
                             premises=premises, operations=operations)

    @staticmethod
    def _text(idea: str, premises: List[str], unresolved: bool) -> str:
        if not premises:
            return idea.strip()
        joined = " ".join(premises)
        note = f" ({SUBJECT_TOKEN} is the main subject above.)" if unresolved and SUBJECT_TOKEN in joined else ""
        return f"{idea.strip()}\n\n{joined}{note}"

    @staticmethod
    def _instructions(premises: List[str], procedures: List[str], restatement: str, register: str, charge: str,
                      impossible: bool, settings: SurrealSettings, unresolved: bool) -> str:
        lines = ["SURREAL PREMISE (a deliberate strategy for this prompt; image models drift toward the plausible, so protect it):"]
        if premises:
            lines.append("Concepts - keep the MEANING of each, but express it in the wording that works best for the target model:")
            lines.extend(f"  - {premise}" for premise in premises)
        if procedures:
            lines.append("Do this first, silently. Its one-sentence result is the premise of this prompt: keep its meaning through every rewording.")
            lines.extend(f"  * {procedure}" for procedure in procedures)
        lines.append("How to write it:")
        if unresolved and any(SUBJECT_TOKEN in text for text in premises + procedures):
            lines.append(f"  * {SUBJECT_TOKEN} means the main subject of the user's idea. Name it; never write the words '{SUBJECT_TOKEN}'.")
        if impossible:
            lines.append("  * State the anomaly early, as plain physical fact in the present tense, the way a report would. "
                         "Then restate it once, later, in different words" + (f" (for example: {restatement})" if restatement else "") +
                         ", so the image model cannot normalise it away.")
            lines.append("  * " + ("Exactly these anomalies and no others." if len(premises) + len(procedures) > 1 else "Exactly ONE anomaly.") +
                         " Everything else is rigorously ordinary: a real place, real light with a stated source and direction, "
                         "real materials, consistent perspective and shadows. Nobody in the picture reacts to the anomaly.")
        else:
            lines.append("  * NOTHING impossible appears in this picture. Do not add an anomaly. The strangeness is entirely in the hour, "
                         "the emptiness, the stillness, the process, and in a story that is not told.")
        lines.append(f"  * Register: {register}. {REGISTERS[register]}")
        charge_text = CHARGES.get(charge, "")
        if charge_text:
            lines.append(f"  * What it serves: {charge_text}. Carry it through light, distance and posture - never name the emotion.")
        lines.append("  * Pose the question and refuse the answer: no explanation, no symbolism, no moral, no 'as if', no caption.")
        lines.append("  * Leave out the cliches of the genre (melting clocks, floating islands, glow, mist) and the words surreal, "
                     "dreamlike, ethereal, whimsical, otherworldly. Do not write 'no X' to exclude anything: an image model reads "
                     "'no mist' as mist. Simply leave things out.")
        lines.append("  * In the target format: a TAG list carries the premise as two or three adjacent tags near the front (weighted, "
                     "e.g. (fur teacup:1.3), only if the format allows weights); JSON with elements gives it an element of its own; "
                     "named fields put it in the first visual field.")
        if settings.medium == "video":
            lines.append("  * Video: the anomaly is present from the first frame and persists unchanged for the whole clip; it is not a "
                         "transformation that happens during the shot unless the premise says so. Sound stays ordinary unless the premise is about sound.")
        return "\n".join(lines)

    @staticmethod
    def _why(plan: SurrealPlan, verdict: Optional[Verdict], operations: List[str], affinity: str, register: str, notes: List[str]) -> str:
        lines = [f"seed {plan.seed}  |  modes: {', '.join(plan.modes)}  |  critic: {'LLM' if verdict is not None else 'code'}"
                 f"  |  register: {register}  |  charge: {plan.charge}"]
        for name in operations:
            operation = OPERATIONS.get(name)
            if operation is not None:
                lines.append(f"operation: {name} - {operation.what}  ({operation.lineage})")
        if verdict is not None and verdict.subject:
            lines.append(f"subject: {verdict.subject}")
        if affinity:
            lines.append(f"affinity: {affinity}")
        if verdict is not None and verdict.title:
            lines.append(f"title: {verdict.title}")
        lines.append("candidates (* = chosen):")
        chosen_indexes = {verdict.chosen_index} if verdict is not None else {plan.candidates.index(c) for c in plan.chosen if c in plan.candidates}
        for number, candidate in enumerate(plan.candidates):
            mark = "*" if number in chosen_indexes else " "
            lines.append(f" {mark}{number + 1}. [{candidate.mode}] {candidate.line()[:240]}")
        if verdict is not None and verdict.chosen_index < 0:
            lines.append(" * the critic wrote its own premise rather than keeping a candidate")
        if verdict is not None and verdict.judgements:
            lines.append("critic's judgements: " + " | ".join(verdict.judgements))
        lines.extend(f"note: {note}" for note in notes)
        return "\n".join(lines)
