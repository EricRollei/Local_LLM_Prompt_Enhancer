"""
Resolution record: what the wildcard engine chose, slot by slot.

This is the bridge between wildcards and the LLM rewriter. Other wildcard tools
hand the LLM a finished string, so the rewriter cannot tell a deliberate random
pick from filler and often drops it. Here every pick is recorded with a binding:

    concept   (default) the MEANING must survive; the LLM chooses wording that
              suits the target platform ("rusty" -> "oxidized steel flaking orange")
    verbatim  ('=')     the exact string must survive (LoRA triggers, names, quoted text)
    loose     ('?')     inspiration only; may be transformed or absorbed

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from .syntax_tree import BINDING_CONCEPT, BINDING_LOOSE, BINDING_VERBATIM


@dataclass
class Slot:
    index: int
    kind: str                      # variant | wildcard | tag_query | provider | variable | conditional | legacy
    source: str                    # raw text of the construct, e.g. "__materials__"
    value: str                     # final resolved text for this slot
    binding: str = BINDING_CONCEPT
    label: Optional[str] = None    # legacy {label:...} name, wildcard name, or variable name
    origin: str = ""               # file (and key) the pick came from
    depth: int = 0
    parent: Optional[int] = None
    in_output: bool = True         # False for picks made while assigning a variable
    option_count: int = 0


def is_filter_note(text: str) -> bool:
    """A warning written by the content filter, the violence filter or the nsfw filter."""
    return text.startswith(("content filter:", "violence filter", "nsfw filter")) or ": content filter:" in text \
        or ": violence filter" in text or ": nsfw filter" in text


@dataclass
class Resolution:
    text: str = ""
    slots: List[Slot] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    seed: Optional[int] = None
    mode: str = "random"
    combination_space: int = 1     # product of option counts met on this path (combinatorial mode)
    fresh_roll: bool = False       # True when no seed was given and the engine drew one (it is in `seed`)
    upstream_instructions: str = ""  # an llm_instructions block handed in from a node earlier in the graph
    blocked: str = ""              # why the content filter blanked this prompt ('' = it did not)

    # -- views ------------------------------------------------------------------
    def top_level_slots(self) -> List[Slot]:
        return [slot for slot in self.slots if slot.depth == 0 and slot.in_output and slot.value]

    def slots_by_binding(self, binding: str) -> List[Slot]:
        if binding == BINDING_VERBATIM:
            # A verbatim pick must survive even when nested inside a concept-bound parent.
            candidates = [slot for slot in self.slots if slot.binding == binding and slot.in_output and slot.value]
        else:
            candidates = [slot for slot in self.top_level_slots() if slot.binding == binding]
        # A variable used twice yields two slots with one value; the LLM needs it once.
        unique: List[Slot] = []
        seen = set()
        for slot in candidates:
            if slot.value not in seen:
                seen.add(slot.value)
                unique.append(slot)
        return unique

    def legacy_replacements(self) -> Dict[str, str]:
        """Same shape the old _process_wildcards returned: {label: chosen}."""
        return {slot.label: slot.value for slot in self.top_level_slots() if slot.label}

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(
            {
                "text": self.text,
                "seed": self.seed,
                "fresh_roll": self.fresh_roll,
                "mode": self.mode,
                "combination_space": self.combination_space,
                "slots": [asdict(slot) for slot in self.slots],
                "variables": self.variables,
                "warnings": self.warnings,
            },
            indent=indent,
            ensure_ascii=False,
        )

    def summary(self) -> str:
        seed_text = f"seed={self.seed}"
        if self.fresh_roll:
            seed_text += " (fresh roll - use this number as the seed to get these picks again)"
        # Filter notes lead the report: what the content / violence filter held back or blocked.
        lines = [f"FILTER: {note}" for note in self.filter_notes()]
        lines.append(f"{len(self.top_level_slots())} slot(s) resolved, mode={self.mode}, {seed_text}")
        for slot in self.top_level_slots():
            name = slot.label or slot.source
            lines.append(f"  [{slot.binding}] {name} -> {slot.value}")
        for warning in self.warnings:
            if not is_filter_note(warning):
                lines.append(f"  warning: {warning}")
        return "\n".join(lines)

    def filter_notes(self) -> List[str]:
        """The warnings the content and violence filters left (re-rolls, blocked prompts, dropped references)."""
        return [warning for warning in self.warnings if is_filter_note(warning)]

    def format_for_llm(self) -> str:
        """
        Instruction block for the rewriter's system or user prompt. Empty string when
        nothing was resolved, so callers can append it unconditionally.
        """
        concept = self.slots_by_binding(BINDING_CONCEPT)
        verbatim = self.slots_by_binding(BINDING_VERBATIM)
        loose = self.slots_by_binding(BINDING_LOOSE)
        if not (concept or verbatim or loose):
            return ""

        lines: List[str] = ["RANDOMLY SELECTED ELEMENTS (chosen on purpose for this run; unusual picks are intentional, do not normalise them):"]
        if concept:
            lines.append("Concepts - keep the MEANING of each, but express it in the wording that works best for the target model:")
            lines.extend(f"  - {slot.value}" for slot in concept)
        if verbatim:
            lines.append("Verbatim - these exact words must appear unchanged in your output, woven into the prompt where "
                         "they belong. They are not text to be rendered in the picture and must not be listed separately:")
            lines.extend(f'  - "{slot.value}"' for slot in verbatim)
        if loose:
            lines.append("Inspiration - optional; transform freely or let them colour the whole:")
            lines.extend(f"  - {slot.value}" for slot in loose)
        return "\n".join(lines)
