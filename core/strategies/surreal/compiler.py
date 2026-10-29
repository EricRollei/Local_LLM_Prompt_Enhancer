"""
Structured surreal render plans and operation-specific prompt compilation.

The compiler receives a finished artistic decision. It does not choose a mode, invent another object or explain
the symbolism. Its job is to turn the transformed scene into positive, visible image facts while preventing the
ordinary source object from leaking back into the final prompt.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from .lint import lint_render, named_terms
from .scene import SceneInventory


@dataclass
class CompositionPlan:
    anomaly_scale: str = "dominant"
    placement: str = "central"
    frame_share: str = "at least one third of the frame"
    scale_reference: str = ""


@dataclass
class StructuredRenderPlan:
    operation: str
    anomaly: str
    ordinary_scene: str = ""
    preserved_scene: str = ""
    target: str = ""
    replacement: str = ""
    preserved_properties: List[str] = field(default_factory=list)
    suppress_entities: List[str] = field(default_factory=list)
    suppress_properties: List[str] = field(default_factory=list)
    visual_evidence: List[str] = field(default_factory=list)
    forbidden_interpretations: List[str] = field(default_factory=list)
    composition: CompositionPlan = field(default_factory=CompositionPlan)
    law: str = ""
    edit_instruction: str = ""

    def report_lines(self) -> List[str]:
        lines = [f"structured plan: operation={self.operation}"]
        if self.target:
            lines.append(f"structured plan: target={self.target}")
        if self.replacement:
            lines.append(f"structured plan: replacement={self.replacement}")
        if self.preserved_properties:
            lines.append("structured plan: preserve=" + "; ".join(self.preserved_properties))
        if self.suppress_entities:
            lines.append("structured plan: removed entities=" + "; ".join(self.suppress_entities))
        if self.suppress_properties:
            lines.append("structured plan: replaced properties=" + "; ".join(self.suppress_properties))
        if self.visual_evidence:
            lines.append("structured plan: visual proof=" + " | ".join(self.visual_evidence))
        if self.forbidden_interpretations:
            lines.append("structured plan: reject=" + " | ".join(self.forbidden_interpretations))
        lines.append(
            "structured plan: composition="
            f"{self.composition.anomaly_scale}, {self.composition.placement}, {self.composition.frame_share}"
            + (f", scale reference={self.composition.scale_reference}" if self.composition.scale_reference else "")
        )
        return lines


@dataclass
class CompilationResult:
    text: str
    plan: StructuredRenderPlan
    warnings: List[str] = field(default_factory=list)
    ok: bool = True


DEFAULT_FORBIDDEN = {
    "displacement": ["the replacement merely beside the original", "both the original and replacement visible"],
    "material_substitution": ["the new material shown beside the target", "a coating that hides the target's form"],
    "scale_violation": ["an ordinary-sized target described only with the word enormous", "everything enlarged together"],
    "hybridization": ["two separate objects touching", "a collage with a visible seam"],
    "inversion": ["a picture or model of the contained world", "ordinary contents inside the opening"],
    "animation_petrification": ["a statue standing beside the living subject", "a surface filter without physical material"],
    "multiplication": ["different instances rather than exact copies", "copies without their own shadows"],
    "behavior_transfer": ["a literal prop made from the borrowed material", "a small ordinary action instead of a changed physical law"],
}


def _unique(items: Sequence[str], limit: int = 8) -> List[str]:
    found = []
    for item in items:
        text = re.sub(r"\s+", " ", str(item or "")).strip().strip(".")
        if text and text.lower() not in {entry.lower() for entry in found}:
            found.append(text)
    return found[:limit]


def _entity_terms(items: Sequence[str]) -> List[str]:
    """Full removed descriptions plus their head nouns, because the source idea may use a shorter wording."""
    terms = []
    for item in items:
        text = re.sub(r"^(?:a|an|the|some)\s+", "", str(item or "").strip(), flags=re.I)
        if not text:
            continue
        terms.append(text)
        first_segment = re.split(r"\s+(?:on|with|in|at|under|over|beside|near|holding)\s+|,", text, maxsplit=1)[0]
        words = re.findall(r"[A-Za-z][A-Za-z'-]+", first_segment)
        if words:
            terms.append(words[-1])
    return _unique(terms, 16)


def _sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return ""
    text = text[:1].upper() + text[1:]
    return text if text[-1:] in ".!?" else text + "."


def _evidence_sentence(plan: StructuredRenderPlan) -> str:
    evidence = _unique(plan.visual_evidence, 4)
    if not evidence:
        return ""
    if len(evidence) == 1:
        return _sentence(evidence[0])
    return _sentence(", ".join(evidence[:-1]) + ", and " + evidence[-1])


def _clean_context(context: str, suppress: Sequence[str]) -> Tuple[str, List[str]]:
    """Drop whole clauses that name removed entities. Never perform a noun-level deletion that leaves broken prose."""
    if not context:
        return "", []
    pieces = re.split(r"(?<=[.!?;])\s+|(?<=,)\s+(?=(?:and|with|beside|near|under|over|holding|wearing)\b)", context)
    kept, dropped = [], []
    for piece in pieces:
        if named_terms(piece, suppress):
            dropped.append(piece.strip())
        else:
            kept.append(piece.strip())
    cleaned = " ".join(piece for piece in kept if piece)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;")
    if cleaned and cleaned[-1:] not in ".!?":
        cleaned += "."
    return cleaned, dropped


def _compile_displacement(plan: StructuredRenderPlan) -> List[str]:
    return [_sentence(plan.anomaly), _evidence_sentence(plan), _sentence(plan.preserved_scene)]


def _compile_material(plan: StructuredRenderPlan) -> List[str]:
    return [_sentence(plan.anomaly), _evidence_sentence(plan), _sentence(plan.preserved_scene)]


def _compile_scale(plan: StructuredRenderPlan) -> List[str]:
    evidence = list(plan.visual_evidence)
    if plan.composition.scale_reference:
        evidence.append(f"its scale is visibly measured against {plan.composition.scale_reference}")
    return [_sentence(plan.anomaly), _evidence_sentence(_copy_with_evidence(plan, evidence)), _sentence(plan.preserved_scene)]


def _compile_behavior(plan: StructuredRenderPlan) -> List[str]:
    return [_sentence(plan.anomaly), _evidence_sentence(plan), _sentence(plan.preserved_scene)]


def _copy_with_evidence(plan: StructuredRenderPlan, evidence: Sequence[str]) -> StructuredRenderPlan:
    return StructuredRenderPlan(
        operation=plan.operation,
        anomaly=plan.anomaly,
        ordinary_scene=plan.ordinary_scene,
        preserved_scene=plan.preserved_scene,
        target=plan.target,
        replacement=plan.replacement,
        preserved_properties=list(plan.preserved_properties),
        suppress_entities=list(plan.suppress_entities),
        suppress_properties=list(plan.suppress_properties),
        visual_evidence=list(evidence),
        forbidden_interpretations=list(plan.forbidden_interpretations),
        composition=plan.composition,
        law=plan.law,
        edit_instruction=plan.edit_instruction,
    )


COMPILERS = {
    "displacement": _compile_displacement,
    "material_substitution": _compile_material,
    "scale_violation": _compile_scale,
    "behavior_transfer": _compile_behavior,
}


def build_render_plan(
    *,
    operation: str,
    anomaly: str,
    idea: str,
    inventory: Optional[SceneInventory] = None,
    preserved_scene: str = "",
    target: str = "",
    replacement: str = "",
    preserved_properties: Sequence[str] = (),
    suppress_entities: Sequence[str] = (),
    suppress_properties: Sequence[str] = (),
    visual_evidence: Sequence[str] = (),
    forbidden_interpretations: Sequence[str] = (),
    composition: Optional[CompositionPlan] = None,
    law: str = "",
    edit_instruction: str = "",
) -> StructuredRenderPlan:
    ordinary_scene = inventory.preserved_scene if inventory is not None else idea
    context = preserved_scene or ordinary_scene
    context, _dropped = _clean_context(context, suppress_entities)
    forbidden = list(forbidden_interpretations) + DEFAULT_FORBIDDEN.get(operation, [])
    return StructuredRenderPlan(
        operation=operation,
        anomaly=re.sub(r"\s+", " ", anomaly or "").strip(),
        ordinary_scene=ordinary_scene,
        preserved_scene=context,
        target=target,
        replacement=replacement,
        preserved_properties=_unique(preserved_properties),
        suppress_entities=_entity_terms(suppress_entities),
        suppress_properties=_unique(suppress_properties, 12),
        visual_evidence=_unique(visual_evidence),
        forbidden_interpretations=_unique(forbidden),
        composition=composition or CompositionPlan(),
        law=law,
        edit_instruction=edit_instruction,
    )


def compile_render_plan(plan: StructuredRenderPlan) -> CompilationResult:
    if not plan.anomaly:
        return CompilationResult("", plan, ["structured compiler received no visible anomaly"], ok=False)
    compile_operation = COMPILERS.get(plan.operation)
    parts = compile_operation(plan) if compile_operation else [
        _sentence(plan.anomaly),
        _evidence_sentence(plan),
        _sentence(plan.preserved_scene),
    ]
    text = " ".join(part for part in parts if part)
    text = re.sub(r"\s+", " ", text).strip()
    warnings = []

    named = named_terms(text, plan.suppress_entities)
    if named and plan.preserved_scene:
        plan.preserved_scene, dropped = _clean_context(plan.preserved_scene, named)
        if dropped:
            warnings.append("structured compiler dropped context naming removed entities: " + " / ".join(dropped[:3]))
        parts = compile_operation(plan) if compile_operation else [
            _sentence(plan.anomaly),
            _evidence_sentence(plan),
            _sentence(plan.preserved_scene),
        ]
        text = re.sub(r"\s+", " ", " ".join(part for part in parts if part)).strip()
        named = named_terms(text, plan.suppress_entities)
    if named:
        return CompilationResult(
            "",
            plan,
            warnings + ["structured compiler refused a prompt naming removed entities: " + ", ".join(named)],
            ok=False,
        )
    grammar = lint_render(text)
    if grammar:
        return CompilationResult("", plan, warnings + grammar, ok=False)
    return CompilationResult(text, plan, warnings, ok=True)
