# Text-to-Image Prompt Enhancer - Complete Guide

## Overview

The **Text-to-Image Prompt Enhancer** is an advanced multi-platform node that transforms simple text prompts into platform-optimized, detailed prompts for image generation models.

### Supported Platforms

1. **Flux (FLUX.1)** - Natural language, artistic, detailed (75-150 tokens)
2. **Stable Diffusion XL** - Token-optimized, front-loaded quality (40-75 tokens)
3. **Pony Diffusion** - Booru tags, score system, structured (40-80 tokens)
4. **Illustrious XL** - Anime-focused, booru tags, detailed (50-100 tokens)
5. **Chroma (Meissonic)** - Complex scenes, natural language (100-200 tokens)
6. **Qwen Image** - Balanced, versatile, natural (50-100 tokens)
7. **Qwen Image Edit** - Concise, edit-focused (20-50 tokens)
8. **Wan Image** - Technical, cinematic, structured (60-120 tokens)

## Why Platform-Specific?

Different models respond best to different prompting styles:

| Platform | Format | Example |
|----------|--------|---------|
| **Flux** | Natural, artistic | "a masterpiece photograph of a woman in a garden, golden hour lighting, in the style of Annie Leibovitz" |
| **SDXL** | Front-loaded quality | "masterpiece, best quality, highly detailed, woman in garden, golden hour, professional photography" |
| **Pony** | Booru tags + scores | "score_9, score_8_up, score_7_up, 1girl, long_hair, garden, golden_hour, photorealistic" |
| **Illustrious** | Anime booru tags | "masterpiece, best quality, 1girl, detailed_face, long_flowing_hair, garden_background, golden_hour_lighting" |
| **Chroma** | Complex natural | "A detailed scene showing a woman with flowing auburn hair standing in a lush garden filled with roses and lavender, bathed in warm golden hour sunlight..." |
| **Wan Image** | Technical cinematic | "Medium shot, woman in garden, soft lighting, golden hour, rule of thirds composition, professional photography, warm color grading" |

## Features

### Core Capabilities
- ✅ 8 platform-specific prompt formats
- ✅ Advanced aesthetic controls (camera, lighting, weather, etc.)
- ✅ Wildcard random options for variety
- ✅ Optional reference image support (1-2 images)
- ✅ Custom keyword integration (LoRA triggers, etc.)
- ✅ Platform-specific negative prompts
- ✅ File export with metadata

### Control Options

#### Camera & Composition
- **Camera Angle**: eye level, low angle, high angle, dutch angle, bird's eye, etc.
- **Composition**: rule of thirds, centered, symmetrical, golden ratio, etc.

#### Lighting
- **Lighting Source**: natural sunlight, studio, golden hour, moonlight, neon, etc.
- **Lighting Quality**: soft diffused, hard dramatic, high contrast, volumetric, etc.

#### Time & Atmosphere
- **Time of Day**: dawn, morning, noon, golden hour, dusk, night, etc.
- **Weather**: clear, cloudy, misty, foggy, rainy, snowy, etc.

#### Style & Color
- **Art Style**: photorealistic, digital art, oil painting, anime, 3D render, etc.
- **Color Mood**: vibrant, muted, warm tones, cool tones, pastel, high contrast, etc.

#### Quality
- **Detail Level**: standard, highly detailed, intricate, simplified, minimalist
- **Quality Emphasis**: Adds platform-specific quality tokens

### Wildcard Options

Set any control to "random" for variety:
- Random camera angles
- Random lighting combinations
- Random weather conditions
- Random color moods
- Random compositions

Perfect for generating varied outputs!

## Platform-Specific Details

### Flux (FLUX.1-dev/schnell)

**Best For**: Natural language prompts, artistic styles, photography

**Format**: Natural, detailed descriptions (75-150 tokens)

**Prompting Tips**:
- Use natural language
- "in the style of [artist/style]" works well
- Photography terms (bokeh, depth of field, etc.)
- Quality descriptors important

**Example**:
```
Input: "a woman reading a book"
Settings: art_style=photorealistic, lighting_source=window light

Output: "masterpiece, best quality, highly detailed photograph of a 
woman reading a book by a window, soft natural window light creating 
gentle shadows, professional photography, shallow depth of field, 
in the style of Steve McCurry, warm tones, contemplative mood, 8k uhd"
```

