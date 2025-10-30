"""
Text-to-Image Prompt Enhancer Node
Advanced multi-platform prompt enhancement for image generation
Supports: SDXL, Pony, Illustrious, Flux, Chroma, Qwen-Image, Qwen-Edit, Wan-Image
"""

import torch
import numpy as np
from PIL import Image
import io
import random
import re
from typing import Tuple, Optional, Dict, List, Any, Union
from .llm_backend import LLMBackend
from .qwen3_vl_backend import caption_with_qwen3_vl
from .platforms import get_platform_config, get_negative_prompt_for_platform
from .utils import save_prompts_to_file, parse_keywords


class TextToImagePromptEnhancer:
    """
    Advanced text-to-image prompt enhancement with platform-specific optimization
    
    Features:
    - Multiple platform support with tailored prompting
    - Optional image reference input (1-2 images)
    - Advanced aesthetic controls (lighting, camera, time of day, etc.)
    - Wildcard random options
    - Platform-specific formatting and token optimization
    """
    
    def __init__(self):
        self.type = "text_to_image_enhancement"
        self.output_dir = "output/txt2img_prompts"
        
        # Wildcard options
        self.camera_angles = [
            "eye level", "low angle", "high angle", "dutch angle", "bird's eye view",
            "worm's eye view", "over the shoulder", "point of view", "extreme close-up angle"
        ]
        
        self.lighting_sources = [
            "natural sunlight", "studio lighting", "golden hour sun", "moonlight",
            "candlelight", "neon lights", "firelight", "spotlight", "ambient lighting",
            "backlight", "rim lighting", "window light", "street lights"
        ]
        
        self.lighting_quality = [
            "soft diffused", "hard dramatic", "even balanced", "high contrast",
            "low key", "high key", "chiaroscuro", "volumetric", "atmospheric"
        ]
        
        self.times_of_day = [
            "dawn", "early morning", "mid-morning", "noon", "afternoon",
            "golden hour", "dusk", "twilight", "night", "midnight", "blue hour"
        ]
        
        self.weather_conditions = [
            "clear sky", "partly cloudy", "overcast", "misty", "foggy",
            "rainy", "stormy", "snowy", "sunny", "hazy"
        ]
        
        self.composition_styles = [
            "rule of thirds", "centered", "symmetrical", "asymmetrical",
            "golden ratio", "leading lines", "frame within frame", "negative space",
            "balanced", "dynamic diagonal"
        ]
        
        self.genre_styles = [
            "surreal", "cinematic", "dramatic", "action", "humorous",
            "indie", "horror", "scifi", "romantic", "artistic",
            "documentary", "minimalist", "maximalist", "vintage", "modern",
            "fantasy", "noir", "cyberpunk", "steampunk", "dieselpunk",
            "mythic", "gothic", "art deco", "retro futurism"
        ]
        
        self.historical_periods = [
            "prehistoric era", "ancient civilizations", "classical antiquity",
            "medieval era", "renaissance", "baroque period", "industrial revolution",
            "victorian era", "edwardian era", "roaring twenties", "mid-century modern",
            "1960s counterculture", "1980s neon wave", "1990s digital dawn",
            "modern day", "near future", "far future", "cyberpunk future",
            "post-apocalyptic era", "fantasy realm", "science fiction epoch"
        ]
        
        self.subject_framings = [
            "extreme close-up", "close-up", "medium close-up",
            "medium shot", "medium wide", "wide shot",
            "full body", "cowboy shot", "bust shot",
            "head and shoulders", "three-quarter", "establishing shot",
            "aerial overview", "profile view"
        ]
        
        self.subject_poses = [
            "standing", "sitting", "lying down", "kneeling", "crouching",
            "action pose", "portrait pose", "dynamic", "static",
            "asymmetric", "contrapposto", "relaxed", "tense",
            "walking", "running", "jumping", "dancing", "floating"
        ]
        
        self.creative_randomness_modes = {
            "off": "Stay close to user wording with minimal embellishment.",
            "subtle": "Add gentle flourishes that enhance mood without changing subject focus.",
            "moderate": "Introduce fresh context, supporting details, or small narrative beats.",
            "bold": "Transform the prompt into a vivid scene with new narrative hooks and world-building.",
            "storyteller": "Invent an imaginative mini-story or scenario that surprises while honoring the subject.",
            "chaotic": "Push boundaries with experimental, dreamlike, or surreal twists." 
        }
        
        self.random_story_settings = [
            "abandoned futuristic metropolis", "misty forest crossroads",
            "luminous underwater research lab", "quiet suburban street at dawn",
            "ancient floating temple", "deserted lunar colony", "ornate victorian ballroom",
            "hidden speakeasy behind a bookstore", "glitching neon arcade",
            "forgotten museum of impossible inventions", "bioluminescent cavern",
            "storm-lashed airship deck", "sunset-drenched mountain pass",
            "labyrinthine library of living books", "gravity-defying market square"
        ]
        
        self.random_story_companions = [
            "a time-traveling archivist", "an eccentric inventor", "a sentient automaton",
            "a mysterious stranger in vintage attire", "a playful cosmic entity",
            "a band of skyship pirates", "a chorus of bioluminescent sprites",
            "a rival artist seeking inspiration", "a loyal cybernetic fox",
            "an undercover interstellar diplomat"
        ]
        
        self.random_story_conflicts = [
            "searching for the last fragment of a lost melody",
            "racing against an impending temporal storm",
            "unlocking a doorway hidden inside a beam of light",
            "negotiating peace between rival realities",
            "decoding whispers carried by the rain",
            "restoring color to a world frozen in monochrome",
            "solving a puzzle etched into the constellations",
            "protecting a fragile artifact of collective memories"
        ]
        
        self.reference_usage_labels = {
            "caption": "scene overview",
            "style": "artistic style and texture",
            "lighting": "lighting qualities and direction",
            "genre": "genre or mood cues",
            "time_period": "time period context",
            "subject": "primary subject appearance",
            "objects": "notable secondary objects",
            "color": "color palette or grading",
            "composition": "framing and spatial layout"
        }

        self.reference_directive_choices = [
            "none",
            "auto",
            "recreate",
            "reinterpret",
            "subject only",
            "style only",
            "lighting only",
            "composition",
            "genre"
        ]

        self._seed_state: Dict[str, Any] = {
            "last_seed": None,
            "last_mode": None,
            "last_input": None
        }

        self.reference_directive_configs = {
            "none": {
                "display": "None",
                "user_guidance": "Use this reference for broad inspiration using its full caption.",
                "user_summary": "Incorporate helpful elements from the reference caption without enforcing a specific focus.",
                "include_categories": ["caption"],
                "exclude_categories": [],
                "llm_instruction": (
                    "Absorb the entire reference caption as general inspiration. Keep the meaningful traits but avoid over-emphasizing any single element."
                ),
                "analysis_focus": (
                    "Summarize the overall subject, setting, lighting, mood, and notable items so the prompt can mirror the scene holistically."
                )
            },
            "auto": {
                "display": "Auto",
                "user_guidance": "Adapt helpful traits from the reference based on context.",
                "user_summary": "Auto-balances useful cues from the reference.",
                "include_categories": [
                    "caption",
                    "style",
                    "lighting",
                    "color",
                    "genre",
                    "composition",
                    "subject",
                    "objects",
                    "time_period"
                ],
                "exclude_categories": [],
                "llm_instruction": (
                    "Absorb the full caption from this reference to strengthen the user's brief. "
                    "Borrow cues that align with the goal and adjust anything that conflicts."
                ),
                "analysis_focus": (
                    "Identify the most influential subject, style, lighting, composition, and supporting details from the"
                    " complete caption that will benefit the final prompt."
                )
            },
            "recreate": {
                "display": "Recreate",
                "user_guidance": "Match the reference closely across subject, palette, lighting, and mood.",
                "user_summary": "Recreate the reference look as faithfully as possible.",
                "include_categories": "all",
                "exclude_categories": [],
                "llm_instruction": (
                    "Reproduce this reference almost verbatim. Maintain subject identity, palette, lighting, composition, "
                    "and supporting props unless the main prompt explicitly overrides them."
                ),
                "analysis_focus": (
                    "List the critical traits that must be preserved exactly: subject identity, pose, palette, lighting,"
                    " composition, and key props or environment cues."
                )
            },
            "reinterpret": {
                "display": "Reinterpret",
                "user_guidance": "Use the reference as inspiration; preserve core subject or mood, but embrace smart variations.",
                "user_summary": "Keep the spirit of the reference while allowing tasteful changes.",
                "include_categories": [
                    "caption",
                    "subject",
                    "objects",
                    "genre",
                    "style",
                    "lighting",
                    "color",
                    "composition",
                    "time_period"
                ],
                "exclude_categories": [],
                "llm_instruction": (
                    "Preserve the recognizable subject or atmosphere from this reference using the full caption as context, yet "
                    "refresh style, palette, or composition when it improves alignment with the user's prompt."
                ),
                "analysis_focus": (
                    "Summarize the anchor traits (subject identity, mood, palette cues) drawn from the entire caption while"
                    " noting which aspects feel flexible for reinterpretation."
                )
            },
            "subject_only": {
                "display": "Subject Only",
                "user_guidance": "Preserve the subject’s identity, pose, and defining traits; let other elements follow the prompt.",
                "user_summary": "Keep subject fidelity; redesign other aspects.",
                "include_categories": ["caption", "subject", "objects", "composition"],
                "exclude_categories": ["style", "lighting", "color", "genre"],
                "llm_instruction": (
                    "Carry over the subject's identity, pose, and silhouette from this reference using the full caption as context. "
                    "Invent fresh style, lighting, and background details to suit the user's prompt."
                ),
                "analysis_focus": (
                    "Describe the subject's appearance, pose, silhouette, distinguishing features, and supportive forms as captured"
                    " in the caption so the identity remains unmistakable."
                )
            },
            "style_only": {
                "display": "Style Only",
                "user_guidance": "Borrow the artistic style, texture, palette, and brushwork; ignore subject and composition cues.",
                "user_summary": "Transfer the reference style while changing subject matter.",
                "include_categories": ["caption", "style", "color", "genre", "lighting"],
                "exclude_categories": ["subject", "objects", "composition"],
                "llm_instruction": (
                    "Adopt the artistic style, texture, and palette suggested by this reference after studying the complete caption. "
                    "Replace its subject and layout with the user's requested scene."
                ),
                "analysis_focus": (
                    "Detail the artistic medium, techniques, palette tendencies, brushwork, texture, and stylistic motifs present"
                    " in the caption so the style can be transferred accurately."
                )
            },
            "lighting_only": {
                "display": "Lighting Only",
                "user_guidance": "Replicate lighting qualities like direction, intensity, and warmth; disregard subject or style cues.",
                "user_summary": "Reuse lighting mood without copying subject matter.",
                "include_categories": ["caption", "lighting", "color"],
                "exclude_categories": ["subject", "objects", "style", "genre", "composition"],
                "llm_instruction": (
                    "Match the lighting direction, intensity, and warmth suggested by this reference while treating the full caption as context. "
                    "Do not replicate its subject, style, or composition."
                ),
                "analysis_focus": (
                    "Explain the lighting direction, intensity, quality, shadow behavior, and color temperature found in the caption"
                    " so the mood can be recreated without losing context."
                )
            },
            "composition": {
                "display": "Composition",
                "user_guidance": "Adopt the camera angle, framing, and spatial layout; let subject and style come from the prompt.",
                "user_summary": "Mirror the reference framing while refreshing other traits.",
                "include_categories": ["composition", "caption", "objects"],
                "exclude_categories": ["style", "lighting", "color", "genre"],
                "llm_instruction": (
                    "Borrow the framing, camera angle, and spatial relationships implied by this reference using the caption as your map. "
                    "Populate that layout with the subjects and styling requested in the prompt."
                ),
                "analysis_focus": (
                    "Describe the camera angle, focal length impression, framing, depth relationships, and placement of key elements"
                    " from the caption so the layout can be preserved."
                )
            },
            "genre": {
                "display": "Genre",
                "user_guidance": "Match the genre or storytelling conventions; let other specifics follow the prompt unless genre demands otherwise.",
                "user_summary": "Carry over the reference genre atmosphere.",
                "include_categories": ["caption", "genre", "style", "color", "lighting"],
                "exclude_categories": ["subject", "objects", "composition"],
                "llm_instruction": (
                    "Preserve the genre tone and storytelling conventions from this reference by internalizing the whole caption. "
                    "Let the user's prompt determine subject matter and layout unless genre cues require tweaks."
                ),
                "analysis_focus": (
                    "Summarize the genre-defining mood, atmosphere, storytelling motifs, and stylistic cues from the full caption"
                    " so the tone carries over cleanly."
                )
            }
        }

        self.default_reference_analysis_method = "sequential_refine"
        self.reference_guardrail_text = (
            "Blend reference guidance without repeating yourself. Do not mention source image dimensions, aspect ratios, "
            "or pixel resolutions under any circumstance."
        )
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Core inputs
                "text_prompt": ("STRING", {
                    "multiline": True,
                    "default": "a beautiful woman in a garden",
                    "placeholder": "Describe the image you want to generate\n\n"
                                  "Supports:\n"
                                  "- Emphasis: (keyword:1.5) to increase weight\n"
                                  "- De-emphasis: (keyword:0.5) to decrease weight\n"
                                  "- Alternation: {apple|banana|orange} picks one randomly\n"
                                  "- Nested: {red|blue|green} (dress:1.2) works too"
                }),

                "reference_directive_1": ([
                    "none",
                    "auto",
                    "recreate",
                    "reinterpret",
                    "subject only",
                    "style only",
                    "lighting only",
                    "composition",
                    "genre"
                ], {
                    "default": "none"
                }),

                "reference_directive_2": ([
                    "none",
                    "auto",
                    "recreate",
                    "reinterpret",
                    "subject only",
                    "style only",
                    "lighting only",
                    "composition",
                    "genre"
                ], {
                    "default": "none"
                }),
                
                "prompt_context": ([
                    "none",
                    "auto",
                    "expand_short_prompt",
                    "finish_opening_line",
                    "prompt_from_item_list",
                    "modify_reference_image",
                    "enhance_reference_image"
                ], {
                    "default": "none",
                    "tooltip": (
                        "none/auto: Standard prompt\n"
                        "expand_short_prompt: Expand shorthand into full description\n"
                        "finish_opening_line: Continue from your opening line\n"
                        "prompt_from_item_list: Transform comma-separated elements into scene\n"
                        "modify_reference_image: Alter specific parts of reference\n"
                        "enhance_reference_image: Enrich reference with new elements"
                    )
                }),
                
                "creative_randomness": ([
                    "auto", "none", "off", "subtle", "moderate", "bold", "storyteller", "chaotic"
                ], {
                    "default": "none",
                    "tooltip": (
                        "off/none: Minimal embellishment\n"
                        "subtle: Gentle mood enhancement\n"
                        "moderate: Add supporting details\n"
                        "bold: Vivid scene with narrative hooks\n"
                        "storyteller: Imaginative mini-story\n"
                        "chaotic: Experimental, surreal twists"
                    )
                }),
                
                # Platform selection
                "target_platform": ([
                    "flux",
                    "flux_kontex",
                    "sd_xl",
                    "sd_1_5",
                    "pony",
                    "illustrious",
                    "chroma",
                    "pixart_sigma",
                    "aura_flow",
                    "noobai",
                    "kolors",
                    "qwen_image",
                    "qwen_image_edit",
                    "wan_image"
                ], {
                    "default": "flux"
                }),
                
                # LLM settings
                "llm_backend": ([
                    "lm_studio",
                    "ollama",
                    "qwen3_vl"
                ], {
                    "default": "lm_studio",
                    "tooltip": (
                        "lm_studio: Uses currently loaded model in LM Studio\n"
                        "ollama: Uses currently loaded model in Ollama\n"
                        "qwen3_vl: Auto-detects local Qwen3-VL model (no API server needed)"
                    )
                }),
                
                "api_endpoint": ("STRING", {
                    "default": "http://localhost:1234/v1",
                    "multiline": False,
                    "tooltip": (
                        "lm_studio/ollama: API endpoint URL\n"
                        "qwen3_vl: Leave default, or specify custom model path like 'A:\\path\\to\\model'"
                    )
                }),
                
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.1,
                    "max": 2.0,
                    "step": 0.1
                }),

                "vision_backend": ([
                    "auto",
                    "lm_studio",
                    "ollama",
                    "qwen3_vl",
                    "disable"
                ], {
                    "default": "auto",
                    "tooltip": "Vision captioning: auto=inherit from main LLM, qwen3_vl=local Qwen3-VL, lm_studio/ollama=separate vision model, disable=heuristics only"
                }),
                
                "vision_api_endpoint": ("STRING", {
                    "default": "http://localhost:1234/v1",
                    "multiline": False,
                    "tooltip": (
                        "Vision backend API endpoint (lm_studio/ollama) or custom model path (qwen3_vl)\n"
                        "For qwen3_vl: Leave default for auto-detect, or specify 'A:\\path\\to\\model'"
                    )
                }),
                
                # Camera & Composition
                "camera_angle": ([
                    "auto", "random", "none",
                    "eye level", "low angle", "high angle", "dutch angle",
                    "bird's eye view", "worm's eye view", "over the shoulder",
                    "point of view", "extreme close-up angle"
                ], {
                    "default": "none"
                }),
                
                "composition": ([
                    "auto", "random", "none",
                    "rule of thirds", "centered", "symmetrical", "asymmetrical",
                    "golden ratio", "leading lines", "frame within frame",
                    "negative space", "balanced", "dynamic diagonal"
                ], {
                    "default": "none"
                }),
                
                # Lighting
                "lighting_source": ([
                    "auto", "random", "none",
                    "natural sunlight", "studio lighting", "golden hour sun",
                    "moonlight", "candlelight", "neon lights", "firelight",
                    "spotlight", "ambient lighting", "backlight", "rim lighting",
                    "window light", "street lights"
                ], {
                    "default": "none"
                }),
                
                "lighting_quality": ([
                    "auto", "random", "none",
                    "soft diffused", "hard dramatic", "even balanced",
                    "high contrast", "low key", "high key", "chiaroscuro",
                    "volumetric", "atmospheric"
                ], {
                    "default": "none"
                }),
                
                # Time & Weather
                "time_of_day": ([
                    "auto", "random", "none",
                    "dawn", "early morning", "mid-morning", "noon", "afternoon",
                    "golden hour", "dusk", "twilight", "night", "midnight", "blue hour"
                ], {
                    "default": "none"
                }),
                
                "historical_period": ([
                    "auto", "random", "none",
                    "prehistoric era", "ancient civilizations", "classical antiquity",
                    "medieval era", "renaissance", "baroque period", "industrial revolution",
                    "victorian era", "edwardian era", "roaring twenties", "mid-century modern",
                    "1960s counterculture", "1980s neon wave", "1990s digital dawn",
                    "modern day", "near future", "far future", "cyberpunk future",
                    "post-apocalyptic era", "fantasy realm", "science fiction epoch"
                ], {
                    "default": "none"
                }),
                
                "weather": ([
                    "auto", "random", "none",
                    "clear sky", "partly cloudy", "overcast", "misty", "foggy",
                    "rainy", "stormy", "snowy", "sunny", "hazy"
                ], {
                    "default": "none"
                }),
                
                # Style & Quality
                "art_style": ([
                    "auto", "none",
                    "photorealistic", "digital art", "oil painting", "watercolor",
                    "anime", "manga", "sketch", "pencil drawing", "3D render",
                    "illustration", "concept art", "impressionist", "abstract",
                    "pixel art", "low poly", "papercraft", "isometric"
                ], {
                    "default": "none"
                }),
                
                "genre_style": ([
                    "auto", "random", "none",
                    "surreal", "cinematic", "dramatic", "action", "humorous",
                    "indie", "horror", "scifi", "romantic", "x-rated", "pg",
                    "artistic", "documentary", "minimalist", "maximalist",
                    "vintage", "modern", "fantasy", "noir", "cyberpunk",
                    "steampunk", "dieselpunk", "mythic", "gothic", "art deco", "retro futurism"
                ], {
                    "default": "none"
                }),
                
                "color_mood": ([
                    "auto", "random", "none",
                    "vibrant", "muted", "monochrome", "warm tones", "cool tones",
                    "pastel", "high contrast", "desaturated", "neon", "earth tones"
                ], {
                    "default": "none"
                }),
                
                # Subject Controls
                "subject_framing": ([
                    "auto", "random", "none",
                    "extreme close-up", "close-up", "medium close-up",
                    "medium shot", "medium wide", "wide shot",
                    "full body", "cowboy shot", "bust shot",
                    "head and shoulders", "three-quarter", "establishing shot",
                    "aerial overview", "profile view"
                ], {
                    "default": "none"
                }),
                
                "subject_pose": ([
                    "auto", "random", "none",
                    "standing", "sitting", "lying down", "kneeling", "crouching",
                    "action pose", "portrait pose", "dynamic", "static",
                    "asymmetric", "contrapposto", "relaxed", "tense",
                    "walking", "running", "jumping", "dancing", "floating"
                ], {
                    "default": "none"
                }),
                
                # Keywords
                "positive_keywords": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Additional keywords, LoRA triggers, specific details"
                }),
                
                "negative_keywords": ("STRING", {
                    "default": "ugly, blurry, duplicate, deformed, distorted, lowres, bad anatomy, disfigured, poorly drawn, mutation, mutated, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, fused fingers, too many fingers, long neck",
                    "multiline": True,
                    "placeholder": "Things to avoid"
                }),

                "seed_mode": ([
                    "random",
                    "fixed",
                    "increment",
                    "decrement"
                ], {
                    "default": "random"
                }),
                
                "random_seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2_147_483_647,
                    "step": 1
                }),

                # Output
                "save_to_file": ("BOOLEAN", {
                    "default": False
                }),
                
                "filename_base": ("STRING", {
                    "default": "txt2img_prompt",
                    "multiline": False
                })
            },
            "optional": {
                # Optional image references
                "reference_image_1": ("IMAGE",),
                "reference_image_2": ("IMAGE",),
                "reference_caption_override_1": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Optional external caption for Reference 1"
                }),
                "reference_caption_override_2": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Optional external caption for Reference 2"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "settings_used", "status", "vision_caption", "seed_used")
    
    FUNCTION = "enhance_prompt"
    CATEGORY = "Eric Prompt Enhancers"
    OUTPUT_NODE = True
    
    @classmethod
    def IS_CHANGED(cls, random_seed: int, seed_mode: str, **kwargs):
        """Determine if the node should re-execute based on seed mode.
        
        Returns a unique value for modes that need to re-run each time,
        or the seed value for fixed mode (to use ComfyUI's caching).
        """
        import time
        
        mode = str(seed_mode).strip().lower()
        
        # For random/increment/decrement, return unique value each time to force re-execution
        if mode in {"random", "increment", "decrement"}:
            # Return timestamp to guarantee uniqueness
            return float(time.time())
        
        # For fixed mode, return the seed value so ComfyUI can cache
        try:
            seed_value = int(random_seed)
            if seed_value < 0:
                # Negative seed means random even in fixed mode
                return float(time.time())
            return seed_value
        except Exception:
            return float(time.time())

    def enhance_prompt(
        self,
        text_prompt: str,
        reference_directive_1: str,
        reference_directive_2: str,
        prompt_context: str,
        target_platform: str,
        llm_backend: str,
        api_endpoint: str,
        temperature: float,
        vision_backend: str,
        vision_api_endpoint: str,
        camera_angle: str,
        composition: str,
        lighting_source: str,
        lighting_quality: str,
        time_of_day: str,
        historical_period: str,
        weather: str,
        art_style: str,
        genre_style: str,
        color_mood: str,
        creative_randomness: str,
        subject_framing: str,
        subject_pose: str,
        positive_keywords: str,
        negative_keywords: str,
        seed_mode: str,
        random_seed: int,
        save_to_file: bool,
        filename_base: str,
        reference_image_1: Optional[torch.Tensor] = None,
        reference_image_2: Optional[torch.Tensor] = None,
        reference_caption_override_1: str = "",
        reference_caption_override_2: str = ""
    ) -> Tuple[str, str, str, str]:
        """Main processing function"""
        try:
            requested_seed = int(random_seed)
        except Exception:
            requested_seed = -1

        seed_mode_normalized = str(seed_mode).strip().lower()
        seed_value, resolved_seed_mode = self._resolve_seed_value(seed_mode_normalized, requested_seed)

        python_random_state = random.getstate()
        numpy_random_state = np.random.get_state()

        random.seed(seed_value)
        np.random.seed(seed_value % (2**32))

        try:
            # STEP 0: Process alternations first (before LLM)
            text_prompt = self._process_alternations(text_prompt)
            
            # STEP 0.5: Protect emphasis syntax
            text_prompt = self._preserve_emphasis_syntax(text_prompt)
            
            # STEP 1: Process reference images if provided
            reference_images = []
            directive_inputs = []
            override_1 = (reference_caption_override_1 or "").strip()
            override_2 = (reference_caption_override_2 or "").strip()

            if reference_image_1 is not None:
                reference_images.append({
                    "label": "Reference 1",
                    "tensor": reference_image_1,
                    "caption_override": override_1,
                    "override_source": "user" if override_1 else None
                })
                directive_inputs.append(("Reference 1", reference_directive_1))
            elif override_1:
                # Allow caption-only references when external descriptor provided
                reference_images.append({
                    "label": "Reference 1",
                    "tensor": None,
                    "caption_override": override_1,
                    "override_source": "user"
                })
                directive_inputs.append(("Reference 1", reference_directive_1))

            if reference_image_2 is not None:
                reference_images.append({
                    "label": "Reference 2",
                    "tensor": reference_image_2,
                    "caption_override": override_2,
                    "override_source": "user" if override_2 else None
                })
                directive_inputs.append(("Reference 2", reference_directive_2))
            elif override_2:
                reference_images.append({
                    "label": "Reference 2",
                    "tensor": None,
                    "caption_override": override_2,
                    "override_source": "user"
                })
                directive_inputs.append(("Reference 2", reference_directive_2))

            reference_plan = self._prepare_reference_plan(directive_inputs)

            # Initialize LLM backend (model_name auto-detected)
            llm = LLMBackend(
                backend_type=llm_backend,
                endpoint=api_endpoint,
                model_name=None,  # Auto-detect for all backends
                temperature=temperature
            )

            vision_backend_selection = (vision_backend or "inherit").strip().lower()
            if not vision_backend_selection:
                vision_backend_selection = "auto"
            
            # Vision backend now supports custom endpoint via vision_api_endpoint

            vision_llm: Optional[LLMBackend] = None
            vision_qwen_config: Optional[Dict[str, Any]] = None
            vision_backend_mode = "disabled"
            vision_caption_enabled = False
            vision_model_used = ""
            vision_init_warning: Optional[str] = None

            if vision_backend_selection in {"", "auto", "inherit"}:
                if llm.supports_images():
                    vision_llm = llm
                    vision_backend_mode = "inherit"
                    vision_caption_enabled = True
                    vision_model_used = getattr(llm, "model_name", "auto-detected")
                else:
                    vision_backend_mode = "disabled"
            elif vision_backend_selection == "disable":
                vision_backend_mode = "disabled"
            elif vision_backend_selection in {"lm_studio", "ollama"}:
                # Use vision-specific endpoint
                try:
                    vision_llm = LLMBackend(
                        backend_type=vision_backend_selection,
                        endpoint=vision_api_endpoint,
                        model_name=None,  # Auto-detect
                        temperature=temperature
                    )
                    if vision_llm.supports_images():
                        vision_backend_mode = vision_backend_selection
                        vision_caption_enabled = True
                        vision_model_used = getattr(vision_llm, "model_name", "auto-detected")
                    else:
                        vision_backend_mode = "disabled"
                        vision_init_warning = (
                            f"Vision backend '{vision_backend_selection}' does not advertise image support."
                        )
                except Exception as exc:
                    vision_backend_mode = "disabled"
                    vision_init_warning = (
                        f"Vision backend init failed ({vision_backend_selection}): {exc}"
                    )
                    print(f"[Text-to-Image] ⚠️ Vision backend '{vision_backend_selection}' initialization failed: {exc}")
                    print(f"[Text-to-Image] → Continuing with text expansion only (no vision captions)")
                    vision_llm = None
            elif vision_backend_selection == "qwen3_vl":
                # Use vision_api_endpoint for custom model path
                vision_qwen_config = {
                    "model": None,  # Auto-detect from vision_api_endpoint
                    "backend_hint": vision_api_endpoint if vision_api_endpoint != "http://localhost:1234/v1" else None,
                }
                vision_backend_mode = "qwen3_vl"
                vision_caption_enabled = True
                vision_model_used = "Qwen3-VL (auto-detected)"
            else:
                vision_backend_mode = "disabled"

            if not vision_model_used:
                vision_model_used = getattr(llm, "model_name", "auto-detected")

            analysis_backend_label = vision_backend_mode
            if analysis_backend_label == "inherit":
                analysis_backend_label = f"inherit:{llm.backend_type}"

            if not vision_caption_enabled:
                vision_model_used = ""

            reference_warnings: List[str] = []
            if vision_init_warning:
                reference_warnings.append(vision_init_warning)
            if reference_images and not vision_caption_enabled:
                reference_warnings.append(
                    "Vision captioning disabled; reference traits rely on heuristic estimates."
                )

            # Wrap vision processing in try/except to prevent vision failures from breaking text expansion
            image_analyses = []
            try:
                for entry in reference_images:
                    label = entry.get("label", "Reference")
                    tensor = entry.get("tensor")
                    override_caption = entry.get("caption_override")
                    analysis = self._analyze_reference_image(
                        tensor,
                        label,
                        vision_llm=vision_llm if vision_caption_enabled and vision_llm is not None else None,
                        override_caption=override_caption,
                        qwen_config=vision_qwen_config if vision_backend_mode == "qwen3_vl" else None,
                        vision_temperature=temperature,
                        vision_backend=analysis_backend_label,
                        vision_model=vision_model_used
                    )
                    if override_caption:
                        existing_warnings = analysis.setdefault("warnings", [])
                        override_note = f"{label}: caption supplied by override."
                        if override_note not in existing_warnings:
                            existing_warnings.append(override_note)
                    warnings_from_analysis = analysis.get("warnings") or []
                    for warning in warnings_from_analysis:
                        if warning not in reference_warnings:
                            reference_warnings.append(warning)
                    image_analyses.append(analysis)
            except Exception as vision_exc:
                # Vision processing failed - log error but continue with text expansion
                error_msg = f"Vision processing failed: {str(vision_exc)}"
                print(f"[Text-to-Image] ⚠️ {error_msg}")
                reference_warnings.append(error_msg)
                # Create fallback analyses if we got partial results
                if not image_analyses and reference_images:
                    for entry in reference_images:
                        label = entry.get("label", "Reference")
                        fallback = {
                            "label": label,
                            "summary": f"{label}: vision analysis failed, continuing with text expansion",
                            "details": ["Vision model unavailable"],
                            "warnings": [error_msg]
                        }
                        image_analyses.append(fallback)

            # STEP 2: Resolve random/auto options
            resolved_settings, setting_sources = self._resolve_settings(
                camera_angle, composition, lighting_source, lighting_quality,
                time_of_day, historical_period, weather, art_style, genre_style, color_mood,
                creative_randomness,
                subject_framing, subject_pose, prompt_context,
                target_platform
            )
            
            # STEP 3: Build enhancement prompt
            platform_config = get_platform_config(target_platform)
            quality_emphasis = bool(platform_config.get("quality_emphasis", True))
            resolved_settings["quality_emphasis"] = "enabled" if quality_emphasis else "disabled"
            setting_sources["quality_emphasis"] = {"mode": "platform", "value": resolved_settings["quality_emphasis"]}
            
            # Wrap reference guidance processing to prevent failures from blocking text expansion
            reference_guidance = ""
            reference_notes = []
            reference_meta = {}
            
            try:
                directive_analyses, directive_meta = self._run_reference_directive_analysis(
                    image_analyses,
                    reference_plan,
                    llm
                )

                reference_guidance, reference_notes, guidance_meta = self._build_reference_guidance(
                    directive_analyses,
                    reference_plan,
                    llm,
                    prompt_context
                )
                reference_meta = self._merge_reference_metadata(reference_plan, directive_meta, guidance_meta)
            except Exception as ref_exc:
                # Reference guidance processing failed - log but continue
                error_msg = f"Reference guidance generation failed: {str(ref_exc)}"
                print(f"[Text-to-Image] ⚠️ {error_msg}")
                reference_warnings.append(error_msg)
                # Initialize empty reference data
                reference_meta = {
                    "analysis_method": "failed",
                    "reference_count": len(image_analyses),
                    "llm_queries": 0,
                    "llm_successes": 0,
                    "warnings": [error_msg]
                }
            
            # Always update reference_meta with vision info (even if guidance failed)
            reference_meta.update(
                {
                    "vision_backend_requested": vision_backend_selection,
                    "vision_backend_resolved": vision_backend_mode,
                    "vision_caption_enabled": vision_caption_enabled,
                    "vision_model_used": vision_model_used,
                }
            )
            if vision_qwen_config:
                reference_meta["vision_backend_config"] = vision_qwen_config
            if reference_warnings:
                reference_meta["warnings"] = reference_warnings

            backend_set = sorted(
                {
                    str(analysis.get("vision_backend"))
                    for analysis in image_analyses
                    if analysis.get("vision_backend")
                }
            )
            model_set = sorted(
                {
                    str(analysis.get("vision_model"))
                    for analysis in image_analyses
                    if analysis.get("vision_model")
                }
            )
            source_set = sorted(
                {
                    str(analysis.get("vision_caption_source"))
                    for analysis in image_analyses
                    if analysis.get("vision_caption_source")
                }
            )
            if backend_set:
                reference_meta["vision_backends_used"] = backend_set
            if model_set:
                reference_meta["vision_models_used"] = model_set
            if source_set:
                reference_meta["vision_caption_sources"] = source_set

            reference_caption_payload: List[Tuple[str, str]] = []
            for analysis, entry in zip(image_analyses, reference_plan):
                label = entry.get("label", analysis.get("label", "Reference"))
                caption_text = analysis.get("vision_caption") or analysis.get("summary")
                if caption_text:
                    prefix = "(override) " if analysis.get("caption_override") else ""
                    reference_caption_payload.append((label, f"{prefix}{caption_text}"))
            
            creative_brainstorm = self._generate_creative_brainstorm(
                text_prompt,
                resolved_settings.get("creative_randomness", "off")
            )
            
            system_prompt = self._build_system_prompt(
                target_platform,
                platform_config,
                resolved_settings,
                reference_plan,
                prompt_context
            )
            
            user_prompt = self._build_user_prompt(
                text_prompt,
                resolved_settings,
                target_platform,
                prompt_context,
                reference_guidance,
                creative_brainstorm,
                reference_caption_payload
            )
            
            # STEP 4: Prepare keyword overrides and call LLM
            pos_kw_list = parse_keywords(positive_keywords)
            neg_kw_list = parse_keywords(negative_keywords)

            max_tokens_requested = self._determine_max_tokens(
                platform_config,
                resolved_settings.get("creative_randomness")
            )
            capped_tokens, token_cap_note = self._cap_tokens_for_backend(
                llm.backend_type,
                getattr(llm, "model_name", None),
                max_tokens_requested
            )
            backend_params = {
                "backend_type": llm_backend,
                "endpoint": api_endpoint,
                "temperature": temperature
            }

            response, llm_used, llm_attempts = self._call_main_llm_with_retries(
                llm,
                system_prompt,
                user_prompt,
                capped_tokens,
                backend_params
            )
            llm = llm_used
            raw_llm_output = response.get("response", "")
            llm_error_message = response.get("error", "")
            main_llm_success = bool(response.get("success")) and bool((raw_llm_output or "").strip())

            fallback_meta: Optional[Dict[str, Any]] = None
            fallback_used = False

            # STEP 5: Parse and format response (fallback on failure)
            if main_llm_success:
                enhanced_prompt = self._parse_llm_response(raw_llm_output, target_platform)
                print(f"[Text-to-Image] LLM successfully enhanced prompt (length: {len(enhanced_prompt)} chars)")
            else:
                enhanced_prompt, fallback_meta = self._build_deterministic_fallback_prompt(
                    text_prompt,
                    target_platform,
                    platform_config,
                    resolved_settings,
                    reference_notes
                )
                fallback_used = True
                print(f"[Text-to-Image] ⚠️ LLM failed or returned empty content - using deterministic fallback")
                if llm_error_message:
                    print(f"[Text-to-Image] Error details: {llm_error_message}")
            
            # STEP 5.5: Restore emphasis syntax that was protected
            enhanced_prompt = self._restore_emphasis_syntax(enhanced_prompt)
            
            # STEP 6: Add custom keywords
            if pos_kw_list:
                enhanced_prompt = self._add_keywords(enhanced_prompt, pos_kw_list, target_platform)
            
            # STEP 7: Add platform-specific required tokens
            enhanced_prompt = self._add_platform_requirements(enhanced_prompt, target_platform)

            # STEP 7.5: Boost density if the output is too terse
            enhanced_prompt, density_meta = self._ensure_prompt_density(
                enhanced_prompt,
                target_platform,
                platform_config,
                reference_notes,
                resolved_settings
            )

            if density_meta and density_meta.get("added_phrases"):
                print(
                    f"[Text-to-Image] ℹ️ Density boost added {density_meta['added_phrases']} phrase(s) "
                    f"(words {density_meta['before_words']}→{density_meta['after_words']})."
                )
            else:
                density_meta = None
            
            # STEP 8: Generate negative prompt
            negative_prompt = get_negative_prompt_for_platform(target_platform, neg_kw_list)

            # STEP 8.5: Determine actual selections mentioned by the LLM output
            actual_selections = self._infer_setting_mentions(enhanced_prompt)
            display_context = {
                "setting_sources": setting_sources,
                "actual_selections": actual_selections,
                "reference_meta": reference_meta,
                "reference_image_count": len(reference_images),
                "main_llm_success": main_llm_success,
                "main_llm_error": llm_error_message,
                "llm_attempts": llm_attempts,
                "llm_token_cap_note": token_cap_note,
                "max_tokens_requested": max_tokens_requested,
                "max_tokens_used": capped_tokens,
                "fallback_used": fallback_used,
                "fallback_meta": fallback_meta,
                "density_meta": density_meta,
                "quality_emphasis": quality_emphasis,
                "reference_guidance_used": bool(reference_guidance.strip()) if reference_guidance else False,
                "reference_directives": reference_plan,
                "reference_warnings": reference_warnings,
                "random_seed": {
                    "value": seed_value,
                    "mode": resolved_seed_mode,
                    "requested": requested_seed,
                    "requested_mode": seed_mode_normalized
                },
                "vision": {
                    "requested_backend": vision_backend_selection,
                    "resolved_backend": vision_backend_mode,
                    "resolved_model": vision_model_used,
                    "caption_enabled": vision_caption_enabled,
                }
            }
            
            # STEP 9: Format settings display
            settings_display = self._format_settings_display(
                resolved_settings,
                platform_config,
                reference_notes,
                display_context
            )
            
            # STEP 10: Save if requested
            if save_to_file:
                metadata = {
                    "type": "text-to-image",
                    "platform": target_platform,
                    "platform_name": platform_config["name"],
                    "model": llm.model_name or "auto-detected",
                    "backend": llm_backend,
                    "temperature": temperature,
                    "original_prompt": text_prompt,
                    "settings": resolved_settings,
                    "setting_sources": setting_sources,
                    "reference_meta": reference_meta,
                    "vision_captions": reference_meta.get("vision_captions", []),
                    "vision_caption_errors": reference_meta.get("vision_caption_errors", []),
                    "vision_backend_requested": vision_backend_selection,
                    "vision_backend_resolved": vision_backend_mode,
                    "vision_model_used": vision_model_used,
                    "vision_caption_enabled": vision_caption_enabled,
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "raw_llm_output": raw_llm_output,
                    "creative_brainstorm": creative_brainstorm,
                    "reference_guidance": reference_guidance,
                    "reference_notes_log": reference_notes,
                    "reference_llm_logs": reference_meta.get("llm_logs", []),
                    "main_llm_success": main_llm_success,
                    "main_llm_error": llm_error_message,
                    "reference_warnings": reference_warnings,
                    "max_tokens_requested": max_tokens_requested,
                    "max_tokens_used": capped_tokens,
                    "token_cap_note": token_cap_note,
                    "llm_attempts": llm_attempts,
                    "fallback_used": fallback_used,
                    "fallback_meta": fallback_meta,
                    "density_meta": density_meta,
                    "random_seed_requested": requested_seed,
                    "random_seed_used": seed_value,
                    "random_seed_mode_requested": seed_mode_normalized,
                    "random_seed_mode_resolved": resolved_seed_mode
                }

                if vision_qwen_config:
                    metadata["vision_backend_config"] = vision_qwen_config
                
                save_result = save_prompts_to_file(
                    positive_prompt=enhanced_prompt,
                    negative_prompt=negative_prompt,
                    breakdown=settings_display,
                    metadata=metadata,
                    filename_base=filename_base,
                    output_dir=self.output_dir
                )
                
                file_status = f"💾 Saved to {save_result['filepath']}" if save_result["success"] else "⚠️ Save failed"
            else:
                file_status = "Not saved"
            
            llm_status_parts = []
            if main_llm_success:
                llm_status_parts.append("Main LLM: responded")
            else:
                error_snippet = (llm_error_message or "unknown error").splitlines()[0][:120]
                error_snippet = error_snippet.replace('|', '/')
                llm_status_parts.append(f"Main LLM: failed ({error_snippet})")

            if token_cap_note:
                llm_status_parts.append(
                    f"Token cap {capped_tokens}/{max_tokens_requested}"
                )

            if llm_attempts and len(llm_attempts) > 1:
                llm_status_parts.append(f"LLM attempts: {len(llm_attempts)}")

            if fallback_used:
                fallback_phrase_count = fallback_meta.get("combined_total") if fallback_meta else None
                if fallback_phrase_count:
                    llm_status_parts.append(f"Fallback detail +{fallback_phrase_count}")
                else:
                    llm_status_parts.append("Fallback detail applied")

            if density_meta:
                llm_status_parts.append(
                    f"Density boost +{density_meta.get('added_phrases', 0)}"
                )

            ref_count = reference_meta.get("reference_count", 0)
            ref_method = reference_meta.get("analysis_method", "none")
            if ref_count:
                queries = reference_meta.get("llm_queries", 0)
                successes = reference_meta.get("llm_successes", 0)
                if queries:
                    llm_status_parts.append(
                        f"Reference LLM: {successes}/{queries} responses ({ref_method})"
                    )
                else:
                    llm_status_parts.append(f"Reference LLM: not invoked ({ref_method})")
            else:
                llm_status_parts.append("Reference LLM: no references")

            if ref_count:
                llm_status_parts.append(f"References sent: {ref_count}")
                directive_labels = reference_meta.get("directive_labels") or []
                if directive_labels:
                    llm_status_parts.append("Directives: " + ", ".join(directive_labels))
            else:
                llm_status_parts.append("References sent: none")

            if reference_warnings:
                warning_preview = reference_warnings[0]
                if len(reference_warnings) > 1:
                    warning_preview += f" (+{len(reference_warnings) - 1} more)"
                if len(warning_preview) > 160:
                    warning_preview = warning_preview[:157] + "…"
                llm_status_parts.append(f"Reference warnings: {warning_preview}")

            llm_status_parts.append(f"Seed: {seed_value} ({resolved_seed_mode})")

            status_prefix = "✅" if main_llm_success else "⚠️"
            status = (
                f"{status_prefix} Enhanced for {platform_config['name']} | "
                + " | ".join(llm_status_parts)
                + f" | {file_status}"
            )
            
            # Format vision captions for output
            vision_captions_list = reference_meta.get("vision_captions", [])
            if vision_captions_list:
                vision_caption_output = "\n\n".join(
                    f"Reference {i+1}: {caption}"
                    for i, caption in enumerate(vision_captions_list)
                )
            else:
                vision_caption_output = ""
            
            return (
                enhanced_prompt,
                negative_prompt,
                settings_display,
                status,
                vision_caption_output,
                seed_value,
                {
                    "ui": {
                        "random_seed": int(seed_value),
                        "seed_mode": resolved_seed_mode
                    }
                }
            )
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"ERROR in text-to-image enhancement: {error_detail}")
            return (
                text_prompt,
                "",
                "",
                f"❌ Error: {str(e)}",
                "",
                -1
            )
        finally:
            random.setstate(python_random_state)
            np.random.set_state(numpy_random_state)
    
    def _get_simple_image_description(self, image: torch.Tensor, label: str) -> str:
        """Backward-compatible helper returning the concise summary of an image analysis."""

        analysis = self._analyze_reference_image(image, label)
        return str(analysis.get("summary", f"{label}: [Image provided as reference]"))
    
    def _process_alternations(self, text: str) -> str:
        """
        Process alternation syntax {option1|option2|option3}
        Replaces with randomly chosen option
        """
        import re
        
        # Pattern to match {option1|option2|option3}
        pattern = r'\{([^{}]+)\}'
        
        def replace_alternation(match):
            options = match.group(1).split('|')
            # Strip whitespace from each option
            options = [opt.strip() for opt in options]
            return random.choice(options)
        
        # Keep replacing until no more alternations found (handles nested cases)
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        while '{' in text and '|' in text and iteration < max_iterations:
            new_text = re.sub(pattern, replace_alternation, text)
            if new_text == text:  # No more changes
                break
            text = new_text
            iteration += 1
        
        return text
    
    def _preserve_emphasis_syntax(self, text: str) -> str:
        """
        Protect emphasis syntax (keyword:1.5) from being modified
        Replaces temporarily with placeholders during LLM processing
        """
        import re
        
        # Pattern to match (text:number) emphasis syntax
        # This matches things like (dark skin:1.5) or (hair:0.8)
        pattern = r'\(([^():]+):(\d+\.?\d*)\)'
        
        # Find all emphasis patterns
        emphasis_patterns = re.findall(pattern, text)
        
        # Store original patterns
        self._emphasis_store = []
        
        # Replace with placeholders
        def replace_emphasis(match):
            full_match = match.group(0)
            placeholder = f"__EMPHASIS_{len(self._emphasis_store)}__"
            self._emphasis_store.append(full_match)
            return placeholder
        
        text = re.sub(pattern, replace_emphasis, text)
        
        return text
    
    def _restore_emphasis_syntax(self, text: str) -> str:
        """
        Restore emphasis syntax that was protected
        """
        if not hasattr(self, '_emphasis_store'):
            return text
        
        # Restore placeholders with original emphasis syntax
        for i, original in enumerate(self._emphasis_store):
            placeholder = f"__EMPHASIS_{i}__"
            text = text.replace(placeholder, original)
        
        # Clear the store
        self._emphasis_store = []
        
        return text
    
    def _resolve_settings(
        self,
        camera_angle: str,
        composition: str,
        lighting_source: str,
        lighting_quality: str,
        time_of_day: str,
        historical_period: str,
        weather: str,
        art_style: str,
        genre_style: str,
        color_mood: str,
        creative_randomness: str,
        subject_framing: str,
        subject_pose: str,
        prompt_context: str,
        platform: str
    ) -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
        """Resolve auto/random options to actual values and record their origins."""

        resolved: Dict[str, str] = {}
        sources: Dict[str, Dict[str, str]] = {}

        # Camera angle
        if camera_angle == "random":
            choice = random.choice(self.camera_angles)
            resolved["camera_angle"] = choice
            sources["camera_angle"] = {"mode": "random", "value": choice}
        elif camera_angle not in ["auto", "none"]:
            resolved["camera_angle"] = camera_angle
            sources["camera_angle"] = {"mode": "user", "value": camera_angle}
        elif camera_angle == "auto":
            resolved["camera_angle"] = "auto (LLM chooses camera angle)"
            sources["camera_angle"] = {"mode": "llm"}
        else:
            sources["camera_angle"] = {"mode": "none"}

        # Composition
        if composition == "random":
            choice = random.choice(self.composition_styles)
            resolved["composition"] = choice
            sources["composition"] = {"mode": "random", "value": choice}
        elif composition not in ["auto", "none"]:
            resolved["composition"] = composition
            sources["composition"] = {"mode": "user", "value": composition}
        elif composition == "auto":
            resolved["composition"] = "auto (LLM arranges composition)"
            sources["composition"] = {"mode": "llm"}
        else:
            sources["composition"] = {"mode": "none"}

        # Lighting source
        if lighting_source == "random":
            choice = random.choice(self.lighting_sources)
            resolved["lighting_source"] = choice
            sources["lighting_source"] = {"mode": "random", "value": choice}
        elif lighting_source not in ["auto", "none"]:
            resolved["lighting_source"] = lighting_source
            sources["lighting_source"] = {"mode": "user", "value": lighting_source}
        elif lighting_source == "auto":
            resolved["lighting_source"] = "auto (LLM selects lighting source)"
            sources["lighting_source"] = {"mode": "llm"}
        else:
            sources["lighting_source"] = {"mode": "none"}

        # Lighting quality
        if lighting_quality == "random":
            choice = random.choice(self.lighting_quality)
            resolved["lighting_quality"] = choice
            sources["lighting_quality"] = {"mode": "random", "value": choice}
        elif lighting_quality not in ["auto", "none"]:
            resolved["lighting_quality"] = lighting_quality
            sources["lighting_quality"] = {"mode": "user", "value": lighting_quality}
        elif lighting_quality == "auto":
            resolved["lighting_quality"] = "auto (LLM refines lighting quality)"
            sources["lighting_quality"] = {"mode": "llm"}
        else:
            sources["lighting_quality"] = {"mode": "none"}

        # Time of day
        if time_of_day == "random":
            choice = random.choice(self.times_of_day)
            resolved["time_of_day"] = choice
            sources["time_of_day"] = {"mode": "random", "value": choice}
        elif time_of_day not in ["auto", "none"]:
            resolved["time_of_day"] = time_of_day
            sources["time_of_day"] = {"mode": "user", "value": time_of_day}
        elif time_of_day == "auto":
            resolved["time_of_day"] = "auto (LLM selects time of day)"
            sources["time_of_day"] = {"mode": "llm"}
        else:
            sources["time_of_day"] = {"mode": "none"}

        # Historical period
        if historical_period == "random":
            choice = random.choice(self.historical_periods)
            resolved["historical_period"] = choice
            sources["historical_period"] = {"mode": "random", "value": choice}
        elif historical_period not in ["auto", "none"]:
            resolved["historical_period"] = historical_period
            sources["historical_period"] = {"mode": "user", "value": historical_period}
        elif historical_period == "auto":
            resolved["historical_period"] = "auto (LLM infers historical context)"
            sources["historical_period"] = {"mode": "llm"}
        else:
            sources["historical_period"] = {"mode": "none"}

        # Weather
        if weather == "random":
            choice = random.choice(self.weather_conditions)
            resolved["weather"] = choice
            sources["weather"] = {"mode": "random", "value": choice}
        elif weather not in ["auto", "none"]:
            resolved["weather"] = weather
            sources["weather"] = {"mode": "user", "value": weather}
        elif weather == "auto":
            resolved["weather"] = "auto (LLM selects weather)"
            sources["weather"] = {"mode": "llm"}
        else:
            sources["weather"] = {"mode": "none"}

        # Art style
        if art_style not in ["auto", "none"]:
            resolved["art_style"] = art_style
            sources["art_style"] = {"mode": "user", "value": art_style}
        elif art_style == "auto":
            resolved["art_style"] = "auto (LLM selects art style)"
            sources["art_style"] = {"mode": "llm"}
        else:
            sources["art_style"] = {"mode": "none"}

        # Color mood
        if color_mood == "random":
            choice = random.choice([
                "vibrant", "muted", "warm tones", "cool tones", "pastel", "high contrast"
            ])
            resolved["color_mood"] = choice
            sources["color_mood"] = {"mode": "random", "value": choice}
        elif color_mood not in ["auto", "none"]:
            resolved["color_mood"] = color_mood
            sources["color_mood"] = {"mode": "user", "value": color_mood}
        elif color_mood == "auto":
            resolved["color_mood"] = "auto (LLM selects color mood)"
            sources["color_mood"] = {"mode": "llm"}
        else:
            sources["color_mood"] = {"mode": "none"}

        # Genre style
        if genre_style == "random":
            choice = random.choice(self.genre_styles)
            resolved["genre_style"] = choice
            sources["genre_style"] = {"mode": "random", "value": choice}
        elif genre_style not in ["auto", "none"]:
            resolved["genre_style"] = genre_style
            sources["genre_style"] = {"mode": "user", "value": genre_style}
        elif genre_style == "auto":
            resolved["genre_style"] = "auto (LLM selects genre/mood)"
            sources["genre_style"] = {"mode": "llm"}
        else:
            sources["genre_style"] = {"mode": "none"}

        # Creative randomness level
        if creative_randomness == "auto":
            resolved_randomness = self._auto_randomness_choice(platform)
            sources["creative_randomness"] = {"mode": "auto", "value": resolved_randomness}
        elif creative_randomness == "none":
            resolved_randomness = "none"
            sources["creative_randomness"] = {"mode": "none", "value": "none"}
        else:
            resolved_randomness = creative_randomness
            sources["creative_randomness"] = {"mode": "user", "value": resolved_randomness}
        resolved["creative_randomness"] = resolved_randomness

        # Subject framing
        if subject_framing == "random":
            choice = random.choice(self.subject_framings)
            resolved["subject_framing"] = choice
            sources["subject_framing"] = {"mode": "random", "value": choice}
        elif subject_framing not in ["auto", "none"]:
            resolved["subject_framing"] = subject_framing
            sources["subject_framing"] = {"mode": "user", "value": subject_framing}
        elif subject_framing == "auto":
            resolved["subject_framing"] = "auto (LLM frames subject)"
            sources["subject_framing"] = {"mode": "llm"}
        else:
            sources["subject_framing"] = {"mode": "none"}

        # Subject pose
        if subject_pose == "random":
            choice = random.choice(self.subject_poses)
            resolved["subject_pose"] = choice
            sources["subject_pose"] = {"mode": "random", "value": choice}
        elif subject_pose not in ["auto", "none"]:
            resolved["subject_pose"] = subject_pose
            sources["subject_pose"] = {"mode": "user", "value": subject_pose}
        elif subject_pose == "auto":
            resolved["subject_pose"] = "auto (LLM chooses pose)"
            sources["subject_pose"] = {"mode": "llm"}
        else:
            sources["subject_pose"] = {"mode": "none"}

        # Prompt context
        if prompt_context == "auto":
            resolved["prompt_context"] = "auto (LLM interprets input role)"
            sources["prompt_context"] = {"mode": "llm"}
        elif prompt_context == "none":
            resolved["prompt_context"] = "none"
            sources["prompt_context"] = {"mode": "none"}
        else:
            resolved["prompt_context"] = prompt_context
            sources["prompt_context"] = {"mode": "user", "value": prompt_context}

        # Attach platform-specific defaults for length/detail expectations
        platform_config = get_platform_config(platform)
        resolved_length = platform_config.get(
            "length_guidance",
            "Generate a full-length, highly detailed prompt"
        )
        resolved_detail = platform_config.get(
            "detail_expectation",
            "Ultra detailed description"
        )
        resolved["length_mode"] = resolved_length
        resolved["detail_mode"] = resolved_detail
        sources["length_mode"] = {"mode": "platform", "value": resolved_length}
        sources["detail_mode"] = {"mode": "platform", "value": resolved_detail}

        return resolved, sources

    def _auto_randomness_choice(self, platform: str) -> str:
        """Choose a creative randomness default based on platform capabilities."""

        platform = platform.lower()
        if platform in {"flux", "chroma"}:
            return "bold"
        if platform in {"wan_image", "wan22", "wan"}:
            return "moderate"
        if platform in {"qwen_image", "qwen_image_edit"}:
            return "storyteller"
        if platform in {"hunyuan_image"}:
            return "subtle"
        if platform in {"sd_xl", "pony", "illustrious"}:
            return "moderate"
        return "subtle"

    def _analyze_reference_image(
        self,
        image: Optional[torch.Tensor],
        label: str,
        vision_llm: Optional[LLMBackend] = None,
        override_caption: Optional[str] = None,
        qwen_config: Optional[Dict[str, Any]] = None,
        vision_temperature: float = 0.7,
        vision_backend: str = "",
        vision_model: str = ""
    ) -> Dict[str, Any]:
        """Generate descriptive statistics and optional vision captions for a reference image."""

        llm_logs: List[Dict[str, Any]] = []
        warnings: List[str] = []
        vision_caption: Optional[str] = None
        vision_error: Optional[str] = None
        vision_caption_source: Optional[str] = None

        try:
            if isinstance(image, torch.Tensor):
                img_np = image.detach().cpu().numpy()

                if img_np.ndim == 4:
                    img_np = img_np[0]

                img_np = np.clip(img_np, 0.0, 1.0)

                if img_np.shape[-1] < 3:
                    rgb = np.repeat(img_np[..., :1], 3, axis=-1)
                else:
                    rgb = img_np[..., :3]

                height, width = rgb.shape[:2]
                aspect_ratio = width / height if height else 1.0
                orientation = "landscape" if aspect_ratio > 1.25 else "portrait" if aspect_ratio < 0.8 else "square"

                avg_rgb = rgb.mean(axis=(0, 1))
                brightness = float(avg_rgb.mean())

                if brightness > 0.7:
                    tone = "bright"
                elif brightness > 0.45:
                    tone = "balanced"
                else:
                    tone = "dim"

                grayscale = rgb.mean(axis=2)
                contrast_value = float(grayscale.std())
                if contrast_value < 0.08:
                    contrast_desc = "low contrast"
                elif contrast_value < 0.16:
                    contrast_desc = "moderate contrast"
                else:
                    contrast_desc = "high contrast"

                edge_y = np.abs(np.diff(grayscale, axis=0))
                edge_x = np.abs(np.diff(grayscale, axis=1))
                edge_density = float((edge_x.mean() + edge_y.mean()) / 2.0)
                if edge_density < 0.02:
                    texture_desc = "soft textures"
                elif edge_density < 0.05:
                    texture_desc = "mixed textures"
                else:
                    texture_desc = "detailed textures"

                palette_names, palette_hex = self._extract_palette(rgb)

                warmth_score = float(avg_rgb[0] - avg_rgb[2])
                if warmth_score > 0.05:
                    temperature_desc = "warm color temperature"
                elif warmth_score < -0.05:
                    temperature_desc = "cool color temperature"
                else:
                    temperature_desc = "neutral color temperature"

                genre_hint = self._infer_genre_suggestion(tone, contrast_desc, palette_names)

                palette_description = ', '.join(palette_names) if palette_names else "mixed tones"
                base_summary = (
                    f"{label}: {orientation} framing with {tone} exposure, {contrast_desc}, {temperature_desc}, "
                    f"palette leans {palette_description}"
                )

                detail_lines = [
                    f"Orientation: {orientation} framing that feels {texture_desc}.",
                    f"Lighting: {tone} exposure with {temperature_desc}.",
                    f"Contrast impression: {contrast_desc} supporting {texture_desc} detail.",
                    f"Palette impression: {palette_description} hues dominate.",
                    f"Suggested genre alignment: {genre_hint}"
                ]

                category_notes = {
                    "caption": base_summary,
                    "style": f"{contrast_desc} with {texture_desc}; keep the {temperature_desc} mood.",
                    "lighting": f"{tone} lighting with {temperature_desc}; preserve the same luminance mood.",
                    "genre": genre_hint,
                    "time_period": "No explicit era cues detected; align with selected time period.",
                    "subject": f"Maintain the subject presence implied by the {orientation} framing.",
                    "objects": "Refer to this image for relative placement of supporting forms.",
                    "color": f"Palette guidance: {palette_description} tones.",
                    "composition": f"Keep a {orientation} layout and similar balance between subject and environment."
                }

                caption_prompt = (
                    "Describe this reference image in exhaustive detail. Cover subjects, setting, focal points, "
                    "lighting, mood, palette, and any noteworthy props or actions. Write at least three complete sentences "
                    "that mention every important element you observe."
                )
                caption_system_prompt = (
                    "You are an expert visual analyst. Describe every element in the image clearly and precisely."
                )

                pil_image: Optional[Image.Image] = None

                if override_caption and override_caption.strip():
                    vision_caption = override_caption.strip()
                    vision_caption_source = "override"
                elif qwen_config:
                    try:
                        pil_image = Image.fromarray((rgb * 255).astype(np.uint8))
                        qwen_result = caption_with_qwen3_vl(
                            image=pil_image,
                            prompt=caption_prompt,
                            system_prompt=caption_system_prompt,
                            model_spec=qwen_config.get("model"),
                            backend_hint=qwen_config.get("backend_hint"),
                            max_new_tokens=768,
                            temperature=max(0.0, float(vision_temperature)),
                        )
                        if qwen_result.get("success") and qwen_result.get("caption"):
                            vision_caption = qwen_result["caption"].strip()
                            vision_caption_source = "qwen3_vl"
                        else:
                            error_message = qwen_result.get("error") or "Qwen3-VL caption failed"
                            snippet = str(error_message).splitlines()[0][:200]
                            warnings.append(f"{label}: Qwen3-VL caption failed ({snippet})")
                            vision_error = snippet
                    except Exception as exc:
                        snippet = str(exc).splitlines()[0][:200]
                        warnings.append(f"{label}: Qwen3-VL caption failed ({snippet})")
                        vision_error = snippet
                elif vision_llm:
                    if pil_image is None:
                        pil_image = Image.fromarray((rgb * 255).astype(np.uint8))
                    image_buffer = io.BytesIO()
                    pil_image.save(image_buffer, format="PNG")
                    image_bytes = image_buffer.getvalue()
                    image_buffer.close()

                    caption_result = vision_llm.caption_image(
                        image_bytes=image_bytes,
                        label=label,
                        prompt=caption_prompt,
                        max_tokens=480
                    )
                    log_entry = caption_result.get("log_entry") if isinstance(caption_result, dict) else None
                    if log_entry:
                        llm_logs.append(log_entry)
                    if caption_result.get("success") and caption_result.get("caption"):
                        vision_caption = caption_result["caption"].strip()
                        vision_caption_source = vision_llm.backend_type
                    else:
                        error_message = caption_result.get("error") if isinstance(caption_result, dict) else None
                        if error_message:
                            snippet = str(error_message).splitlines()[0][:160]
                            warnings.append(f"{label}: vision caption failed ({snippet})")
                            vision_error = snippet
            else:
                if not (override_caption and override_caption.strip()):
                    raise ValueError("Reference image must be provided unless a caption override is supplied")

                vision_caption = override_caption.strip()
                vision_caption_source = "override"
                warnings.append(f"{label}: analysis based solely on supplied caption override.")
                height = width = 0
                aspect_ratio = 1.0
                orientation = "unspecified"
                tone = "balanced"
                contrast_desc = "moderate contrast"
                texture_desc = "mixed textures"
                temperature_desc = "neutral color temperature"
                palette_names = []
                palette_hex = []
                palette_description = "mixed tones"
                genre_hint = "Flexible genre potential; adapt to project goals."
                base_summary = f"{label}: reference caption provided without image analysis."
                detail_lines = [vision_caption]
                category_notes = {
                    key: vision_caption for key in self.reference_usage_labels.keys()
                }

            summary = vision_caption and f"{label}: {vision_caption}" or base_summary

            if vision_caption:
                detail_lines = [vision_caption] + detail_lines
                caption_for_notes = vision_caption
                category_notes = {
                    key: caption_for_notes for key in self.reference_usage_labels.keys()
                }
                category_notes["lighting"] = (
                    f"{caption_for_notes} | Lighting heuristics: {tone} with {temperature_desc}."
                )
                category_notes["composition"] = (
                    f"{caption_for_notes} | Maintain the {orientation} framing relationships."
                )
                category_notes["color"] = (
                    f"{caption_for_notes} | Palette impression: {palette_description} hues."
                )

            analysis_result: Dict[str, Any] = {
                "label": label,
                "width": width,
                "height": height,
                "orientation": orientation,
                "aspect_ratio": aspect_ratio,
                "tone": tone,
                "contrast_description": contrast_desc,
                "texture_description": texture_desc,
                "temperature_description": temperature_desc,
                "palette_names": palette_names,
                "palette_hex": palette_hex,
                "summary": summary,
                "details": detail_lines,
                "category_notes": category_notes
            }

            if llm_logs:
                analysis_result["llm_logs"] = llm_logs
            if warnings:
                analysis_result["warnings"] = warnings
            if vision_caption:
                analysis_result["vision_caption"] = vision_caption
                if override_caption and override_caption.strip():
                    analysis_result["caption_override"] = True
            if vision_caption_source:
                analysis_result["vision_caption_source"] = vision_caption_source
            if vision_error:
                analysis_result["vision_caption_error"] = vision_error
            analysis_result["vision_backend"] = vision_backend or "disabled"
            analysis_result["vision_model"] = vision_model or ""

            return analysis_result
        except Exception as exc:
            print(f"Warning: Could not analyze reference image ({label}): {exc}")
            fallback_summary = f"{label}: reference image provided (analysis unavailable)"
            result = {
                "label": label,
                "summary": fallback_summary,
                "details": [fallback_summary],
                "category_notes": {
                    key: fallback_summary for key in self.reference_usage_labels.keys()
                },
                "palette_names": [],
                "palette_hex": []
            }
            if warnings:
                result["warnings"] = warnings
            if llm_logs:
                result["llm_logs"] = llm_logs
            return result

    def _extract_palette(self, rgb: np.ndarray, max_colors: int = 3) -> Tuple[List[str], List[str]]:
        """Approximate dominant palette using simple quantization."""

        flat = rgb.reshape(-1, 3)
        if flat.shape[0] > 5000:
            indices = np.random.choice(flat.shape[0], 5000, replace=False)
            flat = flat[indices]

        quantized = (flat * 255).astype(int)
        quantized = (quantized // 32) * 32 + 16

        color_counts: Dict[Tuple[int, int, int], int] = {}
        for r, g, b in quantized:
            key = (int(r), int(g), int(b))
            color_counts[key] = color_counts.get(key, 0) + 1

        if not color_counts:
            color_counts = {(128, 128, 128): 1}

        top_colors = sorted(color_counts.items(), key=lambda item: item[1], reverse=True)[:max_colors]

        palette_rgb = [np.array(color) for color, _ in top_colors]
        palette_names = [self._nearest_color_name(tuple(color)) for color in palette_rgb]
        palette_hex = [self._rgb_to_hex(tuple(color)) for color in palette_rgb]

        return palette_names, palette_hex

    def _nearest_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Map RGB values to a basic color name."""

        reference_colors = {
            "black": (0, 0, 0),
            "white": (255, 255, 255),
            "gray": (128, 128, 128),
            "red": (210, 50, 40),
            "orange": (230, 140, 45),
            "yellow": (235, 220, 70),
            "green": (70, 150, 70),
            "teal": (50, 150, 150),
            "blue": (60, 100, 220),
            "purple": (130, 80, 200),
            "magenta": (200, 70, 180),
            "brown": (120, 80, 50),
            "pink": (240, 170, 200)
        }

        r, g, b = rgb
        best_name = "color"
        best_distance = float("inf")
        for name, ref_rgb in reference_colors.items():
            distance = ((r - ref_rgb[0]) ** 2 + (g - ref_rgb[1]) ** 2 + (b - ref_rgb[2]) ** 2) ** 0.5
            if distance < best_distance:
                best_distance = distance
                best_name = name
        return best_name

    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        return "#" + "".join(f"{max(0, min(255, channel)):02x}" for channel in rgb)

    def _infer_genre_suggestion(self, tone: str, contrast_desc: str, palette_names: List[str]) -> str:
        """Generate a lightweight genre recommendation from tonal clues."""

        if tone == "dim" and "high" in contrast_desc:
            return "Could lean into noir, horror, or dramatic lighting."
        if tone == "bright" and "high" in contrast_desc:
            return "Supports energetic action or bold cinematic styles."
        if tone == "bright" and "low" in contrast_desc:
            return "Suited for airy documentary, minimalist, or romantic moods."
        if "blue" in palette_names or "teal" in palette_names:
            return "Great candidate for sci-fi or cyberpunk palettes."
        if "brown" in palette_names or "orange" in palette_names:
            return "Pairs well with vintage, steampunk, or historical vibes."
        return "Flexible genre potential; adapt to project goals."

    def _resolve_reference_directive_key(self, choice: Optional[str]) -> str:
        """Map user-facing directive text to an internal key."""

        if not choice:
            return "auto"

        normalized = " ".join(choice.strip().lower().replace('-', ' ').split())
        alias_map = {
            "subject only": "subject_only",
            "subject_only": "subject_only",
            "style only": "style_only",
            "style_only": "style_only",
            "lighting only": "lighting_only",
            "lighting_only": "lighting_only"
        }

        if normalized in alias_map:
            key = alias_map[normalized]
        else:
            key = normalized.replace(" ", "_")

        if key not in self.reference_directive_configs:
            return "auto"
        return key

    def _build_reference_plan_entry(self, label: str, choice: Optional[str]) -> Dict[str, Any]:
        """Create a normalized directive entry for a reference image."""

        directive_key = self._resolve_reference_directive_key(choice)
        config = self.reference_directive_configs.get(directive_key, self.reference_directive_configs["auto"])
        display = config.get("display") or directive_key.replace('_', ' ').title()
        return {
            "label": label,
            "user_choice": choice,
            "directive_key": directive_key,
            "display": display,
            "config": config
        }

    def _prepare_reference_plan(self, directive_inputs: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Normalize user selections into directive plan entries."""

        plan: List[Dict[str, Any]] = []
        for label, choice in directive_inputs:
            plan.append(self._build_reference_plan_entry(label, choice))
        return plan

    def _align_reference_plan(self, analyses: List[Dict[str, Any]], plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Align directive plan entries with available analyses, defaulting to auto when missing."""

        resolved_plan: List[Dict[str, Any]] = []
        for idx, analysis in enumerate(analyses):
            if idx < len(plan):
                resolved_plan.append(plan[idx])
            else:
                label = analysis.get("label", f"Reference {idx + 1}")
                resolved_plan.append(self._build_reference_plan_entry(label, "none"))
        return resolved_plan

    def _resolve_category_list(self, categories: Union[str, List[str], None]) -> List[str]:
        """Resolve category hints into a concrete ordered list."""

        if categories is None:
            return []

        if isinstance(categories, str):
            cleaned = categories.strip().lower()
            if cleaned == "all":
                return list(self.reference_usage_labels.keys())
            return [cleaned]

        resolved: List[str] = []
        seen: set = set()
        for category in categories:
            key = str(category).strip().lower()
            if not key:
                continue
            if key == "all":
                return list(self.reference_usage_labels.keys())
            if key not in seen:
                seen.add(key)
                resolved.append(key)
        return resolved

    def _collect_directive_traits(
        self,
        analysis: Dict[str, Any],
        include_hint: Union[str, List[str], None]
    ) -> List[str]:
        """Gather trait notes that align with the selected directive categories."""

        categories = self._resolve_category_list(include_hint)
        notes = analysis.get("category_notes", {}) or {}
        traits: List[str] = []

        for category in categories:
            note = notes.get(category)
            if not note:
                continue
            label = self.reference_usage_labels.get(category, category.replace('_', ' '))
            traits.append(f"{label}: {note}")

        return traits

    def _normalize_focus_lines(self, focus_note: Optional[str]) -> List[str]:
        """Break directive focus text into clean bullet-friendly lines."""

        if not focus_note:
            return []

        sanitized = focus_note.replace("•", "\n").replace(" - ", "\n").replace("- ", "\n")
        fragments = [frag.strip(" \t•-") for frag in sanitized.splitlines() if frag.strip(" \t•-")]

        if not fragments:
            cleaned = focus_note.strip()
            return [cleaned] if cleaned else []

        if len(fragments) == 1:
            sentences = [seg.strip() for seg in re.split(r'(?<=[.!?])\s+', fragments[0]) if seg.strip()]
            return sentences or fragments

        return fragments

    def _clone_analysis_payload(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Copy analysis dictionary while ensuring mutable members are duplicated."""

        cloned = dict(analysis)
        cloned.pop("llm_logs", None)
        details = analysis.get("details")
        if isinstance(details, list):
            cloned["details"] = list(details)
        elif details is None:
            cloned["details"] = []
        else:
            cloned["details"] = [str(details)]

        category_notes = analysis.get("category_notes")
        cloned["category_notes"] = dict(category_notes) if isinstance(category_notes, dict) else {}
        return cloned

    def _append_analysis_detail(self, analysis: Dict[str, Any], detail: str) -> None:
        """Attach a detail string to the analysis record if it is new."""

        if not detail:
            return

        details = analysis.get("details")
        if not isinstance(details, list):
            details = [str(details)] if details else []

        if detail not in details:
            details.append(detail)
        analysis["details"] = details

    def _fallback_directive_analysis(self, analysis: Dict[str, Any], focus_text: str) -> str:
        """Provide a deterministic fallback summary when LLM analysis fails."""

        summary = analysis.get("summary") or "Reference image supplied."
        focus = focus_text.strip() if focus_text else ""
        if focus and focus.lower() not in summary.lower():
            return f"{summary} Focus: {focus}."
        return summary

    def _conduct_directive_analysis_llm(
        self,
        llm: Optional[LLMBackend],
        analysis: Dict[str, Any],
        entry: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any], bool]:
        """Call the LLM to produce directive-focused reference notes."""

        cloned = self._clone_analysis_payload(analysis)
        config = entry.get("config", {}) or {}

        directive_text = config.get("llm_instruction") or config.get("user_guidance") or "Follow the directive."
        focus_text = config.get("analysis_focus") or "Highlight the most useful traits from this reference."

        label = entry.get("label") or cloned.get("label", "Reference")
        display = entry.get("display") or entry.get("directive_key", "Directive")

        category_notes = cloned.get("category_notes") or {}
        note_lines: List[str] = []
        for category, note in category_notes.items():
            if not note:
                continue
            label_text = self.reference_usage_labels.get(category, category.replace('_', ' '))
            note_lines.append(f"{label_text}: {note}")

        details = cloned.get("details")
        if not isinstance(details, list):
            details = [str(details)] if details else []

        caption_text = cloned.get("vision_caption")
        if caption_text:
            normalized_caption = caption_text.strip()
            details = [
                str(detail)
                for detail in details
                if str(detail).strip() and str(detail).strip() != normalized_caption
            ]

        system_prompt = (
            "You analyze detailed reference captions for a prompt engineer. Provide up to two concise sentences that"
            " explain how to use the full caption while honoring the directive focus. Avoid mentioning pixel dimensions,"
            " aspect ratios, or describing yourself. Do not use bullet points or numbering. Keep all critical subjects intact."
        )

        lines: List[str] = [
            f"Reference label: {label}",
            f"Directive choice: {display}",
            f"Directive intent: {directive_text}",
            "",
            "Baseline summary:",
            cloned.get("summary", "")
        ]

        if caption_text:
            lines.append("")
            lines.append("Full reference caption (canonical):")
            lines.append(caption_text)

        if details:
            lines.append("")
            lines.append("Additional analysis notes:")
            lines.extend(f"- {detail}" for detail in details)

        if note_lines:
            lines.append("")
            lines.append("Category cues:")
            lines.extend(f"- {note}" for note in note_lines)

        lines.append("")
        lines.append("Focus request:")
        lines.append(f"- {focus_text}")
        lines.append("")
        lines.append("Compose at most two sentences that satisfy the focus. Return plain text without headers.")

        user_prompt = "\n".join(lines)

        log_entry = {
            "label": label,
            "directive": display,
            "mode": "directive_analysis",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "raw_response": None,
            "success": False
        }

        attempted = bool(llm)
        if not attempted:
            fallback = self._fallback_directive_analysis(cloned, focus_text)
            cloned["directive_analysis"] = fallback
            self._append_analysis_detail(cloned, fallback)
            return cloned, log_entry, attempted

        try:
            response = llm.send_prompt(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=220)
            raw = response.get("response", "")
            if response.get("success") and raw:
                cleaned = raw.strip()
                log_entry["raw_response"] = cleaned
                log_entry["success"] = True
                cloned["directive_analysis"] = cleaned
                self._append_analysis_detail(cloned, cleaned)
                return cloned, log_entry, attempted
            if raw:
                log_entry["raw_response"] = raw.strip()
        except Exception as exc:
            print(f"Directive analysis failed: {exc}")

        fallback = self._fallback_directive_analysis(cloned, focus_text)
        cloned["directive_analysis"] = fallback
        self._append_analysis_detail(cloned, fallback)
        return cloned, log_entry, attempted

    def _run_reference_directive_analysis(
        self,
        analyses: List[Dict[str, Any]],
        plan: List[Dict[str, Any]],
        llm: Optional[LLMBackend]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Generate directive-driven summaries for each reference before prompt construction."""

        if not analyses:
            empty_meta = {
                "phase": "directive_analysis",
                "reference_count": 0,
                "llm_queries": 0,
                "llm_successes": 0,
                "llm_logs": []
            }
            return [], empty_meta

        resolved_plan = self._align_reference_plan(analyses, plan)
        processed: List[Dict[str, Any]] = []
        llm_logs: List[Dict[str, Any]] = []
        llm_queries = 0
        llm_successes = 0

        for analysis, entry in zip(analyses, resolved_plan):
            analysis_logs = analysis.get("llm_logs") or []
            for pre_log in analysis_logs:
                llm_logs.append(pre_log)
                attempted_flag = pre_log.get("attempted")
                if attempted_flag not in (False, None):
                    llm_queries += 1
                    if pre_log.get("success"):
                        llm_successes += 1

            if entry.get("directive_key") == "none":
                cloned = self._clone_analysis_payload(analysis)
                cloned.pop("llm_logs", None)
                caption_text = analysis.get("vision_caption") or analysis.get("summary") or "Reference image provided."
                cloned["directive_analysis"] = caption_text
                self._append_analysis_detail(cloned, caption_text)
                processed.append(cloned)
                continue

            enriched, log_entry, attempted = self._conduct_directive_analysis_llm(llm, analysis, entry)
            processed.append(enriched)
            if log_entry:
                llm_logs.append(log_entry)
            if attempted:
                llm_queries += 1
                if log_entry.get("success"):
                    llm_successes += 1

        meta = {
            "phase": "directive_analysis",
            "reference_count": len(processed),
            "llm_queries": llm_queries,
            "llm_successes": llm_successes,
            "llm_logs": llm_logs
        }
        return processed, meta

    def _build_reference_guidance(
        self,
        analyses: List[Dict[str, Any]],
        plan: List[Dict[str, Any]],
        llm: LLMBackend,
        prompt_context: str
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """Generate textual guidance for using reference images and capture LLM usage stats."""

        if not analyses:
            return "", [], {
                "analysis_method": "none",
                "reference_count": 0,
                "llm_queries": 0,
                "llm_successes": 0,
                "guardrail": self.reference_guardrail_text,
                "directive_labels": [],
                "directives": [],
                "llm_logs": []
            }

        resolved_plan = self._align_reference_plan(analyses, plan)

        method = self.default_reference_analysis_method or "sequential_refine"
        if method not in {"single_pass", "sequential_refine"}:
            method = "sequential_refine"
        if not llm:
            method = "single_pass"

        guidance_lines: List[str] = [
            "Reference guardrails:",
            f"- {self.reference_guardrail_text}",
            "- Integrate each directive once; avoid repeating identical phrasing.",
            "- Preserve every major subject and environmental cue from the provided captions."
        ]

        guidance_lines.append("")

        reference_notes: List[str] = []
        reference_logs: List[Dict[str, Any]] = []
        previous_guidance = ""
        llm_queries = 0
        llm_successes = 0
        vision_captions: List[str] = []
        vision_caption_errors: List[str] = []

        for analysis, entry in zip(analyses, resolved_plan):
            note_label = entry.get('label', analysis.get('label', 'Reference'))
            note_display = entry.get('display', 'Auto')
            focus_lines = self._normalize_focus_lines(analysis.get("directive_analysis"))
            focus_block: List[str] = []
            if focus_lines:
                focus_header = f"{note_label} directive focus:"
                focus_block.append(focus_header)
                focus_block.extend(f"- {line}" for line in focus_lines)

            if method == "sequential_refine":
                refined, success, log_entry = self._refine_reference_with_llm(llm, analysis, entry, previous_guidance)
                llm_queries += 1
                if success:
                    llm_successes += 1
            else:
                refined = self._compose_reference_line(analysis, entry)
                success = False
                log_entry = {
                    "label": entry.get("label", analysis.get("label", "Reference")),
                    "directive": entry.get("display"),
                    "mode": "single_pass",
                    "system_prompt": None,
                    "user_prompt": None,
                    "raw_response": None,
                    "success": False
                }

            block_lines: List[str] = []
            if focus_block:
                guidance_lines.extend(focus_block)
                block_lines.extend(focus_block)

            guidance_lines.append(refined)
            block_lines.append(refined)

            config = entry.get('config', {})
            summary_note = config.get('user_summary') or config.get('user_guidance') or ""
            focus_note = focus_lines[0] if focus_lines else ""
            note_parts: List[str] = []
            if summary_note:
                note_parts.append(summary_note)
            if focus_note:
                note_parts.append(f"Focus: {focus_note}")

            caption_text = analysis.get("vision_caption")
            if caption_text:
                vision_captions.append(caption_text)
                snippet = caption_text if len(caption_text) <= 220 else caption_text[:217] + "…"
                note_parts.append(f"Caption: {snippet}")
            elif analysis.get("vision_caption_error"):
                error_entry = analysis.get("vision_caption_error")
                if error_entry:
                    vision_caption_errors.append(str(error_entry))

            if note_parts:
                reference_notes.append(f"{note_label} ({note_display}): " + " | ".join(note_parts))
            else:
                reference_notes.append(f"{note_label} ({note_display})")

            previous_guidance += "\n".join(block_lines) + "\n"
            reference_logs.append(log_entry)

        if prompt_context == "reference_modification":
            guidance_lines.append(
                "Focus on adjusting existing reference traits rather than inventing wholly new scenes."
            )

        return "\n".join(guidance_lines).strip(), reference_notes, {
            "analysis_method": method,
            "reference_count": len(analyses),
            "llm_queries": llm_queries,
            "llm_successes": llm_successes,
            "guardrail": self.reference_guardrail_text,
            "directive_labels": [entry.get("display") for entry in resolved_plan],
            "directives": [entry.get("directive_key") for entry in resolved_plan],
            "llm_logs": reference_logs,
            "vision_captions": vision_captions,
            "vision_caption_errors": vision_caption_errors
        }

    def _merge_reference_metadata(
        self,
        plan: List[Dict[str, Any]],
        directive_meta: Dict[str, Any],
        guidance_meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine directive analysis and guidance metadata for downstream reporting."""

        directives = [entry.get("directive_key") for entry in plan]
        directive_labels = [entry.get("display") for entry in plan]

        directive_queries = directive_meta.get("llm_queries", 0)
        guidance_queries = guidance_meta.get("llm_queries", 0)
        directive_success = directive_meta.get("llm_successes", 0)
        guidance_success = guidance_meta.get("llm_successes", 0)

        reference_count = max(
            directive_meta.get("reference_count", 0),
            guidance_meta.get("reference_count", 0),
            len(plan)
        )

        combined_logs = (directive_meta.get("llm_logs") or []) + (guidance_meta.get("llm_logs") or [])
        analysis_method = guidance_meta.get("analysis_method") or (
            self.default_reference_analysis_method or "sequential_refine"
        )

        if reference_count == 0:
            analysis_method = "none"

        return {
            "analysis_method": analysis_method,
            "reference_count": reference_count,
            "llm_queries": directive_queries + guidance_queries,
            "llm_successes": directive_success + guidance_success,
            "guardrail": self.reference_guardrail_text,
            "directive_labels": directive_labels,
            "directives": directives,
            "llm_logs": combined_logs,
            "analysis_phase": directive_meta,
            "guidance_phase": guidance_meta,
            "vision_captions": guidance_meta.get("vision_captions", []),
            "vision_caption_errors": guidance_meta.get("vision_caption_errors", [])
        }

    def _resolve_seed_value(self, mode: str, requested_seed: int) -> Tuple[int, str]:
        """Resolve the actual seed value based on the selected seed mode."""

        normalized_mode = (mode or "random").strip().lower()
        valid_modes = {"random", "fixed", "increment", "decrement"}
        if normalized_mode not in valid_modes:
            normalized_mode = "random"

        max_seed = 2_147_483_647
        system_rng = random.SystemRandom()

        state = self._seed_state
        last_mode = state.get("last_mode")
        last_seed = state.get("last_seed")
        last_input = state.get("last_input")

        if requested_seed is None:
            requested_seed = -1
        else:
            requested_seed = int(requested_seed)
        seed_specified = requested_seed >= 0

        def fresh_seed() -> int:
            if seed_specified:
                return requested_seed
            return system_rng.randint(0, max_seed)

        if normalized_mode == "fixed":
            if seed_specified:
                seed_value = requested_seed
            elif last_mode == "fixed" and last_input == requested_seed and last_seed is not None:
                seed_value = int(last_seed)
            else:
                seed_value = fresh_seed()
        elif normalized_mode == "increment":
            if last_mode == "increment" and last_input == requested_seed and last_seed is not None:
                seed_value = int(last_seed) + 1
                if seed_value > max_seed:
                    seed_value = 0
            else:
                seed_value = fresh_seed()
        elif normalized_mode == "decrement":
            if last_mode == "decrement" and last_input == requested_seed and last_seed is not None:
                seed_value = int(last_seed) - 1
                if seed_value < 0:
                    seed_value = max_seed
            else:
                seed_value = fresh_seed()
        else:  # random or fallback
            seed_value = system_rng.randint(0, max_seed)
            normalized_mode = "random"

        state["last_seed"] = int(seed_value)
        state["last_mode"] = normalized_mode
        state["last_input"] = requested_seed

        return int(seed_value), normalized_mode

    def _compose_reference_line(self, analysis: Dict[str, Any], entry: Dict[str, Any]) -> str:
        """Compose a descriptive line for a reference image using directive presets."""

        label = analysis.get("label", "Reference")
        summary = analysis.get("summary", f"{label}: reference image provided")
        config = entry.get("config", {})
        include_hint = config.get("include_categories")
        exclude_categories = config.get("exclude_categories", []) or []
        extra_note = config.get("extra_notes")

        lines = [f"- {summary}"]
        directive_text = config.get("user_guidance")
        if directive_text:
            lines.append(f"  • Directive: {directive_text}")

        traits = self._collect_directive_traits(analysis, include_hint)
        for trait in traits:
            lines.append(f"  • {trait}")

        focus_lines = self._normalize_focus_lines(analysis.get("directive_analysis"))
        for focus in focus_lines:
            lines.append(f"  • Focus note: {focus}")

        for category in exclude_categories:
            label_text = self.reference_usage_labels.get(category, category.replace('_', ' '))
            lines.append(f"  • Avoid mirroring {label_text}; generate a fresh interpretation.")

        if extra_note:
            lines.append(f"  • {extra_note}")

        return "\n".join(lines)

    def _refine_reference_with_llm(
        self,
        llm: LLMBackend,
        analysis: Dict[str, Any],
        entry: Dict[str, Any],
        previous_guidance: str
    ) -> Tuple[str, bool, Dict[str, Any]]:
        """Request a compact reference summary from the LLM when sequential refinement is desired."""

        config = entry.get("config", {})
        include_hint = config.get("include_categories")
        exclude_categories = config.get("exclude_categories", []) or []
        directive_text = config.get("llm_instruction") or config.get("user_guidance", "Follow the directive.")

        emphasis_lines = self._collect_directive_traits(analysis, include_hint)
        avoid_lines = []
        for category in exclude_categories:
            label_text = self.reference_usage_labels.get(category, category.replace('_', ' '))
            avoid_lines.append(f"Avoid copying {label_text}; invent something new.")

        detail_entries = analysis.get("details", [])
        if not isinstance(detail_entries, (list, tuple)):
            detail_entries = [str(detail_entries)] if detail_entries else []

        system_prompt = (
            "You help transform reference analysis into concise prompt guidance. Provide at most two sentences. "
            "Do not mention pixel dimensions, resolutions, or aspect ratios. Avoid repeating phrases verbatim."
        )

        lines: List[str] = [
            f"Reference label: {analysis.get('label', 'Reference')}",
            f"Directive: {directive_text}",
            f"Summary: {analysis.get('summary', '')}"
        ]

        if emphasis_lines:
            lines.append("Focus cues:")
            lines.extend(f"- {cue}" for cue in emphasis_lines)

        if avoid_lines:
            lines.append("Avoid copying:")
            lines.extend(f"- {cue}" for cue in avoid_lines)

        if detail_entries:
            lines.append("Additional observations:")
            lines.extend(f"- {str(detail)}" for detail in detail_entries)

        if previous_guidance:
            lines.append("Guidance already covered for earlier references:")
            lines.append(previous_guidance.strip())

        lines.append("Write guidance that honors the directive without repeating earlier sentences.")
        user_prompt = "\n".join(lines)

        log_entry = {
            "label": analysis.get("label", "Reference"),
            "directive": entry.get("display"),
            "mode": "sequential_refine",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "raw_response": None,
            "success": False
        }

        try:
            response = llm.send_prompt(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=240)
            raw_payload = response.get("response")
            if response.get("success") and raw_payload:
                raw = raw_payload.strip()
                log_entry["raw_response"] = raw
                log_entry["success"] = True
                return "- " + raw, True, log_entry
            if raw_payload:
                log_entry["raw_response"] = raw_payload.strip()
        except Exception as exc:
            print(f"Reference refinement failed: {exc}")

        fallback_text = self._compose_reference_line(analysis, entry)
        return fallback_text, False, log_entry

    def _generate_creative_brainstorm(self, text_prompt: str, randomness_mode: str) -> Optional[str]:
        """Produce creative guidance snippets based on the selected randomness level."""

        randomness_mode = (randomness_mode or "off").lower()
        if randomness_mode in {"off", "none"}:
            return None

        base_subject = text_prompt.split(',')[0].strip() if text_prompt else "the subject"

        if randomness_mode == "subtle":
            return (
                "Creative flourish: add gentle ambient storytelling cues (background sounds, faint weather, or "
                "minor props) that enrich the scene without changing the main subject."
            )

        if randomness_mode == "moderate":
            suggestion = random.choice(self.random_story_settings)
            companion = random.choice(self.random_story_companions)
            return (
                "Creative prompt idea: place {subject} within {setting} accompanied by {companion}. "
                "Retain the original tone but add cohesive environmental storytelling."
            ).format(subject=base_subject, setting=suggestion, companion=companion)

        if randomness_mode in {"bold", "storyteller", "chaotic"}:
            setting = random.choice(self.random_story_settings)
            companion = random.choice(self.random_story_companions)
            conflict = random.choice(self.random_story_conflicts)
            tone = "Embrace surreal twists" if randomness_mode == "chaotic" else "Craft a vivid narrative"
            return (
                f"{tone}: imagine {base_subject} within {setting}, joined by {companion}, {conflict}. "
                "Blend this storyline into the enhanced prompt while preserving user intent."
            )

        return None

    def _determine_max_tokens(
        self,
        platform_config: Dict,
        creative_randomness: Optional[str]
    ) -> int:
        """Adjust LLM max tokens according to platform and desired verbosity."""

        max_tokens_hint = platform_config.get("max_tokens")
        max_words_hint = platform_config.get("max_words")

        if max_tokens_hint:
            base_tokens = int(max_tokens_hint)
        elif max_words_hint:
            base_tokens = int(max_words_hint * 1.45)
        else:
            base_tokens = 1000

        if creative_randomness in {"bold", "storyteller", "chaotic"}:
            base_tokens += 120

        # Provide additional headroom for extremely long prompts
        return min(base_tokens + 200, 1800)

    def _cap_tokens_for_backend(
        self,
        backend: str,
        model_name: Optional[str],
        requested_tokens: int
    ) -> Tuple[int, Optional[str]]:
        """Apply backend-aware caps to avoid overloading smaller local models."""

        backend_lower = (backend or "").lower()
        model_lower = (model_name or "").lower()
        adjusted = int(requested_tokens)
        cap_reason: Optional[str] = None

        def apply_cap(limit: int, reason: str) -> None:
            nonlocal adjusted, cap_reason
            if adjusted > limit:
                adjusted = limit
                if cap_reason is None:
                    cap_reason = reason

        if backend_lower == "qwen3_vl":
            apply_cap(512, "Capped max tokens to 512 for local Qwen3-VL stability.")
        elif backend_lower in {"lm_studio", "ollama"}:
            small_signals = ["1.5b", "2b", "3b", "4b", "tiny", "mini", "phi-2", "phi-3", "phi3", "smol"]
            medium_signals = ["5b", "6b", "7b", "8b"]
            if any(sig in model_lower for sig in small_signals):
                apply_cap(512, f"Capped max tokens for small model '{model_name}'.")
            elif any(sig in model_lower for sig in medium_signals):
                apply_cap(768, f"Capped max tokens for mid-size model '{model_name}'.")
            apply_cap(1024, f"Capped max tokens to 1024 for backend '{backend}'.")
        else:
            apply_cap(1024, "Capped max tokens to 1024 for stability.")

        return adjusted, cap_reason

    def _call_main_llm_with_retries(
        self,
        llm: LLMBackend,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        backend_params: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], LLMBackend, List[Dict[str, Any]]]:
        """Send prompt with limited retries and adaptive token ceilings."""

        attempt_tokens: List[int] = [int(max_tokens)]
        fallback_candidates = [max(240, min(max_tokens, 640)), 320]
        for candidate in fallback_candidates:
            if candidate < attempt_tokens[0]:
                attempt_tokens.append(int(candidate))
        # Preserve order while removing duplicates
        seen: set = set()
        ordered_tokens: List[int] = []
        for value in attempt_tokens:
            if value not in seen:
                ordered_tokens.append(value)
                seen.add(value)

        attempts_log: List[Dict[str, Any]] = []
        current_llm = llm
        last_response: Dict[str, Any] = {"success": False, "response": "", "error": "No attempt"}

        for attempt_index, tokens in enumerate(ordered_tokens):
            response = current_llm.send_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=tokens
            )
            last_response = response
            attempt_info = {
                "attempt": attempt_index + 1,
                "backend": current_llm.backend_type,
                "model": getattr(current_llm, "model_name", None),
                "max_tokens": tokens,
                "success": bool(response.get("success")),
                "error": response.get("error"),
                "empty_response": not bool((response.get("response") or "").strip())
            }
            attempts_log.append(attempt_info)

            if response.get("success") and (response.get("response") or "").strip():
                attempt_info["used"] = True
                return response, current_llm, attempts_log

            if attempt_index < len(ordered_tokens) - 1:
                try:
                    current_llm = LLMBackend(
                        backend_type=backend_params["backend_type"],
                        endpoint=backend_params["endpoint"],
                        model_name=None,
                        temperature=backend_params["temperature"]
                    )
                except Exception as exc:
                    attempts_log.append({
                        "attempt": attempt_index + 1,
                        "backend": backend_params.get("backend_type"),
                        "max_tokens": tokens,
                        "success": False,
                        "error": f"Backend reinit failed: {exc}",
                        "reinit_failed": True
                    })
                    # Continue with existing llm instance if reinit fails

        return last_response, current_llm, attempts_log

    def _settings_to_phrases(self, settings: Dict[str, str]) -> List[str]:
        """Convert resolved settings into descriptive phrases for fallbacks."""

        phrases: List[str] = []
        mapping = {
            "camera_angle": "shot from {value}",
            "composition": "composition guided by {value}",
            "lighting_source": "lit by {value}",
            "lighting_quality": "lighting quality is {value}",
            "time_of_day": "set during {value}",
            "historical_period": "evokes the {value}",
            "weather": "{value} conditions",
            "color_mood": "{value} color palette",
            "genre_style": "{value} tone",
            "subject_framing": "{value} framing",
            "subject_pose": "subject posed {value}"
        }

        for key, template in mapping.items():
            value = settings.get(key)
            if not value:
                continue
            lowered = value.lower()
            if "auto" in lowered or "none" in lowered:
                continue
            phrase = template.format(value=value)
            if phrase not in phrases:
                phrases.append(phrase)

        return phrases

    def _build_deterministic_fallback_prompt(
        self,
        base_prompt: str,
        platform: str,
        platform_config: Dict[str, Any],
        settings: Dict[str, str],
        reference_notes: List[str]
    ) -> Tuple[str, Dict[str, Any]]:
        """Synthesize a deterministic enhancement when the main LLM fails."""

        base = base_prompt.strip() or "Describe the requested scene vividly"
        phrases = self._settings_to_phrases(settings)
        reference_phrases: List[str] = []
        for note in reference_notes:
            if not note:
                continue
            cleaned = note.split(":", 1)[-1].strip() if ":" in note else note.strip()
            if cleaned and cleaned not in reference_phrases:
                reference_phrases.append(cleaned)

        combined = phrases + reference_phrases
        meta = {
            "setting_phrases": len(phrases),
            "reference_phrases": len(reference_phrases),
            "combined_total": len(combined)
        }

        if not combined:
            return base, meta

        addition = ", ".join(combined[:8])

        if platform == "pony":
            normalized = base
            prefix_tokens = ["score_9", "score_8_up", "score_7_up"]
            normalized_lower = normalized.lower()
            missing_prefix = [token for token in prefix_tokens if token not in normalized_lower]
            if missing_prefix:
                normalized = ", ".join(missing_prefix + [normalized])
            if not normalized.endswith(","):
                normalized = normalized.rstrip() + ","
            fallback_prompt = f"{normalized} {addition}".strip()
        else:
            cleaned_base = base.rstrip("., ")
            fallback_prompt = f"{cleaned_base}. {addition}."

        return fallback_prompt, meta

    def _ensure_prompt_density(
        self,
        prompt: str,
        platform: str,
        platform_config: Dict[str, Any],
        reference_notes: List[str],
        settings: Dict[str, str]
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Pad prompts that land well below the target word count."""

        target_words = platform_config.get("max_words")
        if not target_words or target_words < 60:
            return prompt, None

        min_words = max(80, int(target_words * 0.7))
        words_before = len(prompt.split())
        if words_before >= min_words:
            return prompt, None

        additions: List[str] = []
        for note in reference_notes:
            if not note:
                continue
            cleaned = note.split(":", 1)[-1].strip() if ":" in note else note.strip()
            if cleaned and cleaned not in additions:
                additions.append(cleaned)
            if words_before + sum(len(entry.split()) for entry in additions) >= min_words:
                break

        if words_before + sum(len(entry.split()) for entry in additions) < min_words:
            for phrase in self._settings_to_phrases(settings):
                if phrase and phrase not in additions:
                    additions.append(phrase)
                if words_before + sum(len(entry.split()) for entry in additions) >= min_words:
                    break

        if not additions:
            return prompt, None

        if platform == "pony":
            updated = prompt.rstrip()
            if not updated.endswith(","):
                updated = updated.rstrip("., ") + ","
            updated = f"{updated} {', '.join(additions)}"
        else:
            cleaned = prompt.rstrip(".")
            extra = "; ".join(additions)
            updated = f"{cleaned}. {extra}."

        density_meta = {
            "min_words": min_words,
            "before_words": words_before,
            "after_words": len(updated.split()),
            "added_phrases": len(additions)
        }

        return updated, density_meta

    def _build_system_prompt(
        self,
        platform_key: str,
        platform_config: Dict,
        settings: Dict,
        reference_plan: List[Dict[str, Any]],
        prompt_context: str
    ) -> str:
        """Build LLM system prompt with platform-specific instructions"""
        quality_emphasis = bool(platform_config.get("quality_emphasis", True))
        
        platform_name = platform_config["name"]
        platform = platform_config.get("prompt_style", "natural")
        target_words = platform_config.get("max_words")
        min_word_goal: Optional[int] = None
        if isinstance(target_words, (int, float)) and target_words >= 60:
            min_word_goal = max(80, int(target_words * 0.75))
        
        prompt = f"""You are an expert prompt engineer for {platform_name} image generation.

CRITICAL OUTPUT RULES:
1. Output ONLY the final prompt text - no labels, explanations, or meta-commentary
2. Do NOT include phrases like "Here is...", "Prompt:", etc.
3. Start directly with the image description
4. Follow the platform-specific format precisely
5. Never mention source image dimensions, aspect ratios, or pixel counts
6. Keep the user's base prompt concept central; additions must support rather than replace it
7. Treat every reference directive and focus note from the user message as mandatory content; weave them into the final prompt exactly once.

TARGET PLATFORM: {platform_name}
Description: {platform_config['description']}
Prompting Style: {platform_config['prompt_style']}
Optimal Length: {platform_config['optimal_length']}

"""
        prompt += "\nOUTPUT INTENSITY GUIDANCE:\n"
        if min_word_goal:
            prompt += f"- Minimum acceptable length: {min_word_goal} words. Falling short counts as a failure.\n"
        else:
            prompt += "- Deliver a multi-sentence, richly layered description (no terse summaries).\n"

        if reference_plan:
            prompt += "- Dedicate vivid language to every reference directive so each image influences the result.\n"
            if len(reference_plan) > 1:
                prompt += "- Keep reference-derived cues distinct; do not merge them into a single generic sentence.\n"

        if platform_key == "pony":
            prompt += (
                "- Start with the score tags exactly once, then shift into flowing natural-language prose.\n"
                "- After the score tags, produce an expansive narrative covering subject, wardrobe, environment, lighting, and atmosphere. Sparse checklists are unacceptable.\n"
            )
            if reference_plan:
                prompt += "- When references are provided, weave their traits into luxuriant supporting clauses for extra detail.\n"
        prompt += "\n"
        
        # Add platform-specific preferences
        if platform_config.get("preferences"):
            prompt += "\nPLATFORM REQUIREMENTS:\n"
            for pref in platform_config["preferences"]:
                prompt += f"- {pref}\n"
        
        # Add quality tokens if enabled
        if quality_emphasis and platform_config.get("quality_tokens"):
            prompt += f"\nQUALITY TOKENS (use appropriately): {', '.join(platform_config['quality_tokens'][:8])}\n"
        
        # Add required tokens for specific platforms
        if platform_config.get("required_positive"):
            prompt += f"\nREQUIRED TOKENS (must include): {', '.join(platform_config['required_positive'])}\n"
        
        # Add things to avoid
        if platform_config.get("avoid"):
            prompt += "\nAVOID:\n"
            for avoid in platform_config["avoid"]:
                prompt += f"- {avoid}\n"
        
        # Add user-specified settings
        prompt += "\n=== USER REQUIREMENTS ===\n"
        prompt += "Incorporate these settings into the prompt:\n\n"
        
        # Length and detail expectations (always max detail)
        length_guidance = platform_config.get("length_guidance")
        if length_guidance:
            prompt += f"TARGET LENGTH: {length_guidance}\n"

        detail_expectation = platform_config.get("detail_expectation")
        if detail_expectation:
            prompt += f"DETAIL EXPECTATION: {detail_expectation}\n"

        max_words = platform_config.get("max_words")
        if max_words:
            floor_words = int(max_words * 0.6)
            if min_word_goal and min_word_goal > floor_words:
                floor_words = min_word_goal
            prompt += f"ABSOLUTE MINIMUM DETAIL: deliver no fewer than {floor_words} words.\n\n"
        else:
            prompt += "Ensure the description is long-form and exhaustive.\n\n"
        # Handle genre/style if specified
        genre = settings.get("genre_style", "")
        if genre and "auto" not in genre.lower() and "none" not in genre.lower():
            genre_guidance = {
                "surreal": "dreamlike, unexpected juxtapositions, reality-bending elements",
                "cinematic": "film-like quality, dramatic lighting, professional composition",
                "dramatic": "high contrast, emotional intensity, dynamic tension",
                "action": "dynamic motion, energy, movement, intensity",
                "humorous": "playful, whimsical, lighthearted, amusing elements",
                "indie": "artistic, unconventional, creative freedom, unique perspective",
                "horror": "dark atmosphere, ominous mood, eerie elements, tension",
                "scifi": "futuristic, technology, otherworldly, advanced elements",
                "romantic": "soft, intimate, emotional warmth, tender mood",
                "x-rated": "mature themes, adult content, sensual elements",
                "pg": "family-friendly, clean, wholesome, appropriate for all ages",
                "artistic": "creative interpretation, aesthetic focus, expressive",
                "documentary": "realistic, authentic, unposed, natural",
                "minimalist": "simple, clean, essential elements only, negative space",
                "maximalist": "rich details, complex, layered, ornate",
                "vintage": "classic, retro, aged aesthetic, nostalgic feel",
                "modern": "contemporary, current, sleek, clean lines",
                "fantasy": "magical, mythical, imaginative, enchanted",
                "noir": "dark, moody, high contrast shadows, mystery",
                "cyberpunk": "neon, futuristic dystopia, tech, gritty urban",
                "steampunk": "retro-futuristic contraptions, brass machinery, victorian flair",
                "dieselpunk": "industrial grit, roaring engines, interwar aesthetics",
                "mythic": "legendary scale, archetypal symbolism, timeless myth",
                "gothic": "dramatic architecture, chiaroscuro mood, romantic darkness",
                "art deco": "sleek geometry, metallic sheen, roaring twenties glamour",
                "retro futurism": "optimistic vintage sci-fi, bold colors, nostalgic futurism"
            }
            style_desc = genre_guidance.get(genre, genre)
            prompt += f"STYLE/GENRE: {genre} - Infuse the prompt with {style_desc}\n\n"

        # Prompt context guidance
        context_map = {
            "expand_short_prompt": "User provided a shorthand idea. Expand it into a full, production-ready description.",
            "finish_opening_line": "Treat input as the opening line of the prompt. Continue and embellish it coherently.",
            "prompt_from_item_list": "User supplied a checklist. Transform it into a cohesive narrative scene.",
            "modify_reference_image": "Focus on altering specific parts of the reference imagery as requested.",
            "enhance_reference_image": "Use reference images as a base and enrich them with new imaginative elements.",
            # Legacy mappings for backward compatibility
            "abbreviated_prompt": "User provided a shorthand idea. Expand it into a full, production-ready description.",
            "prompt_seed": "Treat input as the opening line of the prompt. Continue and embellish it coherently.",
            "item_list": "User supplied a checklist. Transform it into a cohesive narrative scene.",
            "reference_modification": "Focus on altering specific parts of the reference imagery as requested.",
            "reference_expansion": "Use reference images as a base and enrich them with new imaginative elements."
        }
        if prompt_context in context_map:
            prompt += f"PROMPT CONTEXT: {context_map[prompt_context]}\n\n"

        # Historical period guidance
        historical = settings.get("historical_period")
        if historical and "auto" not in historical.lower() and "none" not in historical.lower():
            prompt += f"TIME PERIOD: Align visuals with the {historical}.\n\n"

        # Creative randomness guidance
        creativity = settings.get("creative_randomness", "off")
        if creativity in self.creative_randomness_modes and creativity not in ["off", "none"]:
            prompt += f"CREATIVE RANDOMNESS ({creativity.upper()}): {self.creative_randomness_modes[creativity]}\n"
            prompt += "Blend surprise elements while keeping the requested subject recognizable.\n\n"

        # Base prompt reinforcement
        prompt += "\nBASE PROMPT PRIORITY:\n"
        prompt += "- The user's text prompt is the authoritative subject. Preserve its characters, actions, and tone.\n"
        prompt += "- If creative randomness or references introduce new ideas, they must enhance (not replace) the base concept.\n"
        prompt += "- Reference directives override conflicting improvisations; missing them counts as failing the task.\n"

        # Reference usage guidance
        if reference_plan:
            prompt += "REFERENCE IMAGE GUIDELINES:\n"
            prompt += f"- {self.reference_guardrail_text}\n"
            prompt += "- Integrate guidance once within the final prompt; do not repeat phrases verbatim.\n"
            for entry in reference_plan:
                config = entry.get("config", {})
                display = entry.get("display", "Reference")
                instruction = config.get("llm_instruction") or config.get("user_guidance")
                label = entry.get("label", "Reference")
                if instruction:
                    prompt += f"- {label} ({display}): {instruction}\n"
            prompt += "\n"
        
        for key, value in settings.items():
            if key in [
                "genre_style",
                "creative_randomness",
                "prompt_context",
                "historical_period",
                "length_mode",
                "detail_mode"
            ]:
                continue
            if value and "none" not in value.lower() and "auto" not in value.lower():
                label = key.replace("_", " ").title()
                prompt += f"- {label}: {value}\n"
        
        # Platform-specific format instructions
        if "pony" in platform_name.lower():
            prompt += """
PONY DIFFUSION FORMAT (CRITICAL):
- MUST START with exactly: score_9, score_8_up, score_7_up
- After score tags, use NATURAL LANGUAGE descriptions (NO underscores)
- Comma-separated detailed phrases
- DO NOT use danbooru tag format (no long_hair, brown_eyes, etc.)
- Use readable text: "long flowing hair", "brown eyes", "red dress"
- Aim for 150-200 words of rich descriptive detail
- Example: score_9, score_8_up, score_7_up, a young woman with long flowing hair, intense gaze, wearing elegant red dress, soft studio lighting, professional portrait
"""
        
        elif "illustrious" in platform_name.lower():
            prompt += """
ILLUSTRIOUS-SPECIFIC INSTRUCTIONS:
- Start with quality tags: masterpiece, best quality
- Use danbooru tag format with underscores
- Detailed character appearance tags
- Clothing and accessory tags
- Background and atmosphere tags
- Example: masterpiece, best quality, 1girl, detailed_face, flowing_dress, etc.
"""
        
        elif "flux" in platform_name.lower():
            prompt += """
FLUX-SPECIFIC INSTRUCTIONS:
- Natural language descriptions (75-150 tokens)
- Use artistic terminology
- Can include "in the style of [artist/style]"
- Quality modifiers important
- Photography terms work well
"""
        
        elif "chroma" in platform_name.lower() or "meisson" in platform_name.lower():
            prompt += """
CHROMA-SPECIFIC INSTRUCTIONS:
- Natural, detailed language (100-200 tokens)
- Excellent with complex scenes
- Can handle multiple subjects
- Describe spatial relationships clearly
- Compositional details important
"""
        
        elif "wan" in platform_name.lower():
            prompt += """
WAN-SPECIFIC INSTRUCTIONS:
- Technical cinematography terms
- Structured format: subject, setting, lighting, composition
- Specific lighting types (soft lighting, edge lighting, etc.)
- Professional photography language
- Medium length (60-120 tokens)
"""
        
        elif "sd_xl" in platform_name.lower() or "sdxl" in platform_name.lower():
            prompt += """
SDXL-SPECIFIC INSTRUCTIONS:
- Token limit: 40-75 tokens optimal
- Front-load important concepts
- Quality tokens at start
- Can use natural language or tags
- Keep concise but descriptive
"""
        
        prompt += """
CRITICAL OUTPUT REQUIREMENTS:
- Output ONLY the final image prompt text
- DO NOT include any settings information in your output
- DO NOT append "Settings:" or list the camera/lighting/etc values
- Incorporate settings naturally INTO the description
- Follow platform format exactly
- Use appropriate length for platform
- Start generating NOW (no preamble, no explanations)

Example of CORRECT output:
"masterpiece, best quality, detailed portrait of a woman with flowing hair, 
golden hour sunlight, shot from low angle, dramatic composition..."

Example of WRONG output (DO NOT DO THIS):
"...flowing hair in golden hour sunlight | Settings: camera angle: low angle..."
"""
        
        return prompt
    
    def _build_user_prompt(
        self,
        text_prompt: str,
        settings: Dict,
        platform: str,
        prompt_context: str,
        reference_guidance: str,
        creative_brainstorm: Optional[str],
        reference_captions: Optional[List[Tuple[str, str]]] = None
    ) -> str:
        """Build user prompt for LLM"""

        context_labels = {
            "expand_short_prompt": "Compressed idea to expand",
            "finish_opening_line": "Prompt opening line",
            "prompt_from_item_list": "Checklist of required elements",
            "modify_reference_image": "Modify references",
            "enhance_reference_image": "Expand upon references",
            # Legacy mappings for backward compatibility
            "abbreviated_prompt": "Compressed idea to expand",
            "prompt_seed": "Prompt opening line",
            "item_list": "Checklist of required elements",
            "reference_modification": "Modify references",
            "reference_expansion": "Expand upon references"
        }

        header = context_labels.get(prompt_context, "Base prompt")
        parts = [f"{header}: {text_prompt}"]

        parts.append(
            f'MANDATORY SUBJECT ANCHOR: The final description must clearly feature "{text_prompt}" without omission or substitution.'
        )

        if reference_guidance:
            parts.append(
                "REFERENCE DIRECTIVES (MANDATORY):\n"
                f"{reference_guidance}\n\n"
                "MANDATORY ACTION: integrate each reference block and focus note above into the final prompt exactly once,"
                " preserving every major subject and environmental clue from the captions."
            )

        if reference_captions:
            caption_lines = [
                "REFERENCE CAPTIONS (VERBATIM):"
            ]
            for label, caption in reference_captions:
                caption_lines.append(f"{label}: {caption}")
            caption_lines.append(
                "MANDATORY: Maintain the core subjects, actions, objects, and environmental details expressed in these captions."
            )
            parts.append("\n".join(caption_lines))

        # Add explicit settings inline - NOT appended to final output
        explicit_settings = []
        for key, value in settings.items():
            if not isinstance(value, str):
                continue
            lowered = value.lower()
            if "auto" in lowered or "none" in lowered:
                continue
            if key in {"prompt_context", "length_mode", "detail_mode"}:
                continue
            display_key = key.replace('_', ' ')
            explicit_settings.append(f"{display_key}: {value}")

        if explicit_settings:
            parts.append("Settings to weave into the prompt: " + "; ".join(explicit_settings))

        if creative_brainstorm:
            parts.append(creative_brainstorm)

        return "\n\n".join(parts)
    
    def _parse_llm_response(self, response: str, platform: str) -> str:
        """Clean and parse LLM response"""
        
        cleaned = response.strip()
        
        # Remove common artifacts
        artifacts = [
            "here is the prompt:", "here's the prompt:", "here is:", "here's:",
            "prompt:", "final prompt:", "output:", "result:",
            "generated prompt:", "enhanced prompt:"
        ]
        
        cleaned_lower = cleaned.lower()
        for artifact in artifacts:
            if cleaned_lower.startswith(artifact):
                cleaned = cleaned[len(artifact):].strip()
                cleaned_lower = cleaned.lower()
        
        # Remove markdown code blocks
        if cleaned.startswith("```"):
            lines = cleaned.split('\n')
            if len(lines) > 2:
                cleaned = '\n'.join(lines[1:-1])
            cleaned = cleaned.strip()
        
        # Remove quotes if entire prompt is quoted
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        if cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        
        # Remove any "| Settings:" or similar trailing settings info
        import re
        # Pattern to match | Settings: ... or | settings: ... at the end
        cleaned = re.sub(r'\s*\|\s*[Ss]ettings:.*$', '', cleaned)
        # Also catch standalone Settings: at the end
        cleaned = re.sub(r'\s*[Ss]ettings:.*$', '', cleaned)
        # Remove any trailing pipe symbols
        cleaned = cleaned.rstrip('|').strip()
        
        return cleaned.strip()
    
    def _add_keywords(self, prompt: str, keywords: List[str], platform: str) -> str:
        """Add custom keywords in platform-appropriate format"""
        
        if not keywords:
            return prompt
        
        # Check which keywords are already present
        prompt_lower = prompt.lower()
        missing_keywords = [kw for kw in keywords if kw.lower() not in prompt_lower]
        
        if not missing_keywords:
            return prompt
        
        # Add missing keywords
        platform_config = get_platform_config(platform)
        
        if platform in ["illustrious"]:
            # Illustrious uses tag format with underscores
            formatted_kw = [kw.replace(" ", "_") for kw in missing_keywords]
            return f"{prompt}, {', '.join(formatted_kw)}"
        else:
            # Natural language (including Pony after score tags)
            return f"{prompt}, {', '.join(missing_keywords)}"
    
    def _add_platform_requirements(self, prompt: str, platform: str) -> str:
        """Add platform-specific required tokens if missing"""
        
        platform_config = get_platform_config(platform)
        required = platform_config.get("required_positive", [])
        
        if not required:
            return prompt
        
        # Check if required tokens are present
        prompt_lower = prompt.lower()
        missing = [token for token in required if token.lower() not in prompt_lower]
        
        if missing:
            # Add at the beginning for these platforms
            if platform in ["pony", "illustrious"]:
                return f"{', '.join(missing)}, {prompt}"
        
        return prompt
    
    def _format_choice_label(self, text: Optional[str]) -> str:
        """Human-friendly capitalization for option labels."""
        if not text:
            return ""

        cleaned = text.replace('_', ' ').strip()
        if not cleaned:
            return ""

        words = []
        for word in cleaned.split():
            upper = word.upper()
            if upper in {"POV", "OTS", "HDR", "SDXL"}:
                words.append(upper)
            elif any(char.isdigit() for char in word):
                words.append(word.upper())
            else:
                words.append(word.capitalize())

        result = " ".join(words)
        result = result.replace("'S", "'s").replace("’S", "’s")
        result = result.replace(" - ", "-")
        return result

    def _format_setting_value(
        self,
        key: str,
        settings: Dict[str, str],
        sources: Dict[str, Dict[str, str]],
        actuals: Dict[str, str]
    ) -> Optional[str]:
        """Produce a descriptive string for a setting using origin metadata."""

        source = sources.get(key, {})
        mode = source.get("mode")
        stored_value = source.get("value") or settings.get(key)
        actual_value = actuals.get(key)

        if mode == "llm":
            if actual_value:
                return f"LLM chose {self._format_choice_label(actual_value)}"
            return "LLM will decide during prompt generation"

        if mode == "random":
            label = self._format_choice_label(stored_value)
            return f"Randomized → {label}" if label else "Randomized"

        if mode == "auto":
            label = self._format_choice_label(stored_value)
            return f"Auto default → {label}" if label else "Auto-resolved"

        if mode == "platform":
            return f"{stored_value} (platform default)"

        if mode == "none":
            return "Not specified"

        if stored_value:
            return self._format_choice_label(stored_value)

        if actual_value:
            return self._format_choice_label(actual_value)

        return None

    def _infer_setting_mentions(self, prompt: str) -> Dict[str, str]:
        """Scan the enhanced prompt to detect explicit mentions of key settings."""

        normalized = prompt.lower().replace("’", "'")
        normalized_alt = normalized.replace('-', ' ')
        search_texts = [normalized, normalized_alt]

        results: Dict[str, str] = {}

        search_map: Dict[str, List[str]] = {
            "camera_angle": self.camera_angles,
            "composition": self.composition_styles,
            "lighting_source": self.lighting_sources,
            "lighting_quality": self.lighting_quality,
            "time_of_day": self.times_of_day,
            "weather": self.weather_conditions,
            "art_style": [style for style in [
                "photorealistic", "digital art", "oil painting", "watercolor",
                "anime", "manga", "sketch", "pencil drawing", "3d render",
                "illustration", "concept art", "impressionist", "abstract",
                "pixel art", "low poly", "papercraft", "isometric"
            ]],
            "genre_style": self.genre_styles,
            "color_mood": [
                "vibrant", "muted", "monochrome", "warm tones", "cool tones",
                "pastel", "high contrast", "desaturated", "neon", "earth tones"
            ],
            "subject_framing": self.subject_framings,
            "subject_pose": self.subject_poses
        }

        alias_map: Dict[Tuple[str, str], List[str]] = {
            ("camera_angle", "point of view"): ["pov", "pov shot", "point-of-view"],
            ("camera_angle", "over the shoulder"): ["ots", "over-the-shoulder"],
            ("camera_angle", "bird's eye view"): ["birds eye view", "birdseye view", "bird-eye view"],
            ("camera_angle", "worm's eye view"): ["worms eye view", "worms-eye view"],
            ("subject_framing", "extreme close-up"): ["extreme closeup"],
            ("subject_framing", "medium close-up"): ["medium closeup"],
            ("subject_pose", "lying down"): ["lying-down"],
            ("color_mood", "warm tones"): ["warm-toned", "warm lighting"],
            ("color_mood", "cool tones"): ["cool-toned", "cool lighting"],
            ("color_mood", "high contrast"): ["high-contrast"],
            ("art_style", "3d render"): ["3d-render", "3d rendering"]
        }

        for key, options in search_map.items():
            if key in results:
                continue
            for option in options:
                option_lower = option.lower()
                if any(option_lower in text for text in search_texts):
                    results[key] = option
                    break
                alias_key = (key, option_lower)
                aliases = alias_map.get(alias_key, [])
                if any(alias.lower() in text for text in search_texts for alias in aliases):
                    results[key] = option
                    break

        return results
    
    def _format_settings_display(
        self,
        settings: Dict[str, str],
        platform_config: Dict[str, Any],
        reference_notes: List[str],
        context: Dict[str, Any]
    ) -> str:
        """Format settings for display with origin tracking and detected selections."""

        sources: Dict[str, Dict[str, str]] = context.get("setting_sources", {}) or {}
        actuals: Dict[str, str] = context.get("actual_selections", {}) or {}
        ref_meta: Dict[str, Any] = context.get("reference_meta", {}) or {}
        main_llm_success: bool = context.get("main_llm_success", True)
        main_llm_error: str = context.get("main_llm_error", "")
        ref_count: int = context.get("reference_image_count", 0)
        quality_emphasis_active: bool = bool(context.get("quality_emphasis", False))
        ref_warnings: List[str] = context.get("reference_warnings", []) or []
        vision_context: Dict[str, Any] = context.get("vision", {}) or {}

        lines = [
            "=" * 60,
            "TEXT-TO-IMAGE PROMPT ENHANCEMENT",
            "=" * 60,
            f"\nTarget Platform: {platform_config['name']}",
            f"Prompting Style: {platform_config['prompt_style']}",
            f"Optimal Length: {platform_config['optimal_length']}"
        ]

        lines.append("\nLLM CALL SUMMARY:")
        if main_llm_success:
            lines.append("  - Main prompt LLM: responded")
        else:
            snippet = (main_llm_error or "unknown error").splitlines()[0][:120]
            snippet = snippet.replace('|', '/').strip()
            lines.append(f"  - Main prompt LLM: FAILED ({snippet or 'no details'})")

        analysis_method = ref_meta.get("analysis_method", "none")
        ref_queries = ref_meta.get("llm_queries", 0)
        ref_successes = ref_meta.get("llm_successes", 0)
        if ref_count:
            if ref_queries:
                lines.append(
                    f"  - Reference LLM: {ref_successes}/{ref_queries} responses ({analysis_method})"
                )
            else:
                lines.append(f"  - Reference LLM: not invoked ({analysis_method})")
        else:
            lines.append("  - Reference LLM: no reference images")

        lines.append(f"  - References sent: {ref_count}")
        if ref_count:
            lines.append(f"  - Reference guidance applied: {'yes' if context.get('reference_guidance_used') else 'no'}")
        directive_labels = ref_meta.get("directive_labels") or []
        if directive_labels:
            lines.append(f"  - Reference directives: {', '.join(directive_labels)}")
        lines.append(f"  - Quality emphasis: {'enabled' if quality_emphasis_active else 'disabled'}")

        if vision_context:
            requested_backend = (vision_context.get("requested_backend") or "auto").strip() or "auto"
            resolved_backend = (vision_context.get("resolved_backend") or "disabled").strip() or "disabled"
            resolved_model = vision_context.get("resolved_model") or "auto"
            caption_enabled = bool(vision_context.get("caption_enabled"))

            if resolved_backend.startswith("inherit:"):
                inherit_source = resolved_backend.split(":", 1)[1]
                resolved_display = f"inherit ({inherit_source})"
            else:
                resolved_display = resolved_backend

            status_note = "enabled" if caption_enabled else "disabled"
            lines.append(
                f"  - Vision captioning: {status_note} (requested: {requested_backend}, resolved: {resolved_display})"
            )
            if caption_enabled and resolved_model:
                lines.append(f"    • Vision model: {resolved_model}")

        lines.append("\nSETTINGS APPLIED:")

        context_display = {
            "expand_short_prompt": "Abbreviated prompt (expand fully)",
            "finish_opening_line": "Prompt seed (continue logically)",
            "prompt_from_item_list": "Item list (merge into scene)",
            "modify_reference_image": "Modify reference traits",
            "enhance_reference_image": "Expand reference storytelling",
            # Legacy mappings for backward compatibility
            "abbreviated_prompt": "Abbreviated prompt (expand fully)",
            "prompt_seed": "Prompt seed (continue logically)",
            "item_list": "Item list (merge into scene)",
            "reference_modification": "Modify reference traits",
            "reference_expansion": "Expand reference storytelling"
        }

        ordered_keys = [
            "camera_angle", "composition", "lighting_source", "lighting_quality",
            "time_of_day", "historical_period", "weather",
            "art_style", "genre_style", "color_mood",
            "creative_randomness", "subject_framing", "subject_pose",
            "prompt_context", "length_mode", "detail_mode", "quality_emphasis"
        ]

        remaining_keys = [key for key in settings.keys() if key not in ordered_keys]
        display_keys = ordered_keys + remaining_keys

        for key in display_keys:
            if key not in settings:
                continue

            label = key.replace("_", " ").title()
            desc: Optional[str] = None

            if key == "prompt_context":
                mode = sources.get(key, {}).get("mode")
                if mode == "llm":
                    desc = "LLM interprets input role dynamically"
                else:
                    raw_value = settings.get(key, "")
                    desc = context_display.get(raw_value, self._format_choice_label(raw_value))

            elif key == "creative_randomness":
                desc = self._format_setting_value(key, settings, sources, actuals)
                raw_value = (settings.get(key, "") or "").lower()
                explanation = self.creative_randomness_modes.get(raw_value)
                if explanation:
                    pretty = self._format_choice_label(raw_value)
                    if desc:
                        desc = f"{desc} — {explanation}"
                    else:
                        desc = f"{pretty or raw_value} — {explanation}"

            elif key in {"length_mode", "detail_mode"}:
                desc = self._format_setting_value(key, settings, sources, actuals)

            elif key == "quality_emphasis":
                mode = sources.get(key, {}).get("mode")
                if mode == "platform":
                    origin = "platform default"
                elif mode:
                    origin = mode
                else:
                    origin = settings.get(key, "")
                desc = f"{'Enabled' if quality_emphasis_active else 'Disabled'} ({origin})"

            else:
                desc = self._format_setting_value(key, settings, sources, actuals)

            if not desc:
                desc = settings.get(key)

            if desc:
                lines.append(f"  - {label}: {desc}")

        if ref_count:
            lines.append("\nREFERENCE IMAGE NOTES:")
            guardrail = ref_meta.get("guardrail")
            if guardrail:
                lines.append(f"  • Guardrail: {guardrail}")
            for note in reference_notes:
                lines.append(f"  • {note}")
            for warning in ref_warnings:
                lines.append(f"  • Warning: {warning}")
            caption_sources = ref_meta.get("vision_caption_sources") or []
            backends_used = ref_meta.get("vision_backends_used") or []
            models_used = ref_meta.get("vision_models_used") or []
            if backends_used:
                lines.append(f"  • Vision backends used: {', '.join(backends_used)}")
            if models_used:
                lines.append(f"  • Vision models used: {', '.join(model for model in models_used if model) or 'n/a'}")
            if caption_sources:
                lines.append(f"  • Vision caption sources: {', '.join(caption_sources)}")
        elif ref_warnings:
            lines.append("\nREFERENCE WARNINGS:")
            for warning in ref_warnings:
                lines.append(f"  • {warning}")

        seed_info = context.get("random_seed") or {}
        seed_value = seed_info.get("value")
        if seed_value is not None:
            mode_label = seed_info.get("mode", "manual")
            lines.append(f"\nRandom Seed Used: {seed_value} ({mode_label})")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)
