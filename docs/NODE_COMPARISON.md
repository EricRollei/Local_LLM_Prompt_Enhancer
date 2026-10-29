# Node Comparison Guide - Which Node Should I Use?

All 18 nodes live under **Add Node → Eric Prompt Enhancers**. This guide groups them by job and
helps you pick. For full per-node descriptions see README.md → "The Nodes".

## Quick Decision Tree

```
What do you want to do?

├─ Expand a short idea into a full prompt (with an LLM)
│   │
│   ├─ For VIDEO, from TEXT
│   │   ├─ Simple, preset-driven      → Video Prompt Expander
│   │   └─ Precise camera/lighting     → Video Prompt Expander (Advanced)
│   │
│   ├─ For VIDEO, from an IMAGE        → Image-to-Video Prompt Expander
│   │
│   ├─ For an IMAGE, from an IMAGE     → Image-to-Image Prompt Expander
│   │
│   ├─ For an IMAGE, from TEXT         → Text-to-Image Prompt Enhancer
│   │
│   └─ For Alice text-to-video         → Alice T2V Prompt Refiner
│
├─ Take a FINISHED prompt and format it for a specific model
│   ├─ Any of 60+ platform profiles    → Platform Prompt Rewriter
│   └─ Ideogram 4 (structured JSON)     → Ideogram 4 Magic Prompt
│
├─ Work with WILDCARDS / add variation
│   ├─ Resolve wildcard syntax          → Wildcard Processor
│   ├─ Nudge picks to neighbours        → Semantic Variation
│   ├─ Did the key idea survive?        → Concept Survival Check
│   └─ One surreal anomaly              → Surreal Premise
│
├─ BUILD a prompt with buttons (no typed syntax)
│   ├─ Whole prompt, section by section → Wildcard Prompt Composer
│   └─ A reusable character             → Wildcard Character Composer
│
└─ Keep a LIBRARY of prompts
    ├─ Save one                          → Save Prompt to DB
    ├─ Find one                          → Search Prompt DB
    ├─ Bulk-import many                  → Import Prompts to DB
    └─ Fetch one / random                → Browse / Random Prompt DB
```

---

## 1. LLM expanders & enhancers

These turn a short idea (and optionally a reference image) into a full prompt with a local LLM.

| Node | Input | Output | Vision | Platform-aware |
|------|-------|--------|--------|----------------|
| **Video Prompt Expander** | Text | Video prompt | ❌ | video `target_model` |
| **Video Prompt Expander (Advanced)** | Text (+ optional image) | Video prompt | ✅ (optional) | video `target_model` |
| **Image-to-Video Prompt Expander** | Image + motion | Video prompt | ✅ | video `target_model` |
| **Image-to-Image Prompt Expander** | Image + changes | Image prompt | ✅ | ✅ 6 platforms |
| **Text-to-Image Prompt Enhancer** | Text (+ 1-2 ref images) | Image prompt | ✅ (optional) | ✅ 8 platforms |
| **Alice T2V Prompt Refiner** | Text and/or images | Alice T2V prompt | ✅ (optional) | Alice |

### Video Prompt Expander
Simple, fast video prompts. Style presets, five `expansion_tier` levels (auto/basic/enhanced/advanced/
cinematic), up to 3 variations. **Use when** you want a quick video prompt from a short idea.

### Video Prompt Expander (Advanced)
Granular video control: operation modes (`expand_from_idea`, `refine_existing`, `modify_style`,
`add_details`), Concise/Moderate/Detailed/Exhaustive detail, 50+ camera/lighting/visual dropdowns, and an
optional reference image (Qwen3-VL). **Use when** you need specific cinematography or want to refine an
existing prompt.

### Image-to-Video Prompt Expander
A vision model describes your image, then motion and camera are added. **Use when** you're animating an
existing image.

### Image-to-Image Prompt Expander
Platform-aware image-to-image prompts (6 platforms: flux, sd_xl, wan22, hunyuan_image, qwen_image,
qwen_image_edit) with vision analysis of the source. **Use when** you're transforming or editing an image.

### Text-to-Image Prompt Enhancer
Multi-platform image prompts (8 platforms incl. Flux, SDXL, Pony, Illustrious, Chroma, Qwen Image/Edit, Wan
Image), 22 genre styles, optional reference images, emphasis `(keyword:1.5)` and alternation `{a|b|c}`.
**Use when** you're generating a still image from text.

