# Reference Mode Complete Guide

## How Reference Modes Work

When you attach a reference image to the **Advanced Video Prompt Expander** node, the system follows this flow:

### The Complete Pipeline

```
1. Reference Image (your uploaded image)
   ↓
2. Qwen3-VL Analysis (mode-specific prompt)
   ↓
3. Mode Instruction (tells LLM how to use analysis)
   ↓
4. Combined with Your Prompt (from GUI)
   ↓
5. LM Studio Expansion (generates final video prompt)
```

---

## All 7 Reference Modes Explained

### 1. recreate_exact (Default)

**When to use:** Animating existing artwork, maintaining exact appearance

**Qwen3-VL analyzes:**
- ✅ Main subject: facial features, expression, hair, body, pose, clothing
- ✅ Exact outfit: style, color, material, accessories
- ✅ Environment: location, background elements, spatial layout
- ✅ Lighting: direction, quality, color temperature, shadows
- ✅ Color palette: dominant colors, saturation
- ✅ Visual style: artistic style, rendering, mood
- ✅ Camera framing and composition
- ✅ Props, objects, environmental details

**LLM Instruction:**
```
[REFERENCE MODE: RECREATE EXACT]
Use the provided image as the exact character and costume reference.
Keep the same face, hair, outfit, lighting, and overall aesthetic.
Animate this character/scene without changing identity or appearance.
Match the visual style, mood, and composition of the reference image.
```

**Example:**
- Image: Character in medieval armor
- Your prompt: "walking through a forest"
- Result: Same character, same armor, walking through forest

---

### 2. subject_only

**When to use:** Place character in completely new environment/lighting

**Qwen3-VL analyzes:**
- ✅ Facial features: face shape, eyes, expression, skin tone
- ✅ Hair: style, length, color, texture
- ✅ Body type: build, proportions, posture
- ✅ Current clothing (for reference)
- ✅ Personality traits in expression
- ✅ Age, gender, distinctive features
- ❌ Background (ignored)
- ❌ Environment (ignored)
- ❌ Lighting (ignored)

**LLM Instruction:**
```
[REFERENCE MODE: SUBJECT ONLY]
Preserve ONLY the subject's face, body identity, and core appearance.
Ignore the original background, lighting, and environment.
Place this character in the new scene with new lighting and atmosphere.
Keep character identity consistent but change everything else.
```

**Example:**
- Image: Woman in studio with soft lighting
- Your prompt: "in a cyberpunk alley at night"
- Result: Same woman, new outfit, cyberpunk environment, neon lighting

---

### 3. style_only

**When to use:** Apply artistic style to new content

**Qwen3-VL analyzes:**
- ✅ Artistic style: photorealism, illustration, anime, painterly
- ✅ Lighting style: quality, mood, direction, color temperature
- ✅ Color grading: palette, saturation, contrast, toning
- ✅ Atmospheric treatment: haze, clarity, depth, mood
- ✅ Cinematographic style: film look, vintage, modern
- ✅ Visual effects: grain, blur, sharpness, filters
- ✅ Overall mood and emotional tone
- ❌ Subject identity (ignored)
- ❌ Character (ignored)
- ❌ Scene content (ignored)

**LLM Instruction:**
```
[REFERENCE MODE: STYLE TRANSFER]
Match the lighting, color palette, visual aesthetic, and cinematic mood.
Create a completely new subject, character, and scene.
Apply the same artistic style, color grading, and atmospheric treatment.
```

**Example:**
- Image: Film noir scene (high contrast, dramatic shadows)
- Your prompt: "a detective investigating a crime scene"
- Result: New detective, new scene, same noir lighting/style

---

### 4. color_palette_only

**When to use:** Match color mood, different subject

