# Eric's Prompt Enhancers for ComfyUI

A comprehensive suite of AI-powered prompt enhancement nodes for ComfyUI using local LLMs (LM Studio or Ollama). Transform simple prompts into detailed, platform-optimized descriptions for video and image generation.

## 🎯 All Nodes (Under "Eric Prompt Enhancers" Category)

### 1. Video Prompt Expander
Simple video prompt expansion with presets and expansion tiers.

### 2. Video Prompt Expander (Advanced)
Granular control over video aesthetics with detailed settings.

### 3. Image-to-Video Prompt Expander
Vision model analyzes images and adds motion descriptions.

### 4. Image-to-Image Prompt Expander
Platform-aware image-to-image prompt generation (Flux, SDXL, Hunyuan, Qwen, Wan).

### 5. Text-to-Image Prompt Enhancer ⭐ NEW
Advanced multi-platform image prompt enhancement with extensive controls.

**Supports:** Flux, SDXL, Pony Diffusion, Illustrious XL, Chroma, Qwen Image, Qwen Edit, Wan Image

## ✨ Key Features

### Video Nodes
- 🎬 **5 Expansion Tiers**: Auto, Basic, Enhanced, Advanced, Cinematic
- 🎨 **6 Style Presets**: Cinematic, Surreal, Action, Stylized, Noir, Random
- 🎯 **Auto-Detection**: Analyzes input complexity
- 🔄 **Multiple Variations**: Generate up to 3 variations
- � **Vision Support**: Analyze images for video generation

### Image Nodes (NEW!)
- 🖼️ **8 Platform Support**: Flux, SDXL, Pony, Illustrious, Chroma, Qwen, Wan
- 🎨 **Advanced Controls**: Camera, lighting, weather, time of day
- � **Wildcard Random**: Auto-variety in batch generation
- 📸 **Reference Images**: Optional 1-2 image inputs
- 🏷️ **Platform-Specific**: Automatic token optimization per platform

### Universal
- 🤖 **Local LLM Support**: LM Studio and Ollama
- 📝 **Keyword Integration**: Add LoRA triggers and custom terms
- � **File Export**: Save prompts with metadata
- ➖ **Smart Negatives**: Platform-optimized negative prompts

## Installation

1. Navigate to your ComfyUI custom nodes directory:
```bash
cd ComfyUI/custom_nodes/
```

2. The node is already installed in: `video_prompter/`

3. Restart ComfyUI

4. All nodes will appear under: **Add Node → Eric Prompt Enhancers**

## Requirements

### Python Dependencies
```bash
pip install requests
```

### LLM Backend Setup

