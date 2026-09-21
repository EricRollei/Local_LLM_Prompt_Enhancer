# Video model prompting research (for ComfyUI LLM prompt-enhancer platform profiles)

Research date: 2026-09-20. Confidence labels: **high** = official source read directly (repo file cloned / vendor doc fetched); **medium** = official but indirect (vendor doc summarised by fetch tool, or official-but-adjacent); **low** = third-party only.
Method notes: GitHub repos were cloned / raw files downloaded and read verbatim. Vendor web docs were read through a fetch-and-summarise tool, so wording of quotes from web docs may be lightly paraphrased. huggingface.co was not reachable from this environment (proxy 403), so HF model cards were NOT read directly.

Official rewriter / enhancer system-prompt files (raw URLs) are collected in the last section.

---

## 1. Wan 2.2 (Alibaba Tongyi / Wan team) and later Wan releases

### 1.1 Release status matrix

| Version | Weights | Audio generation | Notes |
|---|---|---|---|
| Wan 2.1 (Feb 2025) | Open, Apache-2.0 | No | T2V 1.3B/14B, I2V 14B, VACE, FLF2V |
| Wan 2.2 (Jul 2025) | Open, Apache-2.0 | No (silent). S2V-14B is audio-*driven* (audio in, not out); Animate-14B is video-driven | T2V-A14B, I2V-A14B (MoE high/low-noise experts, boundary 0.875), TI2V-5B (24 fps, 121 frames, 720p) |
| Wan 2.5 (preview, Sep 2025) | API only | Yes ("automatic dubbing" or custom `audio_url`) | 5 or 10 s; prompt <= 1500 chars |
| Wan 2.6 (Dec 2025) | API only | Yes | 2-15 s; multi-shot; reference-to-video (`character1` ...); prompt <= 1500 chars |
| Wan 2.7 (API ids `wan2.7-i2v-2026-04-25`, `wan2.7-t2v-2026-06-12`) | API only | Yes (generates BGM/SFX when no `audio_url`; `driving_audio` supported) | 2-15 s; 720P/1080P; prompt <= 5000 chars |
| Wan 3.0 (public beta Aug 2026 per third parties) | API only as of research date. `github.com/AlibabaCloud-Official/Wan3.0` exists but is a marketing README with NO weights/code | Yes | native 30 s, up to 20 reference assets (README claims) |
| Wan-Dancer-14B (Jul 2026) | Open (official `Wan-Video/Wan-Dancer` repo) | Music-driven dance video (audio in) | niche |

Verified by probing: `Wan-Video/Wan2.5`, `Wan2.6`, `Wan2.7`, `Wan3`, `Wan3.0` repos do not exist (404) on GitHub; `Wan-Video/Wan2.1`, `Wan2.2`, `Wan-Dancer` exist. Third-party SEO sites contradict each other on Wan 3.0 open weights (wan27.org claims open 1.3B/14B weights; atlascloud and wavespeed, both of which checked the official orgs on Aug 20-25 2026, say no weights). Treat "Wan 3.0 open weights" as **not found / unconfirmed**.

### 1.2 Core facts (Wan 2.2 open weights)

- Developer: Alibaba (Wan team / Tongyi Lab).
- Text encoder: **umT5-XXL** (`google/umt5-xxl` tokenizer), `text_len = 512` tokens (hard truncation). Multilingual; Chinese and English both first-class.
- Caption style: dense prose. Official rewriter output for T2V = leading comma-separated cinematic tags (lighting, shot size, composition, tone) followed by descriptive sentences. Style phrase goes FIRST if a style is specified.
- Recommended length: official T2V rewriter targets **60-200 words** (ZH: 60-200 字); official I2V rewriter targets **<= 100 words**. Hosted API limit for wan2.2: 800 characters; negative prompt 500 chars.
- Negative prompt: **supported** (CFG; guide scale (3.0, 4.0) low/high noise for A14B, 5.0 for 5B). Note: distilled/LightX2V-style 4-step LoRA workflows run CFG=1 where the negative prompt has no effect (community knowledge, not from an official source).
- Standard Chinese negative prompt (verbatim from `wan/configs/shared_config.py`):
  `色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走`
- Audio: none in 2.2. Never write dialogue/sound cues for Wan 2.2 (wasted tokens). The words "speaks/talks" are fine as *visual* motion ("a man talks, his gestures lively").
- Defaults: 16 fps, 81 frames (~5 s) for A14B; 24 fps, 121 frames for TI2V-5B. Actions must fit ~5 s.

### 1.3 Official prompt formula (Alibaba Cloud Model Studio guide)

- Basic: **Entity + Scene + Motion**.
- Advanced: **Entity description + Scene description + Motion description + Aesthetic control + Stylization**. Aesthetic control = light source, lighting environment, shot size, camera angle, lens, camera movement. Motion description should carry amplitude/speed ("swaying violently", "moving slowly").
- I2V: **Motion + Camera movement** only. The image already defines entity, scene and style. Use speed/intensity adverbs; "fixed camera" to lock.
- Sound formula (Wan 2.5/2.6/2.7/3.0 only): Entity + Scene + Motion + **Sound description (voice / sound effect / BGM)**.
  - Voice: `Character's lines + Emotion + Tone + Speed + Timbre + Accent`. Example: *A man doing stand-up comedy says, 'Study hard and make progress every day,' in a relaxed tone, at moderate speed, with a clear voice, in American English.*
  - SFX: `Source material + Action + Ambient sound`. BGM: `Background music/score + Style`.
  - Multi-speaker rules: unique consistent labels (no pronouns), bind each line to a visible action ("The agent slams his hand on the table. [Black-suited Agent, angrily]: 'Where is the truth?'"), distinct voice label per character, explicit temporal linking words ("Immediately, ...") so lines do not merge.
  - Suppression phrases (2.7/3.0 reference-to-video): "No dialogue.", "No background music."