**Qwen3-VL analyzes:**
- ✅ Dominant colors (3-5 main colors with percentages)
- ✅ Accent colors
- ✅ Color relationships: complementary, analogous, triadic
- ✅ Saturation level: vivid, muted, desaturated
- ✅ Value range: bright, dark, balanced
- ✅ Color temperature: warm, cool, neutral
- ✅ Color mood: emotional tone
- ❌ Subjects (ignored)
- ❌ Composition (ignored)
- ❌ Lighting style (ignored)

**LLM Instruction:**
```
[REFERENCE MODE: COLOR PALETTE ONLY]
Extract and apply the dominant color scheme from the reference image.
Use the same hues, saturation levels, and color relationships.
Create an entirely new subject and scene.
Maintain color harmony with the reference palette.
```

**Example:**
- Image: Sunset landscape (warm oranges, purples, magentas)
- Your prompt: "a spaceship landing on an alien planet"
- Result: Spaceship scene using sunset color palette

---

### 5. action_only

**When to use:** Recreate pose/motion with different character

**Qwen3-VL analyzes:**
- ✅ Body position: stance, posture, weight distribution
- ✅ Arm positions and hand gestures
- ✅ Leg positions and foot placement
- ✅ Head position and tilt
- ✅ Movement direction
- ✅ Energy level: static, dynamic, tense, relaxed
- ✅ Action being performed
- ✅ Physical dynamics and balance
- ❌ Character identity (ignored)
- ❌ Clothing (ignored)
- ❌ Environment (ignored)

**LLM Instruction:**
```
[REFERENCE MODE: ACTION/POSE ONLY]
Recreate the pose, gesture, body language, and action/movement.
Change the character identity, environment, lighting, costume, and visual style.
Keep only the physical positioning and motion dynamic.
```

**Example:**
- Image: Dancer mid-leap
- Your prompt: "a warrior in battle armor"
- Result: Warrior performing the same leap pose

---

### 6. character_remix

**When to use:** Same character, different story/scenario

**Qwen3-VL analyzes:**
- ✅ Core identity markers: distinctive facial features, expression
- ✅ Character archetype: hero, villain, mystic, warrior
- ✅ Key personality traits in pose/expression
- ✅ Body language and demeanor
- ✅ Age range and build
- ✅ Current context (to change): what they're doing, where they are
- ✅ Outfit and setting (for reference)
- ⚠️ Emphasis on what makes THIS CHARACTER unique

**LLM Instruction:**
```
[REFERENCE MODE: CHARACTER REMIX]
Keep the character's core identity (face, build, personality traits).
Place them in a completely new scenario, environment, time period, or genre.
Change their outfit, lighting, setting, and mood.
Maintain character recognition while adapting to new context.
```

**Example:**
- Image: Samurai warrior in feudal Japan
- Your prompt: "as a detective in 1940s New York"
- Result: Same person's face/identity, detective outfit, noir setting

---

### 7. reimagine (NEW!)

**When to use:** Creative reinterpretation of concept/theme

**Qwen3-VL analyzes:**
- ✅ Core concept or theme
- ✅ Mood and emotional tone
- ✅ Narrative or story suggested
- ✅ Key symbolic elements or motifs
- ✅ Overall compositional approach
- ✅ What makes the image compelling
- ✅ Underlying ideas or themes
- ✅ The "feeling" or atmosphere
- ⚠️ Focus on abstract qualities, not literal details

**LLM Instruction:**
```
[REFERENCE MODE: REIMAGINE]
Use the reference image as loose inspiration for creative reinterpretation.
Take the core concept, mood, or theme and reimagine it in a new way.
Feel free to change subject, style, setting, and execution.
Maintain thematic connection while interpreting the essence freely.
```

**Example:**
- Image: Lonely astronaut on barren planet
- Your prompt: "underwater exploration"
- Result: Lone diver in vast ocean depths (same isolation/exploration theme)

---

## Complete Example Flow

### Using character_remix mode:

**Input:**
- Reference Image: Photo of a woman in Victorian dress
- reference_mode: "character_remix"  
- Your prompt: "in a futuristic cyberpunk city"

