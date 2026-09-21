"""
Syntax tree for the wildcard grammar.

The parser (parser.py) turns prompt text into these nodes; the resolver
(resolver.py) walks them. Keeping the tree explicit is what makes nesting,
variables, bindings and a resolution record possible, where the old flat regex
approach could not.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# --- Binding: how the LLM rewriter must treat a resolved slot -----------------
BINDING_CONCEPT = "concept"    # default: meaning must survive, wording is free
BINDING_VERBATIM = "verbatim"  # marker '=': exact string must survive (LoRA triggers, names)
BINDING_LOOSE = "loose"        # marker '?': inspiration only, may be absorbed

BINDING_MARKERS = {"=": BINDING_VERBATIM, "?": BINDING_LOOSE}

# --- Sampler: how one choice point picks --------------------------------------
SAMPLER_DEFAULT = "default"    # follow the run mode (random or combinatorial)
SAMPLER_RANDOM = "random"      # marker '~': always random, even in combinatorial mode
SAMPLER_CYCLICAL = "cyclical"  # marker '@': options[cycle_index % n]

SAMPLER_MARKERS = {"~": SAMPLER_RANDOM, "@": SAMPLER_CYCLICAL}

# count_max value meaning "as many as there are options", from an open range such as {2-$$a|b|c}
COUNT_ALL = -1


@dataclass
class Node:
    """Base class. `source` is the raw text the node was parsed from."""
    source: str = ""


@dataclass
class Text(Node):
    text: str = ""


@dataclass
class Sequence(Node):
    parts: List[Node] = field(default_factory=list)

    def is_plain_text(self) -> bool:
        return all(isinstance(part, Text) for part in self.parts)

    def plain_text(self) -> str:
        return "".join(part.text for part in self.parts if isinstance(part, Text))


@dataclass
class Option:
    body: Sequence = field(default_factory=Sequence)
    weight: float = 1.0


@dataclass
class Variant(Node):
    """{a|b|c}, {2::a|1::b}, {2$$a|b|c}, {1-3$$ and $$a|b|c}, {label:a|b} (legacy)."""
    options: List[Option] = field(default_factory=list)
    count_min: int = 1
    count_max: int = 1
    has_count: bool = False
    separator: str = ", "
    sampler: str = SAMPLER_DEFAULT
    binding: str = BINDING_CONCEPT
    label: Optional[str] = None


@dataclass
class Wildcard(Node):
    """__name__, __dir/name__, __colors*__, __name(k=v)__, __name[tag AND tag]__, __[tag]__."""
    name: str = ""                      # "" when the reference is a pure tag query
    params: Dict[str, str] = field(default_factory=dict)
    tag_expression: Optional[str] = None
    sampler: str = SAMPLER_DEFAULT
    binding: str = BINDING_CONCEPT


@dataclass
class Provider(Node):
    """__db:query__, __llm:instruction__ - filled by a callable the host supplies."""
    kind: str = ""
    argument: str = ""
    binding: str = BINDING_CONCEPT


@dataclass
class VariableAssign(Node):
    """${name=value} (deferred: re-rolled on every use) or ${name=!value} (immediate: rolled once)."""
    name: str = ""
    value: Sequence = field(default_factory=Sequence)
    immediate: bool = False


@dataclass
class VariableRef(Node):
    """${name} or ${name:default}."""
    name: str = ""
    default: Optional[Sequence] = None


@dataclass
class Conditional(Node):
    """[if condition : then | else]"""
    condition: str = ""
    then_branch: Sequence = field(default_factory=Sequence)
    else_branch: Optional[Sequence] = None
