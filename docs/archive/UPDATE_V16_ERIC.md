# Version 1.6 Update - Eric's Prompt Enhancers

## What's New

### 🎯 Rebranded as "Eric's Prompt Enhancers"

All nodes now appear under **"Eric Prompt Enhancers"** category in ComfyUI for easy access!

### 🆕 Text-to-Image Prompt Enhancer Node

A powerful new node for advanced text-to-image prompt enhancement with multi-platform support!

**Supported Platforms:**
1. **Flux** - Natural, artistic, detailed (75-150 tokens)
2. **Stable Diffusion XL** - Token-optimized, front-loaded (40-75 tokens)
3. **Pony Diffusion** - Booru tags, score system (40-80 tokens) ⭐ NEW
4. **Illustrious XL** - Anime booru tags, detailed (50-100 tokens) ⭐ NEW
5. **Chroma (Meissonic)** - Complex scenes, natural (100-200 tokens) ⭐ NEW
6. **Qwen Image** - Balanced, versatile (50-100 tokens)
7. **Qwen Image Edit** - Concise, edit-focused (20-50 tokens)
8. **Wan Image** - Technical, cinematic (60-120 tokens) ⭐ NEW

## Key Features

### Advanced Aesthetic Controls

**Camera & Composition:**
- Camera angles (eye level, low angle, bird's eye, etc.)
- Composition styles (rule of thirds, golden ratio, etc.)

**Lighting:**
- Lighting sources (natural, studio, golden hour, moonlight, etc.)
- Lighting quality (soft diffused, dramatic, volumetric, etc.)

**Time & Weather:**
- Time of day (dawn, noon, golden hour, night, etc.)
- Weather conditions (clear, foggy, rainy, snowy, etc.)

**Style & Mood:**
- Art styles (photorealistic, anime, oil painting, etc.)
- Color moods (vibrant, muted, warm, cool, etc.)
- Detail levels (standard, highly detailed, minimalist, etc.)

### Wildcard Random Options

Set any control to "random" for automatic variety:
- Random camera angles
- Random lighting combinations
- Random weather conditions
- Random color moods

Perfect for batch generation with variety!

### Optional Reference Images

- Supports 1-2 reference images
- Images noted for context
- Can guide enhancement direction

### Platform-Specific Optimization

Each platform gets prompts formatted exactly as it works best:

**Flux Example:**
```
"masterpiece, best quality, highly detailed photograph of a woman 
in a garden, golden hour lighting, in the style of Annie Leibovitz"
```

**Pony Example:**
```
"score_9, score_8_up, score_7_up, 1girl, long_hair, detailed_face, 
garden, golden_hour, photorealistic, best_quality"
```

**SDXL Example:**
```
"masterpiece, best quality, highly detailed, woman in garden, 
golden hour, professional photography, sharp focus"
```

## Platform-Specific Details

### Pony Diffusion ⭐ NEW

**Critical Requirements:**
- ✅ MUST start with: `score_9, score_8_up, score_7_up`
- ✅ Use underscores (not spaces): `long_hair` not "long hair"
- ✅ Danbooru tag format
- ✅ Character count: `1girl`, `2boys`, etc.

**Negative MUST include:**
- `score_6, score_5, score_4, worst quality, low quality`

### Illustrious XL ⭐ NEW

**Requirements:**
- ✅ Start with: `masterpiece, best quality`
- ✅ Use underscores in tags
- ✅ Detailed character descriptions
- Good for anime, detailed characters

### Chroma (Meissonic) ⭐ NEW

**Strengths:**
- Handles complex scenes with multiple subjects
- Natural language, detailed (100-200 tokens)
- Excellent for compositional complexity
- Spatial relationships well understood

### Wan Image ⭐ NEW

**Style:**
- Technical cinematography terms
- Structured: subject, setting, lighting, composition
- Professional photography language
- Specific lighting types

## File Structure

### New Files Created:
- ✅ `text_to_image_node.py` - Main text-to-image enhancer node
- ✅ `TXT2IMG_GUIDE.md` - Complete documentation
- ✅ `UPDATE_V16_ERIC.md` - This file

### Updated Files:
- ✅ `__init__.py` - Added new node, rebranded all nodes
- ✅ `platforms.py` - Added 4 new platforms (Pony, Illustrious, Chroma, Wan Image)
- ✅ `prompt_expander_node.py` - Updated category
- ✅ `prompt_expander_node_advanced.py` - Updated category
- ✅ `image_to_video_node.py` - Updated category
- ✅ `image_to_image_node.py` - Updated category

## All Nodes Now Available

Under **"Eric Prompt Enhancers"** category:

1. **Video Prompt Expander** - Simple video prompt expansion
2. **Video Prompt Expander (Advanced)** - Granular video controls
3. **Image-to-Video Prompt Expander** - Vision + motion expansion
4. **Image-to-Image Prompt Expander** - Platform-aware img2img
5. **Text-to-Image Prompt Enhancer** ⭐ NEW - Advanced multi-platform txt2img

## Quick Start

### Text-to-Image Enhancer

1. Add node: `Eric Prompt Enhancers → Text-to-Image Prompt Enhancer`

2. Enter basic prompt:
   ```
   "a woman in a garden"
   ```

3. Select platform:
   - flux, sd_xl, pony, illustrious, chroma, etc.

4. Set controls (optional):
   - Camera angle
   - Lighting
   - Time of day
   - Art style
   - etc.

5. Connect outputs:
   ```
   positive_prompt → CLIP Text Encode → KSampler
   negative_prompt → CLIP Text Encode → KSampler
   ```

### Platform Selection Guide

| Your Image Model | Select Platform |
|------------------|-----------------|
| FLUX.1-dev/schnell | flux |
| Stable Diffusion XL | sd_xl |
| Pony Diffusion | pony |
| Illustrious XL | illustrious |
| Meissonic/MeissonFlow | chroma |
| Qwen Image | qwen_image |
| Wan models | wan_image |

## Example Workflows

### Example 1: Flux Photorealistic

```
Text-to-Image Enhancer:
  - text_prompt: "portrait of a woman"
  - target_platform: flux
  - art_style: photorealistic
  - lighting_source: golden hour sun
  - camera_angle: eye level
  - composition: rule of thirds
  
→ positive_prompt: "masterpiece, best quality, highly detailed 
   professional photograph of a woman, golden hour sunlight, 
   shot at eye level, rule of thirds composition..."
```

### Example 2: Pony Anime Character

```
Text-to-Image Enhancer:
  - text_prompt: "magical girl with blue hair"
  - target_platform: pony
  - art_style: anime
  - time_of_day: night
  - positive_keywords: "magical_staff, sparkles"
  
→ positive_prompt: "score_9, score_8_up, score_7_up, 1girl, 
   magical_girl, long_blue_hair, magical_staff, sparkles, 
   night, detailed_face, anime_style, best_quality..."

→ negative_prompt: "score_6, score_5, score_4, worst quality, 
   low quality, bad anatomy, sketch, jpeg artifacts..."
```

### Example 3: Chroma Complex Scene

```
Text-to-Image Enhancer:
  - text_prompt: "busy coffee shop"
  - target_platform: chroma
  - time_of_day: morning
  - lighting_source: window light
  - composition: dynamic
  
→ positive_prompt: "high quality, intricate, masterpiece: 
   A bustling coffee shop interior on a sunny morning, 
   with warm natural window light streaming through large 
   windows, baristas working, customers at tables, plants 
   hanging from ceiling, dynamic composition with multiple 
   focal points..."
```

## Platform Token Optimization

The node automatically optimizes token usage per platform:

| Platform | Target Length | Auto-Handled |
|----------|---------------|--------------|
| Flux | 75-150 tokens | ✅ |
| SDXL | 40-75 tokens | ✅ |
| Pony | 40-80 tokens | ✅ |
| Illustrious | 50-100 tokens | ✅ |
| Chroma | 100-200 tokens | ✅ |
| Qwen Image | 50-100 tokens | ✅ |
| Qwen Edit | 20-50 tokens | ✅ |
| Wan Image | 60-120 tokens | ✅ |

## Tips & Best Practices

### General Tips

1. **Match Your Model**: Always select the correct platform
2. **Start Simple**: Let the node enhance basic prompts
3. **Use Auto**: "auto" settings let LLM decide
4. **Quality Emphasis**: Keep ON for best results
5. **Negative Prompts**: Always connect negative output

### Platform-Specific Tips

**Pony & Illustrious:**
- ✅ MUST use correct format (scores, tags, underscores)
- Include character count (1girl, 1boy, etc.)
- Use danbooru tag style

**Flux & Chroma:**
- Natural language works best
- More verbose = better
- Artistic references encouraged

**SDXL:**
- Keep concise (under 75 tokens)
- Front-load important concepts
- Quality tokens at start

**Wan Image:**
- Technical terminology
- Think cinematography
- Structured descriptions

### Wildcard Random Usage

Great for variety in batch generation:

```
camera_angle: random
lighting_source: random
weather: random
color_mood: random
```

Each generation gets different combinations!

## Troubleshooting

### Node Not Appearing
- ✅ Restart ComfyUI completely
- ✅ Check console for Python errors
- ✅ Look under "Eric Prompt Enhancers" category

### LLM Connection Issues
- ✅ Verify LM Studio/Ollama is running
- ✅ Check API endpoint (default: `http://localhost:1234/v1`)
- ✅ Test with simple prompt first

### Poor Results
- ✅ Verify correct platform selected
- ✅ Check if your image model matches platform setting
- ✅ Try adjusting temperature (0.6-0.8 recommended)
- ✅ Add positive/negative keywords
- ✅ Set specific controls (don't leave all on "auto")

### Pony/Illustrious Not Working
- ✅ Check output includes score tags
- ✅ Verify underscores in tags
- ✅ Make sure negative has required score_6, score_5, score_4

## Documentation

**Complete guides available:**

- 📘 `README.md` - Overview and installation
- 📘 `TXT2IMG_GUIDE.md` - Complete text-to-image guide with examples
- 📘 `IMG2IMG_GUIDE.md` - Image-to-image guide
- 📘 `CONFIGURATION.md` - LLM setup and configuration
- 📘 `LM_STUDIO_SETUP.md` - LM Studio setup guide

## Next Steps

1. **Restart ComfyUI** to load new nodes
2. **Find nodes** under "Eric Prompt Enhancers"
3. **Try each platform** to see differences
4. **Experiment with controls** to understand effects
5. **Use wildcards** for variety
6. **Read TXT2IMG_GUIDE.md** for detailed examples

---

**Enjoy your new multi-platform prompt enhancement capabilities!**

All nodes are now conveniently organized under "Eric Prompt Enhancers" for easy access.
