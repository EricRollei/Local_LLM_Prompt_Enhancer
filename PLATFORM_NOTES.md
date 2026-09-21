# Platform profiles - notes, changes and tailoring log

Phase 2 of the v2 plan. Facts checked 2026-09-20 (open models) and 2026-09-21 (hosted / API models).
The research behind every profile, with sources and confidence labels, is in `docs/platform_research/`.

## What this is

Everything the nodes know about a target model now lives in one YAML file per model under
`profiles/` (image, edit, video). `core/profiles/` reads them; nothing in there depends on ComfyUI,
torch or an LLM. Adding a model means adding a file, not editing a node. `profiles/_TEMPLATE.yaml`
is the starting point and `core/profiles/schema.py` documents every field.

Your own profiles, and edited copies of shipped ones, go in `profiles_user/` (git-ignored, never
touched by an update). A file there with the same `id` as a shipped profile replaces it. Extra
folders can be listed in `config.json` under `"profile_paths"`.

Three consumers:

1. **Platform Prompt Rewriter** (new node). One idea in, one prompt out, for any profile, including
   the formats the older nodes cannot produce: MiniMax H3 fields, Hailuo bracket commands, FLUX.2 and
   Ideogram JSON, edit instructions. Outputs the prompt, the negative prompt (empty when the model
   cannot use one), a report, and the exact system prompt that was sent, so the reasoning is
   inspectable.
2. **Text-to-Image Prompt Enhancer** and **Image-to-Image Prompt Expander**. Their platform
   dropdowns keep their original values in their original order; new image and edit profiles are
   appended after them. `platforms.py` asks the profile library first and falls back to its own
   table, which is left in place untouched as the safety net.
3. **The three video expander nodes** (Video Prompt Expander, Advanced, Image-to-Video) have a
   `target_model` input, appended last, default **`minimax_h3`**. See the next section.

## The video nodes and `target_model`

The video nodes were written around Wan 2.2 end to end: tiers of 150-1000 words, a Wan shot format, a Wan
option list, a Wan negative prompt. That is all still there, untouched, behind `target_model = wan22_video`.

Any other target takes a different path through `expansion_engine.py`:

- The model-specific part - format, length, rules, camera vocabulary, sound and dialogue syntax, and the
  vendor's own rewriter prompt where one is published - comes from the profile, exactly as in the Platform
  Prompt Rewriter node.
- The node's own controls are added as "the user's direction": preset, aesthetic controls, creativity mode,
  reference-image mode, variation number, required keywords, and (Advanced node) the shot count, phrased so
  the target model's own way of writing shots is used.
- **The tier sets length inside the model's own range** (basic = the low end, cinematic = the top), not the
  Wan word counts. A model that states words per second (`words_per_second` in the profile; MiniMax H3:
  35-45) gets its length from `duration_seconds` instead, because there the clip length is what decides.
- `duration_seconds` (appended with `target_model`, default 6) is what the timeline, the amount of action and
  the dialogue are fitted to. Set it to the length you will actually generate.
- The answer is checked by the profile's validator instead of the Wan parser (which drops a short first line
  and would damage field formats). Warnings appear in the breakdown / status output.
- Required keywords and verbatim wildcard picks the LLM dropped are put at the end of the FIRST field of a
  field-format prompt (MiniMax H3), not after the last one, where they would land in the music field.
- The negative prompt is the target model's own, or empty when it has none. Your negative keywords pass through.
- Image-to-Video node: the picture description is handed over as a fact about the start frame and the idea
  is the motion alone, which is how every image-to-video model wants to be prompted.

**Existing workflows.** A workflow saved before this input existed has no value for it, so ComfyUI gives it
the default: it will write MiniMax H3 prompts until you set `target_model` to `wan22_video` and save. That is
the price of making H3 the default, and there is no way around it that does not involve guessing. API-format
workflows are different: there a missing input reaches the Python function, whose default is `wan22_video`.

## Hosted / API models

Closed models still need prompts, and their vendors publish more exact rules than most open models get.
Profiles for them carry two extra things:

