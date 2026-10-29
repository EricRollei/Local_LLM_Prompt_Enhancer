"""
Resolver: walks a parsed syntax tree and produces text plus a resolution record.

Determinism: every random decision goes through one private random.Random(seed).
The global `random` module is never seeded, reseeded or drawn from, so other
nodes in a ComfyUI graph are unaffected. Same seed + same files = same text.

Run modes
    random         weighted random picks
    combinatorial  `index` enumerates combinations: each choice point consumes one
                   mixed-radix digit of the index (weights ignored). The product of
                   the option counts met on the way is reported as combination_space,
                   so a sequencer can walk 0 .. combination_space-1.
Per-construct samplers override the mode: '~' always random, '@' cyclical
(options[cycle_index % n]).

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import random
import re
from typing import Callable, Dict, List, Optional, Tuple, Union

from .boolean_expr import BooleanExpressionError, compile_expression, evaluate
from .library import (NSFW_EXPLICIT, NSFW_LEVELS, VIOLENCE_LEVELS, Entry, WildcardLibrary, nsfw_level,
                      violence_blocked, violence_level)
from .parser import parse
from .record import Resolution, Slot
from .syntax_tree import (
    COUNT_ALL,
    BINDING_CONCEPT,
    SAMPLER_CYCLICAL,
    SAMPLER_RANDOM,
    Conditional,
    Node,
    Provider,
    Sequence,
    Text,
    VariableAssign,
    VariableRef,
    Variant,
    Wildcard,
)

MODE_RANDOM = "random"
MODE_COMBINATORIAL = "combinatorial"
MODES = (MODE_RANDOM, MODE_COMBINATORIAL)

MAX_DEPTH = 30
_FALSY = {"", "0", "false", "no", "none", "off"}

# provider(argument, text_so_far, rng) -> replacement text, or None when it cannot fill the slot
ProviderCallable = Callable[[str, str, random.Random], Optional[str]]


class PickContext:
    """
    What a pick hook sees at one choice point. A hook may return a replacement list of indices
    into `candidates` (same length as `chosen`), or None to keep the engine's own pick.
    Used by core/variability to move a pick to a semantic neighbour without touching the grammar.
    """

    __slots__ = ("kind", "key", "source", "candidates", "chosen", "depth", "binding", "rng")

    def __init__(self, kind: str, key: str, source: str, candidates: List[str], chosen: List[int],
                 depth: int, binding: str, rng: random.Random):
        self.kind = kind              # "wildcard" | "variant"
        self.key = key                # wildcard name / tag query, or "" for an inline variant
        self.source = source          # raw construct text, e.g. "__materials__"
        self.candidates = candidates  # raw text of every entry or option that could have been picked
        self.chosen = chosen          # indices the engine picked
        self.depth = depth
        self.binding = binding
        self.rng = rng


PickHook = Callable[[PickContext], Optional[List[int]]]

# A variable holds resolved text plus its binding (immediate) or an unresolved tree (deferred).
_VariableValue = Union[Tuple[str, str], Sequence]


class _Chooser:
    """All selection logic in one place, so random / combinatorial / cyclical stay consistent."""

    def __init__(self, rng: random.Random, mode: str, index: int, cycle_index: int):
        self.rng = rng
        self.mode = mode if mode in MODES else MODE_RANDOM
        self.remaining_index = max(0, int(index))
        self.cycle_index = max(0, int(cycle_index))
        self.combination_space = 1

    def _digit(self, radix: int) -> int:
        self.combination_space *= radix
        digit = self.remaining_index % radix
        self.remaining_index //= radix
        return digit

    def choose_count(self, low: int, high: int, sampler: str) -> int:
        if high <= low:
            return low
        if self.mode == MODE_COMBINATORIAL and sampler != SAMPLER_RANDOM:
            return low + self._digit(high - low + 1)
        return self.rng.randint(low, high)

    def choose(self, weights: List[float], count: int, sampler: str) -> List[int]:
        """Return `count` DISTINCT indices into a list of len(weights)."""
        total = len(weights)
        if total == 0:
            return []
        count = max(0, min(count, total))

        if sampler == SAMPLER_CYCLICAL:
            start = self.cycle_index % total
            return [(start + offset) % total for offset in range(count)]

        available = list(range(total))
        chosen: List[int] = []

        if self.mode == MODE_COMBINATORIAL and sampler != SAMPLER_RANDOM:
            for _ in range(count):
                chosen.append(available.pop(self._digit(len(available))))
            return chosen

        for _ in range(count):
            pool_weights = [max(0.0, weights[i]) for i in available]
            if sum(pool_weights) <= 0:
                pool_weights = [1.0] * len(available)
            picked = self.rng.choices(range(len(available)), weights=pool_weights, k=1)[0]
            chosen.append(available.pop(picked))
        return chosen


class Resolver:
    def __init__(
        self,
        library: WildcardLibrary,
        seed: Optional[int] = None,
        mode: str = MODE_RANDOM,
        index: int = 0,
        cycle_index: int = 0,
        legacy: bool = False,
        providers: Optional[Dict[str, ProviderCallable]] = None,
        variables: Optional[Dict[str, str]] = None,
        pick_hook: Optional[PickHook] = None,
        nsfw="off",
        violence: int = 0,
    ):
        self.library = library
        self.nsfw = nsfw_level(nsfw)                 # 0 off .. 3 explicit (library.NSFW_LEVELS)
        self._nsfw_emptied = False                   # set by _entries_for when the level left nothing
        self.violence = violence_level(violence)     # 0 off .. 3 (library.VIOLENCE_LEVELS)
        self._violence_emptied = False               # set by _entries_for when the filter left nothing
        self._context_keys: List[str] = []      # keys of the lists whose entries are being resolved (innermost last)
        self.pick_hook = pick_hook
        self.rng = random.Random(seed) if seed is not None else random.Random()
        self.chooser = _Chooser(self.rng, mode, index, cycle_index)
        self.legacy = legacy
        self.providers = providers or {}
        self.resolution = Resolution(seed=seed, mode=self.chooser.mode)
        self._initial_variables: Dict[str, _VariableValue] = {
            name: (str(value), BINDING_CONCEPT) for name, value in (variables or {}).items()
        }
        self._entry_cache: Dict[str, Sequence] = {}
        self._output_so_far: List[str] = []

    # -- public -----------------------------------------------------------------
    def resolve_text(self, text: str) -> Resolution:
        tree = parse(text, legacy=self.legacy)
        scope = dict(self._initial_variables)
        self.resolution.text = self._resolve(tree, scope, depth=0, parent=None, in_output=True, track=True)
        self.resolution.combination_space = self.chooser.combination_space
        self.resolution.variables = {
            name: value[0] for name, value in scope.items() if isinstance(value, tuple)
        }
        for warning in self.library.all_warnings():
            if warning not in self.resolution.warnings:
                self.resolution.warnings.append(warning)
        return self.resolution

    # -- dispatch ---------------------------------------------------------------
    def _resolve(self, node: Node, scope: Dict[str, _VariableValue], depth: int,
                 parent: Optional[int], in_output: bool, track: bool = False) -> str:
        if isinstance(node, Text):
            if track:
                self._output_so_far.append(node.text)
            return node.text
        if isinstance(node, Sequence):
            pieces: List[str] = []
            for part in node.parts:
                piece = self._resolve(part, scope, depth, parent, in_output, track)
                if piece and pieces and not isinstance(part, Text):
                    pieces[-1] = agree_article(pieces[-1], piece)
                pieces.append(piece)
            return "".join(pieces)

        if depth > MAX_DEPTH:
            self._warn(f"nesting deeper than {MAX_DEPTH} at {node.source!r}; left as text (a wildcard probably refers to itself)")
            return node.source

        if isinstance(node, Variant):
            result = self._resolve_variant(node, scope, depth, parent, in_output)
        elif isinstance(node, Wildcard):
            result = self._resolve_wildcard(node, scope, depth, parent, in_output)
        elif isinstance(node, Provider):
            result = self._resolve_provider(node, depth, parent, in_output)
        elif isinstance(node, VariableAssign):
            result = self._resolve_assignment(node, scope, depth, parent)
        elif isinstance(node, VariableRef):
            result = self._resolve_reference(node, scope, depth, parent, in_output)
        elif isinstance(node, Conditional):
            result = self._resolve_conditional(node, scope, depth, parent, in_output)
        else:
            result = node.source

        if track:
            self._output_so_far.append(result)
        return result

    # -- helpers ----------------------------------------------------------------
    def _apply_pick_hook(self, kind: str, key: str, source: str, candidates: List[str],
                         chosen: List[int], depth: int, binding: str) -> List[int]:
        """Let the host move a pick. Any hook failure or bad answer keeps the engine's own pick."""
        if self.pick_hook is None or not chosen:
            return chosen
        try:
            replacement = self.pick_hook(PickContext(kind, key, source, candidates, list(chosen), depth, binding, self.rng))
        except Exception as error:
            self._warn(f"pick hook failed at {source}: {error}")
            return chosen
        if (
            replacement is None
            or len(replacement) != len(chosen)
            or len(set(replacement)) != len(replacement)
            or any(not isinstance(i, int) or i < 0 or i >= len(candidates) for i in replacement)
        ):
            return chosen
        return list(replacement)

    def _warn(self, message: str) -> None:
        if message not in self.resolution.warnings:
            self.resolution.warnings.append(message)

    def _open_slot(self, kind: str, source: str, binding: str, depth: int, parent: Optional[int],
                   in_output: bool, label: Optional[str] = None) -> Slot:
        slot = Slot(index=len(self.resolution.slots), kind=kind, source=source, value="", binding=binding,
                    label=label, depth=depth, parent=parent, in_output=in_output)
        self.resolution.slots.append(slot)
        return slot

    def _parse_entry(self, text: str) -> Sequence:
        tree = self._entry_cache.get(text)
        if tree is None:
            tree = parse(text, legacy=False)
            self._entry_cache[text] = tree
        return tree

    def _resolve_entries(self, entries: List[Entry], indices: List[int], scope: Dict[str, _VariableValue],
                         slot: Slot, in_output: bool) -> List[str]:
        values: List[str] = []
        origins: List[str] = []
        for entry_index in indices:
            entry = entries[entry_index]
            # References inside this entry resolve in the entry's own pack first (library same-pack rule).
            self._context_keys.append(entry.key)
            try:
                values.append(self._resolve(self._parse_entry(entry.text), scope, slot.depth + 1, slot.index, in_output).strip())
            finally:
                self._context_keys.pop()
            if entry.origin and entry.origin not in origins:
                origins.append(entry.origin)
        slot.origin = "; ".join(origins)
        return values

    # -- {variant} --------------------------------------------------------------
    def _resolve_variant(self, node: Variant, scope: Dict[str, _VariableValue], depth: int,
                         parent: Optional[int], in_output: bool) -> str:
        single = len(node.options) == 1
        only_body = node.options[0].body if single else None

        if single and not node.has_count and node.label is None:
            # Legacy {category}: a bare name that matches a wildcard file.
            if self.legacy and only_body.is_plain_text():
                name = only_body.plain_text().strip()
                if name and self.library.has(name, nsfw=self.nsfw, context=self._context()):
                    legacy_node = Wildcard(source=node.source, name=name, sampler=node.sampler, binding=node.binding)
                    return self._resolve_wildcard(legacy_node, scope, depth, parent, in_output, kind="legacy")
            # Not a choice at all: keep the braces, still resolve anything inside them.
            return "{" + self._resolve(only_body, scope, depth, parent, in_output) + "}"

        slot = self._open_slot("variant", node.source, node.binding, depth, parent, in_output, label=node.label)

        # Pool size is needed to close an open range ({2-$$...}); for {N$$__wildcard__} the pool is the file.
        draws_from_wildcard = (
            single and node.has_count and len(only_body.parts) == 1 and isinstance(only_body.parts[0], Wildcard)
        )
        wildcard_entries = self._entries_for(only_body.parts[0]) if draws_from_wildcard else []
        pool_size = len(wildcard_entries) if wildcard_entries else len(node.options)
        count_max = pool_size if node.count_max == COUNT_ALL else min(node.count_max, pool_size)
        count_min = min(node.count_min, count_max)
        count = self.chooser.choose_count(count_min, count_max, node.sampler)

        # {2$$__flavours__}: draw several distinct entries from one wildcard.
        if draws_from_wildcard:
            reference = only_body.parts[0]
            entries = wildcard_entries
            if entries:
                slot.kind = "wildcard"
                slot.label = reference.name or reference.tag_expression
                slot.option_count = len(entries)
                child_scope = self._scope_with_params(scope, reference)
                indices = self.chooser.choose([entry.weight for entry in entries], count, node.sampler)
                indices = self._apply_pick_hook("wildcard", slot.label or "", node.source,
                                                [entry.text for entry in entries], indices, depth, node.binding)
                slot.value = node.separator.join(self._resolve_entries(entries, indices, child_scope, slot, in_output))
                return slot.value

        slot.option_count = len(node.options)
        indices = self.chooser.choose([option.weight for option in node.options], count, node.sampler)
        indices = self._apply_pick_hook("variant", node.label or "", node.source,
                                        [option.body.source or option.body.plain_text() for option in node.options],
                                        indices, depth, node.binding)
        values = [
            self._resolve(node.options[option_index].body, scope, depth + 1, slot.index, in_output)
            for option_index in indices
        ]
        slot.value = node.separator.join(values)
        return slot.value

    # -- __wildcard__ -----------------------------------------------------------
    def _context(self) -> str:
        return self._context_keys[-1] if self._context_keys else ""

    def _entries_for(self, node: Wildcard) -> List[Entry]:
        if node.tag_expression:
            entries = self.library.query_tags(node.tag_expression, scope=node.name,
                                              nsfw=self.nsfw, context=self._context())
        else:
            entries = self.library.lookup(node.name, nsfw=self.nsfw, context=self._context())
        if not entries and self.nsfw < NSFW_EXPLICIT and not node.tag_expression \
                and self.library.lookup(node.name, nsfw=NSFW_EXPLICIT, context=self._context()):
            self._nsfw_emptied = True               # the list exists; everything in it is rated above this run
        if self.violence and entries:
            kept = [entry for entry in entries if not violence_blocked(entry.text, entry.key, self.violence)]
            if not kept:
                self._violence_emptied = True
            entries = kept
        if node.exclude and entries:
            banned = {item.casefold() for item in node.exclude}
            kept = [entry for entry in entries if entry.text.strip().casefold() not in banned]
            if not kept:
                self._warn(f"{node.source} excludes every entry; exclusions ignored")
                return entries
            return kept
        return entries

    @staticmethod
    def _scope_with_params(scope: Dict[str, _VariableValue], node: Wildcard) -> Dict[str, _VariableValue]:
        if not node.params:
            return scope
        child = dict(scope)
        for key, value in node.params.items():
            child[key] = (value, BINDING_CONCEPT)
        return child

    def _resolve_wildcard(self, node: Wildcard, scope: Dict[str, _VariableValue], depth: int,
                          parent: Optional[int], in_output: bool, kind: Optional[str] = None) -> str:
        self._violence_emptied = False
        self._nsfw_emptied = False
        entries = self._entries_for(node)
        if not entries and self._nsfw_emptied:
            # The list, or every entry in it, is rated above the run's level ("__lingerie__" at off): dropped
            # from the prompt rather than left as text.
            self._warn(f"nsfw filter ({NSFW_LEVELS[self.nsfw]}): {node.source} dropped - "
                       f"its list or every entry in it is rated above {NSFW_LEVELS[self.nsfw]}")
            return ""
        if not entries and self._violence_emptied:
            # Every entry is in the blocked tier: the reference itself names that content ("__weapons__"), so
            # it is dropped from the prompt rather than left as text.
            self._warn(f"violence filter ({VIOLENCE_LEVELS[self.violence]}): {node.source} dropped - "
                       f"every entry is in the blocked tier")
            return ""
        if not entries:
            if node.tag_expression:
                self._warn(f"no entries match {node.source}; left as text")
            else:
                self._warn(f"wildcard '{node.name}' not found; left as text")
            return node.source

        slot_kind = kind or ("tag_query" if node.tag_expression else "wildcard")
        slot = self._open_slot(slot_kind, node.source, node.binding, depth, parent, in_output,
                               label=node.name or node.tag_expression)
        slot.option_count = len(entries)
        indices = self.chooser.choose([entry.weight for entry in entries], 1, node.sampler)
        indices = self._apply_pick_hook("wildcard", node.name or node.tag_expression or "", node.source,
                                        [entry.text for entry in entries], indices, depth, node.binding)
        child_scope = self._scope_with_params(scope, node)
        slot.value = self._resolve_entries(entries, indices, child_scope, slot, in_output)[0]
        return slot.value

    # -- __db:...__ / __llm:...__ -------------------------------------------------
    def _resolve_provider(self, node: Provider, depth: int, parent: Optional[int], in_output: bool) -> str:
        provider = self.providers.get(node.kind)
        replacement: Optional[str] = None
        if provider is not None:
            try:
                replacement = provider(node.argument, "".join(self._output_so_far), self.rng)
            except Exception as error:  # a provider must never break the run
                self._warn(f"{node.kind} provider failed for {node.source}: {error}")

        slot = self._open_slot("provider", node.source, node.binding, depth, parent, in_output, label=node.kind)
        if replacement:
            slot.value = replacement.strip()
            slot.origin = node.kind
        else:
            # Nobody could fill it now. Keep the instruction readable and flag it, so an LLM
            # rewriter further down the line can fill it in context.
            slot.value = node.argument
            slot.origin = f"{node.kind} (unfilled)"
            self._warn(f"no '{node.kind}' provider filled {node.source}; its instruction text was kept")
        return slot.value

    # -- ${variables} -----------------------------------------------------------
    def _resolve_assignment(self, node: VariableAssign, scope: Dict[str, _VariableValue], depth: int,
                            parent: Optional[int]) -> str:
        if node.immediate:
            binding = BINDING_CONCEPT
            if len(node.value.parts) == 1 and hasattr(node.value.parts[0], "binding"):
                binding = node.value.parts[0].binding
            value = self._resolve(node.value, scope, depth + 1, parent, in_output=False).strip()
            scope[node.name] = (value, binding)
        else:
            scope[node.name] = node.value
        return ""

    def _resolve_reference(self, node: VariableRef, scope: Dict[str, _VariableValue], depth: int,
                           parent: Optional[int], in_output: bool) -> str:
        stored = scope.get(node.name)
        if stored is None:
            if node.default is not None:
                return self._resolve(node.default, scope, depth + 1, parent, in_output)
            self._warn(f"variable '{node.name}' is not defined; left as text")
            return node.source

        if isinstance(stored, tuple):
            value, binding = stored
            slot = self._open_slot("variable", node.source, binding, depth, parent, in_output, label=node.name)
            slot.value = value
            return value

        slot = self._open_slot("variable", node.source, BINDING_CONCEPT, depth, parent, in_output, label=node.name)
        slot.value = self._resolve(stored, scope, depth + 1, slot.index, in_output).strip()
        return slot.value

    # -- [if ...] ---------------------------------------------------------------
    def _resolve_conditional(self, node: Conditional, scope: Dict[str, _VariableValue], depth: int,
                             parent: Optional[int], in_output: bool) -> str:
        try:
            compiled = compile_expression(node.condition)
        except BooleanExpressionError as error:
            self._warn(f"bad condition in {node.source}: {error}; left as text")
            return node.source

        picked_text = " ".join(slot.value for slot in self.resolution.slots if slot.value).lower()

        def term_is_true(term: str) -> bool:
            term = term.strip()
            if "=" in term:
                name, expected = term.split("=", 1)
                stored = scope.get(name.strip())
                return isinstance(stored, tuple) and stored[0].strip().lower() == expected.strip().lower()
            stored = scope.get(term)
            if isinstance(stored, tuple):
                return stored[0].strip().lower() not in _FALSY
            if isinstance(stored, Sequence):
                return True
            return re.search(r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)", picked_text) is not None

        branch = node.then_branch if evaluate(compiled, term_is_true) else node.else_branch
        if branch is None:
            return ""
        return self._resolve(branch, scope, depth + 1, parent, in_output)