---

### Stable Diffusion XL

**Best For**: General purpose, realistic and artistic images

**Format**: Token-optimized, front-loaded (40-75 tokens max)

**Prompting Tips**:
- Front-load important concepts
- Quality tokens at start
- Keep under 75 tokens
- Can use natural language OR tags
- Negative prompts very important

**Example**:
```
Input: "cyberpunk city street at night"
Settings: lighting_source=neon lights, color_mood=high contrast

Output: "masterpiece, best quality, highly detailed, cyberpunk city 
street at night, neon lights, high contrast, wet pavement reflections, 
professional photography, sharp focus, intricate details"
```

---

### Pony Diffusion

**Best For**: Anime, furry, stylized characters

**Format**: Booru tags with score system (40-80 tokens)

**CRITICAL Requirements**:
- ✅ **MUST start with**: `score_9, score_8_up, score_7_up`
- ✅ Use underscores instead of spaces
- ✅ Danbooru tag format
- ✅ Character count tags (1girl, 1boy, etc.)

**Prompting Tips**:
- Tags, not sentences
- Underscores: `long_hair` not "long hair"
- Character appearance tags
- Quality tags at beginning
- Negative: MUST include `score_6, score_5, score_4`

**Example**:
```
Input: "anime girl with fox ears"
Settings: art_style=anime, time_of_day=sunset

Output: "score_9, score_8_up, score_7_up, 1girl, fox_ears, animal_ears, 
long_hair, detailed_face, sunset, orange_sky, warm_lighting, detailed, 
best_quality, anime_style"

Negative: "score_6, score_5, score_4, worst quality, low quality, 
bad anatomy, sketch, jpeg artifacts, blurry"
```

---

### Illustrious XL

**Best For**: High-quality anime images, detailed characters

**Format**: Booru tags, detailed (50-100 tokens)

**CRITICAL Requirements**:
- ✅ Start with: `masterpiece, best quality`
- ✅ Use underscores in tags
- ✅ Character description tags
- ✅ Detailed appearance

**Prompting Tips**:
- More detailed than Pony
- Character appearance very detailed
- Clothing and accessory tags
- Background and atmosphere tags
- Good with complex character designs

**Example**:
```
Input: "elegant elf warrior"
Settings: art_style=anime, lighting_quality=soft diffused

Output: "masterpiece, best quality, very aesthetic, 1girl, elf, 
pointed_ears, long_flowing_silver_hair, detailed_face, elegant_armor, 
ornate_sword, soft_lighting, detailed_background, forest_setting, 
intricate_details, official_art"
```

---

### Chroma (Meissonic/MeissonFlow)

**Best For**: Complex scenes, multiple subjects, detailed compositions

**Format**: Natural language, detailed (100-200 tokens)

**Prompting Tips**:
- Can handle complex scenes
- Multiple subjects work well
- Describe spatial relationships
- Compositional details important
- Natural, flowing descriptions

**Example**:
```
Input: "marketplace scene"
Settings: time_of_day=afternoon, composition=dynamic

Output: "high quality, intricate, masterpiece: A bustling marketplace 
scene in the warm afternoon light, with vendors arranging colorful 
fruits and vegetables in wooden crates, customers browsing the stalls, 
hanging fabric awnings creating dappled shadows, dynamic composition 
with multiple focal points, people in various poses and activities, 
detailed architecture in the background, warm color palette, 
professional photography, rich textures and details throughout"
```

---

### Qwen Image

**Best For**: Versatile, natural language, diverse styles

**Format**: Balanced natural language (50-100 tokens)

**Prompting Tips**:
- Natural conversational descriptions
- Good with various art styles
- Handles cultural elements well
- Balanced detail level
- Not too technical

**Example**:
```
Input: "traditional tea ceremony"
Settings: art_style=photorealistic, lighting_quality=soft diffused

Output: "high quality, detailed, professional photograph of a traditional 
tea ceremony, soft diffused lighting, elegant kimono, peaceful atmosphere, 
tatami mat flooring, paper screen windows, refined composition, cultural 
authenticity, warm tones, beautiful details, serene mood"
```

---

