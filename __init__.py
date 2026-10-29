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
- Alice T2V Prompt Refiner: Structures prompts specifically for the Alice T2V 14B MoE model

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
Version: 2.1.0
Date: September 2026
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
- Chroma by lodestones
- Qwen by Alibaba Cloud
- Wan by Alibaba (Wan team / Tongyi Lab)
- Alice T2V by Mirage (gomirageai)
"""

from .prompt_expander_node import AIVideoPromptExpander
from .prompt_expander_node_advanced import AIVideoPromptExpanderAdvanced
from .image_to_video_node import ImageToVideoPromptExpander
from .image_to_image_node import ImageToImagePromptExpander
from .text_to_image_node import TextToImagePromptEnhancer
from .alice_prompter_node import AlicePromptRefiner

# Prompt Database nodes
from .save_prompt_node import SavePromptToDatabase
from .search_prompt_node import SearchPromptDatabase
from .import_prompts_node import ImportPromptsToDatabase
from .browse_prompt_node import BrowsePromptDatabase

# Ideogram 4 nodes
from .ideogram_magic_node import IdeogramMagicPrompt

# Wildcard engine (core/wildcards) and variability engine (core/variability)
from .wildcard_processor_node import WildcardProcessor
from .semantic_variation_node import SemanticVariation
from .concept_survival_node import ConceptSurvivalCheck
from .surreal_node import SurrealPremise

# LoRA Suggester: moved to the Eric_LoRA_Catalog node pack (2026-10-11).

# Platform profiles (core/profiles + profiles/*.yaml)
from .platform_rewriter_node import PlatformPromptRewriter

# Prompt builders (core/builder + builders/*.yaml + web/prompt_builder.js)
from .prompt_builder_node import CharacterBuilder, PromptBuilder
from .prompt_builder_support import register_routes as _register_builder_routes

try:
    _register_builder_routes()
except Exception as _error:  # the nodes still work without the panel's routes
    print(f"[Wildcard Composer] routes not registered: {_error}")

# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "EricVideoPromptExpander": AIVideoPromptExpander,
    "EricVideoPromptExpanderAdvanced": AIVideoPromptExpanderAdvanced,
    "EricImageToVideoPromptExpander": ImageToVideoPromptExpander,
    "EricImageToImagePromptExpander": ImageToImagePromptExpander,
    "EricTextToImagePromptEnhancer": TextToImagePromptEnhancer,
    "EricAlicePromptRefiner": AlicePromptRefiner,
    # Database nodes
    "EricSavePromptToDB": SavePromptToDatabase,
    "EricSearchPromptDB": SearchPromptDatabase,
    "EricImportPromptsToDB": ImportPromptsToDatabase,
    "EricBrowsePromptDB": BrowsePromptDatabase,
    # Ideogram 4
    "EricIdeogramMagicPrompt": IdeogramMagicPrompt,
    # Wildcards
    "EricWildcardProcessor": WildcardProcessor,
    "EricSemanticVariation": SemanticVariation,
    "EricConceptSurvivalCheck": ConceptSurvivalCheck,
    "EricSurrealPremise": SurrealPremise,
    # Platform profiles
    "EricPlatformPromptRewriter": PlatformPromptRewriter,
    # Prompt builders
    "EricPromptBuilder": PromptBuilder,
    "EricCharacterBuilder": CharacterBuilder,
}

# Display names in ComfyUI
NODE_DISPLAY_NAME_MAPPINGS = {
    "EricVideoPromptExpander": "Video Prompt Expander",
    "EricVideoPromptExpanderAdvanced": "Video Prompt Expander (Advanced)",
    "EricImageToVideoPromptExpander": "Image-to-Video Prompt Expander",
    "EricImageToImagePromptExpander": "Image-to-Image Prompt Expander",
    "EricTextToImagePromptEnhancer": "Text-to-Image Prompt Enhancer",
    "EricAlicePromptRefiner": "Alice T2V Prompt Refiner",
    # Database nodes
    "EricSavePromptToDB": "Save Prompt to DB",
    "EricSearchPromptDB": "Search Prompt DB",
    "EricImportPromptsToDB": "Import Prompts to DB",
    "EricBrowsePromptDB": "Browse / Random Prompt DB",
    # Ideogram 4
    "EricIdeogramMagicPrompt": "Ideogram 4 Magic Prompt",
    # Wildcards
    "EricWildcardProcessor": "Wildcard Processor",
    "EricSemanticVariation": "Semantic Variation",
    "EricConceptSurvivalCheck": "Concept Survival Check",
    "EricSurrealPremise": "Surreal Premise",
    # Platform profiles
    "EricPlatformPromptRewriter": "Platform Prompt Rewriter",
    # Prompt builders
    "EricPromptBuilder": "Wildcard Prompt Composer",
    "EricCharacterBuilder": "Wildcard Character Composer",
}

WEB_DIRECTORY = "./web"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
