# Ideogram 4 Magic Prompt - design & rationale notes

This documents the Ideogram 4 Magic Prompt node (and the schema decisions that
affect the Composer Studio + Style node work). Kept per the "base on the official
repo, improve with tailoring, keep notes on the rationale" plan.

## What it is
`IdeogramMagicPrompt` ("Ideogram 4 Magic Prompt") expands a plain idea into an
Ideogram 4 structured caption JSON, using a local LLM through the existing
`LLMBackend` (LM Studio / Ollama / local Qwen3-VL). Optional reference image is
captioned first (vision backend) and folded into the idea.

Files:
- `ideogram_magic_core.py` - engine (load prompt, call LLM, parse/repair JSON, reorder keys, dims).
- `ideogram_magic_node.py` - the ComfyUI node.
- `ideogram_prompts/v1_official.txt` - Ideogram's official system prompt (auto-downloaded + cached).
- `ideogram_prompts/v1_tailoring.txt` - our additive tailoring (toggle via `use_tailoring`).

## Source / license of the system prompt
`v1.txt` is Ideogram's **open-source** magic-prompt system prompt, Apache-2.0,
from https://github.com/ideogram-oss/ideogram4
(`src/ideogram4/magic_prompt_system_prompts/v1.txt`). It is downloaded and cached
to `ideogram_prompts/v1_official.txt` on first run; if the machine is offline,
place that file there manually (the node prints the URL). We ship no copy in git -
we fetch the upstream source of truth so it stays current. Integration code is
under this repo's own license.

## How it mirrors Ideogram's mechanics
Faithful to their `magic_prompt.py`:
1. Parse the file's `[SYSTEM]` / `[USER]` sections; the user template substitutes
   `{{aspect_ratio}}` and `{{original_prompt}}`.
2. One OpenAI-style chat call (system + user). Temperature default 1.0.
3. Strip markdown code fences from the reply.
4. Reorder keys to the canonical schema order (style_description / compositional_
   deconstruction / each element), so a CaptionVerifier stays quiet.
5. Drop the top-level `aspect_ratio` (we pass width/height separately, matching the
   open-weight pipeline) but use the model's committed ratio to compute dims.
6. Optionally strip element bboxes (`keep_bboxes=false`). Ideogram strips by default;
   we **keep by default** because our primary use is loading into the Composer canvas.

## KEY SCHEMA FINDING - v14 vs v15 (RESOLVED: Option C)
Ideogram's official magic prompt emits **three** top-level keys:
`{"aspect_ratio", "high_level_description", "compositional_deconstruction"}` -
**no `style_description`**. Style is carried as prose (in high_level / background /
element descs), with strong tuning baked into the prompt (e.g. the word "warm" is
*banned* as a grading adjective; default to an iPhone-snapshot look rather than
DSLR bokeh; "professional photo of a person" = corporate headshot, not studio rig).
This is the **v15 prose-style** convention.

By contrast:
- The open-weight `prompting.md` documents `style_description` (with photo XOR
  art_style, strict key order, color_palette) as **optional**. (v14)
- Our **Ideogram 4 Composer + Style node** currently emit `style_description`. (v14)

Both are valid inputs to the open-weight model. But Ideogram's *own* shipped tooling
chose prose-only. Open question for the wider pipeline:
- **Option A (v15 / prose):** drop `style_description`; let the Style node produce
  prose style guidance folded into high_level/background. Matches Ideogram's tuned
  magic prompt; loses the explicit `color_palette` control surface.
- **Option B (v14 / style_description):** keep `style_description`; gives explicit
  palette + medium control (a distinctive Ideogram-4 feature). Diverges from the
  magic prompt's prose tuning, so the two paths produce stylistically different
  captions unless reconciled.
- **Option C (both):** Composer supports either; magic prompt stays prose; Style
  node optionally emits `style_description` for palette control. Most flexible,
  most surface area.

**RESOLVED - Option C is implemented (2026-06).** In `Eric_Composer_studio`:
`core/ideogram_schema.py` gained `normalize_style` + `apply_style`; IDEOGRAM_STYLE
is now a wrapper `{mode: structured|prose|off, style_description, prose, medium_tag}`
(a legacy bare `style_description` dict is still accepted as structured). The
advanced `Ideogram 4 Style` node emits any of the three modes (prose folds into
`background` + a short medium tag onto `high_level_description`). Both composers
route style through `apply_style`, so they consume whichever a caption carries, and
the canvas JSON import preserves an imported `style_description` via a hidden
`imported_style_description` in `layout_data` (fallback when no Style node is wired),
so a structured caption round-trips faithfully. The magic-prompt node here still
emits faithful **prose (v15)**; prose imports carry their style in the
high-level/background text, so they round-trip too.

## Tailoring applied (v1)
Currently one additive instruction (`v1_tailoring.txt`): require a `bbox` on every
individually-placeable element, so a caption loads cleanly onto the Composer canvas
(the official prompt allows omitting bboxes; the canvas wants them present). It does
not change the schema or the style tuning. Toggle off with `use_tailoring=false`.

Future tailoring candidates (Option C chosen), each to be logged here
with its rationale before adoption:
- optional `style_description` emission (Option B/C) for palette control;
- tightening element-count or background discipline for our specific samplers.

## Wildcard support (2026-09)
`idea` now passes through the shared wildcard engine (`core/wildcards`) before expansion, so
`__name__`, `{a|b}`, tag queries and variables work here as in the other nodes. Two appended
optional inputs: `wildcard_seed` (-1 = fresh roll each run) and `wildcard_llm_block`.

Rationale for where the selected-elements block goes: `core.expand` gained `extra_system`, which
is appended to the SYSTEM prompt after the tailoring file. It is deliberately NOT appended to the
idea text. The official user template wraps the idea as the thing to depict, so an instruction
placed there risks being treated as content, and Ideogram renders quoted text. The official
system prompt and the schema are untouched; with no wildcards in the idea, `extra_system` is
empty and the call is byte-identical to before.

