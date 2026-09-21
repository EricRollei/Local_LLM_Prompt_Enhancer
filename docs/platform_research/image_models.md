# Image-model prompting facts for LLM prompt-enhancer profiles

Research date: 2026-09-20. Confidence labels: **high** = official source read directly this session; **medium** = official but indirect (official text seen through a mirror, or inferred from official code); **low** = third-party only.

Access notes: GitHub raw files and diffusers source were read directly (verbatim). HuggingFace / vendor pages were read through a summarising fetcher (content is official, wording may be paraphrased unless shown in quotes). The official BFL Kontext guide URL returned 404 / was blocked, so Kontext rules come from a mirror plus BFL's own `skills` repo.

Local verbatim copies of official rewriter prompts (same scratchpad dir): `qwen_pu.py`, `q_prompt_utils_2512.py`, `qwen21_pe_core.py`, `hy3_PE_system_prompt.py`, `hy3_hunyuan_image_3_system_prompt.py`, `f_reprompt.py`, `flux2_system_messages.py`, `krea_expansion.txt`, `ideo_v1.txt`, `ideo_prompting.md`, `bfl/*.md`.

---

## 1. FLUX.2 [dev] and FLUX.2 [klein]  — confidence: high

| Field | FLUX.2 [dev] | FLUX.2 [klein] 4B / 9B (+ Base, 9B-KV) |
|---|---|---|
| Developer | Black Forest Labs | Black Forest Labs (released 2026-01-15) |
| Text encoder | Mistral-Small-3.2-24B-Instruct-2506 (LLM/VLM) | Qwen3 (Qwen3ForCausalLM; repo loads `Qwen/Qwen3-{variant}-FP8`; 4B model pairs with Qwen3-4B, 9B with Qwen3-8B) |
| Hard token limit | 512 (`MAX_LENGTH = 512`, diffusers `tokenizer_max_length = 512`) | 512 |
| Best style | Natural-language prose, or JSON structured prompt; T2I + single/multi-reference edit in one model | "Narrative prose", novelist style, lighting-heavy; **no prompt upsampling on klein – be descriptive yourself** |
| Recommended length | 30–80 words "usually ideal"; 10–30 quick; 80+ complex scenes | 40–70 words ("moderately detailed") |
| Negative prompt | **Not supported** (guidance-distilled; diffusers Flux2Pipeline has no `negative_prompt`) | Distilled klein: no (CFG disabled when `is_distilled`). Base (undistilled) klein: real CFG exists in diffusers, but BFL guidance is still "no negative prompts" |
| Quality tokens | Hurt/ignored: BFL shows `woman, portrait, beautiful, ... 8k, detailed` as the *less effective* keyword style. Use camera/lens/film stock instead | same |

Structure: `Subject + Action + Style + Context` (docs) / `[Subject] + [Action/Pose] + [Style/Medium] + [Context/Setting] + [Lighting] + [Technical]` (skills repo). Word order matters: "FLUX.2 pays more attention to what comes first."

JSON base schema (official): keys `scene`, `subjects[] {description, position, action}` (examples also use `type`, `pose`, `color_match`, `detail_preservation`), `style`, `color_palette` (array of hex), `lighting`, `mood`, `background`, `composition`, `camera {angle, lens, depth_of_field}` (examples also `distance`, `focus`, `lens-mm`, `f-number`, `ISO`). Official upsampler rule: "Keep structured inputs structured (enhance within fields). Convert natural language to detailed paragraphs."

Hex colours: supported. Signal with the word "color" or "hex" before the code and bind it to an object: `an apple in color #0047AB`, `walls in hex #C4725A`; gradients: `starting with color #02eb3c and finishing with color #edfa3c`. Skills repo: "Use #RRGGBB alongside color names."

Rendered text: put it in quotation marks; state placement, font style, size, colour. Official T2I upsampler: "Put ALL text in quotation marks, matching the prompt's language. Always provide explicit quoted text for objects that would contain text in reality (signs, labels, screens) – without it, the model generates gibberish."

Editing (I2I) official rewriter rules: one concise instruction, 50–80 words (~30 for brief requests); analytical language (avoid "whimsical", "cascading"); say what changes AND what stays the same (face, lighting, composition); reference actual image elements; turn negatives into positives ("don't change X" -> "keep X"); make abstractions concrete. Reference images: klein up to 4, pro 8, max 8–10; refer by "image 1 / image 2" or natural language.

Do: front-load subject; always describe lighting (BFL: biggest quality lever); camera/lens/film for photorealism; quote text; bind hex to objects.
Don't: negative phrasing ("no glasses" -> "clear face, visible eyes"); keyword soup; "8k, masterpiece"; vague hex with no object; prompt weights (no weight syntax documented).

When to upsample (official): helps text-in-image, image-annotation instructions, code/math reasoning; little benefit for simple direct prompts.

Official rewriter system prompts:
- https://raw.githubusercontent.com/black-forest-labs/flux2/main/src/flux2/system_messages.py (`SYSTEM_MESSAGE_UPSAMPLING_T2I`, `SYSTEM_MESSAGE_UPSAMPLING_I2I`)

