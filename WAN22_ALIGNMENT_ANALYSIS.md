# Wan 2.2 Alignment Analysis & Recommendations

## Date: October 24, 2025

## Executive Summary

After reviewing the comprehensive Wan 2.2 Prompt Design Guide and Director System Prompt, I've identified **significant opportunities** to improve our video prompt generation to better align with Wan 2.2's capabilities.

**Current Status**: 🟡 PARTIALLY ALIGNED  
**Recommendation**: 🔧 MAJOR ENHANCEMENT NEEDED

---

## Key Findings

### ✅ What We're Doing Right

1. **Camera Movement Vocabulary** - Our menus include most Wan 2.2-compatible terms:
   - ✅ "camera pushes in," "camera pulls back"
   - ✅ "camera pans right/left," "camera tilts up/down"
   - ✅ "static shot," "tracking shot," "arc shot"
   - ✅ "handheld camera," "dolly in/out"

2. **Shot Size Control** - We have proper framing options:
   - ✅ extreme close-up, close-up, medium shot, wide shot, etc.

3. **Lighting & Time of Day** - Comprehensive options aligned with Wan guide

4. **Aesthetic Controls** - Advanced node has granular control over cinematography

### ❌ Critical Gaps

#### 1. **No Shot Structure / Temporal Progression** 🚨 CRITICAL
**Wan 2.2 Requirement:**
- Prompts should be structured as Shot 1 → Shot 2 → Shot 3 (storyboard style)
- OR as 0-2s → 2-4s → 4-6s (continuous timed beats)
- Must include "Final wide reveal" or "Final shot" ending cue

**Our Current Implementation:**
- Generates ONE CONTINUOUS PARAGRAPH description
- No temporal structure or shot progression
- No explicit ending instruction
- LLM instructions say: "Write as ONE continuous paragraph describing the scene"

**Impact:** HIGH - Wan 2.2 expects temporal structure for best results

---

#### 2. **Missing Parallax & Atmospheric Motion Cues** 🚨 CRITICAL
**Wan 2.2 Requirement:**
- Explicitly describe foreground/background depth
- Add atmospheric motion: "rain streaks past lens," "steam drifts," "mist rises," "fabric ripples," "particles drift in air"
- These create parallax and prevent static-looking output

**Our Current Implementation:**
- Generic instruction to "describe textures, materials, motion characteristics"
- No specific requirement for atmospheric/environmental motion
- No explicit parallax language

**Impact:** HIGH - Without this, videos look flat/static even with camera movement

---

#### 3. **No Reference Image Mode Instructions** 🚨 CRITICAL
**Wan 2.2 Requirement:**
- When image reference is provided, MUST specify how to use it:
  - "Use the provided image as exact character and costume reference..."
  - "Match lighting/mood only, create new pose..."
  - "Preserve face only, ignore background..."
  - "Loosely base character, change outfit/setting..."

**Our Current Implementation:**
- Image-to-video node uses vision model to caption image
- BUT: No explicit instruction about HOW to use the reference
- Vision caption is just appended to prompt without mode guidance

**Impact:** HIGH - Wan may copy unwanted elements or drift identity

---

#### 4. **Word Count Too Low for Detailed Tiers**
**Wan 2.2 Recommendation:**
- Advanced: 400-600 words
- Cinematic: 600-1000 words

**Our Current Implementation:**
- Advanced: "400-600 words minimum" ✅ CORRECT
- Cinematic: "600-1000 words minimum" ✅ CORRECT
- BUT: Single paragraph format makes it hard to structure this much content coherently

**Impact:** MEDIUM - Format issue, not length issue

---

#### 5. **Missing Explicit Ending Instructions**
**Wan 2.2 Requirement:**
- Every prompt should end with clear termination cue:
  - "Final wide reveal"
  - "Final overhead shot"
  - "Final establishing shot"

**Our Current Implementation:**
- No requirement for ending instruction
- Prompts just... end

**Impact:** MEDIUM - Videos may loop awkwardly or cut off abruptly

---

#### 6. **Missing Identity Consistency Across Beats**
**Wan 2.2 Recommendation:**
- Repeat character capsule in each shot block:
  - "Shot 1: the same woman in white Hanfu..."
  - "Shot 2: the same woman in white Hanfu..."

**Our Current Implementation:**
- Not applicable since we don't use shot blocks

