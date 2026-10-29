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

### Special folders inside a pack folder

```text
_nsfw/<pack>/...    NSFW lists, rated explicit. Only a node whose nsfw is explicit uses them; there
                    they answer to their name without the _nsfw/ prefix. _nsfw/suggestive/<pack>/ and
                    _nsfw/nudity/<pack>/ rate a folder lower (see NSFW levels).
_generated/...      lists written by the tools themselves. Always searched.
_prompts/<pack>/... whole prompts, one per line (see Prompt files). Answer only to prompts/... names.
_anything_else/     any other top-level folder starting with "_" is ignored
                    (_duplicates, _quarantine, _cleanup, ...).
```

Lists whose own name rates them (`nsfw_poses.txt`, `sex_act.txt`, a YAML key `clothes/nsfw`, `lingerie.txt`)
are gated by level wherever they sit (see NSFW levels). `__MACOSX`, `.git` and `._` fork files are always skipped.
Entries that pair minor-related and sexual terms are removed at load time in every folder, whatever
the nsfw level says. The same test runs on each finished prompt, where terms from different picks meet,
with explicit sexual terms only (nudity words alone do not count there): a roll that fails is
re-rolled with derived seeds when the picks caused it, and blanked with the reason in the report (or,
for an LLM's rewrite, in the console) when the typed text did or no re-roll passes. It is a plain
word match (no LLM, no VRAM), on by default; `config.json` -> `"wildcards": {"content_filter": false}`
turns both checks off. `<lora:...>` tags inside entries are removed at load time
(`config.json` -> `"wildcards": {"strip_lora": false}` keeps them).

### Renamed and dumped lists

The wildcard review (tools/wildcard_review) can rename a list you keep: a `.txt` is renamed in its folder, a key inside a
YAML / JSON file is written out as its own `.txt` (the old key hidden, the pack file untouched). The old name keeps
working: `_catalog_user.yaml` gets `aliases: {old name: new name}`, so saved workflows and templates still find it.
Its "Move dumped files" step moves dumped files to `_dumped/` (same paths; skipped like every other `_` folder).
Both write a manifest; `python tools/wildcard_review/server.py --undo <manifest>` puts things back. A list's `slot:`
in `_catalog_user.yaml` may name several Composer buttons (a list of ids).

### Prompt files (_prompts)

Lists whose entries are whole prompts live in `_prompts/`, keeping their pack and theme folders
(`dev/move_prompt_lists.py` moved them there; `--undo <manifest>` puts them back). They are their own area:

```text
__prompts/<pack>/<theme>/<file>__   one prompt from that file
__prompts/<pack>/<theme>/*__        one prompt from any file in that folder (and its subfolders)
__prompts/<pack>/<theme>__          the same: a folder name stands for everything in it
```

Nothing else reaches them: a bare name (`__forest__`), an ordinary glob (`__*/forest__`), the Composer's
buttons, More lists, Find and the catalog only ever see the normal lists, so a whole prompt can't land in a
Setting or Style pill. A YAML or JSON file under `_prompts/` is named with its folder in front
(`_prompts/pack/x.yaml` with key `mood/rain` -> `prompts/pack/mood/rain`); a file that is only a list (a JSON
array) is named after the file. `_prompts/_nsfw/...` is rated like `_nsfw/` and answers to `prompts/...`.
Stars, hide, drop and entry ratings work as for any list (saved under the `prompts/...` name).

### NSFW levels

Every node that resolves wildcards has an `nsfw` setting, the same levels as the LoRA cards and the LoRA Suggester:

| Setting | A run uses |
|---|---|
| off (default) | SFW only: no suggestive, nude or explicit lists or entries |
| suggestive | also lingerie, bikinis, underwear, "sexy", "seductive", cleavage ... |
| nudity | also nude, naked, topless, nipples ... |
| explicit | everything, including lists under `_nsfw/` |

off is its own category: to get suggestive content, set suggestive. Lists and entries are rated by a word match
(no LLM, no VRAM), and you can correct any rating:

- **A list** is rated by its folder (`_nsfw/` = explicit; `_nsfw/suggestive/` and `_nsfw/nudity/` rate a folder
  lower; the level folder is not part of the name, so `_nsfw/nudity/pack/poses` answers to `__pack/poses__`), by its
  name below the pack folder (`lingerie`, `underwear`, `bikini` -> suggestive; `nude`, `naked`, `topless` -> nudity;
  `nsfw`, `sex`, `porn`, `fetish` -> explicit), or by the catalog finding explicit content. A list above the run's
  level does not exist for lookups, globs, tag queries or slot buttons.
- **An entry** is rated by its words, so an SFW list can still hold a few suggestive entries and an off run leaves
  just those out. Words that mean something else are exempt ("Garter Snake", "Naked Mole Rat", "nude pumps",
  "a bottomless pit", "summa cum laude").
- **A reference** whose list, or every entry in it, is above the run's level is dropped from the prompt (like the
  violence filter) and the report says `nsfw filter (off): __lingerie__ dropped ...`.
