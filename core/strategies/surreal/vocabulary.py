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
    law: str = ""        # the transformation rule this KIND of violation obeys: what may change, what may not
    visible: str = ""    # how the anomaly becomes POSITIVELY visible: what the pixels actually show
    impossible: bool = True   # False = nothing impossible is depicted
    two_stage: bool = False   # can be staged as an ordinary picture plus ONE instruction edit (see STAGING_CHOICES)


OPERATIONS: Dict[str, Operation] = {op.id: op for op in [
    Operation("displacement", "an ordinary object where it has no business being", "Magritte, Lautreamont",
              visible=("the out-of-place object is in full view, sharply lit and correctly scaled, close to the centre of interest"),
              law="Things may appear where they do not belong, unaltered in themselves and correct in size, light and shadow; "
                  "nothing is changed in its nature, and nobody present acknowledges that it is out of place.", two_stage=True),
    Operation("scale_violation", "one thing at the wrong size, everything else correct", "Magritte",
              visible=("the wrongly sized thing shares the frame with something of known size, so the error is measurable by eye"),
              law="Exactly one thing departs from true scale, and it behaves as its new size demands; perspective, light and "
                  "every other object stay exactly correct.", two_stage=True),
    Operation("hybridization", "two things fused at a logical seam, best frozen mid-change", "Magritte, Ernst",
              visible=("the seam is in frame and legible, and both originals stay recognisable in the single object"),
              law="Two things may become one only where their shapes already coincide, and the join is continuous with no seam "
                  "to be found; nothing else in the picture is fused.", two_stage=True),
    Operation("material_substitution", "right form, wrong substance", "Oppenheim, Dali",
              visible=("the wrong substance is read from the surface itself: weave, grain, sheen, and the way the thing sits under its own weight"),
              law="Substance alone may change; every outline, seam, wear mark and proportion stays exact, and the new substance "
                  "behaves as itself under light, weight and touch.", two_stage=True),
    Operation("physics_negation", "one law suspended, all others intact", "Magritte, Varo",
              visible=("the suspended law leaves a positive mark: a gap of air beneath, a shadow in the wrong place, a surface that should have given way and has not"),
              law="One physical law is suspended, for one thing, throughout the picture; every other law and every other object "
                  "behaves exactly as it should, including their shadows."),
    Operation("inversion", "container and contained, inside and outside, swap", "Magritte, Escher",
              visible=("the opening is in frame, and what is inside it is drawn at its own scale with its own light spilling out onto the surroundings"),
              law="Any opening may contain something larger than the thing it is cut into; the opening keeps its own true size, "
                  "and what is inside keeps its own true scale and its own light.", two_stage=True),
    Operation("double_image", "one form honestly readable two ways", "Dali, Arcimboldo",
              visible=("one silhouette with both readings fully drawn, from the single viewpoint of the camera"),
              law="One form may be honestly two things at once from this single viewpoint, both readings complete and fully "
                  "rendered; nothing is blended, faded, doubled or reflected to achieve it."),
    Operation("animation_petrification", "the inanimate lives, or the living becomes object", "Ernst, Bellmer, Tanning",
              visible=("the crossing is on the surface: carved folds and tool marks, or warmth, breath and slackness in a thing that has none"),
              law="Life may cross between the made and the living in one direction only and for one thing; whatever crosses keeps "
                  "its exact form, and everything around it carries on unchanged and unsurprised.", two_stage=True),
    Operation("absence", "the veiled face, the shadow with no caster", "Magritte, de Chirico",
              visible=("an absence needs an EDGE. Draw the clean boundary of what is missing and the surroundings continuing correctly through it; never rely on a thing merely not being there"),
              law="What is missing or covered leaves its exact outline behind and is never explained; everything else is fully "
                  "present, and nothing in the picture acknowledges the gap."),
    Operation("metaphysical_space", "empty arcades, long wrong shadows, stopped time", "de Chirico, Sage, Tanguy",
              visible=("the shadows are the subject: long, hard-edged, drawn as dark shapes on the ground and pointed the wrong way"),
              law="Light, shadow and time in this place follow a rule of their own and hold it consistently across the whole "
                  "frame; every solid object is ordinary, correct and exactly where it should be."),
    Operation("literalized_language", "an idiom rendered straight", "Magritte, Carrington",
              visible=("the figure of speech is built from real material in the frame - actual cord, actual glass, actual weight - and never implied"),
              law="One figure of speech is true here as plain physical fact, in full and without irony; nothing else in the scene "
                  "is figurative, and nobody remarks on it."),
    Operation("multiplication", "one thing too many times, identical", "Magritte, Kusama",
              visible=("every copy is inside the frame at once, evenly placed, each with its own shadow"),
              law="Exactly one kind of thing is subject to repetition; every copy is identical down to its wear and its shadow, "
                  "and nothing else in the picture repeats at all.", two_stage=True),
    Operation("working_machine", "an impossible machine that looks as if it works", "Varo",
              visible=("every linkage is turned to the camera: what goes in, the mechanism, and what comes out, all visible in the one shot"),
              law="Every step of the mechanism is visible and follows from the one before it, and each linkage would work; only "
                  "the chain taken as a whole is impossible."),
    Operation("temporal", "video: one thing wrong in time, everything else in ordinary time", "Cocteau, Deren",
              visible=("the difference in time shows as blur, position or a trail, against things in the same frame that are sharp"),
              law="One thing runs on a time of its own from the first frame to the last; every other motion, and all sound, "
                  "keeps ordinary time, and nothing in the shot reacts to the difference."),
    Operation("causal_reversal", "the effect is present and its cause is absent, or arrives after it", "Magritte, Bunuel",
              visible=("the consequence is rendered at full strength - the soaked ground, the scorch, the pressed dust - and the place its cause should occupy is shown as ordinary empty space"),
              law="Consequences arrive before their causes and are complete; every cause is still to come, and nothing in the "
                  "scene anticipates, explains or reacts to it."),
    Operation("autonomy", "a shadow, reflection or garment acts on its own, against what it belongs to", "Magritte, Svankmajer",
              visible=("the double is drawn in a position its owner is not in, and both are in frame together, so the disagreement between them is what the picture shows"),
              law="Only what is cast by something - a shadow, a reflection, an imprint, a hanging garment - can act on its own; "
                  "the things that cast them cannot, and never react."),
    Operation("taxonomy_error", "the thing is presented as a specimen, classified under the wrong kingdom", "Ernst, Cornell, Broodthaers",
              visible=("the apparatus of classification IS the picture: the case, the pin, the cotton wool, the printed label, the catalogue number, the scale bar"),
              law="Nothing here is physically altered; only the system that classifies it is wrong, and it is applied with "
                  "complete institutional consistency."),
    Operation("found_strange", "nothing impossible: hour, emptiness, stillness, a withheld story", "Atget, Crewdson",
              visible=("with no anomaly to carry it, the picture needs a visible object or a visible light: a thing left where it should not be, or light where there should be none"),
              law="Nothing impossible may appear; the hour, the emptiness, the stillness and the light do all of the work, and "
                  "the story behind the scene is never completed.", impossible=False),
    Operation("process_estrangement", "nothing impossible: an ordinary subject, one photographic process", "Man Ray, Lee Miller",
              visible=("the process is visible across the whole frame as a physical photographic effect - reversed tones, a solarised edge, a contact shadow - never as a filter laid over a normal picture"),
              law="The subject is entirely ordinary and untouched; the estrangement is in the photographic process alone, and it "
                  "is applied evenly across the whole frame.", impossible=False),
    Operation("behavior_transfer", "one thing keeps its identity but obeys the physical behaviour of another material", "Dali, Magritte",
              visible=("the original material remains unmistakable while folds, tension, sag, peeling or another borrowed behaviour "
                       "changes its geometry and leaves a positive contact, shadow or exposed surface"),
              law="Exactly one thing may borrow the physical behaviour of one distant material while keeping its own substance, "
                  "identity and connection to the scene; everything else obeys ordinary physics.", two_stage=True),
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
    Mode("found_strange", "Atget, Crewdson", "no anomaly at all: ONE hour and ONE condition - emptiness, stillness, "
                                             "light or a trace - and a story that is withheld"),
    Mode("process_estrangement", "Man Ray, Miller", "an ordinary subject and one photographic process"),
]}

