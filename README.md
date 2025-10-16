# Eric's Prompt Enhancers for ComfyUI# Eric's Prompt Enhancers for ComfyUI



[![License](https://img.shields.io/badge/License-Dual%20(NC%2FCommercial)-blue.svg)](LICENSE)A comprehensive suite of AI-powered prompt enhancement nodes for ComfyUI using local LLMs (LM Studio or Ollama). Transform simple prompts into detailed, platform-optimized descriptions for video and image generation.

[![Version](https://img.shields.io/badge/version-1.7.0-green.svg)](CHANGELOG.md)

[![ComfyUI](https://img.shields.io/badge/ComfyUI-Compatible-orange.svg)](https://github.com/comfyanonymous/ComfyUI)## 🎯 All Nodes (Under "Eric Prompt Enhancers" Category)



A comprehensive suite of **5 AI-powered prompt enhancement nodes** for ComfyUI using local LLMs (LM Studio or Ollama). Transform simple prompts into detailed, platform-optimized descriptions for video and image generation.### 1. Video Prompt Expander

Simple video prompt expansion with presets and expansion tiers.

![Eric's Prompt Enhancers](https://img.shields.io/badge/Nodes-5-brightgreen) ![Platforms](https://img.shields.io/badge/Image%20Platforms-8-blue) ![Video Support](https://img.shields.io/badge/Video-✓-success)

### 2. Video Prompt Expander (Advanced)

---Granular control over video aesthetics with detailed settings.



## 🎯 All Nodes### 3. Image-to-Video Prompt Expander

Vision model analyzes images and adds motion descriptions.

Find all nodes under the **"Eric Prompt Enhancers"** category in ComfyUI.

### 4. Image-to-Image Prompt Expander

### 1. 🎬 Video Prompt ExpanderPlatform-aware image-to-image prompt generation (Flux, SDXL, Hunyuan, Qwen, Wan).

Simple video prompt expansion with style presets and expansion tiers.

- **5 Expansion Tiers**: Auto, Basic, Enhanced, Advanced, Cinematic### 5. Text-to-Image Prompt Enhancer ⭐ NEW

- **6 Style Presets**: Cinematic, Surreal, Action, Stylized, Noir, RandomAdvanced multi-platform image prompt enhancement with extensive controls.

- **Auto-Detection**: Analyzes input complexity and selects optimal tier

**Supports:** Flux, SDXL, Pony Diffusion, Illustrious XL, Chroma, Qwen Image, Qwen Edit, Wan Image

### 2. 🎬 Video Prompt Expander (Advanced)

Granular control over video aesthetics with **50+ detailed settings**.## ✨ Key Features

- **Lighting Controls**: Light source, lighting type, time of day

- **Camera Controls**: Shot size, composition, lens, angle, movement### Video Nodes

- **Color/Style**: Color tone, visual style, visual effects- 🎬 **5 Expansion Tiers**: Auto, Basic, Enhanced, Advanced, Cinematic

- **Motion/Emotion**: Character emotion, movement dynamics- 🎨 **6 Style Presets**: Cinematic, Surreal, Action, Stylized, Noir, Random

- 🎯 **Auto-Detection**: Analyzes input complexity

### 3. 🖼️➡️🎬 Image-to-Video Prompt Expander- 🔄 **Multiple Variations**: Generate up to 3 variations

Vision model analyzes images and adds motion descriptions for video generation.- � **Vision Support**: Analyze images for video generation

- **Image Analysis**: Automatic scene understanding

- **Motion Addition**: AI-generated motion descriptions### Image Nodes (NEW!)

- **Style Integration**: Combines visual analysis with expansion tiers- 🖼️ **8 Platform Support**: Flux, SDXL, Pony, Illustrious, Chroma, Qwen, Wan

- 🎨 **Advanced Controls**: Camera, lighting, weather, time of day

### 4. 🖼️➡️🖼️ Image-to-Image Prompt Expander- � **Wildcard Random**: Auto-variety in batch generation

Platform-aware image-to-image prompt generation.- 📸 **Reference Images**: Optional 1-2 image inputs

- **5 Platforms**: Flux Redux, SDXL Img2Img, Hunyuan Img2Img, Qwen Edit, Wan Edit- 🏷️ **Platform-Specific**: Automatic token optimization per platform

- **Transformation Controls**: Style transfer, detail level, creativity

- **Vision Analysis**: Understands source image characteristics### Universal

- 🤖 **Local LLM Support**: LM Studio and Ollama

### 5. ⭐ 📝➡️🖼️ Text-to-Image Prompt Enhancer **(NEW v1.7)**- 📝 **Keyword Integration**: Add LoRA triggers and custom terms

Advanced multi-platform image prompt enhancement with extensive creative controls.- � **File Export**: Save prompts with metadata

- **8 Platforms**: Flux, SDXL, Pony Diffusion, Illustrious XL, Chroma, Qwen Image, Qwen Edit, Wan Image- ➖ **Smart Negatives**: Platform-optimized negative prompts

- **Reference Images**: Optional 1-2 image inputs with visual analysis

- **Genre Styles**: 22 styles (cinematic, horror, cyberpunk, etc.)## Installation

- **Prompt Length Control**: Very Short to Very Long (20-400 tokens)

- **Subject Controls**: Framing (14 options) and Pose (17 options)1. Navigate to your ComfyUI custom nodes directory:

- **Advanced Settings**: Camera, lighting, weather, time, composition, color mood```bash

- **Special Syntax**: Emphasis `(keyword:1.5)` and Alternation `{a|b|c}`cd ComfyUI/custom_nodes/

```

---

2. The node is already installed in: `video_prompter/`

## ✨ Key Features

3. Restart ComfyUI

### 🤖 Local LLM Support

- **LM Studio**: OpenAI-compatible API (recommended)4. All nodes will appear under: **Add Node → Eric Prompt Enhancers**

- **Ollama**: Simple CLI-based LLM server

- **Privacy**: All processing happens locally, no data sent to cloud services## Requirements



### 🎨 Platform-Specific Optimization### Python Dependencies

Each platform has unique requirements and prompting styles:```bash

pip install requests

| Platform | Style | Optimal Length | Specialization |```

|----------|-------|----------------|----------------|

| **Flux** | Natural language | 75-150 tokens | Photography, artistic |### LLM Backend Setup

| **SDXL** | Natural/tags hybrid | 40-75 tokens | Versatile, balanced |

| **Pony Diffusion** | Booru tags | Tag count | Anime, characters |**Option 1: LM Studio**

| **Illustrious XL** | Danbooru tags | Tag count | Detailed anime |1. Download from: https://lmstudio.ai/

| **Chroma/Meissonic** | Detailed natural | 100-200 tokens | Complex scenes |2. Load a model (recommended: Llama 3 or similar)

| **Qwen Image** | Technical descriptions | Medium | General purpose |3. Start the server (default: http://localhost:1234)

| **Qwen Edit** | Edit instructions | Medium | Image editing |

| **Wan Image** | Cinematography | 60-120 tokens | Professional video stills |**Option 2: Ollama**

1. Install from: https://ollama.ai/

### 🎯 Advanced Controls (Text-to-Image v1.7)2. Pull a model: `ollama pull llama3`

- **Prompt Length**: 6 options (very_short to very_long)3. Server runs automatically (default: http://localhost:11434)

- **Genre/Style**: 22 genres (surreal, cinematic, horror, cyberpunk, noir, etc.)

- **Subject Framing**: 14 shot types (close-up, wide shot, cowboy shot, etc.)## Node Inputs

- **Subject Pose**: 17 poses (standing, action, contrapposto, etc.)

- **Camera**: Angle, composition (11 options each)### Core Inputs

- **Lighting**: Source, quality, time of day, weather (8-13 options each)- **basic_prompt**: Your simple video idea

- **Color**: Art style, color mood (18, 10 options)- **preset**: Style preset (custom/cinematic/surreal/action/stylized/noir/random)

- **Detail Level**: 6 options from simplified to intricate- **expansion_tier**: Detail level (auto/basic/enhanced/advanced/cinematic)

- **mode**: text-to-video or image-to-video

All controls support: `auto` (intelligent defaults), `random` (variety), `none` (disable), or specific values.

### LLM Configuration

### 🔧 Special Syntax Support- **llm_backend**: lm_studio or ollama

- **model_name**: Model identifier (e.g., "llama3")

**Emphasis (Weight Control)**- **api_endpoint**: API URL (default LM Studio: http://localhost:1234/v1)

```- **temperature**: 0.1-2.0 (lower = focused, higher = creative)

(keyword:1.5)    # Increase importance

(keyword:0.5)    # Decrease importance### Keywords

```- **positive_keywords**: Comma-separated must-include terms (LoRA triggers, etc.)

- **negative_keywords**: Comma-separated terms to avoid

**Alternation (Random Selection)**

```### Output Options

{cat|dog|rabbit}           # Picks one randomly- **num_variations**: Generate 1-3 variations

{red|blue|green} dress     # Random color- **save_to_file**: Save prompts to disk

```- **filename_base**: Base name for saved files



**Combined**## Node Outputs

```

{elegant|casual} woman with (detailed face:1.5) and {blonde|red} (hair:1.2)1. **positive_prompt_1**: First enhanced prompt

```2. **positive_prompt_2**: Second variation (if requested)

3. **positive_prompt_3**: Third variation (if requested)

---4. **negative_prompt**: Auto-generated negative prompt

5. **breakdown**: Detailed analysis of expansion

## 📦 Installation6. **status**: Success/error messages and file save location



### Method 1: Git Clone (Recommended)## Expansion Tiers



```bash### Basic

cd ComfyUI/custom_nodes/**Formula**: Subject + Scene + Motion

git clone https://github.com/EricRollei/video_prompter.git- Simple expansion with essential details

```- Clear subject, setting, and action

- ~50-100 words

### Method 2: Manual Install

### Enhanced

1. Download this repository as ZIP**Formula**: Subject + Scene + Motion + Basic Aesthetics

2. Extract to `ComfyUI/custom_nodes/video_prompter/`- Detailed descriptions with characteristics

3. Restart ComfyUI- Basic shot size and lighting

- ~100-200 words

### Dependencies

### Advanced

Install Python requirements:**Formula**: Full Details + Complete Aesthetics + Camera Work

- Professional cinematography terms

```bash- Specific lighting, composition, lens choices

cd ComfyUI/custom_nodes/video_prompter/- Camera angles and movements

pip install -r requirements.txt- ~200-350 words

```

### Cinematic

**Requirements:****Formula**: Masterful Description + All Professional Elements

- Python 3.8+- Director-level shot description

- PyTorch (usually included with ComfyUI)- Complete lighting setup with technical details

- NumPy (usually included with ComfyUI)- Precise camera movements and choreography

- Pillow/PIL (usually included with ComfyUI)- Color grading and atmospheric elements

- requests (for LLM API calls)- ~350-500+ words



---## Presets Explained



## ⚙️ Setup### Cinematic

Professional film quality with emphasis on lighting, composition, and camera movement.

### LLM Backend Setup (Required)- Edge lighting, soft lighting, warm colors

- Smooth camera movements

Choose **one** of these options:- Professional framing



#### Option 1: LM Studio (Recommended)### Surreal

Dreamlike, otherworldly aesthetics with unusual elements.

1. **Download**: [https://lmstudio.ai/](https://lmstudio.ai/)- Unnatural lighting and mixed sources

2. **Install** and launch LM Studio- Floating, ethereal movements

3. **Download a model** (search for "llama" or "mistral", recommended: Llama 3.2 8B)- Saturated or desaturated colors

4. **Start the server**: Click "↔" (Server) tab → "Start Server"

   - Default: `http://localhost:1234/v1`### Action

5. **Note the model name** (e.g., "llama3")High-energy, dynamic sequences with rapid motion.

- Fast camera movement, tracking shots

See [docs/LM_STUDIO_SETUP.md](docs/LM_STUDIO_SETUP.md) for details.- High contrast, dramatic lighting

- Explosive, kinetic action

#### Option 2: Ollama

### Stylized

1. **Install**: [https://ollama.ai/](https://ollama.ai/)Artistic visual style over realism.

2. **Pull a model**: `ollama pull llama3`- Strong visual identity

3. **Server runs automatically** at `http://localhost:11434/v1`- Consistent color palette

- Graphic, illustrative elements

---

### Noir

## 🚀 Quick StartDark, moody, high-contrast aesthetic.

- High contrast, hard lighting

1. **Add Node**: Right-click → Add Node → Eric Prompt Enhancers- Deep shadows and chiaroscuro

2. **Enter Prompt**: "a woman in a garden"- Desaturated or black and white

3. **Configure LLM**: Backend (lm_studio), Model Name (llama3), API Endpoint- Low angles and dutch angles

4. **Set Options**: Platform, style, settings

5. **Connect Output**: Link to your generation node### Random

6. **Generate**: Run workflowRandomly selects complementary elements from the Wan 2.2 guide for creative exploration.



### Example Output## Usage Examples



```### Example 1: Basic Text-to-Video

Input: "a woman in a garden"```

Platform: fluxInput: "A cat playing piano"

Genre: cinematicPreset: Cinematic

Length: mediumTier: Auto (detects "Enhanced")



Output: "Cinematic medium shot portrait of an elegant woman in a lush garden Output: "A fluffy orange tabby cat sits at a polished black grand piano in a warmly lit living room. The cat's paws press down on the ivory keys with surprising dexterity. Soft afternoon light streams through a nearby window, creating edge lighting on the cat's fur. Medium close-up shot, eye-level angle. The camera slowly pushes in as the cat continues to play. Warm color palette, soft lighting, clean single shot."

bathed in warm golden hour sunlight, captured from a low angle, graceful pose, ```

detailed botanical environment with soft bokeh, professional photography quality, 

(detailed face:1.4), flowing dress, film-like aesthetics"### Example 2: Image-to-Video with Keywords

``````

Input: "The woman turns and walks toward the camera"

---Mode: Image-to-Video

Preset: Noir

## 📚 DocumentationPositive Keywords: myLoRA_trigger, detailed_face

Tier: Advanced

Comprehensive guides in [docs/](docs/):

Output: "The woman slowly turns her head, edge lighting creating dramatic shadows across her face, myLoRA_trigger, detailed_face. She begins walking directly toward the camera with deliberate, purposeful steps. Her silhouette is backlit by a single streetlight, creating a strong rim light effect. The camera remains static as she approaches, her features gradually emerging from shadow. High contrast lighting, desaturated colors, low angle shot. The scene has a tense, mysterious atmosphere."

### Getting Started```

- [QUICKSTART.md](docs/QUICKSTART.md) - Fast introduction

- [LM_STUDIO_SETUP.md](docs/LM_STUDIO_SETUP.md) - LM Studio setup### Example 3: Multiple Variations for Action

- [CONFIGURATION.md](docs/CONFIGURATION.md) - Settings explained```

Input: "Superhero landing from the sky"

### Node GuidesPreset: Action

- [TXT2IMG_GUIDE.md](docs/TXT2IMG_GUIDE.md) - Text-to-Image (20+ pages)Variations: 3

- [IMG2IMG_GUIDE.md](docs/IMG2IMG_GUIDE.md) - Image-to-ImageTier: Cinematic

- [WILDCARD_GUIDE.md](docs/WILDCARD_GUIDE.md) - Random wildcards

Results in 3 different takes:

### Reference- Variation 1: Emphasizes impact crater and dust

- [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - All nodes- Variation 2: Focuses on dynamic camera arc around landing

- [NODE_COMPARISON.md](docs/NODE_COMPARISON.md) - Which node to use- Variation 3: Features slow-motion with particle effects

```

### Updates

- [CHANGELOG.md](CHANGELOG.md) - Version history## Workflow Integration

- [UPDATE_V17_ENHANCED_CONTROLS.md](docs/UPDATE_V17_ENHANCED_CONTROLS.md) - v1.7

### Basic Workflow

---```

[AI Video Prompt Expander]

## 🔄 Version History    ↓ (positive_prompt_1)

[Video Generation Node]

### v1.7.0 (October 2025) - Enhanced Controls    ↓

- ✅ Fixed reference image usage[Output]

- ✨ Prompt length control (6 options)```

- ✨ Genre/style control (22 genres)

- ✨ Subject framing (14 types)### Advanced Workflow with Variations

- ✨ Subject pose (17 options)```

[AI Video Prompt Expander] (num_variations: 3)

### v1.6.1 (October 2025) - Bug Fixes    ↓ (positive_prompt_1) → [Video Gen 1]

- 🐛 Fixed settings leaking into output    ↓ (positive_prompt_2) → [Video Gen 2]  

- 🐛 Fixed emphasis syntax `(keyword:1.5)`    ↓ (positive_prompt_3) → [Video Gen 3]

- ✨ Added alternation `{a|b|c}`    ↓ (negative_prompt) → [All Video Gens]

```

### v1.6.0 (October 2025) - Text-to-Image

- ✨ New Text-to-Image node## File Output

- 🎨 8 platform support

- 📸 Reference imagesWhen **save_to_file** is enabled, prompts are saved to:

```

See [CHANGELOG.md](CHANGELOG.md) for complete history.ComfyUI/output/video_prompts/[filename_base]_[timestamp].txt

```

---

File includes:

## 🛠️ Troubleshooting- Enhanced positive prompt

- Negative prompt

### LLM Connection- Detailed breakdown

- Check server is running (LM Studio "Running" status)- Metadata (preset, tier, model, temperature)

- Verify endpoint URL matches- Original input

- Model name exact match (case-sensitive)

## Troubleshooting

### Output Quality

- Adjust `prompt_length` for target size### "Cannot connect to LM Studio/Ollama"

- Verify `genre_style` matches mood- Ensure LM Studio or Ollama is running

- Update to v1.6.1+ for bug fixes- Check the API endpoint URL

- Verify the model is loaded

### Node Not Appearing

- Restart ComfyUI after installation### "Request timed out"

- Check "Eric Prompt Enhancers" category- LLM might be slow on complex prompts

- Run `pip install -r requirements.txt`- Try lowering the tier

- Reduce temperature

---- Use a smaller/faster model



## 📄 License### "Missing keywords in output"

- Keywords are automatically appended if missing

**Dual License:**- Check the positive_keywords field spelling

- Verify keywords are comma-separated

### Non-Commercial Use

[Creative Commons Attribution-NonCommercial 4.0 International](http://creativecommons.org/licenses/by-nc/4.0/)### Empty outputs

- Check LLM backend connection

### Commercial Use- Review status output for error messages

Separate license required. Contact:- Try with a simpler input prompt first

- **Email**: eric@historic.camera or eric@rollei.us

- **GitHub**: [@EricRollei](https://github.com/EricRollei)## Tips for Best Results



See [LICENSE](LICENSE) for full terms.1. **Start Simple**: Begin with basic concepts and let the node expand them

2. **Use Auto Tier**: Let the node detect appropriate complexity

---3. **Experiment with Presets**: Different presets dramatically change the output

4. **Adjust Temperature**: Lower (0.3-0.5) for consistency, higher (0.8-1.2) for creativity

## 🙏 Credits5. **Combine Keywords**: Use positive_keywords for LoRA triggers and style terms

6. **Save Good Prompts**: Enable save_to_file to build a library

### Author7. **Generate Variations**: Use multiple variations to explore different interpretations

**Eric Hiss** ([@EricRollei](https://github.com/EricRollei))

## Wan 2.2 Guide Reference

### Dependencies

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - GPL-3.0This node implements the comprehensive Wan 2.2 prompting framework including:

- [PyTorch](https://pytorch.org/) - BSD-style

- [NumPy](https://numpy.org/) - BSD- **Aesthetic Control**: Lighting sources/types, time of day, shot sizes, composition, lenses, camera angles

- [Pillow](https://python-pillow.org/) - HPND- **Dynamic Control**: Motion types, character emotions, camera movements

- [requests](https://requests.readthedocs.io/) - Apache 2.0- **Stylization**: Visual styles (3D, 2D, watercolor, etc.), visual effects



### LLM BackendsFor more details, see the original guide: https://wan.video/

- [LM Studio](https://lmstudio.ai/) - Proprietary

- [Ollama](https://ollama.ai/) - MIT## Credits



### Platforms- Based on the Wan 2.2 Video Generation Prompting Guide

- **Flux** by Black Forest Labs- Developed for ComfyUI integration

- **SDXL** by Stability AI- Supports LM Studio and Ollama backends

- **Pony Diffusion** by Astralite

- **Illustrious XL** by OnomaAI Research## Version

- **Chroma/Meissonic** by Tencent AI Lab

- **Qwen** by Alibaba Cloud**v1.0** - Initial release with full Wan 2.2 framework integration

- **Wan** by Wuhan AI Institute

## License

---

MIT License - Free to use and modify

## 📞 Support

---

- **GitHub Issues**: [Report bugs here](https://github.com/EricRollei/video_prompter/issues)

- **Email**: eric@historic.camera, eric@rollei.us**Questions or Issues?** Check the status output for detailed error messages, or review the saved prompt files for debugging information.

- **Documentation**: Check [docs/](docs/) folder

---

**Made with ❤️ by Eric Hiss | Star ⭐ if you find this useful!**
