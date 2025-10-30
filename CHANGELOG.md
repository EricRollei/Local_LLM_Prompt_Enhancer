# Changelog

All notable changes to Eric's Prompt Enhancers for ComfyUI.

---

## [1.9.7] - 2025-01-27

### 🎯 Model-Agnostic Creativity Control

**Problem Identified:** Two major issues with temperature-based creativity control:
1. **Temperature behavior varies drastically between models** - What works at 0.7 for one model may be too conservative or too wild for another
2. **LLMs have probability bias** - Even with high temperature, they tend to favor "best choice" high-probability outputs, reducing true randomness
3. **Non-functional creative_randomness slider** - Defined in UI but never actually used in code

**User Insight:** *"From what I've read the temp setting for good results can vary from model to model. We can't rely on 0.7"*

**Solution:** Replaced numeric temperature slider with semantic **Creativity Mode** dropdown using hybrid approach:

#### Changes

**Removed:**
- ❌ Temperature float slider (0.1-2.0)
- ❌ Creative randomness float slider (non-functional)

**Added:**
- ✅ **Creativity Mode dropdown** with 4 semantic options:
  - **Conservative** (temp 0.5)
  - **Balanced** (temp 0.7) - default
  - **Creative** (temp 0.85)
  - **Highly Creative** (temp 1.0)

#### How It Works - Hybrid Approach

**Temperature Mapping:**
```python
conservative → 0.5
balanced → 0.7
creative → 0.85
highly_creative → 1.0
```

**Explicit LLM Instructions** (overrides probability bias):

**Conservative Mode:**
- Focus: Predictable, proven techniques
- Instruction: "Stay very close to original concept"
- Effect: Standard camera angles, natural lighting, conventional choices

**Balanced Mode:**
- Focus: Mix proven with fresh ideas
- Instruction: "70% established techniques, 30% creative variations"
- Effect: Mostly traditional with some unexpected elements

**Creative Mode:**
- Focus: Bold and experimental
- Instruction: "Avoid obvious choices, favor unusual perspectives, sample from MIDDLE and LOWER probability range"
- Effect: Unconventional camera angles, dramatic lighting, unexpected elements

**Highly Creative Mode:**
- Focus: Maximum experimentation
- Instruction: "⚠️ AVOID obvious choices, be BOLD. Skip eye-level → use dutch angles. Skip standard lighting → use unconventional setups. Choose from LOWER 50% probability options. What would surprise a cinematographer?"
- Effect: Experimental camera work, unusual lighting, gravity-defying elements, distinctive choices

#### Why This Works

1. **Model-Agnostic:** Users pick outcome (conservative/creative) not numbers - works across all models
2. **Explicit Instructions:** LLM knows to "avoid the first option" and "sample from lower probability" - overcomes bias
3. **Temperature Reinforcement:** Safe range (0.5-1.0) provides technical backing
4. **User-Friendly:** Semantic labels make intent clear - no guessing what "0.7" means

#### Impact