### Alice T2V Prompt Refiner
Refines rough text and/or reference images into structured Alice text-to-video prompts. **Use when** you're
targeting Alice.

---

## 2. Platform output

Format an already-written prompt for a specific model.

### Platform Prompt Rewriter
Rewrites a finished prompt for any of 60+ platform profiles, in that model's exact format (including
structured ones: MiniMax H3 fields, FLUX.2 / Ideogram JSON, edit instructions), and keeps it inside the
text encoder's token limit so trigger words aren't dropped. **Use when** you already have a prompt and want
it tuned for a particular model. Outputs: prompt, negative_prompt, report, system_prompt.

### Ideogram 4 Magic Prompt
Builds an Ideogram 4 "magic prompt" (structured JSON + high-level line) with a recommended canvas size.
**Use when** you're generating with Ideogram 4.

---

## 3. Wildcards & variation

### Wildcard Processor
Resolves wildcard syntax (`__name__`, `{a|b|c}`, weights, ranges, variables, `__objects[metal AND handheld]__`)
read from `models/wildcards`. **Use when** you want wildcard expansion without an LLM.

### Semantic Variation
Moves each random wildcard pick to a semantic neighbour, along named direction axes. **Use when** you want
controlled variety across runs.

### Concept Survival Check
Measures whether the key concepts (a surreal anomaly, exact LoRA triggers, ...) survived the LLM rewrite.
**Use when** you need to confirm something important wasn't paraphrased away. Outputs: report, all_survived,
missing, carried_by_json.

### Surreal Premise
Turns an ordinary scene into one anomaly stated as plain physical fact, with an instruction block that
protects it through the rewrite. Its `llm_instructions` plug into any enhancer's `wildcard_instructions`.
**Use when** you want a grounded surreal premise. See SURREAL_GUIDE.md.

---

## 4. Prompt builders (click, don't type)

### Wildcard Prompt Composer
Builds a whole prompt section by section with clickable pills instead of typed wildcard syntax, in the
chosen platform's section order. Lock a section to hold it while re-rolling, drag to reorder, save as a
template. **Use when** you want to assemble a prompt visually. See PROMPT_BUILDER_GUIDE.md.

### Wildcard Character Composer
The same node limited to the Subject section, for a character you reuse across prompts or branches.

---

## 5. Prompt database

| Node | Does |
|------|------|
| **Save Prompt to DB** | Saves a prompt (+ optional negative) to the local SQLite DB; passes the prompt through unchanged |
| **Search Prompt DB** | Finds the top match by keyword, category, platform, rating, tags or favourites |
| **Import Prompts to DB** | Bulk-imports prompts from `.txt` / `.csv` / other files |
| **Browse / Random Prompt DB** | Fetches a prompt by ID, or a random/filtered one by seed |

**Use when** you want to build and reuse a personal library of prompts.

---

## Feature availability (expanders)

| | Standard | Advanced | Img2Vid | Img2Img | Txt2Img |
|---|---|---|---|---|---|
| **Presets** | ✅ | ✅ | ✅ | ❌ (platforms) | ❌ (genres) |
| **Wildcards** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Vision model** | ❌ | optional | ✅ | ✅ | optional |
| **Platform optimization** | video target | video target | video target | ✅ 6 | ✅ 8 |
| **Random mode** | ✅ | ✅ (respects controls) | ✅ | ❌ | ✅ |

---

## Common questions

**Q: Quick video prompt?** Video Prompt Expander. **Precise?** Advanced. **From an image?** Image-to-Video.

**Q: I already have a prompt — how do I format it for my model?** Platform Prompt Rewriter (60+ profiles).

**Q: Which nodes support wildcards?** All the expanders, plus the dedicated Wildcard Processor and the
Composer builders.

**Q: Which use a vision model?** Image-to-Video and Image-to-Image always; Advanced and Text-to-Image
optionally.

**Q: How do I build a prompt without typing wildcard syntax?** Wildcard Prompt Composer (whole prompt) or
Wildcard Character Composer (one character).

**Q: Where do I keep prompts I like?** The four Prompt Database nodes.

---

**Pick the right tool for your workflow — the nodes are designed to chain together.**