- **Your corrections** go in `_catalog_user.yaml` (see the Catalog section): `nsfw: <level>` on a list, `ratings:` on
  single entries, or a top-level `ratings:` for an entry in every list. The Composer's list viewer writes both: the
  *NSFW level* menu by the stars, and a small menu on every rated entry. Entries the node's level leaves out are
  shown greyed.

The Wildcard Composer passes its level on in `sections`; the LoRA Suggester uses the lowest of what the prompt asks
for, its own `nsfw` setting and the Composer's level. `dev/nsfw_levels_dryrun.py` rates your whole library without
changing anything (report in `dev/logs/nsfw_levels_dryrun.md`, every rated entry in `dev/logs/nsfw_entry_ratings.csv`).

### Violence filter

Every node with `nsfw` also has `violence_filter`, right after it:

| Setting | Held back |
|---|---|
| off (default) | nothing |
| no gore | blood and gore, torture, mutilation, dismemberment, corpses |
| no gore or violent acts | also murder, massacre, execution, stabbing, strangling, suicide / self-harm |
| no violence or weapons | also guns, swords, knives, bombs, battle, war |

It works on wildcard picks: entries whose words fall in the chosen tier (or a lower one) are
skipped, and lists whose name says it (`gore`, `torture`, `violence`, `weapons`, `guns` ...) are
hidden, in the Composer's buttons too. A reference whose entries are all held back is dropped from
the prompt (`a knight holding __weapons__` -> `a knight holding`). Text you type is left as is.

Whatever either filter did (a re-roll, a blocked prompt, a dropped reference) is listed first in the
node's report, one `FILTER: ...` line each. A word match, no model; titles
and names that contain the words ("Corpse Bride") are held back with them.

### Which list a bare name means

`__pose__` is exact first. Inside a pack's own list, a reference resolves in that pack first, so a
template written as `__wildcards/quality__` finds its own pack's `wildcards/quality`. Otherwise
`__pose__` finds lists named `pose` in subfolders; when several packs have one, ONE pack is used
(the highest-priority folder, then the shortest path) and the report names the others. Lists of
different packs are never mixed by accident. To pool on purpose, write `__**/pose__`.
`config.json` -> `"wildcards": {"pool_mode": "legacy"}` restores the old pool-everything lookup.

## Syntax

```text
__animal__                       one entry from animal.txt (or animal.yaml)
__light/setups__                 a list inside a folder
__painters__                     depth-agnostic: finds style/painters if no top-level list has that name
__materials__                    a folder name stands for everything inside it (same as __materials/**__)
__camera/**__                    any list under a folder
__colors*__                      glob on the name
__expression!{furious|sad}__     any entry except these (case-insensitive; markers go first: __=name!{a}__)

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

## The catalog and your curation

The first time a node uses wildcards, a background thread indexes every list into
`_catalog.sqlite` in each wildcard folder (the package's own lists index into `cache/catalogs/`).
Later starts only look at files that changed. For each list it records what kind of list it is
(single items, phrases, full prompts, templates, booru tags), a quality score (clean, short, varied
entries score high; quality boilerplate, weight syntax, broken characters and tiny lists score low),
lists with identical content in other packs, and NSFW found by content: a list full of explicit
words is rated explicit, like one under `_nsfw/`, wherever it sits.

Your own judgement goes in `_catalog_user.yaml` next to the lists. The Wildcard Prompt Composer's list viewer
writes it (stars, Hide list, drop an entry); you can also edit it by hand:

```yaml
lists:
  "mrweazsfwildcardssfw_v30glamour/hair_colors":
    stars: 5                     # ranks it first for slot buttons and ambiguous names
  "cushyswildcard_v6/pose":
    hidden: true                 # never used by a bare name, a glob or a slot; __its/exact/name__ still works
  "thepromptbuilder_v21ponyillustrious/face_expression":
    drop: [Sarcasm, Smug]        # these entries are never picked
  "some_pack/camera":
    nsfw: off                    # the list's NSFW level, overrides folder / name / content (off | suggestive | nudity | explicit)
    ratings: {lace boyshorts: off}   # one entry's level in this list (overrides its words)
ratings:                         # an entry's level in every list
  Naked Mole Rat: off
```

When a bare `__name__` matches lists in several packs, the pack with your stars (else the best
quality score) is used. Turn the whole thing off with `"wildcards": {"catalog": false}` in config.json.

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

**Wildcard Character Composer** (and later Scene / Style builders) writes a prompt section with slot buttons
instead of typed syntax; see [PROMPT_BUILDER_GUIDE.md](PROMPT_BUILDER_GUIDE.md).

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
