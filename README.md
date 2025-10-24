# Eric's Prompt Enhancers for ComfyUI

[![License](https://img.shields.io/badge/License-Dual%20(NC%2FCommercial)-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.8.0-green.svg)](CHANGELOG.md)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Compatible-orange.svg)](https://github.com/comfyanonymous/ComfyUI)

A comprehensive suite of **5 AI-powered prompt enhancement nodes** for ComfyUI using local LLMs (LM Studio or Ollama). Transform simple prompts into detailed, platform-optimized descriptions for video and image generation.

![Eric's Prompt Enhancers](https://img.shields.io/badge/Nodes-5-brightgreen) ![Platforms](https://img.shields.io/badge/Image%20Platforms-8-blue) ![Video Support](https://img.shields.io/badge/Video-✓-success)

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

## 🎯 The 5 Nodes

Find all nodes under the **"Eric Prompt Enhancers"** category in ComfyUI.

### 1. 🎬 Video Prompt Expander

Simple video prompt expansion with style presets.

- **4 Detail Levels**: Concise, Moderate, Detailed, Exhaustive
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

- **5 Platforms**: Flux Redux, SDXL Img2Img, Hunyuan Img2Img, Qwen Edit, Wan Edit
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

## 📚 Documentation

### Quick References
- [QUICKSTART.md](docs/QUICKSTART.md) - Get started in 5 minutes
- [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - Fast reference guide
- [QUICK_REF_V17.md](docs/QUICK_REF_V17.md) - Text-to-Image quick reference

### Node Guides
- [TXT2IMG_GUIDE.md](docs/TXT2IMG_GUIDE.md) - Text-to-Image node complete guide
- [IMG2IMG_GUIDE.md](docs/IMG2IMG_GUIDE.md) - Image-to-Image workflows
- [NODE_COMPARISON.md](docs/NODE_COMPARISON.md) - Which node to use when
- [ADVANCED_NODE_REDESIGN.md](docs/ADVANCED_NODE_REDESIGN.md) - Advanced node v1.8 redesign details

### Setup Guides
- [LM_STUDIO_SETUP.md](docs/LM_STUDIO_SETUP.md) - LM Studio configuration
- [VISION_BACKEND_GUIDE.md](VISION_BACKEND_GUIDE.md) - Qwen3-VL setup for image analysis
- [CONFIGURATION.md](docs/CONFIGURATION.md) - Advanced configuration options

### Platform & Technical
- [WAN_GUIDE_REFERENCE.md](docs/WAN_GUIDE_REFERENCE.md) - Wan 2.2 video prompt guide
- [WILDCARD_GUIDE.md](docs/WILDCARD_GUIDE.md) - Wildcard syntax examples

### Updates & Fixes
- [CHANGELOG.md](CHANGELOG.md) - Complete version history
- [UPDATE_V17_ENHANCED_CONTROLS.md](docs/UPDATE_V17_ENHANCED_CONTROLS.md) - v1.7 features
- [BUGFIX_ADVANCED_NODE.md](docs/BUGFIX_ADVANCED_NODE.md) - v1.8 bug fixes
- [BUGFIX_V161.md](docs/BUGFIX_V161.md) - v1.6.1 syntax fixes

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

See [docs/ADVANCED_NODE_REDESIGN.md](docs/ADVANCED_NODE_REDESIGN.md) for complete details.

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

**Version**: 1.8.0  
**Last Updated**: October 24, 2025  
**Author**: Eric Rollei  
**Repository**: https://github.com/EricRollei/Local_LLM_Prompt_Enhancer