- Multi-shot (2.6/2.7/3.0): `Overall description + Shot number + Timestamp + Shot content`, e.g. `Shot 1 [0-3 s] ...`. For a single shot on 2.7 write "Generate single shot."
- Reference-to-video: 2.7/3.0 use "Image 1"/"Video 1" identifiers; 2.6 uses `character1`, `character2`.
- Guide's "do not prompt" list: real people by name, rapid scene changes within a clip, exact legible text, very long action sequences, exact lip-sync to specific words.

### 1.4 Vocabulary the official rewriter draws from (verbatim English lists in `T2V_A14B_EN_SYS_PROMPT`)

- Time: Day time, Night time, Dawn time, Sunrise time (default Day time)
- Light source: Daylight, Artificial lighting, Moonlight, Practical lighting, Firelight, Fluorescent lighting, Overcast lighting, Sunny lighting
- Intensity: Soft lighting, Hard lighting. Angle: Top lighting, Side lighting, Underlighting, Edge lighting
- Tone: Warm colors, Cool colors, Mixed colors
- Shot size: Medium shot, Medium close-up shot, Wide shot, Medium wide shot, Close-up shot, Extreme close-up shot, Extreme wide shot (default Medium or Wide)
- Angle: Over-the-shoulder shot, Low angle shot, High angle shot, Dutch angle shot, Aerial shot, Overhead shot (omit if user gave camera movement)
- Composition: Center, Balanced, Right-heavy, Left-heavy, Symmetrical, Short-side composition
- Camera movement phrasing seen in official examples / Model Studio guide: "camera pushes in", "camera pulls back/out", "camera moves left/right", "the camera pans up", "camera tilts downward", "tracking shot", "orbit (keep arc under 45 degrees)", "fixed camera", compound moves (drone shot, fly-through, tilt up). The EN rewriter prompt picks **at most 4** aesthetic tags.

### 1.5 Rewriter behaviour worth copying (from the system prompts)

- Do not change subject/action; do not add subjects that were not in the prompt (no people added to landscapes).
- Do NOT output literary mood sentences ("the scene is full of tension").
- Describe the motion process in detail; if no motion is given, add some (body sway, clouds drifting, wind in leaves).
- Style: if absent do not add one; if present put it first; for 2D/illustration styles skip the cinematic-lighting tags.
- Sky mentioned -> rewrite as "azure blue sky" to avoid overexposure.
- I2V: keep dynamic parts, keep and emphasise camera-move text, remove descriptions of static things already visible in the image, expand bare verbs using the image ("dancing" -> "a girl is dancing"), <= 100 words. There is a separate "EMPTY" prompt for I2V with no user text (imagine plausible motion from the image).
- CAUTION: rules 8-10 of the T2V prompts are vendor content-moderation rules that silently *replace* the user's prompt (including for same-sex kissing and bikini content). They are policy, not prompting technique; do not copy them into a local enhancer.

### 1.6 Do / Don't

Do: 80-120 words EN, tags first then prose; explicit motion verbs with speed; one camera move; Chinese or English.
Don't: exceed 512 tokens; write audio cues; describe the image in I2V; ask for legible text; pile multiple scene cuts into 5 s.

### Sources
- https://raw.githubusercontent.com/Wan-Video/Wan2.2/main/wan/utils/system_prompt.py — all six official rewriter prompts, length targets, vocab lists (**high**, read verbatim)
- https://raw.githubusercontent.com/Wan-Video/Wan2.2/main/wan/configs/shared_config.py — umT5-XXL, text_len 512, negative prompt, 16 fps/81 frames (**high**)
- https://github.com/Wan-Video/Wan2.2 (README) — prompt extension methods (Dashscope / local Qwen), S2V, Animate, guide scales (**high**)
- https://www.alibabacloud.com/help/en/model-studio/text-to-video-prompt — official formulas, sound formula, multi-shot, version compatibility table, camera/style vocab (**medium**: official page, read via summariser)
- https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference and https://www.alibabacloud.com/help/en/model-studio/legacy-wan-text-to-video-api-reference and https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference — char limits, negative_prompt 500 chars, audio behaviour, durations, `prompt_extend` default true (**medium**)
- https://raw.githubusercontent.com/AlibabaCloud-Official/Wan3.0/main/README.md — Wan 3.0 feature claims, no weights present (**high** for "no weights in that repo")
- https://www.atlascloud.ai/blog/tips/is-wan-3.0-open-source , https://wavespeed.ai/blog/video-model-access/is-wan-3-0-open-source/ — Wan 2.5-3.0 API-only as of late Aug 2026 (**low**); https://wan27.org/blog/wan-3-open-source claims the opposite (**low**, judged unreliable: also wrongly says Wan 2.5 has no audio)

