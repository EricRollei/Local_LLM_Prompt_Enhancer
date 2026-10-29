"""
Surreal strategy: a generator / critic procedure grounded in how the surrealists actually worked.
See vocabulary.py for the two governing ideas and docs/SURREAL_GUIDE.md for the research.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from .critic import Verdict, code_choose, critic_messages, parse_critic, violations
from .compiler import CompilationResult, CompositionPlan, StructuredRenderPlan, build_render_plan, compile_render_plan
from .engine import SurrealEngine, SurrealPlan, SurrealResult, SurrealSettings
from .generators import MODE_GENERATORS, OPERATION_GENERATORS, SECOND_OPERATIONS, Candidate, Context
from .lint import SUPPRESS_MARKER, lint_prompt, lint_render, suppress_from_instructions
from .sources import Item, SurrealSources, head_noun, mentioned
from .scene import SceneEntity, SceneInventory, inventory_for_critic, parse_scene_inventory, scene_messages
from .vocabulary import (
    AUTO, BAN_LIST, BANNED_TITLES, CHARGE_CHOICES, CHARGE_LAWS, CHARGES, GENERIC_LAWS, MODE_CHOICES, MODES, NONE,
    OPERATION_CHOICES, OPERATIONS, REGISTER_CHOICES, REGISTERS, RUBRIC, STAGING_CHOICES, STRANGENESS_CHOICES, SUBJECT_TOKEN,
    TITLE_STRATEGIES, law_seed,
)

__all__ = [
    "SurrealEngine", "SurrealSettings", "SurrealPlan", "SurrealResult", "SurrealSources", "Item", "Candidate", "Context",
    "Verdict", "code_choose", "critic_messages", "parse_critic", "violations", "mentioned", "head_noun",
    "MODE_GENERATORS", "OPERATION_GENERATORS", "SECOND_OPERATIONS",
    "AUTO", "NONE", "MODES", "MODE_CHOICES", "OPERATIONS", "OPERATION_CHOICES", "REGISTERS", "REGISTER_CHOICES",
    "CHARGES", "CHARGE_CHOICES", "STRANGENESS_CHOICES", "BAN_LIST", "SUBJECT_TOKEN",
    "CHARGE_LAWS", "GENERIC_LAWS", "law_seed", "RUBRIC", "TITLE_STRATEGIES", "BANNED_TITLES",
    "STAGING_CHOICES", "lint_render", "lint_prompt", "suppress_from_instructions", "SUPPRESS_MARKER",
    "SceneEntity", "SceneInventory", "scene_messages", "parse_scene_inventory", "inventory_for_critic",
    "CompositionPlan", "StructuredRenderPlan", "CompilationResult", "build_render_plan", "compile_render_plan",
]