**Impact:** LOW (since we're single-paragraph) - Would become HIGH if we adopt shot structure

---

## Detailed Comparison

### Camera Movement Menus

| Wan 2.2 Recommended | Our Advanced Node | Status |
|---------------------|-------------------|--------|
| camera pans left/right | ✅ camera pans left/right | ALIGNED |
| camera tilts up/down | ✅ camera tilts up/down | ALIGNED |
| slow dolly in/out | ✅ dolly in/out | ALIGNED |
| camera pulls back | ✅ camera pulls back | ALIGNED |
| tracking shot | ✅ tracking shot | ALIGNED |
| arc shot | ✅ arc shot | ALIGNED |
| crane shot | ✅ crane shot | ALIGNED |
| handheld camera | ✅ handheld camera | ALIGNED |
| steadicam | ✅ steadicam | ALIGNED |
| static shot | ✅ static shot | ALIGNED |
| **the camera orbits around her** | ❌ MISSING | **GAP** |
| **smooth glide** | ❌ MISSING | **GAP** |
| **locked-off shot** | ❌ MISSING | **GAP** |
| **crash zoom** | ❌ MISSING | **GAP** |
| **whip pan** | ✅ whip pan | ALIGNED |
| **compound move** | ✅ compound move | ALIGNED |
| **camera cranes up** | ⚠️ "crane shot" (less specific) | PARTIAL |

### Shot/Angle Menus

| Wan 2.2 Recommended | Our Advanced Node | Status |
|---------------------|-------------------|--------|
| extreme close-up | ✅ | ALIGNED |
| close-up | ✅ | ALIGNED |
| medium close-up | ✅ | ALIGNED |
| medium shot | ✅ | ALIGNED |
| medium wide shot | ✅ | ALIGNED |
| wide shot | ✅ | ALIGNED |
| extreme wide shot | ✅ | ALIGNED |
| establishing shot | ✅ | ALIGNED |
| over-the-shoulder | ✅ | ALIGNED |
| **first-person POV** | ❌ MISSING | **GAP** |
| **profile close-up** | ❌ MISSING | **GAP** |

### Lighting (Well Covered)

Our lighting options are comprehensive and aligned with Wan 2.2 guide. ✅

---

## LLM System Prompt Analysis

### Current Expansion Engine Prompt

```
You are an expert AI video prompt engineer for Wan 2.2 video generation.

CRITICAL OUTPUT RULES:
1. Output ONLY the enhanced prompt - no labels, no explanations
2. Do NOT repeat or echo the user's input
3. Do NOT include phrases like "Here is..."
4. Write as ONE continuous paragraph describing the scene  ❌ WRONG FORMAT
5. Start directly with the description
```

### Wan 2.2 Director Prompt (From Guide)

```
You are a cinematic prompt director for Wan 2.2...

Return the final prompt in this structure:

[GLOBAL SETUP PARAGRAPH — 2-4 sentences]

Shot 1: [framing, camera move, subject action, parallax, emotion]

Shot 2: [new angle, escalation, new camera motion]

Shot 3: [final reveal, include "Final shot" or "Final wide reveal"]

[STYLE / TECH FOOTER]
```

### Critical Differences

| Aspect | Our Current Prompt | Wan 2.2 Guide | Gap Severity |
|--------|-------------------|---------------|--------------|
| **Structure Format** | Single paragraph | Multi-shot blocks | 🚨 CRITICAL |
| **Temporal Progression** | Not mentioned | Required (Shot 1/2/3 or 0-2s/2-4s/4-6s) | 🚨 CRITICAL |
| **Ending Instruction** | Not mentioned | Required ("Final wide reveal") | 🚨 CRITICAL |
| **Parallax Cues** | Generic "motion" | Explicit atmospheric motion required | 🚨 CRITICAL |
| **Identity Repetition** | Not mentioned | Repeat character capsule per shot | ⚠️ MEDIUM |
| **Word Count** | Correct minimums | Correct | ✅ ALIGNED |
| **Camera Verbs** | Good coverage | Good coverage | ✅ ALIGNED |

---

## Recommendations

### 🔴 PRIORITY 1: Restructure LLM System Prompt

**Action:** Replace single-paragraph format with shot-based structure

**New Format Option A (Storyboard Style):**
```
[GLOBAL SETUP - 2-4 sentences: subject, environment, mood, style]

Shot 1: [Framing + Camera Move]
[Describe subject action, foreground/background parallax, atmospheric motion, emotional beat]
[2-3 sentences]

Shot 2: [New Angle + Camera Move]
[Escalation, new details, continued motion, depth cues]
[2-3 sentences]

Shot 3: [Final Reveal + Camera Move]
[Ending beat, pullback/crane/reveal, say "Final shot" or "Final wide reveal"]
[2-3 sentences]

[STYLE/TECH FOOTER: 1-2 sentences with fps, resolution, style, negatives]
```

**New Format Option B (Continuous Timed):**
```
[GLOBAL SETUP - 2-4 sentences]

0-2s (Opening):
[Starting framing + camera move + initial action + atmospheric motion]

2-4s (Development):
[Camera transition + escalation + new details + parallax cues]

4-6s (Final):
[Ending move + reveal + "Final shot" termination cue]

[STYLE/TECH FOOTER]
```

**Benefits:**
- ✅ Aligns with Wan 2.2's temporal expectations
- ✅ Forces inclusion of ending cue
- ✅ Easier to structure 400-1000 words coherently
- ✅ Better camera choreography across beats

---

### 🔴 PRIORITY 2: Add Atmospheric Motion Requirements

**Action:** Update tier instructions to mandate parallax/atmospheric elements

**Add to ALL tier instructions:**
```
YOU MUST INCLUDE ATMOSPHERIC MOTION & PARALLAX:
- Foreground elements: particles drifting, rain streaks past lens, steam blowing, fabric rippling
- Background depth: mist rising, clouds moving, reflections shimmering, distant motion
- Environmental animation: leaves falling, water flowing, smoke drifting, shadows moving
- These create depth and prevent static-looking output

Examples:
- "rain streaks diagonally past the lens, catching neon light"
- "low mist rises from the lake surface and drifts across frame"
- "steam from street vents blows between camera and subject"
- "her long sleeves leave glowing trails as they sweep through air"
```

---

### 🔴 PRIORITY 3: Add Reference Image Mode Instructions

**Action:** Update image-to-video node to include explicit mode selection

**Add New Parameter to Image-to-Video Node:**
```python
"reference_mode": ([
    "recreate_exact",     # Keep exact character, outfit, lighting - animate this
    "style_transfer",     # Match lighting/mood only, new pose/scene
    "character_remix",    # Use character but change outfit/setting
    "face_only"          # Preserve face identity, ignore background/lighting
], {
    "default": "recreate_exact",
    "tooltip": "How to use the reference image"
})
```

**Update LLM Prompt to Include:**
```
REFERENCE IMAGE MODE: {reference_mode}

If recreate_exact:
"Use the provided image as the exact character and costume reference. Keep the same face, hair, outfit, and lighting. Animate this character without changing identity."

If style_transfer:
"Match the lighting, color palette, and cinematic mood of the provided image, but create a new pose and new scene."

If character_remix:
"Loosely base the main character on the provided image, but change the outfit and relocate them to a new setting."

If face_only:
"Preserve ONLY the subject's face and body identity from the provided image. Ignore the original background and lighting. Place this character in the new described scene."
```

---

### 🟡 PRIORITY 4: Expand Camera Movement Options

**Action:** Add missing Wan 2.2-recommended camera moves

**Add to camera_movement dropdown:**
```python
"camera orbits around subject",
"smooth glide",
"locked-off shot",
"crash zoom in",
"camera cranes up",
"camera cranes down"
```

**Add to shot_size dropdown:**
```python
"first-person POV",
"profile close-up"
```

---

### 🟡 PRIORITY 5: Add Negative Prompt Blocks

**Action:** Include Wan 2.2-recommended negatives based on style

**In expansion_engine.py, add:**
```python
def _get_negative_prompt_block(self, visual_style: str) -> str:
    """Generate Wan 2.2-optimized negative prompts"""
    
    if visual_style in ["photorealistic", "cinematic", "none", "auto"]:
        return """
Negative: no subtitles, no on-screen text, no watermarks, no logos, no extra limbs, no deformed hands, no distortion, not low quality
"""
    elif "anime" in visual_style.lower() or "cartoon" in visual_style.lower():
        return """
Negative: no photoreal skin texture, no live-action lighting, no watermarks, no subtitles, keep clean cel shading, no flicker, no jitter
"""
    else:
        return """
Negative: no watermarks, no subtitles, no text overlay, no distortion
"""
```

---

## Implementation Roadmap

### Phase 1: Critical Fixes (v1.9.0)
**Target: Next release**

1. ✅ Restructure LLM system prompt to use shot-based format (Storyboard OR Continuous)
2. ✅ Add explicit ending instruction requirement ("Final shot")
3. ✅ Add atmospheric motion/parallax requirements to all tier instructions
4. ✅ Add reference_mode parameter to image-to-video node
5. ✅ Include reference mode instruction in LLM prompt

**Estimated Work:** 4-6 hours  
**Impact:** HIGH - Transforms output quality for Wan 2.2

---

### Phase 2: Enhancement (v1.9.1)
**Target: Follow-up release**

1. ✅ Add missing camera movement options
2. ✅ Add missing shot/angle options
3. ✅ Implement negative prompt blocks
4. ✅ Add "creative_randomness" control (already done in v1.8.1)
5. ✅ Update documentation with Wan 2.2 best practices

**Estimated Work:** 2-3 hours  
**Impact:** MEDIUM - Completes Wan 2.2 alignment

---

### Phase 3: Advanced Features (v2.0.0)
**Target: Future**

1. ⚠️ Add multi-shot preview mode (show all 3 shots separately)
2. ⚠️ Add shot duration control (let user set 2s, 3s, 4s per shot)
3. ⚠️ Add "Director's Notes" field for extra instructions
4. ⚠️ Create Wan 2.2-specific preset library

**Estimated Work:** 8-12 hours  
**Impact:** MEDIUM - Power user features

---

## Example: Before vs After

### BEFORE (Current v1.8.1)

**LLM Output (Single Paragraph):**
```
A graceful woman in flowing white Hanfu dances at the edge of a moonlit lake at night, her long sleeves catching soft blue rim light as tiny birds of glowing spirit energy blossom from her fingertips and circle her in synchronized motion, leaving shimmering trails through the air while the dark water reflects their luminous glow and faint mist drifts across the scene, creating an ethereal wuxia fantasy atmosphere with cinematic realism and smooth motion at 24fps...
[continues for 400 words in one paragraph]
```

**Issues:**
- ❌ No temporal structure
- ❌ No explicit camera choreography progression
- ❌ No ending cue
- ❌ Limited parallax description
- ❌ Hard to parse for 400+ words

---

### AFTER (Proposed v1.9.0)

**LLM Output (Shot-Based Structure):**
```
A graceful woman in flowing white Hanfu dances at the edge of a moonlit lake at night. Soft blue rim light outlines her sleeves, and faint mist drifts across the water. Glowing spirit-bird particles gather around her hands as she moves. Cinematic realism, ethereal wuxia fantasy mood.

Shot 1: Close-up, Slow Dolly In
The camera starts in a close-up on her hands. She turns her wrists with elegant precision, and tiny birds of light blossom from her fingertips. Their wings glow softly and leave shimmering trails in the air. Slow dolly in toward her glowing fingertips, gentle handheld feel.

Shot 2: Medium Shot, Orbital Arc
The camera eases back to a medium shot of her upper body and begins a smooth orbital arc around her to the left. Her long sleeves sweep through the air, leaving ribbons of light. The spirit birds circle her in synchronized motion, tracing spirals above the dark lake. Mist drifts between camera and subject. Her face is calm, focused, powerful.

Shot 3: Overhead Crane Reveal (Final Shot)
The camera cranes upward and tilts down to an overhead view. The glowing birds form a radiant halo around her on the lakeshore, their reflections flickering on the black water. Moonlight and spirit-light merge into a swirling galaxy around her. Final wide reveal, majestic and otherworldly.

24fps, 1280×720, cinematic realism, smooth motion.
Negative: no subtitles, no on-screen text, no watermarks, no extra limbs, no distorted hands.
```

**Improvements:**
- ✅ Clear temporal progression (Shot 1 → 2 → 3)
- ✅ Explicit camera choreography per beat
- ✅ "Final wide reveal" ending cue
- ✅ Atmospheric motion ("mist drifts between camera and subject")
- ✅ Parallax cues ("reflections flickering")
- ✅ Negative prompt block included
- ✅ Much easier to read and parse
- ✅ Direct match to Wan 2.2 Director System Prompt format

---

## Conclusion

Our current implementation is **70% aligned** with Wan 2.2 best practices. We have excellent camera vocabulary and aesthetic controls, but we're missing the **critical structural format** that Wan 2.2 expects.

**The single biggest improvement** we can make is adopting the shot-based structure from the Wan 2.2 Director System Prompt. This alone will dramatically improve output quality.

**Recommended Action:**
1. Implement Phase 1 changes immediately (v1.9.0)
2. Test with real Wan 2.2 generations
3. Iterate based on results
4. Document Wan 2.2-specific workflows in README

**Risk Level:** LOW - Changes are additive and backward-compatible  
**Expected Benefit:** HIGH - Output quality should improve significantly

---

## Next Steps

Would you like me to:
1. ✅ Implement Phase 1 changes now (restructure LLM prompts)?
2. ✅ Create new test examples with shot-based format?
3. ✅ Update documentation with Wan 2.2 best practices?
4. ✅ All of the above?

Let me know how you'd like to proceed!