---

## 2. LTX-2 / LTX-2.3 / LTX-2.5 (Lightricks) — joint audio + video, open weights

### 2.1 Versions
- **LTX-2** (Jan 2026, 19B): Gemma 3 12B text encoder. [parameter count from memory, not re-verified: medium]
- **LTX-2.3** (22B, dev + distilled 1.1; "legacy" in the repo now): Gemma 3 12B (`google/gemma-3-12b-it-qat-q4_0-unquantized`), redesigned text connector, better audio.
- **LTX-2.5** (repo changelog 1.2.0, **2026-08-11**): 22B dev + distilled transformers, **Gemma 4 12B fine-tuned for LTX** (`gemma4-12b-with-proj-ltx-2.5`, stock Gemma 4 is not a substitute), diffusion video-VAE decoder, separate audio VAE, optional **duration head** (clip length predicted from the caption), DFR pipeline up to 4K, Dub-It, A2Vid, Retake, HDR. License: LTX community license (free under $10M ARR, per LTX blog). ComfyUI: `Lightricks/ComfyUI-LTXVideo` (has 2.5 workflows).
- Tokenizer pads/truncates prompts to **1024 tokens** (hard limit, from `base_encoder.py`).

### 2.2 Caption style and length
- **Single flowing paragraph, present tense, chronological, literal.** No headings, no "Audio:" / "Visual:" labels, no bullet lists. Start directly with the action (never "The scene opens with...").
- README: "Keep within 200 words." Blog guides: 4-8 descriptive sentences; LTX-2.3+: "longer, more descriptive prompts consistently outperform short ones"; make sure prompt content fills the clip duration (8-10 s) or the model rushes.
- LTX-2.5 official enhancer target: **roughly 150-220 words**. LTX-2/2.3 enhancer: `max_new_tokens` 512.
- README structure: main action in one sentence -> movements/gestures -> appearances -> background/environment -> camera angles and movements -> lighting and colours -> changes/sudden events.
- Blog six elements: establish the shot; set the scene; describe the action; define characters (age, hair, clothing; emotion via physical cues); camera movement; **describe the audio**.
- Optional leading style tag (Gemma-3 enhancer): `Style: <style>, <rest of prompt>`; default cinematic-realistic; omit if unclear. Screenplay sluglines ("INT. OVEN - DAY.") appear in official examples for longer scenes.

### 2.3 Audio, dialogue, music
- Spoken words go in **quotation marks**, with a speaker identified by visual description and **voice characteristics** ("The man says in an excited voice: 'You won't believe what I just saw!'"). State language if not English, accent if relevant; write non-English dialogue in its **native script**.
- Never alter user-supplied dialogue; do **not invent dialogue** unless the user mentions speech/singing/conversation (I2V enhancer: if the user says "is talking" with no text, generate contextual quoted dialogue).
- Soundscape woven **chronologically alongside the actions, not dumped at the end** (I2V enhancer says this explicitly). Be specific ("soft footsteps on tile", "espresso machine hiss") not vague ("ambient sound").
- Music: type, mood, volume changes; for multi-shot state whether audio "continues across the cut".
- Dialogue acting (LTX-2.3 guide): **segment dialogue** into short quoted phrases with one acting direction between them (gaze / pause / voice quality / physical beat). One cue per beat; over-directing gives twitchy results. One unbroken quoted block gets rushed. Acoustic space ("faint room tone", "echo of a marble lobby") can be added.
- Volume words respond: whisper, mutters, shouts, screams. Voice types: "energetic announcer", "robotic monotone", "distorted radio-style".

### 2.4 Camera vocabulary
follows, tracks, pans across, circles around, tilts upward, pushes in / pulls back, overhead view, handheld movement, over-the-shoulder, wide establishing shot, static frame, slow dolly, crane, zoom; temporal: slow motion, time-lapse, lingering shot, continuous shot, freeze-frame, fade-in/out. Multi-shot (2.5): name the edit in prose ("A hard cut transitions to...", match cut, dissolve); 2-4 cuts; re-establish framing and subjects after each cut.
- **Version difference (important):** the Gemma-3 enhancer (LTX-2/2.3) says "DO NOT invent camera motion unless requested". The Gemma-4 enhancer (LTX-2.5) says camera motion must **always be stated** (or explicitly "the camera remains static"), along with exactly one shot type (extreme wide / wide / medium / medium close-up / close-up / extreme close-up) and a viewpoint (front-facing / back-facing / side view / over-the-shoulder / top-down / low-angle / high-angle), all woven into prose, never as tags.
- LTX-2.5 transitions: "Initially...", "A moment later...", "Simultaneously...". LTX-2/2.3: "as", "then", "while".

### 2.5 I2V rules
- LTX-2/2.3 enhancer: describe **only changes from the image**; do not reiterate established visual details ("Inaccurate descriptions may cause scene cuts"); concise, action-focused.
- LTX-2.5 enhancer: the opposite emphasis — the caption's opening must **match the reference image exactly** (subject, clothing, setting, lighting, composition), then narrate the requested action; single continuous take, no hard cuts.
- Both: no timestamps / cuts unless requested.

