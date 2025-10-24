# Advanced Prompt Expander Node - Redesign (v1.8.0)

## Overview

The Advanced Prompt Expander Node has been completely redesigned to address three critical usability issues and improve its functionality for real-world workflows.

---

## Problems Fixed

### ❌ Problem 1: No Way to Modify Existing Prompts

**Before:**
The node was designed only to "expand" short stub prompts like "a cat playing piano." If you had an existing detailed prompt that needed modification, refinement, or style changes, there was no way to tell the node to treat it differently.

**Now: ✅ Operation Mode Selection**

Added a new `operation_mode` dropdown with 4 modes:

1. **expand_from_idea** (default)
   - Original behavior: Take a short concept and expand it into full detail
   - Use when: You have a simple idea that needs fleshing out
   - Example: "a cat playing piano" → full cinematic description

2. **refine_existing**
   - Keep the core content but improve clarity, flow, and descriptive quality
   - Use when: You have a working prompt that needs polishing
   - Example: Improve grammar, enhance descriptions, better word choices

3. **modify_style**
   - Keep the subject/action but change aesthetic, mood, and cinematography
   - Use when: You want the same scene but different visual treatment
   - Example: Same cat scene, but change from "cinematic" to "noir" style

4. **add_details**
   - Keep everything that's there and add richer descriptions and sensory elements
   - Use when: Your prompt is good but needs more depth
   - Example: Add atmospheric details, textures, emotional beats

**Implementation:**
```python
def _apply_operation_mode(self, prompt: str, operation_mode: str, image_context: str = "") -> str:
    """
    Apply operation mode to modify how the prompt is processed
    """
    if operation_mode == "refine_existing":
        instruction = "\n\n[INSTRUCTION: This is an existing prompt to refine..."
        return prompt + instruction + image_context
    # ... etc
```

The node now adds specific instructions to the LLM based on the operation mode, guiding it on how to treat the input.

---

### ❌ Problem 2: Confusing Tier System

**Before:**
- Used terms like "basic", "enhanced", "advanced", "cinematic", "auto"
- Not clear what these mean or when to use them
- Word counts (150-250, 250-400, 400-600, 600-1000) were hidden from users
- "auto" tried to detect complexity but users didn't understand what it did

**Now: ✅ Clear Detail Levels**

Replaced `expansion_tier` with `detail_level` using intuitive names:

1. **concise** (replaces "basic")
   - ~150-200 words
   - Brief, essential details only
   - Use when: You want compact prompts

2. **moderate** (replaces "enhanced")
   - ~250-350 words
   - Good balance of detail
   - Use when: Standard detailed description

3. **detailed** (replaces "advanced")
   - ~400-500 words
   - Rich, comprehensive description
   - Use when: You want thorough detail (DEFAULT)

4. **exhaustive** (replaces "cinematic")
   - ~600-1000 words
   - Maximum detail for cinematic quality
   - Use when: Professional-grade video prompts

**Added Tooltips:**
Each option now has a clear tooltip explaining what it does and when to use it.

**Backward Compatibility:**
The expansion_engine.py now includes a mapping so old tier names still work internally:
```python
tier_mapping = {
    "concise": "basic",
    "moderate": "enhanced",
    "detailed": "advanced",
    "exhaustive": "cinematic"
}
```

**Removed "auto" option** - Users should choose their detail level explicitly.

---

### ❌ Problem 3: Image-to-Video Mode Without Image Input

**Before:**
- Had a "mode" dropdown with "text-to-video" and "image-to-video" options
- BUT: No way to actually provide an image!
- "image-to-video" mode was completely non-functional
- The Qwen3-VL backend exists but wasn't being used

**Now: ✅ Optional Image Input with Qwen3-VL**

**Added to INPUT_TYPES:**
```python
"optional": {
    # Optional image/video reference for image-to-video workflows
    "reference_image": ("IMAGE", {
        "tooltip": "Optional: Provide an image to analyze and incorporate into the prompt using Qwen3-VL"
    }),
}
```

**How it works:**

1. **If no image is provided:**
   - Works exactly as before
   - mode = "text-to-video"
   - Normal text expansion

2. **If image IS provided:**
   - Image is analyzed using Qwen3-VL vision model
   - Detailed caption is generated describing:
     - Main subject and appearance
     - Actions and movements
     - Environment and setting
     - Lighting and atmosphere
     - Colors and visual style
     - Notable objects/elements
   - mode automatically switches to "image-to-video"
   - Caption is appended to the working prompt as context
   - LLM incorporates image analysis into the expanded prompt

**Image Processing:**
```python
def _process_reference_image(self, image_tensor):
    """Process ComfyUI image tensor using Qwen3-VL for captioning"""
    # Convert ComfyUI format (B,H,W,C) to PIL Image
    # Call Qwen3-VL with detailed video-focused prompt
    # Return caption or None if error
```

**Status Display:**
The status now shows:
- `Mode: text-to-video` - if no image
- `Mode: image-to-video (with image)` - if image provided

---

## Migration Guide

### For Existing Workflows

**Old Node Configuration:**
```
expansion_tier: "advanced"
mode: "text-to-video"
basic_prompt: "your prompt here"
```

**New Equivalent:**
```
detail_level: "detailed"
operation_mode: "expand_from_idea"
basic_prompt: "your prompt here"
reference_image: (empty/optional)
```

