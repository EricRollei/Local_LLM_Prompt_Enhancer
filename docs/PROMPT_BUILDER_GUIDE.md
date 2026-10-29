# Wildcard Composer Guide

Builder nodes write a prompt section by section, with buttons instead of typed wildcard syntax.

- **Wildcard Prompt Composer** holds every section in one node: Format, Subject, Action, Setting,
  Light & atmosphere, Composition, Camera and Style & finish (plus Text when you add it), shown in
  the order the chosen platform wants them. Most of the time this is the only builder node you need.
- **Wildcard Character Composer** is the same node limited to the Subject section (with Pose from Action), for
  a character you want to reuse across several Wildcard Prompt Composers or branches.

A Subject phrase, for example:

```text
a [Age] [Occupation] in typical uniform, with dark wrinkled skin, a [Face] and [Hair color] hair
lit by glowing fiery red light, with a [Expression] expression
```

The words are yours; each `[Pill]` is a wildcard. One roll reads: *"a middle-aged adult professor in
typical uniform, with dark wrinkled skin, a gaunt face and cinnamon brown hair lit by glowing fiery
red light, with a thoughtful expression."*

## The panel

**Section strip** (top): the platform's section order, read from the `structure` line of the
platform profile you pick in `platform` (Krea 2: subject with its actions, then setting, light,
medium, framing; FLUX.2: subject, action, style, setting, lighting, technical). Click a section to
work on it; it turns amber. Sections with something in them have a solid outline. `+ Subject` adds
Subject 2 (3, ...), placed right after Subject so each person keeps their own attributes, which is
what Krea 2 asks for. `+ Text` adds the optional Text section (words shown in the picture).

**Your own section order**: drag a section chip onto another to reorder. The node then builds and
joins its sections in that order (saved with the node and its templates) whatever the platform;
**Platform order** goes back to the platform's. The sections and why: dev/PROMPT_TAXONOMY_SPEC.md.

**Prompt frame**: every section of the prompt, one line each, in platform order. Every gap between
pills is a text box; type there. The amber gap is the insert point: click a gap (in any section) to
move it there. Typed text may use wildcard syntax too (`{red|blue}`, `__name__`). A word doubled
across a pill (`auburn hair` + typed `hair`) is written once. Each line has two switches:

- **Lock** keeps that section's picks while the seed moves, so you can hold a character and re-roll
  only the setting (the section is held at the seed it last rolled with; click again to release).
- **LLM fills** asks the Platform Prompt Rewriter to write the section when you leave it empty
  ("a setting that suits the subject"). It needs `llm_instructions` connected to the rewriter's
  `wildcard_instructions`. A section you have written in is used as written.

**Moving wildcards**: drag a pill to a gap (in its own section or another one) to move it there;
drop it on another pill to put it just before that one. The text on either side of where it was
closes up, as when a pill is removed. Clicking a pill opens its list and makes the gap right after
it the insert point, so the next slot button adds a wildcard just after the one you selected.
To add one at the very start, click the small gap before the first pill.

**Slot buttons**: the buttons for the active section (Setting shows Location, Interior, Era,
Weather...), under headings for the Subject (Person, Face & hair, Clothing, Accessories). A button
appears only when your library has at least one list for it, so another user's panel shows fewer
or more buttons depending on their packs; hover a button to see how many lists back it.

**Subject type** (the menu on Subject lines): Person, Animal, Creature, Object, Vehicle or Food
shows that type's buttons (an Animal subject isn't offered Makeup); *Any type* shows them all.
*Scene only* means no subject at all (a landscape, an empty plate for a composite, a storyboard
background): the Subject line is left out of the prompt and the rewriter is told not to add one.

**Arrange** (next to *+ Button*): drag a button onto another button to put it there, onto a group
heading to move it under that heading, or onto a section chip to move it to that section; *hide*
takes it off the palette (Arrange still shows it, to bring it back). The layout is saved in
`builders_user/button_layout.yaml` and applies to every node; **Reset layout** returns to the
shipped one. The shipped `builders/prompt.yaml` is never changed.

**Any · Woman · Man** (on Subject lines, for people): which lists the buttons use for that subject. Lists
named for the other gender are left out and lists named for this one come first (lists named for
neither follow). Switching moves the pills that are still on Random to the best list for the new
choice; pills with picks keep their list. Subject 2 has its own switch. Click one to insert a pill at the amber gap. Its list is the best match in your
library (see *Where the lists come from*); change it in the list viewer.

