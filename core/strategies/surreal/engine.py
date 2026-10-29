"""
The surreal engine: ordinary-scene inventory -> generator -> critic -> structured compiler -> brief.

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

from .compiler import CompositionPlan, StructuredRenderPlan, build_render_plan, compile_render_plan
from .critic import Verdict, code_choose, critic_messages
from .generators import MODE_GENERATORS, Candidate, Context
from .lint import SUPPRESS_MARKER
from .scene import SceneInventory, inventory_for_critic
from .sources import SurrealSources
from .vocabulary import (
    AUTO, CHARGES, MODE_WEIGHTS, MODES, NONE, OPERATIONS, REGISTERS, RUBRIC, SUBJECT_TOKEN, law_seed,
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
    law: str = ""                        # the transformation rule, written by hand; blank = drawn from the charge
    staging: str = "one_stage"           # one_stage | two_stage (two_stage = only operations that can be staged as one edit)


@dataclass
class SurrealPlan:
    idea: str
    settings: SurrealSettings
    seed: int
    modes: List[str]
    candidates: List[Candidate]
    chosen: List[Candidate]              # the code critic's choice; the fallback when there is no LLM verdict
    charge: str
    law: str = ""                        # the law offered to the critic: the user's, the operation's, or the charge's
    inventory: Optional[SceneInventory] = None
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
    law: str = ""
    visible: str = ""
    ok: bool = True
    renders: List[str] = field(default_factory=list)     # the premises as the image model reads them (result only)
    suppress: List[str] = field(default_factory=list)    # what the anomaly replaced: never named in the prompt
    scene_prompt: str = ""            # two-stage, stage 1: the ordinary picture. Blank when the operation cannot be staged
    edit_instruction: str = ""        # two-stage, stage 2: one imperative edit that adds the anomaly
    render_plan: Optional[StructuredRenderPlan] = None


class SurrealEngine:
    def __init__(self, sources: SurrealSources):
        self.sources = sources

    # ---- generator + code critic ---------------------------------------------------------------------
    def plan(self, idea: str, settings: SurrealSettings, seed: Optional[int] = None,
             distance: Optional[Callable[[str], float]] = None,
             inventory: Optional[SceneInventory] = None) -> SurrealPlan:
        if seed is None:
            seed = random.SystemRandom().randrange(0, 0x7FFFFFFF)
        rng = random.Random(seed)
        settings.count = 2 if int(settings.count or 1) >= 2 else 1
        context = Context(idea=idea or "", rng=rng, sources=self.sources, medium=settings.medium,
                          strangeness=settings.strangeness, distance=distance,
                          staging=settings.staging if settings.staging in ("one_stage", "two_stage") else "one_stage")
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

        # The law must GOVERN the premise that was chosen, or the instruction to remove whatever disobeys it would
        # delete the premise itself. So: the user's own law wins; then a candidate's more specific one; then the law
        # of the operation actually chosen. The charge's law is only a last resort, and is offered to the LLM critic
        # as a suggestion rather than used as written, because an emotion does not know which anomaly was picked.
        law = (settings.law or "").strip()
        if not law:
            law = next((candidate.law_hint for candidate in chosen if candidate.law_hint), "")
        if not law:
            law = next((OPERATIONS[candidate.operation].law for candidate in chosen
                        if candidate.operation in OPERATIONS and OPERATIONS[candidate.operation].law), "")
        if not law:
            law = law_seed(charge, rng)
            notes.append("no operation law applied; the law was drawn for the charge and may not fit the premise")
        return SurrealPlan(idea=idea or "", settings=settings, seed=seed, modes=modes, candidates=candidates,
                           chosen=chosen, charge=charge, law=law, inventory=inventory, notes=notes)

    def _modes(self, settings: SurrealSettings, rng: random.Random, notes: List[str]) -> List[str]:
        if settings.operation != AUTO:
            if settings.mode not in (AUTO, "affinity_search"):
                notes.append(f"operation '{settings.operation}' was chosen, so the affinity search is used instead of mode '{settings.mode}'")
            return ["affinity_search"]
        if settings.mode == AUTO and settings.staging == "two_stage":
            # Only object-level operations can be staged as one edit; the procedure mode is kept because the LLM critic
            # writes its own edit for whatever it finds.
            return ["affinity_search", "problem"]
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
        return critic_messages(plan.idea, plan.candidates, plan.settings.count, plan.charge, plan.settings.strangeness,
                               plan.settings.medium, law=plan.law, inventory=inventory_for_critic(plan.inventory))

    # ---- brief ---------------------------------------------------------------------------------------------
    def finish(self, plan: SurrealPlan, verdict: Optional[Verdict] = None, critic_problems: Optional[List[str]] = None) -> SurrealResult:
        settings = plan.settings
        notes = list(plan.notes)
        if critic_problems:
            notes.append("LLM critic not used: " + "; ".join(critic_problems) + " - the code critic's choice stands")

        procedures: List[str] = []
        suppress: List[str] = []
        edit, scene = "", ""
        selected_candidate: Optional[Candidate] = None
        if verdict is not None:
            premises = [verdict.premise]
            renders = [verdict.render or verdict.premise]
            suppress = list(verdict.suppress)
            operations = [verdict.operation]
            affinity, restatement, title = verdict.affinity, verdict.restatement, verdict.title
            visible = verdict.visible
            register_hint = plan.candidates[verdict.chosen_index].register_hint if verdict.chosen_index >= 0 else ""
            selected_candidate = plan.candidates[verdict.chosen_index] if verdict.chosen_index >= 0 else None
            notes.extend(verdict.notes)
            operation = OPERATIONS.get(verdict.operation)
            if verdict.edit and (operation is None or operation.impossible):
                edit = verdict.edit
                scene = verdict.scene or plan.idea.strip()
        else:
            if not plan.chosen:
                return SurrealResult(text=plan.idea, instructions="", ok=False,
                                     why="No acceptable candidate was produced; the idea is passed through unchanged.\n" + "\n".join(notes))
            premises = [candidate.premise for candidate in plan.chosen if candidate.premise]
            renders = [candidate.rendered() for candidate in plan.chosen if candidate.premise]
            for candidate in plan.chosen:
                suppress.extend(term for term in candidate.suppress if term not in suppress)
            procedures = [candidate.procedure for candidate in plan.chosen if candidate.procedure and not candidate.premise]
            operations = [candidate.operation for candidate in plan.chosen]
            affinity = plan.chosen[0].affinity
            restatement, title = "", ""
            visible = ""
            register_hint = plan.chosen[0].register_hint
            selected_candidate = plan.chosen[0]
            if plan.chosen[0].edit:
                edit = plan.chosen[0].edit
                scene = plan.idea.strip()
        if edit and len(operations) > 1:
            notes.append("two-stage: the edit carries the first operation only; the second is in the one-stage prompt")
        if settings.staging == "two_stage" and not edit:
            notes.append(f"two-stage asked for, but '{', '.join(operations)}' cannot be applied as one edit; use the "
                         "one-stage text")

        register = settings.register if settings.register in REGISTERS else "deadpan photographic"
        if register_hint and register_hint != register:
            photographic_only = "process_estrangement" in operations
            if register == "deadpan photographic" or (photographic_only and register in PAINTED_REGISTERS):
                notes.append(f"register '{register}' -> '{register_hint}': the chosen operation needs it")
                register = register_hint
        impossible = any(OPERATIONS[name].impossible for name in operations if name in OPERATIONS)
        # The critic's law beats the one the plan offered it: the critic saw the premise it actually chose.
        law = (verdict.law if verdict is not None and verdict.law else "") or plan.law
        if settings.law.strip():
            law = settings.law.strip()          # a hand-written law is never overridden

        how_seen = next((OPERATIONS[name].visible for name in operations if name in OPERATIONS and OPERATIONS[name].visible), "")

        render_plan = None
        compiled_warnings: List[str] = []
        if renders:
            candidate = selected_candidate
            composition_data = verdict.composition if verdict is not None else {}
            composition = CompositionPlan(
                anomaly_scale=str(composition_data.get("anomaly_scale") or "dominant"),
                placement=str(composition_data.get("placement") or "central"),
                frame_share=str(composition_data.get("frame_share") or "at least one third of the frame"),
                scale_reference=str(composition_data.get("scale_reference") or (candidate.scale_reference if candidate else "")),
            )
            evidence: List[str] = []
            if verdict is not None:
                evidence.extend(verdict.visual_evidence)
            if candidate is not None:
                evidence.extend(candidate.evidence)
            if visible:
                evidence.append(visible)
            render_plan = build_render_plan(
                operation=operations[0] if operations else "",
                anomaly=" ".join(renders),
                idea=plan.idea,
                inventory=plan.inventory,
                preserved_scene=verdict.preserved_scene if verdict is not None else "",
                target=(verdict.target if verdict is not None else "") or (candidate.target if candidate else ""),
                replacement=(verdict.replacement if verdict is not None else "") or (candidate.replacement if candidate else ""),
                preserved_properties=(verdict.preserve if verdict is not None else []) or (candidate.preserve if candidate else []),
                suppress_entities=suppress,
                suppress_properties=verdict.suppress_properties if verdict is not None else [],
                visual_evidence=evidence,
                forbidden_interpretations=(verdict.forbidden_interpretations if verdict is not None else [])
                + (candidate.forbidden if candidate else []),
                composition=composition,
                law=law,
                edit_instruction=edit,
            )
            compiled = compile_render_plan(render_plan)
            compiled_warnings.extend(compiled.warnings)
            if not compiled.ok:
                return SurrealResult(
                    text=plan.idea,
                    instructions="",
                    why=("Structured surreal compiler refused the selected premise: "
                         + "; ".join(compiled.warnings)
                         + ". The original idea was passed through unchanged."),
                    ok=False,
                    premises=premises,
                    operations=operations,
                    law=law,
                    renders=renders,
                    suppress=suppress,
                    scene_prompt=scene,
                    edit_instruction=edit,
                    render_plan=render_plan,
                )
            text = compiled.text
        else:
            text = self._text(plan.idea, renders, unresolved=verdict is None)
        notes.extend(compiled_warnings)
        instructions = self._instructions(renders, procedures, restatement, register, plan.charge, impossible, settings,
                                          law=law, visible=visible, how_seen=how_seen, unresolved=verdict is None,
                                          suppress=suppress, render_plan=render_plan)
        why = self._why(plan, verdict, operations, affinity, register, law, visible, how_seen, notes,
                        renders=renders, premises=premises, suppress=suppress, scene=scene, edit=edit,
                        render_plan=render_plan)
        negative = ", ".join(verdict.counter_terms) if verdict is not None else ""
        return SurrealResult(text=text, instructions=instructions, why=why, title=title, negative_additions=negative,
                             premises=premises, operations=operations, law=law, visible=visible or how_seen,
                             renders=renders, suppress=suppress, scene_prompt=scene, edit_instruction=edit,
                             render_plan=render_plan)

    @staticmethod
    def _text(idea: str, premises: List[str], unresolved: bool) -> str:
        if not premises:
            return idea.strip()
        joined = " ".join(premises)
        note = f" ({SUBJECT_TOKEN} is the main subject above.)" if unresolved and SUBJECT_TOKEN in joined else ""
        return f"{idea.strip()}\n\n{joined}{note}"

    @staticmethod
    def _instructions(premises: List[str], procedures: List[str], restatement: str, register: str, charge: str,
                      impossible: bool, settings: SurrealSettings, law: str, visible: str, how_seen: str,
                      unresolved: bool, suppress: Optional[List[str]] = None,
                      render_plan: Optional[StructuredRenderPlan] = None) -> str:
        """`premises` here are the RENDERED forms: what the camera sees, never the substitution (lint.py)."""
        lines = ["SURREAL PREMISE (a deliberate strategy for this prompt; image models drift toward the plausible, so protect it):"]
        if premises:
            lines.append("Concepts - keep the MEANING of each, but express it in the wording that works best for the target model:")
            lines.extend(f"  - {premise}" for premise in premises)
        if render_plan is not None:
            lines.append("STRUCTURED RENDER PLAN - this is already decided. Verbalize it; do not reinterpret it or restore the ordinary source:")
            lines.append(f"  operation: {render_plan.operation}")
            if render_plan.target:
                lines.append(f"  target: {render_plan.target}")
            if render_plan.replacement:
                lines.append(f"  replacement/material/behaviour: {render_plan.replacement}")
            if render_plan.preserved_properties:
                lines.append("  preserve: " + "; ".join(render_plan.preserved_properties))
            if render_plan.visual_evidence:
                lines.append("  required visual proof: " + " | ".join(render_plan.visual_evidence))
            if render_plan.forbidden_interpretations:
                lines.append("  reject these ordinary readings: " + " | ".join(render_plan.forbidden_interpretations))
            lines.append(
                f"  composition: {render_plan.composition.anomaly_scale}; {render_plan.composition.placement}; "
                f"{render_plan.composition.frame_share}"
            )
        if suppress:
            lines.append(f"  {SUPPRESS_MARKER} {'; '.join(suppress)}")
            lines.append("  (Naming it makes the image model draw it. Describe the spot it would occupy by what surrounds it - "
                         "the surface, the hand, the shelf - and never by its name.)")
        if procedures:
            lines.append("Do this first, silently. Its one-sentence result is the premise of this prompt: keep its meaning through every rewording.")
            lines.extend(f"  * {procedure}" for procedure in procedures)
        if law:
            lines.append("The law - the picture follows this rule consistently, and it is what makes the anomaly read as "
                         "inevitable rather than random:")
            lines.append(f"  {law}")
            lines.append("  Show the rule in effect; never state it, name it or explain it. Anything in the picture that does "
                         "not obey it is removed.")
        lines.append("What the viewer must SEE - an image model can only render what is present in the frame, never an "
                     "absence, a negation or a cause:")
        if visible:
            lines.append(f"  {visible}")
        if how_seen:
            lines.append(f"  {how_seen}")
        lines.append("How to write it:")
        if unresolved and any(SUBJECT_TOKEN in text for text in premises + procedures):
            lines.append(f"  * {SUBJECT_TOKEN} means the main subject of the user's idea. Name it; never write the words '{SUBJECT_TOKEN}'.")
        if impossible:
            lines.append("  * The anomaly is the FIRST thing in the prompt, stated as plain physical fact in the present tense: what "
                         "the camera sees, never what it replaced, never 'should be', 'instead of', 'in place of' or 'as if'. "
                         "Then give it a second visible consequence later on - its shadow, its weight on what holds it, its "
                         "texture up close" + (f" (the same fact in other words: {restatement})" if restatement else "") +
                         " - so the image model cannot normalise it away.")
            lines.append("  * Make it large in the frame and central, lit like everything else. Deadpan is not the same as small: "
                         "a viewer must see it in a thumbnail at a glance.")
            lines.append("  * " + ("Exactly these anomalies and no others." if len(premises) + len(procedures) > 1 else "Exactly ONE anomaly.") +
                         " Everything else is rigorously ordinary: a real place, real light with a stated source and direction, "
                         "real materials, consistent perspective and shadows. People in the picture carry on with ordinary "
                         "actions; never write that nobody notices or that it goes unnoticed - that has no pixels.")
            lines.append("  * Spend the words on the anomaly: it and its evidence take at least a third of the prompt. Leave out "
                         "camera-body, lens and film-stock detail unless the register needs it.")
        else:
            lines.append("  * NOTHING impossible appears in this picture. Do not add an anomaly. The strangeness is entirely in the hour, "
                         "the emptiness, the stillness, the process, and in a story that is not told.")
        lines.append(f"  * Register: {register}. {REGISTERS[register]}")
        charge_text = CHARGES.get(charge, "")
        if charge_text:
            lines.append(f"  * What it serves: {charge_text}. Carry it through light, distance and posture - never name the emotion.")
        lines.append("  * Pose the question and refuse the answer: no explanation, no symbolism, no moral, no 'as if', no caption.")
        lines.append("  * Add NO further symbolic objects. Every noun you add competes with the premise; a long inventory of "
                     "dreamlike things is the commonest way to lose it. If a detail is not the anchor, the anomaly, the law "
                     "or the light, leave it out.")
        if impossible:
            lines.append("  * Order it this way: the impossible fact, stated flatly as what is seen; then the ordinary place and what "
                         "the subject is doing, briefly; then light and surface. Nothing else.")
        else:
            lines.append("  * Order it this way: the ordinary place and what the subject is doing; then the hour, the light and the "
                         "one detail that carries the strangeness; then camera and surface. Nothing else.")
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
    def _why(plan: SurrealPlan, verdict: Optional[Verdict], operations: List[str], affinity: str, register: str,
             law: str, visible: str, how_seen: str, notes: List[str], renders: Optional[List[str]] = None,
             premises: Optional[List[str]] = None, suppress: Optional[List[str]] = None, scene: str = "",
             edit: str = "", render_plan: Optional[StructuredRenderPlan] = None) -> str:
        lines = [f"seed {plan.seed}  |  modes: {', '.join(plan.modes)}  |  critic: {'LLM' if verdict is not None else 'code'}"
                 f"  |  register: {register}  |  charge: {plan.charge}  |  staging: {plan.settings.staging}"]
        if renders and premises and renders != premises:
            lines.append("rendered as: " + " | ".join(renders))
        if suppress:
            lines.append("never named in the prompt: " + ", ".join(suppress))
        if edit:
            lines.append(f"two-stage: scene = {scene[:160]}")
            lines.append(f"two-stage: edit  = {edit}")
        if plan.inventory is not None:
            lines.append("ordinary inventory: " + plan.inventory.summary())
        if render_plan is not None:
            lines.extend(render_plan.report_lines())
        for name in operations:
            operation = OPERATIONS.get(name)
            if operation is not None:
                lines.append(f"operation: {name} - {operation.what}  ({operation.lineage})")
        if verdict is not None and verdict.subject:
            lines.append(f"subject: {verdict.subject}")
        if affinity:
            lines.append(f"affinity: {affinity}")
        if law:
            if plan.settings.law.strip():
                source = "yours"
            elif verdict is not None and verdict.law:
                source = "the critic's"
            elif any(law in (candidate.law_hint, OPERATIONS.get(candidate.operation, OPERATIONS["displacement"]).law)
                     for candidate in plan.chosen):
                source = "the operation's"
            else:
                source = f"drawn for '{plan.charge}'"
            lines.append(f"law ({source}): {law}")
        if visible:
            lines.append(f"visible (the critic's): {visible}")
        elif how_seen:
            lines.append(f"visible (the operation's): {how_seen}")
        if verdict is not None and verdict.scores:
            ordered = [f"{name} {verdict.scores[name]}" for name in RUBRIC if name in verdict.scores]
            lines.append(f"rubric (0-4): {', '.join(ordered)}   total {sum(verdict.scores.values())}/{4 * len(verdict.scores)}")
            if verdict.weakest:
                lines.append(f"revised for the weakest dimension ({verdict.weakest}): {verdict.repair or 'no repair stated'}")
        elif verdict is not None:
            lines.append("rubric: the critic returned no scores")
        if verdict is not None and verdict.title:
            lines.append(f"title ({verdict.title_strategy or 'strategy not named'}): {verdict.title}")
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