### Mapping Old to New

| Old `expansion_tier` | New `detail_level` | Word Count |
|---------------------|-------------------|------------|
| basic | concise | 150-200 |
| enhanced | moderate | 250-350 |
| advanced | detailed | 400-500 |
| cinematic | exhaustive | 600-1000 |
| auto | (removed) | user chooses |

**The old "mode" dropdown has been removed** - it's now automatically determined by whether an image is provided.

---

## New Workflows Enabled

### Workflow 1: Refine an Existing Long Prompt
```
Input: [Your 300-word existing prompt]
operation_mode: refine_existing
detail_level: detailed
Result: Polished version with better flow and clarity
```

### Workflow 2: Change Style of Existing Prompt
```
Input: [Your existing prompt about a detective scene]
operation_mode: modify_style
preset: noir (changed from cinematic)
detail_level: detailed
Result: Same detective scene, but now in noir style
```

### Workflow 3: Image-to-Video with Context
```
Input: "Make the subject move towards the camera dramatically"
operation_mode: expand_from_idea
reference_image: [Your reference image]
detail_level: detailed
Result: Detailed video prompt incorporating image analysis + your direction
```

### Workflow 4: Add More Detail to Good Prompt
```
Input: [Your working prompt that's a bit sparse]
operation_mode: add_details
detail_level: exhaustive
Result: Same prompt but with atmospheric details, textures, emotions added
```

---

## Technical Changes

### Files Modified

1. **prompt_expander_node_advanced.py**
   - Added `operation_mode` parameter
   - Renamed `expansion_tier` → `detail_level`
   - Removed `mode` parameter (auto-detected)
   - Added optional `reference_image` input
   - Added `_apply_operation_mode()` helper method
   - Added `_process_reference_image()` for Qwen3-VL integration
   - Updated status display to show operation mode and image usage
   - Updated metadata for saved files

2. **expansion_engine.py**
   - Added tier name mapping for backward compatibility
   - Supports both old and new tier names
   - Cleaner logic for tier detection

### New Dependencies

The node now imports from qwen3_vl_backend.py when an image is provided:
```python
from .qwen3_vl_backend import caption_with_qwen3_vl
```

This is only imported if needed, so the node still works without Qwen3-VL installed (just can't use image input).

---

## Testing Checklist

### Test 1: Operation Modes
- [ ] expand_from_idea: "cat playing piano" expands fully
- [ ] refine_existing: Long prompt gets polished, not expanded
- [ ] modify_style: Subject stays same, style changes with preset
- [ ] add_details: Original content preserved, details added

### Test 2: Detail Levels
- [ ] concise: Output ~150-200 words
- [ ] moderate: Output ~250-350 words
- [ ] detailed: Output ~400-500 words
- [ ] exhaustive: Output ~600-1000 words

### Test 3: Image Input
- [ ] No image: Works normally, mode=text-to-video
- [ ] With image: Qwen3-VL analyzes it, mode=image-to-video
- [ ] Image analysis appears in breakdown
- [ ] Status shows "(with image)"

### Test 4: Backward Compatibility
- [ ] Old workflows with "advanced" tier still work
- [ ] Old tier names map to new detail levels correctly

### Test 5: Combined Features
- [ ] modify_style + with_image: Changes style based on image
- [ ] refine_existing + exhaustive: Makes existing prompt much more detailed
- [ ] add_details + moderate: Balanced detail addition

---

## Benefits

✅ **More Intuitive**
- Clear operation modes match user intent
- Detail levels have obvious names and tooltips

✅ **More Powerful**
- Can now modify existing prompts 4 different ways
- Can incorporate image analysis for image-to-video workflows

✅ **Better UX**
- Tooltips explain every option
- Status messages are more informative
- No more confusing "auto" mode

✅ **Backward Compatible**
- Old tier names still work internally
- Existing workflows won't break
- Expansion engine supports both naming systems

✅ **Leverages Existing Tech**
- Finally uses the Qwen3-VL backend that was already there
- ComfyUI image tensors integrate seamlessly

---

## Future Enhancements

Possible future additions:
- Support for video input (Qwen3-VL can handle it)
- Multiple reference images
- Image directive modes (like text_to_image_node has)
- Comparison of before/after for modify/refine modes
- Batch processing with different operation modes

---

## Status

**Version:** 1.8.0
**Date:** October 23, 2025
**Status:** ✅ Complete - Ready for Testing
**Tested:** No syntax errors, imports validated
**Next:** Test in ComfyUI with actual LLM and images

---

## Questions & Answers

**Q: Do I need Qwen3-VL to use this node?**
A: No! It's optional. The node works fine without it - you just can't use the image input feature.

**Q: Will my old workflows break?**
A: No. The expansion_engine still understands old tier names internally, so saved workflows with "advanced" will still work.

**Q: What if I'm happy with the old simple behavior?**
A: Just use `operation_mode: expand_from_idea` and ignore the image input. It works exactly as before.

**Q: Can I use multiple images?**
A: Not yet, but the architecture supports it. Currently limited to one reference image.

**Q: What's the best detail level?**
A: Start with "detailed" (the default). Use "exhaustive" for professional work, "moderate" for quick tests, "concise" for API token savings.

**Q: When should I use modify_style vs add_details?**
A: 
- **modify_style**: You want the same scene but different visual treatment
- **add_details**: You want to keep the style but make it richer

