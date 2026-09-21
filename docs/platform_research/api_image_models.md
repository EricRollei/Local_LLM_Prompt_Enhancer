# Closed / API-only image models: prompting research

Research date: 2026-09-20/21. Method: WebSearch + WebFetch only. WebFetch returns a small-model summary of the page, so "verbatim" quotes below are as relayed by that summariser; treat them as close paraphrase unless marked otherwise. Confidence labels: **high** = vendor page read directly; **medium** = vendor page via summary/partner mirror or vendor page only partly readable; **low** = third-party only.

Access problems worth knowing:
- `docs.byteplus.com` and `docs.volcengine.com` (Seedream) are JavaScript-rendered; the fetch returned only navigation chrome. Seedream facts therefore come from the ByteDance Seed blog (vendor) plus API-reseller mirrors of the official docs.
- `kling.ai/document-api` (Kling API reference) is JS-rendered; only Kling's user guides were readable.
- `docs.cloud.google.com/...gemini-image-generation-best-practices` returned navigation only.
- Adobe Firefly API reference root returned 404; only the how-to guides were readable.
- Reve has no publicly readable vendor API docs that I could find.

---

## 0. Version snapshot (Sept 2026)

| Vendor | Current model(s) | Date | Note |
|---|---|---|---|
| ByteDance | **Seedream 5.0 Pro** (flagship), Seedream 5.0 Lite; 4.5 / 4.0 still served | 5.0 Pro: 2026-07-08 | There is no "Seedream 2.5". Lineage: 3.0 -> 4.0 -> 4.5 -> 5.0 Lite -> 5.0 Pro. |
| Google | **Nano Banana 2** (`gemini-3.1-flash-image`), **Nano Banana Pro** (`gemini-3-pro-image`), **Nano Banana 2 Lite** (`gemini-3.1-flash-lite-image`, GA 2026-06-30); legacy Nano Banana (`gemini-2.5-flash-image`) | NB2: Feb 2026 | **Imagen is shut down** in the Gemini API ("Imagen models are shut down. Use Nano Banana for image generation."). |
| OpenAI | **gpt-image-2.5-sunburst** / **gpt-image-2.5-flare** (2026-09-08); gpt-image-2 (2026-04-21), 1.5, 1, 1-mini still listed | 2026-09-08 | |
| Midjourney | **V8.2** default (2026-07-24); V8.1 (2026-04-14); V7 (2025-04-03); Niji 7 (2026-01-09) | | No public API. |
| Black Forest Labs | FLUX.2 [pro] / [max] / [flex] / [klein] hosted; [dev] open | no newer family in docs | |
| Ideogram | **Ideogram 4.0** (2026-06-03, also open weights); 3.0 (`V_3_1`/`V_3_0`) still served | | |
| Recraft | **V4.1** (latest), V4, V4 Styles, V3, V2 | | |
| Luma | **Uni-1 / Uni-1-max** (Luma Agents API); Photon-1 / Photon-flash-1 (legacy Dream Machine API) | | |
| xAI | `grok-imagine-image-2.0` | | "Aurora" name no longer used in docs. |
| Adobe | Firefly **Image 5** (API: "Image5"), Image 4 / 4 Ultra | | |
| Leonardo | Phoenix 1.0 / 0.9 | | |
| Kling (Kuaishou) | **Kling IMAGE 3.0** (2026-02-04), **IMAGE 3.0 Omni** (2026-02-06), IMAGE O1; older API names `kling-v1..v2-1` (Kolors lineage) | | |
| Runway | `gen4_image`, `gen4_image_turbo` | | |

---

## 1. ByteDance Seedream

