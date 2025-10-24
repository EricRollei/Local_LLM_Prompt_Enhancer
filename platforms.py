"""
Platform-specific configurations for image generation models
Each platform has different prompting preferences and optimal formats
"""

from typing import Optional, Sequence

PLATFORMS = {
    "flux": {
        "name": "Flux (FLUX.1-dev/schnell)",
        "description": "Black Forest Labs - Natural language, detailed, artistic",
        "prompt_style": "natural_detailed",
        "optimal_length": "extended (~200 words)",
        "max_words": 200,
        "max_tokens": 280,
    "quality_emphasis": False,
        "length_guidance": "Aim for about 200 words (or more) with layered, cinematic imagery.",
        "detail_expectation": "Deliver ultra-detailed, sensory-rich storytelling with multiple focal elements.",
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

    "flux_kontex": {
        "name": "Flux Kontex",
        "description": "Black Forest Labs - Context-aware variant built for extra-long descriptive prompts",
        "prompt_style": "natural_detailed",
        "optimal_length": "extended (~220 words)",
        "max_words": 220,
        "max_tokens": 320,
    "quality_emphasis": False,
        "length_guidance": "Push toward 220+ words with exhaustive scene breakdowns and cross-subject relationships.",
        "detail_expectation": "Stack contextual storytelling, environmental cues, and emotional subtext for every subject.",
        "supports": ["style_references", "artist_names", "quality_modifiers", "environmental_storytelling"],
        "preferences": [
            "Deep environmental storytelling",
            "Precise lighting and atmosphere descriptions",
            "Detailed character motivations and actions",
            "Layered color grading references",
            "Artistic nods and medium descriptors"
        ],
        "quality_tokens": [
            "masterpiece", "best quality", "ultra detailed", "hyper realistic",
            "award-winning", "cinematic lighting", "8k uhd", "immersive"
        ],
        "avoid": [
            "Short, generic summaries",
            "Sparse descriptions lacking context",
            "Repeating the same adjective without adding information"
        ]
    },

    "pixart_sigma": {
        "name": "PixArt Sigma",
        "description": "PixArt - Natural language with vibrant artistic flair",
        "prompt_style": "natural_detailed",
        "optimal_length": "extended (~210 words)",
        "max_words": 210,
        "max_tokens": 300,
    "quality_emphasis": True,
        "length_guidance": "Craft around 210 words blending cinematic staging and painterly vocabulary.",
        "detail_expectation": "Mix bold color stories, lighting gradients, and stylistic references with intricate subject detail.",
        "supports": ["style_references", "color_theory", "lighting_scenarios"],
        "preferences": [
            "Layered color palettes",
            "Dynamic lighting descriptions",
            "Specific medium references (gouache, airbrush, ink)",
            "Character expressions and body language",
            "Camera and lens hints"
        ],
        "quality_tokens": [
            "masterpiece", "vivid", "highly detailed", "dynamic lighting",
            "vibrant color", "award-winning", "studio quality", "dramatic contrast"
        ],
        "avoid": [
            "Monochrome descriptions unless intentional",
            "Under-specified backgrounds",
            "Generic phrases without artistic specificity"
        ]
    },

    "aura_flow": {
        "name": "Aura Flow",
        "description": "Stability AI - Photographic realism with flowing stylistic accents",
        "prompt_style": "natural_photo",
        "optimal_length": "extended (~180 words)",
        "max_words": 180,
        "max_tokens": 260,
    "quality_emphasis": True,
        "length_guidance": "Aim for ~180 words blending photoreal cues with stylistic direction.",
        "detail_expectation": "Combine technical photography language with vivid stylistic descriptors and ambiance cues.",
        "supports": ["photography_terms", "lighting_details", "style_modifiers"],
        "preferences": [
            "Lens and camera specifications",
            "Exposure and lighting adjectives",
            "Environment and weather context",
            "Wardrobe/fabric texture callouts",
            "Post-processing or grading notes"
        ],
        "quality_tokens": [
            "ultra high resolution", "sharp focus", "cinematic lighting", "photo-realistic",
            "8k", "professionally lit", "hyper detailed", "premium quality"
        ],
        "avoid": [
            "Overly abstract artistic terminology without photographic grounding",
            "Short clip descriptions",
            "Contradictory lighting instructions"
        ]
    },

    "noobai": {
        "name": "NoobAI",
        "description": "NoobAI diffusion model - balanced between natural language and structured tags",
        "prompt_style": "natural_balanced",
        "optimal_length": "extended (~200 words)",
        "max_words": 200,
        "max_tokens": 280,
    "quality_emphasis": True,
        "length_guidance": "Generate around 200 words focusing on clarity, character detail, and background narrative.",
        "detail_expectation": "Interleave narrative beats with descriptive art direction and technical camera hints.",
        "supports": ["natural_descriptions", "camera_language", "art_direction"],
        "preferences": [
            "Well-structured scene descriptions",
            "Clear subject hierarchy",
            "Movement or action cues",
            "Texture and material specificity",
            "Lighting and emotion descriptors"
        ],
        "quality_tokens": [
            "masterpiece", "finely detailed", "studio lighting", "ultra sharp",
            "beautiful composition", "high dynamic range", "award-winning"
        ],
        "avoid": [
            "Minimal prompts",
            "Missing background context",
            "Vague adjectives without support"
        ]
    },

    "kolors": {
        "name": "Kolors",
        "description": "Kolas Labs - vivid, color-driven imagery with strong stylistic sensibility",
        "prompt_style": "natural_detailed",
        "optimal_length": "extended (~230 words)",
        "max_words": 230,
        "max_tokens": 330,
    "quality_emphasis": True,
        "length_guidance": "Push toward 230 words emphasizing color design, lighting, and stylistic motifs.",
        "detail_expectation": "Paint with words—describe palettes, gradients, reflections, and mood-rich environments in depth.",
        "supports": ["color_theory", "lighting_scenarios", "style_references", "mood_descriptors"],
        "preferences": [
            "Chromatic palettes with hex or descriptive names",
            "Lighting direction, intensity, and softness",
            "Scene moods and emotions",
            "Material/texture contrasts",
            "Creative stylistic references (art movements, artists)"
        ],
        "quality_tokens": [
            "vibrant color", "highly detailed", "dynamic lighting", "cinematic",
            "immersive", "ultra sharp", "award-winning", "rich texture"
        ],
        "avoid": [
            "Desaturated or generic descriptions unless intentional",
            "Color contradictions",
            "Sparse scene context"
        ]
    },
    
    "wan22": {
        "name": "Wan 2.2 (Video - adapted for image)",
        "description": "Tencent - Technical cinematography terms, structured",
        "prompt_style": "technical_structured",
        "optimal_length": "extended (~250 words)",
        "max_words": 250,
        "max_tokens": 360,
    "quality_emphasis": True,
        "length_guidance": "Target roughly 250 words with full cinematic breakdowns.",
        "detail_expectation": "Deliver exhaustive cinematography cues across subject, lighting, lensing, and motion.",
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
        "optimal_length": "extended (~250 words)",
        "max_words": 250,
        "max_tokens": 360,
    "quality_emphasis": True,
        "length_guidance": "Push toward 250 words while staying clear and photographic.",
        "detail_expectation": "Even in simple English, include exhaustive realism cues (lighting, setting, styling).",
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
        "optimal_length": "extended (~250 words)",
        "max_words": 250,
        "max_tokens": 360,
    "quality_emphasis": True,
        "length_guidance": "Stretch toward 250 words with purposeful, imaginative detail.",
        "detail_expectation": "Blend cultural nuance, mood, and scene-building for maximum richness.",
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
        "optimal_length": "concise (5-30 words)",
        "max_words": 30,
        "max_tokens": 45,
    "quality_emphasis": False,
        "length_guidance": "Stay between 5 and 30 words; short, direct edit commands only.",
        "detail_expectation": "Laser-focused on the requested change; avoid full-scene rewrites.",
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
    
    "sd_1_5": {
        "name": "Stable Diffusion 1.5",
        "description": "Stability AI - Classic diffusion model favoring dense, token-efficient prompts",
        "prompt_style": "token_optimized",
        "optimal_length": "extended (≤120 tokens ~90 words)",
        "max_words": 90,
        "max_tokens": 120,
    "quality_emphasis": True,
        "length_guidance": "Stay under ~120 tokens (~90 words) while front-loading essential quality and scene descriptors.",
        "detail_expectation": "Pack quick-hit descriptors for subject, environment, lighting, and mood without wasting tokens.",
        "supports": ["quality_emphasis", "booru_tags", "attention_syntax"],
        "preferences": [
            "Quality tokens at the beginning",
            "Concise but specific descriptions",
            "Optional ( ) emphasis syntax",
            "Lighting and composition succinctly described",
            "Negative prompt pairing"
        ],
        "quality_tokens": [
            "masterpiece", "best quality", "ultra detailed", "sharp focus",
            "high resolution", "8k", "professional lighting", "intricate details"
        ],
        "avoid": [
            "Overly long sentences that exceed token budget",
            "Redundant modifiers",
            "Unnecessary filler words"
        ]
    },

    "sd_xl": {
        "name": "Stable Diffusion XL",
        "description": "Stability AI - Token-aware, quality emphasis, booru tags optional",
        "prompt_style": "token_optimized",
        "optimal_length": "extended (≤150 tokens ~110 words)",
        "max_words": 110,
        "max_tokens": 150,
    "quality_emphasis": True,
        "length_guidance": "Aim for up to 150 tokens (~110 words) with dense, front-loaded details.",
        "detail_expectation": "Even within token limits, pack the prompt with intricate, high-impact descriptors.",
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
        "optimal_length": "extended (~75 tags/words)",
        "max_words": 75,
        "max_tokens": 110,
    "quality_emphasis": True,
        "length_guidance": "Provide roughly 75 booru tags with exhaustive character, outfit, and background coverage.",
        "detail_expectation": "Stack quality, anatomy, clothing, and background tags for maximum specificity.",
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
        "optimal_length": "extended (~150 tags/words)",
        "max_words": 150,
        "max_tokens": 210,
    "quality_emphasis": True,
        "length_guidance": "Provide around 150 detailed tags covering quality, anatomy, clothing, and atmosphere.",
        "detail_expectation": "Go beyond basics—describe micro-details, accessories, background storytelling, and lighting tags.",
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
        "optimal_length": "extended (~220 words)",
        "max_words": 220,
        "max_tokens": 310,
    "quality_emphasis": True,
        "length_guidance": "Deliver around 220 words describing every subject, relation, and environment nuance.",
        "detail_expectation": "Layer in compositional geometry, lighting, mood, and background storytelling for each subject.",
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
        "optimal_length": "extended (~250 words)",
        "max_words": 250,
        "max_tokens": 360,
    "quality_emphasis": True,
        "length_guidance": "Target ~250 words with thorough cinematic breakdowns (camera, lighting, blocking, motion).",
        "detail_expectation": "Describe sequence-level cinematography, color design, and atmosphere in exhaustive detail.",
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
    style: Optional[str] = None,
    quality_emphasis: Optional[bool] = None
) -> str:
    """
    Format a prompt optimally for the target platform
    
    Args:
        description: Base image description from vision model
        change_request: User's requested changes
        platform: Target platform name
        style: Optional style override
    quality_emphasis: Optional override for enabling quality tokens
    """
    config = get_platform_config(platform)

    if quality_emphasis is None:
        resolved_quality: bool = bool(config.get("quality_emphasis", True))
    else:
        resolved_quality = bool(quality_emphasis)
    
    if platform == "qwen_image_edit":
        # Edit model: very concise, focus on changes only
        return _format_for_edit(description, change_request, config, resolved_quality)

    if platform in {"flux", "flux_kontex", "pixart_sigma", "kolors"}:
        # Flux variants: natural, detailed, artistic
        return _format_for_flux(description, change_request, config, style, resolved_quality)

    if platform == "wan22":
        # Wan: technical, structured
        return _format_for_wan(description, change_request, config, resolved_quality)

    if platform == "hunyuan_image":
        # Hunyuan: clear, concise, realistic
        return _format_for_hunyuan(description, change_request, config, resolved_quality)

    if platform in {"qwen_image", "aura_flow", "noobai"}:
        # Qwen family: balanced, natural
        return _format_for_qwen(description, change_request, config, resolved_quality)

    if platform in {"sd_xl", "sd_1_5"}:
        # Stable Diffusion: token-optimized
        return _format_for_sdxl(description, change_request, config, resolved_quality)

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


def _format_for_flux(description: str, changes: str, config: dict, style: Optional[str], quality: bool) -> str:
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


def get_negative_prompt_for_platform(
    platform: str,
    custom_negatives: Optional[Sequence[str]] = None
) -> str:
    """Generate platform-optimized negative prompts"""
    
    base_negatives = {
        "flux": "blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, signature, text",
        "flux_kontex": "blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, text artifacts",
        "pixart_sigma": "blurry, low quality, dull colors, banding, messy details, inaccurate anatomy, artifacts",
        "aura_flow": "blurry, low quality, overexposed, underexposed, harsh shadows, artifacts, unnatural skin",
        "noobai": "low quality, blurry, distorted, bad composition, poor lighting, artifacts, bad anatomy",
        "kolors": "low quality, muddy colors, flat lighting, artifacts, color banding, bland composition",
        "wan22": "low quality, blurry, distorted, poor composition, bad lighting, flat",
        "hunyuan_image": "low quality, blurry, distorted, unrealistic, bad details",
        "qwen_image": "low quality, blurry, distorted, artifacts, bad anatomy",
        "qwen_image_edit": "unnatural, inconsistent, artifacts, seams, low quality",
        "sd_1_5": "worst quality, low quality, blurry, bad anatomy, deformed, disfigured, extra limbs, artifacts",
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