### Qwen Image Edit

**Best For**: Image editing, modifications, changes

**Format**: Very concise, edit-focused (20-50 tokens)

**Prompting Tips**:
- VERY brief
- Focus on what changes
- Use change language: "change X to Y", "add Z"
- Don't re-describe unchanged parts
- Include preservation hints if needed

**Example**:
```
Input: "change hair to red and add sunset background"
Settings: quality_emphasis=true

Output: "change hair color to red, replace background with sunset scene, 
keep subject and composition, seamless, natural, high quality"
```

---

### Wan Image

**Best For**: Cinematic quality, technical photography

**Format**: Technical cinematographic (60-120 tokens)

**Prompting Tips**:
- Technical cinematography terms
- Structured: subject, setting, lighting, composition
- Specific lighting types (soft, hard, edge, rim)
- Composition rules
- Professional photography language

**Example**:
```
Input: "portrait of a musician"
Settings: lighting_source=studio lighting, composition=rule of thirds

Output: "high quality, professional, Medium shot portrait of a musician, 
studio lighting setup, three-point lighting, soft key light, edge lighting 
on the subject, rule of thirds composition, shallow depth of field, 
sharp focus on subject, blurred background, warm color grading, 
cinematic quality, detailed, professional photography"
```

---

## Quick Start

### Basic Usage

1. **Add the node**: `Eric Prompt Enhancers → Text-to-Image Prompt Enhancer`

2. **Enter your prompt**: Simple description of what you want

3. **Choose platform**: Match your image generation model

4. **Set controls** (or leave as "auto"):
   - Camera angle
   - Lighting
   - Time of day
   - Art style
   - etc.

5. **Generate**: Connect positive/negative outputs to your image gen node

### Example Workflow

```
[Text-to-Image Prompt Enhancer]
  - text_prompt: "a cat in a garden"
  - target_platform: flux
  - lighting_source: golden hour sun
  - composition: rule of thirds
  ↓
[CLIP Text Encode] ← positive_prompt
[CLIP Text Encode] ← negative_prompt
  ↓
[KSampler]
```

## Advanced Features

### Reference Images

Add 1-2 reference images (optional):
- Connect images to `reference_image_1` and/or `reference_image_2`
- Node will note that references are provided
- LLM can consider them in enhancement

### Custom Keywords

**Positive Keywords**:
- LoRA triggers
- Specific terms to include
- Character names
- Special requirements

**Negative Keywords**:
- Things to avoid
- Unwanted elements
- Quality issues to prevent

**Example**:
```
positive_keywords: "ohwx person, cinematic lighting LoRA"
negative_keywords: "cartoon, illustration, painting"
```

### Wildcard Random

Set any control to "random" for variety:

```
camera_angle: random
lighting_source: random
weather: random
color_mood: random
```

Each generation will pick random values!

### File Saving

Enable `save_to_file`:
- Saves enhanced prompts to disk
- Includes all settings and metadata
- Organized with timestamps
- Great for tracking what works

## Tips & Best Practices

### General Tips

1. **Match Your Model**: Always set the correct platform for your image gen model
2. **Start Simple**: Begin with basic prompts, let the node enhance them
3. **Use Auto**: "auto" settings let the LLM decide what fits best
4. **Quality Emphasis**: Usually keep this ON for best results
5. **Negative Prompts**: Always connect the negative output

### Platform-Specific Tips

**For Pony & Illustrious**:
- These NEED specific formats (scores, tags)
- Don't skip the required tokens
- Use underscores in multi-word concepts
- Include character count (1girl, 2boys, etc.)

**For Flux & Chroma**:
- More verbose is better
- Natural language works great
- Artistic references encouraged
- Detail your vision

**For SDXL**:
- Keep it concise (under 75 tokens)
- Front-load important concepts
- Quality tokens at start matter

**For Wan Image**:
- Technical terms work best
- Think like a cinematographer
- Lighting types matter
- Composition rules important

### Getting Better Results

1. **Be Specific**: "woman" → "young woman with curly hair"
2. **Set Key Controls**: At minimum, set lighting or art style
3. **Use Positive Keywords**: For LoRAs, specific styles, etc.
4. **Check Negatives**: Platform negatives are auto-generated but add your own
5. **Iterate**: Try different control combinations

