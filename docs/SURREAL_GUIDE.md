# Surreal Guide

Version 2 replaces the `surreal` preset's list of style words ("dreamlike, ethereal, magical realism") with a
working procedure. This document says why, what the procedure is, and how to use it.

## Why a style word fails

Image models regress toward the plausible. Ask for "surreal" and you get the averaged look of everything tagged
surreal: purple mist, floating islands, melting clocks. The word names an effect and gives the model nothing to
build it from.

The surrealists who lasted did not imagine strange things and then paint them. Each had a repeatable procedure
with two halves. A **generator** supplied something outside conscious control: chance texture (Ernst's rubbings
of floorboards), a misperception (Magritte's egg in the birdcage), a stock of unrelated negatives (Uelsmann's
contact sheets), a rule. A **critic** then read, selected and finished with full craft. Most generated material
was thrown away. The imitators copied the results and skipped the procedure.

Two findings from the research (`Surrealist methods` tab of the plan) govern the engine:

1. **One anomaly, full credibility.** A single violation with light, perspective, material and craft all
   consistent. Varo's machines look as if they work; Ernst's seams are invisible. Several anomalies at once
   read as a collage of effects and the viewer stops asking why.
2. **Affinity beats distance.** Magritte's own correction of his early work: the shock comes from two things
   secretly bound together (by shape, function, material, a word), not from two things merely far apart.

Two of the strongest photographic modes depict nothing impossible at all (Atget, Crewdson, solarisation): the
strangeness is the hour, the emptiness, the stillness, the process, and a story that is withheld.

## The engine

`core/strategies/surreal/`. Eight generator modes, one shared critic, no ComfyUI dependency.

| Mode | From | What the generator does |
|---|---|---|
| affinity search | Magritte | For an object the idea names, finds partners far in domain yet bound by form (the tag vocabulary of `objects.yaml`) |
| problem | Magritte | A procedure for the LLM: list the subject's defining properties, find the one substitution that exposes one |
| read the noise | Ernst | Draws unrelated fragments and asks for the one seamless scene they are already part of |
| double reading | Dali | Two things with the same silhouette, one form that is honestly both |
| working machine | Varo | Mechanism + feedstock + product, joined by a causal chain that looks functional |
| archive composite | Uelsmann, Maar | Fragments from YOUR iconography file and prompt database, never from stock |
| found strange | Atget, Crewdson | No anomaly: ONE hour and ONE condition - emptiness, stillness, light or a trace |
| process estrangement | Man Ray, Miller | An ordinary subject and one photographic process |

The operations table from the plan (displacement, scale violation, hybridization, material substitution, behaviour
transfer, physics
negation, inversion, double image, animation / petrification, absence, metaphysical space, literalized language,
multiplication, causal reversal, autonomy, taxonomy error, and for video a temporal one) is the critic's
vocabulary for describing a result. The last three come from the transformation atlas in the *Surrealism Field
Manual*: the consequence present without its cause; the shadow, reflection or garment that acts while the thing
that casts it does not; and the object left physically untouched but catalogued as a specimen of the wrong
kingdom. Autonomy is allowed as a second operation, because a shadow behaving on its own echoes an object-level
anomaly rather than competing with it.

### A premise is a picture, not an inventory

`found_strange` originally joined its hour to two independently drawn conditions. Measured over 300 seeds that
gave four and a half unrelated facts per premise — the generator itself producing the prompt soup the method
exists to avoid — and in 33% of draws it paired a daylight hour with a condition that only reads in darkness
("noon with hardly a shadow" and "only one light in the whole scene is on"). Handed two facts that cannot both
be true, the LLM critic would look for the relation joining them and invent one, and nothing downstream could
recover: in the run that exposed this, a telephone receiver became the only light source in a garden at noon.

It now draws ONE hour and ONE condition, and the entries carry a light tag (`dark` / `bright` on the hour,
`needs_dark` on the conditions that are invisible in daylight) so an incompatible pair cannot be drawn at all.
Two hours by three groups also gives the critic six genuinely different candidates where a forced mode used to
yield two near-copies, which matters because the critic's whole job is to reject most of what it is given.
Contradictions measured after the change: none in 300 seeds.

### The law