- `api_note`: what to set in the API call. Mostly this is **how to switch the vendor's own prompt rewriting
  off**, because a prompt rewritten twice drifts: FLUX.2 [pro] `disable_pup: true`, [flex]
  `prompt_upsampling: false`; Ideogram 3 `magic_prompt: "OFF"`, Ideogram 4 send `json_prompt`; Leonardo
  enhance OFF; Wan 3.0 `prompt_extend: false`; MiniMax H3-Max `extra.prompt_expansion_mode: "disabled"`;
  GPT Image: call the Images API, not the Responses tool. Seedance, Kling, Runway, Luma, Grok, Vidu and
  PixVerse document no such flag; Seedream and Veo have one that cannot be reliably switched off. The note is
  printed in the rewriter's report and in the video nodes' breakdown.
- `negative: inline`, a fourth negative mode: there is no negative field, but the vendor endorses short
  exclusions written into the prompt (GPT Image "no watermark", Seedance "keep it subtitle-free", Kling,
  Recraft, Gemini Omni). The plain `no` mode tells the LLM never to name unwanted things; `inline` allows a
  few at the end, only for things the user asked to exclude.

Things that differ from what one would guess:

- **There is no "Seedream 2.5".** ByteDance's image line runs 3.0, 4.0, 4.5, 5.0 Lite, 5.0 Pro (`seedream5`).
  The 2.5 is **Seedance 2.5**, the video model (`seedance25`).
- **Seedance 2.0 and 2.5 want opposite things.** 2.0: shot numbers only - ByteDance warns that seconds in the
  prompt "may lead to abnormal generation results" - and special characters for sound: `{dialogue}`,
  `<sound effect>`, `（music）`, `【subtitle】`. 2.5: whole-second timestamps work, and sound is labelled plain
  text with quoted speech.
- **Kling 3.0's current API has no negative prompt** and cites references as `@image_1`; the fixed multi-shot
  form is `shot 1, 3, words; shot 2, 4, words;` with the seconds adding up to the clip length. Sound is OFF
  by default. ComfyUI partner nodes may still use the legacy `<<<image_1>>>` form.
- **Midjourney is the opposite of everything else here**: its own docs say short and simple prompts give the
  best images. The profile targets 8-45 words with parameters last, and `::` weights are not emitted (listed
  for V1-V6.1 only). `--no` is returned in the negative output for you to append.
- **Hosted MiniMax H3 takes prose** (`minimax_h3_api`); the local checkpoints take the structured fields
  (`minimax_h3`). The hosted endpoint does the conversion itself.
- **Imagen is shut down** in the Gemini API; `nano_banana` replaces it. **Sora 2** ends 2026-09-24 and has no
  profile. **Veo 3.1** is still Google's latest Veo; **Gemini Omni Flash** is a separate new video model that
  cuts between shots unless told not to.
- Runway Act-Two takes no text prompt. Runway Aleph 2.0 (`runway_aleph2`) is a video EDIT model and is offered
  by the rewriter node only, not in the video nodes' dropdown.

