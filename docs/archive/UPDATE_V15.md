# Version 1.5 Update - Image-to-Image Node with Platform Support

## What's New

### 🆕 Image-to-Image Prompt Expander Node

A platform-aware node that generates optimized prompts for different image generation models!

**Supported Platforms:**
1. **Flux** (FLUX.1-dev/schnell) - Natural, artistic, detailed
2. **Stable Diffusion XL** - Token-optimized, front-loaded
3. **Wan 2.2** (adapted) - Technical, cinematic terms
4. **Hunyuan Image** - Clear, realistic, simple English
5. **Qwen Image** - Balanced, versatile, natural
6. **Qwen Image Edit** - Concise, edit-focused

## Key Features

### 1. Platform-Specific Formatting

Each platform gets prompts formatted THE WAY IT WORKS BEST:

**Flux Example:**
```
Input: "make it look like oil painting"
Output: "masterpiece, best quality, [image], rendered as 
         oil painting with rich textures, in style of..."
(Natural, 75-150 tokens, artistic)
```

**Qwen Edit Example:**
```
Input: "change background to forest"
Output: "replace background with forest, keep subject, 
         seamless, natural"
(Very concise, 20-50 tokens, edit-focused)
```

### 2. Vision Model Integration

- Llama 3.2 Vision, LLaVA support
- AI describes your image
- You just say what to change

### 3. Advanced Aesthetic Controls

- **Art Style**: photorealistic, digital art, painting, anime, etc.
- **Lighting**: natural, studio, dramatic, golden hour, etc.
- **Composition**: rule of thirds, centered, symmetrical, etc.
- **Color Palette**: vibrant, muted, warm, cool, etc.
- **Mood**: serene, dramatic, mysterious, etc.
- **Detail Level**: standard, highly detailed, minimalist, etc.

### 4. Smart Adaptation

Controls adapt to each platform:
- Flux: Adds "in the style of..."
- SDXL: Front-loads quality tokens
- Qwen Edit: Focuses on changes only
- Hunyuan: Simplifies language

## Quick Setup

### 1. Files Created

- ✅ `platforms.py` - Platform configurations
- ✅ `img2img_expansion_engine.py` - Platform-aware expansion
- ✅ `image_to_image_node.py` - Main node
- ✅ `__init__.py` - Updated registration
- ✅ `IMG2IMG_GUIDE.md` - Complete documentation

### 2. Workflow

```
[Load Image] 
  ↓
[Image-to-Image Prompt Expander]
  - Select platform (flux, sd_xl, etc.)
  - Describe changes
  - Set aesthetic controls
  ↓
[Your Image Gen Model]
```

### 3. Example Use Cases

**Style Transfer:**
```
Platform: flux
Change: "convert to impressionist painting"
Art Style: oil painting
→ Artistic, detailed Flux prompt
```

**Lighting Change:**
```
Platform: sd_xl
Change: "add golden hour sunset"
Lighting: golden hour
→ Token-optimized SDXL prompt
```

**Quick Edit:**
```
Platform: qwen_image_edit
Change: "change shirt to red"
→ Concise edit instruction
```

## Platform Comparison

| Platform | Best For | Token Count | Style |
|----------|----------|-------------|-------|
| Flux | Artistic, creative | 75-150 | Natural, detailed |
| SDXL | Standard workflows | 40-75 | Token-optimized |
| Wan 2.2 | Cinematic quality | 50-100 | Technical, structured |
| Hunyuan | Photorealistic | 40-80 | Clear, simple |
| Qwen Image | Versatile | 50-100 | Balanced, natural |
| Qwen Edit | Specific edits | 20-50 | Concise, focused |

## Node Outputs

1. **positive_prompt** - Platform-optimized prompt
2. **negative_prompt** - Platform-specific negatives  
3. **image_description** - Vision analysis
4. **status** - Processing info

## Integration with Existing Nodes

**You now have 4 nodes:**

1. **AI Video Prompt Expander** - Text-to-video, simple
2. **AI Video Prompt Expander (Advanced)** - Text-to-video, detailed controls
3. **Image-to-Video Prompt Expander** - Animate images
4. **Image-to-Image Prompt Expander** - Transform images (NEW!)

**All in:** `Add Node → video/prompting` or `image/prompting`

## Restart Required

**YES** - Restart ComfyUI to see the new node

## Quick Test

### Test Platform Optimization

**Try this with Flux:**
```
Load an image
Platform: flux
Change: "make it look like anime art"
Art Style: anime
Generate
→ Should get natural, artistic Flux prompt
```

**Try same image with Qwen Edit:**
```
Same image
Platform: qwen_image_edit  
Change: "make it look like anime art"
Generate
→ Should get very concise edit instruction
```

**See the difference!** Same request, different formatting per platform.

## Version History

- **v1.5** - Image-to-Image node with 6 platforms
- **v1.4** - Image-to-Video node with vision
- **v1.3** - Fixed random, added wildcards
- **v1.2** - Fixed auto mode
- **v1.1** - Advanced node
- **v1.0** - Initial release

## Summary

**v1.5 brings:**
- 🆕 Image-to-Image node
- 🆕 6 platform configurations (Flux, SDXL, Wan, Hunyuan, Qwen, Qwen Edit)
- 🆕 Platform-specific prompt formatting
- 🆕 Advanced aesthetic controls for images
- 🆕 Vision model integration for img2img
- ✅ All previous features intact

**Key innovation:** Same change request → Different prompt format per platform → Optimal results!

---

**Restart ComfyUI and transform images with platform-optimized prompts!**

See `IMG2IMG_GUIDE.md` for complete documentation.
