# MiniMax prompting facts for platform profiles

Research date: 2026-09-20. Confidence labels: **high** = official doc/file read directly; **medium** = official but read through a summarizer / indirect; **low** = third-party only.

Method note: GitHub raw files were downloaded byte-for-byte with curl (cached copies listed in section 0). huggingface.co and platform.minimax.io are blocked for direct curl in this environment, so those pages were read through WebFetch (a small model summarizes the page; quotes from those pages are as reported by that tool and should be treated as near-verbatim, not byte-exact).

---

## 0. Official prompt template files (download + cache these)

Raw URLs (all HTTP 200 on 2026-09-20):

| File | Raw URL | Role |
|---|---|---|
| SKILL.md | https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/SKILL.md | Skill entry point: mode routing, output rules |
| base-en.txt | https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/references/base-en.txt | Guide for T2VA / I2VA / FL2VA / L2VA (15.8 KB) |
| ref-en.txt | https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/references/ref-en.txt | Guide for full-reference Ref2VA (23.6 KB) |
| agents/openai.yaml | https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/agents/openai.yaml | Optional UI metadata only |
| Music3 SKILL.md | https://raw.githubusercontent.com/MiniMax-AI/MiniMax-Music3/main/skills/music-caption-rewriter/SKILL.md | Music 3 structured-caption rewriter (needs its references/ + templates/ folders to be fully functional) |

Same H3 guides on Hugging Face (HF model card links these as the "Prompting Guidance"; section headings and key quotes matched the GitHub txt files):
- https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md (raw: replace `/blob/` with `/raw/`)
- https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md

Probed and NOT present (404): `references/base-zh.txt`, `ref-zh.txt`, `base-cn.txt`. Only English guides found in the skill folder.

Local cached copies made during this research:
- `h3/SKILL.md`, `base-en.txt`, `ref-en.txt`, `README_gh.md`
- `mm/music3_README.md`, `music_skill.md`

Important: these files are **writing guides**, not a ready-made "you are a prompt enhancer" system prompt. MiniMax's own enhancer (H3-Context-IR) is a hosted multi-stage system and is explicitly NOT open-sourced. The guides are what MiniMax tells developers to use to "build your own context-processing system". For a local-LLM enhancer, wrap base-en.txt / ref-en.txt in your own system prompt.

---

## 1. MiniMax H3 (a.k.a. Hailuo 3.0)   — confidence: HIGH

### What it is
- Announced 2026-07-31 on the MiniMax blog ("open up the model weights in the coming days"); license text is dated 2026-08-02; third-party news dates the weights/ComfyUI support to ~2026-08-03 and the official skills to ~2026-08-10 (dates of weights/skills: low confidence, third-party).
- "general-purpose, omni-modal generative system ... can generate video with native stereo audio at resolutions up to 2K and durations of up to 15 seconds."
- Repos: https://github.com/MiniMax-AI/MiniMax-H3 and https://huggingface.co/MiniMaxAI/MiniMax-H3 ; ComfyUI repack: https://huggingface.co/Comfy-Org/MiniMax-H3
- Open weights: yes, two checkpoints, BF16:
  - `FL2VA/` — tasks `t2va` and `fl2va` (0, 1 or 2 images: none = text-to-video; one = first-frame OR last-frame; two = first+last).
  - `Ref2VA/` — task `ref2va` (omni-reference: images <= 9; videos <= 3 clips, each 2-15 s, total <= 15 s; audio <= 3 clips, each 2-15 s, total <= 15 s; max 12 files total).
