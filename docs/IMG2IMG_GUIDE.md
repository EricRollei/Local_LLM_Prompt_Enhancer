# Image-to-Image Prompt Expander - Complete Guide

## What It Does

The **Image-to-Image Prompt Expander** is a platform-aware node that:

1. **Analyzes your image** with a vision model
2. **Takes your change request** (what to modify)
3. **Generates platform-optimized prompts** for:
   - Flux (FLUX.1-dev/schnell)
   - Stable Diffusion XL
   - Wan 2.2 (adapted for images)
   - Hunyuan Image
   - Qwen Image
   - Qwen Image Edit

**Each platform gets prompts formatted the way it works best!**

## Why Platform-Specific Matters

Different models need different prompting styles:

| Platform | Prefers |
|----------|---------|
| **Flux** | Natural language, artistic, "in the style of", 75-150 tokens |
| **SDXL** | Front-loaded quality, 40-75 tokens, token-optimized |
| **Wan 2.2** | Technical terms, structured, cinematographic |
| **Hunyuan** | Simple English, clear, realistic focus, 40-80 tokens |
| **Qwen Image** | Natural, balanced, cultural elements, 50-100 tokens |
| **Qwen Edit** | VERY concise, change-focused, 20-50 tokens |

**This node knows these differences and formats prompts accordingly!**

## Quick Start

### Basic Setup

```
[Load Image] → [Image-to-Image Prompt Expander] → [Your Image Gen Node]
```

### Configuration

1. **Load vision model** (LM Studio or Ollama)
2. **Set platform**: flux, sd_xl, hunyuan_image, etc.
3. **Describe changes**: "change dress to red, add sunset lighting"
4. **Aesthetic controls**: style, lighting, composition
5. **Generate!**

## Node Parameters

### Image & Changes

**image** (Image Input)
- Connect from Load Image
- Your source image

**change_request** (String)
- What to change/modify
- Examples:
  - "change dress color to red"
  - "add sunset lighting"
  - "replace background with forest"
  - "make it look like an oil painting"
  - (Leave empty to just enhance description)

### Platform Selection

**target_platform** (Dropdown)
- `flux`: Flux.1-dev/schnell (natural, detailed)
- `sd_xl`: Stable Diffusion XL (token-optimized)
- `wan22`: Wan 2.2 adapted (technical, structured)
- `hunyuan_image`: Hunyuan (clear, realistic)
- `qwen_image`: Qwen (balanced, natural)
- `qwen_image_edit`: Qwen Edit (concise changes)

**Choose based on what image model you're using!**

### Vision Model Settings

**use_vision_model** (Boolean)
- `True`: AI describes the image
- `False`: Skip vision (manual description)

**vision_backend** / **vision_model_name** / **vision_endpoint**
- Same as Image-to-Video node
- Use Llama 3.2 Vision, LLaVA, etc.

### Expansion Model Settings

**expansion_backend** / **expansion_model_name** / **expansion_endpoint**
- Model that formats the prompt
- Can be same or different from vision
- Use Llama 3.1, Qwen, etc.

**temperature** (0.1 - 2.0)
- `0.5-0.6`: Precise, platform-following
- `0.7`: Balanced (recommended)
- `0.8+`: More creative

### Aesthetic Controls

**art_style**
- photorealistic, digital art, oil painting, watercolor
- anime, sketch, 3D render, illustration, concept art

**lighting_type**
- natural, studio, soft, dramatic
- golden hour, blue hour, rim, volumetric

**composition**
- rule of thirds, centered, symmetrical
- golden ratio, dynamic, minimalist

**color_palette**
- vibrant, muted, monochrome
- warm, cool, pastel, high contrast

**mood**
- serene, dramatic, mysterious
- cheerful, melancholic, epic, intimate

**detail_level**
- standard, highly detailed, intricate
- simplified, minimalist

**quality_emphasis** (Boolean)
- Adds platform-specific quality tokens
- Recommended: True

## Platform-Specific Examples

### Example 1: Flux