# -- output tidying ---------------------------------------------------------------
_SPACE_RUN = re.compile(r"[ \t]{2,}")
_SPACE_BEFORE_PUNCTUATION = re.compile(r"[ \t]+([,.;])(?![\w])")
_DUPLICATE_COMMAS = re.compile(r",(\s*,)+")
_BLANK_LINES = re.compile(r"\n{3,}")
# "A {animal}" + the entry "a raven" -> "A a raven". Keep the entry's article, in the first one's case.
_DOUBLE_ARTICLE = re.compile(r"\b(a|an|the)[ \t]+(a|an|the)\b", re.IGNORECASE)


def _merge_articles(match: "re.Match") -> str:
    first, second = match.group(1), match.group(2)
    return second.capitalize() if first[0].isupper() else second


# "a" / "an" agreement where a pick lands right behind an article: "a {owl|cat}" must not read "a owl".
# Applied ONLY at that boundary, never to the user's own words ("plan a or b" stays as written).
# Spelling only approximates sound, so known exceptions are listed and anything unsure is left alone.
_TRAILING_ARTICLE = re.compile(r"(^|[\s(\[\"'])(a|an|A|An)([ \t]+)$")
_FIRST_WORD = re.compile(r"^[\s\"'(]*([A-Za-z][a-z]+)")
_VOWEL_LETTER_CONSONANT_SOUND = ("uni", "use", "usu", "uti", "ute", "ura", "uro", "eu", "ewe", "one", "once", "ubiq", "uku", "ufo")
_CONSONANT_LETTER_VOWEL_SOUND = ("hour", "honest", "honor", "honour", "heir", "herb")


def agree_article(before: str, value: str) -> str:
    """`before` with its trailing a/an corrected for the word `value` starts with. Unsure -> unchanged."""
    article = _TRAILING_ARTICLE.search(before)
    word = _FIRST_WORD.match(value or "")
    if not article or not word:
        return before
    first = word.group(1).lower()
    if first[0] in "aeiou":
        wants_an = not first.startswith(_VOWEL_LETTER_CONSONANT_SOUND)
    else:
        wants_an = first.startswith(_CONSONANT_LETTER_VOWEL_SOUND)
    current = article.group(2)
    wanted = ("An" if current[0] == "A" else "an") if wants_an else ("A" if current[0] == "A" else "a")
    if wanted == current:
        return before
    return before[:article.start(2)] + wanted + article.group(3)


def tidy(text: str) -> str:
    """Remove the scars that empty picks and variable assignments leave behind. Newlines are kept."""
    text = _DUPLICATE_COMMAS.sub(",", text)
    text = _DOUBLE_ARTICLE.sub(_merge_articles, text)
    text = _SPACE_BEFORE_PUNCTUATION.sub(r"\1", text)
    text = _SPACE_RUN.sub(" ", text)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()
