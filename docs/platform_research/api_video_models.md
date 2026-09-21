# Closed / API-only video models: prompt-profile research

Research date: 2026-09-21. Method note: most vendor doc sites are JavaScript-rendered and return only navigation chrome to WebFetch. Where marked "(browser-rendered)", the vendor page was opened in a real browser session (Playwright) and the rendered text was read directly, so those facts are primary-source, verbatim-checked. Everything else is WebFetch/WebSearch and is labelled.

Confidence labels: high = vendor source read directly; medium = vendor via summary/partner mirror; low = third-party only.

---

## 1. ByteDance Seedance (BytePlus ModelArk "Dreamina Seedance 2.5" and "2.0 series")

**Developer:** ByteDance Seed; sold via BytePlus ModelArk (international) / Volcengine Ark (China); consumer surfaces Dreamina / Jimeng / CapCut.

**Current version:** YES, there is a newer model. **Dreamina Seedance 2.5**, model ID `dreamina-seedance-2-5-260628` (ID date stamp 2026-06-28; third-party reports say preview 2026-06-23 at Volcano Engine FORCE, launch 2026-07-31; BytePlus site banner on 2026-09-21: "Official Dreamina Seedance 2.5 API is now live"). Still-current 2.0 series: `dreamina-seedance-2-0-260128`, `dreamina-seedance-2-0-fast-260128`, `dreamina-seedance-2-0-mini-260615`. API reference page last updated 2026-09-17.

**Caption style:** Structured "engineering-style instruction", not copywriting prose. Both versions want: (1) asset bindings, (2) one-sentence summary, (3) shot list or timeline, (4) global notes (style, quality, constraints).
- 2.0 basic patterns: `Reference <Subject_N> in <Image_N> to generate...`; `Reference <Action/Camera_movement/Style/Sound_effect> in <Video_N> to generate...`; `Reference the timbre in <Audio_N> to generate...`.
- 2.0 advanced formula (verbatim): "precise subject + action details + scene/environment + lighting & color tone + camera movement + visual style + image quality + constraints".
- 2.5 one-sentence summary (verbatim): "Subject + Location + Event + Genre/Style + Camera movement..." followed by "Detailed Plot Description" (shot sequence OR timeline) and "Additional Notes".
- NOTE: the first-pass formula "subject + motion + environment + camera + aesthetics + audio" is not the wording in the current official guides; use the formulas above.

**Multi-shot syntax:** `Shot 1: ... Shot 2: ... Shot 3: ...` in event order. Per-shot logic recommended by 2.0 guide: camera movement/transition -> subject action and expression -> position/spatial change -> audio. 2.5 examples put a bracketed camera header first: `Shot 1: [Wide shot, locked-off camera, eye-level, rule-of-thirds composition] ...` and may combine shot + time: `Shot 1 (0-3s): ...`.
- **Timestamps: version-dependent.** 2.0 guide: "The model's support for precise timing (such as 0-3 seconds) is unstable, and forcibly limiting duration may lead to abnormal generation results" -> do NOT put per-shot durations in 2.0 prompts. 2.5 guide: "Seedance 2.0 does not respond to timestamps and only responds to shot numbers, while Seedance 2.5 supports integer-second timestamps." Accepted 2.5 forms: `0-3 seconds...3-7 seconds...`, `[1s-4s]....[4s-8s]`, `0s-3s:`, time-point ("At the 2-second mark, ..."), relative ("After 3 seconds, ..."). Use 1-second granularity, keep the timeline gap-free, do not use timestamps for high-frequency actions.

**Length:** Recommended (API reference, verbatim): "no more than 500 Chinese characters or 1,000 English words. Lengthy text will lead to scattered information, and the model may ignore details". No hard character/token limit is published -> hard limit: not found.

**Duration:** API parameter `duration` (integer seconds), not prose. 2.5: 4-30 s or `-1` (model picks); 2.0 series: 4-15 s or `-1`. Older 1.x models also accept `frames` and in-prompt text commands (`--rs 720p --rt 16:9 --dur 5 --seed 11 --cf false --wm true`); do not emit these for 2.x. Editing tasks on 2.5 require `ratio: adaptive`, `duration: -1`. 2.5 extension up to multiple rounds. Writing "Generate a 30-second video in a 16:9 widescreen format" in prose appears in official examples but the parameter governs.

**Resolution / ratio:** 2.5: 480p/720p/1080p (10-bit at 1080p); 2.0: up to 4k listed for Seedance 2.0 standard; ratios 21:9, 16:9, 4:3, 1:1, 3:4, 9:16, adaptive.

**Audio:** Native joint audio+video; parameter `generate_audio` (default true). 2.5 natively supports 11 languages (zh, en, es, id, ms, th, ar, pt, vi, ja, ko); 2.0 supports zh, en + es, id, pt, ja.
- **Official 2.0 "special character standards" (verbatim table):** Music `（）` e.g. `（fast-paced rock music is playing in the background）`; Sound effect `<>` e.g. `< dog barking can be heard in the distance >`; Dialogue `{}` e.g. `{Hello, world}`; Subtitles `【】` e.g. `【Chapter One: Departure】`. For less common languages mark the language: `says in Japanese {こんにちは}`. Dialogue language must be consistent; do not mix Chinese and English.
- 2.5 official examples instead use labelled plain text with double quotes: `Dialogue (elderly woman): "Fly safe, my child. Come back to me."`, `Voiceover reads the full line: "..."`, `Sound effects: roaring heat waves and a slightly exaggerated dry cracking sound.`, and BGM in prose ("Use Chinese-style 8-bit wuxia background music").
- So the first-pass "dialogue in double quotes" is correct for 2.5 examples; the 2.0 guide's canonical form is curly braces. Both are vendor-sourced.
- Negative audio control (2.5): "No BGM; generate only environmental sounds and action sounds.", "No audio.", "Keep the original audio unchanged."

