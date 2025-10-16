"""
Platform-specific configurations for image generation models
Each platform has different prompting preferences and optimal formats
"""

PLATFORMS = {
    "flux": {
        "name": "Flux (FLUX.1-dev/schnell)",
        "description": "Black Forest Labs - Natural language, detailed, artistic",
        "prompt_style": "natural_detailed",
        "optimal_length": "long",  # 75-150 tokens
        "supports": ["style_references", "artist_names", "quality_modifiers"],
        "preferences": [
            "Natural language descriptions",
            "Artistic style references (e.g., 'in the style of...')",
            "Photography terms (e.g., 'professional photograph', 'studio lighting')",
            "Quality descriptors (e.g., 'masterpiece', 'highly detailed', '8k')",
            "Medium specifications (e.g., 'oil painting', 'digital art', 'photograph')"
        ],
        "quality_tokens": [
            "masterpiece", "best quality", "highly detailed", "8k uhd", 
            "professional", "award-winning", "stunning", "exceptional quality"
        ],
        "avoid": [
            "Too technical/robotic language",
            "Repetitive keywords",
            "Overly structured format"
        ]
    },
    
    "wan22": {
        "name": "Wan 2.2 (Video - adapted for image)",
        "description": "Tencent - Technical cinematography terms, structured",
        "prompt_style": "technical_structured",
        "optimal_length": "medium",  # 50-100 tokens
        "supports": ["cinematography_terms", "lighting_types", "composition_rules"],
        "preferences": [
            "Specific lighting terminology (soft lighting, edge lighting, etc.)",
            "Composition rules (rule of thirds, symmetrical, etc.)",
            "Technical quality terms",
            "Structured descriptions (subject, setting, lighting, composition)"
        ],
        "technical_terms": {
            "lighting": ["soft lighting", "hard lighting", "edge lighting", "rim lighting", "natural lighting"],
            "composition": ["center composition", "rule of thirds", "symmetrical composition", "balanced composition"],
            "quality": ["high contrast", "low contrast", "saturated colors", "desaturated colors"]
        },
        "avoid": [
            "Casual language",
            "Abstract artistic terms",
            "Long flowery descriptions"
        ]
    },
    
    "hunyuan_image": {
        "name": "Hunyuan Image",
        "description": "Tencent - Realistic, good with Asian subjects, simpler English",
        "prompt_style": "clear_concise",
        "optimal_length": "medium",  # 40-80 tokens
        "supports": ["realistic_descriptions", "asian_aesthetics", "simple_modifiers"],
        "preferences": [
            "Clear, direct descriptions",
            "Simpler English (avoids complex vocabulary)",
            "Photorealism focus",
            "Good with Asian aesthetics and subjects",
            "Quality over quantity of words"
        ],
        "quality_tokens": [
            "high quality", "detailed", "realistic", "clear", 
            "professional", "beautiful", "sharp"
        ],
        "avoid": [
            "Complex sentence structures",
            "Abstract artistic concepts",
            "Too many adjectives",
            "Overly technical jargon"
        ]
    },
    
    "qwen_image": {
        "name": "Qwen Image",
        "description": "Alibaba - Natural language, versatile, good with diverse styles",
        "prompt_style": "balanced_natural",
        "optimal_length": "medium",  # 50-100 tokens
        "supports": ["natural_descriptions", "style_variety", "cultural_elements"],
        "preferences": [
            "Natural, conversational descriptions",
            "Good with various art styles",
            "Handles both Eastern and Western aesthetics",
            "Balanced detail level",
            "Cultural elements well understood"
        ],
        "quality_tokens": [
            "high quality", "detailed", "professional", "beautiful",
            "intricate", "refined", "elegant"
        ],
        "avoid": [
            "Overly formal language",
            "Excessive technical terms",
            "Platform-specific keywords from other models"
        ]
    },
    
    "qwen_image_edit": {
        "name": "Qwen Image Edit",
        "description": "Alibaba - Specialized for editing, clear change instructions",
        "prompt_style": "edit_focused",
        "optimal_length": "short",  # 20-50 tokens
        "supports": ["edit_instructions", "preservation_hints", "change_specifications"],
        "preferences": [
            "VERY concise change instructions",
            "Focus on what changes, not what stays",
            "Clear before/after language",
            "Direct commands (e.g., 'change X to Y', 'add Z', 'remove W')",
            "Preservation hints (e.g., 'keep background', 'maintain composition')"
        ],
        "quality_tokens": [
            "seamless", "natural", "realistic", "consistent", "high quality"
        ],
        "edit_templates": [
            "Change {element} to {new_value}",
            "Add {new_element} to {location}",
            "Remove {element}",
            "Replace {old} with {new}",
            "Modify {element}: {description}"
        ],
        "avoid": [
            "Long descriptions of unchanged elements",
            "Redundant information",
            "Vague change requests",
            "Overly artistic language"
        ]
    },
    
    "sd_xl": {
        "name": "Stable Diffusion XL",
        "description": "Stability AI - Token-aware, quality emphasis, booru tags optional",
        "prompt_style": "token_optimized",
        "optimal_length": "medium",  # 40-75 tokens (SDXL limit)
        "supports": ["quality_emphasis", "booru_tags", "natural_language"],
        "preferences": [
            "Front-load important concepts",
            "Quality/style tokens at start",
            "Can use natural language or danbooru tags",
            "Emphasis with (parentheses) or attention syntax",
            "Negative prompts very important"
        ],
        "quality_tokens": [
            "masterpiece", "best quality", "highly detailed", "professional",
            "8k", "intricate details", "sharp focus", "vibrant"
        ],
        "avoid": [
            "Exceeding ~75 tokens (diminishing returns)",
            "Repetitive terms",
            "Too many parentheses/emphasis"
        ]
    },
    
    "pony": {
        "name": "Pony Diffusion",
        "description": "Anime/furry model - Booru tags, score system, specific quality tags required",
        "prompt_style": "booru_structured",
        "optimal_length": "medium",  # 40-80 tokens
        "supports": ["booru_tags", "score_system", "quality_modifiers", "rating_tags"],
        "preferences": [
            "Start with score_9, score_8_up, score_7_up",
            "Use danbooru tag format",
            "Underscores instead of spaces in tags",
            "Specific quality tags at beginning",
            "Rating at start (safe/questionable/explicit)",
            "Character descriptions in tag format"
        ],
        "quality_tokens": [
            "score_9", "score_8_up", "score_7_up", "best quality", "amazing quality",
            "very aesthetic", "absurdres", "newest"
        ],
        "required_positive": [
            "score_9", "score_8_up", "score_7_up"
        ],
        "required_negative": [
            "score_6", "score_5", "score_4", "worst quality", "low quality",
            "bad anatomy", "sketch", "jpeg artifacts"
        ],
        "avoid": [
            "Natural language descriptions",
            "Spaces in multi-word concepts (use underscores)",
            "Missing score tags",
            "Long narrative descriptions"
        ]
    },
    
    "illustrious": {
        "name": "Illustrious XL",
        "description": "Anime model - Booru tags, quality emphasis, detailed character descriptions",
        "prompt_style": "booru_detailed",
        "optimal_length": "medium",  # 50-100 tokens
        "supports": ["booru_tags", "character_details", "quality_emphasis", "anime_specific"],
        "preferences": [
            "Start with quality tags (masterpiece, best quality)",
            "Use danbooru tag format with underscores",
            "Detailed character appearance tags",
            "Clothing and accessory tags",
            "Background and atmosphere tags",
            "Lighting and color mood tags"
        ],
        "quality_tokens": [
            "masterpiece", "best quality", "very aesthetic", "absurdres",
            "intricate details", "official art", "extremely detailed"
        ],
        "avoid": [
            "Overly long narrative descriptions",
            "Realistic photography terms",
            "3D render terminology"
        ]
    },
    
    "chroma": {
        "name": "Chroma (Meissonic)",
        "description": "MeissonFlow - Natural language, handles complex compositions, multiple subjects",
        "prompt_style": "natural_compositional",
        "optimal_length": "long",  # 100-200 tokens
        "supports": ["complex_scenes", "multiple_subjects", "natural_language", "detailed_positioning"],
        "preferences": [
            "Natural, detailed descriptions",
            "Can handle multiple subjects well",
            "Spatial relationships clearly described",
            "Complex compositional instructions",
            "Quality descriptors throughout",
            "Good with scene complexity"
        ],
        "quality_tokens": [
            "high quality", "detailed", "professional", "intricate",
            "masterpiece", "stunning", "exceptional composition"
        ],
        "avoid": [
            "Too simplistic descriptions",
            "Single-word tags",
            "Overly technical jargon"
        ]
    },
    
    "wan_image": {
        "name": "Wan Image",
        "description": "Tencent video model adapted for images - Technical, structured, cinematic",
        "prompt_style": "technical_cinematic",
        "optimal_length": "medium",  # 60-120 tokens
        "supports": ["cinematography_terms", "technical_specs", "lighting_details", "composition_rules"],
        "preferences": [
            "Technical cinematography terminology",
            "Structured format: subject, setting, lighting, composition",
            "Specific lighting types (soft, hard, edge, rim, etc.)",
            "Composition rules (rule of thirds, symmetrical, etc.)",
            "Professional photography terms",
            "Color grading and mood descriptors"
        ],
        "quality_tokens": [
            "high quality", "professional", "detailed", "sharp focus",
            "well composed", "balanced lighting", "cinematic quality"
        ],
        "avoid": [
            "Casual language",
            "Abstract artistic terms without technical grounding",
            "Overly long flowery descriptions"
        ]
    }
}


