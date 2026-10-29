"""
Builder nodes: click slot buttons to drop wildcards into a phrase you write, see the lists behind
them, and fix, subset or exclude entries. Each builder fills one or more prompt sections and hands
them on (PROMPT_SECTIONS) to the next builder, or as text to a Platform Prompt Rewriter.

    Wildcard Prompt Composer      every section in one node: subject, action, setting, lighting, style, camera
    Wildcard Character Composer   the Subject section only: age, occupation, hair, eyes, outfit, pose...

The slot buttons and their lists are defined in builders/<id>.yaml; the panel is drawn by
web/prompt_builder.js. See docs/PROMPT_BUILDER_GUIDE.md.

Author: Eric Hiss (GitHub: EricRollei)
License: Dual License (Non-Commercial and Commercial Use). See LICENSE.
"""

from .prompt_builder_support import PromptBuilderNode


class PromptBuilder(PromptBuilderNode):
    """A whole prompt, section by section: click a section, type between wildcard pills, move on."""
    BUILDER_ID = "prompt"
    DESCRIPTION = ("Build every section of a prompt in one node: Subject, Action, Setting, Lighting, Style, Camera, "
                   "in the platform's order. Lock a section to keep it while re-rolling the rest; mark empty "
                   "sections for the LLM rewriter to write.")


class CharacterBuilder(PromptBuilderNode):
    """One character's look as a phrase: text you type between wildcard pills."""
    BUILDER_ID = "character"
    DESCRIPTION = ("Write the Subject section: type text between wildcard pills (Age, Occupation, Hair color...). "
                   "Click a pill to see its list and fix, subset or exclude entries.")
