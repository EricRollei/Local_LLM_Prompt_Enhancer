# Changelog

All notable changes to Eric's Prompt Enhancers for ComfyUI.

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