**One row per pill** of the active section:

| control | what it does | syntax written |
|---|---|---|
| Random | any entry | `__list__` |
| Fixed | always your first pick, or your own text | `{1$$value}` |
| Subset | random among your picks | `{a\|b\|c}` |
| Exclude | random, never your picks | `__list!{a\|b}__` |
| − n + | that many different entries, joined with "and" | `{2$$ and $$…}` |
| Meaning | the LLM polish may reword it, keeping the meaning | (default) |
| Exact | kept word for word (names, LoRA triggers) | `=` marker |
| Loose | inspiration; the LLM may drop it | `?` marker |

The row also shows what the pill rolled for the current seed.

**List viewer** (click a pill or its row). Long lists load 300 entries at a time as you scroll.
Lists rated above off join the source menu at that level, marked with it (`suggestive ·`, `explicit ·`). The
viewer's *NSFW level* menu rates the list, and every rated entry has its own small menu (auto = its words);
entries the node's `nsfw` level leaves out are greyed. Both save to `_catalog_user.yaml`. choose the source list (every list in your library
that matches the slot; lists with identical content are shown once, and each is labelled short,
medium or long by its median entry length), search it, tick entries, then *Fix to first pick*,
*Use picks as subset* or *Exclude picks*. Rate while you look: the stars rate the list (starred lists
come first for that slot everywhere), *Hide list* takes it out of every slot and bare name, and
*drop* on an entry means it is never picked again from that list. All three are saved in
`_catalog_user.yaml` next to the lists, so they apply to every node, not just this one. *Or fix to your own value* sets any text, for example an
exact age such as "7-year-old" or "42-year-old".

**Preview**: exactly what the node outputs for the seed on the node (the same code runs both).
*Re-roll* moves the seed on by one.

## Outputs and chaining

| output | use |
|---|---|
| `sections` | every section filled so far. Connect to the next builder's `sections` input. |
| `text` | all sections as one prompt in the platform's order. Use as is, or connect to a Platform Prompt Rewriter's `idea` for LLM polish. |
| `llm_instructions` | which picks were random and how to keep them. Connect to the rewriter's `wildcard_instructions` so Exact picks survive the rewrite. |
| `template` | the prompt as unresolved wildcard syntax, to save or to let another node roll it. |
| `report` | the picks and any warnings. |

Usually: **Wildcard Prompt Composer** → **Platform Prompt Rewriter** (`idea` ← `text`,
`wildcard_instructions` ← `llm_instructions`).

Chaining is for reuse: one **Wildcard Character Composer** feeding the `sections` input of several
Wildcard Prompt Composers gives the same character in different scenes. A section both nodes fill is joined, the
upstream one first.

### With the LoRA Suggester (Krea2)

| from | to |
|---|---|
| Composer `text` | Platform Prompt Rewriter `idea` |
| Composer `llm_instructions` | Rewriter `wildcard_instructions` |
| Composer `sections` | LoRA Suggester `sections` |
| Rewriter `prompt` | LoRA Suggester `text` |
| LoRA Suggester `prompt_with_triggers` | the Krea2 text encoder |
| LoRA Suggester `suggestions` | Eric Krea2 Multi-LoRA Stack `suggestions` |

The Suggester picks LoRAs from the Composer's separate sections (style and format feed the style role, setting the
environment role, and so on), so the rewriter's prose cannot blur that choice; the trigger words are added after the
rewrite, so the LLM never sees them. The Composer's `nsfw` level travels with `sections` and caps the Suggester too.

Rewriter settings for this: platform **Krea 2**, `official_prompt` **off** (Krea's own prompt expands short prompts;
off uses the profile's rules: keep every subject, add nothing, polish a detailed prompt rather than inflate it,
60-150 words), temperature about 0.5. `extra_instructions` like "name the medium and style in the first sentence"
keeps the style words where Krea2's 512-token limit cannot cut them. The Krea2 Magic Prompt node is a short-prompt
expander: after a Composer it rewrites the picks and pushes the style words to the end.