**Reference syntax:** API `content[]` items with `role`: `reference_image`, `reference_video`, `reference_audio`, `first_frame`, `last_frame`. In the prompt refer to assets BY UPLOAD ORDER per modality. Spellings that appear in official docs (all accepted): `@Image1`, `@Image 1`, `@Video1`, `@Audio 1`, `Image 1`, `[Video 1]`, `<video1>`. Binding patterns: `Define the woman wearing a red dress and a straw hat in Image 1 as Subject 1`; `Zhang San@Image 1`; `Asset Bindings: Storyboard @Image1, bedroom @Image2, Li Tian @Image3`; `Images 1-2 are Character 1 and correspond to Audio 1`. Never use the Asset ID (`asset://...`) inside the prompt. Do not rely on names written inside the image.
- Limits: 2.0 series = 15 assets (9 images + 3 videos + 3 audios), audio-only reference not allowed, reference A/V total <= 15 s. 2.5 = 50 assets (30 images + 10 videos + 10 audios), reference video/audio combined <= 30 s each, audio-only allowed. (The first-pass "up to 12 files" figure does not appear in the BytePlus API docs; its origin was not verified - possibly the consumer app. Coincidentally, MiniMax H3 caps mixed inputs at 12.) Official advice: do not use the full limit; 4-5 assets is the recommended configuration for 2.0.
- Edit/extend: refer to the clip directly as `<Video_N>`/`@Video 1`; do NOT write "reference Video 1" (mis-classified as a reference task). Edit trigger words: edit video, add, insert, remove, delete, modify, replace, change to. Extend trigger words: extend forward/backward, continue, continue from, extend the story. 2.5 API hint `omni_reference_task_type`: auto | reference | edit | extend.
- First/last frame via prompt (unlocked aspect): "Image 1 is the first frame.", "Image 3 is the first frame, and Image 5 is the last frame." Keyframes: first sentence "Use Images 1 to 7 in order as keyframes."

**Camera:** No numeric camera parameters for 2.x (`camera_fixed` exists but is only supported by Seedance 1.5 pro / 1.0 pro / 1.0 pro fast). Camera is prose using standard terms: shot size (extreme wide / wide / medium / medium close-up / close-up), movement (push in, pull out, pan, track, follow, orbit, dive, pull back, tilt up, handheld shake), angle (low angle, overhead, first-person), techniques (one-shot/long take, Hitchcock zoom/dolly zoom, aerial, FPV, bullet time, handheld, speed ramp). Niche terms: write `[term + descriptive explanation]`, e.g. "Rack focus: the focus shifts smoothly; ...". 2.0: "Try to specify only 1 type of camera movement in a single shot." Transitions: give trigger time + method ("At the 5-second mark, ... left wipe combined with a natural dissolve").

**Negative prompt:** No `negative_prompt` API field. Use in-prompt "constraint words": "keep it subtitle-free", "avoid generating any text or subtitles", "do not generate a logo", "do not generate a watermark". 2.5: "Use positive descriptions whenever possible. Negative constraints are supported for subtitles and audio control". An official 2.5 example does include a `[Strictly exclude]` block listing unwanted styles.

**I2V rules:** `first_frame`/`last_frame` roles lock aspect ratio (2.5 requires `ratio: adaptive`); first and last frame should share aspect ratio. Example I2V prompt is motion+camera only: "A strawberry sandwich cookie slowly completes one full rotation while the camera moves smoothly around it and keeps the product centered." When a reference is accurate, "simply state that it should be referenced and avoid repeatedly describing the scene in detail."

**Prompt rewriting:** No rewrite/enhance flag documented in the ModelArk video API (not found). BytePlus instead ships an external prompt-optimizer skill (`npx skills add ... --skill sd25-pe`, invoked as `/sd25-pe`).

**Do / Don't**
- DO bind every asset explicitly by order and role; put the most important asset first.
- DO externalise emotion as physical detail (official table: sadness -> "lowering the head, shoulders trembling slightly, eyes reddening...").
- DO quantify motion (slowly / quickly / slightly) and prefer slow, continuous small movements; describe transitions between actions.
- DO end with style + quality + constraint lines ("The character's face remains stable without deformation; movements are natural and smooth, with no stutter or flicker.").
- DON'T stack camera moves in one shot; DON'T put second-level timing in 2.0 prompts; DON'T mix dialogue languages; DON'T use multi-view character sheets with 2.0 (OK in 2.5).
- DON'T over-stuff a time range in 2.5 (causes extra cuts or dropped beats).

**Confidence:** high (browser-rendered vendor pages).

**Sources**
- https://docs.byteplus.com/en/docs/ModelArk/2607689 (browser-rendered) - Seedance 2.5 prompt guide: formula, timestamps, negative control, camera language, reference mapping, locked/unlocked tasks, differences from 2.0, examples.
- https://docs.byteplus.com/en/docs/ModelArk/2607688 (browser-rendered) - Seedance 2.5 tutorial: model IDs, capability table, asset limits, durations, languages, task-type constraints, API examples.
- https://docs.byteplus.com/en/docs/ModelArk/2222480 (browser-rendered) - Seedance 2.0 series prompt guide: basic/advanced formula, Shot N rule, timing warning, special characters for music/SFX/dialogue/subtitles, constraint words, FAQ.
- https://docs.byteplus.com/en/docs/ModelArk/1520757 (browser-rendered) - Create video generation task API: recommended prompt length, parameters, `camera_fixed` model support, text-command example.
- https://vidmuse.ai/blog/seedance-2-5-guide (third-party) - launch dates only.

---

## 2. Kling VIDEO 3.0 / 3.0 Omni / 3.0 Turbo (Kuaishou)

**Developer:** Kuaishou Technology (Kling AI).

**Current version:** Kling VIDEO 3.0 and 3.0 Omni (launched 2026-02, Kuaishou IR release) remain the flagship; the API docs now also list **Kling 3.0 Turbo** tagged NEW (T2V/I2V only, 720p/1080p). Kling O1, 2.6, 2.5 Turbo are still listed. **Kling 4.0: not released** - only third-party speculation (morphic.com page says "Coming soon... yet to be confirmed").

**Caption style:** Prose for single shots; fixed-format shot list for multi-shot.

**Hard limits (new "contents" API, vendor verbatim):** prompt text "should not exceed 3072 characters in length, and it is recommended not to exceed 2500 characters" (3.0 and 3.0 Omni). 3.0 Turbo: "cannot exceed 2500 characters". Legacy v1 API: prompt <= 2500 chars, negative_prompt <= 2500 chars. Per-shot prompt max 512 characters; 1-6 shots.