### 2.6 Negative prompt
Supported on the full (dev) model with CFG/STG pipelines; ignored by the distilled pipelines (no CFG). Official default (from `ltx_pipelines/utils/constants.py`) is an English list that includes audio terms; starts: `has_subtitles, has_blurbox, transition from black, transition to black, speech_ending_short, blurry, out of focus, overexposed, ...` and ends `... mismatched lip sync, silent or muted audio, distorted voice, robotic voice, echo, background noise, off-sync audio, incorrect dialogue, added dialogue, repetitive speech, jittery movement, awkward pauses, ... cinematic oversaturation, stylized filters, or AI artifacts.`

### 2.7 Things to avoid (official)
Emotion labels without physical cues ("sad"); readable text/logos; complex physics / chaotic motion (jumping, juggling; dancing is fine); too many characters or layered actions; conflicting light sources; non-visual senses (smell, taste, touch); intensified colour/lighting words ("vibrant blue", "blinding light") — use plain, restrained terms; inferring ethnicity/nationality (2.5 enhancer); starting with punctuation; reusing LTX-2 prompts unmodified on 2.3.

### Sources
- https://github.com/Lightricks/LTX-2 (README, CHANGELOG.md, MODELS-LTX-2.3.md; cloned 2026-09-20) — versions, Gemma 4, 200-word rule, structure list, `enhance_prompt` (**high**)
- Enhancer system prompts in `packages/ltx-core/src/ltx_core/text_encoders/gemma/encoders/prompts/` (gemma3_* and gemma4_*; raw URLs at end) (**high**, read verbatim)
- https://github.com/Lightricks/ComfyUI-LTXVideo `system_prompts/gemma_t2v_system_prompt.txt`, `gemma_i2v_system_prompt.txt` — byte-identical to the gemma3_* files; no gemma4 prompt files in that repo as of 2026-09-17 commit (**high**)
- `packages/ltx-pipelines/src/ltx_pipelines/utils/constants.py` — DEFAULT_NEGATIVE_PROMPT (**high**); `base_encoder.py` — 1024-token padding, 512/600 max_new_tokens (**high**)
- https://ltx.io/model/model-blog/prompting-guide-for-ltx-2 — six elements, camera vocab, avoid list, examples (**medium**)
- https://ltx.io/blog/ltx-2-3-prompt-guide , https://ltx.io/blog/directing-dialogue-and-acting — longer prompts, dialogue segmentation (**medium**)
- https://ltx.io/blog/ltx-2-5-prompt-guide — 2.5 multi-shot prose cuts, native-script dialogue, I2V single take (**medium**)
- Max clip duration: **not found** in sources read.

---

## 3. HunyuanVideo 1.5 (Tencent Hunyuan) — open weights, silent

- 8.3B DiT, T2V + I2V, 480p/720p + SR to 1080p, 5-10 s. Tencent Hunyuan Community License. Last repo commit 2026-04-10; no newer HunyuanVideo release found.
- Text encoder: **MLLM = Qwen2.5-VL-7B-Instruct** (recommended open substitute for the unreleased HunyuanMLLM; max_length 1000 tokens in pipeline) + **Glyph-ByT5** for in-video text (`byt5_max_length = 256`).
- Audio: **none**. (HunyuanVideo-Foley is a separate V2A model.) Do not write sound cues.
- Negative prompt: supported (`--negative_prompt`, default empty string). Distilled (CFG/step-distilled) checkpoints ignore it.
- Languages: Chinese and English. Official T2V rewriter outputs **English**; official I2V rewriter outputs **Chinese** ("无论用户输入是中文还是英文，你的输出都必须是中文").

### Handbook formulas
- T2V: `Prompt = Subject + Motion + Scene + [Shot Type] + [Camera Movement] + [Lighting] + [Style] + [Atmosphere]`.
- I2V: `Prompt = Subject Motion Dynamics + Scene Motion Dynamics + [Camera Movement]`.
- README: "By writing longer and more detailed prompts, the generated video will be significantly improved." Handbook also says keep vocabulary and grammar simple and direct.
- Temporal sequencing: "First... then... next... meanwhile... finally..."; objective detail instead of emotion words ("The boy smiles, eyes crinkling slightly"); precise frame-relative directions (left/right side of the frame, foreground/background); disambiguate multiple characters by attribute or position.
- In-video text: put it in quotes — English prompt uses "" ; Chinese prompt uses “”. Never spell text letter by letter.

### Official T2V rewrite system prompt (key rules)
- Structure, general to specific: (1) one-sentence **summary** naming all main subjects; (2) subject detail; (3) **chronological action sequence** with "Initially / Then / Next / As / Finally"; (4) environment/background; (5) closing technical + style block in short declaratives ("The camera pans right. Low angle. Sense of adventure.").
- Present tense, declarative, objective tone.
- **Length budget: ~140 words for the main subject (mostly its action) + ~70 words background + <= 140 words for composition/lighting/style/atmosphere/angle/shot type** (~300-350 words total).
- Mention the core style **3-5 times** and end with a style sentence ("The entire video is in a cinematic realistic style."). Default style: **cinematic realistic style**.
- Duration fixed at **5 s**: all action must be completable in 5 s.
- Entities: keep exact user counts; if vague ("a group"), cap at **three or fewer**, placed mid/foreground with uncropped limbs.
- Convert non-visual ideas to visuals (a sound cue becomes a visible event: birdsong -> birds in scene).
- Camera: obey the user; if none given, shot line must be "The shot is at an eye-level angle with the main subject." and movement chosen from static / push forward / pull back / pan right / pan left / zoom in / zoom out, preferring slight motion.
- Never name invisible light sources; do not name composition techniques (arrange elements instead); flag high-risk items (sparks, lightning, sweat, complex sports physics, dynamic typography); state orientation of phone screens/camera lenses.
- Typography mode: start with `The words "[Text]" rendered as ...`, front/top-down view, centred, end with "The entire [phrase] is fully visible"; avoid "huge", "close-up", "intricate".

