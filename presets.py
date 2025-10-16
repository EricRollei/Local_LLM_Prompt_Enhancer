"""
Preset configurations for different video styles
Based on Wan 2.2 prompting guide
"""

PRESETS = {
    "custom": {
        "description": "No preset - use tier settings only",
        "focus_areas": [],
        "style_hints": [],
        "camera_preferences": [],
        "lighting_preferences": [],
        "motion_preferences": []
    },
    
    "cinematic": {
        "description": "Professional film quality with emphasis on cinematography",
        "focus_areas": ["cinematography", "lighting", "composition", "camera_movement"],
        "style_hints": [
            "cinematic",
            "film-like",
            "professional cinematography",
            "dramatic lighting"
        ],
        "camera_preferences": [
            "smooth camera movement",
            "deliberate framing",
            "dynamic composition",
            "depth of field"
        ],
        "lighting_preferences": [
            "professional lighting setup",
            "edge lighting",
            "carefully controlled shadows",
            "high contrast or soft lighting as appropriate"
        ],
        "motion_preferences": [
            "fluid motion",
            "realistic physics",
            "natural movement"
        ],
        "technical_specs": [
            "medium to long lens",
            "considered shot size",
            "intentional color grading"
        ]
    },
    
    "surreal": {
        "description": "Dreamlike, otherworldly aesthetics",
        "focus_areas": ["style", "color", "unusual_elements"],
        "style_hints": [
            "surreal",
            "dreamlike",
            "ethereal",
            "magical realism",
            "fantastical"
        ],
        "camera_preferences": [
            "unusual angles",
            "floating camera movement",
            "disorienting perspectives"
        ],
        "lighting_preferences": [
            "unnatural lighting",
            "mixed light sources",
            "saturated or desaturated colors",
            "mysterious ambiance"
        ],
        "motion_preferences": [
            "slow motion",
            "floating",
            "gravity-defying",
            "morphing",
            "ethereal movement"
        ],
        "technical_specs": [
            "creative color grading",
            "atmospheric effects",
            "visual distortion"
        ]
    },
    
    "action": {
        "description": "High-energy, dynamic motion sequences",
        "focus_areas": ["motion", "camera_movement", "energy"],
        "style_hints": [
            "dynamic",
            "energetic",
            "intense",
            "fast-paced"
        ],
        "camera_preferences": [
            "rapid camera movement",
            "tracking shots",
            "handheld camera feel",
            "quick cuts implied by motion"
        ],
        "lighting_preferences": [
            "high contrast",
            "dramatic lighting",
            "hard lighting",
            "strong shadows"
        ],
        "motion_preferences": [
            "fast motion",
            "explosive action",
            "athletic movement",
            "kinetic energy",
            "impact and force"
        ],
        "technical_specs": [
            "wide-angle lens",
            "motion blur",
            "dynamic framing"
        ]
    },
    
    "stylized": {
        "description": "Artistic visual style over realism",
        "focus_areas": ["visual_style", "aesthetics", "artistic_interpretation"],
        "style_hints": [
            "stylized",
            "artistic",
            "illustrative",
            "graphic",
            "design-forward"
        ],
        "camera_preferences": [
            "deliberate framing",
            "symmetrical or rule-of-thirds composition",
            "clean visual lines"
        ],
        "lighting_preferences": [
            "artistic lighting",
            "color-coordinated palette",
            "intentional color scheme"
        ],
        "motion_preferences": [
            "stylized movement",
            "choreographed motion",
            "artistic interpretation of physics"
        ],
        "technical_specs": [
            "strong visual identity",
            "consistent color palette",
            "graphic elements"
        ],
        "style_options": [
            "3D animation style",
            "2D anime style",
            "watercolor",
            "oil painting",
            "pixel art",
            "claymation"
        ]
    },
    
    "noir": {
        "description": "Dark, moody, high-contrast aesthetic",
        "focus_areas": ["lighting", "atmosphere", "shadow"],
        "style_hints": [
            "film noir",
            "neo-noir",
            "dark",
            "moody",
            "atmospheric"
        ],
        "camera_preferences": [
            "low angle shots",
            "dutch angles",
            "dramatic framing",
            "shadow play"
        ],
        "lighting_preferences": [
            "high contrast lighting",
            "hard lighting",
            "venetian blind shadows",
            "single light source",
            "dramatic shadows",
            "chiaroscuro"
        ],
        "motion_preferences": [
            "deliberate movement",
            "tension in stillness",
            "slow, purposeful actions"
        ],
        "technical_specs": [
            "desaturated colors or black and white",
            "deep shadows",
            "limited color palette",
            "night time or low-light settings"
        ],
        "atmosphere": [
            "mysterious",
            "tense",
            "foreboding",
            "urban decay"
        ]
    },
    
    "random": {
        "description": "Randomize elements from the guide for creative exploration",
        "focus_areas": ["random_selection"],
        "style_hints": ["creative", "experimental", "unexpected"],
        "random_elements": True,
        "instruction": "Select random but complementary elements from different categories"
    }
}


# Random element pools for "random" preset
RANDOM_POOLS = {
    "lighting_types": [
        "sunny lighting", "artificial lighting", "moonlighting", "practical lighting",
        "firelighting", "fluorescent lighting", "overcast lighting", "mixed lighting"
    ],
    "lighting_quality": [
        "soft lighting", "hard lighting", "edge lighting", "side lighting",
        "top lighting", "underlighting", "silhouette lighting", "low contrast lighting",
        "high contrast lighting"
    ],
    "times_of_day": [
        "sunrise time", "night time", "dusk time", "sunset time", "dawn time"
    ],
    "shot_sizes": [
        "extreme close-up shot", "close-up shot", "medium shot",
        "medium close-up shot", "medium wide shot", "wide shot", "extreme wide shot"
    ],
    "compositions": [
        "center composition", "balanced composition", "left-weighted composition",
        "right-weighted composition", "symmetrical composition", "short-side composition"
    ],
    "lenses": [
        "medium lens", "wide lens", "long-focus lens", "telephoto lens",
        "fisheye lens", "wide-angle lens"
    ],
    "camera_angles": [
        "eye-level shot", "high angle shot", "low angle shot",
        "dutch angle shot", "aerial shot", "over-the-shoulder shot"
    ],
    "camera_movements": [
        "camera pushes in", "camera pulls back", "camera pans right",
        "camera pans left", "camera tilts up", "camera tilts down",
        "tracking shot", "arc shot", "handheld camera"
    ],
    "color_tones": [
        "warm colors", "cool colors", "saturated colors", "desaturated colors"
    ],
    "visual_styles": [
        "3D cartoon style", "2D anime style", "watercolor painting",
        "oil painting style", "pixel art style", "claymation style",
        "felt style", "puppet animation", "photorealistic"
    ],
    "visual_effects": [
        "tilt-shift photography", "time-lapse", "motion blur",
        "depth of field", "bokeh", "lens flare"
    ]
}


def get_preset(preset_name: str) -> dict:
    """Get preset configuration by name"""
    return PRESETS.get(preset_name.lower(), PRESETS["custom"])


def get_random_elements(num_elements: int = 5) -> dict:
    """Get random elements for the random preset"""
    import random
    
    selected = {}
    for category, options in RANDOM_POOLS.items():
        if random.random() > 0.5:  # 50% chance to include each category
            selected[category] = random.choice(options)
    
    return selected