**Multi-shot syntax (API, verbatim):** `"shot n, m, words; shot n, m, words;"` separated by standard (half-width) semicolons; n = shot number (1-6), m = shot duration in seconds (each >= 1 s; sum must equal total `duration`), words = shot prompt (<= 512 chars). `settings.multi_shot` defaults to true; "When set to false, multi-shot prompts will not produce multi-shot output." The web-app user guide writes the same idea as `Shot 1 (3s): Wide shot, @Boxer A and @Boxer B face off...` or `Shot 1, profile shot of ... Shot 2, frontal macro shot...`. Legacy API used `multi_shot` + `shot_type` (customize | intelligence) + `multi_prompt[]` {index, prompt, duration}.

**Duration:** parameter `settings.duration`, integer 3-15 s (default 5). In multi-shot the per-shot seconds are written in the prompt AND must sum to the parameter.

**Audio:** `settings.audio`: `native` | `off` (Omni adds `original` to keep a reference video's sound); default off. Legacy API: `sound: on|off`. Languages (user guide): Chinese, English, Japanese, Korean, Spanish, plus dialects/accents (Cantonese, Sichuanese, Northeastern, Beijing, Taiwanese; American, British, Indian English); code-switching supported.
- Dialogue (3.0 user guide): `Mom (softly, in a surprised tone): Wow, I didn't expect this plot at all.` / Omni guide: `@Grace says, "Hey! Watch your dog!"`. Tag language/dialect before the line ("in Cantonese: ..."). Explicitly pair each character with their line to avoid speaker confusion.
- Voice binding (legacy API): `voice_list` + `<<<voice_1>>>` in prompt, max 2 voices, "Simpler grammar is better. For example: The man <<<voice_1>>> said, \"Hello.\"". New API binds voices to Elements instead.
- SFX/music: no label syntax documented; describe in prose (not found as formal syntax).

**Reference syntax:** New API: every `contents[]` item has an `id` (e.g. `image_1`, `video_1`, `element_1`) and the prompt cites it as `@xxx`: "Specify an image, an Element, a video in the format of @xxx, such as @image_1, @Zhang, @video_1." Rules: avoid Element names that are substrings of each other (`@Zhang` vs `@ZhangSan`) and names that collide with prompt text (`@gmail`). Legacy API (kling-video-o1 / older SDKs, ComfyUI partner nodes): `<<<image_1>>>`, `<<<element_1>>>`, `<<<video_1>>>`. Content types: `first_frame`, `last_frame`, `refer_image`, `feature_video` (style/motion reference), `base_video` (video to edit), `element`.
- Limits: no ref video -> refer_images + multi-image elements <= 7; with ref video or with video-character elements -> <= 4; max 1 reference video (3-15.5 s, <= 200 MB); I2V endpoints: up to 3 Elements; with first/last frame max 3 elements. feature_video forces `audio: off` and `multi_shot: true`; base_video (edit) forbids multi-shot, native audio and first/last frames.

**Camera:** No camera-control parameter on 3.0-generation endpoints (legacy `camera_control` applies only to Kling v1.x; not present on current pages). Use prose: profile shot, macro shot, low-angle rear wide shot, first-person POV, side-on tracking shot, 360-degree pan, cinematic handheld, bird's-eye, top-down.

**Negative prompt:** New API has NO negative field: "The prompt can include positive and negative descriptions." Legacy API has `negative_prompt` (<= 2500 chars) with the vendor note "It is recommended to supplement negative prompt via negative sentences within positive prompts". So: write exclusions as sentences in the main prompt.

**I2V rules:** first frame required, last frame optional; "last frame only" unsupported; 3.0 Turbo is first-frame only. Example I2V prompt is motion/emotion only: "A girl sat on the train, looking out the window with a melancholic expression, her head swaying with the train."

**Prompt rewriting:** no rewrite/enhance parameter documented (not found).

**Do / Don't**
- DO use the exact `shot n, m, words;` format when you want deterministic cuts, and make seconds sum to duration.
- DO keep each shot <= 512 chars and the whole prompt <= 2500 chars.
- DO name speakers and attach tone + language to each line.
- DON'T use overlapping @names; DON'T expect audio when using feature_video or base_video.
- DON'T rely on a separate negative prompt; fold it into sentences.

**Confidence:** high for API facts (browser-rendered vendor API docs); medium for user-guide phrasing (vendor page via WebFetch summary).

**Sources**
- https://kling.ai/document-api/api/video/3-0-omni/video-omni (browser-rendered) - Omni API: 3072/2500 char limits, shot format, @xxx syntax, content types, reference limits, audio enum, duration enum.
- https://kling.ai/document-api/api/video/3-0-omni/image-to-video (browser-rendered) - Kling 3.0 I2V: same limits, elements <= 3, first/last frame rules.
- https://kling.ai/document-api/api/video/3-0-turbo/image-to-video (browser-rendered) - 3.0 Turbo exists, 2500-char limit, first-frame only.
- https://kling.ai/document-api/api/video/3-0-omni/video-omni/legacy and .../text-to-video/legacy (browser-rendered) - legacy `<<<image_1>>>`, `<<<voice_1>>>`, negative_prompt, multi_prompt.
- https://kling.ai/quickstart/klingai-video-3-omni-model-user-guide (WebFetch summary) - @Element usage, shot examples, input limits.
- https://kling.ai/quickstart/klingai-video-3-model-user-guide (WebFetch summary) - dialogue format, languages/dialects, multi-shot modes.
- https://morphic.com/resources/models/kling-4 (third-party) - Kling 4.0 is speculation only.

---
## 3. Google Veo 3.1 (and the new Gemini Omni Flash video model)

**Developer:** Google DeepMind; served via Gemini API (ai.google.dev) and Vertex AI, which is now branded "Gemini Enterprise Agent Platform" (docs moved to docs.cloud.google.com/gemini-enterprise-agent-platform/...).

**Current version:** Veo 3.1 is still "our latest line of video generation models" on Google Cloud. **No Veo 3.2 or Veo 4 found.** IDs: Vertex GA `veo-3.1-generate-001` (released 2025-11-17, retirement "November 17, 2026 or later"), plus 3.1 Fast and 3.1 Lite; Gemini API `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`, `veo-3.1-lite-generate-preview` (model page "Latest update: January 2026"). NEW sibling: **Gemini Omni Flash** (`gemini-omni-1.1-flash`; Vertex sample also shows `gemini-omni-flash-preview`), a conversational generate/edit/extend video model via the Interactions API - doc last updated 2026-09-17. Worth its own profile (see below).

**Caption style (Veo):** Prose; optional timestamped shot list. Five-part formula (Google Cloud blog, verbatim): `[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]`. Gemini API guide elements: subject, action, style, camera positioning/motion, composition, focus/lens effects, ambiance.

**Hard limit:** text input **1,024 tokens** (Gemini API model page). Recommended length: not stated. English is the only validated prompt language.

**Duration:** parameter `durationSeconds` 4, 6 or 8 (8 required for 1080p/4k, for reference images, and for extension in Gemini API). Not prose. Timestamp prompting inside the 8 s window is supported: `[00:00-00:02] Medium shot from behind ... [00:02-00:04] Reverse shot ... SFX: The rustle of dense leaves...`.

**Audio:** native; Vertex `generateAudio` (default true); Gemini API audio always on.
- Dialogue: Gemini API/blog: quotes - `A woman says, "We have to leave now."` Vertex prompt guide uses colon without quotes - `The seasoned detective says: Your story has holes.` Both are vendor forms (the colon form is commonly used to reduce burned-in subtitles; that rationale is third-party).
- SFX: `SFX: thunder cracks in the distance`. Ambient: `Ambient noise: the quiet hum of a starship bridge`. Music in prose ("A swelling, gentle orchestral score begins to play"). Vertex guide: "use separate sentences in your prompt to describe the audio."
- Also accepted label seen in official example: `Emotion: Wonder and reverence.`

**Reference ("Ingredients to Video"):** up to 3 asset reference images (`referenceImages`, referenceType asset; Veo 3.1 lists "Asset images: Supported"), 8 s only. No tag syntax; cite by description: "Using the provided images for the detective, the woman, and the office setting, create a medium shot of ...". Vertex `task: referenceToVideo` = "one to three reference images, an optional reference audio and a text prompt".

**First/last frame:** image + `lastFrame`; prompt describes the transition and audio: "The camera performs a smooth 180-degree arc shot, starting with the front-facing view of the singer and circling around her to seamlessly end on the POV shot from behind her on stage. The singer sings '...'"

**Extension:** Veo-generated input only; +7 s per call, up to 20 times, max 148 s total; 720p only; input <= 141 s; 2-day storage window. Prompt describes what happens next.

**Camera:** prose vocabulary only (dolly, tracking, crane, aerial, slow pan, POV, arc; wide/close-up/extreme close-up/low angle/two-shot; shallow DOF, wide-angle, macro, deep focus; Vertex guide adds cinematic terms: match cut, jump cut, establishing shot sequence, montage, split diopter).

**Negative prompt:** `negativePrompt` parameter (Vertex, verbatim: "Things that shouldn't appear in the generated videos. For example: \"low quality\", \"ugly\", \"deformed\"."). Write nouns, not instructions: recommended "wall, frame"; not recommended "no walls" / "don't show walls". In the main prompt, describe the wanted state positively ("a desolate landscape with no buildings or roads" rather than "no man-made structures").

**I2V:** image is the first frame; prompt should describe motion/camera/audio. 20 MB max image.

**Prompt rewriting:** Vertex `enhancePrompt` boolean, "Defaults to true"; "If prompt enhancement is enabled, providing a seed won't guarantee consistent results." `enablePromptRewriting` is deprecated/no effect. The former "turn the prompt rewriter off" doc page now redirects to the overview, so whether Veo 3.x honours `enhancePrompt:false` is not confirmed (historically Veo 3 required true). Gemini API: no flag found.

**Do / Don't:** lead with cinematography; put audio in separate labelled sentences; keep dialogue short enough for 8 s; use timestamps for multi-shot; don't use "no/don't" in negativePrompt; don't exceed 1,024 tokens; don't expect non-English prompts to be reliable.

### 3b. Gemini Omni Flash (profile stub - vendor prompt guide read in browser)
- Model `gemini-omni-1.1-flash`; input limit 1,048,576 tokens; output 3-10 s, 24 fps, 360p/720p(default)/1080p/4K (upscaled); 16:9 or 9:16; audio auto-generated; extension +10 s up to 40 s total; multi-turn editing with `previous_interaction_id`.
- Natural-language prompts, no rigid syntax. Defaults to MULTI-SHOT; for one shot write "In a single unbroken scene" / "In a single continuous shot" / "No scene cuts".
- Audio: `Sound design: Gentle breeze, distant bird chirps. No dialogue.`; "Include calm background music"; "The video has a high energy techno beat".
- Negatives are simple in-prompt phrases: "No dialogue", "No embellishments", "No extra sound effects". No negative-prompt parameter, no system instruction, no temperature.
- Timing: natural language ("After 3 seconds, a woman enters the scene.") or timecode `[0-3s] ... [3-6s] ... [6-10s] ...`. In extensions 0 s = start of the extension.
- Media tags: `<FIRST_FRAME>`, `<LAST_FRAME>` (needs FIRST_FRAME), `<IMAGE_REF_N>` and `<VIDEO_REF_N>` (0-indexed); complex form `[# Sources <FIRST_FRAME>@Image1] [# References <IMAGE_REF_0>@Image2]`. Example with 6 image refs is in the docs. Up to 3 video refs of <= 3 s; audio in video refs ignored; audio upload unsupported.
- Editing: keep it short + "Keep everything else the same." (vendor "Avoid/Simplify" examples).
- Meta prompting is encouraged: "Consider micro-detail, expression and timing to create a very rich, detailed but entirely natural scene."

**Confidence:** high (Gemini API pages via WebFetch + Vertex/Omni pages browser-rendered; Google Cloud blog via WebFetch).

**Sources**
- https://ai.google.dev/gemini-api/docs/veo - Veo 3.1 params, durations, reference images, extension limits, audio cues.
- https://ai.google.dev/gemini-api/docs/models/veo-3.1-generate-preview - 1,024-token text input limit, model codes, update date.
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/veo/3-1-generate (browser-rendered) - GA model ID, dates, specs, "latest line".
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/rest/Shared.Types/VideoGenerationModelParams (browser-rendered) - negativePrompt, enhancePrompt default true, generateAudio, task enum.
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/video-gen-prompt-guide (browser-rendered) - audio sentence advice, colon dialogue form, negative prompt do/don't, cinematic terms.
- https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1 - five-part formula, SFX:/Ambient noise:, timestamp example, ingredients and first/last frame phrasing.
- https://ai.google.dev/gemini-api/docs/omni (browser-rendered) and https://ai.google.dev/gemini-api/docs/models/gemini-omni-flash - Gemini Omni Flash guide, tags, limits.

---

## 4. Runway Gen-4.5 / Gen-4 Turbo / Aleph 2.0 / Act-Two

**Developer:** Runway.

**Current version:** `gen4.5` (API Feb 2026; T2V + I2V, 2-10 s, 720p; now with HDR/ProRes output options), `gen4_turbo` (I2V only), **Aleph 2.0** `aleph2` (Jun 2026; "Gen-4 Aleph" and Gen-3 Alpha Turbo were sunset Jul 2026), `act_two`. No Gen-5 found. NOTE: Runway's API is now also a reseller/router for third-party models (IDs seen in the API reference: `seedance2`, `seedance2_5`, `veo3.1`, `gemini_omni_flash_1.1`, `grok_imagine_1_5`, `wan3`, `wan3_prime`, `h3_max`) plus a Model Router endpoint.

**Hard limits (API reference, verbatim):** `promptText` "string [1 .. 1000] characters - A non-empty string up to 1000 characters (measured in UTF-16 code units)". Aleph 2 `promptText` also 1..1000 and optional; `keyframes` 1-5 timed guidance images ({uri, at}). Model Router generic input: promptText up to 20000 chars, `negativePrompt` <= 1000 chars, up to 4 reference images with roles (first/last/reference) - these are mapped to whichever model is selected.

**Caption style:** Prose, positive phrasing. Academy formulas (verbatim): T2V `[Camera] shot of [a subject/object] [action] in [environment]. [Supporting component descriptions]`; I2V `The camera [motion description] as the subject [action]. [Additional descriptions]`. Sequencing: natural language ("X occurs, then Y occurs") or timestamps (`[00:01] X occurs`). Gen-4.5 "excels at understanding and executing complex, sequenced instructions".

**Duration:** parameter (`duration` integer, 2-10 for gen4.5). Ratios by pixel string e.g. `1280:720`, `720:1280`, `960:960`, `1104:832`, `832:1104`, `1584:672` (T2V on gen4.5 is 16:9 only per help center).

**Audio:** No audio parameter on gen4.5/gen4_turbo/aleph2 in the API reference -> native audio for Runway's own video models: not found. Audio is separate endpoints (text-to-speech `eleven_v3` with tags like `[laughs]`, sound effects, `seed_audio`, dubbing). Do not write dialogue/SFX into Gen-4.5 prompts.

**References:** Gen-4.5 video: single `promptImage` (first frame; array form allows position). No @-tag syntax for video (the @tag syntax belongs to Gen-4 Image References, not covered here).

**Camera:** prose only; no numeric camera parameters.

**Negative prompt:** none for Runway's own models. "Describe what you want to see rather than what you don't want."

**I2V rules:** describe motion only; do not re-describe the image. Input images with implied motion cues (motion blur, mid-action poses) can fight the prompt.

**Aleph 2.0 (video edit) prompt style:** `action verb + description`: "add, remove, change, replace, re-light, re-style". Examples: "Change the outfit and bag to soft yellow", "change background to ancient city ruins", "heavy overcast and raining", "Chiaroscuro lighting", "Swap for black leather clutch with gold buckle", "1920s silent era film". "Simplicity, iteration, and precision work best." Unmentioned elements are preserved. Keyframe edits usually need no text; add a short motion prompt only when the motion would not occur naturally.

**Act-Two:** no text prompt at all. Inputs: character image/video + driving performance video; knobs `bodyControl` (bool), `expressionIntensity` 1-5 (default 3). A prompt-enhancer should output nothing for Act-Two.

**Prompt rewriting:** no flag documented (not found).

**Do / Don't:** stay under 1000 UTF-16 units; one subject/action chain; concrete observable language, no abstract concepts; avoid conflicting instructions; no negatives; I2V = motion + camera only; Aleph = one short imperative edit per pass.

**Confidence:** high for limits/IDs (browser-rendered API reference); medium for guidance (vendor pages via WebFetch summary).

**Sources**
- https://docs.dev.runwayml.com/api/ (browser-rendered) - promptText 1..1000, aleph2 keyframes, act_two params, router limits, third-party model IDs.
- https://docs.dev.runwayml.com/api-details/api_changelog/ - 2026 model timeline, Aleph sunset.
- https://docs.dev.runwayml.com/guides/models - model IDs and I/O.
- https://help.runwayml.com/hc/en-us/articles/46974685288467-Creating-with-Gen-4-5 - durations, ratios, motion-focused I2V.
- https://academy.runwayml.com/guides/prompting-guide - formulas, positive phrasing, sequencing, I2V cautions.
- https://help.runwayml.com/hc/en-us/articles/52150503729171-Aleph-2-0-Prompting-Guide - Aleph 2.0 verb+description style and examples.

---

## 5. Alibaba Wan (hosted, Model Studio / DashScope)

**Developer:** Alibaba Tongyi Lab; hosted on Alibaba Cloud Model Studio (closed; Wan 3.0 weights not announced as open).

**Current flagship:** **Wan 3.0** - `wan3.0-video` (standard) and `wan3.0-video-prime` (high-speed). Blog dated 2026-08-13. "All-in-One": one endpoint routes T2V / I2V (first, first+last) / multimodal reference / video edit / video extension by inputs + prompt intent. Wan 2.7 and earlier remain available with separate T2V/I2V endpoints.

**Hard limits:** prompt max **20,000 characters** (Chinese character or letter = 1). Duration 2-30 s (default 5; `-1` = smart duration); with video input, input+output <= 30 s. 480P/720P/1080P (default 1080P), 30 fps; ratios adaptive (default), 21:9, 16:9, 4:3, 1:1, 3:4, 9:16. References: <= 10 images, <= 5 videos (<= 15 s total), <= 5 audio (<= 15 s total), first/last frame 1 each, also documents (docx/xlsx/pptx/pdf/txt/md); up to 20 materials per request.

**Caption style / formulas (vendor prompt guide, updated 2026-09-04, verbatim):**
- Basic: `Prompt = Entity + Scene + Motion`
- Advanced: `Entity (description) + Scene (description) + Motion (description) + Aesthetic control + Stylization`
- I2V: `Prompt = Motion + Camera movement`
- Sound (Wan 3.0/2.7/2.6/2.5): `Entity + Scene + Motion + Sound description (voice/sound effect/background music)`; Voice = `Character's lines + Emotion + Tone + Speed + Timbre + Accent`; SFX = `Source material + Action + Ambient sound`; BGM = `Background music/score + Style`.
- Multi-shot (3.0/2.7/2.6): `Overall description + Shot number + Timestamp + Shot content`, e.g. `Shot 1 [0-3 s] ...`. The Wan 3.0 guide also shows `(0:00 - 0:03) Scene description`.
- Reference-to-video (3.0/2.7): `Reference identifier + Action + Scene + Lines (optional) + Background music (optional)`.

**Audio:** `audio` boolean, default true. Dialogue inline: `the character says: '...'` with voice descriptors ("She whispers in a relaxed tone at moderate speed with a clear voice in American English."). Multi-speaker: unique labels + visual anchors + distinct voice attributes + temporal links ("Immediately", "Then").

**Reference syntax:** "Image 1" / "Img 1" / "Video 1" / "Audio 1" by array order, counted separately per type. Edit trigger words: "edit video", "remove", "replace", "change to". Extend: "extend", "continue", "extend forward/backward".

**Camera:** prose vocabulary (camera pushes in / pulls out / moves left / tracks, orbiting, drone shot, compound movement; close-up, wide-angle; over-the-shoulder, high-angle, aerial; long-focus, fisheye; center/left-heavy composition). No camera parameters.

**Negative prompt:** no `negative_prompt` in the Wan 3.0 API (it exists on legacy Wan 2.x endpoints).

**Prompt rewriting:** `prompt_extend` boolean, **default true** ("intelligent prompt rewriting"). Set `prompt_extend: false` when supplying an already-enhanced prompt.

**Do / Don't (vendor):** keep actions simple/short; bind each line of dialogue to a labelled, visually anchored character; don't name real people; don't expect legible text, rapid scene changes in one clip, or long choreographies.

**Confidence:** medium-high (vendor pages via WebFetch summary; not browser-verified).

**Sources**
- https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-api-reference - model IDs, 20,000-char limit, duration, references, prompt_extend, audio.
- https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-guide - all-in-one routing, reference labels, timestamps, trigger words.
- https://www.alibabacloud.com/help/en/model-studio/text-to-video-prompt - formulas, sound structures, camera vocabulary, what fails.
- https://www.alibabacloud.com/blog/wan3-0-30-second-ai-video-generation-from-any-input_603452 - date, pricing, positioning.

---

## 6. OpenAI Sora 2 - CONFIRMED end of life

OpenAI API docs (verbatim): "The Sora 2 video generation models and Videos API are deprecated and will shut down on September 24, 2026." Affects `sora-2`, `sora-2-pro` and dated snapshots. Help Center: "The Sora web and app experiences were discontinued on April 26, 2026." / "The Sora API will be discontinued on September 24, 2026." No successor named. Recommendation: do not ship a Sora profile (3 days of life left at research date). For the record: prose prompts "shot type, subject, action, setting, and lighting"; `seconds` and `size` are parameters; `input_reference` = first frame and must match output resolution.

**Confidence:** high. **Sources:** https://developers.openai.com/api/docs/guides/video-generation ; https://help.openai.com/en/articles/20001152-what-to-know-about-the-sora-discontinuation

---

## 7. Luma Ray 3.2

**Developer:** Luma AI. **Current:** Ray3.2, released 2026-06-09; Luma's own "llm-info" page says it supersedes Ray3, Ray3.14, Ray2 (deprecated). API model ID `ray-3.2` (Luma Agents API). The older docs.lumalabs.ai Dream Machine API page still only lists ray-2 / ray-flash-2 with `concepts` and camera-motion list - treat as legacy.

- **Prompt:** prose, **1-6,000 characters**, "describing subject, motion, camera movement, lighting, and pacing".
- **Duration:** parameter `5s` (default) or `10s`. Resolution 360p/540p/720p(default)/1080p; ratios 9:16, 3:4, 1:1, 4:3, 16:9, 21:9. `loop`, `hdr` (HDR MP4; 720p/1080p only), `exr_export`.
- **Keyframes:** `video.start_frame`, `video.end_frame`, or `video.keyframes` (1-64 guide images) + `video.keyframe_indexes` (5 s: 0-120, 10 s: 0-240). Incompatibilities: 10s excludes HDR/start/end frame; loop excludes 10s/HDR/end_frame/keyframes; keyframes exclude start/end/loop. (News post says "up to 16 keyframes"; API doc says 64.)
- **Modify (V2V, `type: "video_edit"`):** source <= 20 s, output duration = source. Prompt describes the **target end state, not a sequence of changes** (motion comes from the source). Controls: Motion and Structure adherence 1-9; character locks Faces / Bodies / Poses / Blocking. Reframe: `type: "video_reframe"`.
- **Audio:** not mentioned in any Ray3.2 source -> treat as silent (not found).
- **Camera:** prose ("Camera is controlled by language"); legacy API has `/camera_motion/list` concepts. Negative prompt: not found. Prompt enhancement flag: not found.
- **Do/Don't:** for Modify write the final look (materials, environment, style), never "first... then..."; use keyframes for art-directed moments; do not write dialogue/SFX.

**Confidence:** medium (vendor pages via WebFetch summary). **Sources:** https://docs.agents.lumalabs.ai/guides/videos/generation (params, 6,000 chars); https://lumalabs.ai/learning-center/articles/ray-3-2-introduction-and-core-concepts (Modify inputs and controls); https://lumalabs.ai/news/introducing-ray-3-2 (date, features); https://lumalabs.ai/llm-info (current/deprecated models); https://docs.lumalabs.ai/docs/video-generation (legacy API).

---

## 8. MiniMax H3 / H3 Max hosted API (Hailuo 3.0)

**Developer:** MiniMax (H3 Max: "jointly released by MiniMax and fal.ai", speed-optimised post-train). Model IDs `MiniMax-H3`, `MiniMax-H3-Max`; endpoint `POST /v2/video_generation`. The old v1 endpoint (Hailuo 2.3 / 02 / I2V-01-Director) is what carried the 2,000-char limit, the 15 bracket commands and `prompt_optimizer`.

- **Hard limit:** prompt **<= 7,000 characters** per text item (exactly one non-empty text item required).
- **Duration:** parameter, integer; H3 4-15 s (768P / 2K), H3 Max 5-15 s (480P / 768P). `ratio` default adaptive, but T2V requires an explicit ratio. Official examples nevertheless open with "15s, 16:9." in prose.
- **Brackets vs prose on the hosted endpoint:** official H3 examples are all PROSE (cinematography described in sentences: "Subtle handheld shake, hesitant close-focus, backlit exposure fluctuation"). The guide only says you may "add camera motion instructions (e.g., [pan], [zoom], [static]) directly after key descriptions" - the full 15-command Director list ([Truck left], [Push in], [Pedestal up], [Tracking shot], [Static shot]...) is documented only for Hailuo 2.3/02/I2V-01-Director. Recommendation: prose first, at most one simple bracket tag per beat.
- **References:** `content[]` roles `first_frame`, `last_frame`, `reference_image`, `reference_video`, `reference_audio`; <= 9 images, <= 3 videos (2-15 s each, <= 15 s total), <= 3 audio (same), max 12 files. Cite in prose by order: "Image 1: mood, setting, film grain. Image 2: character. Image 3: bag. Image 4: ending logo." / "following the motion in reference video 1; the character's appearance follows reference images 1 and 2."
- **Audio:** native; no on/off flag in the v2 API (not found). Official example: "Sound: kitchen ambience plus the creature's soft electronic hums." Dialogue syntax: not documented on the hosted docs (not found) - reuse the open-weights profile.
- **Negative prompt / seed / watermark:** none in v2 API.
- **Prompt rewriting:** `extra.prompt_expansion_mode` = `disabled` | `balanced` (default) | `quality`, **H3-Max only**. For H3 no flag is documented. (Legacy v1: `prompt_optimizer` default true, `fast_pretreatment`.)

**Confidence:** high (guide browser-rendered) / medium (API reference via WebFetch). **Sources:** https://platform.minimax.io/docs/guides/video-generation (browser-rendered; models, limits, reference phrasing); https://platform.minimax.io/docs/guides/video-prompt (browser-rendered; official example prompts); https://platform.minimax.io/docs/api-reference/video-generation-v2-create (parameters, prompt_expansion_mode); https://platform.minimax.io/docs/api-reference/video-generation-i2v (legacy bracket commands, 2000 chars, prompt_optimizer).

---

## 9. xAI Grok Imagine Video 1.5

**Developer:** xAI (docs now branded "SpaceXAI"). Models `grok-imagine-video-1.5` (latest; native 1080p for T2V/I2V; first+last frame) and `grok-imagine-video`.
- Duration parameter 1-15 s; ratios 1:1, 16:9 (default), 9:16, 4:3, 3:4, 3:2, 2:3; 480p (default) / 720p / 1080p. Reference-to-video capped at 720p; video editing input <= 8.7 s and keeps source duration; extension continues from last frame.
- **Audio:** on by default; `generate_audio=False` to mute. Up to 3 preset voices via `reference_audios`.
- **Reference syntax:** angle-bracket tags - images `<IMAGE_1>`, `<IMAGE_2>`... (1-indexed, max 7), voices `<AUDIO_0>`, `<AUDIO_1>`, `<AUDIO_2>` (0-indexed). Example: "The person from <IMAGE_1> presents the product from <IMAGE_2>... speaking with the voice from <AUDIO_0>."
- Prompt length limit, negative prompt, rewrite flag, dialogue format: not found. Caption style: prose.

**Confidence:** medium (vendor docs via WebFetch summary). **Sources:** https://docs.x.ai/developers/model-capabilities/video/generation ; https://docs.x.ai/developers/model-capabilities/video/reference-to-video

---

## 10. Vidu Q3 (Shengshu)

Models (API): `viduq3-mix`, `viduq3-turbo`, `viduq3`, `viduq2-pro`, `viduq2`, `viduq1`, `vidu2.0`.
- **Prompt max 5,000 characters.**
- **Reference-to-video syntax:** subjects array {name, images (<= 3 each), voice_id optional}; cite in the prompt as `@1`, `@2` ... Example (vendor): `"@1 and @2 are cooking together, and both say they love hot pot."` Plain reference endpoint: 1-7 images (1-4 if videos are supplied; videos only on viduq2-pro: 1 x 8 s or 2 x 5 s).
- Parameters: duration (model-dependent, 1-16 s), resolution 540p/720p/1080p, `audio` (bool), `bgm`, `movement_amplitude` auto/small/medium/large, `off_peak`.
- Dialogue format, negative prompt, rewrite flag: not found.

**Confidence:** medium. **Source:** https://platform.vidu.com/docs/reference-to-video

---

## 11. PixVerse V6 / C1

Official Platform API (browser-rendered): models `v3.5/v4/v4.5/v5/v5.5/v5.6/v6/c1`.
- **Prompt <= 5,000 characters**; vendor how-to recommends "25-200 words".
- Duration parameter: v5 5/8; v5.5/v5.6 5/8/10 (no 10 at 1080p); **v6/c1 1-15 s**. Quality 360p-1080p. v6/c1 ratios add 2:3, 3:2, 21:9.
- Audio: `generate_audio_switch` (v5.5+; **default false**) - native audio incl. speech; `generate_multi_clip_switch` (v5.5/v6; default false) for multi-shot. v5 and below use `sound_effect_switch` + `sound_effect_content` and `lip_sync_tts_content` (~140 chars).
- `camera_movement` (e.g. `zoom_in`) and `motion_mode` exist as optional fields (full enum not captured); `negative_prompt` appears in responses (limit not captured); `seed` 0-2147483647.
- Dialogue syntax and rewrite flag: not found.

**Confidence:** high for listed limits. **Sources:** https://docs.platform.pixverse.ai/text-to-video-generation-13016634e0 (browser-rendered); https://docs.platform.pixverse.ai/how-to-use-text-to-video-882970m0

---

## 12. Midjourney Video

Image-to-video only (start image -> 5 s clip; extend ~4 s up to 4 times = 21 s max). Auto (no prompt) or Manual (motion prompt). Parameters: `--motion low` (default) / `--motion high`, `--raw` (less creative interpretation, more literal prompt), `--loop` (end = start frame), `--end <image URL>`, `--bs 1|2|4`, `--video` (Discord). SD 480p all plans; HD 720p Standard+ in Fast mode. Other image parameters are stripped. Audio: none documented. Version number, prompt length limit: not found. No public API. Profile advice: short motion-only prompt + flags.

**Confidence:** medium. **Source:** https://docs.midjourney.com/hc/en-us/articles/37460773864589-Video

---

## 13. Adobe Firefly Video

Help page (last updated 2026-06-16): "Firefly Video is the default"; model version not stated. Text prompt + UI controls rather than prompt syntax: Shot size (Extreme close up, Close up, Medium, Long, Extreme long), Camera angle (Aerial, Eye level, High angle, Low angle, Top down), Motion (Zoom in/out, Move left/right, Tilt up/down, Static, Handheld). "Enhance prompt" toggle next to Generate (opt-in in UI). Sound effects are a separate post-generation step ("Add sound effects using text prompts or your own voice recording"). Firefly also hosts partner models (Veo, Runway, Luma, etc.). Prompt limit, durations, API parameters: not found in the page read.

**Confidence:** medium-low. **Source:** https://helpx.adobe.com/firefly/web/work-with-audio-and-video/work-with-video/generate-videos-using-text-prompts.html

---

## 14. Pika 2.2 (partner mirror only)

Vendor developer docs could not be sourced (Pika distributes its API through fal.ai). fal schema for Pikascenes v2.2: `prompt`, `negative_prompt` (default "ugly, bad, terrible"), `image_urls` (ingredients), `ingredients_mode` precise|creative, duration 5|10, 720p|1080p, ratios 16:9, 9:16, 1:1, 4:5, 5:4, 3:2, 2:3. Pikaframes: 2-5 keyframes, total transitions <= 25 s. No audio, no prompt limit stated. A newer Pika model version: not verified.

**Confidence:** medium (official partner mirror). **Source:** https://fal.ai/models/fal-ai/pika/v2.2/pikascenes/api (third-party partner)

---

## 15. Moonvalley Marey (Realism v1.5)

- Vendor help center: "Aim for a minimum of 50 words of detail"; structure `[Camera Movement] + [Scale/Perspective] + [Core Visual] + [Environmental Details] + [Lighting/Technical Specs]`. Negatives go in the separate negative-prompt field ("Add or remove words as needed").
- fal partner schema: `negative_prompt` default "<synthetic> <scene cut> low-poly, flat shader, bad rigging, stiff animation, uncanny eyes, low-quality textures, looping glitch, cheap effect, overbloom, bloom spam, default lighting, game asset, stiff face, ugly specular, AI artifacts"; duration 5s|10s; dimensions 1920x1080, 1152x1152, 1536x1152, 1152x1536; guidance_scale 0-20. Separate motion-transfer and pose-transfer endpoints. Audio: none.

**Confidence:** medium. **Sources:** https://help.moonvalley.com/en/articles/11898182-quick-start-guide-and-walkthrough (vendor); https://fal.ai/models/moonvalley/marey/t2v/api (partner mirror)

---

## 16. LTX hosted API (LTX-2.5 / LTX-2.3)

Vendor prompting guide (docs.ltx.io): single-shot = "a single flowing paragraph", present tense, "roughly 4-8 descriptive sentences"; multi-shot (LTX-2.5) = "one chronological paragraph" with named transitions (hard cut, dissolve, match cut) - explicitly NOT shot lists/numbered beats; screenplay style (scene headers + character cues) for dialogue-heavy scenes. Dialogue in quotation marks, specify language/accent; describe ambient sound, music and speech separately. LTX-2.5 has an optional duration predictor. Hard limits and negative prompt: not found. Same guidance as the open-weights profile; no hosted-only differences found.

**Confidence:** medium. **Source:** https://docs.ltx.io/api-documentation/implementation-guides/prompting-guide

---

## 17. Higgsfield - skipped

docs.higgsfield.ai (and its llms.txt) expose only generic API structure and Soul image endpoints in what could be read; model-specific docs live behind console.higgsfield.ai. No vendor-sourced prompt rules for Higgsfield's own video model (DoP) were found. Higgsfield is primarily an aggregator (Seedance, Kling, Veo...), so use the underlying model's profile. **Not found / skipped.**

---

## Cross-cutting corrections to the first pass

1. Seedance: 2.5 exists (30 s, 50 refs, integer-second timestamps). 2.0 must NOT get timestamps; 2.0 canonical audio markup is `{dialogue}`, `<sfx>`, `（music）`, `【subtitle】`; API limit is 9+3+3 refs (not 12); recommended <= 1,000 English words; no negative-prompt field; no rewrite flag.
2. Kling: new API dropped `negative_prompt` and `<<<image_1>>>` in favour of in-prompt negatives and `@id`; hard 3072 / recommended 2500 chars; shot format `shot n, m, words;` with 512 chars/shot, 6 shots; 3.0 Turbo is new; 4.0 unreleased.
3. Veo: 1,024-token cap; no 3.2/4; `enhancePrompt` default true; Gemini Omni Flash is a new Google video model with its own tag syntax.
4. Runway: 1000 UTF-16 chars; Aleph is now Aleph 2.0 (`aleph2`); no native audio; Act-Two takes no prompt.
5. Wan: flagship is Wan 3.0 (20,000 chars, 2-30 s, `prompt_extend` default true, no negative prompt).
6. Sora 2 API shutdown 2026-09-24 confirmed.
7. Rewrite flags to disable when feeding LLM-enhanced prompts: Wan `prompt_extend:false`; Veo (Vertex) `enhancePrompt:false` (support on 3.x unconfirmed); MiniMax H3-Max `extra.prompt_expansion_mode:"disabled"`; legacy Hailuo `prompt_optimizer:false`. None found for Seedance, Kling, Runway, Luma, Grok, Vidu, PixVerse.