### Camera control keyword library (rewriter maps user intent to these canonical English phrases)
"The camera rotates 360 degrees" · first-person/FPV view · "The camera moves upward / rises / ascends" · moves downward/descends · low angle · tilts up / tilts down · ground-level shot · "The camera pushes forward" · pulls back · moves (trucks) left / right · time-lapse · macro shot · slow motion · zooms in / zooms out · pans left / pans right · drone view · "The camera orbits the subject" · "The camera follows the subject" · over-the-shoulder · rotates clockwise / counter-clockwise · "The camera remains still/static" · high angle · fisheye lens · bird's-eye view. Dynamic combos allowed ("Initially the camera follows..., then pulls back...").

### Official I2V rewrite system prompt (key rules)
- Standardise camera phrases (pull back, push forward, move up/down/left/right, pan, follow, orbit, static, handheld) but **never add camera moves the user did not ask for** — including never adding "camera remains static".
- Break motion into a micro time-sequence with connectives (then / next / meanwhile / afterwards).
- Objective subject-adverb-action chains; precise frame positions for entering/exiting objects; resolve pronouns into explicit entities.
- **Restrained association**: no new key events; **never add lighting/shadow descriptions** unless asked (and never say "no lighting changes"); output length proportional to user input. Official examples are 1-4 sentences.

### Do / Don't
Do: English ~300 words T2V; short motion-only I2V; repeat the style phrase; limit to 3 subjects; 5-second action budget.
Don't: audio cues; invisible light sources; many subjects; lighting text in I2V; letter-by-letter text.

### Sources
- https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5 (README; cloned) — rewrite recommendations (Qwen3-235B-A22B-Thinking for T2V, Qwen3-VL-235B-A22B-Instruct for I2V), `--negative_prompt` (**high**)
- `hyvideo/utils/rewrite/t2v_prompt.py`, `hyvideo/utils/rewrite/i2v_prompt.py` (raw URLs at end) (**high**, read verbatim, Chinese-language prompts)
- https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/assets/HunyuanVideo_1_5_Prompt_Handbook_EN.md — formulas, text rendering quotes, camera library, sequencing rules (**high**)
- `checkpoints-download.md` — Qwen2.5-VL-7B-Instruct as text encoder; pipeline file for byT5 length (**high**)

---

## 4. Closed / API models

### 4.1 Kling (Kuaishou) — latest confirmed: Kling VIDEO 3.0 and 3.0 Omni (Feb 2026). "Kling 4.0" appears only on third-party speculative pages: **not found** as released.
- Text encoder: not disclosed.
- Structure: natural-language cinematic prose; model infers angles from film language. **Multi-shot**: toggle, or custom form `Shot 1: [description], duration X seconds / Shot 2: ...`. API (fal mirror): `multi_prompt` list, `shot_type` = `customize` | `intelligent`.
- Audio: native (dialogue, SFX, ambience). Dialogue syntax from the official guide: `Character Name (tone descriptor, language): "line"`, e.g. `Mom (softly, in a surprised tone): Wow, I didn't expect this plot`. Omni guide uses prose form: "the male lead says in a relaxed tone, '...'". Languages: Chinese, English, Japanese, Korean, Spanish; dialect/accent in parentheses ("(in Cantonese)", "(British accent)"). Simple grammar works better. Tone words: whispers, exclaims, cheerfully, gently, low flat voice.
- Negative prompt: **supported as a separate API field** (fal schema default `"blur, distort, and low quality"`); not mentioned in the vendor's 3.0 guide. `cfg_scale` default 0.5.
- Limits: 3-15 s, 720p/1080p, 16:9 / 9:16 / 1:1. Prompt character limit: **not found** in official sources read (older Kling API docs used 2500 chars; unverified for 3.0 — the official API doc page would not render).
- Camera vocab: zoom in/out, pan, tracking, orbit / 360-degree rotation, push in / pull back, handheld, close-up/medium/wide.
- I2V: describe motion and camera; start/end frames supported. Omni supports element/voice references.
- Sources: https://kling.ai/quickstart/klingai-video-3-model-user-guide (**medium**), https://kling.ai/blog/kling-video-3-omni-native-lip-sync-audio-guide (**medium**), https://fal.ai/models/fal-ai/kling-video/v3/standard/text-to-video/api (**low/partner**), https://kling.ai/document-api/apiReference/model/textToVideo (unreadable, JS-rendered).