Left out, with reasons: Reve (no vendor documentation readable), Adobe Firefly (API reference unreadable, prompt
limits unknown), Pika and Moonvalley Marey (partner mirrors only), Higgsfield (an aggregator: use the underlying
model's profile), Midjourney Video (image-to-video with a handful of flags, no real prompt format), hosted LTX
(same guidance as the open `ltx25`). Low-confidence profiles say so in their report line: `grok_imagine_image`,
`grok_imagine_video`, `vidu_q3`, `pixverse_v6`.

## Official rewriter prompts

Wan, LTX, Qwen-Image, FLUX.2, Krea 2, Hunyuan, Z-Image, Ideogram and MiniMax publish the system
prompt (or writing guide) their own rewriter uses. A profile can name one under `official:`. It is
downloaded from the vendor's repository on first use and cached in `cache/official_prompts/<id>/`;
nothing is shipped or redistributed with this package. The node's `official_prompt` input chooses:
`auto` (use it unless it is over 30,000 characters; only Qwen-Image 2512 is), `on`, `off` (always the profile's own rules;
works offline), `refresh`. A failed download falls back to the built-in rules, says so in the
report, and is not retried for ten minutes.

After the vendor text the rewriter appends a short block: the output contract (faithfulness, output
only the prompt), hard limits, the prompt language, and the profile's `tailoring` text. Python files
are read with `ast`; nothing downloaded is ever executed.

### Tailoring log

Every deviation from a vendor's text is listed here, as IDEOGRAM_NOTES.md does for Ideogram.

- **Wan 2.2 text-to-video rewriter, rules 8-10 removed** (`drop_lines` in `wan22_video.yaml`, inherited
  by `alice_t2v`). Those rules tell the LLM to silently replace the user's prompt with an unrelated
  "high-aesthetic" one when it sees suggestive content, a bikini (move it to a beach), or two men
  or two women kissing (swap for a different action). They are Alibaba's hosted-service moderation,
  not prompting technique, and a local enhancer that quietly swaps your idea for another is broken
  whatever the content. One part of rule 8 is worth keeping and is kept as a plain rule in the
  tailoring text: never depict a minor in a sexualised way.
- **FLUX.2 edit rewriter: "Keep content PG-13" left in place.** It is a content guideline, not a
  silent substitution. To remove it, copy `flux2_dev.yaml` to `profiles_user/` and add
  `drop_lines: ["Keep content PG-13"]` to the edit entry.
- **MiniMax H3**: the published files are writing guides, not system prompts, so each entry carries a
  one-paragraph `preamble` naming the mode (T2VA, I2VA, FL2VA, Ref2VA). Tailoring adds two lines:
  never decorate or reorder the field names, keep the timeline inside the clip length.
- **Qwen-Image 2512**: the vendor prompt is about 35,000 characters, so `auto` skips it and uses the
  profile's rules, which are taken from it. `on` uses it and needs an LLM context of 12k or more.
- **HunyuanVideo 1.5 image-to-video**: Tencent's rewriter answers in Chinese, so the profile uses its
  own rules (taken from that prompt) for i2v and the vendor prompt for t2v only.
- **Z-Image**: the vendor template asks for JSON with a `revised_prompt` key; the key is unwrapped
  automatically.

All 24 vendor prompts were downloaded and parsed on 2026-09-20 with `dev/try_official_prompts.py`
(run it again whenever a report says a file "changed shape").

## What changed for the platforms that already existed

All 16 ids are kept, so saved workflows load. Length targets you had tuned are kept wherever they
fit the model's hard limit.

| id | change | why |
|---|---|---|
| `flux` | quality tokens now forbidden in the instructions; "Quality modifiers important" block gone | BFL's own guidance: keyword and quality-token style is the less effective one; config already had quality off, the instruction block contradicted it |
| `flux_kontex` | now an **edit-instruction** profile (12-60 words, change + keep clause, no pronouns, "transform" pitfall) | Kontext is an instruction edit model, not a long-prompt FLUX variant. Id spelling kept for saved workflows |
| `chroma` | name and description corrected; T5-only, real CFG, long negative prompt | Chroma (lodestones, FLUX.1-schnell derivative) has nothing to do with Meissonic |
| `wan22`, `wan_image` | developer corrected to Alibaba; cinematic tags taken from Wan's own rewriter vocabulary | was listed as Tencent |
| `aura_flow` | developer corrected to fal; 256-token limit stated | was listed as Stability AI |
| `kolors` | developer corrected to Kuaishou; target lowered from ~230 to 90-170 words | ChatGLM3 encoder has a hard 256-token limit: the pipeline raises an error above it |
| `noobai` | now a **tag** profile with the model card's prefix, tag order and negative | it is a Danbooru + e621 tag model; "balanced natural language" was wrong |
| `pixart_sigma` | 300-token limit stated; target 100-200 words | fits the T5 window |
| `qwen_image` | 2512 rewriter rules: quoted text with placement, "no recognizable text" closer, no negation words, negative prompt | from Qwen's published rewriter |
| `qwen_image_edit` | Picture 1 / Picture 2 naming, text edits as `Replace "x" to "y"`, keep-clauses for people | from Qwen's edit rewriter and the 2509/2511 pipeline |
| `hunyuan_image` | relabelled HunyuanImage 2.1: overall-detail-conclusion structure, double-quoted text for the glyph encoder, long prompts | the old "simple English, concise" advice was for the 2024 Hunyuan-DiT |
| `sd_xl`, `sd_1_5`, `pony` | facts unchanged; instructions now generated from the profile | - |
| `illustrious` | tags with **spaces**, not underscores; quality tags at the **end**; 25-80 words instead of ~150 | OnomaAI's paper writes every prompt with spaced tags ("looking at viewer", "hatsune miku") and gives the training caption order: person count, character, rating, general tags, artist, quality, year. The Text-to-Image node used to convert your keywords to underscores for this platform; it no longer does. The ~150 target only produced padding, as it did for NoobAI |
| `kling3`, `seedance2`, `veo31`, `runway_gen45` | rewritten from the vendors' own pages, now high confidence | first pass relied on partner mirrors; see "Hosted / API models" |
| all | negative prompt output is empty for models that cannot use one (user keywords still pass through) | sending boilerplate negatives to a CFG-free model only misleads |

Text-to-Image node, three small fixes that ride along: the minimum length now comes from the
profile (the old fixed 80-word floor padded FLUX.2 klein past its 40-70 word target); the closing
"example of correct output" no longer shows `masterpiece, best quality` to models that do not want
it; the platform format block is no longer chosen by matching words in the display name. Pony keeps
its hand-written block.

## New profiles

Hosted / API, added 2026-09-21 - image: `seedream5`, `nano_banana`, `gpt_image`, `midjourney_v8`, `flux2_pro`,
`ideogram3`, `recraft_v4`, `leonardo_phoenix`, `kling_image3`, `runway_gen4_image`, `luma_uni1`,
`grok_imagine_image`; video: `seedance25`, `gemini_omni_flash`, `runway_aleph2`, `wan3_api`, `luma_ray32`,
`minimax_h3_api`, `grok_imagine_video`, `vidu_q3`, `pixverse_v6`.

Open models and first-pass API profiles, added 2026-09-20 -
Image: `flux2_dev`, `flux2_klein`, `flux2_json`, `krea2`, `z_image_turbo`, `z_image`, `qwen_image_21`,
`hunyuan_image_3`, `ernie_image`, `anima`, `pony_v7`, `ideogram4`, `minimax_image_01`.
Edit: `flux2_edit` (plus the corrected `flux_kontex` and `qwen_image_edit`).
Video: `minimax_h3`, `hailuo_23`, `wan22_video`, `alice_t2v`, `wan_api_audio`, `ltx2`, `ltx25`,
`hunyuan_video_15`, `kling3`, `veo31`, `seedance2`, `runway_gen45`.

Sora 2 was left out on purpose: OpenAI shuts the API down on 2026-09-24.

## Things worth knowing

- **MiniMax H3.** The local checkpoints want MiniMax's structured fields; only the hosted API
  rewrites free prose into them. `<d>` is a real tokenizer token, so its spelling matters. Bracket
  camera commands are the old Hailuo format and are wrong for H3. Dialogue needs a speaker id:
  `(S1) says: <d>[English] ...</d>`. The reference mode has six sections, including
  `retention_analysis`. One non-technical point: the MiniMax H3 Community License lists the USA, EU,
  UK and South Korea as excluded territories (Hugging Face has a separate application form for
  those regions). That is a licence question for you, not something these nodes act on.
- **Do not rewrite twice.** HunyuanImage 3.0 (`bot_task=image`), ERNIE-Image (`use_pe=False`), Hailuo
  (`prompt_optimizer=false`) and hosted Wan (`prompt_extend=false`) all rewrite prompts themselves
  unless told not to.
- **LTX-2.5 reverses two LTX-2 rules**: camera motion must now always be stated, and image-to-video
  prompts open by matching the start image instead of avoiding it.
- **Base versus distilled.** Krea 2 Raw, Z-Image base, Chroma HD, Anima base and ERNIE-Image base run
  with CFG and can use a negative prompt; their Turbo / Flash versions cannot. Profiles describe the
  version most people run and say so in `negative_note`.

## Open questions

- Illustrious is settled (spaces, quality tags last, shorter). One thing Onoma does not publish is an
  official negative string; the profile's default is assembled from the model's real quality labels.
- Medium confidence: `wan_api_audio`, `wan3_api`, `hailuo_23`, `minimax_image_01`, `minimax_h3_api`,
  `seedream5` (ByteDance's guide page is a JavaScript app that could not be read; facts come from the Seed blog
  and mirrors of the API reference), `luma_ray32`, `kling_image3`.
- MiniMax H3 `words_per_second: [35, 45]` is taken from MiniMax's examples and is assumed to count all
  three fields together. If H3 prompts come out too long or short for a clip, this is the number to change.
- Qwen-Image 2.1 was released on the day of the check; its profile is provisional.
- Tag-model length. A live run with a 4B model padded NoobAI to 147 words of filler at the old 40-150
  target, so NoobAI is 25-70 words (about 15-40 tags) and Illustrious 25-80.

## Done since the first version of this file

- The rewriter node takes IMAGE inputs (`image`, `end_image`) and captions them through the same LLM
  backend (a vision model must be loaded); a wired-in description wins. With an image connected,
  `task = auto` becomes flf2v, i2v or edit, whichever the profile supports.
- The prompt database's platform list now includes every profile id, after its original entries.
- Live run against LM Studio (`dev/try_live_llm.py`, qwen3-4b-2507): H3 fields with speaker id and
  `<d>` dialogue, Krea 2 prose on Krea's own expander prompt, a Kontext edit with its keep-clause,
  NoobAI tags with the required prefix, Hailuo brackets - all in the right format on the first try.
  What a 4B model gets wrong is content, not format: it under-writes Hailuo (the report warns), and on
  Krea 2 it added props the idea did not contain. Use a larger model for real work.
- `flux2/schema.yaml` and `deepseek_rewriter_node.py` in this folder are not loaded by anything
  (the node is not registered in `__init__.py`). FLUX.2 is served by the profiles now. Both files were
  left untouched.

## What the live run of the video nodes showed (2026-09-21, qwen3-4b-2507)

`dev/try_video_targets.py` runs the three video nodes and four API profiles against a real LLM. Formats came out
right on the first try (H3 fields with timestamps inside the 6 s clip, Seedance 2.5 `Shot 1 (0-3s):`, Seedance 2.0
`{dialogue}` with no timestamps, Illustrious spaced tags ending in the quality tags, Midjourney 26 words plus
parameters). A small model also did three things that are now guarded against:

- **It invented speech.** With H3's guide in front of it, it gave a silent scene a voiceover. When the idea has no
  quotation marks and no verb of speaking or singing, the instructions now say outright: no dialogue, no voiceover.
- **It invented reference files.** Seedance prompts came back with `Asset Bindings: @Image1 ...` copied from the
  rules. Reference syntax now lives under the `ref2v` task only, and every other task of such a model is told that
  no reference files exist. To write a reference prompt, use the rewriter node with `task = ref2v`.
- **It put the LoRA trigger on a line of its own after the last H3 field**, where H3 would read it as music. Such
  lines are now lifted out and the term is placed at the end of the first field.

It also wrote Kling's multi-shot form loosely (`Shot 1, 3 seconds:`). The profile now carries an exact example and
a `kling_shots` validator that reports inexact lines. A 24B or larger model is the real fix for that kind of slip.

## Testing

`python_embeded\python.exe dev\verify_platforms.py` - part 1 checks the core and every profile
without ComfyUI; part 2 checks `platforms.py`, the dropdowns, the two image nodes and the rewriter
node against a stub LLM. `dev\snapshot_widgets.py --check` guards widget order.