- NOT open: H3-Context-IR (the official prompt rewriter) and H3-Regenerate-2K (2K upscaler-by-regeneration). Both are API-only.
- License: "MiniMax H3 Community License Agreement" (custom, not OSI). Territory = "worldwide, excluding the Excluded Territories" = EU, UK, Republic of Korea, USA (HF has a separate application form for those regions). Separate written authorization needed above USD 20M yearly revenue. Commercial products must prominently display "MiniMax H3". Outputs may not be used to improve other AI models. (Read via WebFetch of the HF LICENSE: medium confidence on exact clause wording.)
- Architecture facts relevant to prompting:
  - Text encoder: "The H3-Encoder uses the full pretrained weights of Qwen3-VL-32B and provides the hidden states from its 50th layer".
  - "We add several special tokens, such as `<d>`, to the tokenizer configuration. When using H3, the tokenizer and associated configuration files provided in the H3 repository are required." => `<d>` is a real special token, not decoration; do not alter its spelling.
  - "The released checkpoints are CFG-distilled Omni Transformer model weights." => no negative prompt. No negative-prompt field exists in the official request JSON (`task`, `prompt`, `conditions[]`, `target{short_edge, aspect_ratio, duration_seconds}`, `seed`).
  - 33B dense single-stream transformer (approx. 13B of it in AdaLN branches that can be precomputed).
- Output spec: 4-15 s; 24 FPS; 32 kHz stereo audio; default short side 768 px; many aspect ratios (21:9, 16:9, 4:3, 1:1, 3:4, 9:16).
- ComfyUI docs: native canvas 768 px short edge (1344x768 at 16:9), resolutions round to multiples of 32, duration snaps to the "17-frame-per-block (17k+5) grid at 24fps" (confirms frameCount % 17 == 5).
- Dialogue languages: "Stable support for 11 languages: Arabic, Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Russian, and Spanish."
- Hosted variants (platform.minimax.io): `MiniMax H3` (768P / 2K, 4-15 s) and `MiniMax H3 Max` (fal.ai post-trained, 480P / 768P, 5-15 s). Hosted endpoints run Context-IR for you, so they accept free-form natural language; the **local H3-Base wants the structured IR format below**.

### Prompt format A — base modes (T2VA / I2VA / FL2VA / L2VA), from base-en.txt

Order (exact field names, colon, one blank line between fields):
```
[optional instruction line for keyframe modes]
<blank line>
integrated_multimodal_description: [Shot 1] ...

overall_soundscape: ...

non_diegetic_music: ...
```

Instruction line (must be line 1, followed by one blank line). T2VA has none.
- I2VA, always: `For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.`
- FL2VA, always: `How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video.` (note: no angle brackets / square brackets in this one; em dash)
- L2VA, always: `How the reference pictures align with the target video — <Picture 1> (from [Shot N]) aligns with the S.SS-second mark of the target video.`
- "`N` is the index of the actual final shot, and `S.SS` is the effective video duration formatted to exactly two decimal places."

Field roles (verbatim):
- "**integrated_multimodal_description**: Describes visuals, actions, shots, speakers, dialogue, singing, and diegetic audio along the timeline."
- "**overall_soundscape**: Summarizes ambient sound, physical action sounds, and non-verbal human sounds across the entire video."
- "**non_diegetic_music**: Describes background music that the characters cannot hear and only the audience can hear."

Shots:
- Start of `[Shot 1]`: state overall style + initial composition. Listed styles: `Cinematic`, `live-action`, `2D-animated`, `3D CG`, `claymation`, `watercolor`, `vintage film`. Example: `[Shot 1] Live-action, cinematic, a medium-wide shot frames...`
- "Do not add a timestamp to the first shot." Later shots: `[Shot 2] At 00:03.500, the camera cuts to...` (format MM:SS.mmm, strictly increasing, inside the duration).
- Allowed cut phrases: `the camera cuts to`, `the shot cuts to`, `the shot transitions to`, `the shot changes to`, `the shot switches to`. Cross-dissolve / fade / wipe only "When explicitly requested by the user".
- "If only the distance or a slight angle needs to change, prefer camera motion." FL2VA "generally favors a single shot".