def get_platform_config(platform_name: str) -> dict:
    """Get configuration for a specific platform"""
    return PLATFORMS.get(platform_name, PLATFORMS["flux"])


def get_platform_list() -> list:
    """Get list of supported platform names"""
    return list(PLATFORMS.keys())


def get_platform_display_names() -> list:
    """Get list of platform display names for UI"""
    return [config["name"] for config in PLATFORMS.values()]


def format_for_platform(
    description: str,
    change_request: str,
    platform: str,
    style: str = None,
    quality_emphasis: bool = True
) -> str:
    """
    Format a prompt optimally for the target platform
    
    Args:
        description: Base image description from vision model
        change_request: User's requested changes
        platform: Target platform name
        style: Optional style override
        quality_emphasis: Whether to add quality tokens
    """
    config = get_platform_config(platform)
    
    if platform == "qwen_image_edit":
        # Edit model: very concise, focus on changes only
        return _format_for_edit(description, change_request, config, quality_emphasis)
    
    elif platform == "flux":
        # Flux: natural, detailed, artistic
        return _format_for_flux(description, change_request, config, style, quality_emphasis)
    
    elif platform == "wan22":
        # Wan: technical, structured
        return _format_for_wan(description, change_request, config, quality_emphasis)
    
    elif platform == "hunyuan_image":
        # Hunyuan: clear, concise, realistic
        return _format_for_hunyuan(description, change_request, config, quality_emphasis)
    
    elif platform == "qwen_image":
        # Qwen: balanced, natural
        return _format_for_qwen(description, change_request, config, quality_emphasis)
    
    elif platform == "sd_xl":
        # SDXL: token-optimized
        return _format_for_sdxl(description, change_request, config, quality_emphasis)
    
    else:
        # Default: balanced approach
        return f"{description}, {change_request}"