For variety across a batch, put wildcards in the Style and Format sections (a medium, a movement, a rendering), not
only in the subject: the Suggester's `variety` only reshuffles LoRAs that score close to each other, while a different
style phrase picks a different family of LoRAs. "LLM fills" on the Style section leaves the Suggester nothing to read.

**Sliders.** Slider LoRAs (age, waist, shot size, saturation ...) are not scored like other LoRAs: the Suggester reads
the prompt for phrases that ask for a place on a slider's axis ("wasp waist", "a very old fisherman", "extreme
close-up") and sets that slider to a signed weight. Everyday style words ("detailed", "dark", "comic") are kept below
the firing line so they do not dial anything. The phrases live in the LoRA Catalog tool's `axes.yaml` and
`axes_ladders.yaml`; what every file is, and how to add phrases, calibrate a slider with your own weights or add an
axis: **SLIDERS_AND_AXES.md** in the LoRA Catalog folder. Node widgets: `slider_max`, `slider_range` (used when a
slider's card has no believable range), `slider_min_strength` (1 any cue, 2 the default, 3 only strong asks).

**exclude / pin boxes.** Whole words, one entry per line or comma separated. Plain words match a LoRA's name or file
name; `folder:<words>`, `role:<role>` and `axis:<axis>` (exclude only, except `axis:` pins) widen it. A pin uses one
LoRA, the best match, and may carry a weight: `waist slider=-8`, `axis:age=+3`. The node's tooltips have the full
list, and the report says what each entry matched.

## Where the lists come from

`builders/prompt.yaml` defines the sections and every slot button; `builders/character.yaml`
extends it and keeps the subject and action buttons. A slot finds its lists by name: a list belongs to a slot when its
leaf name (last path segment, lower case, pack prefixes such as `cops_wc_` removed) fully matches one
of the slot's `match` patterns. Your stars rank first, then earlier patterns, then the catalog's
quality score (booru-tag lists rank below prose), then bigger lists; hidden lists are left out. The
viewer's source menu shows each list's stars, size, length or `tags`, and quality (`q85`). Lists
with `lora` in the key are never offered. Lists rated above the node's `nsfw` level (by folder, content, or
words in the key: see the Wildcard guide, NSFW levels) are not offered; the others are marked with their level.

A slot can also take `folders` (regexes searched in the folder part of the key: every list in a
matching folder counts, after `match`) and `search` (words that must all be in the key, see below).
The Name button uses `folders` for packs such as a name megalist whose lists are called
`black - female`.

When a list's own name says nothing a button knows (`basemodel/eye-color/brown`,
`loom/10-lighting/female/soft`), its nearest meaningful folder name is matched instead: generic
folders (`female`, `general`, `v2` ...) are looked past, leading numbers dropped, the pack folder
never used, and only one level up (further up, folders tend to name a whole scene).

## Prompt line (your prompt files)

**+ Prompt** adds a Prompt line; drag its chip like any other line, and put a Setting, Format, a second
Subject or anything else around it. Its button, **Browse prompts.**, opens your prompt files (`_prompts`,
see the Wildcard guide) folder by folder: click a file to read its first prompts, **Use** inserts it,
**Use the whole folder** inserts a pill that draws from every file in that folder. The search box finds
files by name in every folder. Click the pill afterwards to see all its prompts, search them, pick, fix,
exclude or drop some, exactly as with any list; **Browse prompts.** in that window swaps the file. The
Prompt line feeds every role of the LoRA Suggester. A whole prompt often names its own place or style, so
an added Setting can contradict it; the Platform Prompt Rewriter after the Composer smooths that out.

## More lists

**More lists…**, the last button of every palette, shows the usable lists no button above offers:
word, phrase and tag lists with 3+ entries (whole prompts and templates stay with Find). Each gets
a section from the catalog's reading of its content, or from words in its path, and a group from
the path word it shares with the most other lists (Makeup, Creature, Food ...). Click a group, then
a list to insert it; ☆ saves one list as a button, **☆ Button for all N lists** saves the group.
Lists with identical content are shown once.

## Find, and your own buttons

The **Find** box next to the section heading searches every list: first lists whose key has all your
words, then (when the catalog is built) lists whose entries match. Click a result to insert that
list at the amber gap; the pill is labelled with the list's name. The Woman / Man switch of the
section filters Find too.

