# Wildcard lists

These are the lists that ship with Eric's Prompt Enhancers. **Your own packs do not go here.**

## Where packs live

Put downloaded packs in `ComfyUI/models/wildcards`. Every node in this package reads that folder,
and any `wildcards:` entry in `extra_model_paths.yaml`, without configuration. Dynamic Prompts and
Impact Pack packs (`.txt`, nested `.yaml`) work as they are.

Folders are searched in this order, and when a name exists in more than one, the first one wins:

1. a node's `extra_paths` input
2. `ComfyUI/models/wildcards`
3. `wildcards:` folders from `extra_model_paths.yaml`
4. `"wildcard_paths": ["D:/more/packs"]` in this package's `config.json`
5. this folder

So a pack's `animal.txt` replaces the shipped `animal.txt`; it is not mixed into it.

Inside a pack folder, `_nsfw/` holds lists only nodes with `allow_nsfw` on can use, `_generated/` holds lists
the tools write, and any other top-level `_folder` is ignored. A bare `__name__` that exists in several packs
uses one pack (and says which); write `__**/name__` to pool them. See docs/WILDCARD_GUIDE.md.

A pack written for a folder called `look` still resolves (`__look/styles__`) when it was unzipped
as `theLookWildcards_v10`, as long as the real folder name contains the expected one and only one
such folder exists.

Run `python_embeded\python.exe custom_nodes\video_prompter\dev\scan_wildcard_packs.py` for a
report on everything found: unreadable files, names defined twice, references to packs you do not
have, and syntax from other tools.

| Use | Syntax |
| --- | --- |
| One entry from a file | `__animal__`, `__light/setups__` |
| Any file under a folder | `__camera/**__`, `__objects/**__` |
| Entries by tag | `__objects[metal AND handheld]__`, `__spaces[empty AND NOT natural]__`, `__[hollow AND antique]__` |
| Several entries | `{2$$__color__}`, `{1-3$$ and $$__objects/kitchen__}` |
| Pick once, reuse | `${who=!__person__} ... ${who}` |
| Exact words must survive the LLM rewrite | `__=name__`, `{=a|b}` |
| Inspiration only | `__?emotion__`, `{?a|b}` |

`.txt`: one entry per line, `# comment` lines ignored, optional weight prefix `3::common entry`.
`.yaml`: keys form the wildcard path; items are strings or `{text, tags, weight}`. See `objects.yaml`.

The entries are deliberately specific and physical ("a barn owl", "soft north-window light from the
left") because image models render concrete nouns and real lighting far better than adjectives.

## vp/ - the Wildcard Composer's own lists

`vp/<section>.yaml` holds lists written for this package (same dual licence as the code) for the
Wildcard Composer's buttons, named `__vp/<section>/<list>__` (for example `__vp/format/image_type__`,
`__vp/lighting/studio_setup__`). Each button in `builders/prompt.yaml` offers its `vp/` list first,
then the matching lists from your own packs. Entries are written to slot into typed text; each
file's header says how (Era reads after "in", Holding after "holding"). Where it helps, entries
carry tags (`__vp/format/image_type[photo]__` = photographic types only).
Each list's own header line (a comment just above it) gives its entry form. Lists without a button
of their own (`vp/subject/age_described`: "in their early thirties") are reachable by name and
from the section's More lists. Tagged lists: image_type (medium family), era and era_aesthetic
(period), age, fashion_style, group (count), atmosphere, photographer (genre), typography
(sans / serif / script / hand / display / mono).
