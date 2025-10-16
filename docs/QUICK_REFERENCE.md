# Quick Reference Guide - Eric's Prompt Enhancers

## Finding the Nodes

After restarting ComfyUI, all nodes appear under:

**Add Node → Eric Prompt Enhancers**

You'll find 5 nodes:
1. Video Prompt Expander
2. Video Prompt Expander (Advanced)
3. Image-to-Video Prompt Expander
4. Image-to-Image Prompt Expander
5. Text-to-Image Prompt Enhancer ⭐ NEW

---

## Text-to-Image Prompt Enhancer (NEW)

### Platform Selection

| Your Image Model | Select Platform |
|------------------|-----------------|
| FLUX.1-dev/schnell | flux |
| Stable Diffusion XL | sd_xl |
| Pony Diffusion v6 | pony |
| Illustrious XL | illustrious |
| Meissonic/MeissonFlow | chroma |
| Qwen Image | qwen_image |
| Qwen Image Edit | qwen_image_edit |
| Wan Image Models | wan_image |

### Platform Requirements

#### Pony Diffusion (CRITICAL!)
```
Positive MUST start with: score_9, score_8_up, score_7_up
Use underscores: long_hair NOT "long hair"
Negative MUST include: score_6, score_5, score_4
```

#### Illustrious XL
```
Positive MUST start with: masterpiece, best quality
Use underscores in tags
Detailed character appearance
```

#### All Others
```
Follow platform guidelines automatically
Node handles formatting
```

### Quick Workflow

```
[Text-to-Image Prompt Enhancer]
  - text_prompt: "your simple description"
  - target_platform: (match your image model)
  - camera_angle: (optional, or "auto")
  - lighting_source: (optional, or "auto")
  - time_of_day: (optional, or "auto")
  ↓
positive_prompt → [CLIP Text Encode] → [KSampler]
negative_prompt → [CLIP Text Encode] → [KSampler]
```

### Control Options

**Set to:**
- **"auto"** = LLM decides what fits best
- **"random"** = Random choice for variety
- **"none"** = Omit this control
- **Specific value** = Force this setting

**Available Controls:**
- camera_angle: Eye level, low angle, high angle, bird's eye, etc.
- composition: Rule of thirds, centered, golden ratio, etc.
- lighting_source: Natural, studio, golden hour, moonlight, etc.
- lighting_quality: Soft, dramatic, volumetric, etc.
- time_of_day: Dawn, noon, golden hour, dusk, night, etc.
- weather: Clear, foggy, rainy, snowy, etc.
- art_style: Photorealistic, anime, oil painting, etc.
- color_mood: Vibrant, muted, warm tones, etc.
- detail_level: Standard, highly detailed, minimalist

### Wildcards for Variety

```
camera_angle: random
lighting_source: random
weather: random
color_mood: random
```

Perfect for batch generation with variety!

---

## Image-to-Image Prompt Expander

### Platform Selection

Same as Text-to-Image, but focused on image editing:
- flux, sd_xl, wan22, hunyuan_image, qwen_image, qwen_image_edit

### Quick Workflow

```
[Load Image]
  ↓
[Image-to-Image Prompt Expander]
  - image: (from Load Image)
  - change_request: "what to change"
  - target_platform: (match your model)
  - use_vision_model: true
  ↓
positive_prompt → [Your Image Gen Node]
negative_prompt → [Your Image Gen Node]
```

### Vision Model Setup

**LM Studio:**
- Load a vision model (Llama 3.2 Vision, LLaVA)
- Start server
- vision_endpoint: http://localhost:1234/v1

**Ollama:**
- Pull vision model: `ollama pull llama3.2-vision`
- vision_endpoint: http://localhost:11434

---

## Video Prompt Expander

### Expansion Tiers

- **auto**: LLM analyzes and chooses tier
- **basic**: ~50-100 words, simple
- **enhanced**: ~100-200 words, detailed
- **advanced**: ~200-350 words, professional
- **cinematic**: ~300-500 words, film-quality

### Presets

- **cinematic**: Professional film, dramatic lighting
- **surreal**: Dreamlike, otherworldly
- **action**: High-energy, dynamic
- **stylized**: Artistic, creative
- **noir**: Dark, moody, dramatic
- **random**: Random preset each time

### Quick Workflow

```
[Video Prompt Expander]
  - basic_prompt: "your video idea"
  - preset: cinematic
  - expansion_tier: auto
  - mode: text-to-video
  ↓
positive_prompt_1 → [Your Video Gen Node]
negative_prompt → [Your Video Gen Node]
```

---

## Image-to-Video Prompt Expander

### Quick Workflow

