"""
ComfyUI Nodes: Eric's Prompt Enhancers for ComfyUI
Description: A comprehensive suite of AI-powered prompt enhancement nodes for ComfyUI
using local LLMs (LM Studio or Ollama). Transform simple prompts into detailed,
platform-optimized descriptions for video and image generation.

Includes:
- Video Prompt Expander: Simple, preset-based video prompt expansion
- Video Prompt Expander (Advanced): Granular control over video aesthetics with 50+ controls
- Image-to-Video Prompt Expander: Vision model analyzes image + motion expansion
- Image-to-Image Prompt Expander: Platform-aware img2img prompt generation (5 platforms)
- Text-to-Image Prompt Enhancer: Advanced multi-platform image prompt generation (8 platforms)

Features:
- 8 image platforms: Flux, SDXL, Pony Diffusion, Illustrious XL, Chroma, Qwen Image/Edit, Wan Image
- Multiple expansion tiers: Auto, Basic, Enhanced, Advanced, Cinematic
- Style presets: Cinematic, Surreal, Action, Stylized, Noir, Random
- Advanced controls: Camera, lighting, weather, time of day, composition, genre, framing, pose
- Reference image support with visual analysis
- Wildcard random options for variety
- Platform-specific token optimization
- Emphasis syntax: (keyword:1.5)
- Alternation syntax: {option1|option2|option3}
- LoRA trigger and keyword integration
- File export with metadata

Author: Eric Hiss (GitHub: EricRollei)
Contact: [eric@historic.camera, eric@rollei.us]
Version: 1.7.0
Date: October 2025
License: Dual License (Non-Commercial and Commercial Use)
Copyright (c) 2025 Eric Hiss. All rights reserved.

Dual License:
1. Non-Commercial Use: This software is licensed under the terms of the
   Creative Commons Attribution-NonCommercial 4.0 International License.
   To view a copy of this license, visit http://creativecommons.org/licenses/by-nc/4.0/
   
2. Commercial Use: For commercial use, a separate license is required.
   Please contact Eric Hiss at [eric@historic.camera, eric@rollei.us] for licensing options.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT.

Dependencies and Credits:
- Python 3.8+ (https://www.python.org/) - PSF License
- PyTorch (https://pytorch.org/) - BSD-style License
- NumPy (https://numpy.org/) - BSD License
- Pillow/PIL (https://python-pillow.org/) - HPND License
- requests (https://requests.readthedocs.io/) - Apache 2.0 License
- ComfyUI (https://github.com/comfyanonymous/ComfyUI) - GPL-3.0 License
- LM Studio (https://lmstudio.ai/) - Proprietary (Optional)
- Ollama (https://ollama.ai/) - MIT License (Optional)

Platform Knowledge Credits:
- Flux by Black Forest Labs
- SDXL by Stability AI
- Pony Diffusion by Astralite
- Illustrious XL by OnomaAI Research
- Chroma/Meissonic by Tencent AI Lab
- Qwen by Alibaba Cloud
- Wan by Wuhan AI Institute
"""

from .prompt_expander_node import AIVideoPromptExpander
from .prompt_expander_node_advanced import AIVideoPromptExpanderAdvanced
from .image_to_video_node import ImageToVideoPromptExpander
from .image_to_image_node import ImageToImagePromptExpander
from .text_to_image_node import TextToImagePromptEnhancer

# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "EricVideoPromptExpander": AIVideoPromptExpander,
    "EricVideoPromptExpanderAdvanced": AIVideoPromptExpanderAdvanced,
    "EricImageToVideoPromptExpander": ImageToVideoPromptExpander,
    "EricImageToImagePromptExpander": ImageToImagePromptExpander,
    "EricTextToImagePromptEnhancer": TextToImagePromptEnhancer
}

# Display names in ComfyUI
NODE_DISPLAY_NAME_MAPPINGS = {
    "EricVideoPromptExpander": "Video Prompt Expander",
    "EricVideoPromptExpanderAdvanced": "Video Prompt Expander (Advanced)",
    "EricImageToVideoPromptExpander": "Image-to-Video Prompt Expander",
    "EricImageToImagePromptExpander": "Image-to-Image Prompt Expander",
    "EricTextToImagePromptEnhancer": "Text-to-Image Prompt Enhancer"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