### 4.2 Google Veo 3.1 (latest Veo; Oct 2025). No Veo 4 as of research. Google announced "Gemini Omni" at I/O May 2026 (third-party report, **low**); its prompting guidance was not researched.
- Model IDs: `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`, `veo-3.1-lite-generate-preview`, `veo-3-*`.
- Formula (Google Cloud blog): **[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]**. Gemini API doc elements: subject, action, style, camera positioning/motion, composition, focus/lens, ambiance.
- Audio syntax (official): dialogue in quotes — `A woman says, "We have to leave now."`; `SFX: thunder cracks in the distance`; `Ambient noise: the quiet hum of a starship bridge`. Gemini doc: quotes for speech, explicit SFX description, ambient soundscape description.
- Timestamp prompting (official): `[00:00-00:02] Medium shot ... [00:02-00:04] Reverse shot ...` within one 8 s clip.
- Subtitle avoidance (third-party, Replicate blog, **low**): write speech after a **colon without quotes** (`A guy says: My name is Ben`), add `(no subtitles)`, repeat "No subtitles." if needed. Official docs do not cover subtitles.
- Negative prompt: supported as a parameter. Official rule (Vertex guide): do NOT use "no"/"don't"; list the unwanted things ("wall, frame"). In-prompt alternative from the blog: describe the absence positively ("a desolate landscape with no buildings or roads").
- Limits: 4/6/8 s (8 s required for 1080p/4k/reference images), 720p/1080p/4k, 16:9 or 9:16, 24 fps, up to 3 reference images ("ingredients"), first+last frame. Prompt token limit: **not found** in the pages read (1024 tokens is commonly cited; unverified here).
- Camera vocab: dolly shot, tracking shot, crane shot, aerial view, slow pan, POV shot, arc shot; wide/close-up/extreme close-up/low angle/two-shot; shallow depth of field, wide-angle lens, macro lens, rack/soft/deep focus.
- I2V: describe motion/camera/audio; "Using the provided images for the detective, the woman, and the office setting, ..." for ingredients.
- Official rewriter system prompt: **not found** (Vertex has an `enhancePrompt` option; its prompt is not public).
- Sources: https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1 (**medium**), https://ai.google.dev/gemini-api/docs/veo (**medium**), https://cloud.google.com/vertex-ai/generative-ai/docs/video/video-gen-prompt-guide (**medium**), https://replicate.com/blog/using-and-prompting-veo-3 (**low**).