**Step 1 - Qwen3-VL Analysis (mode-specific):**
```
Core identity markers: Oval face, high cheekbones, piercing green eyes, 
determined expression, regal bearing. Character archetype: aristocratic 
but with rebellious undertones visible in her expression. Age: mid-20s. 
Build: slender but strong posture. Current context: Standing in Victorian 
parlor, wearing elaborate blue dress with corset. Key personality: 
Confident, intelligent, hint of defiance in her gaze.
```

**Step 2 - Mode Instruction Added:**
```
[REFERENCE MODE: CHARACTER REMIX]
Keep the character's core identity (face, build, personality traits).
Place them in a completely new scenario, environment, time period, or genre.
Change their outfit, lighting, setting, and mood.
Maintain character recognition while adapting to new context.
```

**Step 3 - Combined with Your Prompt:**
```
[Your prompt]: in a futuristic cyberpunk city

[REFERENCE MODE: CHARACTER REMIX]
Keep the character's core identity...

REFERENCE IMAGE ANALYSIS:
Core identity markers: Oval face, high cheekbones, piercing green eyes...
```

**Step 4 - LM Studio Generates:**
```
[GLOBAL SETUP]
The same woman with distinctive green eyes and regal bearing, now wearing 
sleek black tactical gear with neon blue accent lights. Towering holographic 
billboards reflect in rain-soaked streets of a cyberpunk megacity at night.

Shot 1: Close-up on her face as she surveys the neon-lit streets.
Her piercing green eyes catch the glow of holographic advertisements.
Camera slowly dollies in. Rain droplets stream past the lens...
```

---

## Key Improvements in v1.9.2

### Before (v1.9.1):
❌ Same generic Qwen3-VL prompt for all modes  
❌ Analyzed everything regardless of what mode needed  
❌ Wasted tokens on irrelevant details  
❌ LLM had to filter out what to ignore  
❌ Less precise control  
❌ No "reimagine" option

### After (v1.9.2):
✅ Mode-specific Qwen3-VL prompts  
✅ Only analyzes what's relevant for each mode  
✅ Efficient token usage  
✅ LLM gets pre-filtered focused information  
✅ More precise control  
✅ Added "reimagine" mode for creative freedom

---

## Which Mode Should I Use?

| Goal | Best Mode |
|------|-----------|
| Animate existing character art exactly | `recreate_exact` |
| Same character, different environment | `subject_only` |
| Apply film/art style to new scene | `style_only` |
| Match color mood of reference | `color_palette_only` |
| Recreate a specific pose/action | `action_only` |
| Character in different time/genre | `character_remix` |
| Thematic inspiration, creative freedom | `reimagine` |

---

## Technical Details

**Qwen3-VL Model:** Qwen/Qwen2-VL-7B-Instruct  
**Analysis Quality:** High-detail vision-language understanding  
**Token Efficiency:** Mode-specific prompts reduce unnecessary analysis  
**LLM Backend:** LM Studio (OpenAI-compatible API)  
**Integration:** Seamless Qwen3-VL → LM Studio pipeline

---

## Troubleshooting

**"Image not analyzed" error:**
- Check Qwen3-VL model is loaded
- Verify transformers>=4.42.0 installed
- Check image format (should be ComfyUI IMAGE type)

**"Reference mode not working as expected":**
- Clear ComfyUI cache and restart
- Verify you're using v1.9.2+
- Check LM Studio is running and connected
- Review console output for Qwen3-VL analysis

**"Character identity drifts":**
- Use `subject_only` or `character_remix` mode
- Make sure Qwen3-VL analysis includes facial features
- Try more detailed GUI prompt about maintaining identity

---

## Version History

**v1.9.2** (Current)
- Added mode-specific Qwen3-VL prompts
- Added "reimagine" mode
- Improved character_remix focus
- More efficient token usage

**v1.9.1**
- Added 6 reference modes
- Basic mode instructions

**v1.9.0**
- Initial reference image support
- Generic Qwen3-VL analysis