An operation says what is violated. The **law** says what governs the violation: what may change, what may not,
and how the change behaves. Without one the picture reads as random, and a second anomaly reads as a second idea
instead of an echo - the commonest failure in generated surrealism, and the one the field manual is most
insistent about. Every operation carries its own law, so the law always governs the premise that was actually
chosen; the node's `law` input overrides it and is never touched. The eight charges carry laws of their own -
grief makes what the missing person touched heavier, desire makes what is wanted larger - but these are offered
to the LLM critic as a *suggestion* only, because an emotion does not know which anomaly was picked. The law
reaches the instruction block under its own heading, with the standing order to show the rule in effect, never
state it, and remove anything that does not obey it.

The critic exists twice. The **code critic** is seeded, offline and instant: it filters cliches and explanations
and chooses by score. It cannot check that a second operation obeys the first one's law, and says so in `why`.

The LLM path is now staged. The first call inventories the **ordinary scene**: stable entity ids, visible
attributes, ordinary physical properties, relationships, affordances, subject action, setting, light and
viewpoint. It does not invent an anomaly. The **LLM critic** is the second call. It names the subject, keeps or rejects each
candidate with a reason (an affinity that cannot be said in one short clause is rejected), carries out the
procedure modes, writes the law that fits the premise it chose, and then does the field manual's own critique
step: it scores its draft premise on seven rubric dimensions from 0 to 4 - reality anchor, rupture, psychic
pressure, transformation rule, formal unity, ambiguity, residual power - names the lowest-scoring one, and
rewrites the premise with that one repair applied. The scores, the weakest dimension and the repair are printed
in `why`, so the judgement can be judged. It also picks one of five named title strategies (sideways
association, false classification, temporal clue, ordinary phrase, poetic friction); "Dream", "Untitled" and
anything containing "surreal" are refused. If its answer is unusable the code critic's choice stands and the
`why` output says so; a missing or malformed part - no scores, no repair, an over-long or placeholder law - is
dropped rather than guessed at, and the rest of the verdict is still used.

The critic also returns a structured render plan: target, replacement/material/borrowed behaviour, properties to
preserve, positive visual evidence, likely ordinary interpretations to reject, composition, and a
`preserved_scene` from which replaced entities and properties have already been removed.

An operation-specific compiler turns that plan into the node's **text** output. It never prepends the untouched
idea: doing that restored replaced objects because the platform rewriter is required to keep every noun the user
named. Removed entity descriptions and their head nouns are hard validation failures. Context clauses that name
one are dropped; if the anomaly itself names one or uses substitution grammar, compilation is refused and the
unchanged idea is returned with an explicit error in `why`.

The instruction block travels through the `wildcard_instructions` input every enhancer already has. The block tells the
enhancer's LLM to state the anomaly early as fact, restate it once in other words, keep everything else
rigorously ordinary, render in the chosen register, serve the chosen charge, add no further symbolic objects
(every extra noun competes with the premise, which is how a prompt becomes soup), and never use the ban-list. Its
`Concepts` heading is the one the Concept Survival Check parses, so whether the anomaly survived the rewrite
can be measured.

## Using it

**Surreal Premise node** (`Eric Prompt Enhancers`). Connect `text` to an enhancer's prompt and `llm_instructions`
to its `wildcard_instructions`. `why` shows every candidate, the critic's judgements, the rubric scores and the
reasoning. `title`, `negative_additions` and `law` are extras.

Controls: `mode` and `operation` (auto, or force one), `count` (1 or 2, never more; a second operation is always
atmosphere-level so both read as one event), `strangeness` (shifts which modes and operations are drawn),
`register` (deadpan photographic by default: a photograph argues with its own impossibility), `charge` (the
emotional source the anomaly serves; an anomaly with no stake reads as a gimmick), `critic` (llm or code),
`seed`, `medium` (video adds anomalies in time), an optional `embedder` (partners far from the idea in meaning
score higher), `use_archive`, and `law` (leave blank and the chosen operation's law is used; type one and it is
used verbatim, for instance *only patterned fabric can cross the boundary between a body and a wall*).

**The old `surreal` preset** on the three video nodes and `genre_style = surreal` on the Text-to-Image node now
route through the engine with the code critic, seeded like the node's wildcards, so each variation gets its own
operation. If the engine produces nothing the old text is used.

**Your iconography.** Copy `wildcards/iconography.yaml` to `ComfyUI/models/wildcards/iconography.yaml` and fill
it with your own recurring objects, places and motifs. The engine draws from it first, and the archive-composite
mode needs it. Magritte's bowler hat, apple and curtain were a small private vocabulary recombined for decades;
that is what makes a body of work recognisable instead of averaging toward everyone's.

