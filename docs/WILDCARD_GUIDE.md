# Wildcard and Variation Guide

Wildcards turn one prompt into many. Every enhancer node in this package resolves them before the
LLM sees the text, tells the LLM which elements were picked, and checks that the ones you marked as
exact survived the rewrite. The grammar is the Dynamic Prompts / Impact Pack grammar, so packs you
have already downloaded work as they are, with a few additions on top.

Everything written for the first version of this guide still works: `{animal}`,
`{instrument:piano|guitar|drums}`.

## Where lists live

Put packs in `ComfyUI/models/wildcards`. Every node reads that folder, plus any `wildcards:` entry
in `extra_model_paths.yaml`, with no configuration. The lists that ship with the package are in its
own `wildcards/` folder; see the README there for the search order and what happens when two folders
define the same name (the first folder wins, your pack replaces the shipped list).

`python_embeded\python.exe custom_nodes\video_prompter\dev\scan_wildcard_packs.py` reports on
everything found: unreadable files, names defined twice, references to packs you do not have.

## Syntax

```text
__animal__                       one entry from animal.txt (or animal.yaml)
__light/setups__                 a list inside a folder
__painters__                     depth-agnostic: finds style/painters if no top-level list has that name
__materials__                    a folder name stands for everything inside it (same as __materials/**__)
__camera/**__                    any list under a folder
__colors*__                      glob on the name

{red|green|blue}                 variant: one of these
{3::common|1::rare}              weights
{2$$red|green|blue}              two of them, joined with ", "
{1-3$$ and $$a|b|c|d}            one to three, joined with " and "
{-3$$a|b|c|d}  {2-$$a|b|c|d}     open ranges: up to three / two or more
{@a|b|c}                         cyclical: steps with the node's index instead of rolling

${who=!__person__} ... ${who}    pick once, reuse the same pick
${who=__person__} ... ${who}     store the wildcard, roll it again each time it is used
${mood:calm}                     a variable with a default
__season(place=harbour)__        pass a value into a list that uses ${place}

__objects[metal AND handheld]__  entries of a tagged list that match a tag expression
__[hollow AND antique]__         the same across every tagged list
                                 operators: AND OR NOT XOR and parentheses, in capitals

[if rain : umbrella | sunhat]    conditional on what was PICKED so far ({rain|sun} earlier in the prompt),
[if t=night : neon | sunlight]   or on a variable's value; words you typed yourself do not count
__db:red door__                  a matching prompt from the prompt database

{animal}  {label:a|b|c}          first-version forms, still accepted (legacy_syntax on)
```

Braces that are not wildcards are left alone: JSON prompts pass through untouched, and so does a
single-option brace such as `{word}`.

When a pick lands behind "a" or "an", the article is corrected for it ("a {owl|cat}" reads "an owl"),
by sound where spelling misleads ("a unicorn", "an hour"). Your own words are never changed.

## Concepts, exact words, inspiration

A wildcard pick is an idea, not a string. After the picks are made, the LLM is given a short block
listing them and is free to say each one in whatever words suit the target model: "rusty" may become
"oxidised steel flaking orange at the seams" for a prose model or `rust, corroded metal` for a tag
model. Three bindings decide how tightly a pick is held:

```text
__materials__     concept (default)   the meaning must survive; the wording is the LLM's
__=lora_triggers__  {=a|b}   verbatim  the exact string must survive. For LoRA triggers, names, text to render.
__?moods__          {?a|b}   loose     inspiration only; the LLM may transform or absorb it
```

Verbatim picks are checked in the LLM's answer and added back if it dropped them. The
`wildcard_llm_block` toggle on each node turns the block off, in which case the LLM only sees the
resolved text.

## Seeds

`wildcard_seed` on every enhancer: `-1` rolls fresh picks on every run, `0` or more is reproducible
(same seed, same lists, same picks). The Text-to-Image node uses its own `random_seed` and
`seed_mode` instead. With several variations, variation N uses seed + N.

A fresh roll is not lost: the node's report shows the seed that was drawn, for example
`seed=1739572853 (fresh roll - use this number as the seed to get these picks again)`.

## Nodes

**Wildcard Processor** resolves a prompt with no LLM. Outputs the text, the `llm_instructions` block,
the full record as JSON, and a report. `mode = combinatorial` with a rising `index` walks every
combination in order, which pairs well with sweep workflows.

**Semantic Variation** keeps a prompt's meaning and moves its picks. Each wildcard or `{a|b}` is a
slot; a variation moves every slot to a semantic neighbour inside its own list. `strength` sets how
far (0.1 = the nearest 1% of the list, 0.5 = a quarter of the way out, 1.0 = the far end),
`far_jumps` lets a few slots jump while the rest drift, `variation` numbers are reproducible, and
`avoid_recent` keeps the candidate least like what you generated lately. `direction` and
`direction_amount` lean every move along a named axis (ordinary to uncanny, new to decayed, domestic
to industrial, ...); the axes are example phrases in `variability/directions.yaml`, and your own go
in `variability/directions_user.yaml`. The report shows each slot's lean, so you can see whether an
axis bites on a given list.

**Concept Survival Check** measures whether concept picks survived a rewrite: for each concept it
shows the phrase in the rewritten prompt that carries it and a similarity score, and for verbatim
picks whether the exact words are there. `all_survived` can gate a retry.

Resolving upstream: when a Wildcard Processor or Semantic Variation node does the picking, connect
its `text` to the enhancer's prompt and its `llm_instructions` to the enhancer's
`wildcard_instructions` input. The enhancer then treats those picks exactly like its own.

## Shipped lists worth knowing

`__constraints__` is a deck of constraint cards, one rule that forces the picture to be invented
("lit only from below", "the main subject is present only as a reflection"). `__?observers__` sees the
scene through a particular kind of attention ("as recorded by a forensic photographer..."); use it
with the loose marker so it colours the whole prompt. `objects.yaml`, `spaces.yaml` and
`materials.yaml` are tagged by material, scale, domain and era for tag queries.

## Writing lists

`.txt`: one entry per line, `# comment` lines ignored, optional weight prefix `3::common entry`.
`.yaml`: nested keys form the wildcard path; items are strings or `{text, tags, weight}`. Entries may
contain wildcards themselves. Specific, physical entries ("a barn owl", "soft north-window light from
the left") render far better than adjectives.
