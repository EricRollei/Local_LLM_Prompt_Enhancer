"""
Prompt builders: slot-button composers that write wildcard templates section by section.

    slots.py     builder definitions (builders/*.yaml) and which lists back each slot
    compose.py   composer state -> wildcard template; platform section order
    sections.py  PROMPT_SECTIONS, the bundle builders pass along

No ComfyUI dependency. See docs/PROMPT_BUILDER_GUIDE.md.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from .compose import (DEFAULT_ORDER, MODES, OPTIONAL_SECTIONS, SECTION_LABELS, SECTIONS, ComposerState, Token, base_section, escape_literal,
                      join_pieces, join_sections, order_sections, section_label, section_order, section_seed_offset)
from .layout import LAYOUT_FILE, apply_layout, layout_hide, layout_move, read_layout, write_layout
from .merge import MINE_FOLDER, fold_key, merge_entries, merged_key, merged_path, pick_root, slot_words, write_merged
from .more import more_lists, path_words, section_of
from .sections import PromptSections
from .slots import (MY_BUTTONS_FILE, PERSON_GROUPS, SUBJECT_KINDS, kinds_of, BuilderDef, ListInfo, PartDef, SlotDef, SlotMatcher, builder_from_dict,
                    button_id, clean_button, key_has_terms, leaf_name, load_builders, read_buttons, write_buttons)

__all__ = [
    "MODES", "SECTIONS", "DEFAULT_ORDER", "OPTIONAL_SECTIONS", "SECTION_LABELS", "ComposerState", "Token", "escape_literal", "join_pieces",
    "join_sections", "section_order", "order_sections", "section_label", "section_seed_offset", "base_section",
    "PromptSections",
    "BuilderDef", "PartDef", "SlotDef", "ListInfo", "SlotMatcher", "builder_from_dict", "leaf_name", "load_builders",
    "MINE_FOLDER", "fold_key", "merge_entries", "merged_key", "merged_path", "pick_root", "slot_words", "write_merged",
    "LAYOUT_FILE", "apply_layout", "layout_hide", "layout_move", "read_layout", "write_layout",
    "more_lists", "path_words", "section_of",
    "PERSON_GROUPS", "SUBJECT_KINDS", "kinds_of",
    "MY_BUTTONS_FILE", "button_id", "clean_button", "key_has_terms", "read_buttons", "write_buttons",
]