- 🎯 Consistent creative outcomes across different LLM backends (LM Studio, Ollama, Qwen3-VL)
- 🎨 True creativity variation - not just "best choice" repeated
- 🚀 Intuitive UX - users understand what each mode will produce
- ✅ Works within model limitations (some can't exceed temp 1.0)

---

## [1.9.6] - 2025-01-27

### 🎨 Enhanced Preset Effectiveness

**Problem Identified:** Presets (cinematic, noir, surreal, etc.) were having minimal impact on output because they were buried in the system prompt.

**Solution:** Completely rewrote how presets are communicated to the LLM:

#### What Changed

**Before:**
- Preset was mentioned as tiny note: `PRESET EMPHASIS: lighting, atmosphere`
- Lost among 500+ lines of generic instructions
- LLM barely noticed the preset selection

**After:**
- **Dedicated prominent section** at top of system prompt
- **Mandatory requirements** clearly marked with ⚠️ warnings
- **Specific technical requirements** for each preset:
  - **Camera requirements:** Exact camera movements and angles
  - **Lighting requirements:** Specific lighting setups
  - **Motion style:** How movement should be portrayed
  - **Technical specs:** Lens, color grading, effects
  - **Atmosphere:** Mood and feeling requirements

#### Preset Details Now Enforced

**Cinematic:**
- ✅ Professional lighting setup, edge lighting, controlled shadows
- ✅ Smooth camera movement, deliberate framing, depth of field
- ✅ Fluid motion, realistic physics
- ✅ Medium to long lens, intentional color grading

**Noir:**
- ✅ High contrast lighting, hard lighting, venetian blind shadows
- ✅ Low angle shots, dutch angles, dramatic framing
- ✅ Deliberate movement, tension in stillness
- ✅ Desaturated colors, deep shadows, night settings
- ✅ Mysterious, tense, foreboding atmosphere

**Surreal:**
- ✅ Unnatural lighting, mixed sources, saturated/desaturated colors
- ✅ Unusual angles, floating camera, disorienting perspectives
- ✅ Slow motion, floating, gravity-defying movement
- ✅ Creative color grading, atmospheric effects

**Action:**
- ✅ High contrast, dramatic hard lighting, strong shadows
- ✅ Rapid camera movement, tracking shots, handheld feel
- ✅ Fast motion, explosive action, kinetic energy
- ✅ Wide-angle lens, motion blur, dynamic framing

**Stylized:**
- ✅ Artistic lighting, color-coordinated palette
- ✅ Deliberate framing, symmetrical composition
- ✅ Stylized movement, choreographed motion
- ✅ Strong visual identity, consistent color palette

#### Impact

You should now see **dramatic differences** between presets:
- **Noir** → Dark, moody, high-contrast with dramatic shadows
- **Cinematic** → Professional film quality with controlled lighting
- **Surreal** → Dreamlike, otherworldly, unusual perspectives
- **Action** → Fast-paced, dynamic, energetic movement
- **Stylized** → Artistic, design-forward aesthetic

**Testing:** Try the same prompt with different presets - you should now see completely different visual treatments!

---

## [1.9.5] - 2025-10-27

### 🎯 Simplified Configuration - Removed model_name Field

**Breaking Change:** Removed confusing `model_name` field from **all nodes**.

#### Nodes Updated

All nodes in the suite have been updated with this change:
- ✅ **AI Video Prompt Expander (Advanced)** - prompt_expander_node_advanced.py
- ✅ **AI Prompt Expander (Basic)** - prompt_expander_node.py
- ✅ **Text-to-Image Prompt Enhancer** - text_to_image_node.py
- ✅ **Image-to-Video Prompt Expander** - image_to_video_node.py
- ✅ **Image-to-Image Prompt Expander** - image_to_image_node.py

#### Why This Change?

The `model_name` field was problematic:
- **LM Studio/Ollama:** Can't control which model is loaded remotely - they use whatever is currently running
- **Qwen3-VL:** Auto-detection is smarter than manual entry
- **User Experience:** Confusing to have a text field with no clear guidance on what to enter

#### What Changed

**Removed from all nodes:**
- `model_name` input field (was a confusing text input)
- `vision_model_name` input field (in nodes with vision)
- `expansion_model_name` input field (in nodes with separate expansion backend)

**Simplified to:**
- `llm_backend` dropdown: Choose your backend (lm_studio, ollama, qwen3_vl)
- `api_endpoint` / `vision_endpoint` / `expansion_endpoint`: 
  - **For LM Studio/Ollama:** API URL (e.g., `http://localhost:1234/v1`)
  - **For Qwen3-VL:** Custom model path (optional, auto-detects if left as default)

#### How Each Backend Works Now

**LM Studio:**
- Uses whatever model you've loaded in LM Studio
- Just ensure LM Studio is running with a model loaded
- Node will query and use the active model

**Ollama:**
- Uses whatever model you've loaded in Ollama
- Start Ollama with your preferred model first
- Node will query and use the active model

**Qwen3-VL:**
- **Auto-detects** local models in `ComfyUI/models/VLM/` directory
- Checks for `Qwen3-VL-4B-Instruct` first
- Falls back to any `Qwen*-VL-*` model found
- **Custom path (optional):** Use endpoint field to specify custom model location:
  ```
  api_endpoint: "A:\path\to\your\qwen\model"
  ```
  or with `local:` prefix:
  ```
  api_endpoint: "local:A:\path\to\your\qwen\model"
  ```

#### Migration Guide

If you were using custom model names:

**Before (v1.9.4):**
```
llm_backend: "qwen3_vl"
model_name: "local:A:\my\custom\path"
api_endpoint: "http://localhost:1234/v1"
```

**After (v1.9.5):**
```
llm_backend: "qwen3_vl"
api_endpoint: "A:\my\custom\path"
```

**LM Studio/Ollama users:** No workflow changes needed - ComfyUI will automatically remove deprecated fields.

#### Benefits

✅ **Clearer UX** - No more "what do I type here?" confusion  
✅ **Less clutter** - Fewer fields, cleaner interface  
✅ **Smarter defaults** - Auto-detection just works  
✅ **Matches reality** - Can't control LM Studio/Ollama models remotely anyway  
✅ **Dual-purpose field** - Endpoint field works for both API URL and local paths

---

## [1.9.4] - 2025-10-27

### ✨ New Feature - Qwen3-VL as LLM Backend

Added support for using local Qwen3-VL models for prompt expansion (no API server required).

#### New LLM Backend Option

**What's New:**
- Added `qwen3_vl` to LLM backend dropdown
- Use local Qwen3-VL models directly for text generation
- No need for LM Studio or Ollama API servers
- Leverages existing Qwen3-VL model if already loaded for vision
- **Auto-detects local models** in `ComfyUI/models/VLM/` directory

#### Smart Local Model Detection

The backend now automatically finds your local Qwen3-VL models:

1. **First checks:** `ComfyUI/models/VLM/Qwen3-VL-4B-Instruct/`
2. **Falls back to:** Any `Qwen*-VL-*` model in VLM directory
3. **Last resort:** Downloads from HuggingFace (if no local model found)

**This means:** If you already have Qwen3-VL installed for vision, it will use that same model!

#### Usage Examples (DEPRECATED - See v1.9.5)

**Auto-detect local model (recommended):**
```
llm_backend: "qwen3_vl"
api_endpoint: "http://localhost:1234/v1"  (leave as default)
```
model_name: "Qwen3-VL-7B-Instruct"  (looks in VLM folder)
```

**Download specific HuggingFace model:**
```
llm_backend: "qwen3_vl"
model_name: "Qwen/Qwen3-VL-4B-Instruct@4bit"
```

#### Files Modified

- `llm_backend.py`: Added `_call_qwen3_vl()` method
- `prompt_expander_node_advanced.py`: Added qwen3_vl to backend options
- Updated tooltips for model_name and api_endpoint

---

## [1.9.3] - 2025-10-26

### 🐛 Critical Bug Fix - LM Studio Error Handling

Fixed crash when LM Studio returns error responses.

#### Issue
- **Error:** `ERROR: LM Studio Error: 'choices'`
- **Root Cause:** Code tried to access `data['choices'][0]` without checking if response contained errors
- **Impact:** Node crashed instead of displaying helpful error message

#### Fix
- Added response structure validation in `_call_lm_studio()` and `_caption_lm_studio()`
- Check for `choices` field before accessing
- Check if choices array is non-empty
- Extract and display actual LM Studio error messages
- Added KeyError exception handling
- Added debug logging to show response structure

#### New Error Messages
- "LM Studio API Error: {actual error message from server}"
- "LM Studio returned empty choices array"
- "LM Studio returned unexpected response structure"

#### Debug Logging
- Console now shows: `[LLM Backend] LM Studio response keys: [...]`
- On error: `[LLM Backend] LM Studio error response: {...}`
- On expansion fail: `[Advanced Node] LLM expansion failed: {error}`

---

## [1.9.2] - 2025-10-26

### 🎯 Mode-Specific Vision Analysis

Significantly improved reference image handling with mode-specific Qwen3-VL prompts.

#### Critical Improvement - Focused Analysis

**BEFORE (v1.9.1):** Same generic Qwen3-VL prompt for all modes  
**AFTER (v1.9.2):** Mode-specific prompts that only analyze relevant aspects

#### New Reference Mode: "reimagine"

Added 7th reference mode for creative reinterpretation:
- `reimagine`: Loose inspiration, creative freedom, thematic connection

#### Mode-Specific Qwen3-VL Prompts

Each reference mode now has a tailored vision analysis prompt:

**recreate_exact:**
- Analyzes: Subject, outfit, environment, lighting, colors, style, composition
- Focus: Every detail for exact recreation

**subject_only:**
- Analyzes: Facial features, hair, body type, personality traits
- Ignores: Background, environment, lighting
- Focus: Character identity only

**style_only:**
- Analyzes: Artistic style, lighting style, color grading, atmosphere
- Ignores: Subject identity, character, scene content
- Focus: Visual aesthetic only

**color_palette_only:**
- Analyzes: Dominant colors, relationships, saturation, temperature
- Ignores: Subjects, composition, lighting style
- Focus: Pure color extraction

**action_only:**
- Analyzes: Pose, gesture, body position, movement, dynamics
- Ignores: Character identity, clothing, environment
- Focus: Physical action only

**character_remix:**
- Analyzes: Core identity, personality traits, archetype, demeanor
- Notes: Current outfit/setting for reference
- Focus: Character essence for new scenarios

**reimagine:**
- Analyzes: Core concept, mood, theme, narrative, symbolism
- Focus: Abstract qualities and themes
- Focus: Creative reinterpretation

#### Benefits

- ✅ More efficient token usage (only analyze what's needed)
- ✅ More accurate mode behavior (pre-filtered information)
- ✅ Faster Qwen3-VL processing (focused prompts)
- ✅ Better LLM results (receives relevant context only)
- ✅ Creative freedom with new "reimagine" mode

#### Technical Changes

**Modified Files:**
- `prompt_expander_node_advanced.py`:
  - Updated `_process_reference_image()` to accept `reference_mode` parameter
  - Added mode-specific Qwen3-VL prompt dictionary with 7 detailed prompts
  - Added "reimagine" mode to reference_mode parameter
  - Updated mode instruction for character_remix (clarity improvement)

#### Example: character_remix Before vs After

**Before (v1.9.1):**
```
Qwen3-VL Prompt: "Describe this image in detail for video generation purposes..."
Result: Describes everything (character, background, lighting, props)
LLM: Must figure out what to ignore
```

**After (v1.9.2):**
```
Qwen3-VL Prompt: "Focus on character essentials for remixing. Describe:
- Core identity markers: distinctive facial features, expression, personality
- Character archetype: hero, villain, mystic, warrior, etc..."
Result: Focused on character identity only
LLM: Gets exactly what it needs
```

---

## [1.9.1] - 2025-10-26

### 🎛️ Enhanced Advanced Node Controls

Added two critical control parameters to the Advanced Video Prompt Expander for better creative control.

#### New Parameters

**1. Reference Image Mode** (`reference_mode`)
Controls how reference images are interpreted when attached to the Advanced node:
- `recreate_exact`: Use as exact character/costume/setting reference (default)
- `subject_only`: Keep character identity, ignore background/lighting
- `style_only`: Match aesthetic and mood, create new subject
- `color_palette_only`: Extract and apply color scheme only
- `action_only`: Use pose/gesture, change everything else
- `character_remix`: Keep character, place in new scenario

Each mode includes explicit LLM instructions optimized for Wan 2.2 image-to-video workflows.

**2. Shot Structure Control** (`shot_structure`)
Choose how the output prompt is structured:
- `continuous_paragraph`: Single flowing description (no shot breaks)
- `2_shot_structure`: Two shots (Opening + Final Reveal)
- `3_shot_structure`: Three shots - Setup, Development, Finale (default, recommended)
- `4_shot_structure`: Four shots - Intro, Build, Climax, Resolution

Allows users to match different video generation needs:
- Continuous for smooth single-camera moves
- 2-shot for simple before/after narratives
- 3-shot for balanced storytelling (Wan 2.2 recommended)
- 4-shot for complex narrative arcs

#### Technical Changes

**Modified Files:**
- `prompt_expander_node_advanced.py`:
  - Added `reference_mode` parameter with 6 options
  - Added `shot_structure` parameter with 4 options
  - New method `_build_reference_mode_instruction()` for mode-specific LLM instructions
  - Updated `expand_prompt()` signature to accept and pass new parameters

- `expansion_engine.py`:
  - Added `shot_structure` parameter to `expand_prompt()` and `_build_system_prompt()`
  - New methods for structure templates:
    - `_get_3_shot_structure_instructions()` (default)
    - `_get_2_shot_structure_instructions()`
    - `_get_4_shot_structure_instructions()`
    - `_get_continuous_structure_instructions()`
  - Dynamic structure selection based on user choice

#### User Benefits

- **More Control**: Users can now explicitly choose output format instead of always getting 3-shot structure
- **Better Image-to-Video**: Reference mode instructions prevent identity drift and unwanted element copying
- **Flexibility**: Support for different video lengths and narrative styles
- **Backward Compatible**: Defaults maintain v1.9.0 behavior (3-shot structure, recreate_exact mode)

---

## [1.9.0] - 2025-10-24

### 🎬 WAN 2.2 ALIGNMENT - Major Video Prompt Restructure

This release completely restructures video prompt generation to align with Wan 2.2 best practices, following the official Wan 2.2 Prompt Design Guide and Director System Prompt.

#### 🚨 Critical Changes - Shot-Based Structure

**BEFORE (v1.8.x):** Single continuous paragraph output  
**AFTER (v1.9.0):** Structured shot-based format with temporal progression

**New Output Format:**
```
[Global Setup - 2-4 sentences]

Shot 1: [Framing + Camera Move]
[Action, parallax, atmosphere - 2-3 sentences]

Shot 2: [New Angle + Camera Move]
[Escalation, depth cues - 2-3 sentences]

Shot 3: [Final Reveal + Camera Move]
[Ending with "Final shot" termination - 2-3 sentences]

[Style/Tech Footer + Negatives]
```

#### Added - Atmospheric Motion & Parallax Requirements

All tiers now **require** depth and motion cues in every shot:
- **Foreground:** rain streaks past lens, particles drifting, steam blowing, fabric rippling
- **Background:** mist rising, clouds moving, reflections shimmering, shadows shifting
- **Environmental:** leaves falling, water flowing, smoke drifting, wind effects

**Impact:** Videos no longer look flat or static - proper depth perception created

#### Added - Reference Image Mode (Image-to-Video Node)

New `reference_mode` parameter with 4 Wan 2.2-optimized modes:
1. **recreate_exact** - Keep exact character, outfit, lighting - animate this
2. **style_transfer** - Match lighting/mood only, new pose/scene
3. **character_remix** - Use character but change outfit/setting
4. **face_only** - Preserve face identity only, ignore background/lighting

Each mode includes explicit LLM instruction following Wan 2.2 guidelines.

#### Enhanced - Camera Movement Options

Added missing Wan 2.2-recommended camera moves to Advanced Node:
- `camera orbits around subject`
- `smooth glide`
- `locked-off shot`
- `crash zoom in`
- `camera cranes up`
- `camera cranes down`

Added shot/angle options:
- `first-person POV`
- `profile close-up`

**Total camera_movement options:** 24 (was 17, +41%)

#### Enhanced - Negative Prompts (Wan 2.2 Style)

Negative prompts now adapt based on visual_style:

**For photorealistic/cinematic:**
- "no subtitles, no on-screen text, no watermarks, no logos, no extra limbs, no deformed hands, no distortion, not low quality"

**For anime/stylized:**
- "no photoreal skin texture, no live-action lighting, no watermarks, no subtitles, keep clean cel shading, no flicker, no jitter"

**Auto-applied** based on visual_style parameter in Advanced Node.

#### Enhanced - LLM System Prompt

Complete rewrite of expansion_engine system prompts:
- ✅ Shot-based structure required (not optional)
- ✅ Explicit ending cue requirement ("Final shot" or "Final wide reveal")
- ✅ Character identity repetition across shots
- ✅ Atmospheric motion mandatory in every shot
- ✅ Professional camera language (Wan 2.2 vocabulary only)

#### Technical Changes

**Modified Files:**
1. `expansion_engine.py`
   - Restructured `_build_system_prompt()` to use shot format
   - Updated all tier instructions (basic, enhanced, advanced, cinematic)
   - Added atmospheric motion requirements section
   - Enhanced `generate_negative_prompt()` with visual_style parameter
   
2. `prompt_expander_node_advanced.py`
   - Added 7 new camera_movement options
   - Added 2 new camera_angle options
   - Updated to pass visual_style to negative prompt generation
   
3. `image_to_video_node.py`
   - Added `reference_mode` parameter
   - Created `_build_combined_prompt_with_mode()` method
   - Includes explicit reference mode instructions in LLM prompt

**Backward Compatibility:**
- ✅ All existing parameters retained
- ✅ Old workflows will work (new format auto-applied)
- ✅ No breaking changes to API

#### Documentation

- `WAN22_ALIGNMENT_ANALYSIS.md` - Complete analysis of gaps and fixes
- `docs/Wan2.2_Prompt_Design_Guide.md` - Official Wan 2.2 guide (reference)
- `docs/Wan2.2_Director_System_Prompt.md` - Official Director prompt (reference)

#### Migration Notes

**For existing users:**
- Your old prompts will automatically use new shot-based structure
- Output format will change (structured vs. paragraph) - this is INTENTIONAL and improves Wan 2.2 quality
- No action required - all changes are automatic

**For advanced users:**
- Review WAN22_ALIGNMENT_ANALYSIS.md for detailed technical changes
- Test new reference_mode options in image-to-video workflows
- Experiment with new camera movements (orbits, crash zooms, etc.)

#### Known Improvements

Users should see:
- ✅ Better temporal progression in videos (clear shot changes)
- ✅ More dynamic camera work (not just static or simple moves)
- ✅ Improved depth perception (parallax from atmospheric motion)
- ✅ Cleaner endings (no awkward loops or abrupt cuts)
- ✅ Better identity consistency in image-to-video
- ✅ More professional-looking cinematography

#### Version Jump Explanation

Jumped from v1.8.1 → v1.9.0 (not v1.8.2) because:
- Major structural changes to core LLM prompts
- New output format (shot-based vs paragraph)
- Significant architectural improvements
- Wan 2.2 alignment is a major feature milestone

---

## [1.8.1] - 2025-10-24

### Enhanced - Advanced Prompt Expander Node

#### Added Creative Controls
1. **New `creative_randomness` Parameter**
   - Float slider (0.0 to 1.0, default 0.5)
   - Controls LLM creativity level
   - 0.0 = Stay close to original, 1.0 = Maximum creative liberty
   - Positioned logically after `detail_level`

2. **New `art_style` Parameter**
   - 26 options including famous artists and art movements
   - Classic Artists: Picasso, Van Gogh, Monet, Dali, Rembrandt, Caravaggio, etc.
   - Modern/Contemporary: Banksy, Warhol, Rockwell, Hopper
   - Studio Styles: Studio Ghibli, Tim Burton, Wes Anderson, Pixar
   - Art Movements: Renaissance, Baroque, Impressionist, Surrealist, Cubist, Pop Art, etc.

3. **New `scene_detail` Parameter**
   - 9 options controlling scene complexity
   - Range: simple → minimalist → clean → detailed → intricate → cluttered → maximalist
   - Separate control from prompt detail_level

#### Expanded Existing Menus
1. **`light_source` Expansion** (10 → 20 options)
   - Added: ambient, reflected, softbox, camera flash, neon lights
   - Added: striplight, computer screen glow, flashlight, candlelight, spotlight

2. **`lighting_type` → `lighting_quality`** (13 → 18 options)
   - Renamed for clarity
   - Added: spotlight effect, dappled, cinematic, diffused, dramatic lighting

#### Technical Changes
- Updated function signatures to include new parameters
- Enhanced `_gather_aesthetic_controls()` to collect new style parameters
- All changes backward compatible with existing workflows

#### Documentation
- `ENHANCEMENT_v1.8.1.md` - Detailed enhancement documentation
- `QUICK_REF_v1.8.1.md` - Quick reference with examples

---

## [1.8.0] - 2025-10-24

### Major Redesign - Advanced Prompt Expander Node

#### Fixed - Critical Usability Issues
1. **No Way to Modify Existing Prompts**
   - Added `operation_mode` dropdown with 4 modes:
     - `expand_from_idea`: Original behavior (expand short concepts)
     - `refine_existing`: Polish and improve existing prompts
     - `modify_style`: Change aesthetic while keeping subject
     - `add_details`: Add richer descriptions to existing content
   
2. **Confusing Tier System**
   - Replaced `expansion_tier` with `detail_level` using intuitive names:
     - `concise` (150-200 words) - replaces "basic"
     - `moderate` (250-350 words) - replaces "enhanced"
     - `detailed` (400-500 words) - replaces "advanced" (DEFAULT)
     - `exhaustive` (600-1000 words) - replaces "cinematic"
   - Removed confusing "auto" option
   - Added clear tooltips explaining each option
   - Backward compatible - old tier names still work internally

3. **Image-to-Video Mode Without Image Input**
   - Added optional `reference_image` input (IMAGE type)
   - Integrated Qwen3-VL vision analysis for image captioning
   - Automatic mode detection (text-to-video vs image-to-video)
   - Removed manual "mode" dropdown - now auto-detected
   - Status display shows "(with image)" when image is provided

#### Added
- `_apply_operation_mode()` - Applies operation-specific instructions to LLM
- `_process_reference_image()` - Qwen3-VL integration for image analysis
- Tier name mapping in expansion_engine.py for backward compatibility
- Enhanced status messages showing operation mode, detail level, and image usage
- Updated metadata for saved files

#### Documentation
- `docs/ADVANCED_NODE_REDESIGN.md` - Complete redesign documentation
- `BUGFIX_SUMMARY.md` - Quick reference for fixes

### Fixed - All Nodes (Emphasis & Alternation Syntax)
- **Emphasis Syntax Preservation**: Fixed `(keyword:1.5)` being mangled by LLM
  - Added `_preserve_emphasis_syntax()` and `_restore_emphasis_syntax()` methods
  - Emphasis patterns protected with placeholders during LLM processing
  - Applied to: prompt_expander_node.py and prompt_expander_node_advanced.py
  
- **Alternation Syntax Support**: Added `{option1|option2|option3}` random selection
  - Added `_process_alternations()` method
  - Handles nested alternations up to 10 levels
  - Applied to: prompt_expander_node.py and prompt_expander_node_advanced.py

#### Documentation
- `docs/BUGFIX_ADVANCED_NODE.md` - Technical details of emphasis/alternation fixes

---

## [1.7.0] - 2025-10-16

### Added - Text-to-Image Node v1.7
- **Reference Image Analysis**: Images now properly analyzed for dimensions, brightness, and color tones
- **Prompt Length Control**: 6 options (very_short, short, medium, long, very_long, auto)
- **Genre/Style Control**: 22 genre options with mood guidance (cinematic, horror, cyberpunk, noir, etc.)
- **Subject Framing**: 14 shot types (close-up, wide shot, cowboy shot, etc.)
- **Subject Pose**: 17 pose options (standing, action, contrapposto, etc.)
- **Enhanced System Prompts**: Genre guidance with descriptive mood instructions

### Fixed
- Reference images now actually used in prompt enhancement (was placeholder before)
- Reference image characteristics prominently displayed in LLM prompt

### Documentation
- UPDATE_V17_ENHANCED_CONTROLS.md - Comprehensive v1.7 guide
- QUICK_REF_V17.md - Fast reference for new features

---

## [1.6.1] - 2025-10-16

### Fixed - Critical Bug Fixes
- **Settings Leakage**: Fixed settings appearing in output with "| Settings:" separator
- **Emphasis Syntax**: Fixed `(keyword:1.5)` being broken by LLM processing
  - Implemented preserve/restore system with placeholders
  - Weight syntax now preserved exactly
- **Settings in Output**: Added regex cleanup to strip any leaked settings

### Added
- **Alternation Syntax**: Support for `{option1|option2|option3}` random selection
- **Tooltip Updates**: Added usage instructions for emphasis and alternation
- **Test Suite**: Unit tests for all bug fixes (test_txt2img_bugfixes.py)

### Documentation
- BUGFIX_V161.md - Technical documentation of fixes
- TESTING_GUIDE_V161.md - User testing guide with examples

---

## [1.6.0] - 2025-10

### Added - Text-to-Image Node
- **New Node**: Text-to-Image Prompt Enhancer
- **8 Platform Support**: Flux, SDXL, Pony Diffusion, Illustrious XL, Chroma, Qwen Image, Qwen Edit, Wan Image
- **Reference Images**: Optional 1-2 image inputs
- **Advanced Controls**: 
  - Camera: angle, composition
  - Lighting: source, quality, time of day, weather
  - Style: art style, color mood, detail level
- **Quality Emphasis**: Platform-specific quality tokens
- **Wildcard Random**: Auto-variety in batch generation

### Changed - Rebranding
- All nodes moved to "Eric Prompt Enhancers" category
- Node display names updated
- Consistent branding across all nodes

### Added - Platform Support
- **Pony Diffusion**: Booru tag format, score tokens
- **Illustrious XL**: Danbooru tag format, detailed character tags
- **Chroma/Meissonic**: Natural language, complex scenes
- **Wan Image**: Cinematography terms, professional format

### Documentation
- TXT2IMG_GUIDE.md - Comprehensive 20+ page guide
- UPDATE_V16_ERIC.md - Rebranding and new features
- Platform-specific examples and best practices

---

## [1.5.0] - 2025

### Added - Image-to-Image Node
- **New Node**: Image-to-Image Prompt Expander
- **5 Platforms**: Flux Redux, SDXL Img2Img, Hunyuan, Qwen Edit, Wan Edit
- **Vision Analysis**: Automatic source image understanding
- **Transformation Controls**: Style transfer, detail, creativity
- **Dual Engine**: Separate expansion engine for img2img

### Documentation
- IMG2IMG_GUIDE.md - Complete img2img guide
- Platform comparison and use cases

---

## [1.3.0] - 2025

### Added - Image-to-Video Node
- **New Node**: Image-to-Video Prompt Expander
- **Vision Model Integration**: Automatic image analysis
- **Motion Descriptions**: AI-generated movement details
- **Mode Support**: Combines image analysis with expansion tiers

---

## [1.2.0] - 2025

### Added - Advanced Node
- **New Node**: Video Prompt Expander (Advanced)
- **50+ Controls**: Granular aesthetic settings
- **Lighting Controls**: Light source, type, time of day
- **Camera Controls**: Shot size, composition, lens, angle, movement
- **Color/Style**: Tone, visual style, effects
- **Motion/Emotion**: Character emotion, dynamics

---

## [1.0.0] - 2025-01-07

### Added - Initial Release
- **Video Prompt Expander**: Simple preset-based expansion
- **5 Expansion Tiers**: Auto, Basic, Enhanced, Advanced, Cinematic
- **6 Style Presets**: Cinematic, Surreal, Action, Stylized, Noir, Random
- **LLM Backends**: LM Studio and Ollama support
- **Text-to-Video Mode**: Transform simple text prompts
- **Keyword Integration**: Positive and negative keywords
- **File Export**: Save with metadata
- **Auto-Detection**: Analyzes prompt complexity

### Features
- Wan 2.2 framework implementation
- Multiple variation generation (up to 3)
- Temperature control
- Configurable API endpoints
- Status output with error messages

### Documentation
- README.md with usage instructions
- CONFIGURATION.md with examples
- LM_STUDIO_SETUP.md for backend setup
- Test script for verification

---

## Version Summary

| Version | Date | Major Features |
|---------|------|----------------|
| **1.7.0** | Oct 2025 | Reference images fixed, Length/Genre/Framing/Pose controls |
| **1.6.1** | Oct 2025 | Bug fixes: settings, emphasis, alternation |
| **1.6.0** | Oct 2025 | Text-to-Image node, 8 platforms, rebranding |
| **1.5.0** | 2025 | Image-to-Image node, 5 platforms |
| **1.3.0** | 2025 | Image-to-Video node, vision model |
| **1.2.0** | 2025 | Advanced node, 50+ controls |
| **1.0.0** | Jan 2025 | Initial release, video prompts |

---

## Planned Features

### Future Enhancements
- [ ] Vision AI integration (CLIP, BLIP) for deep image understanding
- [ ] Multi-image blending with weights
- [ ] Explicit style transfer from reference images
- [ ] Preset combinations and saving
- [ ] Advanced pose library (yoga, martial arts, dance)
- [ ] Genre mixing (noir + cyberpunk, etc.)
- [ ] Batch processing optimization
- [ ] Prompt templates library
- [ ] Token counting and estimation
- [ ] A/B testing for variations
- [ ] Additional LLM backend support
- [ ] Custom platform configurations

---

## Known Issues

None currently reported for v1.7.0.

Previous issues (fixed in v1.6.1):
- ~~Settings appearing in output~~ - Fixed
- ~~Emphasis syntax broken~~ - Fixed
- ~~No alternation support~~ - Fixed

---

## Migration Notes

### From 1.6.1 to 1.7.0
- Fully backward compatible
- New inputs have sensible defaults
- Existing workflows continue to work
- Restart ComfyUI to see new controls

### From 1.6.0 to 1.6.1
- Bug fix update, no breaking changes
- Emphasis syntax now preserved
- Update recommended for all users

### From 1.5.0 to 1.6.0
- Category changed to "Eric Prompt Enhancers"
- Update workflows to use new category
- All functionality preserved

---

## Technical Requirements

- **Python**: 3.8+
- **ComfyUI**: Latest version recommended
- **LLM Backend**: LM Studio or Ollama
- **RAM**: 8GB minimum, 16GB+ recommended
- **GPU**: Optional (LLM can run on CPU)

---

## Credits

**Author**: Eric Hiss ([@EricRollei](https://github.com/EricRollei))

**Dependencies**:
- ComfyUI - GPL-3.0
- PyTorch - BSD-style
- NumPy - BSD
- Pillow - HPND
- requests - Apache 2.0
- LM Studio - Proprietary
- Ollama - MIT

**Platforms**:
- Flux by Black Forest Labs
- SDXL by Stability AI
- Pony Diffusion by Astralite
- Illustrious XL by OnomaAI Research
- Chroma/Meissonic by Tencent AI Lab
- Qwen by Alibaba Cloud
- Wan by Wuhan AI Institute

---

## Support

- **Issues**: [GitHub Issues](https://github.com/EricRollei/video_prompter/issues)
- **Email**: eric@historic.camera, eric@rollei.us
- **Documentation**: See [docs/](docs/) folder

---

**Made with ❤️ by Eric Hiss**