Sources:
- https://docs.bfl.ml/guides/prompting_guide_flux2 — structure, lengths, JSON schema, hex, no negatives, typography (guide is titled for [pro]/[max]; applies family-wide)
- https://raw.githubusercontent.com/black-forest-labs/flux2/main/README.md — klein release, dev encoder = Mistral-Small-3.2-24B, "dev benefits significantly from prompt upsampling"
- https://raw.githubusercontent.com/black-forest-labs/flux2/main/src/flux2/text_encoder.py — MAX_LENGTH 512, Qwen3 embedder for klein
- https://raw.githubusercontent.com/black-forest-labs/flux2/main/docs/flux2_with_prompt_upsampling.md — when to upsample
- https://raw.githubusercontent.com/black-forest-labs/skills/master/skills/flux-image-best-practices/rules/flux2-models.md — per-model style; klein 40–70 words, no upsampling, 4 refs
- https://raw.githubusercontent.com/black-forest-labs/skills/master/skills/flux-image-best-practices/rules/core-principles.md — prose > keywords, no negatives, lighting
- https://raw.githubusercontent.com/black-forest-labs/skills/master/skills/flux-image-best-practices/rules/json-structured-prompting.md , `.../hex-color-prompting.md`, `.../typography-text.md`, `.../negative-prompt-alternatives.md`, `.../i2i-prompting.md`, `.../multi-reference-editing.md`
- https://raw.githubusercontent.com/huggingface/diffusers/main/src/diffusers/pipelines/flux2/pipeline_flux2.py and `pipeline_flux2_klein.py` — encoders, 512 limit, negative-prompt handling

---

## 2. FLUX.1 Kontext [dev] (instruction edit) — confidence: medium

- Developer: Black Forest Labs. Text encoders: CLIP-L + T5-XXL (same as FLUX.1; diffusers FluxKontextPipeline).
- Hard limit: **512 tokens** (diffusers raises above 512; official guide states "maximum prompt limit of 512 tokens").
- Style: imperative **edit instruction**, not a scene description. Negative prompt: ignored in normal use (guidance-distilled; diffusers only uses `negative_prompt` when `true_cfg_scale > 1`).
- Quality tokens: irrelevant/harmful – the prompt is an instruction.

Official guide rules (seen via mirror, wording matches BFL guide):
1. Be specific: exact colours, precise verbs; more explicit is better as long as each edit's instructions are not overly complex.
2. Preservation clause: `...while maintaining the same [facial features / composition / lighting]`; "keep everything else identical".
3. Verb choice: **"Transform" may imply a complete change**; prefer "Change the clothing to…", "Replace the background with…".
4. **No pronouns**: write "The woman with short black hair", not "she"/"this person".
5. Text edits: `Replace '[original text]' with '[new text]'` – quotes around both; preserve case; ask to keep font style if wanted.
6. Style transfer: name the style, describe its traits (brushwork, palette), and state what to keep (composition, subject positions).
7. Big changes: go step by step (iterative edits) rather than one giant instruction.
8. Composition control: say "keep the subject in the exact same position, scale, and pose" when swapping backgrounds.

Note: BFL's own skills repo now says FLUX.2 with reference images supersedes Kontext, and its Kontext examples do use "Transform… maintaining the original composition" — i.e. "transform" is acceptable only when paired with an explicit preservation clause.

Official rewriter system prompt: **not found** for Kontext (the FLUX.2 I2I upsampling prompt in section 1 is the closest official equivalent).

Sources:
- https://docs.bfl.ai/guides/prompting_guide_kontext_i2i (official guide; also indexed as https://docs.us.bfl.ai/guides/prompting_guide_kontext_i2i which returned 404 today) — could not be fetched directly
- https://comfyui-wiki.com/en/tutorial/advanced/image/flux/flux-1-kontext — third-party mirror quoting the official guide: 512 tokens, transform pitfall, pronoun pitfall, preservation phrasing, text quote syntax
- https://raw.githubusercontent.com/black-forest-labs/skills/master/skills/flux-image-best-practices/rules/flux1-models.md — official Kontext tips ("Be explicit about what should NOT change", start simple, incremental refinement)
- https://raw.githubusercontent.com/huggingface/diffusers/main/src/diffusers/pipelines/flux/pipeline_flux_kontext.py — CLIP+T5, 512 cap, true_cfg

---

## 3. Chroma (Chroma1-Base / HD / Flash / Radiance) — confidence: medium (specs high, prompting style low)

- Developer: lodestones (Lodestone Rock). 8.9B, derived from FLUX.1-schnell, Apache-2.0. Radiance = pixel-space variant (not separately verified this session).
- Text encoder: **T5-XXL only** (`google/t5-v1_1-xxl`); no CLIP. Hard limit 512 tokens (diffusers default 512).
- Negative prompt: **Yes – real CFG** (de-distilled). Model card example: guidance 3.0, 40 steps; diffusers default 5.0. Chroma1-Flash has CFG "baked" -> run at CFG 1, negative ignored.
- Official example negative: `low quality, ugly, unfinished, out of focus, deformed, disfigure, blurry, smudged, restricted palette, flat colors`.
- Official example positive is full-sentence natural language that ends with quality-style sentences ("The photo is sharp and well-composed… It looks professionally done.").
- No official prompting guide or dataset report exists (users ask for one in the HF discussions; unanswered).