## Troubleshooting

### Node Not Appearing
- Restart ComfyUI
- Check for Python errors in console
- Verify `__init__.py` imports correctly

### LLM Errors
- Check LM Studio/Ollama is running
- Verify API endpoint is correct
- Try a different model
- Check console for detailed errors

### Poor Results
- Wrong platform selected?
- Check if your model matches the platform
- Try adjusting temperature (0.6-0.8 recommended)
- Add more specific controls
- Add positive/negative keywords

### Output Too Short/Long
- Each platform has optimal length
- The node handles this automatically
- If still wrong, check your LLM model

## Examples

### Example 1: Flux Photorealistic Portrait

```
text_prompt: "a woman with red hair"
target_platform: flux
art_style: photorealistic
lighting_source: golden hour sun
camera_angle: eye level
composition: rule of thirds
quality_emphasis: true

Output: "masterpiece, best quality, highly detailed professional 
photograph of a woman with flowing red hair, golden hour sunlight 
creating warm highlights, shot at eye level, rule of thirds composition, 
shallow depth of field, in the style of Peter Lindbergh, photorealistic, 
8k uhd, stunning, beautiful, professional photography"
```

### Example 2: Pony Anime Character

```
text_prompt: "magical girl with blue hair"
target_platform: pony
art_style: anime
time_of_day: night
lighting_source: moonlight
positive_keywords: "magical_staff, sparkles"

Output: "score_9, score_8_up, score_7_up, 1girl, magical_girl, 
long_blue_hair, magical_staff, sparkles, night, moonlight, detailed_face, 
anime_style, best_quality, very_aesthetic, magical_atmosphere"

Negative: "score_6, score_5, score_4, worst quality, low quality, 
bad anatomy, sketch, jpeg artifacts, blurry, simple background"
```

### Example 3: Chroma Complex Scene

```
text_prompt: "busy coffee shop interior"
target_platform: chroma
time_of_day: morning
lighting_source: window light
weather: sunny
composition: dynamic
detail_level: highly detailed

Output: "high quality, intricate, masterpiece, exceptional composition: 
A bustling coffee shop interior on a sunny morning, with warm natural 
window light streaming through large street-facing windows creating 
beautiful light patterns on the wooden floor, baristas working behind 
an antique espresso machine, customers at various tables reading and 
conversing, plants hanging from the ceiling, vintage posters on brick 
walls, dynamic composition with multiple focal points and layers of 
depth, rich textures throughout, warm inviting atmosphere, highly 
detailed, professional photography quality"
```

### Example 4: SDXL Quick Generation

```
text_prompt: "cyberpunk street"
target_platform: sd_xl
lighting_source: neon lights
time_of_day: night
color_mood: high contrast
quality_emphasis: true

Output: "masterpiece, best quality, highly detailed, cyberpunk street 
at night, neon lights, high contrast, wet reflections, rain, futuristic, 
professional, sharp focus, intricate"
```

## FAQ

**Q: Do I need all the settings?**  
A: No! Set to "auto" and the LLM will decide. Or set "none" to omit.

**Q: What's the difference between "auto" and "random"?**  
A: "auto" = LLM decides what fits, "random" = randomly picks from presets

**Q: Can I use multiple platforms?**  
A: Not simultaneously. Choose one platform per generation.

**Q: Do reference images work?**  
A: They're noted but not analyzed (vision model optional future feature)

**Q: Which platform for my model?**  
A: Match your image model: SDXL model = sd_xl, Pony model = pony, etc.

**Q: Why are Pony prompts so different?**  
A: Pony requires specific booru tag format with score system

**Q: Can I edit the enhanced prompt?**  
A: Yes! Output is text - edit before sending to image gen

**Q: Temperature recommendations?**  
A: 0.6-0.8 for consistent, 0.8-1.2 for creative variations

---

## Next Steps

1. **Try Each Platform**: Generate same prompt on different platforms
2. **Experiment with Controls**: See how each control affects output
3. **Save Your Best**: Use file saving to track successful prompts
4. **Mix with LoRAs**: Add LoRA triggers to positive keywords
5. **Create Variations**: Use random options for variety

**Enjoy creating amazing images with platform-optimized prompts!**
