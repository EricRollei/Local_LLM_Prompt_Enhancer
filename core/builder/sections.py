"""
PROMPT_SECTIONS: what builder nodes pass to each other.

A Wildcard Character Composer fills `subject`, a Scene Builder `setting` and `lighting`, and so on. Each
builder takes the bundle from the one before it, adds its own sections and passes it on, so the
last builder's `text` output holds the whole prompt in the platform's order.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .compose import join_pieces


@dataclass
class PromptSections:
    sections: Dict[str, str] = field(default_factory=dict)      # section -> resolved text
    templates: Dict[str, str] = field(default_factory=dict)     # section -> wildcard template
    llm_instructions: List[str] = field(default_factory=list)   # one block per builder that resolved wildcards
    sources: List[str] = field(default_factory=list)            # builder labels, upstream first
    nsfw: Optional[int] = None    # the highest nsfw level (0..3) of the builders that made it; None = not said

    def merged_with(self, section_texts: Dict[str, str], templates: Dict[str, str],
                    llm_instructions: str, source: str, nsfw: Optional[int] = None) -> "PromptSections":
        """
        A new bundle: this one, then the given sections (a section both fill is joined, upstream first).
        nsfw: the adding builder's level; the bundle keeps the highest (what content its sections may hold).
        """
        levels = [level for level in (self.nsfw, nsfw) if level is not None]
        merged = PromptSections(dict(self.sections), dict(self.templates),
                                list(self.llm_instructions), list(self.sources), max(levels) if levels else None)
        for section, text in section_texts.items():
            if not text.strip():
                continue
            earlier = merged.sections.get(section, "").strip()
            merged.sections[section] = join_pieces([earlier.rstrip(",") + ",", text]) if earlier else text.strip()
        for section, template in templates.items():
            earlier = merged.templates.get(section, "").strip()
            merged.templates[section] = f"{earlier}, {template}" if earlier else template
        if llm_instructions.strip():
            merged.llm_instructions.append(llm_instructions.strip())
        merged.sources.append(source)
        return merged

    def instructions_text(self) -> str:
        return "\n\n".join(self.llm_instructions)

    @staticmethod
    def coerce(value) -> "PromptSections":
        """Accept a bundle, a plain dict of section -> text, or nothing."""
        if isinstance(value, PromptSections):
            return value
        if isinstance(value, dict):
            return PromptSections(sections={str(k): str(v) for k, v in value.items() if v})
        return PromptSections()