Third-party (low confidence – levzzz guide shipped in the chromaforge repo, Civitai articles):
- Captions reportedly generated with Gemini 1.5 Flash -> write Gemini-style descriptive prose; optionally append tags at the end. Period-separated tags keep realism; comma tag lists pull toward anime/cartoon.
- "aesthetic N" tags: `aesthetic 0`…`aesthetic 10`, plus `aesthetic 11` for curated AI images (can cause bleed). Typical use: `aesthetic 10`/`aesthetic 11` in positive, `aesthetic 0, aesthetic 1, low quality` in negative. Booru quality tags (`masterpiece, best quality`) have variable effect.
- Negative prompts shorter than ~70 tokens are discouraged (either write a long one or leave empty); T5 padding must leave exactly one pad token unmasked (handled by ComfyUI/diffusers).
- Most artist names and obscure characters were not learned – describe features explicitly.
- e621/danbooru tags are understood (dataset includes lodestones' e621 caption set), but prose should lead.

Do: 2–6 sentence prose, medium stated explicitly ("A photograph of…", "digital illustration"), long descriptive negative, CFG 3–5.
Don't: rely on artist names; use short token-y negatives; use CFG >1 on Flash.

Official rewriter system prompt: **not found**.

Sources:
- https://huggingface.co/lodestones/Chroma1-HD — arch, T5-XXL, example prompt/negative, CFG 3.0 / 40 steps, 5M-of-20M dataset, Flash variant
- https://huggingface.co/docs/diffusers/main/api/pipelines/chroma — 512 tokens, negative prompt support, padding-mask note
- https://huggingface.co/lodestones/Chroma1-HD/discussions/21 — confirms no official prompt guide
- https://huggingface.co/lodestones/Chroma/discussions/72 — "aesthetic 11" question (thread body not retrievable)
- https://github.com/maybleMyers/chromaforge/blob/main/levzzz_chroma_guide.md — third-party: Gemini captions, aesthetic tags, negative length, 512 tokens
- https://civitai.com/articles/20400/aesthetic-tag-in-chroma — third-party (not read)

---

## 4. Krea 2 (K2 Raw / K2 Turbo) — confidence: high

- Developer: Krea. Open weights released 2026-06-23 (`krea/Krea-2-Raw`, `krea/Krea-2-Turbo`), single-stream DiT, Qwen-Image VAE.
- Text encoder: **Qwen3-VL-4B-Instruct** (multi-layer feature aggregation). Hard limit **512 tokens** (`max_length: int = 512` in `encoder.py`). Encoder wraps the prompt in the Qwen-Image-style system template "Describe the image by detailing the color, shape, size, texture, quantity, text, spatial relationships of the objects and background:".
- Style: natural language. Official: "Long detailed prompts yield best results, but the model is capable of generating high quality images with minimal prompt engineering." Official examples are both (a) single dense prose paragraphs of ~60–150 words and (b) comma-separated descriptive phrase lists (not booru tags). Training used long VLM captions re-formatted into multiple lengths/styles.
- Negative prompt: Turbo = 8 steps, **CFG 0 -> negative ignored**. Raw = 52 steps, CFG 3.5 (CLI default 4.5) -> negative usable. "Train on Raw, run on Turbo."
- Rendered text: "putting quotes around the words to be rendered".
- Quality tokens: not used in any official example; the official expander forbids over-specification rather than adding boilerplate.
- Special syntax: none official. `(keyword:1.5)` weights and negative weights come from a community ComfyUI node (low confidence), not from Krea.

Official expander rules (expansion.txt): faithfulness first (no new objects); group each subject with its own attributes/actions; one cohesive paragraph, no bullets/JSON/markdown; quote requested text; **avoid over-specification**; if the prompt is already detailed, only polish; preserve the user's stated medium ("photo of", "illustration of").

Official rewriter system prompt:
- https://raw.githubusercontent.com/krea-ai/krea-2/main/docs/expansion.txt

Sources:
- https://www.krea.ai/blog/krea-2-technical-report — date, architecture, Qwen3-VL encoder, caption pipeline, trained prompt expander, TDM distillation
- https://raw.githubusercontent.com/krea-ai/krea-2/main/README.md — Raw 52 steps/CFG 3.5, Turbo 8 steps/CFG 0, mu 1.15
- https://raw.githubusercontent.com/krea-ai/krea-2/main/docs/prompting.md — official prompting guide + examples
- https://raw.githubusercontent.com/krea-ai/krea-2/main/encoder.py — 512 tokens, template; `inference.py` — `Qwen/Qwen3-VL-4B-Instruct`
- https://docs.comfy.org/tutorials/image/krea/krea-2 — ComfyUI files (`qwen3vl_4b_fp8_scaled.safetensors`)
- https://gist.github.com/cicalooo/6d26f1d4d54f6d05e87e6fde94b703b7 — third-party weighting/pose guide

---

## 5. Z-Image / Z-Image-Turbo (and Z-Image-Edit) — confidence: high

- Developer: Alibaba Tongyi-MAI. 6B single-stream DiT (S3-DiT).
- Text encoder: **Qwen3-4B** (LLM; diffusers applies the Qwen3 chat template with `enable_thinking=True`). Default `max_sequence_length` **512**; official team advice: set `max_sequence_length=1024` locally for longer prompts (online demo caps at 512).
- Style: long, detailed, objective natural-language description; Chinese or English (bilingual text rendering, quote the text). Official team: model works best with "long and detailed prompts", ideally LLM-enhanced. README example prompts are dense, clipped descriptive sentences (~70–120 words EN; ~250 Chinese characters).
- Negative prompt: **Turbo: none** – few-step distilled, run with `guidance_scale=0.0` ("Guidance should be 0 for the Turbo models"); negative text is ignored. **Z-Image (base): negative prompts "strongly recommended"**, guidance 3.0–5.0.
- Quality tokens: **explicitly banned by the official enhancer** – "绝不包含 '8K'、'杰作' 等元标签或绘制指令" (never include meta-tags like "8K", "masterpiece", or drawing instructions). Also bans metaphors and emotional rhetoric.
- Rendered text: transcribe verbatim inside **English double quotes ""**; for posters/menus/UI list every text item with font and layout; for signs/screens give content, position, size, material.
- Prompt-enhancer extras: lock immutable elements (subject, count, action, state, IP names, colours, text); "generative reasoning" – if the user asks for a solution/design, first invent the concrete visual answer, then describe it; then add composition, lighting, materials, colour scheme, spatial layering; output only the final prompt.

Official rewriter system prompt (Chinese, works for EN input too):
- https://huggingface.co/spaces/Tongyi-MAI/Z-Image-Turbo/blob/main/pe.py (raw: https://huggingface.co/spaces/Tongyi-MAI/Z-Image-Turbo/raw/main/pe.py) – variable `prompt_template`; demo calls Qwen3-max and expects JSON with `revised_prompt`.

Sources:
- https://raw.githubusercontent.com/Tongyi-MAI/Z-Image/main/README.md — variants, guidance 0 for Turbo, base: CFG 3–5 + negatives recommended, bilingual text, prompt-enhancer mention
- https://huggingface.co/spaces/Tongyi-MAI/Z-Image-Turbo/raw/main/pe.py — full enhancer template (read verbatim)
- https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/discussions/8 — official "PROMPTING GUIDE" thread by org member: 512 vs 1024 tokens, no CFG/negatives on Turbo, long prompts
- https://huggingface.co/spaces/Tongyi-MAI/Z-Image-Turbo/blob/main/app.py — demo defaults, PE via DashScope
- https://raw.githubusercontent.com/huggingface/diffusers/main/src/diffusers/pipelines/z_image/pipeline_z_image.py — 512 default, thinking chat template

---

## 6. Qwen-Image (2508 / 2512 / 2.0 / 2.1) and Qwen-Image-Edit (2509 / 2511) — confidence: high

- Developer: Alibaba Qwen. Qwen-Image / 2512 / Edit-25xx: 20B MMDiT, text encoder **Qwen2.5-VL-7B**; diffusers `tokenizer_max_length = 1024` (hard error above 1024; call default 512).
- **Qwen-Image-2.0** (2026-02-10): announced as API / Qwen Chat model ("supports 1k-token instructions"); no open weights found under that name.
- **Qwen-Image-2.1** (open weights released 2026-09-20, Qwen Research License): 7B single-stream DiT, unified T2I + edit, text encoder **Qwen3-VL 8B**, native 2K, 40 steps, guidance-scale 1 in the vLLM example. Ships two fine-tuned rewriter models (Qwen3.5-VL 9B): `Qwen/Qwen-Image-2.1-PE-T2I` and `Qwen/Qwen-Image-2.1-PE-I2I`; each checkpoint carries its own `system_prompt.txt` (not fetched – HF blocked). Output contract: T2I `{"rewritten_prompt": "...", "wh_ratio": "16:9"}`; edit `{"rewritten_prompt": "...", "wh_ratio": "", "ratio_follow": "<image1>"}`.
- Style: fluent natural-language description, Chinese or English. Length: original rewriter "less than 200 words"; 2512 rewriter "ideally around 200 words" for portraits (ZH: within 150 characters for portraits); infographics may be much longer with line breaks.
- Negative prompt: **Yes** (true CFG, `true_cfg_scale` 4.0). Use `" "` (single space) if none. Official 2512 negative: `低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。` Edit models: `negative_prompt=" "`.
- **Magic suffix** (original Qwen-Image): EN `", Ultra HD, 4K, cinematic composition."` / ZH `", 超清，4K，电影级构图."` – appended by `prompt_utils.py`. In `prompt_utils_2512.py` the `magic_prompt` variable still exists but is **no longer appended** (function returns the polished prompt only). So: quality suffix helps on 2508, unnecessary on 2512+.
- Rendered text: enclose every string in **English double quotes**, never translate or alter it; give position, layout direction, font style, colour, size, medium (printed/neon/embroidered). If text is implied ("a list of names"), invent the exact concrete text. 2512 rewriter adds: if no text, end with "The image contains no recognizable text."; never modify proper nouns; no markdown lists/headings in output; state an explicit overall style; portraits must specify ethnicity, gender, narrow age, face, skin, makeup, clothing, hair, pose, gaze, hands, background, lighting. ZH rewriter: **no negation words** in the rewritten prompt ("不要有筷子" -> simply omit chopsticks); preserve logical relations (arrows for food chains); never add extra text.

Edit rules (official `polish_edit_prompt`): keep instruction direct and specific; add/delete/replace – supply category, colour, size, orientation, position if vague; "Replace Y with X" + key visual features of X; text edits are always replacements: `Replace "xx" to "yy"`, all text in English double quotes, keep original language and capitalisation; human edits – state what stays (ethnicity, gender, age, hairstyle, expression, outfit), expression/beauty changes "natural and subtle"; style – describe the style by key visual features, put the style clause at the end; fixed templates: `Restore and colorize the photo.`, `Perform inpainting on this image. The original caption is: `, `Extend the image beyond its boundaries using outpainting. The original caption is: `. README: editing "may become unstable if prompt rewriting is not used".

Multi-image (2509/2511): the pipeline itself prefixes `Picture 1: <image>Picture 2: <image>…`, so refer to inputs as **"Picture 1", "Picture 2"** (ZH "图1/图2"): "Replace the girl of picture 1 with the boy of picture 2, keeping picture 2's background unchanged". Qwen-Image-2.1 PE uses `<image1>` tokens.

Official rewriter system prompts:
- https://github.com/QwenLM/Qwen-Image/blob/main/src/examples/tools/prompt_utils.py (raw: https://raw.githubusercontent.com/QwenLM/Qwen-Image/main/src/examples/tools/prompt_utils.py) – `polish_prompt_en`, `polish_prompt_zh`, `polish_edit_prompt`
- https://raw.githubusercontent.com/QwenLM/Qwen-Image/main/src/examples/tools/prompt_utils_2512.py – 2512 EN/ZH rewriters (portrait / text-image / general sub-tasks)
- https://raw.githubusercontent.com/QwenLM/Qwen-Image-2.1/main/prompt_rewrite/pe_core.py – 2.1 rewriter harness; system prompts at https://huggingface.co/Qwen/Qwen-Image-2.1-PE-T2I and https://huggingface.co/Qwen/Qwen-Image-2.1-PE-I2I (`system_prompt.txt`, path inferred from code – unverified)
- Not found: `prompt_utils_2509.py` / `prompt_utils_2511.py` (404). The Edit-2509/2511 HF Spaces may carry a multi-image variant of the edit system prompt – not verified.

Sources:
- https://raw.githubusercontent.com/QwenLM/Qwen-Image/main/README.md — news (2.0, 2512, 2511, 2509), magic suffix, negatives, rewriting recommendation
- https://raw.githubusercontent.com/QwenLM/Qwen-Image-2.1/main/README.md — 2.1 architecture, encoder, PE models
- https://raw.githubusercontent.com/huggingface/diffusers/main/src/diffusers/pipelines/qwenimage/pipeline_qwenimage.py and `pipeline_qwenimage_edit_plus.py` — 1024-token cap, encoder templates, "Picture N" prefix

---

## 7. HunyuanImage 3.0 (and 2.1) — confidence: high

**HunyuanImage 3.0** (Tencent Hunyuan): 80B MoE (13B active) autoregressive unified multimodal model – the LLM itself is the "text encoder" (no CLIP/T5). Variants: base/pretrain (no self-rewrite), **Instruct** and **Instruct-Distil** (2026-01-26; CoT think + prompt self-rewrite + image-to-image; Distil = 8 steps).
- Modes (`--bot-task`): `image` (direct), `recaption` (rewrite -> image), `think_recaption` (think -> rewrite -> image; default on Instruct), `auto`. System prompt types (`--use-system-prompt`): `None, dynamic, en_vanilla, en_recaption, en_think_recaption, en_unified, custom`. `max_new_tokens` 2048.
- If the ComfyUI LLM already enhanced the prompt, use `bot_task=image` (or the base checkpoint) to avoid double rewriting. Base checkpoint: Tencent recommends an external rewrite (DeepSeek-v3.1 with the PE prompts below).
- Recommended structure (official PE, 5-part): 1 main subject & scene -> 2 image quality & style -> 3 composition & viewpoint -> 4 lighting & atmosphere -> 5 technical parameters (aperture, focal length, "8K resolution" allowed here). Subject and style first (highest weight); always name a light source; single line, no markdown; **<= 500 words**; stay faithful to subject, counts and text.
- Built-in `en_recaption` rules: absolute objectivity (no "beautiful", "sad"); physical/logical consistency; general -> specific, background -> foreground, use "foreground / mid-ground / left side of the frame"; present tense; precise quantities/sizes/colours; default to ultra-realistic photography if no style; UI/graphic text in double quotes `""`; typographic art: start the description with the text itself, front-on view; **mention the core style 3–5 times and end with a style-declaration sentence**; no "This image shows…"; output inside `<recaption>` tags.
- Think mode: `<think>` covers subject, composition, lighting, colour palette, style, then `<recaption>`.
- Negative prompt: no conventional negative prompt (AR + diffusion head; not documented). Quality tokens: tolerated in the "technical parameters" slot, but subjective adjectives are prohibited.
- Languages: Chinese and English; quoted text rendering.

**HunyuanImage 2.1**: 17B DiT, 2K native. Text encoders: MLLM (**Qwen2.5-VL**, diffusers `tokenizer_max_length = 1000`) + **ByT5** glyph encoder for quoted text (128). CFG 3.5 (3.25 distilled) – diffusers pipeline accepts a negative prompt, README does not use one. "By writing longer and more detailed prompts, the generated image will be significantly improved." Put text to render in double quotes (the reprompt code converts single quotes to double quotes so ByT5 picks them up). Reprompt structure: "overall – detail – conclusion" (总-分-总): main -> secondary, objective and neutral, spatial logic, **end with one sentence summarising the overall style/type**. PromptEnhancer-32B / 7B (CoT rewriter) recommended.

Official rewriter system prompts:
- https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanImage-3.0/main/PE/system_prompt.py — `system_prompt_universal`, `system_prompt_text_rendering` (DeepSeek rewriter)
- https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanImage-3.0/main/hunyuan_image_3/system_prompt.py — `t2i_system_prompt_en_vanilla`, `..._en_recaption`, `..._en_think_recaption`, `unified_system_prompt_en`
- https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanImage-2.1/main/hyimage/models/reprompt/reprompt.py — 2.1 reprompt `SYSTEM_PROMPT` (ZH + official EN translation)
- https://raw.githubusercontent.com/Hunyuan-PromptEnhancer/PromptEnhancer/main/inference/prompt_enhancer.py — PromptEnhancer inference (system prompt passed in; strips `<think>`)
- Prompt handbook (Tencent Docs, not read): https://docs.qq.com/doc/DUVVadmhCdG9qRXBU

Sources:
- https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanImage-3.0/main/README.md — variants, bot-task / system-prompt flags, DeepSeek PE recommendation
- https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanImage-3.0/main/run_image_gen.py — `--rewrite`, `--sys-deepseek-prompt universal|text_rendering`
- https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanImage-2.1/main/README.md — two encoders, ByT5, long prompts, guidance values, PromptEnhancer-32B
- https://raw.githubusercontent.com/huggingface/diffusers/main/src/diffusers/pipelines/hunyuan_image/pipeline_hunyuanimage.py — Qwen2.5-VL 1000 tokens + ByT5 128

---

## 8. ERNIE-Image / ERNIE-Image-Turbo (Baidu) — confidence: high (exists); prompting style medium

- Exists: `baidu/ERNIE-Image`, `baidu/ERNIE-Image-Turbo`, Apache-2.0, 8B single-stream DiT, ComfyUI-native.
- Text encoder: **Ministral-3 3B** (`Mistral3Model` in diffusers; ComfyUI file `ministral-3-3b.safetensors`). No explicit token cap in the pipeline (tokenizer truncation only) – *hard limit not documented*.
- Prompt Enhancer: a separate fine-tuned ~3B `Ministral3ForCausalLM` shipped in the model repo (`pe/`, `pe_tokenizer/`; ComfyUI `ernie-image-prompt-enhancer.safetensors`). **No published system prompt** – behaviour is trained in; input is a user message containing JSON `{"prompt": "...", "width": 1024, "height": 1024}` (optional system prompt arg defaults to None), temperature 0.6, top_p 0.95. `use_pe=True` by default in diffusers – **turn it off (`use_pe=False`) if your own LLM already expanded the prompt**.
- Official benchmarks show PE is a trade-off: w/ PE improves some scores but lowers others (e.g. GenEval overall 0.8856 w/o PE vs 0.8728 w/ PE), so a faithful detailed prompt without PE is fine.
- Style: long structured natural-language description, Chinese or English; strongest at dense text, posters, infographics, UI, comics, multi-panel layouts. Official showcase prompts are several hundred Chinese characters, describe layout region by region, and put rendered text in **single quotes '…'** (e.g. 标签页名称显示为 'Introduction to LLMs').
- Negative prompt: base = yes (CFG 4.0, 50 steps; `negative_prompt` default ""). Turbo = 8 steps, **CFG 1.0 -> negative ignored** (DMD + RL distilled).
- Quality tokens: not used in official examples; no evidence either way.
- Official prompting guide: **not found** (README + showcase only; gallery at https://ernieimageprompt.com/).

Sources:
- https://raw.githubusercontent.com/baidu/ERNIE-Image/main/README.md — model description, PE, steps/CFG table, PE deployment + JSON input, showcase prompts
- https://huggingface.co/baidu/ERNIE-Image — licence, resolutions, guidance 4.0
- https://docs.comfy.org/tutorials/image/ernie-image/ernie-image — encoder + PE file names
- https://raw.githubusercontent.com/huggingface/diffusers/main/src/diffusers/pipelines/ernie_image/pipeline_ernie_image.py — Mistral3 encoder, PE call format, negative prompt

---

## 9. Anima (CircleStone Labs + Comfy Org) — confidence: high (official model card via fetch summary)

- Exists: `circlestone-labs/Anima`; 2B, built on NVIDIA **Cosmos-Predict2-2B-Text2Image**; variants Anima-Base, Anima-Aesthetic, Anima-Turbo (Civitai lists "turbo-v1.1"). Trained on millions of anime images + ~800k non-anime art; knowledge cutoff Sept 2025; no synthetic data.
- Text encoder: **Qwen3-0.6B base** (`qwen_3_06b_base.safetensors`) plus a trained "LLM adapter" (card: don't train the adapter). Token limit: not stated.
- Format: **Danbooru tags, natural language, or any mix in any order.** Tags lowercase, **spaces not underscores** (score tags keep the underscore).
- Tag order: `[quality/meta/year/safety tags] [1girl/1boy/1other…] [character] [series] [artist] [general tags]`.
- Quality tags: human-score set `masterpiece, best quality, good quality, normal quality, low quality, worst quality`; aesthetic-model set `score_9 … score_1`; may be mixed or omitted. Here quality tags **help** (trained-in).
- Meta: `highres, absurdres, anime screenshot, official art`; time: `year 2025`, or `newest, recent, mid, early, old`. Safety: `safe, sensitive, nsfw, explicit`.
- **Artist syntax: prefix with `@`** – e.g. `@big chungus`; "You must put @ in front of the artist."
- Recommended positive prefix: `masterpiece, best quality, score_7, safe,` Recommended negative: `worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration`.
- Natural language: "more descriptive is better. Aim for at least 2 sentences"; name the character then describe appearance, especially with several characters.
- Negative prompt: yes – CFG 4–5, 30–50 steps (Base/Aesthetic). Turbo: CFG 1, 8–12 steps -> negative ignored.
- Weights: `(tag:weight)` works but needs larger values than SDXL, e.g. `(chibi:2)`.
- Limits: not for photorealism; text rendering weak ("generally do single words").
- Official rewriter system prompt: **not found**.

Sources:
- https://huggingface.co/circlestone-labs/Anima and https://huggingface.co/circlestone-labs/Anima/blob/main/README.md — everything above
- https://civitai.com/models/2458426/anima — turbo version listing (not read)

---

## 10. Ideogram 4 (open weights) — confidence: high

- Developer: Ideogram. Open weights `ideogram-ai/ideogram-4-nf4`, `ideogram-ai/ideogram-4-fp8` (9.3B single-stream DiT, Ideogram 4 Non-Commercial licence); repo `ideogram-oss/ideogram4`.
- Text encoder: **Qwen3-VL-8B-Instruct** (13 hidden layers concatenated). Token limit: not stated.
- Prompt format: **JSON only.** "Ideogram 4 is trained exclusively on structured JSON captions… Passing in plain-text prompts directly to the model will not work and will likely trigger a safety warning." Plain text must go through a magic prompt.
- Negative prompt: none – unconditional branch is zeroed text features (asymmetric CFG, guidance schedule from presets such as `V4_QUALITY_48`).
- Quality tokens: no place for them; aesthetics go in `style_description.aesthetics`.

Schema (key order is strict; `CaptionVerifier` warns on unknown / missing / out-of-order keys):
```
{
  "high_level_description": "1–2 sentence summary",            // optional, strongly recommended
  "style_description": {                                       // optional object
    "aesthetics": "...", "lighting": "...",
    "photo": "...", "medium": "photograph",                    // photo order: aesthetics, lighting, photo, medium, color_palette
    // non-photo order: aesthetics, lighting, medium, art_style, color_palette
    "color_palette": ["#RRGGBB", ...]                          // optional, last, up to 16
  },
  "compositional_deconstruction": {                            // REQUIRED
    "background": "...",                                       // required, before elements
    "elements": [
      {"type":"obj","bbox":[y_min,x_min,y_max,x_max],"desc":"...","color_palette":[...]},
      {"type":"text","bbox":[...],"text":"LITERAL TEXT\nLINE 2","desc":"font/placement","color_palette":[...]}
    ]
  }
}
```
- Exactly one of `photo` / `art_style`. `medium` values: `photograph`, `illustration`, `3d_render`, `painting`, `graphic_design`, … `bbox` optional, normalised 0–1000, **[y_min, x_min, y_max, x_max]**, origin top-left. Per-element palette up to 5. Hex must be **uppercase 6-digit `#RRGGBB`**. Serialise minified: `json.dumps(caption, separators=(",", ":"), ensure_ascii=False)` (no `\uXXXX` escapes).
- Open-source magic-prompt `v1.txt` contract differs slightly: emits `aspect_ratio` ("W:H", first key), `high_level_description` (<= 50 words, one sentence preferred, starts with the subject), `compositional_deconstruction`; element `desc` 30–60 words (60 hard cap); **one coherent subject = one element** (never split a person into parts); single quotes for text references inside prose fields, verbatim user text in the `text` field; single-line minified JSON, no fences. Tested by Ideogram with Claude Opus only; it is *not* the production magic prompt. The hosted `ideogram-4-v1` magic prompt is a free API with no published prompt.

Do: always include `compositional_deconstruction.background` + `elements`; keep key order; put every rendered string in its own `text` element; include background colour in the palette.
Don't: send plain text; lowercase/shorthand hex; split one subject into many elements; escape non-ASCII.

Official rewriter system prompt:
- https://raw.githubusercontent.com/ideogram-oss/ideogram4/main/src/ideogram4/magic_prompt_system_prompts/v1.txt (loader: `src/ideogram4/magic_prompt.py`)

Sources:
- https://raw.githubusercontent.com/ideogram-oss/ideogram4/main/docs/prompting.md — JSON-only, schema, key order, hex rules, magic prompt configs
- https://raw.githubusercontent.com/ideogram-oss/ideogram4/main/README.md — weights, licence, Qwen3-VL-8B encoder
- https://raw.githubusercontent.com/ideogram-oss/ideogram4/main/docs/pipeline.md — asymmetric CFG / zeroed unconditional
- https://huggingface.co/ideogram-ai/ideogram-4-nf4 — weights (not read)

---

## 11. Legacy sanity check

| Model | Developer | Encoder | Style | Length / hard limit | Negative | Quality tokens | Confidence |
|---|---|---|---|---|---|---|---|
| **NoobAI-XL** (eps 1.1 / v-pred) | Laxhar Lab | SDXL CLIP-L + OpenCLIP-bigG | Danbooru **+ e621** tags, native tag captions | 77-token CLIP chunks (UIs concatenate 75-token chunks) | Yes, CFG 5–6, 25–30 steps, Euler a | **Help** (trained) | high |
| **Illustrious XL** v0.1 -> v1.0/1.1/2.0 | OnomaAI Research | SDXL CLIPs | Danbooru tags; v1.0+ officially "combines natural language with concise Danbooru tags" (plain English, tags, or both); 1536 px native from v1.0 | 77-token chunks | Yes | Help (booru quality tags; card gives no official list) | medium |
| **Pony Diffusion V6 XL** | PurpleSmartAI (AstraliteHeart) | SDXL CLIPs | Tags + short NL; prefix `score_9, score_8_up, score_7_up, score_6_up, score_5_up, score_4_up`, plus `source_anime/pony/furry/cartoon`, `rating_safe/questionable/explicit`; clip-skip 2 | 77-token chunks | Yes | Only score_ tags; `masterpiece` does little | medium (from prior knowledge of the Civitai card; not re-read) |
| **Pony V7** | PurpleSmartAI | AuraFlow-based 7B; encoder = AuraFlow's Pile-T5-XL/UMT5 (card doesn't name it) | Template: `special tags, factual description of image, stylistic description of image, additional content tags`; trained on NL + tags, "describing the intended result using normal language works in most cases" | 256 tokens (AuraFlow pipeline default) | CFG-based; card silent | `score_X, style_cluster_x, source_X` are **weak/inconsistent** in V7 ("score_9 would not necessarily yield better results"); fix planned for 7.1 | high |
| **Kolors** | Kuaishou Kolors team | **ChatGLM3-6B** | Natural language, Chinese or English; Chinese text rendering | **256 tokens** hard (diffusers errors above 256) | Yes (SDXL-style CFG ~5) | Neutral | high (limit) / medium (style) |
| **PixArt-Sigma** | PixArt-alpha team (Huawei Noah's Ark et al.) | **T5-XXL** (Flan-T5) | Dense natural-language captions | **300 tokens** (Alpha was 120) | Yes (CFG ~4.5) | Neutral/unneeded | high (limit) |
| **AuraFlow** v0.1–0.3 | fal | Pile-T5-XL (`UMT5EncoderModel` class) | Long, natural, caption-like prose (trained on re-captioned long captions) | **256 tokens** | Yes (CFG ~3.5) | Unneeded | high (limit) / medium (style) |
| **SDXL base** | Stability AI | CLIP ViT-L + OpenCLIP bigG | Short phrases / comma keywords; modest NL | **77 tokens per chunk** (75 usable); A1111/ComfyUI concatenate chunks; keep key content in the first 75 | Yes, important | Mild help on base, strong on booru fine-tunes; `(word:1.2)` weights are a UI feature (A1111/ComfyUI), valid for all CLIP models | medium (well-established; not re-fetched) |
| **SD 1.5** | Runway / CompVis | CLIP ViT-L/14 | Comma keyword lists | 77-token chunks | Yes, essential | Help ("masterpiece, best quality" on anime merges; "8k, highly detailed" folklore elsewhere) | medium |

NoobAI specifics (official card): order `<1girl/1boy/1other/...>, <character>, <series>, <artists>, <special tags>, <general tags>, <other tags>`; quality tags by percentile – `masterpiece` (>95%), `best quality` (85–95), `good quality` (60–85), `normal quality` (30–60), `worst quality` (<=30); period tags `newest` (2021–24), `recent` (2018–20), `mid` (2014–17), `early` (2011–14), `old` (2005–10); prefix `masterpiece, best quality, newest, absurdres, highres, safe,`; negative `nsfw, worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands, mammal, anthro, furry, ambiguous form, feral, semi-anthro`. `very awa` aesthetic tag: widely cited for NoobAI but **not confirmed** in the fetched card text.

Pony V7 limits (official): weak text rendering; small details/faces degrade in some styles; 768–1536 px; >= 30 steps.

Sources:
- https://huggingface.co/Laxhar/noobai-XL-1.1/blob/main/README.md — NoobAI tag order, quality/period tags, prefixes, settings
- https://huggingface.co/OnomaAIResearch/Illustrious-XL-v1.0 — NL + tag support, 1536 native, v0.1 LoRA compatibility
- https://huggingface.co/purplesmartai/pony-v7-base — V7 template, NL+tags, weak special tags, limits
- https://purplesmart.ai/pony/content7x — V7 overview (no prompt rules)
- https://civitai.com/models/257749/pony-diffusion-v6-xl — V6 score-tag recommendation (not re-read)
- https://raw.githubusercontent.com/huggingface/diffusers/main/src/diffusers/pipelines/kolors/pipeline_kolors.py — ChatGLM, 256
- https://raw.githubusercontent.com/huggingface/diffusers/main/src/diffusers/pipelines/pixart_alpha/pipeline_pixart_sigma.py — T5, 300
- https://raw.githubusercontent.com/huggingface/diffusers/main/src/diffusers/pipelines/aura_flow/pipeline_aura_flow.py — UMT5 class, 256

---

## Cross-model cheat sheet for profile authors

| Model | Format | Target length | Neg? | Quote text | Quality boilerplate |
|---|---|---|---|---|---|
| FLUX.2 dev | prose or JSON | 30–80 w (<=512 tok) | no | "double" | no |
| FLUX.2 klein | prose | 40–70 w | no (distilled) | "double" | no |
| Kontext dev | edit instruction + keep-clause | 1–3 sentences (<=512 tok) | no | 'old' -> 'new' | no |
| Chroma HD | prose (+ optional tags) | 50–150 w (<=512 tok) | yes, long | n/a | `aesthetic N` (3rd-party) |
| Krea 2 Turbo | prose paragraph | 60–150 w (<=512 tok) | no (CFG 0) | "double" | no |
| Z-Image-Turbo | objective prose, EN/ZH | 80–250 w (512, up to 1024 tok) | no (CFG 0) | "double" | **forbidden by official PE** |
| Qwen-Image 2512 | prose, EN/ZH | ~200 w (<=1024 tok) | yes | "double" + position/font | suffix only for 2508 |
| Qwen-Image-Edit 2509/2511 | edit instruction, "Picture N" | 1–3 sentences | " " | "double" | no |
| HunyuanImage 3.0 | 5-part prose, single line | <=500 w | no | "double" | camera params ok; no subjective adjectives |
| HunyuanImage 2.1 | overall–detail–summary | long | optional | "double" (ByT5) | end with style sentence |
| ERNIE-Image | long structured prose, ZH/EN | hundreds of chars ok | base yes / Turbo no | 'single' in official examples | no |
| Anima | booru tags / NL / mix | tags + >=2 sentences | yes (not Turbo) | weak text | **yes** (`masterpiece, best quality, score_7, safe`) |
| Ideogram 4 | strict JSON | desc <=60 w per element | no | `text` element | no |
