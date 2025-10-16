# Node Comparison Guide - Which Node Should I Use?

## Quick Decision Tree

```
Do you have an IMAGE or just TEXT?

├─ TEXT → Text-to-Video nodes
│   │
│   ├─ Want SIMPLE presets?
│   │   └─ Use: AI Video Prompt Expander (Standard)
│   │
│   └─ Want DETAILED controls?
│       └─ Use: AI Video Prompt Expander (Advanced)
│
└─ IMAGE → Image-based nodes
    │
    ├─ Want to ANIMATE it (video)?
    │   └─ Use: Image-to-Video Prompt Expander
    │
    └─ Want to TRANSFORM it (image)?
        └─ Use: Image-to-Image Prompt Expander
```

## Complete Node Comparison

| Feature | Standard | Advanced | Image-to-Video | Image-to-Image |
|---------|----------|----------|----------------|----------------|
| **Input** | Text only | Text only | Image + Motion | Image + Changes |
| **Output** | Video prompts | Video prompts | Video prompts | Image prompts |
| **Presets** | ✅ | ✅ | ✅ | ❌ (Platform-based) |
| **Wildcards** | ✅ | ✅ | ✅ | ✅ |
| **Random Mode** | ✅ | ✅ (respects controls) | ✅ | ❌ |
| **Aesthetic Controls** | Basic | Full | Medium | Full (image-focused) |
| **Vision Model** | ❌ | ❌ | ✅ | ✅ |
| **Platform Awareness** | ❌ | ❌ | ❌ | ✅ (6 platforms) |
| **Best For** | Quick video prompts | Precise video control | Animating images | Transforming images |

## Detailed Comparison

### 1. AI Video Prompt Expander (Standard)

**When to use:**
- ✅ Quick video prompt generation
- ✅ Preset-based workflows
- ✅ Don't need fine control
- ✅ Text-to-video generation

**Example:**
```
Input: "A {animal} in a {location}"
Preset: cinematic
Tier: enhanced
Output: Detailed video prompt with cinematic style
```

**Pros:**
- Simple, fast
- Good presets
- Wildcard support
- Random mode

**Cons:**
- Less control
- No vision model
- No platform optimization

---

### 2. AI Video Prompt Expander (Advanced)

**When to use:**
- ✅ Need precise aesthetic control
- ✅ Specific camera/lighting requirements
- ✅ Professional video workflows
- ✅ Text-to-video with details

**Example:**
```
Input: "detective in office"
Shot Size: medium close-up
Camera Angle: low angle
Lighting: edge lighting
Preset: noir
Output: Precise video prompt with all specifications
```

**Pros:**
- Full control
- All Wan 2.2 options
- Respects dropdowns in random mode
- Wildcard support

**Cons:**
- More complex
- No vision model
- No platform optimization

---

### 3. Image-to-Video Prompt Expander

**When to use:**
- ✅ Animating existing images
- ✅ Image-to-video workflows
- ✅ Want AI to describe image
- ✅ Focus on motion/camera

**Example:**
```
Image: portrait.jpg
Motion: "slowly turns and smiles"
Camera: push in
Output: Video prompt preserving image + adding motion
```

**Pros:**
- Vision model describes image
- Focus on motion
- Camera controls
- Preset support

**Cons:**
- Needs vision model
- Video-only (not for img2img)
- No platform optimization

---

### 4. Image-to-Image Prompt Expander (NEW!)

**When to use:**
- ✅ Transforming/editing images
- ✅ Image-to-image workflows
- ✅ Platform-specific needs (Flux, SDXL, etc.)
- ✅ Style transfer, lighting changes

**Example:**
```
Image: photo.jpg
Change: "make it oil painting"
Platform: flux
Art Style: oil painting
Output: Flux-optimized prompt for artistic transformation
```

**Pros:**
- Platform-aware (6 platforms!)
- Vision model
- Art/style controls
- Optimized per model

**Cons:**
- Needs vision model
- Image-only (not for video)
- No presets (uses platforms)

---

## Use Case Examples

### Use Case 1: Quick Video from Text

**Goal:** Fast video prompt
**Node:** AI Video Prompt Expander (Standard)
```
Input: "robot in neon city"
Preset: cinematic
Tier: enhanced
```

### Use Case 2: Precise Video Control