Save what you find as a button, under **My buttons** at the top of the section's palette:

* **☆ Button** on a result (or in a pill's list viewer): a button for that one list.
* **☆ Button for "words"** at the foot of the results, or **+ Button**: a category button. It
  offers every list whose key has all the words, folders included, now and as you add packs.
  A word of 4+ letters may sit inside a longer one (`names` finds `peoplenamemegalist`), a plural
  `s` is optional, and gender words (`female`, `men`, ...) follow the list's gender, so `male` does
  not find female lists. The editor shows how many lists match while you type.

Buttons are saved in `builders_user/my_buttons.yaml` (plain YAML, safe to edit by hand) and are
shared by every builder node whose parts show that section; ✎ on a button edits or deletes it.
A button of yours whose lists are all rated above off is hidden while `nsfw` is off.

```yaml
buttons:
  - id: my_black_names
    label: Black names
    section: subject
    lists: [blackamericanfemalefirstnames_v10/black_female_names]
  - id: my_famous_buildings
    label: Famous buildings
    section: setting
    search: famous buildings
```

To change a slot, add slots or pin your favourite lists, copy `prompt.yaml` to `builders_user/`
(same `id` replaces the shipped one) and edit it. Slots are grouped by the section whose buttons
show them; the package's own curated lists (light/setups, camera/lenses, art/mediums, ...) are
pinned first:

```yaml
  - section: subject
    slots:
      - id: hair_color
        label: Hair color
        match: ['hair_?colou?rs?']
        avoid: ['fantasy']
        lists: ['my_pack/hair_colors_curated']   # pinned first
```

A new YAML file with a new `id` defines a new builder; it needs a node class (one line in
`prompt_builder_node.py`).

## Merging lists

Most packs share one core vocabulary and add their own tail (in one library, "black" was in 13 of
26 hair colour lists). **Merge lists…** in a pill's list viewer folds every list behind that button
into one:

* Near-identical entries become one row: case, hyphens, weights and the button's own words are
  ignored, so "Black hair", "black" and "black-haired" fold for Hair color. The most common
  spelling is shown; hover a row for the lists it came from and the other spellings.
* Rows are sorted by how many lists have them (`×13`); entries in 3+ lists are highlighted. Show
  only entries in 2+ / 3+ / 5+ lists, or only short, medium or long ones; what is shown (and ticked)
  is what gets saved.
* Click a row to leave it out. **Untick shown** / **Tick shown** work on what the search box finds,
  so "untick everything with 'glowing'" is two steps.
* Untick source lists at the top to leave them out of the merge.
* **Save list** writes `mine/<button>/<name>.txt` in the wildcard folder most of the sources come
  from, with a header naming them. Lists in `mine/<button>/` come first on that button, and the pill
  switches to the new list. **Hide the source lists** hides them from every button (Hide list in the
  viewer brings one back).

Your merged lists are for you: the header keeps the sources, since their licences are unknown.

## Templates

The bar at the top of the node saves everything on it as a named template and loads it back on
any composer node:

* **Save as…** asks for a name and writes `builders_user/templates/<name>.json`: every section's
  text and pills (list, mode, picks or exclusions, count, keep), Subject 2, 3 …, the Woman / Man
  choices, LLM fills and the platform. Locks are not saved, so a template always loads free to re-roll.
* **Load template…** replaces what is on the node. **Undo load** puts back what was there.
  Sections the node doesn't have (Setting on the Character Composer, say) are left out, and the
  bar says so.
* **Update** saves the node over the template it was loaded from; **Delete** removes that template.
* A pill whose list isn't in this library (a template from another machine) shows red **missing**;
  open it and pick another source list.

Templates are plain JSON, one file each, so they can be copied, shared or kept in git.

## Ages

The Age slot uses whatever age lists you have, with nothing removed, and any exact age can be typed
as a Fixed value. The only content rule in the wildcard engine is the content filter (on by default,
`"content_filter": false` in config.json turns it off) that drops a single list entry pairing
minor-related and sexual terms, and checks the assembled prompt for a minor term next to an
explicit sexual term (nudity alone does not count). A failing roll is re-rolled; typed text that
fails is blanked, with the reason in the report. It does not touch age lists or ordinary depictions
of people of any age. `violence_filter` (off by default) is separate: see the Wildcard guide.