Camera vocabulary (motion type + optional amplitude + optional speed), written as natural English, NOT bracket tags:
- `Zoom In / Zoom Out`, `Push In / Pull Out`, `Pan Left / Pan Right`, `Truck Left / Truck Right`, `Tilt Up / Tilt Down`, `Pedestal Up / Pedestal Down`, `Arc Shot`, `Tracking Shot`, `Static Shot`, `Shake Slightly / Shake Strongly`, `POV`, `Roll Clockwise / Roll Counterclockwise`
- Amplitude: `with small amplitude` | `with large amplitude`. Speed: `at slow speed` | `at fast speed`. "medium amplitude and normal speed are usually omitted."
- "Camera motion should be written as a natural English action within the shot, rather than stacked as separate labels at the end of a sentence". Example: `The camera pushes in with small amplitude at slow speed toward the folded letter in her hands.`
- => Hailuo-style `[Push in]` brackets are NOT the H3-Base format. (platform.minimax.io's H3 guide does mention "[pan], [zoom], [static]" but that is for the hosted API, which passes through Context-IR.)

Speakers and dialogue:
- Stable IDs `(S1)`, `(S2)`; joint speech `(S1,S2)`; same ID across shots; "characters who never vocalize receive no speaker ID."
- On first appearance give identity + voice (age, gender, on-screen or not, pitch, timbre, rate, accent).
- "Inside `<d>`, include only the language tag and the actual user-provided spoken content. Preserve every original word and punctuation mark verbatim; do not translate or rewrite them."
- Syntax: `The young woman with a quiet, breathy voice (S1) says: <d>[English] I get off at the next station.</d>`
- Group: `The two children (S1,S2) shout together, <d>[English] Wait for us!</d>`
- Voiceover: exact phrase `says in an off-screen voiceover`, and right after the `<d>` block state lips closed: `...: <d>[English] I still remember that road.</d> while his lips remain completely closed.`
- Line crossing a cut: put `<scenetrans>` at the join in both parts and state continuity (`continues seamlessly across the cut`, `continues uninterrupted into the next shot`, `carries over from the previous shot`, `remains audible across the transition`). Speech truncated by video end: `<cutoff>`.
- Language tag = `[English]`, `[Chinese]` etc. (full language name in square brackets, first thing inside `<d>`). Only `[English]` appears in official examples; other names inferred from the supported-language list (medium).
- Singing and diegetic music (radio, TV, instruments characters can hear) go in the main description, not in the music field.

On-screen text: in English double quotes, original language preserved: `A red neon sign reading "营业中" glows above the doorway.`

Audio fields:
- overall_soundscape: "Use 1–4 English sentences in one continuous paragraph". Do not repeat dialogue/singing/diegetic music. "Use `N/A` only when the user explicitly requests complete silence throughout the video."
- non_diegetic_music: "Use 1–3 English sentences ... Focus on instrumentation, speed, rhythm, and dynamic changes; do not use abstract mood words or explain the emotional function of the score." "Use `N/A` when there is no non-diegetic music."

Keyframe-mode writing pattern:
- I2VA: "first-frame anchor → action onset → continuous development → result or reaction"; keep identity, clothing, colors, props, layout consistent with the picture.
- FL2VA: "first-frame state → observable intermediate changes → progressively narrowing differences → last-frame state".
- L2VA: "plausible preceding state → explicit action and transition path → gradual convergence in the final shot → last-frame landing".

### Prompt format B — full-reference Ref2VA, from ref-en.txt

Six sections, this exact order, each as `name:` then content on following lines:
1. `subject_definitions:` — one line per tracked item.
2. `summary:` — one short paragraph starting with a bracketed task-type prefix.
3. `retention_analysis:` — one line per label with a fixed marker.
4. `detailed_description:` — main body (replaces integrated_multimodal_description).
5. `overall_soundscape:`
6. `non_diegetic_music:`

(Your note listed subject_definitions / summary / detailed_description — the official format also requires **retention_analysis** between summary and detailed_description.)

Labels: `<Subject N>` (reusable visible content: people, objects, scenes, clothing, styles, motions), `<Picture N>` (only when the image itself is a frame anchor / storyboard), `<Video N>` (whole-video relation: edit source, continuation, camera/cut/rhythm structure), `<Audio N>` (audio asset or enabled track of a reference video). Video and Audio are numbered independently. "Once a reference label is assigned ... it keeps the same meaning across" all sections.
- `<Subject 1> is the young woman in <Picture 1>, with long dark hair, a blue cardigan, and a thin silver necklace.`
- `<Audio 1> is the voice-timbre reference for <Subject 1> (S1).`
- If an image only defines a character/scene/style, do NOT make a standalone Picture entry; cite it inside the Subject definition.

summary task types (combine with ` + `, no repeats): `keyframe completion`, `reference generation`, `video editing`, `video continuation`, `audio reuse`, `audio reference`. Example: `[reference generation + audio reference] The target video shows ...`. For edits the summary begins: `The target video is an edited version of <Video 1>.` No new labels may be introduced in summary.

retention_analysis markers (fixed English values):
- Visual: `fully_preserved`, `partially_preserved`, `attribute_transfer`, `weak_reference`
- Audio: `fully_copy`, `partially_copy`, `reference`, `weak_reference`
- Line shapes: `<Subject 1> (appears in [Shot 1], [Shot 3]): fully_preserved - ...` / `<Picture 2> ([Shot 1] first frame): fully_preserved - ...` / `<Video 1> (cut and pacing structure): weak_reference - ...` / `<Audio 1>: fully_copy - ...`
- "Do not write `(Sx)` in `retention_analysis`."

detailed_description differences from base mode:
- Style is "Established in one or two English sentences before `[Shot 1]`" (not after it). Example opener: `The target video is in a cinematic, literary music-video style with soft lighting...`
- Shots, cut timestamps, camera wording, `(Sx)`, `<d>[Language] ...</d>`, `<scenetrans>`, `<cutoff>` are identical to base mode.
- Speaking referenced subject: `<Subject 2> (S1) turns toward the woman and says, <d>[English] ...</d>`
- Lyrics inside reused music with no on-screen singer: cite `<Audio N>` as source, no new `(Sx)`.
- Unintelligible source audio: write `[unclear]`. Normalize punctuation to `, . ? !`; "remove repeated tildes, emoji, bullets"; end sentences with `.`, `?`, or `!` before `</d>`.
- Frame anchors phrased naturally: `the shot begins from <Picture 1>`, `the shot's keyframe corresponds to <Picture 2>`, `the shot ends on <Picture 3>`.
- Length: "For generation tasks, `detailed_description` is normally 350-500 English words." Dialogue-dense content prioritizes fitting the full spoken timeline; editing tasks scale with the source.

### Length and other limits
- Base mode: NO explicit word count in base-en.txt. Evidence from official Context-IR outputs embedded in the README: T2VA 10 s example = ~2,500 chars / ~380 words total; I2VA 8 s = ~4,500 chars / ~720 words; Ref2VA 5 s = ~3,600 chars / ~540 words. So official IR prompts are long and dense.
- Duration 4-15 s; description timing must match the requested duration (SKILL.md: "Always match the total duration of the description to the requested video length (4–15 seconds).").
- Hosted prompt limit: fal states "prompts run up to 7,000 characters" (third-party host, low). Official API page for the H3 create endpoint could not be read (see unverified list).

### Things to avoid (SKILL.md + guides)
- "Avoid plot summaries, unresolved reference labels, and timing that does not match the requested duration."
- "Prefer concrete visual and audio details over abstract words like \"cinematic\" or \"beautiful\"." (Note: `Cinematic` is still a legal *style* keyword at the start of Shot 1.)
- No abstract mood words in non_diegetic_music; no dialogue repeated in the two audio fields; no translating or rewriting text inside `<d>`; no timestamp on Shot 1; no camera labels stacked at sentence end; no negative prompt (CFG-distilled).
- "Write rewrite sections in English; preserve dialogue, lyrics, and visible scene text in their original language."

### Corrections to what you had
- Dialogue verb form is `(S1) says: <d>[English] ...</d>` with a speaker ID; `She says <d>...` without `(S1)` is incomplete per the official guide.
- Ref2VA has six sections including `retention_analysis`.
- The community HF discussion #28 "System Prompt IT2V" (time-coded `[0s-2s]` blocks) is unofficial and contradicts the official guide; do not use it.

### Sources
- https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/references/base-en.txt — all base-mode format rules (read directly)
- https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/references/ref-en.txt — all Ref2VA rules (read directly)
- https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/SKILL.md — mode routing, output rules, 4-15 s
- https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/README.md — specs, checkpoints, Qwen3-VL-32B, `<d>` special token, CFG-distilled, Context-IR not open, example IR prompts, request JSON
- https://huggingface.co/MiniMaxAI/MiniMax-H3 — model card, links to docs/VIDEO_PROMPT_WRITING_GUIDE_*_en.md
- https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE — license terms (via summarizer)
- https://www.minimax.io/blog/minimax-h3 — announcement date 2026-07-31
- https://docs.comfy.org/tutorials/video/minimax/minimax-h3 and https://docs.comfy.org/tutorials/video/minimax/minimax-h3-prompt-guide — 1344x768, multiples of 32, 17k+5 frame grid, `embedding:` style embeddings
- https://platform.minimax.io/docs/guides/video-generation — hosted H3 / H3 Max specs
- https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/28 — community (unofficial) system prompts
- https://fal.ai/learn/devs/minimax-h3-prompting-guide — third-party hosted-endpoint advice, 7,000 char claim

---

## 2. Hailuo video: MiniMax-Hailuo-2.3, 2.3-Fast, 02, Director   — confidence: MEDIUM-HIGH
(official API reference pages, read through WebFetch summarizer; now marked "legacy" in the model catalog, superseded by H3)

Facts
- T2V models: `MiniMax-Hailuo-2.3`, `MiniMax-Hailuo-02`, `T2V-01-Director`, `T2V-01`. `prompt` required.
- I2V models: `MiniMax-Hailuo-2.3`, `MiniMax-Hailuo-2.3-Fast`, `MiniMax-Hailuo-02`, `I2V-01-Director`, `I2V-01-live`, `I2V-01`. `prompt` optional; `first_frame_image` required. 2.3-Fast is I2V only.
- Prompt limit: "Text description of the video, up to 2000 characters."
- Camera commands supported by: Hailuo-2.3, 2.3-Fast, 02 and the *-01-Director models (not plain T2V-01 / I2V-01 / I2V-01-live).
- Full list, 15 commands: `[Truck left]`, `[Truck right]`, `[Pan left]`, `[Pan right]`, `[Push in]`, `[Pull out]`, `[Pedestal up]`, `[Pedestal down]`, `[Tilt up]`, `[Tilt down]`, `[Zoom in]`, `[Zoom out]`, `[Shake]`, `[Tracking shot]`, `[Static shot]`.
- Combination rules: "Multiple commands inside one `[]` take effect simultaneously", e.g. `[Pan left,Pedestal up]`; "Recommended max: 3" (a recommendation, not a hard limit). Sequential: place commands in order inside the text, e.g. official example `"A man picks up a book [Pedestal up], then reads [Static shot]."` — the bracket goes right after the clause it applies to. Natural-language camera description also works but "explicit commands yield more accurate results".
- `prompt_optimizer` (bool, default `true`): "Set to `false` for more precise control." `fast_pretreatment` (bool, default `false`): shortens optimizer time; only Hailuo-2.3 / 2.3-Fast / 02.
- No negative prompt parameter in either endpoint.
- Duration/resolution: 2.3 and 2.3-Fast: 768P 6 s or 10 s, 1080P 6 s. 02: 512P (I2V) / 768P 6 or 10 s, 1080P 6 s. 01-series: 720P 6 s.
- I2V image: JPG/JPEG/PNG/WebP, < 20 MB, short edge > 300 px, aspect 2:5 to 5:2.

Profile implication: if your enhancer already writes a full prompt, tell users to set `prompt_optimizer=false`, otherwise MiniMax rewrites it again.

Recommended structure / T2V vs I2V: NO official MiniMax prompt-structure guide was found for Hailuo 02/2.3. Third-party only (low): formula "[Camera command] Subject + visible action + setting + light/look + continuity constraint"; T2V must describe the whole shot, I2V should "Spend words on motion" (motion, camera, stability) instead of restating what the image shows; one location, no time jumps in a 6-10 s clip.

Sources
- https://platform.minimax.io/docs/api-reference/video-generation-t2v — model list, 2000 chars, 15 commands, rules, example, optimizer flags, no negative prompt
- https://platform.minimax.io/docs/api-reference/video-generation-i2v — I2V models, optional prompt, image limits, duration table
- https://platform.minimax.io/docs/guides/models-intro — Hailuo 2.3 / 2.3Fast / 02 listed as legacy
- https://minimax-ai.chat/guide/hailuo-video-prompts/ — THIRD-PARTY structure advice

---

## 3. MiniMax image-01   — confidence: MEDIUM (official pages via summarizer)

- Models: `image-01`, `image-01-live`. No newer dedicated image model found; the current models-intro catalog lists no Image category at all. (A community ComfyUI pack uses H3 for stills; not an official image model.)
- "Text description of the image, max length 1500 characters."
- `prompt_optimizer`: bool, default `false` (opposite default to video).
- No negative prompt parameter documented. No special syntax documented. Plain natural-language / comma-separated descriptors; official examples: "A girl stands by the library window, gazing into the distance" and a tag-style one ending "Fashion photography of 90s, documentary, Film grain, photorealistic". One official example contains ":25" after a phrase, but no weighting syntax is documented; do not emit weights.
- `aspect_ratio`: 1:1 (1024x1024), 16:9 (1280x720), 4:3 (1152x864), 3:2 (1248x832), 2:3 (832x1248), 3:4 (864x1152), 9:16 (720x1280), 21:9 (1344x576). `width`/`height` 512-2048 divisible by 8 (image-01 only). `n` 1-9.
- `subject_reference`: `[{type:"character", image_file: url|base64}]`, single reference image.

Sources
- https://platform.minimax.io/docs/api-reference/image-generation-i2i — limits and parameters
- https://platform.minimax.io/docs/guides/image-generation — example prompts, single reference
- https://platform.minimax.io/docs/guides/models-intro — no image category listed

---

## 4a. MiniMax Music   — API: MEDIUM; Music 3 open model: HIGH

API (`/v1/music_generation`)
- Models: `music-3.0`, `music-2.6`, `music-cover` (+ `-free` variants, being discontinued from 2026-08-20). music-1.5 / 2.0 no longer listed.
- Two separate fields. `prompt` = "A description of the music, specifying style, mood, and scenario." 1-2000 chars when instrumental (required), 0-2000 when vocal (optional); `music-cover`: 10-300.
- `lyrics`: required for vocal, 1-3500 chars (cover: optional 10-1000). Lines separated by `\n`.
- Structure tags: `[Intro]`, `[Verse]`, `[Pre Chorus]`, `[Chorus]`, `[Interlude]`, `[Bridge]`, `[Outro]`, `[Post Chorus]`, `[Transition]`, `[Break]`, `[Hook]`, `[Build Up]`, `[Inst]`, `[Solo]` (API spelling uses a space: `[Pre Chorus]`).
- `is_instrumental` (default false); `lyrics_optimizer` (default false; when true and lyrics empty, lyrics are auto-written from prompt). Cover: `audio_url`/`audio_base64` 6 s - 6 min, <= 50 MB.

Music 3 open weights (github.com/MiniMax-AI/MiniMax-Music3, HF MiniMaxAI/MiniMax-Music3)
- Songs "up to **five minutes**"; 32 kHz 16-bit stereo; inputs = lyrics + music description (SGLang-Omni: lyrics in `input`, description in `instructions`).
- Tags in the open model README: `[Intro]`, `[Verse]`, `[Pre-Chorus]`, `[Chorus]`, `[Post-Chorus]`, `[Bridge]`, `[Instrumental]`, `[Solo]`, `[Outro]` (hyphenated here; differs from API spelling).
- "A concise natural-language description can be used directly." For control, a Structured Caption with three headings in this order: `Global Metadata`, `Vocal Details`, `Arrangement`; rewriter skill defaults to "approximately 250–450 English words", English, never quotes lyrics in the caption, does not invent exact BPM/key.
- Limits: "The tokenized text prompt is limited to 5,000 tokens." "Audio generation is limited to 9,000 acoustic frames." (25 fps).
- License: custom LICENSE on HF, not read (unverified).

Sources
- https://platform.minimax.io/docs/api-reference/music-generation — fields, limits, tags
- https://platform.minimax.io/docs/guides/music-generation — example style prompt, service changes
- https://raw.githubusercontent.com/MiniMax-AI/MiniMax-Music3/main/README.md — open model input format, limits (read directly)
- https://raw.githubusercontent.com/MiniMax-AI/MiniMax-Music3/main/skills/music-caption-rewriter/SKILL.md — structured caption contract (read directly)

## 4b. MiniMax Speech (T2A)   — confidence: MEDIUM

- Models listed: `speech-2.8-hd`, `speech-2.8-turbo`, `speech-2.6-hd/turbo`, `speech-02-hd/turbo`, `speech-01-hd/turbo`. Catalog front page shows only 2.8. No speech-3 found. (speech-2.5 no longer listed.)
- `text` < 10,000 chars (streaming advised above 3,000). Paragraphs = newline.
- Pause marker `<#x#>`, x in seconds, range [0.01, 99.99], max two decimals; must sit between speakable text, not consecutive. Example: `Hello<#0.5#>world`.
- Interjection tags, speech-2.8 only: `(laughs)`, `(chuckle)`, `(coughs)`, `(clear-throat)`, `(groans)`, `(breath)`, `(pant)`, `(inhale)`, `(exhale)`, `(gasps)`, `(sniffs)`, `(sighs)`, `(snorts)`, `(burps)`, `(lip-smacking)`, `(humming)`, `(hissing)`, `(emm)`, `(sneezes)`.
- Emotion is a request PARAMETER (`voice_setting.emotion`), not inline text: `happy`, `sad`, `angry`, `fearful`, `disgusted`, `surprised`, `calm`, `fluent`, `whisper`. Model picks emotion automatically by default; manual only when needed. `fluent`/`whisper` are restricted to certain model families (summarizer output was contradictory about 2.6 vs 2.8 — unverified).
- voice_setting: speed [0.5, 2], vol (0, 10], pitch [-12, 12]. `pronunciation_dict.tone`: `["resume/(rɪˈzjuːm)", "处理/(chu3)(li3)"]`. `timbre_weights`: mix up to 4 voices, weight 1-100. `voice_modify`: pitch/intensity/timbre -100..100 plus one sound effect (`spacious_echo`, `auditorium_echo`, `lofi_telephone`, `robotic`). `language_boost`: language name or `auto`.
- Multi-speaker: no multi-speaker/dialogue syntax documented; one voice_id per request => split script per speaker and make one call each.

Sources
- https://platform.minimax.io/docs/api-reference/speech-t2a-http — all of the above
- https://platform.minimax.io/docs/guides/models-intro — current catalog

---

## 5. Could NOT verify
- Official H3 hosted-API parameter page (https://platform.minimax.io/docs/api-reference/video-generation-v2-create and .../video-generation-v2-h3-context-ir): fetch was blocked; prompt character limit for the official H3 API not confirmed (only fal's 7,000-char claim).
- Exact date the H3 weights went public (blog 2026-07-31 says "coming days"; license 2026-08-02; third-party news 2026-08-03).
- Any official recommended word count for base-mode `integrated_multimodal_description` (none stated; only example lengths).
- Exact language-tag spellings other than `[English]` (no official list of tag strings; inferred to be full English language names).
- Whether `<scenetrans>` / `<cutoff>` are registered special tokens like `<d>` (README says "several special tokens, such as `<d>`" without listing them; tokenizer config on HF not readable from here).
- No Chinese-language guide files found in the skill folder; HF `docs/` folder listing not enumerated.
- Official Hailuo 02/2.3 prompt-structure guide: not found (third-party only).
- Speech `fluent` / `whisper` model availability: contradictory summarizer output; check the page by hand.
- Music3 and H3 license clause wording: read via summarizer only.
- Newer MiniMax image model: none found.
- The 8 other H3 repo skills (style generators) depend on MiniMax Hub tools and were not read.