**Lists** in `wildcards/surreal/` (physics, absences, idioms, processes, temporal, autonomy, reversals,
found_strange, machines, motifs) are
ordinary wildcards too: `__surreal/physics__`. Entries are conditions laid on the user's own scene and say
`THE SUBJECT` for its main subject.

## What a live run showed (2026-09-21, qwen3-4b-2507)

Five ideas, five platforms (Krea 2, FLUX.2, SDXL tags, MiniMax H3 fields), the LLM critic, then the rewriter,
then the survival check with the LLM judge: every premise survived its rewrite, in every format. The critic
rejected candidates for the right reasons ("no affinity with the subject", "too many impossible elements").
What a 4B model gets wrong: it imports things the scene does not have (a chair at a bus stop, since fixed by
making placements relative to the subject), it sometimes rewrites rather than keeps and then reports the wrong
candidate number (now detected), and its own premises can contradict themselves. A 24B or larger model is the
one to use for the critic.

## Phase 1: writing for the image model (2026-10-01)

The 2026-09-21 run showed the idea surviving the rewrite and the picture still coming back ordinary. Three causes,
and what changed (spec: `dev/SURREAL_RENDER_SPEC.md`):

1. **Substitution grammar.** "Where the teacup should be there are boots instead" gives a text encoder a teacup AND
   boots; it keeps nouns and loses the counterfactual. Every candidate now carries a `render` - the result as the
   camera sees it - and the replaced object goes on a `suppress` list the rewriter is told never to name.
   `core/strategies/surreal/lint.py` rejects should be / would be / instead of the / in place of / as if / treats
   it as, and attitudes with no pixels (nobody notices, unnoticed, remains unaware or unfazed), in generator
   output and in the critic's `render`. On the Platform Rewriter's output, attitude clauses are removed and
   substitution grammar or a named suppressed object is reported as a warning.
2. **The anomaly was outvoted.** The block now puts the anomaly FIRST, large in the frame, gives it at least a third
   of the words, asks for a second visible consequence instead of a paraphrase, and drops camera boilerplate
   unless the register needs it.
3. **Conceptual but invisible.** The rubric gains `visibility` (unmistakable in a thumbnail at a glance), and the
   critic is told that deadpan is not the same as small.

**Two-stage.** The node has two new outputs, `scene_prompt` and `edit_instruction`, and a `staging` widget (all
   appended at the end). Generate the ordinary picture from `scene_prompt`, then apply `edit_instruction` with an
   edit model (Qwen-Image-Edit, Flux 2 edit, Kontext, Qwen-Image 2.1 i2i). The edit is filled whenever the
   operation can be done as one edit (displacement, scale, hybridization, material, inversion, petrification,
   multiplication; the LLM critic also writes edits for others when it can). `two_stage` restricts the automatic
   choice to those operations.

### Structured compiler stages (2026-10-18)

1. **Ordinary inventory.** Record the scene before intervention; no surreal invention is allowed.
2. **Generator and critic.** Choose one operation and produce a transformation law plus a structured render plan.
3. **Operation compiler.** Compile only the final transformed scene, anomaly first, with required physical proof
   and no removed entity. Displacement, material substitution, scale violation and behaviour transfer have
   dedicated compilers; the other operations use the shared positive-fact compiler until their own grammar is
   refined from live results.
4. **Platform verbalizer.** The existing enhancer receives the compiled scene and the structured plan. It may
   express that plan in the target model's dialect but may not reinterpret it.

`behavior_transfer` covers cases such as an ocean that remains seawater but forms a stable lifted fold like heavy
fabric. The critic must preserve evidence of the original identity, add evidence of the borrowed behaviour, keep
the surface connected to its scene, and reject the likely normal readings (a handful of water, a splash, or a
literal textile prop).

Two live runs with Mistral Small 3.2 24B as critic and rewriter (`dev/logs/try_surreal_live_p1*.log`): in the first,
8 of 9 premises led with a visible physical fact (the ninth fell back to the code critic) and 7 of 9 came with an
edit instruction; in the second, after fixing the survival check, 9 of 9 survived the rewrite. The survival check
had keyed the judge's verdicts on the exact concept text and lost them whenever the judge echoed a concept slightly
differently, reporting '[none]' for anomalies that were plainly in the prompt.

## The test protocol for the two-operation limit

In the plan doc: ten subjects, one platform, counts 1, 2 and an uncapped control, four seeds each, scored blind
on legibility, credibility and hold, plus anomaly survival per operation. The Krea2 sweep nodes can run the grid;
the three scores need a human eye. `count` is capped at 2 until that run says otherwise.