```
[Load Image]
  ↓
[Image-to-Video Prompt Expander]
  - image: (from Load Image)
  - motion_description: "what should move/happen"
  - preset: cinematic
  - use_vision_model: true
  ↓
positive_prompt → [Your Video Gen Node]
negative_prompt → [Your Video Gen Node]
```

---

## Common Settings (All Nodes)

### LLM Backend

**LM Studio:**
```
llm_backend: lm_studio
api_endpoint: http://localhost:1234/v1
model_name: llama3 (or your loaded model)
```

**Ollama:**
```
llm_backend: ollama
api_endpoint: http://localhost:11434
model_name: llama3
```

### Temperature

- **0.5-0.6**: Precise, consistent
- **0.7**: Balanced (recommended)
- **0.8-1.0**: More creative
- **1.0+**: Very creative, less predictable

### Keywords

**Positive Keywords:**
```
"LoRA_trigger, cinematic_lighting, specific_style"
```
Comma-separated terms to include

**Negative Keywords:**
```
"watermark, blurry, low quality, distorted"
```
Comma-separated terms to avoid

---

## Platform Examples

### Flux Example
```
Input: "a woman in a garden"
Platform: flux
Output: "masterpiece, best quality, highly detailed photograph 
of a woman in a lush garden, golden hour lighting, professional 
photography, in the style of Annie Leibovitz, 8k uhd"
```

### Pony Example
```
Input: "anime girl with cat ears"
Platform: pony
Output: "score_9, score_8_up, score_7_up, 1girl, cat_ears, 
animal_ears, long_hair, detailed_face, garden, best_quality"
Negative: "score_6, score_5, score_4, worst quality, low quality"
```

### SDXL Example
```
Input: "cyberpunk city street"
Platform: sd_xl
Output: "masterpiece, best quality, highly detailed, cyberpunk 
city street at night, neon lights, wet pavement, professional"
```

### Chroma Example
```
Input: "marketplace scene"
Platform: chroma
Output: "high quality, intricate, masterpiece: A bustling 
marketplace scene with vendors arranging colorful fruits, 
customers browsing stalls, hanging fabric awnings creating 
dappled shadows, dynamic composition, detailed..."
```

---

## Troubleshooting

### Nodes Not Appearing
1. Restart ComfyUI completely
2. Check console for errors
3. Verify `__init__.py` has no errors
4. Look under "Eric Prompt Enhancers" category

### LLM Connection Failed
1. Is LM Studio/Ollama running?
2. Check API endpoint URL
3. Test with simple prompt
4. Check console for detailed error

### Poor Output Quality
1. Wrong platform selected?
2. Temperature too high/low?
3. Model not appropriate for task?
4. Add more specific controls
5. Include positive/negative keywords

### Pony/Illustrious Issues
1. Check output has required tokens
2. Verify underscores in tags
3. Make sure negative has score tags
4. Platform must be set to "pony" or "illustrious"

---

## Tips for Best Results

### Text-to-Image
1. ✅ Match platform to your image model
2. ✅ Set at least lighting or art style
3. ✅ Use "auto" for most controls initially
4. ✅ Add LoRA triggers to positive keywords
5. ✅ Always connect negative prompt

### Image-to-Image
1. ✅ Use vision model for best results
2. ✅ Be specific in change requests
3. ✅ Match platform to target model
4. ✅ Set key aesthetic controls
5. ✅ Test without vision first if issues

### Video Prompts
1. ✅ Use "auto" tier to start
2. ✅ Match preset to video style
3. ✅ Add LoRA triggers as keywords
4. ✅ Generate variations for options
5. ✅ Save successful prompts to file

---

## File Saving

Enable `save_to_file: true` to save:
- Enhanced prompts
- All settings used
- Metadata
- Timestamps

Files saved to:
- Video: `output/video_prompts/`
- Image: `output/txt2img_prompts/`
- Img2Img: `output/img2img_prompts/`

---

## Documentation Files

- **README.md** - Overview and installation
- **TXT2IMG_GUIDE.md** - Complete text-to-image guide with examples
- **IMG2IMG_GUIDE.md** - Image-to-image guide
- **UPDATE_V16_ERIC.md** - Version 1.6 update notes
- **CONFIGURATION.md** - LLM setup details
- **LM_STUDIO_SETUP.md** - LM Studio setup
- **QUICKSTART.md** - Getting started quickly

---

## Need More Help?

1. **Read full guides**: See TXT2IMG_GUIDE.md for detailed examples
2. **Check platform requirements**: Each platform has specific needs
3. **Console logs**: Check ComfyUI console for detailed errors
4. **Test simple prompts**: Start basic, then add complexity
5. **Experiment**: Try different settings to learn what works

**Happy prompting!**