- **Developer:** ByteDance Seed; served on Volcengine Ark (doubao-seedream-*) and BytePlus ModelArk.
- **Current version:** Seedream 5.0 Pro, released 2026-07-08 (Seed blog). Seedream 5.0 Lite (`doubao-seedream-5.0-lite`) preceded it. The official prompt guide page is now titled "Seedream 4.0-5.0 prompt guide" on Volcengine (slug `seedream-4-0-5-0-prompt-guide`) and "Seedream 4.0-4.5 prompt guide" on BytePlus (last updated 2026-07-06); there is a separate "Seedream 5.0 pro tutorial" and "Seedream 5.0 pro interactive editing guide". Facts below apply to 4.0-5.0 unless stated.
- **Caption style:** natural-language prose. Rule as mirrored: "Combine subject + action + environment for the content, and use short words for style, color, lighting, composition." Complete sentences beat stacked adjectives ("concise, precise wording works better"). Runware's 5.0 Pro guide recommends a layered order: format -> subject -> composition -> lighting -> in-image text -> style -> constraints, and "Name the format first".
- **Length:** recommended under ~300 Chinese characters or ~600 English words. HARD limit (5.0 Pro / Lite, via reseller mirror of API ref): up to 4000 tokens (about 2,600 Chinese characters). Runware exposes it as 3,000 characters max. Treat ~600 English words as the practical ceiling; the official guide warns that overly long prompts scatter attention (as mirrored; not read directly).
- **Languages:** Chinese and English are primary prompt languages. 5.0 Pro: "native multilingual input and generation" for 10+ languages; text rendering in Chinese, English, French, German, Russian, Japanese, Korean, Spanish, Arabic (RTL handled). Reseller list adds Filipino, Thai, Turkish, Malay, Portuguese, Indonesian, Vietnamese.
- **Negative prompt:** no negative-prompt field in the 4.x/5.x API (not present in any mirror of the parameter list). Put constraints in-prompt as positive statements or explicit "keep X unchanged".
- **Quality tokens:** vendor guidance not found. Third-party (fal) suggests "high resolution, 4K detail" style tokens; the official-guide mirrors instead push concrete description over adjective stacking. Recommendation: omit.
- **Rendered text:** put the exact text in double quotation marks, e.g. `Generate a poster with the title "Seedream 4.0"`.
- **Editing phrasing:** "Action + Object + Attribute". Verbs: Add / Remove (Delete) / Replace / Modify. Examples as mirrored: "Add matching silver earrings and a necklace"; "Remove the girl's hat"; "Replace the largest bread man with a croissant man"; "Turn the three robots into transparent crystal"; "Change the knight's helmet to gold". State what must stay unchanged. Visual markers (arrows, boxes, doodles drawn on the input) can designate the region. 5.0 Pro adds interactive editing: point / lasso / box selection, doodles, colour edits by **hex code** (e.g. #3E4A2E), material replacement, layer separation (10+ layers).
- **Multi-image reference:** refer to inputs by index and give each a role: "Replace subject in Image 1 with subject from Image 2"; "Apply the color scheme of Image 2 to Image 1"; "Place the character from Image 1 into the background of Image 2, using the style of Image 3". For reference-based generation, state the reference target and the generated scene separately. Reference image count: 10 (4.5, 5.0 Pro), 14 (5.0 Lite). (Runware advises addressing references by content rather than index for 5.0 Pro; this conflicts with the official "Image N" convention, so prefer "Image N" plus a content description.)
- **Group / sequential generation:** API `sequential_image_generation: "auto"` with `max_images` (4.x; up to 15 total input+output). Trigger in-prompt with "a series of", "a set of images", "generate N images", and describe what varies between frames and what stays consistent. Support on 5.0 Pro not confirmed (reseller docs for Pro do not list it; Lite accepts n = 1-15).
- **Prompt rewriting:** `optimize_prompt_options.mode` = `standard` (default) or `fast` (4.0/5.0 Pro per reseller mirrors). No documented "off" switch found. **not found:** an official disable flag.
- **Do:** write sentences (subject + action + environment); state use case/format first (poster, logo, storyboard); quote text exactly; name image roles by index; say what to keep unchanged in edits; use "a series of N images" for sets.
- **Don't:** keyword-stack adjectives; use a negative prompt field; exceed ~600 words; leave the edit target ambiguous ("it", "that").

Sources (confidence overall: **medium**)
- https://seed.bytedance.com/en/blog/beyond-generation-it-understands-design-introducing-seedream-5-0-pro - vendor; release date, languages, interactive editing, hex colours (high).
- https://docs.byteplus.com/en/docs/ModelArk/1829186 - vendor prompt guide; exists, updated 2026-07-06, body NOT readable (JS).
- https://docs.volcengine.com/docs/ark/seedream-4-0-5-0-prompt-guide?lang=zh - vendor; confirms guide now covers 4.0-5.0; body not readable.
- https://docs.byteplus.com/en/docs/ModelArk/2582774 - vendor 5.0 Pro tutorial; body not readable.
- https://ai.byteplus.com/lumina/en/resource/seedream-5-0-pro-release-date - vendor; release date 2026-07-08.
- https://evolink.ai/docs/en/api-manual/image-series/seedream/seedream-5.0-pro-image-generate - third-party mirror of API ref: 4000-token limit, 600-word advice, 10 refs, languages, optimize modes (medium/low).
- https://evolink.ai/seedream-5-0 - third-party; 5.0 Lite limits, 14 refs, n 1-15.
- https://www.promptus.ai/blog/seedream-4-0 and https://www.seedream4.net/prompt-guide - third-party restatements of the official guide: quotes for text, edit verbs, Image N phrasing, "a series of" (low/medium; they agree with each other).
- https://runware.ai/docs/models/bytedance-seedream-5-0-pro/guides/prompting - third-party; 3,000-char limit on Runware, seven-layer order (low).
- https://fal.ai/learn/devs/seedream-v4-5-prompt-guide - third-party; 30-100 word advice, front-loading (low).

---

## 2. Google Gemini image models (Nano Banana family); Imagen

- **Developer:** Google / Google DeepMind.
- **Current versions:** Nano Banana 2 = `gemini-3.1-flash-image` ("most versatile ... generalist workhorse"); Nano Banana Pro = `gemini-3-pro-image` ("premium choice for the most complex visual tasks"); Nano Banana 2 Lite = `gemini-3.1-flash-lite-image` (GA 2026-06-30, 1K only); legacy Nano Banana = `gemini-2.5-flash-image`. **Imagen:** the Gemini API Imagen page now reads "Imagen models are shut down. Use Nano Banana for image generation." So no Imagen 4+ profile is needed for the Gemini API. (Old Imagen rules - 480-token prompt cap, `enhancePrompt` - could not be re-verified; page content is gone.)
- **Caption style:** narrative prose. Core rule (Google Developers Blog): **"Describe the scene, don't just list keywords."** Cloud "ultimate guide" formula: `[Subject] + [Action] + [Location/context] + [Composition] + [Style]`; with references: `[Reference images] + [Relationship instruction] + [New scenario]`. "Start with a strong verb" that names the operation. Blog.google elements: subject, composition, action, location, style, editing instructions; add aspect ratio, camera & lighting, exact text.
- **Photographic terms:** encouraged ("Control the camera": "low angle", "aerial view", "wide-angle shot", "macro", "85mm portrait lens", "shallow depth of field (f/1.8)", "three-point softbox setup", "golden hour backlighting", film stock, colour grading). Be specific about materials ("navy blue tweed" rather than "suit jacket").
- **Length:** no recommended word count given. HARD limits are context-window sized: NB2 131,072 input tokens; NB Pro 65,536 input tokens; 32,768 output tokens. Effectively unlimited for prompts.
- **Negative prompt:** no field. Use **semantic negative prompts / positive framing**: describe the desired absence positively ("empty street" instead of "no cars").
- **Quality tokens:** not recommended or discussed; guidance is specificity and photographic language. Omit "masterpiece, 8k".
- **Rendered text:** enclose in quotes ("Happy Birthday"); name or describe the font ("bold, white, sans-serif font", "Century Gothic"); say where it goes. Can prompt in one language and request output text in another. "Text-first hack": have the model draft the copy first, then ask for the image. Docs template: `Create a [image type] for [brand/concept] with the text "[text to render]" in a [font style].` Use Pro for professional text-heavy assets.
- **Editing phrasing:** conversational, multi-turn. Inpainting/semantic mask: "change only the [specific element] to [new description]. Keep everything else ... exactly the same." Remove: "Remove the man from the photo". Style transfer: supply photo, ask to recreate in a named style. Composite: supply several images and say which element comes from which. Restart the chat if character consistency drifts.
- **Reference images:** up to 14 total. Split per model as relayed: NB2 = 10 objects + 4 characters; Pro = 6 objects + 5 characters + 3 styles; Lite up to 14. Define each image's role in the prompt.
- **Aspect ratio / size:** set by API parameter (`aspect_ratio`), not prompt: 1:1, 3:2, 2:3, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9 (+ 1:4, 4:1, 1:8, 8:1 on NB2). Sizes 0.5K/1K/2K/4K (Pro: 1K-4K; Lite: 1K). When editing, the model tends to keep the input's ratio; with several inputs it adopts the last image's ratio.
- **Prompt rewriting:** no separate rewriter; NB2/Pro use built-in "thinking" before rendering (thinking tokens billed). No disable flag for a rewriter found. Optional Google Search grounding (NB2/Pro).
- **Other:** all outputs carry SynthID; C2PA on Vertex.
- **Do:** write a paragraph describing the scene; state intent/use; use camera and lighting vocabulary; quote text and describe the font; say what stays unchanged in edits; iterate in turns.
- **Don't:** keyword lists; "no X" phrasing; put aspect ratio only in the prose when an API parameter exists; rely on tiny text or unverified facts in infographics.

Sources (confidence: **high**)
- https://ai.google.dev/gemini-api/docs/image-generation - vendor; model IDs, resolutions, ratios, reference counts, templates, thinking, grounding.
- https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana - vendor (2026-03-06); formulas, best practices, text rules, token limits, 14 refs.
- https://developers.googleblog.com/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/ - vendor; "Describe the scene, don't just list keywords", editing templates, semantic negatives, aspect-ratio behaviour (written for 2.5 but still linked).
- https://blog.google/products-and-platforms/products/gemini/prompting-tips-nano-banana-pro/ - vendor; six prompt elements, limitations.
- https://cloud.google.com/blog/products/ai-machine-learning/nano-banana-2-lite-and-gemini-omni-flash-available - vendor; Lite GA date.
- https://ai.google.dev/gemini-api/docs/imagen - vendor; Imagen shutdown notice.

---

## 3. OpenAI GPT Image

- **Developer:** OpenAI.
- **Current version:** `gpt-image-2.5-sunburst` (quality / edit precision) and `gpt-image-2.5-flare` (fast), snapshot 2026-09-08 ("ChatGPT Images 2.5"). Also listed: `gpt-image-2` (2026-04-21), `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini`. The cookbook guide is written around gpt-image-2; the "Image prompting" docs page around 2.5.
- **Caption style:** flexible; docs say "Choose a maintainable format" - short prompts, prose, JSON or tagged sections all work. Recommended order (cookbook): "background/scene -> subject -> key details -> constraints", and include the intended use. 2.5 page steps: define the result (subject + intended use); describe visible details (materials, lighting, colours, medium); specify people/actions (framing, scale, gaze); specify exact text; separate changes from constraints; assign roles to references; iterate one change per turn.
- **Length:** HARD limit **32,000 characters** for all GPT image models (API reference). No recommended length; "Long prompts can work well, but debugging is easier when you start with a clean base prompt and refine with small, single-change follow-ups."
- **Negative prompt:** no field. In-prompt exclusions are explicitly endorsed: "State exclusions and invariants explicitly" - "no watermark", "no extra text", "no logos/trademarks".
- **Quality tokens:** generic buzzwords not addressed. Guidance is targeted levers ("film grain", "macro detail") and the word "photorealistic" for photoreal work; real quality control is the `quality` parameter (`low|medium|high|xhigh|max|auto`). Use medium/high for small text, dense infographics, identity-sensitive edits.
- **Rendered text:** put literal text in **quotes** (or ALL CAPS), describe position and typography; "For tricky words (brand names, uncommon spellings), spell them out letter-by-letter"; add "no extra text".
- **Editing / references:** `images/edits` accepts multiple input images plus optional mask (PNG with alpha marking the area to replace; the mask is guidance, the prompt should still describe the whole desired result). Phrase as "change only X" + "keep everything else the same"; list invariants (identity, geometry, layout, lighting, labels, background, camera angle, framing). Multi-image: "Reference each input by index and description" - "Image 1: product photo... Image 2: style reference...". `input_fidelity` (`low|high`) exists for gpt-image-1 / 1.5 only; gpt-image-2 is high-fidelity by default.
- **Transparency:** `background="transparent"` with `output_format` png or webp (not jpeg); ask for an isolated subject, no scenery, no checkerboard. Supported on 2.5; "preview" on gpt-image-2.
- **Size:** `auto` or custom WxH, multiples of 16, max 3,840 px per edge, max 3:1 ratio (2.5). `n` 1-10.
- **Prompt rewriting:** Images API does not return `revised_prompt` for GPT image models (DALL-E 3 only). When used as the `image_generation` tool in the Responses API, the mainline model rewrites the prompt and returns `revised_prompt`; no documented off switch - call the Images API directly to send the prompt unmodified.
- **Do:** state use + subject first; quote text; list invariants for edits; index references with roles; one change per iteration; add explicit "no watermark / no extra text".
- **Don't:** expect jpeg transparency; leave edit scope open; pile multiple changes in one turn; rely on buzzwords instead of `quality`.

Sources (confidence: **high**)
- https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide - vendor cookbook (gpt-image-2 era).
- https://developers.openai.com/api/docs/guides/image-prompting - vendor; 2.5 prompting steps, params, editing language, transparency.
- https://developers.openai.com/api/docs/guides/image-generation - vendor; models, Responses API prompt revision, masks, limitations.
- https://developers.openai.com/api/reference/resources/images/methods/generate - vendor; 32,000-char limit, model list, params.
- https://openai.com/index/introducing-chatgpt-images-2-5/ - vendor; release date and variants.

---

## 4. Midjourney

- **Developer:** Midjourney, Inc. No official public API (web + Discord only); profile is for prompt text users paste.
- **Current version:** V8.2 default (2026-07-24) - "more creative, bold, sophisticated, and edgy"; V8.1 (2026-04-14) - 4-5x faster, 2K `--hd`, better adherence; V7 (2025-04-03); Niji 7 (2026-01-09).
- **Caption style:** short natural-language phrases + trailing parameters. Official Prompt Basics: **"Short and simple prompts typically generate the best images with Midjourney."** "even a single word or emoji works". Think about subject, medium, environment, lighting, colour, mood, composition. Word choice: use specific synonyms ("huge", "gigantic" rather than "big"); use numbers or collective nouns ("three cats", "flock of birds") instead of vague plurals. "Describe what you do want instead of what you don't. If you mention a party with 'no cake,' a cake might still appear." Order: text prompt -> (image prompts) -> parameters at the very end. With `--raw`, more stylistically detailed prompts give more control.
- **Length:** no maximum stated in the docs (**not found**). Shorter is officially preferred.
- **Negative prompt:** `--no item1, item2` (comma separated), equal to a `-0.5` multi-prompt weight. Caveat: every word after `--no` is moderated separately ("--no modern clothing" is read as "no modern" + "no clothing"). Docs say not to write "without any fruit" / "don't add fruit" in the prompt body.
- **Quality tokens:** docs do not recommend them (not addressed); style comes from `--stylize`, `--raw`, `--sref`, personalization. Omit "8k, masterpiece".
- **Rendered text:** wrap in **double** quotation marks (single quotes do not work); V6+; Latin/English best; short words or phrases; add cues like "with the words" / "written"; if it fails try `--raw` or lower `--stylize`.
- **Parameters (verified):**
  - `--ar W:H` aspect ratio.
  - `--stylize / --s` 0-1000, default 100. Low = closer to prompt; high = more artistic. Also scales personalization strength.
  - `--chaos / --c` 0-100, default 0 (variety across the grid).
  - `--weird / --w` listed in the parameter list; range not shown on the page I read (historically 0-3000 - unverified for V8).
  - `--raw` (V5.1+; docs now show `--raw`, not `--style raw`) removes automatic beautification.
  - `--sref URL1 URL2 | code | random`, per-ref weights `URL::2`; `--sw` 0-1000, default 100; `--sv` selects sref model (V7: 6 versions, default 6; codes work with sv 4 and 6). Works V6 through V8.2. With sref: keep text simple and "describe content, not instructions".
  - `--p` / `--p <profileID|code>` personalization (V6+; V7 global profile works on V8.1/8.2; V8 profiles not on V7). Moodboards also available.
  - `--oref URL` + `--ow` 1-1000 (default 100, keep below 400): **V7 only**, one image, 2x GPU cost. **Not supported on V8.x.**
  - `--cref` / `--cw`: legacy (V6); replaced.
  - **Edit Model** (V8.1 / V8.2): `--edit URL [URL...]` up to 4 images; "replaces Omni Reference and Character Reference". Takes instruction-style prompts ("similar to Conversational mode") as well as descriptions. Incompatible with `--tile` and Remix.
  - `--iw` image weight, `--seed`, `--tile`, `--q` (removed options in V8), `--hd` / `--sd`, `--draft` (V7), `--niji`, `--v`, `--r`.
  - Multi-prompts `::` - syntax `space:: ship`, weights `space::2 ship`, negative weights allowed if the total stays positive. Docs list compatibility only for V1-V6.1 and Niji 4-6; **V7, V8.1, V8.2 are not listed**, so do not emit `::` for current versions.
- **Prompt rewriting:** none by default for /imagine. (Conversational mode / Edit Model interpret instructions, but there is no rewrite flag.)
- **Do:** 1-3 short descriptive phrases; concrete nouns, specific numbers; medium/era/lighting words; put all `--params` last; double-quote text; use `--no` for exclusions.
- **Don't:** long paragraphs; "don't/without" in the body; `::` weights on V7/V8; `--oref`/`--cref` on V8 (use Edit Model); multi-word phrases after `--no`; instruction-style text with `--sref`.

Sources (confidence: **high**)
- https://docs.midjourney.com/hc/en-us/articles/32199405667853-Version - versions and dates.
- https://docs.midjourney.com/hc/en-us/articles/32023408776205-Prompt-Basics - short prompts, word choice, structure.
- https://docs.midjourney.com/hc/en-us/articles/32835253061645-Art-of-Prompting - layering medium/era/emotion/colour/environment.
- https://docs.midjourney.com/hc/en-us/articles/32859204029709-Parameter-List - parameter inventory.
- https://docs.midjourney.com/hc/en-us/articles/32658968492557-Multi-Prompts-Weights - `::` rules and version list.
- https://docs.midjourney.com/hc/en-us/articles/32173351982093-No - `--no`.
- https://docs.midjourney.com/hc/en-us/articles/32502277092109-Text-Generation - quoted text.
- https://docs.midjourney.com/hc/en-us/articles/36285124473997-Omni-Reference - `--oref` V7-only.
- https://docs.midjourney.com/hc/en-us/articles/32162917505293-Character-Reference (now "Edit Model") - `--edit`, replaces oref/cref.
- https://docs.midjourney.com/hc/en-us/articles/32180011136653-Style-Reference - sref/sw/sv.
- https://docs.midjourney.com/hc/en-us/articles/32196176868109-Stylize , .../32099348346765-Chaos-Variety , .../32634113811853-Raw , .../32433330574221-Personalization - ranges and behaviour.

---

## 5. Black Forest Labs hosted FLUX.2 [pro] / [max] / [flex] (differences from open [dev])

- **Developer:** Black Forest Labs. No newer family than FLUX.2 appears in the docs. Lineup: [klein] (open, fast, up to 4 refs), [pro], [max] (adds **grounding search**: "when prompted, it performs web searches to access real-time information"), [flex] ("Specialized for typography. Best for text rendering and preserving small details."; exposes `guidance` 1.5-10 default 5 and `steps` 1-50 default 50), [dev] (open).
- **Shared with [dev] (same prompting guide):** prose, `Subject + Action + Style + Context`; front-load importance ("Main subject -> Key action -> Critical style -> Essential context -> Secondary details"); lengths: short 10-30 words, **medium 30-80 "usually ideal"**, long 80+ for complex scenes; **"FLUX.2 does not support negative prompts. Focus on describing what you want, not what you don't want."**; text in quotation marks with placement/style/size; hex colours written as `color #0047AB` or `hex #0047AB` bound to a named object, gradients "starting with color #02eb3c and finishing with color #edfa3c"; JSON structured prompts with keys `scene, subjects[{description, position, action}], style, color_palette[], lighting, mood, background, camera{angle, lens, depth_of_field}`; prompting in the native language of the content is encouraged.
- **What differs on the hosted endpoints:**
  - **Prompt upsampling is ON by default.** [flex]: `prompt_upsampling` boolean, default `true` -> send `false` to keep your exact prompt. [pro]: the flag is inverted and named **`disable_pup`**, default `false` ("Disable automatic prompt upsampling for this request.") -> send `true`. An LLM enhancer should turn upsampling off to avoid double rewriting. ([max] schema not read; assume same as [pro] - unverified.)
  - [pro]/[max] expose no `guidance`/`steps`; [flex] does.
  - Reference images: API fields `input_image` ... `input_image_8` = **8 refs via API** (10 in playground); [dev] ~6; [klein] 4. [pro]: 9 MP total input+output budget (as relayed). Refer to them as "image 1", "image 2": "Combine furniture from image 1 with the style from image 2".
  - Output: min 64x64, max 4 MP, multiples of 16; up to 2 MP recommended. `safety_tolerance` 0-5 (default 2). `output_format` jpeg (default) / png / webp.
  - Prompt length HARD limit: **not specified** in the API schema.
- **Do:** 30-80 word prose; hex codes tied to objects; quote text; JSON when several subjects/palette must be controlled; "image N" roles for edits; disable upsampling when the prompt is already enhanced.
- **Don't:** negative prompts; quality-tag soup (guide does not use it); send `prompt_upsampling` to [pro] (wrong flag name).

Sources (confidence: **high**)
- https://docs.bfl.ai/guides/prompting_guide_flux2 - vendor prompting guide ([pro] & [max]).
- https://docs.bfl.ai/flux_2/flux2_overview - lineup and differences.
- https://docs.bfl.ai/flux_2/flux2_image_editing - "image N" phrasing, 8/10 refs, 4 MP.
- https://docs.bfl.ai/api-reference/models/generate-or-edit-an-image-with-flux2-%5Bflex%5D - `prompt_upsampling` default true, guidance/steps.
- https://docs.bfl.ai/api-reference/models/generate-or-edit-an-image-with-flux2-%5Bpro%5D - `disable_pup`, 8 input images.

---

## 6. Ideogram 3.0 and Ideogram 4.0 (hosted API)

- **Developer:** Ideogram AI. **4.0** released 2026-06-03 (hosted API + open weights under a commercial licence). **3.0** (API `V_3_1` latest, `V_3_0` March 26 build) still served via `/v1/ideogram-v3/*`.

### Ideogram 4.0 (`POST /v1/ideogram-v4/generate`)
- **Caption style: JSON is the native format.** Request takes either `text_prompt` ("A natural-language prompt for image generation. When supplied, magic-prompt is enabled automatically.") or `json_prompt` ("A structured prompt that conforms to the Ideogram 4.0 JSON contract."; magic prompt disabled). Mutually exclusive. So: **to stop the API rewriting, send `json_prompt`.** A helper endpoint `/magic-prompt-v4` turns text into a `json_prompt` you can pass straight back.
- **JSON contract (key ORDER matters; the model was trained on fixed ordering):**
  - `high_level_description` - 1-2 sentence summary (strongly recommended).
  - `style_description` (optional) - exactly one of `photo` or `art_style`. Photo order: `aesthetics, lighting, photo, medium, color_palette`. Non-photo order: `aesthetics, lighting, medium, art_style, color_palette`. `color_palette`: up to 16 image-wide colours, **uppercase `#RRGGBB`** only.
  - `compositional_deconstruction` (required): `background` string + `elements[]`. Element `type` is `"obj"` or `"text"`. Obj order: `type, bbox?, desc, color_palette?`. Text order: `type, bbox?, text, desc, color_palette?`. `bbox` = `[y_min, x_min, y_max, x_max]` in 0-1000 normalised coordinates, optional. Per-element palette up to 5 colours.
- **Rendered text:** literal string goes in the `text` field of a `"text"` element; typography described in `desc`; optional bbox for placement. In plain-text mode, quote the text.
- **Negative prompt:** none in the v4 request schema. **Style types:** none in v4 (style lives in `style_description`). Other params: `resolution` (1K/2K, 38 values), `rendering_speed` FLASH (not yet live) / TURBO / DEFAULT / QUALITY.
- **Length:** not found (no max stated).
- **Open-weights note (for your existing open profile):** "Passing in plain-text prompts directly to the model will not work and will likely trigger a safety warning"; the OSS magic prompt "is not the same magic prompt used in production".
- **When to use JSON vs text (vendor):** JSON for design work, posters, exact text placement, fixed palettes, repeatable layouts; natural language for quick exploration and photoreal scenes.

### Ideogram 3.0 (`POST /v1/ideogram-v3/generate`)
- **Caption style:** natural-language prose; quote the text to render.
- `magic_prompt`: `AUTO` (default) / `ON` / `OFF` -> **send `OFF`** when the prompt is already enhanced. Magic Prompt also translates non-English prompts.
- `style_type`: `AUTO | GENERAL | REALISTIC | DESIGN | FICTION` (API default GENERAL); `style_preset` (62 presets); `style_codes`; `style_reference_images`; `character_reference_images`; `color_palette` (presets or hex + weights).
- `negative_prompt`: **separate field**, comma-separated terms. Vendor caveat: "The content of the regular prompt will always be favored over the negative prompt."; better to write a prompt that excludes things naturally.
- `num_images` 1-8, `seed`, `aspect_ratio` or `resolution`, `rendering_speed`. Transparent-background variant endpoint exists (`generate-transparent-v3`). Prompt max length: not found.
- **Quality tokens:** not addressed by vendor; omit.
- **Do:** (v4) emit valid JSON in the documented key order, uppercase hex, text as text-elements; (v3) prose + quoted text, pick `style_type`, set `magic_prompt: OFF`. **Don't:** mix `text_prompt` and `json_prompt`; reorder keys; lowercase/shorthand hex; contradict the main prompt in the negative prompt.

Sources (confidence: **high**)
- https://developer.ideogram.ai/api-reference/api-reference/generate-v4 - v4 params, text vs json, magic prompt auto.
- https://developer.ideogram.ai/api-reference/api-reference/magic-prompt-v4 - magic-prompt endpoint returns json_prompt.
- https://docs.ideogram.ai/using-ideogram/getting-started/prompting-guide/4.-json-prompting-ideogram-4.0 - JSON schema, key order, bbox, palette.
- https://github.com/ideogram-oss/ideogram4/blob/main/docs/prompting.md - vendor OSS prompting doc.
- https://developer.ideogram.ai/api-reference/api-reference/generate-v3 - v3 params and enums.
- https://docs.ideogram.ai/using-ideogram/generation-settings/negative-prompt , .../magic-prompt , .../available-models - behaviour notes, model list.
- https://ideogram.ai/news/ideogram-4.0/ - release date.

---

## 7. Others (brief)

### Recraft V4 / V4.1 (and V3)
- Developer Recraft. Latest **V4.1** (`recraftv4_1`, `_pro`, `_vector`, `_utility` variants); V4 (`recraftv4`, `recraftv4_pro`, `_vector`); V4 Styles (`recraftv4_styles*`, up to 10 style reference images, a style is mandatory); `recraftv3`, `recraftv2`.
- Style: both modes are valid. Short "interpretive" prompts (3-6 words, e.g. "Fashion couple portrait, close up.") for exploration; long "architectural" structured prose for control, ordered global -> local: core concept, background, framing/pose, physical attributes, secondary subjects, lighting, camera/depth, mood. "Prompt engineering here is not about verbosity. It's about defining structure, surface, space, hierarchy, and control." Putting style first vs scene first shifts emphasis. Vector/logo: define shape logic, strict palette, "Flat colors only - no gradients, shadows, or texture"; avoid texture/material words. Illustration: use drawing logic, not camera logic. Photoreal: avoid stacking dramatic adjectives.
- HARD limit: **10,000 characters** (V4 / V4.1 / V4 Styles); **1,000 characters** (V3 / V2).
- Negative prompt: `negative_prompt` field **V2/V3 only**. V4.x: write constraints in-prompt ("no gradients").
- Text: put exact text in quotation marks; define hierarchy, size, placement; avoid micro text. `text_layout` (text + bbox) is **V3 only**. `controls` (colors, background_color, artistic_level, no_text) only partially supported on V4/V4.1.
- Quality tokens: discouraged implicitly ("Don't stack evaluative adjectives", "vague quality descriptors"). Prompt rewriting: none documented.
- Sources (**high**): https://www.recraft.ai/docs/prompt-engineering-guide/prompting-with-recraft-v4.md ; https://www.recraft.ai/docs/api-reference/endpoints.md ; https://www.recraft.ai/docs/api-reference/appendix.md ; https://www.recraft.ai/docs (model list); https://www.recraft.ai/docs/llms.txt (index; this is the markdown variant used). Third-party: https://runware.ai/docs/models/recraft-v4-styles/guides/prompting (with style refs, keep style words out of the prompt) (low).

### Reve Image
- **Vendor source not found** (no publicly readable Reve API/prompt docs). Third-party only: fal lists **Reve 2.1** with create / edit / remix; remix takes 1-8 images referenced in the prompt with `<frame>N</frame>` tags (0-based); no negative-prompt field; aspect ratio param incl. `auto`; prompt max not stated. Earlier fal/Reve 1.0 remix used `<img>N</img>` tags - check the endpoint version. Confidence **low**. Source: https://fal.ai/models/reve/2.1/remix/api

### Luma (Photon -> Uni-1)
- Developer Luma AI. Legacy Dream Machine API: `photon-1` (default), `photon-flash-1`. Params: `prompt`, `aspect_ratio` (1:1, 3:4, 4:3, 9:16, 16:9 default, 9:21, 21:9), `image_ref` (up to 4, each with `weight`), `style_ref` (weighted), `character_ref` (`identity0`, up to 4 images of the same person), `modify_image_ref` (edit with weight). No negative prompt, no enhancer flag, no length limit documented. Prose prompts.
- Newer Luma Agents API: models **`uni-1`, `uni-1-max`**; prompts **1-6,000 characters**; up to 8 `image_ref`; `image_edit` requires `source`. Guidance: be specific, e.g. "Replace the background with a tropical beach at sunset, warm golden light matching the direction of light on the subject"; label each reference's role: "Apply the lighting from the first reference and the texture from the second." Negative prompt: not mentioned.
- Sources (**high** for params, no prompting guide found): https://docs.lumalabs.ai/docs/image-generation ; https://docs.agents.lumalabs.ai/guides/image-editing/

### xAI Grok Imagine
- Model `grok-imagine-image-2.0` (docs no longer say "Aurora"). Params: `n` 1-10, `aspect_ratio` (incl. `auto`), `resolution` 1k/2k, `quality` low/medium/auto, `response_format`. Editing: source image (URL / data URI / file id) + instruction prompt, e.g. "Render this image as an oil painting in the style of impressionism"; separate multi-image editing feature. No negative prompt, no documented prompt length limit, no `revised_prompt` mentioned, no masks, no vendor prompting guide (**not found**). Use plain descriptive prose.
- Sources (**high**, but thin): https://docs.x.ai/developers/model-capabilities/images/generation ; https://docs.x.ai/developers/model-capabilities/images/editing

### Adobe Firefly Image 4 / 5
- Firefly API "Image5" (Generate Image API, text-to-image and prompt-driven edit). Migration notes: **`negativePrompt` field supported**, `promptBiasingLocaleCode` (e.g. en-US, fr-FR, ja-JP) biases content to a locale, `contentClass`, `visualIntensity`, `upsamplerType`, `numVariations` (renamed from `n`), `customModelId`; removed `aspectRatio` (use width/height) and explicit model versioning. `modelSpecificPayload.prompt_reasoner` (e.g. "quality") "uses enhanced prompt reasoning" = vendor-side prompt reasoning; off-value not captured.
- Prompt formula (Adobe community guide, covers Image 5 / 4 Ultra / 4): image type, subject (expression, posture, emotion), action, angle, lighting, background, colour palette, style. "Be specific, not vague"; keep prompts focused; for Image 5 "be specific from the start. Include expression, lighting, and mood in your first prompt, then add camera details." Do not contradict UI/API style settings in the prompt. Text rendering is called out as a limitation.
- Prompt max length: **not found** in readable pages (API reference 404; historically 1024 chars for Firefly v3 - unverified).
- Sources (**medium**): https://developer.adobe.com/firefly-services/docs/firefly-api/guides/how-tos/cm-generate-image/breaking-changes ; .../cm-generate-image/feature-guide ; .../how-tos/firefly-generate-image-api-tutorial ; https://community.adobe.com/p/firefly-image-guide

### Leonardo Phoenix
- Phoenix 1.0 (`phoenix-v1.0`) and 0.9. Prompt max **2,000 characters**. Negative prompt supported (separate field). **Prompt enhance: AUTO / ON / OFF** -> set OFF when pre-enhanced. Contrast LOW/MEDIUM/HIGH; modes FAST/QUALITY/ULTRA; 25 preset styles by UUID; guidance refs: style (up to 4), content (1), character (1), image-to-image (1), strength LOW..MAX; 1-8 images; 32-2048 px multiples of 8. Prose prompts; Phoenix is marketed on prompt adherence and text rendering; no vendor prompt-style guide read (not found).
- Source (**high**): https://docs.leonardo.ai/docs/phoenix ; enhancer endpoint: https://docs.leonardo.ai/docs/generate-enhanced-prompts

### Kling image (Kolors lineage) - Kuaishou
- "Kolors 2.x" is the consumer name of the older generation; current are **Kling IMAGE 3.0** (2026-02-04) and **IMAGE 3.0 Omni** (2026-02-06; native 2K/4K, image-series mode with min 2 images, auto count), plus IMAGE O1. Hunyuan Image is Tencent, a different vendor - not researched here.
- Style: natural language + images. Edit formula: "Keep everything else unchanged, modify [target] to [desired effect]" (e.g. "Keep everything else unchanged, change the cat into a dog"). Face reference formula: "Keep [person]'s facial features, character has [hairstyle], wearing [clothing], performing [action], background is [setting], with [lighting], and [atmosphere]". Up to 10 reference images. Use clear directional/positional instructions; Omni guide examples are cinematic prose (composition, focal length 24-200mm, aperture, lighting). Omni guide references negative-prompt support without detail.
- Limits: consumer UI guide says prompt up to **500 characters**, Chinese/English. API (third-party wrapper of official spec, models `kling-v1 ... kling-v2-1`): prompt max **2,500 chars**, `negative_prompt` max 2,500 chars, `image_reference` = `subject` | `face` with `image_fidelity` / `human_fidelity` 0-1, n 1-9. Official API reference is JS-rendered and was not readable; limits for IMAGE 3.0 via API: **not found**.
- Sources: https://kling.ai/quickstart/klingai-image-3-model-user-guide (**high**), https://kling.ai/quickstart/klingai-image-3-omni-user-guide (**high**), https://kling.ai/quickstart/ai-image-generation-guide (high; 500 chars), https://github.com/aself101/kling-api (**low**; API limits), https://kling.ai/document-api/apiReference/model/imageGeneration (vendor, unreadable).

### Runway Gen-4 Image / References
- API models `gen4_image`, `gen4_image_turbo` (`POST /v1/text_to_image`). `referenceImages[]` each `{uri, tag}`; mention them in `promptText` with **`@tag`**: "@EiffelTower painted in the style of @StarryNight". Untagged references act as style influence. **Up to 3 references.** Ratios are pixel strings (1920:1080 default, 1080:1920, 1024:1024, 1360:768, 1080:1080, 1168:880, 1440:1080, 1080:1440, 1808:768, 2112:912, 1280:720, 720:1280, 720:720, 960:720, 720:960, 1680:720).
- Style: conversational natural language; "starting with a simple prompt and iterating by adding more details". For full-body shots, describe shoes or trousers. Reference photos: natural even lighting, neutral expression.
- promptText limit: **not found** in readable pages (commonly cited as 1,000 characters - unverified). Negative prompt: none. Rewriting: none documented.
- Sources (**high** for syntax): https://docs.dev.runwayml.com/guides/using-the-api/ ; https://help.runwayml.com/hc/en-us/articles/40042718905875-Creating-with-Gen-4-Image-References ; ratios via https://glama.ai/mcp/servers/runwayml/runway-api-mcp-server/tools/runway_generateImage (Runway's own MCP server listing; medium).

---

## 8. Verification: Illustrious XL (OnomaAI) - open model

**Underscores or spaces? -> SPACES.** Evidence, all from Onoma's own material:
- Paper (arXiv 2409.19946) literal prompts: `"1boy, doctor, masterpiece, looking at viewer"`, `"1girl, hatsune miku, worst quality, ms paint (medium)"`, `"1girl, happy, smile, crying, 2koma"`. Multi-word Danbooru tags (`looking_at_viewer`, `hatsune_miku`, `ms_paint_(medium)`) are written with spaces; parentheses kept.
- Quality tags named in the paper are spaced: "worst quality", "bad quality", "average quality", "good quality", "best quality", "masterpiece".
- v0.1 model card example (via an fp8 mirror that reuses Onoma's sample): "1girl, solo, flower, too many, long hair, sitting, barefoot, dress, sky, water, ocean, beach" + "masterpiece, best quality, original, absurdres".
- Paper on separators: "we split the tags using the ',' convention, later occasionally replacing it with spaces based on a certain probability" - i.e. comma-separated is canonical. No sentence in the paper mentions underscores. (In A1111/ComfyUI, parentheses in tags like `ms paint (medium)` must be escaped `\(medium\)` - tooling convention, not from Onoma.)

**Tag order (paper, training caption schema):** "person count ||| character names ||| rating ||| general tags ||| artist ||| score range based rating ||| year modifier". So: `1girl, <character>, <rating>, <general tags>, <artist>, <quality tag>, <year>` - **quality tags go near the END**, unlike the Animagine/Pony habit of leading with them. (The paper's own demo prompt puts "masterpiece" mid-prompt, so order is a soft prior.)

**Quality tags (score percentiles):** worst quality ~8%, bad quality ~20%, average quality ~60%, good quality ~82%, best quality ~92%, masterpiece ~top. They genuinely condition this model (they are training labels), so keep `masterpiece, best quality` positive and `worst quality, bad quality` negative.

**Prompt length:** no recommended length or token cap is stated in the paper or model cards (**not found**). The paper only notes padding tokens act as register tokens. Standard SDXL CLIP 75-token chunks apply (tooling fact, not an Onoma statement).

**Other official settings (v0.1 model card):** "Euler a, Sampling Steps: 20-28, CFG: 5-7.5"; use composition tags (upper body, portrait, full body) but do not stack conflicting ones (close-up + cowboy shot). Official negative prompt string: not captured.

**Natural language:** v0.1 is tag-only. v1.0 card: supports "plain English descriptions, precise tags, or both", but "tag-based approaches are more concise and accurate"; native 1536 px; knowledge to June 2024. Paper: v1.1 / v2.0 trained with multi-level captions (tags + natural language).

Sources (confidence: **high** for spaces/order/quality tags; medium for sampler settings)
- https://arxiv.org/html/2409.19946v1 - tag order string, quality percentiles, literal prompts, comma convention, dropout notes.
- https://huggingface.co/OnomaAIResearch/Illustrious-xl-early-release-v0 - Euler a / steps / CFG, composition-tag advice.
- https://huggingface.co/OnomaAIResearch/Illustrious-XL-v1.0 and https://civarchive.com/models/1232765?modelVersionId=1389133 (Onoma's Civitai text) - natural language + tags, 1536 px, "tag-based approaches are more concise and accurate".
- https://huggingface.co/OnomaAIResearch/Illustrious-XL-v2.0/blob/main/README.md - v2.0-stable notes (no prompt guidance).
- https://huggingface.co/p1atdev/Illustrious-XL-v0.1-fp8/blob/main/README.md - third-party mirror with spaced sample prompt (low).

---

## 9. Cross-model cheat sheet for profile authors

| Model | Format | Target length | Negative | Text | Disable vendor rewrite |
|---|---|---|---|---|---|
| Seedream 4.x/5.0 | prose, subject+action+environment | <= 600 EN words (hard ~4000 tokens) | none | "double quotes" | not found (`optimize_prompt_options.mode` standard/fast) |
| Nano Banana 2 / Pro | narrative paragraph, verb-first | free (64k-131k tokens) | semantic (positive framing) | "quotes" + font | n/a (thinking built in) |
| gpt-image-2 / 2.5 | any; scene -> subject -> details -> constraints | free (32,000 chars) | in-prompt "no X" is endorsed | "quotes"/CAPS, spell letter-by-letter | use Images API, not Responses tool |
| Midjourney V8.2 | short phrases + `--params` | short; no stated max | `--no a, b` | "double quotes" only | n/a |
| FLUX.2 pro/max/flex | prose or JSON, hex colours | 30-80 words | none | 'quotes' + placement | pro: `disable_pup: true`; flex: `prompt_upsampling: false` |
| Ideogram 4.0 | **JSON contract** | n/a | none | `text` element | send `json_prompt` |
| Ideogram 3.0 | prose | not stated | `negative_prompt` field | "quotes" | `magic_prompt: "OFF"` |
| Recraft V4/4.1 | short or structured prose | <= 10,000 chars | none (V2/V3 only) | "quotes" + hierarchy | n/a |
| Leonardo Phoenix | prose | <= 2,000 chars | field | - | enhance `OFF` |
| Kling IMAGE 3.0 | prose / edit formula | 500 (UI) / 2,500 (API, older models) | field (API) | - | n/a |
| Runway gen4_image | conversational + `@tag` | not found | none | - | n/a |
| Luma uni-1 | prose | 1-6,000 chars | none | - | n/a |
| Grok Imagine 2.0 | prose | not stated | none | - | n/a |
| Firefly Image5 | formula prose | not found | `negativePrompt` | weak | `prompt_reasoner` (off value not found) |