**Option 1: LM Studio**
1. Download from: https://lmstudio.ai/
2. Load a model (recommended: Llama 3 or similar)
3. Start the server (default: http://localhost:1234)

**Option 2: Ollama**
1. Install from: https://ollama.ai/
2. Pull a model: `ollama pull llama3`
3. Server runs automatically (default: http://localhost:11434)

## Node Inputs

### Core Inputs
- **basic_prompt**: Your simple video idea
- **preset**: Style preset (custom/cinematic/surreal/action/stylized/noir/random)
- **expansion_tier**: Detail level (auto/basic/enhanced/advanced/cinematic)
- **mode**: text-to-video or image-to-video

### LLM Configuration
- **llm_backend**: lm_studio or ollama
- **model_name**: Model identifier (e.g., "llama3")
- **api_endpoint**: API URL (default LM Studio: http://localhost:1234/v1)
- **temperature**: 0.1-2.0 (lower = focused, higher = creative)

### Keywords
- **positive_keywords**: Comma-separated must-include terms (LoRA triggers, etc.)
- **negative_keywords**: Comma-separated terms to avoid

### Output Options
- **num_variations**: Generate 1-3 variations
- **save_to_file**: Save prompts to disk
- **filename_base**: Base name for saved files

## Node Outputs

1. **positive_prompt_1**: First enhanced prompt
2. **positive_prompt_2**: Second variation (if requested)
3. **positive_prompt_3**: Third variation (if requested)
4. **negative_prompt**: Auto-generated negative prompt
5. **breakdown**: Detailed analysis of expansion
6. **status**: Success/error messages and file save location

## Expansion Tiers

### Basic
**Formula**: Subject + Scene + Motion
- Simple expansion with essential details
- Clear subject, setting, and action
- ~50-100 words

### Enhanced
**Formula**: Subject + Scene + Motion + Basic Aesthetics
- Detailed descriptions with characteristics
- Basic shot size and lighting
- ~100-200 words

### Advanced
**Formula**: Full Details + Complete Aesthetics + Camera Work
- Professional cinematography terms
- Specific lighting, composition, lens choices
- Camera angles and movements
- ~200-350 words

### Cinematic
**Formula**: Masterful Description + All Professional Elements
- Director-level shot description
- Complete lighting setup with technical details
- Precise camera movements and choreography
- Color grading and atmospheric elements
- ~350-500+ words

## Presets Explained

### Cinematic
Professional film quality with emphasis on lighting, composition, and camera movement.
- Edge lighting, soft lighting, warm colors
- Smooth camera movements
- Professional framing

### Surreal
Dreamlike, otherworldly aesthetics with unusual elements.
- Unnatural lighting and mixed sources
- Floating, ethereal movements
- Saturated or desaturated colors

### Action
High-energy, dynamic sequences with rapid motion.
- Fast camera movement, tracking shots
- High contrast, dramatic lighting
- Explosive, kinetic action

### Stylized
Artistic visual style over realism.
- Strong visual identity
- Consistent color palette
- Graphic, illustrative elements

### Noir
Dark, moody, high-contrast aesthetic.
- High contrast, hard lighting
- Deep shadows and chiaroscuro
- Desaturated or black and white
- Low angles and dutch angles

### Random
Randomly selects complementary elements from the Wan 2.2 guide for creative exploration.

## Usage Examples

### Example 1: Basic Text-to-Video
```
Input: "A cat playing piano"
Preset: Cinematic
Tier: Auto (detects "Enhanced")

Output: "A fluffy orange tabby cat sits at a polished black grand piano in a warmly lit living room. The cat's paws press down on the ivory keys with surprising dexterity. Soft afternoon light streams through a nearby window, creating edge lighting on the cat's fur. Medium close-up shot, eye-level angle. The camera slowly pushes in as the cat continues to play. Warm color palette, soft lighting, clean single shot."
```

### Example 2: Image-to-Video with Keywords
```
Input: "The woman turns and walks toward the camera"
Mode: Image-to-Video
Preset: Noir
Positive Keywords: myLoRA_trigger, detailed_face
Tier: Advanced

Output: "The woman slowly turns her head, edge lighting creating dramatic shadows across her face, myLoRA_trigger, detailed_face. She begins walking directly toward the camera with deliberate, purposeful steps. Her silhouette is backlit by a single streetlight, creating a strong rim light effect. The camera remains static as she approaches, her features gradually emerging from shadow. High contrast lighting, desaturated colors, low angle shot. The scene has a tense, mysterious atmosphere."
```

### Example 3: Multiple Variations for Action
```
Input: "Superhero landing from the sky"
Preset: Action
Variations: 3
Tier: Cinematic

Results in 3 different takes:
- Variation 1: Emphasizes impact crater and dust
- Variation 2: Focuses on dynamic camera arc around landing
- Variation 3: Features slow-motion with particle effects
```

## Workflow Integration

### Basic Workflow
```
[AI Video Prompt Expander]
    ↓ (positive_prompt_1)
[Video Generation Node]
    ↓
[Output]
```

### Advanced Workflow with Variations
```
[AI Video Prompt Expander] (num_variations: 3)
    ↓ (positive_prompt_1) → [Video Gen 1]
    ↓ (positive_prompt_2) → [Video Gen 2]  
    ↓ (positive_prompt_3) → [Video Gen 3]
    ↓ (negative_prompt) → [All Video Gens]
```

## File Output

When **save_to_file** is enabled, prompts are saved to:
```
ComfyUI/output/video_prompts/[filename_base]_[timestamp].txt
```

File includes:
- Enhanced positive prompt
- Negative prompt
- Detailed breakdown
- Metadata (preset, tier, model, temperature)
- Original input

## Troubleshooting

### "Cannot connect to LM Studio/Ollama"
- Ensure LM Studio or Ollama is running
- Check the API endpoint URL
- Verify the model is loaded

### "Request timed out"
- LLM might be slow on complex prompts
- Try lowering the tier
- Reduce temperature
- Use a smaller/faster model

### "Missing keywords in output"
- Keywords are automatically appended if missing
- Check the positive_keywords field spelling
- Verify keywords are comma-separated

### Empty outputs
- Check LLM backend connection
- Review status output for error messages
- Try with a simpler input prompt first

## Tips for Best Results

1. **Start Simple**: Begin with basic concepts and let the node expand them
2. **Use Auto Tier**: Let the node detect appropriate complexity
3. **Experiment with Presets**: Different presets dramatically change the output
4. **Adjust Temperature**: Lower (0.3-0.5) for consistency, higher (0.8-1.2) for creativity
5. **Combine Keywords**: Use positive_keywords for LoRA triggers and style terms
6. **Save Good Prompts**: Enable save_to_file to build a library
7. **Generate Variations**: Use multiple variations to explore different interpretations

## Wan 2.2 Guide Reference

This node implements the comprehensive Wan 2.2 prompting framework including:

- **Aesthetic Control**: Lighting sources/types, time of day, shot sizes, composition, lenses, camera angles
- **Dynamic Control**: Motion types, character emotions, camera movements
- **Stylization**: Visual styles (3D, 2D, watercolor, etc.), visual effects

For more details, see the original guide: https://wan.video/

## Credits

- Based on the Wan 2.2 Video Generation Prompting Guide
- Developed for ComfyUI integration
- Supports LM Studio and Ollama backends

## Version

**v1.0** - Initial release with full Wan 2.2 framework integration

## License

MIT License - Free to use and modify

---

**Questions or Issues?** Check the status output for detailed error messages, or review the saved prompt files for debugging information.
