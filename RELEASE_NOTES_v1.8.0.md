# Release Notes - v1.8.0

**Release Date:** October 24, 2025

---

## 🎉 Major Release: Advanced Node Redesign + Syntax Fixes

This release includes a **complete redesign** of the Advanced Prompt Expander Node and critical syntax preservation fixes for all video nodes.

---

## ⭐ Highlights

### 1. Advanced Node Completely Redesigned

The Advanced Prompt Expander Node has been rebuilt from the ground up to address three critical usability issues:

**✅ Operation Modes** - Finally, you can modify existing prompts!
- `expand_from_idea` - Original expansion behavior
- `refine_existing` - Polish and improve existing prompts
- `modify_style` - Change aesthetic while keeping subject
- `add_details` - Add descriptive richness

**✅ Clear Detail Levels** - No more confusing tiers!
- Renamed from "basic/enhanced/advanced/cinematic" to "concise/moderate/detailed/exhaustive"
- Added tooltips explaining each level
- Removed confusing "auto" mode
- Word counts clearly shown in tooltips

**✅ Image Input Support** - Image-to-video actually works!
- Optional `reference_image` input
- Qwen3-VL vision analysis integration
- Automatic mode detection (text vs image-to-video)
- Status shows when image is being used

### 2. Syntax Preservation for All Video Nodes

Both video nodes now properly preserve special syntax:

**Emphasis Syntax** - Control weights like Stable Diffusion
```
(keyword:1.5)    # Increase importance 1.5x
(keyword:0.5)    # Decrease importance 0.5x
```

**Alternation Syntax** - Random selection for variety
```
{cat|dog|rabbit}              # Picks one randomly
{red|blue|green} dress        # Random color
```

---

## 🔧 What Changed

### Modified Files (Core Functionality)

**Advanced Node**
- `prompt_expander_node_advanced.py` - Complete redesign
  - Added operation modes
  - Renamed tiers to detail levels
  - Added optional image input
  - Added Qwen3-VL integration
  - Added `_apply_operation_mode()` method
  - Added `_process_reference_image()` method
  - Updated metadata and status messages

**Basic Video Node**
- `prompt_expander_node.py` - Syntax preservation
  - Added `_process_alternations()` method
  - Added `_preserve_emphasis_syntax()` method
  - Added `_restore_emphasis_syntax()` method

**Engine Updates**
- `expansion_engine.py` - Backward compatibility
  - Added tier name mapping (concise→basic, etc.)
  - Supports both old and new naming
  - Improved tier detection logic

**Vision Backend**
- `qwen3_vl_backend.py` - NEW FILE
  - Qwen3-VL integration for image analysis
  - Support for multiple Qwen3-VL models
  - Quantization options (4bit, 8bit)

### Documentation Updates

**New Documentation**
- `README.md` - Completely rewritten for clarity
- `docs/ADVANCED_NODE_REDESIGN.md` - Complete redesign details
- `docs/BUGFIX_ADVANCED_NODE.md` - Syntax preservation technical docs
- `docs/BUGFIX_SUMMARY.md` - Quick reference for all fixes
- `VISION_BACKEND_GUIDE.md` - Qwen3-VL setup guide
- `caption-instructions.md` - Vision backend usage

**Updated Documentation**
- `CHANGELOG.md` - v1.8.0 entry added
- `docs/CONFIGURATION.md` - Updated for new parameters
- `docs/IMG2IMG_GUIDE.md` - Minor updates
- `docs/QUICKSTART.md` - Updated for v1.8

**Archived Documentation** (moved to `docs/archive/`)
- Old README
- UPDATE_NOTES.md (v1.0-1.1)
- UPDATE_NOTES_V12.md
- UPDATE_V13.md
- UPDATE_V15.md
- UPDATE_V16_ERIC.md
- UPDATE_V17_ENHANCED_CONTROLS.md (kept in main docs too)
- FILE_CHANGES.md
- SETUP_COMPLETE.md
- BUGFIX_AUTO_MODE.md
- GITHUB_PUBLICATION_COMPLETE.md

### Support Files

- `requirements.txt` - Added vision dependencies (optional)
- `.gitignore` - Already properly configured

---

## 📦 Installation

### For New Users

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/EricRollei/Local_LLM_Prompt_Enhancer.git video_prompter
cd video_prompter
pip install -r requirements.txt
```

### For Existing Users

```bash
cd ComfyUI/custom_nodes/video_prompter
git pull
pip install -r requirements.txt --upgrade
```

Restart ComfyUI after updating.

### Optional: Vision Support

For image analysis features:

```bash
pip install transformers>=4.42.0 accelerate>=0.30.0 huggingface_hub>=0.23.0 bitsandbytes>=0.43.0
```

---

## 🚀 Migration Guide

### Existing Workflows

**Old Advanced Node Configuration:**
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

### Tier Name Mapping

| Old Name | New Name | Still Works? |
|----------|----------|--------------|
| basic | concise | ✅ Yes (internally mapped) |
| enhanced | moderate | ✅ Yes (internally mapped) |
| advanced | detailed | ✅ Yes (internally mapped) |
| cinematic | exhaustive | ✅ Yes (internally mapped) |
| auto | (removed) | ❌ Choose explicitly now |

### Mode Parameter Removed

The manual "mode" dropdown is gone. Mode is now auto-detected:
- **No image** = text-to-video mode
- **With image** = image-to-video mode

---

## 💡 New Workflows Enabled

### 1. Refine Existing Prompt
```
Node: Video Prompt Expander (Advanced)
Input: [Your existing 300-word prompt]
Operation: refine_existing
Detail: detailed
Result: Polished version with better flow
```

### 2. Change Style of Existing Prompt
```
Node: Video Prompt Expander (Advanced)
Input: [Your existing prompt about a detective scene]
Operation: modify_style
Preset: noir (changed from cinematic)
Detail: detailed
Result: Same detective scene, now in noir style
```

### 3. Image-to-Video with Context
```
Node: Video Prompt Expander (Advanced)
Reference Image: [Your reference image]
Input: "Make the subject move towards the camera dramatically"
Operation: expand_from_idea
Detail: detailed
Result: Detailed video prompt incorporating image analysis + your direction
```

### 4. Add More Detail to Good Prompt
```
Node: Video Prompt Expander (Advanced)
Input: [Your working prompt that's a bit sparse]
Operation: add_details
Detail: exhaustive
Result: Same prompt but with atmospheric details, textures, emotions added
```

---

## 🐛 Known Issues

None currently reported.

---

## 🔜 Future Plans

Possible future enhancements:
- Support for video input (Qwen3-VL can handle it)
- Multiple reference images
- Image directive modes (like text_to_image_node)
- Batch processing with different operation modes per prompt
- More vision backends

---

## 🙏 Credits

Special thanks to:
- Users who reported the confusing tier system
- Users who requested the ability to modify existing prompts
- Beta testers who helped validate the redesign
- The ComfyUI community for continued support

---

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

---

## 📚 Documentation

- [README.md](README.md) - Main documentation
- [QUICKSTART.md](docs/QUICKSTART.md) - Get started quickly
- [ADVANCED_NODE_REDESIGN.md](docs/ADVANCED_NODE_REDESIGN.md) - Complete redesign details
- [VISION_BACKEND_GUIDE.md](VISION_BACKEND_GUIDE.md) - Image analysis setup
- [BUGFIX_SUMMARY.md](docs/BUGFIX_SUMMARY.md) - Quick reference

---

**Version:** 1.8.0  
**Release Type:** Major Update  
**Breaking Changes:** None (fully backward compatible)  
**Recommended Action:** Update and restart ComfyUI