**Settings:**
```
target_platform: flux
change_request: "make it look like a renaissance oil painting"
art_style: oil painting
lighting: dramatic lighting
quality_emphasis: True
```

**Output style:**
```
"masterpiece, best quality, highly detailed, [image description], 
rendered as a renaissance oil painting with dramatic lighting, 
rich textures and classical composition, in the style of Caravaggio"
```

### Example 2: SDXL

**Settings:**
```
target_platform: sd_xl
change_request: "add cyberpunk neon lighting"
color_palette: vibrant
detail_level: highly detailed
```

**Output style:**
```
"masterpiece, best quality, highly detailed, [image description], 
with vibrant cyberpunk neon lighting, futuristic atmosphere"
(Front-loaded quality, ~60 tokens)
```

### Example 3: Qwen Image Edit

**Settings:**
```
target_platform: qwen_image_edit
change_request: "change background to forest, keep subject"
```

**Output style:**
```
"replace background with forest, keep subject unchanged, 
seamless, natural, high quality"
(Very concise, edit-focused, ~15 tokens)
```

### Example 4: Hunyuan Image

**Settings:**
```
target_platform: hunyuan_image
change_request: "add soft sunset lighting"
lighting: golden hour
```

**Output style:**
```
"[clear image description], with soft sunset lighting, 
golden hour atmosphere, high quality, realistic, detailed"
(Simple English, photorealistic focus)
```

## Workflow Examples

### Workflow 1: Style Transfer

**Goal:** Turn photo into painting

```
[Load Image: photo.jpg]
  ↓
[Image-to-Image Prompt Expander]
  - platform: flux
  - change: "convert to impressionist oil painting"
  - art_style: oil painting
  - mood: serene
  ↓
[Flux Image Gen]
```

### Workflow 2: Lighting Change

**Goal:** Change time of day

```
[Load Image: daytime.jpg]
  ↓
[Image-to-Image Prompt Expander]
  - platform: sd_xl
  - change: "make it golden hour sunset"
  - lighting: golden hour
  - color_palette: warm
  ↓
[SDXL Image Gen]
```

### Workflow 3: Background Replacement

**Goal:** Change background only

```
[Load Image: portrait.jpg]
  ↓
[Image-to-Image Prompt Expander]
  - platform: qwen_image_edit
  - change: "replace background with city skyline, keep person"
  - composition: centered
  ↓
[Qwen Edit Model]
```

### Workflow 4: Quality Enhancement

**Goal:** Just enhance, no changes

```
[Load Image: low_quality.jpg]
  ↓
[Image-to-Image Prompt Expander]
  - platform: flux
  - change: "" (empty - just enhance)
  - detail_level: highly detailed
  - quality_emphasis: True
  ↓
[Flux Image Gen]
```

## Platform Comparison

### When to Use Each Platform

**Use Flux when:**
- ✅ You want artistic/creative results
- ✅ Style transfer (painting, illustration, etc.)
- ✅ You have VRAM for quality (12GB+)
- ✅ Longer prompts work better

**Use SDXL when:**
- ✅ Standard img2img workflows
- ✅ You're familiar with SD ecosystem
- ✅ Token efficiency matters
- ✅ Strong negatives help

**Use Wan 2.2 when:**
- ✅ You want cinematic/technical quality
- ✅ Precise lighting control needed
- ✅ Professional composition important

**Use Hunyuan when:**
- ✅ Photorealistic results desired
- ✅ Asian subjects/aesthetics
- ✅ Simpler prompts work better
- ✅ Clarity over complexity

**Use Qwen Image when:**
- ✅ Balanced natural results
- ✅ Diverse cultural elements
- ✅ Versatile style handling

**Use Qwen Edit when:**
- ✅ Specific edits only
- ✅ Preserving most of image
- ✅ Minimal changes needed
- ✅ Fast iteration

## Tips for Best Results

### 1. Match Platform to Task

**Creative/Artistic → Flux**
```
change: "make it look like a Studio Ghibli scene"
platform: flux
```

