"""
Wildcard engine for Eric's Prompt Enhancers.

Dynamic Prompts compatible grammar (so existing wildcard packs work) with tag
queries, conditionals, concept/verbatim/loose bindings, provider slots, and a
resolution record the LLM rewriter can read. No ComfyUI or torch dependency.

See parser.py for the grammar, library.py for file formats, record.py for bindings.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from .engine import WildcardEngine, get_engine, split_paths
from .library import Entry, WildcardLibrary
from .parser import parse
from .record import Resolution, Slot
from .resolver import MODE_COMBINATORIAL, MODE_RANDOM, MODES, PickContext, tidy

__all__ = [
    "WildcardEngine", "get_engine", "split_paths", "WildcardLibrary", "Entry", "parse",
    "Resolution", "Slot", "MODE_RANDOM", "MODE_COMBINATORIAL", "MODES", "PickContext", "tidy",
]
