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
| found strange | Atget, Crewdson | No anomaly: hour, emptiness, stillness, a light without a source, a trace |
| process estrangement | Man Ray, Miller | An ordinary subject and one photographic process |

The operations table from the plan (displacement, scale violation, hybridization, material substitution, physics
negation, inversion, double image, animation / petrification, absence, metaphysical space, literalized language,
multiplication, and for video a temporal one) is the critic's vocabulary for describing a result.

The critic exists twice. The **code critic** is seeded, offline and instant: it filters cliches and explanations
and chooses by score. The **LLM critic** is one call: it names the subject, lists its ordinary attributes, keeps
or rejects each candidate with a reason (an affinity that cannot be said in one short clause is rejected),
carries out the procedure modes, and writes the premise, a restatement, a Magritte-style title that names a
problem and never describes the picture, and counter-terms for the negative prompt. If its answer is unusable
the code critic's choice stands and the `why` output says so.

The output is a **brief**: the idea with the premise appended as plain physical fact, and an instruction block
that travels through the `wildcard_instructions` input every enhancer already has. The block tells the
enhancer's LLM to state the anomaly early as fact, restate it once in other words, keep everything else
rigorously ordinary, render in the chosen register, serve the chosen charge, and never use the ban-list. Its
`Concepts` heading is the one the Concept Survival Check parses, so whether the anomaly survived the rewrite
can be measured.

## Using it

**Surreal Premise node** (`Eric Prompt Enhancers`). Connect `text` to an enhancer's prompt and `llm_instructions`
to its `wildcard_instructions`. `why` shows every candidate, the critic's judgements and the reasoning. `title`
and `negative_additions` are extras.

Controls: `mode` and `operation` (auto, or force one), `count` (1 or 2, never more; a second operation is always
atmosphere-level so both read as one event), `strangeness` (shifts which modes and operations are drawn),
`register` (deadpan photographic by default: a photograph argues with its own impossibility), `charge` (the
emotional source the anomaly serves; an anomaly with no stake reads as a gimmick), `critic` (llm or code),
`seed`, `medium` (video adds anomalies in time), an optional `embedder` (partners far from the idea in meaning
score higher), and `use_archive`.

**The old `surreal` preset** on the three video nodes and `genre_style = surreal` on the Text-to-Image node now
route through the engine with the code critic, seeded like the node's wildcards, so each variation gets its own
operation. If the engine produces nothing the old text is used.

**Your iconography.** Copy `wildcards/iconography.yaml` to `ComfyUI/models/wildcards/iconography.yaml` and fill
it with your own recurring objects, places and motifs. The engine draws from it first, and the archive-composite
mode needs it. Magritte's bowler hat, apple and curtain were a small private vocabulary recombined for decades;
that is what makes a body of work recognisable instead of averaging toward everyone's.

**Lists** in `wildcards/surreal/` (physics, absences, idioms, processes, temporal, found_strange, machines) are
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

## The test protocol for the two-operation limit

In the plan doc: ten subjects, one platform, counts 1, 2 and an uncapped control, four seeds each, scored blind
on legibility, credibility and hold, plus anomaly survival per operation. The Krea2 sweep nodes can run the grid;
the three scores need a human eye. `count` is capped at 2 until that run says otherwise.
