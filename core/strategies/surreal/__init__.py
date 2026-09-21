"""
Surreal strategy: a generator / critic procedure grounded in how the surrealists actually worked.
See vocabulary.py for the two governing ideas and docs/SURREAL_GUIDE.md for the research.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from .critic import Verdict, code_choose, critic_messages, parse_critic, violations
from .engine import SurrealEngine, SurrealPlan, SurrealResult, SurrealSettings
from .generators import MODE_GENERATORS, OPERATION_GENERATORS, SECOND_OPERATIONS, Candidate, Context
from .sources import Item, SurrealSources, head_noun, mentioned
from .vocabulary import (
    AUTO, BAN_LIST, CHARGE_CHOICES, CHARGES, MODE_CHOICES, MODES, NONE, OPERATION_CHOICES, OPERATIONS, REGISTER_CHOICES,
    REGISTERS, STRANGENESS_CHOICES, SUBJECT_TOKEN,
)

__all__ = [
    "SurrealEngine", "SurrealSettings", "SurrealPlan", "SurrealResult", "SurrealSources", "Item", "Candidate", "Context",
    "Verdict", "code_choose", "critic_messages", "parse_critic", "violations", "mentioned", "head_noun",
    "MODE_GENERATORS", "OPERATION_GENERATORS", "SECOND_OPERATIONS",
    "AUTO", "NONE", "MODES", "MODE_CHOICES", "OPERATIONS", "OPERATION_CHOICES", "REGISTERS", "REGISTER_CHOICES",
    "CHARGES", "CHARGE_CHOICES", "STRANGENESS_CHOICES", "BAN_LIST", "SUBJECT_TOKEN",
]