def _format_for_edit(description: str, changes: str, config: dict, quality: bool) -> str:
    """Format for edit models - very concise, change-focused"""
    # Extract key elements from description
    # Focus only on changes
    prompt = changes
    if quality:
        prompt = f"{prompt}, seamless, natural, high quality"
    return prompt


def _format_for_flux(description: str, changes: str, config: dict, style: str, quality: bool) -> str:
    """Format for Flux - natural, detailed, artistic"""
    parts = []
    
    if quality:
        parts.append("masterpiece, best quality, highly detailed")
    
    # Combine description and changes naturally
    if changes:
        parts.append(f"{description}, with {changes}")
    else:
        parts.append(description)
    
    if style:
        parts.append(f"in the style of {style}")
    
    return ", ".join(parts)


def _format_for_wan(description: str, changes: str, config: dict, quality: bool) -> str:
    """Format for Wan - technical, structured"""
    parts = []
    
    # Structured format
    parts.append(description)
    
    if changes:
        parts.append(changes)
    
    # Add technical quality terms
    if quality:
        parts.append("high contrast, professional composition, detailed")
    
    return ", ".join(parts)


def _format_for_hunyuan(description: str, changes: str, config: dict, quality: bool) -> str:
    """Format for Hunyuan - clear, concise, realistic"""
    parts = []
    
    # Simple, direct
    if changes:
        parts.append(f"{description}, {changes}")
    else:
        parts.append(description)
    
    if quality:
        parts.append("high quality, detailed, realistic")
    
    return ", ".join(parts)


def _format_for_qwen(description: str, changes: str, config: dict, quality: bool) -> str:
    """Format for Qwen - balanced, natural"""
    parts = []
    
    # Natural combination
    if changes:
        parts.append(f"{description}, {changes}")
    else:
        parts.append(description)
    
    if quality:
        parts.append("high quality, detailed, professional")
    
    return ", ".join(parts)


def _format_for_sdxl(description: str, changes: str, config: dict, quality: bool) -> str:
    """Format for SDXL - token-optimized, front-loaded"""
    parts = []
    
    # Quality tokens first for SDXL
    if quality:
        parts.append("masterpiece, best quality, highly detailed")
    
    # Main content
    if changes:
        parts.append(f"{description}, {changes}")
    else:
        parts.append(description)
    
    # Keep under ~75 tokens
    result = ", ".join(parts)
    tokens = result.split()
    if len(tokens) > 75:
        result = " ".join(tokens[:75])
    
    return result


def get_negative_prompt_for_platform(platform: str, custom_negatives: list = None) -> str:
    """Generate platform-optimized negative prompts"""
    
    base_negatives = {
        "flux": "blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, signature, text",
        "wan22": "low quality, blurry, distorted, poor composition, bad lighting, flat",
        "hunyuan_image": "low quality, blurry, distorted, unrealistic, bad details",
        "qwen_image": "low quality, blurry, distorted, artifacts, bad anatomy",
        "qwen_image_edit": "unnatural, inconsistent, artifacts, seams, low quality",
        "sd_xl": "ugly, tiling, poorly drawn, bad anatomy, deformed, disfigured, worst quality, low quality, blurry",
        "pony": "score_6, score_5, score_4, worst quality, low quality, bad anatomy, sketch, jpeg artifacts, blurry, simple background",
        "illustrious": "worst quality, low quality, bad anatomy, bad hands, bad feet, deformed, disfigured, poorly drawn, blurry, jpeg artifacts",
        "chroma": "low quality, blurry, distorted, bad composition, poor details, artifacts, inconsistent lighting, flat",
        "wan_image": "low quality, blurry, poor composition, bad lighting, flat, distorted, unprofessional, amateur"
    }
    
    negative = base_negatives.get(platform, base_negatives["flux"])
    
    if custom_negatives:
        negative += ", " + ", ".join(custom_negatives)
    
    return negative
