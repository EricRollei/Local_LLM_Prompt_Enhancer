# Eric's Prompt Enhancers for ComfyUI

[![License](https://img.shields.io/badge/License-Dual%20(NC%2FCommercial)-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.2.0-green.svg)](CHANGELOG.md)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Compatible-orange.svg)](https://github.com/comfyanonymous/ComfyUI)

A comprehensive suite of **18 nodes** for ComfyUI using local LLMs (LM Studio or Ollama). Transform simple prompts into detailed, platform-optimized descriptions for video and image generation.

![Eric's Prompt Enhancers](https://img.shields.io/badge/Nodes-18-brightgreen) ![Platforms](https://img.shields.io/badge/Image%20Platforms-8-blue) ![Video Support](https://img.shields.io/badge/Video-✓-success)

---

## 📦 Quick Start

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/EricRollei/Local_LLM_Prompt_Enhancer.git video_prompter
cd video_prompter
pip install -r requirements.txt
```

Restart ComfyUI. All nodes will appear under: **Add Node → Eric Prompt Enhancers**

---

## 🆕 New in 2.0

Version 2.0 keeps every existing node and every saved workflow, and adds three things underneath them.
The documents linked here are current.

**A real wildcard engine.** The Dynamic Prompts / Impact Pack grammar (`__name__`, `{a|b|c}`, weights, ranges,
variables, tag queries such as `__objects[metal AND handheld]__`), read straight from `ComfyUI/models/wildcards`,
in every enhancer node. Picks are handed to the LLM as concepts to express, as exact strings that must survive
(`__=lora_triggers__`), or as loose inspiration (`__?moods__`). New nodes: **Wildcard Processor**,
**Semantic Variation** (moves picks to semantic neighbours, with named direction axes) and
**Concept Survival Check**. See [docs/WILDCARD_GUIDE.md](docs/WILDCARD_GUIDE.md).

**Platform profiles.** Everything the nodes know about a target model is one YAML file in `profiles/`:
format, length, negative prompt or none, quality tokens or none, how text and dialogue are written, and - where
the maker publishes one - the maker's own rewriter prompt, downloaded once and cached. Over 60 models, open and
hosted: FLUX.2, Krea 2, Z-Image, Qwen-Image, HunyuanImage 3, Ideogram 4, Illustrious, NoobAI; MiniMax H3, Wan 2.2,
LTX-2, HunyuanVideo 1.5; and for API use Seedream 5, Nano Banana, GPT Image, Midjourney V8, Seedance 2.5,
Kling 3, Veo 3.1, Wan 3.0 and others. Your own go in `profiles_user/`. The new **Platform Prompt Rewriter** node
writes for any of them, including the structured formats (MiniMax H3 fields, FLUX.2 and Ideogram JSON, edit
instructions). See [PLATFORM_NOTES.md](PLATFORM_NOTES.md).

**Prompts stay inside the text-encoder limit.** A text encoder silently drops whatever runs past its
limit (Krea 2: 512 tokens) - from the END, which is where LoRA trigger words usually go. The Platform
Prompt Rewriter now counts the answer the way the model will (the Qwen tokenizer for Qwen-encoder
models, from files already on disk; a conservative estimate otherwise) and aims below the limit with
headroom for triggers. `length_guard` (appended): `retry+trim` asks the LLM once for a tighter version,
then trims; `trim` trims only; `off` reports only. Trimming drops sentences just before the last one,
so the subject (first) and medium / style (last) survive, and verbatim wildcard picks are never cut.
The report shows `length: N/512 tokens`.

**Surreal as a procedure.** The `surreal` preset and genre now run an ordinary-scene inventory, generator,
critic and structured compiler grounded in how
Magritte, Ernst, Dali, Varo, Uelsmann, Atget and Man Ray actually worked: one anomaly stated as plain fact against
a credible world, chosen for affinity rather than distance. The compiler removes replaced objects before the
platform rewriter and requires visible physical proof of the anomaly. The **Surreal Premise** node shows every
candidate, the structured plan and the reasoning. See [docs/SURREAL_GUIDE.md](docs/SURREAL_GUIDE.md).

**The video nodes have a `target_model`.** The three video expanders were written around Wan 2.2. They now
write for any video profile, and the default is **MiniMax H3**. Choose `wan22_video` to get the original
behaviour exactly. Note for existing workflows: a workflow saved before 2.0 has no value for this new input, so
it loads with the default (MiniMax H3) - set it to `wan22_video` once and save.

---

## 🎯 The Nodes

All **18 nodes** live under the **"Eric Prompt Enhancers"** category in ComfyUI. The five LLM expanders come
first, then platform output, wildcards and variation, the prompt builders, and the prompt database.

### 1. 🎬 Video Prompt Expander

Simple video prompt expansion with style presets.

- **5 Expansion Tiers**: auto, basic, enhanced, advanced, cinematic (`auto` detects the right tier)
- **6 Style Presets**: Cinematic, Surreal, Action, Stylized, Noir, Random
- **Auto-Variation**: Generate up to 3 unique variations
- **Best for**: Quick video prompt expansion from short ideas

### 2. 🎬 Video Prompt Expander (Advanced) ⭐ NEW v1.8

Granular control over video aesthetics with **50+ detailed settings**.

**NEW in v1.8:**
- **4 Operation Modes**: 
  - `expand_from_idea` - Expand short concepts
  - `refine_existing` - Polish existing prompts
  - `modify_style` - Change aesthetic while keeping subject
  - `add_details` - Enrich existing prompts
- **Clear Detail Levels**: Concise, Moderate, Detailed, Exhaustive (with tooltips!)
- **Optional Image Input**: Analyze images with Qwen3-VL for image-to-video workflows
- **Auto Mode Detection**: Automatically switches to image-to-video when image provided

**Controls:**
- **Lighting**: Light source (10 options), Lighting type (13 options), Time of day (9 options)
- **Camera**: Shot size (10 options), Composition (8 options), Lens (6 options), Angle (10 options), Movement (17 options)
- **Visual**: Color tone (7 options), Visual style (15 options), Visual effects (11 options)
- **Character**: Emotion (13 options)

**Best for**: Professional video generation with precise aesthetic control

### 3. 🖼️➡️🎬 Image-to-Video Prompt Expander

Vision model analyzes images and adds motion descriptions for video generation.

- **Automatic Scene Understanding**: Qwen3-VL vision analysis
- **Motion Description Generation**: AI-generated movement and action
- **Style Integration**: Combines visual analysis with expansion tiers
- **Best for**: Converting static images into video prompts

### 4. 🖼️➡️🖼️ Image-to-Image Prompt Expander

Platform-aware image-to-image prompt generation.

- **6 Platforms**: Flux, SDXL, Wan 2.2, HunyuanImage, Qwen-Image, Qwen-Image-Edit
- **Transformation Controls**: Style transfer, detail level, creativity settings
- **Vision Analysis**: Understands source image characteristics
- **Best for**: Image transformation and editing workflows

### 5. 📝➡️🖼️ Text-to-Image Prompt Enhancer (v1.7)

Advanced multi-platform image prompt enhancement with extensive creative controls.

- **8 Platforms**: Flux, SDXL, Pony Diffusion, Illustrious XL, Chroma, Qwen Image, Qwen Edit, Wan Image
- **Reference Images**: Optional 1-2 image inputs with visual analysis
- **Genre Styles**: 22 styles (cinematic, horror, cyberpunk, steampunk, noir, fantasy, etc.)
- **Prompt Length**: 6 options (very_short to very_long, 20-400 tokens)
- **Subject Controls**: Framing (14 options), Pose (17 options)
- **Advanced Settings**: Camera angle, composition, lighting (source/quality), weather, time, color mood
- **Special Syntax**: Emphasis `(keyword:1.5)` and Alternation `{a|b|c}` support
- **Best for**: Professional image generation with platform-specific optimization

### 6. 🎞️ Alice T2V Prompt Refiner

Refines rough text and/or reference images into structured Alice text-to-video prompts.

- **Text-only or image-guided**: optional Qwen3-VL vision analysis of reference images
- **Best for**: Alice / text-to-video prompts from a loose idea

**— Platform output —**

### 7. ✍️ Platform Prompt Rewriter

Rewrites a finished prompt for any **platform profile** (60+ open and hosted models), in that model's exact format,
and keeps it inside the text encoder's token limit so trigger words aren't silently dropped.

- **60+ profiles**: FLUX.2, Krea 2, Qwen-Image, Ideogram 4, Illustrious, MiniMax H3, Wan 2.2, Veo 3.1, and more
  (`profiles/`; your own go in `profiles_user/`)
- **Structured formats**: MiniMax H3 fields, FLUX.2 / Ideogram JSON, edit instructions
- **`length_guard`**: counts tokens the way the model will and trims to fit, never cutting verbatim wildcard picks
- **Outputs**: prompt, negative_prompt, report, system_prompt

### 8. 🪄 Ideogram 4 Magic Prompt

Builds an Ideogram 4 "magic prompt" (structured JSON plus a high-level line) with a recommended canvas size.

- **Outputs**: prompt_json, high_level, width, height, report
- **Best for**: Ideogram 4 generation

**— Wildcards & variation —**

### 9. 🎲 Wildcard Processor

Resolves wildcards, variants, variables and tag queries in a prompt — the Dynamic Prompts / Impact Pack grammar
(`__name__`, `{a|b|c}`, weights, ranges, variables, `__objects[metal AND handheld]__`), read from `models/wildcards`.

### 10. 🔀 Semantic Variation

Varies a wildcard prompt by moving each random pick to a semantic neighbour, along named direction axes.

### 11. ✅ Concept Survival Check

Measures whether the key concepts (a surreal anomaly, exact LoRA triggers, ...) survived the LLM rewrite.

- **Outputs**: report, all_survived, missing, carried_by_json

### 12. 🌀 Surreal Premise

Turns an ordinary scene into **one anomaly stated as plain physical fact**, with an instruction block that protects
it through the rewrite, a Magritte-style title and counter-terms. Eight generator modes feed one critic.

- Its `llm_instructions` plug into any enhancer's `wildcard_instructions`
- See [docs/SURREAL_GUIDE.md](docs/SURREAL_GUIDE.md)

**— Prompt builders (click, don't type) —**

### 13. 🧩 Wildcard Prompt Composer

Builds a whole prompt section by section with clickable pills instead of typed wildcard syntax. Holds every section
(Format, Subject, Action, Setting, Light & atmosphere, Composition, Camera, Style & finish, plus optional Text) in
the order the chosen platform wants. Lock a section to hold it while the seed re-rolls, drag to reorder, save as a
template.

### 14. 👤 Wildcard Character Composer

The same node limited to the Subject section, for a character you reuse across several prompts or branches.

- See [docs/PROMPT_BUILDER_GUIDE.md](docs/PROMPT_BUILDER_GUIDE.md)

**— Prompt database —**

### 15. 💾 Save Prompt to DB

Saves a prompt (and optional negative) to the local SQLite database, passing the prompt through unchanged so the node
can sit inline before a sampler.

### 16. 🔎 Search Prompt DB

Searches the database by keyword, category, platform, rating, tags or favourites, and returns the top match.

### 17. 📥 Import Prompts to DB

Bulk-imports prompts from external files (`.txt`, `.csv`, and more) into the local database.

### 18. 🎰 Browse / Random Prompt DB

Fetches a specific prompt by ID, or a random/filtered prompt by seed.

---

## ✨ Key Features

### 🤖 Local LLM Support

- **LM Studio**: OpenAI-compatible API (recommended)
- **Ollama**: Simple CLI-based LLM server
- **Qwen3-VL (Optional)**: Local vision model for image analysis
- **Privacy**: All processing happens locally, no data sent to cloud

### 🎨 Platform-Specific Optimization

Each platform has unique requirements and prompting styles:

| Platform | Style | Optimal Length | Specialization |
|----------|-------|----------------|----------------|
| **Flux** | Natural language | 75-150 tokens | Photography, artistic |
| **SDXL** | Natural/tags hybrid | 40-75 tokens | Versatile, balanced |
| **Pony Diffusion** | Booru tags | Tag count | Anime, characters |
| **Illustrious XL** | Danbooru tags | Tag count | Detailed anime |
| **Chroma/Meissonic** | Detailed natural | 100-200 tokens | Complex scenes |
| **Qwen Image** | Technical descriptions | Medium | General purpose |
| **Qwen Edit** | Edit instructions | Medium | Image editing |
| **Wan Image** | Cinematography | 60-120 tokens | Professional video stills |

### 🔧 Special Syntax (NEW v1.6.1)

**Emphasis (Weight Control)**
```
(keyword:1.5)    # Increase importance 1.5x
(keyword:0.5)    # Decrease importance 0.5x
(red hair:2.0)   # Double the weight
```

**Alternation (Random Selection)**
```
{cat|dog|rabbit}                    # Picks one randomly
{red|blue|green} dress              # Random color
{elegant|casual} woman with (detailed face:1.5)
```

**Combined**
```
A {tall|short} woman with (dark hair:1.4) wearing a {red|blue|green} (dress:1.2)
```

### 🎯 Intelligent Features

- **Auto-Detection**: Analyzes input complexity and selects optimal detail level (Video nodes)
- **Multiple Variations**: Generate up to 3 unique variations in one run
- **Keyword Integration**: Automatically include LoRA triggers and custom terms
- **Smart Negatives**: Platform-optimized negative prompts
- **File Export**: Save prompts with complete metadata
- **Wildcard Support**: Random element selection for variety

---

## 🚀 Installation

### Prerequisites

- **ComfyUI**: Installed and working
- **Python 3.8+**: Usually included with ComfyUI
- **LLM Backend**: LM Studio or Ollama (see setup below)

### Step 1: Install the Node

**Method 1: Git Clone (Recommended)**

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/EricRollei/Local_LLM_Prompt_Enhancer.git video_prompter
cd video_prompter
pip install -r requirements.txt
```

**Method 2: Manual Install**

1. Download this repository as ZIP
2. Extract to `ComfyUI/custom_nodes/video_prompter/`
3. Install dependencies:
   ```bash
   cd ComfyUI/custom_nodes/video_prompter/
   pip install -r requirements.txt
   ```

### Step 2: Setup LLM Backend

Choose **one** of these options:

**Option 1: LM Studio (Recommended)**

1. Download from: https://lmstudio.ai/
2. Load a model (recommended: Llama 3 8B or similar)
3. Start the server (Settings → Server → Start Server)
4. Default endpoint: `http://localhost:1234/v1`

**Option 2: Ollama**

1. Install from: https://ollama.ai/
2. Pull a model: `ollama pull llama3`
3. Server runs automatically at: `http://localhost:11434`

### Step 3: Restart ComfyUI

All nodes will appear under: **Add Node → Eric Prompt Enhancers**

### Optional: Qwen3-VL Vision Model

For image analysis in Image-to-Video and Image-to-Image nodes:

```bash
pip install transformers>=4.42.0 accelerate>=0.30.0 huggingface_hub>=0.23.0 bitsandbytes>=0.43.0
```

See [VISION_BACKEND_GUIDE.md](VISION_BACKEND_GUIDE.md) for details.

---

## 📖 Usage Guide

### Basic Workflow (Video Prompt Expander)

1. **Add Node**: Right-click → Eric Prompt Enhancers → Video Prompt Expander
2. **Enter Prompt**: "A cat playing piano in a cozy room"
3. **Select Preset**: Choose "cinematic" for film-like quality
4. **Choose Detail Level**: "detailed" for ~400-500 words
5. **Configure LLM**:
   - Backend: `lm_studio`
   - Model: `llama3`
   - Endpoint: `http://localhost:1234/v1`
6. **Generate**: Run the workflow
7. **Use Output**: Connect `positive_prompt_1` to your video generator

### Advanced Workflow (Advanced Node)

1. **Add Node**: Video Prompt Expander (Advanced)
2. **Choose Operation Mode**:
   - `expand_from_idea`: For short concepts
   - `refine_existing`: For polishing existing prompts
   - `modify_style`: To change aesthetic
   - `add_details`: To enrich prompts
3. **Select Detail Level**: Choose based on desired output length
4. **Set Aesthetic Controls**: Configure camera, lighting, style, etc.
5. **Optional**: Add reference image for image-to-video mode
6. **Generate**: Prompts incorporate your specific controls

### Image-to-Video Workflow

1. **Add Node**: Image-to-Video Prompt Expander (or Advanced with image)
2. **Connect Image**: Link your image to the `reference_image` input
3. **Add Direction**: "Camera slowly zooms in on the subject"
4. **Generate**: Vision model analyzes image and incorporates it into prompt

### Text-to-Image Workflow

1. **Add Node**: Text-to-Image Prompt Enhancer
2. **Select Platform**: Choose your target platform (Flux, SDXL, etc.)
3. **Set Length**: Choose prompt length (medium recommended)
4. **Configure Controls**: Set genre, framing, lighting, etc.
5. **Use Syntax**: Add emphasis `(keyword:1.5)` and alternations `{a|b}`
6. **Generate**: Get platform-optimized prompts

---

## 📝 Detail Levels Explained

### Concise (~150-200 words)
- Essential details only
- Clear subject, basic setting, simple action
- **Use when**: You want compact prompts or API token savings

### Moderate (~250-350 words)
- Good balance of detail
- Subject characteristics, environment description, basic aesthetics
- **Use when**: Standard detailed descriptions needed

### Detailed (~400-500 words) - **DEFAULT**
- Rich, comprehensive description
- Full cinematography, specific lighting, camera work
- **Use when**: Professional video generation

### Exhaustive (~600-1000 words)
- Maximum detail for cinematic quality
- Director-level descriptions, complete technical details
- **Use when**: Masterful, film-quality output required

---

## 🎨 Style Presets

### Cinematic
Professional film quality with emphasis on lighting, composition, and smooth camera movements.
- Edge lighting, soft lighting, warm colors
- Professional framing, balanced composition

### Surreal
Dreamlike, unusual scenes with artistic emphasis.
- Unexpected combinations, creative camera angles
- Artistic lighting, ethereal atmosphere

### Action
High-energy motion and dynamic camera work.
- Fast movement, intense action
- Dynamic angles, motion blur

### Stylized
Artistic interpretation with strong visual identity.
- Bold choices, distinctive look
- Creative freedom, unique aesthetics

### Noir
Dark, moody film noir aesthetic.
- High contrast, dramatic shadows
- Low-key lighting, mystery atmosphere

### Random
AI selects random aesthetic elements while respecting your core concept.
- Variety for batch generation
- Creative combinations

---

## 🔧 Configuration

### Common Settings

**LLM Configuration**
- `llm_backend`: `lm_studio` or `ollama`
- `model_name`: Your loaded model (e.g., "llama3")
- `api_endpoint`: LLM server URL
- `temperature`: 0.1-2.0 (0.7 recommended, lower = focused, higher = creative)

**Keywords**
- `positive_keywords`: Comma-separated must-include terms (LoRA triggers, style terms)
- `negative_keywords`: Comma-separated terms to avoid

**Output**
- `num_variations`: Generate 1-3 variations
- `save_to_file`: Save prompts to disk with metadata
- `filename_base`: Base name for saved files

### Node Outputs

All nodes return:
1. **positive_prompt_1/2/3**: Enhanced prompt variations
2. **negative_prompt**: Auto-generated platform-specific negatives
3. **breakdown/settings_used**: Detailed analysis of what was applied
4. **status**: Success messages, errors, file save location

---

## 🗂️ Maintaining Your Wildcard and LoRA Libraries

The Wildcard Composer and the LoRA Suggester are only as good as the lists and LoRA cards behind them. This is
how to add to both, clean them up and keep their indexes current.

### Wildcards

**Where they live.** Any wildcard folder ComfyUI knows (`ComfyUI/models/wildcards`, plus extra model paths such as
`A:\Models\wildcards`). A few top-level folders are special:

| Folder | What it is |
|---|---|
| `_nsfw/` | NSFW lists, used only at the matching NSFW level (`_nsfw/suggestive/`, `_nsfw/nudity/` rate lower) |
| `_prompts/` | whole prompts, one per line: reached only through the Composer's **Prompt** line or `__prompts/<pack>/...__` |
| `_generated/` | lists the tools write |
| `_dumped/` | lists you dumped in the review; the engine skips it |
| `mine/` | your own lists: merges, lists made with the LLM |

Your choices (stars, hidden lists, dropped lines, NSFW ratings, renames, button assignments) are kept in
`_catalog_user.yaml` in the wildcard folder. The pack files themselves are never edited.

**Adding lists.** Copy the files in; nothing else is needed to *use* them. ComfyUI rescans the wildcard folders every
10 seconds, so a new list works in `__name__` references and the Composer at once. The catalog behind Find, More
lists and button ranking catches up by itself in the background each time ComfyUI starts: restart ComfyUI to refresh it.

**Reviewing and cleaning: the wildcard review tool.** Run `tools\wildcard_review\wildcard_review.bat` and open
http://127.0.0.1:8766. (Close an old review window first: a server still running holds the port, and you would
see the old version.) Per list you can:

- **Keep / Dump / Same as / Merge** (keys K / D / S / M; **A** takes the AI judge's call). Dump hides a list and
  never deletes it.
- **Rename** a list you keep, so it is easy to find in pills and pages. Its old name keeps working, so saved workflows
  are safe.
- **Put it on Composer buttons**, any number of them. **+ new button** makes one of your own, under the heading you
  pick (Setting › Place, Subject › Clothing ...).
- **Merge** it with similar lists. A preview shows every combined line and which lists have it; untick any to leave
  them out. The result is written to `mine/`.
- **Drop bad lines.** Click a line and it is never picked again; this is saved at once. **Drop matching** drops every
  line with a word or regex. **Suggest junk** asks the local LLM which lines don't belong, and you confirm.
- **Make new lists** with the local LLM (LM Studio): **+ New list...** from a description and a few samples, or
  **Extend...** to grow a short list. You check every line before it is saved to `mine/`.

**Apply** writes your decisions and does the renames and merges, showing a preview first. **Move dumped files**,
in the same window, moves dumped files to `_dumped/`. Every rename, merge, move and new list writes a manifest; to undo
one, run:

    python tools\wildcard_review\server.py --undo tools\wildcard_review\manifests\<file>.json

The review tool reads the folder set in `LIBRARY_ROOT` at the top of `tools/wildcard_review/server.py` (default
`A:\Models\wildcards`; the `WCR_ROOT` environment variable overrides it). The LLM features use LM Studio at
`http://localhost:1234`; choose the model in the page's header menu.

**Getting new lists into the review.** The review shows lists the triage and the AI judge have seen. After adding
packs, restart ComfyUI (so the catalog is current), then from this folder run the commands below. The judge needs
LM Studio and only judges lists it has not seen.

    ..\..\..\python_embeded\python.exe -X utf8 dev\wildcard_triage.py
    ..\..\..\python_embeded\python.exe -X utf8 dev\wildcard_judge.py --all

Note: check how a fresh triage run treats lists you have since renamed, merged or moved to `_dumped/` before
re-running it on a reviewed library.

See [docs/WILDCARD_GUIDE.md](docs/WILDCARD_GUIDE.md) for the syntax and the folder rules, and
[docs/PROMPT_BUILDER_GUIDE.md](docs/PROMPT_BUILDER_GUIDE.md) for the Composer.

### LoRAs (the LoRA Catalog)

The LoRA Suggester reads a catalog of LoRA "cards": what each LoRA does, its style and subject words. They are
built by the companion LoRA Catalog tool, kept in its own folder (`A:\LoRA_Catalog` here). The path to its database
is the `lora_suggest` section of `config.json` (default `L:\Models\loras\_lora_catalog.sqlite`).

**After adding LoRAs**, run `refresh_new_loras.bat` in the LoRA Catalog folder, with LM Studio running. Every step
skips work already done, so it is safe to run any time. It writes `refresh_new_loras.log`.

| Step | Command | What it does |
|---|---|---|
| 1 | `run.py index` | reads new or changed LoRA files (headers, sidecars, LoRA Manager data) |
| 2 | `run.py crawl` | fetches Civitai records for LoRAs that have none yet (internet; the run carries on if it fails) |
| 3 | `run.py creators` | looks up who made each LoRA (internet; the run carries on if it fails) |
| 4 | `run.py cards --workers 3` | the local LLM writes a card for every LoRA without one |
| 5 | `run.py review-all` | rebuilds the HTML review pages |
| 6 | `run.py facets` | rebuilds `card_facets`, the table the LoRA Suggester reads |

`refresh_new_loras.bat some/model-id` writes the new cards with another LM Studio model. To redo cards that already
exist, run step 4 by hand with `--force` (add `--only Krea2/graphic-art` to limit it to one folder), then step 6.
Never run `facets` while a cards run is still writing.

**Checking and correcting cards: the card editor.** Run `card_editor.bat` in the LoRA Catalog folder and open
http://127.0.0.1:8765. Your edits are kept apart from the generated cards and win over them. Reload the page to see
newly written cards; after editing, run `run.py facets` so the Suggester sees your changes. The pick-list words live
in `vocab.yaml` in the same folder.

## 📚 Documentation

### Quick References
- [QUICKSTART.md](docs/QUICKSTART.md) - Get started in 5 minutes
- [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - Fast reference guide
- [QUICK_REF_V17.md](docs/QUICK_REF_V17.md) - Text-to-Image quick reference

### Node Guides
- [TXT2IMG_GUIDE.md](docs/TXT2IMG_GUIDE.md) - Text-to-Image node complete guide
- [IMG2IMG_GUIDE.md](docs/IMG2IMG_GUIDE.md) - Image-to-Image workflows
- [PROMPT_BUILDER_GUIDE.md](docs/PROMPT_BUILDER_GUIDE.md) - Wildcard Prompt / Character Composer panel
- [SURREAL_GUIDE.md](docs/SURREAL_GUIDE.md) - Surreal Premise node and the surreal engine
- [WILDCARD_GUIDE.md](docs/WILDCARD_GUIDE.md) - Wildcard syntax, folders and the review tool
- [NODE_COMPARISON.md](docs/NODE_COMPARISON.md) - Which node to use when

### Setup Guides
- [LM_STUDIO_SETUP.md](docs/LM_STUDIO_SETUP.md) - LM Studio configuration
- [VISION_BACKEND_GUIDE.md](VISION_BACKEND_GUIDE.md) - Qwen3-VL setup for image analysis
- [CONFIGURATION.md](docs/CONFIGURATION.md) - Advanced configuration options

### Platform & Technical
- [PLATFORM_NOTES.md](PLATFORM_NOTES.md) - Platform profiles and structured formats
- [WAN_GUIDE_REFERENCE.md](docs/WAN_GUIDE_REFERENCE.md) - Wan 2.2 video prompt guide

### Updates & Fixes
- [CHANGELOG.md](CHANGELOG.md) - Complete version history

---

## 🆕 What's New in v2.2.0

### Wildcard Prompt Composer — build a prompt section by section, with buttons

Two new builder nodes write a prompt one section at a time, with clickable pills instead of typed wildcard syntax:

- **Wildcard Prompt Composer** holds every section in one node — Format, Subject, Action, Setting, Light &
  atmosphere, Composition, Camera and Style & finish (plus optional Text) — shown in the order the chosen platform
  wants (Krea 2, FLUX.2, ...). Each `[Pill]` is a wildcard; the words around them are yours. Lock a section to hold
  it while the seed re-rolls, drag sections to reorder, and save the result as a template.
- **Wildcard Character Composer** is the same node limited to the Subject section, for a character you reuse across
  several prompts or branches.

See [docs/PROMPT_BUILDER_GUIDE.md](docs/PROMPT_BUILDER_GUIDE.md) for the full panel reference.

### Wildcard review tool — curate your library in the browser

A local browser tool for cleaning up and organising your wildcard lists. Run
`tools\wildcard_review\wildcard_review.bat` and open http://127.0.0.1:8766. Working one list at a time, you can:

- **Keep or rename** a list; the old name keeps working through aliases, so saved workflows and templates don't break.
- **Put it on Composer buttons** (any number), or make your own button under the heading you pick.
- **Merge** similar lists, with a preview of every combined line so you can untick ones to leave out.
- **Drop bad lines** — one click removes a line from future picks; "Drop matching" clears a pattern across lists.
- **Extend** a short list with the local LLM, checking every line before it's saved.

**Apply** writes your decisions (renames, merges, moves) after showing a preview, and **every change writes a manifest
you can undo**. The tool reads the folder set in `LIBRARY_ROOT` at the top of `tools/wildcard_review/server.py`
(default `A:\Models\wildcards`); LLM features use LM Studio at `http://localhost:1234`.

See the **Wildcards → Reviewing and cleaning** section below and
[docs/WILDCARD_GUIDE.md](docs/WILDCARD_GUIDE.md) for full details.

---

## 🆕 What's New in v1.8.0

### Advanced Prompt Expander Node - Complete Redesign

**3 Major Usability Improvements:**

1. **Operation Modes** - Now you can modify existing prompts!
   - `expand_from_idea` - Original expansion behavior
   - `refine_existing` - Polish and improve prompts
   - `modify_style` - Change aesthetic while keeping subject
   - `add_details` - Add descriptive richness

2. **Clear Detail Levels** - No more confusing tiers!
   - Renamed to: Concise, Moderate, Detailed, Exhaustive
   - Added tooltips explaining each option
   - Removed confusing "auto" mode

3. **Image Input Support** - Image-to-video actually works!
   - Optional `reference_image` input
   - Qwen3-VL vision analysis integration
   - Automatic mode detection (text vs image-to-video)
   - Status shows when image is being used

**Bonus:** All video nodes now support emphasis `(keyword:1.5)` and alternation `{a|b|c}` syntax!

---

## 💡 Tips & Best Practices

### For Best Results

1. **Start Simple**: Begin with basic prompts, let the LLM expand
2. **Use Presets**: They provide consistent, proven aesthetic directions
3. **Experiment with Temperature**: 0.7 is balanced, 0.3-0.5 for consistency, 0.8-1.2 for variety
4. **Leverage Keywords**: Add LoRA triggers and style terms to positive_keywords
5. **Save Your Prompts**: Enable save_to_file to build a library
6. **Use Variations**: Generate 3 variations to pick the best
7. **Platform Matters**: Choose the right platform for your model

### Common Workflows

**Quick Video Prompt**
```
Node: Video Prompt Expander
Input: "cyberpunk street scene"
Preset: stylized
Detail: moderate
```

**Professional Image Generation**
```
Node: Text-to-Image Enhancer
Platform: Flux
Input: "portrait of a (warrior:1.3) with {red|blue|purple} armor"
Length: long
Genre: fantasy
```

**Refine Existing Prompt**
```
Node: Video Prompt Expander (Advanced)
Operation: refine_existing
Input: [Your existing 300-word prompt]
Detail: detailed
```

**Image-to-Video with Direction**
```
Node: Video Prompt Expander (Advanced)
Reference Image: [Your image]
Input: "Camera slowly dollies in while subject looks up"
Operation: expand_from_idea
```

---

## 🐛 Troubleshooting

### LLM Connection Failed

- Check LLM backend is running (LM Studio or Ollama)
- Verify endpoint URL matches your LLM server
- Test in browser: http://localhost:1234/v1 (LM Studio) or http://localhost:11434 (Ollama)

### Empty Output

- Check temperature isn't too high (>1.5)
- Verify model is loaded in LLM backend
- Check ComfyUI console for error messages

### Emphasis Syntax Not Working

- Make sure you're using parentheses with colon: `(keyword:1.5)`
- Syntax is preserved in v1.6.1+ for video nodes, v1.7+ for image nodes

### Image Analysis Not Working

- Install vision dependencies: `pip install transformers accelerate huggingface_hub bitsandbytes`
- Check Qwen3-VL model is downloaded
- See [VISION_BACKEND_GUIDE.md](VISION_BACKEND_GUIDE.md)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

Dual License:
- **Non-Commercial**: Free for personal/research use
- **Commercial**: Contact for licensing

See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- ComfyUI community for the amazing platform
- LM Studio and Ollama teams for excellent LLM backends
- Qwen3-VL team for the vision model
- All users who provided feedback and bug reports

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/EricRollei/Local_LLM_Prompt_Enhancer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/EricRollei/Local_LLM_Prompt_Enhancer/discussions)

---

**Version**: 2.1.0  
**Last Updated**: September 21, 2026  
**Author**: Eric Rollei  
**Repository**: https://github.com/EricRollei/Local_LLM_Prompt_Enhancer