MODE_CHOICES: List[str] = [AUTO] + list(MODES)
OPERATION_CHOICES: List[str] = [AUTO] + [op for op in OPERATIONS if op not in ("found_strange", "process_estrangement", "working_machine", "double_image")]

# Which operations each strangeness level prefers (weights for the auto choice).
STRANGENESS_CHOICES = ["subtle", "balanced", "overt"]
OPERATION_WEIGHTS: Dict[str, Dict[str, float]] = {
    "subtle": {"absence": 3, "material_substitution": 2, "physics_negation": 2.5, "displacement": 2, "literalized_language": 1,
               "metaphysical_space": 2, "scale_violation": 0.5, "hybridization": 0.5, "inversion": 1, "animation_petrification": 1,
               "multiplication": 0.5, "temporal": 2, "causal_reversal": 2, "autonomy": 2.5, "taxonomy_error": 1,
               "behavior_transfer": 1.5},
    "balanced": {"absence": 2, "material_substitution": 2.5, "physics_negation": 2, "displacement": 2.5, "literalized_language": 1.5,
                 "metaphysical_space": 1, "scale_violation": 2, "hybridization": 1.5, "inversion": 2, "animation_petrification": 1.5,
                 "multiplication": 1.5, "temporal": 2, "causal_reversal": 2, "autonomy": 2, "taxonomy_error": 1.5,
                 "behavior_transfer": 2},
    "overt": {"absence": 1, "material_substitution": 2, "physics_negation": 1.5, "displacement": 2, "literalized_language": 2,
              "metaphysical_space": 0.5, "scale_violation": 3, "hybridization": 2.5, "inversion": 3, "animation_petrification": 2,
              "multiplication": 2.5, "temporal": 2, "causal_reversal": 1.5, "autonomy": 1.5, "taxonomy_error": 2,
              "behavior_transfer": 3},
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

# The transformation rule, or LAW. An operation says what is violated; the law says what GOVERNS the violation -
# what may change, what may not, and how the change behaves. Without it a second anomaly reads as a second idea
# rather than an echo of the first, and the picture reads as random. The law is how an emotion becomes physics:
# grief increases gravity, shame removes faces, desire changes scale.
#
# These are seeds, not final text. The code critic uses one as written; the LLM critic is given one as a starting
# point and writes the law that actually fits the premise it chose.
CHARGE_LAWS: Dict[str, Tuple[str, ...]] = {
    "dread": (
        "Whatever is not being looked at has already moved; anything directly in view stays exactly as it is.",
        "Every surface a person has recently left is still warm and slightly deformed, and no other surface is.",
        "Only what is about to be needed has been set out ready; nothing else in the place has been touched.",
    ),
    "longing": (
        "Only the thing that cannot be reached carries its own light; every other object is lit by the room.",
        "Distance behaves as a material: what is wanted is rendered smaller and more finely detailed than perspective "
        "allows, and nothing else departs from perspective.",
        "Whatever has been left behind holds its full colour, and everything present holds its colour one degree weaker.",
    ),
    "absurdity": (
        "Any procedure in the scene is carried out perfectly correctly upon the wrong object; the procedure itself is never wrong.",
        "One object may stand in for another provided the exchange is treated as routine and size and position are preserved.",
        "The rules of the place are obeyed to the letter and apply to the wrong things.",
    ),
    "grief": (
        "Whatever the missing person touched has gained weight: those objects rest lower and press into what holds them, "
        "and nothing else is affected.",
        "Only the objects belonging to the one who is gone still cast shadows; nothing else in the room casts any.",
        "The space a body would have filled stays open, and everything in the picture is arranged around it.",
    ),
    "wonder": (
        "Anything made by repetition may repeat past the point of possibility, provided every repetition is identical "
        "and fully rendered.",
        "One ordinary material continues without limit in one direction at full detail, and no other material does.",
        "Whatever is built to hold something may hold something of any size, and its own dimensions never change.",
    ),
    "tenderness": (
        "Only what is fragile is exempt from force: it cannot fall, break or be reached by weather; everything else obeys ordinary physics.",
        "Any object that has been handled often has grown soft in exactly the places it was held, and nowhere else.",
        "Whatever is cared for takes the material of the thing that cares for it, and nothing else changes substance.",
    ),
    "menace": (
        "Whatever is domestic and orderly may be made of the wrong material; nothing overtly threatening appears at all.",
        "Every object has been arranged by someone who is not present, and the arrangement is perfect.",
        "Only the things meant to open and close have sealed themselves; everything else is untouched.",
    ),
    "desire": (
        "Only the wanted thing is in true focus at every distance; the rest of the scene obeys the lens.",
        "Proximity governs size: the more a thing is wanted the larger it is rendered, and physical distance no longer affects scale.",
        "Whatever stands in for the wanted thing has warmed, softened or opened, and nothing else has.",
    ),
}
GENERIC_LAWS: Tuple[str, ...] = (
    "Only one class of thing in this picture can change; the class is fixed, and every member of it changes in the same way.",
    "The change crosses one boundary only - body to architecture, cloth to skin, inside to outside - and only where a shape, "
    "a pattern or a material is already shared.",
    "Whatever is transformed keeps its exact outline; substance alone is permitted to change.",
    "The anomaly obeys gravity, light and perspective exactly as an ordinary object of its size would.",
)


def law_seed(charge: str, rng) -> str:
    """One transformation rule to start from, drawn for the charge. Falls back to the generic pool."""
    pool = list(CHARGE_LAWS.get(charge, ())) or list(GENERIC_LAWS)
    return rng.choice(pool)


# The rubric the LLM critic scores its own chosen premise against, 0 to 4 per dimension. The total is not the point:
# the LOWEST dimension is the one revision to make, which turns a vague judgement into a specific repair.
RUBRIC: Dict[str, str] = {
    "reality_anchor": "0 = no stable entry point; 2 = recognisable but generic; 4 = specific, credible, sensuously present",
    "rupture": "0 = no violation, or only an error; 2 = visible but familiar; 4 = decisive, fresh, relational",
    "psychic_pressure": "0 = arbitrary novelty; 2 = a mood or theme is present; 4 = feels compelled, consequences radiate",
    "transformation_rule": "0 = inconsistent accident; 2 = partly legible; 4 = clear enough to infer, strange enough to surprise",
    "formal_unity": "0 = parts compete or detach; 2 = mostly coherent; 4 = every formal choice intensifies the premise",
    "ambiguity": "0 = empty or incomprehensible; 2 = two readings; 4 = several precise, incompatible readings",
    "residual_power": "0 = exhausted at first glance; 2 = some afterimage; 4 = deepens or troubles on return",
    # Added after the 2026-09-21 live run: the critic picked premises that are strange only to someone who knows the
    # story (a man holding a river stone). Deadpan is not the same as invisible; Magritte's anomalies are large,
    # central and lit like everything else.
    "visibility": "0 = strange only if you know the story; 2 = noticed on a second look; 4 = unmistakable in a small thumbnail at a glance",
}

# How the picture is made. one_stage: one prompt carries the anomaly. two_stage: an ORDINARY picture is generated first
# (the realism prior then works for the premise instead of against it) and ONE instruction edit applies the anomaly -
# edit models are trained on exactly replace / make-it-out-of / enlarge / remove, and keep everything else intact.
# The Surreal Premise node always emits the scene prompt and the edit instruction when the operation allows it;
# two_stage additionally restricts the automatic choice to operations that can be staged that way.
STAGING_CHOICES: List[str] = ["one_stage", "two_stage"]

# How a title earns its keep. The title is a second image, never a caption for the first.
TITLE_STRATEGIES: Dict[str, str] = {
    "sideways_association": "adds a second image or a context; never restates what is visible",
    "false_classification": "an archival, zoological, clinical or bureaucratic label, related to the form and not a gag",
    "temporal_clue": "implies a before or an after without completing the story or explaining the cause",
    "ordinary_phrase": "a flat domestic or social phrase that makes an extraordinary event feel routine",
    "poetic_friction": "language set against the image rather than beneath it; never decorative obscurity",
}
TITLE_STRATEGY_CHOICES: List[str] = [AUTO] + list(TITLE_STRATEGIES)
BANNED_TITLES: Tuple[str, ...] = ("untitled", "dream", "the dream", "a dream", "surreal", "surrealism", "reverie", "nightmare")

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
# Not hard-rejected in code, because a mask, a chessboard floor and an empty plain are legitimate material (Bellmer,
# de Chirico, Tanguy, Sage) and the shipped motif lists contain them. They are inherited SIGNALS of the genre, so a
# premise may use one only when the premise would still stand with it removed.
SOFT_BAN_FOR_PROMPT = (
    "the postcard versions of masks, chessboards and empty deserts: use one only if it is doing work that nothing else "
    "could do here, never as a signal that the picture is surreal"
)

# Tags in objects.yaml that describe FORM: a shared form tag is a visual rhyme between two objects.
FORM_TAGS = frozenset({"round", "long", "flat", "hollow", "container", "hinged", "wheeled", "sharp", "coiled", "paired", "soft", "rigid"})
SCALE_TAGS = ("tiny", "handheld", "tabletop", "furniture", "large")
MATERIAL_TAGS = frozenset({"metal", "wood", "glass", "ceramic", "fabric", "paper", "stone", "plastic", "leather", "rubber", "wax", "organic", "bone"})
DOMAIN_TAGS = frozenset({"kitchen", "office", "medical", "nautical", "farm", "music", "lab", "toy", "ritual", "sport", "garden", "workshop",
                         "travel", "clothing", "optics", "timekeeping", "writing", "lighting"})
SUBJECT_TOKEN = "THE SUBJECT"