**Realistic/Photo → Hunyuan or Qwen**
```
change: "enhance details, improve lighting"
platform: hunyuan_image
```

**Specific Edits → Qwen Edit**
```
change: "change shirt color to blue"
platform: qwen_image_edit
```

### 2. Be Specific with Changes

❌ Bad: "make it better"
✅ Good: "add dramatic rim lighting, increase contrast"

❌ Bad: "change the vibe"
✅ Good: "make it moody and mysterious with dark blue tones"

### 3. Use Aesthetic Controls

They adapt to each platform automatically:

**Flux:** Adds "in the style of..."
**SDXL:** Front-loads in prompt
**Qwen Edit:** Skips if irrelevant
**Hunyuan:** Simplifies terminology

### 4. Temperature by Platform

| Platform | Recommended Temp |
|----------|------------------|
| Flux | 0.7 (creative OK) |
| SDXL | 0.6 (precise) |
| Qwen Edit | 0.5 (very precise) |
| Others | 0.6-0.7 (balanced) |

### 5. Quality Emphasis

**Turn ON for:**
- Final renders
- Flux, SDXL
- When quality matters

**Turn OFF for:**
- Qwen Edit (conciseness > quality tokens)
- Quick iterations
- When prompt too long

## Outputs

1. **positive_prompt** - Platform-optimized prompt
2. **negative_prompt** - Platform-specific negatives
3. **image_description** - Vision model's analysis
4. **status** - Processing info

## Troubleshooting

### "Platform not working as expected"

**Check:**
- Using correct model for platform?
- Flux needs FLUX.1-dev/schnell
- SDXL needs Stable Diffusion XL
- etc.

**Fix:**
- Verify model matches platform
- Check platform documentation

### "Prompt too long/short"

**Flux/SDXL:** Node automatically optimizes
**Qwen Edit:** Should be very short (working as designed)
**Others:** Adjust via temperature and detail_level

### "Changes not applied correctly"

**For specific edits:**
- Use qwen_image_edit platform
- Be very explicit: "change X to Y"
- Lower temperature (0.5)

**For creative changes:**
- Use flux platform
- Be descriptive
- Use aesthetic controls

### "Vision model fails"

Same as Image-to-Video node:
- Check model loaded
- Verify it's vision-capable
- Test endpoint

## Comparison: Img2Vid vs Img2Img Nodes

| Feature | Image-to-Video | Image-to-Image |
|---------|----------------|----------------|
| Purpose | Animate images | Transform images |
| Focus | Motion, camera | Style, appearance |
| Platforms | Video models | Image models |
| Controls | Camera movement | Art style, lighting |
| Output | Video prompts | Image prompts |

**Use Img2Vid for:** Hunyuan Video, CogVideoX, etc.
**Use Img2Img for:** Flux, SDXL, Qwen, etc.

## Advanced: Two Models, One Node

**Optimal setup:**

```
Vision Model (Port 1234):
  - Llama-3.2-11B-Vision
  - Analyzes image
  
Expansion Model (Port 5000 or Ollama):
  - Llama-3.1-8B-Instruct
  - Formats prompt

In node:
  vision_endpoint: http://localhost:1234/v1
  expansion_endpoint: http://localhost:5000/v1
```

**Why?**
- Vision models are large (11B)
- Text models faster for formatting
- Better resource usage

## Summary

**Image-to-Image node gives you:**
- ✅ Platform-aware prompt generation
- ✅ Vision model image analysis
- ✅ 6 platforms optimized
- ✅ Advanced aesthetic controls
- ✅ Automatic format adaptation

**Supported platforms:**
1. Flux - Creative, artistic, detailed
2. SDXL - Token-optimized, standard
3. Wan 2.2 - Technical, cinematic
4. Hunyuan - Realistic, clear
5. Qwen Image - Balanced, versatile
6. Qwen Edit - Concise, edit-focused

**Each gets prompts formatted the way IT works best!**

---

**Ready to transform images with AI!**

Load vision model → Select platform → Describe changes → Generate!