### 4.3 Seedance (ByteDance Seed) — latest confirmed: Seedance 2.0 ("Dreamina Seedance 2.0 series" on BytePlus ModelArk). "Seedance 2.5" seen only in a third-party page title: **not verified**.
- Official guide exists (https://docs.byteplus.com/en/docs/ModelArk/2222480) but is JS-rendered and could not be read; everything below is second-hand.
- Formula attributed to the official guide: **subject + motion + environment + camera + aesthetics + audio** (fal and heyuan110 agree). Another third party (apiyi) reports "Subject, Action, in Environment, camera ..., style ..., avoid Constraints".
- References: up to 12 files (9 images, 3 videos, 3 audio) cited in the prompt as `@image1`, `@video1`, `@audio1`.
- Audio: native. Dialogue in **double quotes**, short lines (long monologues drift out of sync; split across cuts). Name the sounds wanted; write "no music" when you mean it. Subtitles/on-screen titles can be requested: text content + when + where + how it enters + styling.
- Multi-shot: "cut to" / "then the camera moves to" in one generation.
- Camera vocab: dolly, pan, tilt, crane, push-in, pull-out, tracking, orbit, aerial, handheld, rack focus, locked-off/fixed. Third-party advice: one primary camera move, keep subject motion and camera motion in separate clauses, 60-100 words.
- Negative prompt: no separate field documented; third parties put "avoid jitter, avoid bent limbs, avoid identity drift" inline. Hard prompt-length limit: **not found**. Duration 4-15 s (or auto).
- Seedance 1.0 (from memory, unverified here): prose prompt = subject + action + scene + camera + style; multi-shot via "cut to"; silent.
- Sources: https://fal.ai/learn/tools/seedance-2-0-prompting-guide (**low/partner**), https://www.heyuan110.com/posts/ai/2026-07-11-seedance-2-prompt-guide/ (**low**), https://help.apiyi.com/en/seedance-2-0-prompt-guide-video-generation-camera-style-tips-en.html (**low**).

### 4.4 OpenAI Sora 2 / Sora 2 Pro — **being discontinued**: Sora app ended 2026-04-26; **Sora API ends 2026-09-24** (OpenAI Help Center). A profile is only useful for third-party hosts, if any remain.
- Official anatomy (OpenAI cookbook):
  ```
  [Prose scene description]

  Cinematography:
  Camera shot: [framing and angle]
  Mood: [overall tone]

  Actions:
  - [beat 1]
  - [beat 2]

  Dialogue:
  - Character: "Line"
  ```
- Length: short = more model freedom; long = more control. Describe motion in beats/counts ("takes four steps to the window, pauses, pulls the curtain in the final second"). Style is the strongest lever; set it early. One camera move + one subject action per shot.
- Audio: native. Dialogue in a labelled `Dialogue:` block below the visuals, consistent speaker labels, brief lines (4 s ~ one or two exchanges). Ambient sound cues as short phrases ("distant traffic hiss").
- Size/duration are **API parameters, not prose**: `seconds` 4/8/12/(16/20 per the current cookbook); `size` 1280x720 / 720x1280 (pro adds 1792x1024, 1920x1080 etc.).
- Negative prompt: none. I2V: `input_reference` image must match output resolution; acts as first frame; prompt describes what happens next.
- Camera vocab: wide shot eye level; medium close-up; aerial wide; slow dolly-in; tracking; handheld; shallow depth of field; lens and film-stock names respond.
- Sources: https://developers.openai.com/cookbook/examples/sora/sora2_prompting_guide (**medium**), https://help.openai.com/en/articles/20001152-what-to-know-about-the-sora-discontinuation (**medium**).

### 4.5 Runway Gen-4 / Gen-4.5 (Gen-4.5 is current; no Gen-5 mentioned in help center)
- T2V structure: `[Camera] shot of [subject] [action] in [environment]. [Supporting descriptions]`. I2V structure: `The camera [motion] as the subject [action]. [Additional descriptions]`.
- I2V: describe **motion only** (subject, environment, camera, timing, direction/speed); refer to "the subject / she / the woman"; add visual description only for new elements or transformations. Do not contradict motion implied by the image. To stop unwanted cuts add "Continuous, seamless shot".
- **Positive phrasing only** — no negative prompts ("Locked camera. The camera remains still." instead of "no camera movement"). No conversational/command language. Simple, direct; Gen-4 guide says start minimal and add one element at a time; single scene.
- Timestamps supported: `[00:00 through 00:02] looking away, then turns towards camera`; or natural "X, then Y".
- Audio: **none documented** for Gen-4.5 in the help pages read. 2-10 s, 720p, 24/25 fps. Prompt character limit: **not found** in help pages (Runway API historically 1000 chars; unverified here).
- Camera vocab: locked/static, handheld, dolly, pan, tilt, tracking, orbit, crane, zoom, POV.
- Sources: https://help.runwayml.com/hc/en-us/articles/47313737321107-Text-to-Video-Prompting-Guide , https://help.runwayml.com/hc/en-us/articles/48324313115155-Image-to-Video-Prompting-Guide , https://help.runwayml.com/hc/en-us/articles/39789879462419-Gen-4-Video-Prompting-Guide , https://help.runwayml.com/hc/en-us/articles/46974685288467-Creating-with-Gen-4-5 (all **medium**).

---

## 5. Other significant open-weights video models of 2026

### 5.1 MiniMax H3 ("Hailuo 3.0") — MiniMax; open weights 2026-08-03; joint audio + video. THE major new entry.
- 33B dense single-stream "Omni Transformer" (~13B of it in AdaLN branches), text/vision encoder = **full Qwen3-VL-32B** (hidden states from layer 50), 32 kHz **stereo** audio VAE, 24 fps, 4-15 s, 768p base (2K via H3-Regenerate-2K, not yet open). Checkpoints: **H3-Base-FL2VA** (T2VA / first / last / first+last frame) and **H3-Base-Ref2VA** (<= 9 images, <= 3 videos, <= 3 audio, 12 files max). CFG-distilled, so **no negative prompt**. MiniMax H3 Community License (third party: revenue cap $20M). ComfyUI day-0 native support (ComfyUI >= 0.30.0); int8 "convrot" quantisation cuts memory from 123.6 GB to 42.5 GB (Comfy blog) — fits a 96 GB GPU.
- The official rewriter ("H3-Context-IR") is hosted and **not open**, but MiniMax ships an official prompt-writing guide as an agent skill; the model expects a **structured-field prompt**, not free prose:
  ```
  [I2VA only, first line] For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

  integrated_multimodal_description: [Shot 1] Live-action, cinematic, a medium-wide shot frames ... [Shot 2] At 00:05.000, the camera cuts to ...

  overall_soundscape: 1-4 sentences of ambience, physical action sounds, non-verbal human sounds (or N/A only if total silence requested).

  non_diegetic_music: 1-3 sentences: instrumentation, tempo, rhythm, dynamics; no mood words (or N/A).
  ```
- FL2VA / L2VA first lines: "How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video."
- Dialogue syntax: stable speaker IDs `(S1)`, `(S2)`, compound `(S1,S2)`; voice description outside the tag; spoken text inside `<d>[Language] ...</d>` verbatim, never translated: `The young woman with a quiet, breathy voice (S1) says: <d>[English] I get off at the next station.</d>`. Voiceover: "says in an off-screen voiceover: <d>...</d> while his lips remain completely closed." Cross-cut speech uses `<scenetrans>`; truncated speech `<cutoff>`. Diegetic music/singing goes in the main description, not in `non_diegetic_music`.
- 11 stable dialogue languages (Arabic, Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Russian, Spanish).
- Shots: first shot has no timestamp; later shots `[Shot N] At MM:SS.mmm, the camera cuts to ...`. Style words at start of Shot 1: Cinematic, live-action, 2D-animated, 3D CG, claymation, watercolor, vintage film.
- Camera grammar = **type + amplitude + speed**: Zoom In/Out, Push In/Pull Out, Pan Left/Right, Truck Left/Right, Tilt Up/Down, Pedestal Up/Down, Arc Shot, Tracking Shot, Static Shot, Shake Slightly/Strongly, POV, Roll Clockwise/Counterclockwise; "with small/large amplitude"; "at slow/fast speed"; written as a sentence ("The camera pushes in with small amplitude at slow speed toward ...").
- On-screen text in English double quotes, original script preserved. Ref2VA uses six sections: subject_definitions, summary, retention_analysis, detailed_description, overall_soundscape, non_diegetic_music with `<Subject N>`, `<Picture N>`, `<Video N>`, `<Audio N>` labels.
- Prompts are long (README examples show 5.6k-33k prompt tokens including reference media).
- Sources: https://github.com/MiniMax-AI/MiniMax-H3 README (**high**, cloned); `skills/h3-prompt-writing/SKILL.md`, `references/base-en.txt`, `references/ref-en.txt` (**high**, read verbatim); https://blog.comfy.org/p/minimax-h3-day-0-support-in-comfyui (**medium**); https://soloa.ai/blog/open-weight-ai-video-models-compared-2026 (**low**).

### 5.2 Alice T2V 14B — EXISTS. Developer: **Mirage** (gomirage.ai); repo `mirage-video/Alice`, HF `gomirageai/Alice-T2V-14B-MoE`, arXiv 2605.08115 ("Alice v1"). Apache-2.0. Last commit 2026-04-27.
- It is a **Wan 2.2 A14B derivative**: 14B MoE with high-noise/low-noise experts (boundary 0.875), **umT5-XXL**, text_len 512, 16 fps / 81 frames, Wan 3D causal VAE, rCM-distilled to **4 steps**. Its `alice/utils/system_prompt.py` is the Wan 2.2 prompt-extension file (same six prompts; diff shows whitespace only) and its config carries the same Chinese negative prompt.
- Prompt format = **identical to Wan 2.2** (section 1). Silent. At 4-step distillation CFG is effectively off, so the negative prompt is likely inert (inference from the method; config still lists guide scale (3.0, 4.0) and 40 steps as defaults). Resolutions 1280x720, 720x1280, 960x960, 1024x576. I2V config exists in the repo.
- Sources: https://github.com/mirage-video/Alice (**high**, cloned); https://raw.githubusercontent.com/mirage-video/Alice/main/alice/utils/system_prompt.py (**high**).

### 5.3 Others
- FastH3 8-step (FastVideo distillation of H3, Sep 2026) — same prompt format as H3 (**low**, comfyui-wiki news).
- Wan-Dancer-14B (music-to-dance) — niche, text + audio conditioned (**high** that it exists).
- No other 2026 open-weights base video model of comparable significance was confirmed in this pass (older: CogVideoX-1.5, Open-Sora, SkyReels, Kandinsky 5, Ovi were not re-researched).

---

## 6. Official rewriter / enhancer system-prompt files (raw URLs)

Wan 2.2
- https://raw.githubusercontent.com/Wan-Video/Wan2.2/main/wan/utils/system_prompt.py
- (caller) https://raw.githubusercontent.com/Wan-Video/Wan2.2/main/wan/utils/prompt_extend.py
- (negative prompt) https://raw.githubusercontent.com/Wan-Video/Wan2.2/main/wan/configs/shared_config.py

LTX-2 / 2.3 (Gemma 3) and LTX-2.5 (Gemma 4)
- https://raw.githubusercontent.com/Lightricks/LTX-2/main/packages/ltx-core/src/ltx_core/text_encoders/gemma/encoders/prompts/gemma3_t2v_system_prompt.txt
- https://raw.githubusercontent.com/Lightricks/LTX-2/main/packages/ltx-core/src/ltx_core/text_encoders/gemma/encoders/prompts/gemma3_i2v_system_prompt.txt
- https://raw.githubusercontent.com/Lightricks/LTX-2/main/packages/ltx-core/src/ltx_core/text_encoders/gemma/encoders/prompts/gemma4_t2v_system_prompt.txt
- https://raw.githubusercontent.com/Lightricks/LTX-2/main/packages/ltx-core/src/ltx_core/text_encoders/gemma/encoders/prompts/gemma4_i2v_system_prompt.txt
- https://raw.githubusercontent.com/Lightricks/ComfyUI-LTXVideo/master/system_prompts/gemma_t2v_system_prompt.txt
- https://raw.githubusercontent.com/Lightricks/ComfyUI-LTXVideo/master/system_prompts/gemma_i2v_system_prompt.txt
- (negative prompt) https://raw.githubusercontent.com/Lightricks/LTX-2/main/packages/ltx-pipelines/src/ltx_pipelines/utils/constants.py

HunyuanVideo 1.5
- https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanVideo-1.5/main/hyvideo/utils/rewrite/t2v_prompt.py
- https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanVideo-1.5/main/hyvideo/utils/rewrite/i2v_prompt.py
- (handbook) https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanVideo-1.5/main/assets/HunyuanVideo_1_5_Prompt_Handbook_EN.md

MiniMax H3 (official prompt-writing guides; the hosted H3-Context-IR rewriter itself is not public)
- https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/SKILL.md
- https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/references/base-en.txt
- https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/references/ref-en.txt

Alice (copy of Wan 2.2 prompts)
- https://raw.githubusercontent.com/mirage-video/Alice/main/alice/utils/system_prompt.py

Kling, Veo, Seedance, Sora 2, Runway: official rewriter system prompts **not found** (not published).
