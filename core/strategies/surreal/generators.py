"""
The GENERATOR half of the surreal engine: procedures that supply candidate premises the user did not plan.

Every function here takes a Context and returns Candidates. A candidate is a premise stated as plain physical
fact (or, for the two modes that are questions rather than answers, a procedure for an LLM to carry out), the
operation it uses, and the affinity that justifies it. Nothing here calls an LLM; the critic does that.

THE SUBJECT in a premise stands for the main subject of the user's idea. The generators cannot parse the
idea, so they bind to a concrete object only when the idea names one of the listed objects; otherwise the
LLM that writes the prompt resolves THE SUBJECT.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

from .sources import Item, SurrealSources, bare, mentioned
from .vocabulary import OPERATION_WEIGHTS, SUBJECT_TOKEN


@dataclass
class Candidate:
    mode: str
    operation: str
    premise: str = ""             # plain physical fact; may contain THE SUBJECT
    procedure: str = ""           # for modes that are a question put to the LLM
    affinity: str = ""            # the one short clause that binds the two realities
    ingredients: List[str] = field(default_factory=list)
    score: float = 1.0
    personal: bool = False        # uses the user's own iconography
    register_hint: str = ""       # a mode may insist on a register (process estrangement is photographic)

    def line(self) -> str:
        body = self.premise or self.procedure
        bound = f"  [affinity: {self.affinity}]" if self.affinity else ""
        return f"{self.operation}: {body}{bound}"


@dataclass
class Context:
    idea: str
    rng: random.Random
    sources: SurrealSources
    medium: str = "image"                     # image | video
    strangeness: str = "balanced"
    distance: Optional[Callable[[str], float]] = None   # 0..1, how far a phrase is from the idea (embedding); None = unknown

    def pick(self, items: Sequence, count: int = 1) -> List:
        pool = list(items)
        self.rng.shuffle(pool)
        return pool[:count]

    def pick_objects(self, items: Sequence[Item], count: int = 1) -> List[Item]:
        """Like pick, but the user's own iconography is always in the draw: a personal vocabulary beats stock."""
        personal = [item for item in items if item.personal]
        others = [item for item in items if not item.personal]
        self.rng.shuffle(personal)
        self.rng.shuffle(others)
        pool = personal[:max(1, count // 2)] + others
        chosen = pool[:count]
        self.rng.shuffle(chosen)
        return chosen

    def far(self, text: str) -> float:
        """Bonus for a partner that is far from the idea in meaning: distance is what makes an affinity a shock."""
        if self.distance is None:
            return 0.0
        try:
            return max(0.0, min(1.0, float(self.distance(text))))
        except Exception:
            return 0.0


def _shared_clause(first: Item, second: Item) -> str:
    shared = sorted(first.form & second.form)
    if not shared:
        return ""
    words = {"container": "a container", "hollow": "hollow", "round": "round", "long": "long", "flat": "flat", "hinged": "hinged",
             "wheeled": "on wheels", "sharp": "sharp", "coiled": "coiled", "paired": "one of a pair", "soft": "soft", "rigid": "rigid"}
    return "both are " + " and ".join(words.get(tag, tag) for tag in shared[:3])


def _partners(target: Item, objects: Sequence[Item], minimum_shared: int = 1) -> List[Item]:
    """Objects bound to the target by form and separated from it by domain and material: Magritte's egg for the bird."""
    found = []
    for item in objects:
        if item.text == target.text:
            continue
        shared = len(target.form & item.form)
        if shared < minimum_shared:
            continue
        if target.domains and item.domains and target.domains & item.domains:
            continue
        found.append(item)
    return found


# ---- operations that need a partner (the affinity search proper) -----------------------------------
def substitution(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    candidates = []
    objects = context.sources.objects()
    for target in targets[:2]:
        for partner in context.pick_objects(_partners(target, objects, 2) or _partners(target, objects, 1), 3):
            clause = _shared_clause(target, partner)
            candidates.append(Candidate(
                "affinity_search", "displacement",
                premise=(f"Where the {bare(target.text)} should be there is {partner.text} instead, the same size, in the same "
                         f"position, and everything around it treats it as the {bare(target.text)}."),
                affinity=clause, ingredients=[target.text, partner.text], personal=partner.personal,
                score=1.0 + 0.5 * len(target.form & partner.form) + context.far(partner.text) + (1.0 if partner.personal else 0.0),
            ))
    return candidates


def hybridization(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    candidates = []
    objects = context.sources.objects()
    # Only on an object the idea actually contains: fusing two things the user never mentioned would replace the idea.
    for target in targets[:2]:
        for partner in context.pick_objects(_partners(target, objects, 2), 2):
            clause = _shared_clause(target, partner)
            candidates.append(Candidate(
                "affinity_search", "hybridization",
                premise=(f"{target.text.capitalize()} and {partner.text} are a single object: it begins as the {bare(target.text)} "
                         f"and, where their shapes coincide, continues as the {bare(partner.text)}, with no join to be found."),
                affinity=clause, ingredients=[target.text, partner.text], personal=partner.personal or target.personal,
                score=1.0 + 0.5 * len(target.form & partner.form) + context.far(partner.text),
            ))
    return candidates


OPPOSITES = {"hard": "soft", "soft": "hard", "cold": "warm", "warm": "cold", "heavy": "light", "light": "heavy",
             "matte": "reflective", "reflective": "matte"}


def material_substitution(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    candidates = []
    materials = context.sources.items("materials")
    if not materials:
        return candidates
    for target in list(targets[:2]) + [None]:
        hard_target = target is not None and bool(target.materials & {"metal", "glass", "ceramic", "stone", "wood", "bone", "plastic"})
        for material in context.pick(materials, 2):
            is_soft = "soft" in material.tags
            contrast = target is not None and (hard_target == is_soft)
            subject = f"The {bare(target.text)}" if target is not None else SUBJECT_TOKEN
            touch = "soft" if is_soft else "hard"
            candidates.append(Candidate(
                "affinity_search", "material_substitution",
                premise=(f"{subject} is made entirely of {material.text}: every detail of its form is exact and only the "
                         f"substance is wrong."),
                affinity=(f"a thing meant to be {'hard' if is_soft else 'soft'} to the touch, made {touch}" if contrast or target is None
                          else "right form, wrong substance"),
                ingredients=[target.text if target else SUBJECT_TOKEN, material.text],
                score=1.0 + (1.0 if contrast else 0.0) + (0.5 if target is not None else 0.0),
            ))
    return candidates


VAST_THINGS = [
    "a night sky with stars, at its real depth", "the sea, with a horizon and small waves", "a beech forest in autumn",
    "a steady rainstorm under low cloud", "a lit street at night, seen from above", "a wheat field moving under wind",
    "a snow-covered mountain valley", "a harbour at dawn with boats at anchor",
]


def inversion(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    containers = [item for item in targets if item.tags & {"container", "hollow"}]
    candidates = []
    if not containers:
        # No container is named in the idea: bind to an opening the scene already has, rather than importing an object.
        for vast in context.pick(VAST_THINGS, 2):
            candidates.append(Candidate(
                "affinity_search", "inversion",
                premise=(f"Inside the nearest ordinary container or opening already in the scene - a cup, a drawer, a pocket, a doorway - "
                         f"is {vast}: not a picture of it but the thing itself, at full scale, its own light falling out onto the surroundings."),
                affinity="what holds the small now holds the vast", ingredients=[vast], score=1.3,
            ))
        return candidates
    for container in containers[:2]:
        for vast in context.pick(VAST_THINGS, 2):
            candidates.append(Candidate(
                "affinity_search", "inversion",
                premise=(f"Inside the {bare(container.text)} is {vast}: not a picture of it but the thing itself, at full scale, "
                         f"seen through the opening, its own light falling out onto the surroundings."),
                affinity="what holds the small now holds the vast", ingredients=[container.text, vast],
                personal=container.personal, score=1.5 + (0.5 if container in targets else 0.0),
            ))
    return candidates


SCALE_PHRASES = {
    "small": ["small enough to stand on a saucer", "no taller than a matchbox, and complete in every detail", "the size of a thimble"],
    "large": ["as tall as the room, bent under the ceiling", "the size of a house, resting in the street", "filling the room wall to wall, so the door cannot open"],
}


def scale_violation(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    candidates = []
    for target in list(targets[:1]) + [None]:
        small = target is not None and target.scale in ("furniture", "large")
        direction = "small" if small or (target is None and context.rng.random() < 0.4) else "large"
        subject = f"The {bare(target.text)}" if target is not None else SUBJECT_TOKEN
        for phrase in context.pick(SCALE_PHRASES[direction], 1):
            candidates.append(Candidate(
                "affinity_search", "scale_violation",
                premise=f"{subject} is {phrase}; everything else in the scene is its ordinary size, and the light and perspective are consistent.",
                affinity="one thing at the wrong size, everything else correct",
                ingredients=[target.text if target else SUBJECT_TOKEN, phrase], score=1.2 + (0.5 if target is not None else 0.0),
            ))
    return candidates


# Placements are relative to THE SUBJECT, never to furniture the scene may not have (a bus stop has no chair).
PLACEMENTS = ["on the ground at THE SUBJECT's feet", "held in THE SUBJECT's arms the way one holds a child", "exactly where THE SUBJECT is looking",
              "beside THE SUBJECT at the height of its head, resting on nothing visible", "in the exact centre of the scene, in THE SUBJECT's way",
              "in THE SUBJECT's hands, in place of whatever it was holding"]


def displacement(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    candidates = []
    for thing in context.pick_objects(context.sources.objects(), 3):
        placement = context.pick(PLACEMENTS)[0]
        candidates.append(Candidate(
            "affinity_search", "displacement",
            premise=f"{thing.text.capitalize()} is {placement}; it has no business being here, it is perfectly ordinary in itself, and nobody pays it any attention.",
            affinity="", ingredients=[thing.text, placement], personal=thing.personal,
            score=0.8 + context.far(thing.text) + (1.0 if thing.personal else 0.0),
        ))
    return candidates


# ---- operations that come from a list and act on THE SUBJECT ---------------------------------------
def _from_list(context: Context, list_name: str, operation: str, affinity: str, count: int = 2, score: float = 1.2) -> List[Candidate]:
    return [Candidate("affinity_search", operation, premise=item.text[0].upper() + item.text[1:] + ".", affinity=affinity,
                      ingredients=[item.text], score=score)
            for item in context.pick(context.sources.items(list_name), count)]


def physics_negation(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    return _from_list(context, "physics", "physics_negation", "one law suspended, all others intact")


def absence(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    return _from_list(context, "absences", "absence", "what must be there is missing, or covered")


def temporal(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    if context.medium != "video":
        return []
    return _from_list(context, "temporal", "temporal", "one thing wrong in time, everything else in ordinary time", score=1.6)


def literalized_language(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    return [Candidate("affinity_search", "literalized_language",
                      procedure=(f"Stage the idiom '{item.text}' literally, as physical fact, inside the user's scene and applied to "
                                 f"{SUBJECT_TOKEN}. No wink, no caption, nobody in the picture finds it odd. Then state it as one plain sentence."),
                      affinity=f"the phrase '{item.text}' taken at its word", ingredients=[item.text], score=1.0)
            for item in context.pick(context.sources.items("idioms"), 2)]


def multiplication(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    number = context.pick(["three", "five", "seven", "twelve", "several dozen"])[0]
    target = targets[0] if targets else None
    subject = f"The {bare(target.text)}" if target is not None else SUBJECT_TOKEN
    return [Candidate("affinity_search", "multiplication",
                      premise=(f"{subject} appears {number} times in the scene, identical in every detail including pose and wear, "
                               f"evenly spaced, each casting its own shadow."),
                      affinity="one thing too many times, identical", ingredients=[number], score=1.1)]


LIVING_ACTS = ["breathes slowly, its sides rising and falling", "has turned to face THE SUBJECT", "sleeps curled on the floor like an animal",
               "has put down fine roots into the floorboards", "is warm, and leans slightly toward the window"]
HARD_MATERIALS = ["white marble", "grey granite", "unpainted plaster", "weathered bronze", "dry grey wood"]


def animation_petrification(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    candidates = []
    thing = targets[0] if targets else (context.pick_objects(context.sources.objects())[0] if context.sources.objects() else None)
    if thing is not None:
        act = context.pick(LIVING_ACTS)[0]
        candidates.append(Candidate("affinity_search", "animation_petrification",
                                    premise=f"The {bare(thing.text)} is alive: it {act}. It is otherwise an ordinary {bare(thing.text)}.",
                                    affinity="the inanimate lives", ingredients=[thing.text, act], personal=thing.personal, score=1.2))
    material = context.pick(HARD_MATERIALS)[0]
    candidates.append(Candidate("affinity_search", "animation_petrification",
                                premise=(f"{SUBJECT_TOKEN} is a statue of {material}, caught mid-gesture with every fold and hair carved; "
                                         f"the scene around it is living and ordinary."),
                                affinity="the living becomes object", ingredients=[material], score=1.2))
    return candidates


METAPHYSICAL_FACTS = [
    "every shadow is three times too long for the height of the sun", "the shadows fall in two different directions",
    "a clock in the scene shows a time that contradicts the light", "the scene is emptied of everyone but THE SUBJECT",
    "a train crosses the far horizon, its smoke standing still", "flags fly straight out in air that moves nothing else",
]


def metaphysical_space(context: Context, targets: Sequence[Item]) -> List[Candidate]:
    first, second = context.pick(METAPHYSICAL_FACTS, 2)
    return [Candidate("affinity_search", "metaphysical_space", premise=f"{first[0].upper() + first[1:]}, and {second}.",
                      affinity="stopped time in an emptied place", ingredients=[first, second], score=1.1,
                      register_hint="metaphysical")]


OPERATION_GENERATORS: Dict[str, Callable[[Context, Sequence[Item]], List[Candidate]]] = {
    "displacement": lambda context, targets: substitution(context, targets) or displacement(context, targets),
    "scale_violation": scale_violation,
    "hybridization": hybridization,
    "material_substitution": material_substitution,
    "physics_negation": physics_negation,
    "inversion": inversion,
    "animation_petrification": animation_petrification,
    "absence": absence,
    "metaphysical_space": metaphysical_space,
    "literalized_language": literalized_language,
    "multiplication": multiplication,
    "temporal": temporal,
}
# Atmosphere-level operations: the only ones allowed as a SECOND operation, because they can read as part of
# the same event as an object-level one (a stone bird in flight / over a day sky above a night street).
SECOND_OPERATIONS = ("physics_negation", "metaphysical_space", "absence", "temporal")


# ---- the eight modes ---------------------------------------------------------------------------------
def affinity_search(context: Context, operation: str = "auto") -> List[Candidate]:
    targets = mentioned(context.idea, context.sources.objects())
    if operation != "auto" and operation in OPERATION_GENERATORS:
        return OPERATION_GENERATORS[operation](context, targets)
    weights = OPERATION_WEIGHTS.get(context.strangeness, OPERATION_WEIGHTS["balanced"])
    names = [name for name in OPERATION_GENERATORS if weights.get(name, 0) > 0]
    chosen: List[str] = []
    pool = list(names)
    while pool and len(chosen) < 5:
        pick = context.rng.choices(pool, weights=[weights[name] for name in pool], k=1)[0]
        chosen.append(pick)
        pool.remove(pick)
    candidates: List[Candidate] = []
    for name in chosen:
        candidates.extend(OPERATION_GENERATORS[name](context, targets))
    return candidates


def problem(context: Context, operation: str = "auto") -> List[Candidate]:
    return [Candidate(
        "problem", "displacement",
        procedure=(
            f"Magritte's method. Pose 'the problem of {SUBJECT_TOKEN}': list its defining properties - what it is made of, how big "
            f"it is, where it belongs, what it is for, what it always comes with. Then find the ONE substitution that exposes one "
            f"of those properties: the thing secretly bound to {SUBJECT_TOKEN}, as the egg is bound to the birdcage and the leaf to "
            f"the tree. One substitution only; everything else in the scene stays ordinary. State it as one plain sentence."
        ),
        affinity="to be found: it must fit in one short clause, or the candidate is rejected", score=1.6,
    )]


def read_the_noise(context: Context, operation: str = "auto") -> List[Candidate]:
    fragments: List[str] = []
    for name in ("objects", "materials", "spaces", "animals", "weather"):
        items = context.sources.objects() if name == "objects" else context.sources.items(name)
        fragments.extend(item.text for item in context.pick(items, 1))
    if len(fragments) < 3:
        return []
    return [Candidate(
        "read_the_noise", "hybridization",
        procedure=(
            "Ernst's method. These fragments came up by chance and do not belong together: " + "; ".join(fragments) + ". "
            f"Look at them the way Ernst looked at his rubbings until ONE scene appears that they are already part of, with "
            f"{SUBJECT_TOKEN} as its protagonist. Use at least three of them. The result is a single world with one light and one "
            f"perspective, and no seam can be found. Then state what is impossible in it as one plain sentence."
        ),
        affinity="chance supplies, judgment finishes", ingredients=fragments, score=1.2,
    )]


def double_reading(context: Context, operation: str = "auto") -> List[Candidate]:
    objects = context.sources.objects()
    targets = mentioned(context.idea, objects)
    candidates = []
    if not targets:
        shapes = [item.text for item in context.pick(objects, 4)]
        if not shapes:
            return []
        return [Candidate(
            "double_reading", "double_image",
            procedure=(
                f"Dali's method. Find ONE form already in the user's scene - {SUBJECT_TOKEN} itself, or an object or a gap between "
                f"objects - whose silhouette is honestly shared by something from a distant domain. Shapes that came up by chance, to "
                f"try against it: " + "; ".join(shapes) + ". Keep the pair only if each reading is complete from the same viewpoint. "
                f"Then state it as one plain sentence naming both readings."
            ),
            affinity="one silhouette, two complete readings", ingredients=shapes, score=1.0,
        )]
    for first in targets[:1]:
        partners = [item for item in _partners(first, objects, 2) if item.scale == first.scale]
        for second in context.pick_objects(partners, 2):
            clause = _shared_clause(first, second)
            candidates.append(Candidate(
                "double_reading", "double_image",
                premise=(f"One object in the scene is honestly two things at once, {first.text} and {second.text}: each reading is "
                         f"complete and fully rendered, and neither is a blend, a fade or a reflection of the other."),
                affinity=clause, ingredients=[first.text, second.text], personal=first.personal or second.personal,
                score=1.2 + 0.4 * len(first.form & second.form),
            ))
    return candidates


def working_machine(context: Context, operation: str = "auto") -> List[Candidate]:
    parts = [context.pick(context.sources.items(name), 1) for name in ("mechanism", "feedstock", "product")]
    if not all(parts):
        return []
    mechanism, feedstock, product = (part[0].text for part in parts)
    return [Candidate(
        "working_machine", "working_machine",
        premise=(f"{SUBJECT_TOKEN} operates {mechanism}. It is fed with {feedstock} and it produces {product}. Every linkage between "
                 f"what goes in and what comes out is visible, and each step looks as if it would work."),
        affinity="a causal chain that convinces before it is noticed to be impossible",
        ingredients=[mechanism, feedstock, product], score=1.4,
    )]


def archive_composite(context: Context, operation: str = "auto") -> List[Candidate]:
    fragments: List[str] = []
    for name in ("icon_objects", "icon_places", "icon_motifs"):
        fragments.extend(item.text for item in context.pick(context.sources.items(name), 1))
    if context.sources.archive is not None:
        try:
            fragments.extend(context.sources.archive(context.idea, 2))
        except Exception:
            pass
    fragments = [fragment for fragment in fragments if fragment][:4]
    if len(fragments) < 2:
        return []
    return [Candidate(
        "archive_composite", "hybridization",
        procedure=(
            "Uelsmann's post-visualisation, from the user's OWN archive. These fragments come from their earlier work: "
            + "; ".join(fragments) + f". Find the join: one picture in which {SUBJECT_TOKEN} and at least two of these belong to the "
            f"same world, under one light source, one perspective and one grain. Then state what is impossible in it as one plain sentence."
        ),
        affinity="a private vocabulary, recombined", ingredients=fragments, personal=True, score=2.0,
    )]


def found_strange(context: Context, operation: str = "auto") -> List[Candidate]:
    groups = context.pick(["emptiness", "stillness", "light", "trace"], 2)
    hour = context.pick(context.sources.items("hour"), 1)
    parts = [item.text for name in groups for item in context.pick(context.sources.items(name), 1)]
    if not hour or not parts:
        return []
    facts = [hour[0].text] + parts
    return [Candidate(
        "found_strange", "found_strange",
        premise="Nothing impossible happens. " + " ".join(fact[0].upper() + fact[1:] + "." for fact in facts),
        affinity="the strange is found, not made; the story is withheld", ingredients=facts, score=1.4,
        register_hint="staged photography",
    )]


def process_estrangement(context: Context, operation: str = "auto") -> List[Candidate]:
    return [Candidate(
        "process_estrangement", "process_estrangement",
        premise=f"Nothing impossible is shown. {SUBJECT_TOKEN} is entirely ordinary, and the picture is {item.text}.",
        affinity="the process estranges an ordinary subject", ingredients=[item.text], score=1.3,
        register_hint="deadpan photographic",
    ) for item in context.pick(context.sources.items("processes"), 2)]


MODE_GENERATORS: Dict[str, Callable[[Context, str], List[Candidate]]] = {
    "affinity_search": affinity_search,
    "problem": problem,
    "read_the_noise": read_the_noise,
    "double_reading": double_reading,
    "working_machine": working_machine,
    "archive_composite": archive_composite,
    "found_strange": found_strange,
    "process_estrangement": process_estrangement,
}