**Goal:** Specific cinematography
**Node:** AI Video Prompt Expander (Advanced)
```
Input: "spaceship flying"
Shot: wide shot
Camera: tracking shot
Lighting: rim lighting
Lens: wide-angle
```

### Use Case 3: Animate Portrait

**Goal:** Make image move
**Node:** Image-to-Video Prompt Expander
```
Image: portrait.jpg
Motion: "turns head and smiles"
Camera: dolly in
For: Hunyuan Video, CogVideoX
```

### Use Case 4: Flux Style Transfer

**Goal:** Photo to painting
**Node:** Image-to-Image Prompt Expander
```
Image: photo.jpg
Change: "impressionist painting"
Platform: flux
Art Style: oil painting
For: FLUX.1-dev
```

### Use Case 5: SDXL Enhancement

**Goal:** Enhance with SDXL
**Node:** Image-to-Image Prompt Expander
```
Image: low_res.jpg
Change: "enhance quality, add details"
Platform: sd_xl
Detail: highly detailed
For: SDXL
```

### Use Case 6: Qwen Quick Edit

**Goal:** Fast specific edit
**Node:** Image-to-Image Prompt Expander
```
Image: portrait.jpg
Change: "change background to beach"
Platform: qwen_image_edit
For: Qwen Edit Model
```

## Feature Availability

### Wildcards
✅ All nodes support wildcards!
```
"A {animal:cat|dog|fox} {action:running|flying}"
```

### Random Mode
✅ Standard: Full random
✅ Advanced: Respects dropdowns
✅ Img2Vid: Available
❌ Img2Img: Uses platforms instead

### Vision Model
❌ Standard: No
❌ Advanced: No
✅ Img2Vid: Yes
✅ Img2Img: Yes

### Platform Optimization
❌ Standard: No
❌ Advanced: No (Wan 2.2 focus)
❌ Img2Vid: No (video focus)
✅ Img2Img: Yes! (6 platforms)

## Workflow Recommendations

### Video Generation Workflow

**Option 1: Simple**
```
[Standard Node] → [Video Gen Model]
```

**Option 2: Advanced**
```
[Advanced Node] → [Video Gen Model]
```

**Option 3: From Image**
```
[Load Image] → [Img2Vid Node] → [Video Gen Model]
```

### Image Generation Workflow

**From Image:**
```
[Load Image] → [Img2Img Node] → [Image Gen Model]
```

**Platform-Specific:**
```
For Flux: [Img2Img] (platform: flux) → [Flux Model]
For SDXL: [Img2Img] (platform: sd_xl) → [SDXL Model]
For Qwen: [Img2Img] (platform: qwen_image) → [Qwen Model]
```

## Common Questions

### Q: Which node for best video prompts?
**A:** 
- Quick: Standard
- Precise: Advanced
- From image: Img2Vid

### Q: Which node for Flux img2img?
**A:** Image-to-Image with platform: flux

### Q: Can I use vision model with video nodes?
**A:** Only Img2Vid and Img2Img have vision support

### Q: Which supports wildcards?
**A:** All 4 nodes!

### Q: Which respects my aesthetic dropdowns in random mode?
**A:** Advanced node (video)

### Q: Which optimizes for my image model?
**A:** Image-to-Image (6 platforms!)

## Summary

**Choose based on:**

| Your Task | Use This Node |
|-----------|---------------|
| Text → Video prompt (quick) | Standard |
| Text → Video prompt (precise) | Advanced |
| Image → Video prompt | Image-to-Video |
| Image → Image prompt (Flux) | Image-to-Image (flux) |
| Image → Image prompt (SDXL) | Image-to-Image (sd_xl) |
| Image → Image prompt (Qwen) | Image-to-Image (qwen) |
| Image → Quick edit | Image-to-Image (qwen_edit) |

**All nodes support:**
- ✅ Wildcards
- ✅ LM Studio / Ollama
- ✅ Multiple variations
- ✅ File saving
- ✅ Keyword injection

**Special features:**
- Vision model: Img2Vid, Img2Img only
- Platform optimization: Img2Img only
- Full aesthetic control: Advanced, Img2Img
- Random mode: Standard, Advanced, Img2Vid

---

**Pick the right tool for your workflow!**

All nodes work together - use Standard for quick video prompts, Img2Img for Flux transformations, etc.
