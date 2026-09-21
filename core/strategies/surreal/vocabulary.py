"""
The fixed vocabulary of the surreal engine: generator modes, operations, registers, charges, the ban-list.

Two ideas govern everything here (see docs/SURREAL_GUIDE.md for the research behind them):

  1. A surreal image is ONE impossibility held against an otherwise credible world. The successful
     surrealists worked by procedure - a generator that supplies something unplanned, then a critic that
     selects and finishes with full craft - and not by trying to be strange.
  2. Affinity beats distance (Magritte's own correction of his early work; Reverdy before him): the
     strongest shock joins two things that are far apart and yet secretly bound, by shape, function,
     material or a word. Random pairing is weak.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

AUTO = "auto"
NONE = "none"


@dataclass(frozen=True)
class Operation:
    id: str
    what: str            # one line, shown in tooltips and in the `why` output
    lineage: str
    impossible: bool = True   # False = nothing impossible is depicted


OPERATIONS: Dict[str, Operation] = {op.id: op for op in [
    Operation("displacement", "an ordinary object where it has no business being", "Magritte, Lautreamont"),
    Operation("scale_violation", "one thing at the wrong size, everything else correct", "Magritte"),
    Operation("hybridization", "two things fused at a logical seam, best frozen mid-change", "Magritte, Ernst"),
    Operation("material_substitution", "right form, wrong substance", "Oppenheim, Dali"),
    Operation("physics_negation", "one law suspended, all others intact", "Magritte, Varo"),
    Operation("inversion", "container and contained, inside and outside, swap", "Magritte, Escher"),
    Operation("double_image", "one form honestly readable two ways", "Dali, Arcimboldo"),
    Operation("animation_petrification", "the inanimate lives, or the living becomes object", "Ernst, Bellmer, Tanning"),
    Operation("absence", "the veiled face, the shadow with no caster", "Magritte, de Chirico"),
    Operation("metaphysical_space", "empty arcades, long wrong shadows, stopped time", "de Chirico, Sage, Tanguy"),
    Operation("literalized_language", "an idiom rendered straight", "Magritte, Carrington"),
    Operation("multiplication", "one thing too many times, identical", "Magritte, Kusama"),
    Operation("working_machine", "an impossible machine that looks as if it works", "Varo"),
    Operation("temporal", "video: one thing wrong in time, everything else in ordinary time", "Cocteau, Deren"),
    Operation("found_strange", "nothing impossible: hour, emptiness, stillness, a withheld story", "Atget, Crewdson", impossible=False),
    Operation("process_estrangement", "nothing impossible: an ordinary subject, one photographic process", "Man Ray, Lee Miller", impossible=False),
]}


@dataclass(frozen=True)
class Mode:
    id: str
    source: str
    what: str
    needs_llm: bool = False     # the generator itself is a question put to an LLM


MODES: Dict[str, Mode] = {mode.id: mode for mode in [
    Mode("affinity_search", "Magritte", "finds a partner that is far in domain yet bound to the subject by shape, material or function"),
    Mode("problem", "Magritte", "poses 'the problem of X': lists X's defining properties, then the ONE substitution that exposes one of them", needs_llm=True),
    Mode("read_the_noise", "Ernst", "draws unrelated fragments and asks what single, seamless scene they are"),
    Mode("double_reading", "Dali", "two things with the same silhouette, one form that is honestly both"),
    Mode("working_machine", "Varo", "a mechanism, a feedstock and a product, joined by a causal chain that looks functional"),
    Mode("archive_composite", "Uelsmann, Maar", "joins fragments from YOUR iconography file and prompt database, never from stock"),
    Mode("found_strange", "Atget, Crewdson", "no anomaly at all: hour, emptiness, stillness, a story that is withheld"),
    Mode("process_estrangement", "Man Ray, Miller", "an ordinary subject and one photographic process"),
]}

MODE_CHOICES: List[str] = [AUTO] + list(MODES)
OPERATION_CHOICES: List[str] = [AUTO] + [op for op in OPERATIONS if op not in ("found_strange", "process_estrangement", "working_machine", "double_image")]

# Which operations each strangeness level prefers (weights for the auto choice).
STRANGENESS_CHOICES = ["subtle", "balanced", "overt"]
OPERATION_WEIGHTS: Dict[str, Dict[str, float]] = {
    "subtle": {"absence": 3, "material_substitution": 2, "physics_negation": 2.5, "displacement": 2, "literalized_language": 1,
               "metaphysical_space": 2, "scale_violation": 0.5, "hybridization": 0.5, "inversion": 1, "animation_petrification": 1,
               "multiplication": 0.5, "temporal": 2},
    "balanced": {"absence": 2, "material_substitution": 2.5, "physics_negation": 2, "displacement": 2.5, "literalized_language": 1.5,
                 "metaphysical_space": 1, "scale_violation": 2, "hybridization": 1.5, "inversion": 2, "animation_petrification": 1.5,
                 "multiplication": 1.5, "temporal": 2},
    "overt": {"absence": 1, "material_substitution": 2, "physics_negation": 1.5, "displacement": 2, "literalized_language": 2,
              "metaphysical_space": 0.5, "scale_violation": 3, "hybridization": 2.5, "inversion": 3, "animation_petrification": 2,
              "multiplication": 2.5, "temporal": 2},
}
MODE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "subtle": {"affinity_search": 2, "problem": 2, "read_the_noise": 0.5, "double_reading": 0.5, "working_machine": 0.5,
               "archive_composite": 1, "found_strange": 3, "process_estrangement": 2},
    "balanced": {"affinity_search": 4, "problem": 2.5, "read_the_noise": 1, "double_reading": 1, "working_machine": 1,
                 "archive_composite": 1.5, "found_strange": 1.5, "process_estrangement": 1},
    "overt": {"affinity_search": 4, "problem": 2, "read_the_noise": 1.5, "double_reading": 2, "working_machine": 2,
              "archive_composite": 1.5, "found_strange": 0.3, "process_estrangement": 0.5},
}

# Registers: how the picture is rendered. The default is evidence - a photograph argues with its own impossibility.
REGISTERS: Dict[str, str] = {
    "deadpan photographic": (
        "A plain, sharp, well-exposed photograph of a real place: named focal length, ordinary available or simple studio "
        "light, natural colour, no effects. It must read as evidence."
    ),
    "staged photography": (
        "A large-format staged photograph lit like a film set on a real street or in a real room (Crewdson, Dora Maar's "
        "studio finish): controlled pools of light, deep focus, commercial-grade polish."
    ),
    "academic oil": (
        "Smooth, exact academic oil painting with invisible brushwork (Magritte, Dali, Tanning): catalogue-illustration "
        "sobriety, even light, clean edges."
    ),
    "metaphysical": (
        "De Chirico's register: hard raking late-afternoon light, long shadows, empty architecture, flat saturated planes, "
        "stopped time."
    ),
    "biomorphic": "Tanguy and Sage: smooth invented forms on a bare plain under an even grey sky, rendered with precise shadows.",
    "collage": (
        "Ernst's engraving collage: elements of nineteenth-century steel engravings joined so that no seam can be found, "
        "one consistent hatching and light direction."
    ),
}
REGISTER_CHOICES: List[str] = list(REGISTERS)

# Charge: the emotional source the anomaly serves. An anomaly with no stake in it reads as a gimmick.
CHARGES: Dict[str, str] = {
    NONE: "",
    "dread": "quiet dread: something is about to happen, or has just happened, and nobody in the picture reacts",
    "longing": "longing: distance, a thing out of reach, a place one cannot return to",
    "absurdity": "absurdity held with a perfectly straight face: nobody in the picture finds it odd",
    "grief": "grief: absence made visible, the ordinary world carrying on around it",
    "wonder": "wonder without sweetness: the awe of something too large or too exact to be an accident",
    "tenderness": "tenderness: care taken over something fragile or out of place",
    "menace": "menace in daylight: a threat that is tidy, domestic and calm",
    "desire": "desire: the wanted thing close, displaced onto an object",
}
CHARGE_CHOICES: List[str] = [AUTO] + list(CHARGES)

# What the imitators reach for. Checked in every premise and listed for the rewriter.
BAN_LIST: Tuple[str, ...] = (
    "melting clock", "melting clocks", "floating island", "floating islands", "eye in the sky", "eyes in the sky",
    "staircase to nowhere", "stairs to nowhere", "dreamlike", "dream-like", "dreamy", "ethereal", "whimsical",
    "otherworldly", "mind-bending", "mindbending", "surreal", "surrealist", "surrealism", "fantastical", "magical",
    "mystical", "galaxy", "nebula", "cosmic", "glowing mist", "purple mist", "trippy", "psychedelic", "bizarre", "weird",
)
BAN_LIST_FOR_PROMPT = (
    "melting clocks, floating islands, eyes in the sky, staircases to nowhere, galaxy or nebula fills, gratuitous glow and "
    "mist, and the words surreal, dreamlike, ethereal, whimsical, otherworldly, mind-bending, fantastical, magical, bizarre"
)

# Tags in objects.yaml that describe FORM: a shared form tag is a visual rhyme between two objects.
FORM_TAGS = frozenset({"round", "long", "flat", "hollow", "container", "hinged", "wheeled", "sharp", "coiled", "paired", "soft", "rigid"})
SCALE_TAGS = ("tiny", "handheld", "tabletop", "furniture", "large")
MATERIAL_TAGS = frozenset({"metal", "wood", "glass", "ceramic", "fabric", "paper", "stone", "plastic", "leather", "rubber", "wax", "organic", "bone"})
DOMAIN_TAGS = frozenset({"kitchen", "office", "medical", "nautical", "farm", "music", "lab", "toy", "ritual", "sport", "garden", "workshop",
                         "travel", "clothing", "optics", "timekeeping", "writing", "lighting"})
SUBJECT_TOKEN = "THE SUBJECT"
