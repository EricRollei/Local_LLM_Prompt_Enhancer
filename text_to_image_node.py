"""
Text-to-Image Prompt Enhancer Node
Advanced multi-platform prompt enhancement for image generation
Supports: SDXL, Pony, Illustrious, Flux, Chroma, Qwen-Image, Qwen-Edit, Wan-Image
"""

import torch
import numpy as np
from PIL import Image
import io
import base64
import random
from typing import Tuple, Optional, Dict, List
from .llm_backend import LLMBackend
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
            "fantasy", "noir", "cyberpunk"
        ]
        
        self.subject_framings = [
            "extreme close-up", "close-up", "medium close-up",
            "medium shot", "medium wide", "wide shot",
            "full body", "cowboy shot", "bust shot",
            "head and shoulders", "three-quarter"
        ]
        
        self.subject_poses = [
            "standing", "sitting", "lying down", "kneeling", "crouching",
            "action pose", "portrait pose", "dynamic", "static",
            "asymmetric", "contrapposto", "relaxed", "tense"
        ]
    
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
                
                # Platform selection
                "target_platform": ([
                    "flux",
                    "sd_xl",
                    "pony",
                    "illustrious",
                    "chroma",
                    "qwen_image",
                    "qwen_image_edit",
                    "wan_image"
                ], {
                    "default": "flux"
                }),
                
                # LLM settings
                "llm_backend": ([
                    "lm_studio",
                    "ollama"
                ], {
                    "default": "lm_studio"
                }),
                
                "model_name": ("STRING", {
                    "default": "llama3",
                    "multiline": False
                }),
                
                "api_endpoint": ("STRING", {
                    "default": "http://localhost:1234/v1",
                    "multiline": False
                }),
                
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.1,
                    "max": 2.0,
                    "step": 0.1
                }),
                
                # Camera & Composition
                "camera_angle": ([
                    "auto", "random", "none",
                    "eye level", "low angle", "high angle", "dutch angle",
                    "bird's eye view", "worm's eye view", "over the shoulder",
                    "point of view", "extreme close-up angle"
                ], {
                    "default": "auto"
                }),
                
                "composition": ([
                    "auto", "random", "none",
                    "rule of thirds", "centered", "symmetrical", "asymmetrical",
                    "golden ratio", "leading lines", "frame within frame",
                    "negative space", "balanced", "dynamic diagonal"
                ], {
                    "default": "auto"
                }),
                
                # Lighting
                "lighting_source": ([
                    "auto", "random", "none",
                    "natural sunlight", "studio lighting", "golden hour sun",
                    "moonlight", "candlelight", "neon lights", "firelight",
                    "spotlight", "ambient lighting", "backlight", "rim lighting",
                    "window light", "street lights"
                ], {
                    "default": "auto"
                }),
                
                "lighting_quality": ([
                    "auto", "random", "none",
                    "soft diffused", "hard dramatic", "even balanced",
                    "high contrast", "low key", "high key", "chiaroscuro",
                    "volumetric", "atmospheric"
                ], {
                    "default": "auto"
                }),
                
                # Time & Weather
                "time_of_day": ([
                    "auto", "random", "none",
                    "dawn", "early morning", "mid-morning", "noon", "afternoon",
                    "golden hour", "dusk", "twilight", "night", "midnight", "blue hour"
                ], {
                    "default": "auto"
                }),
                
                "weather": ([
                    "auto", "random", "none",
                    "clear sky", "partly cloudy", "overcast", "misty", "foggy",
                    "rainy", "stormy", "snowy", "sunny", "hazy"
                ], {
                    "default": "auto"
                }),
                
                # Style & Quality
                "art_style": ([
                    "auto", "none",
                    "photorealistic", "digital art", "oil painting", "watercolor",
                    "anime", "manga", "sketch", "pencil drawing", "3D render",
                    "illustration", "concept art", "impressionist", "abstract",
                    "pixel art", "low poly", "papercraft", "isometric"
                ], {
                    "default": "auto"
                }),
                
                "genre_style": ([
                    "auto", "random", "none",
                    "surreal", "cinematic", "dramatic", "action", "humorous",
                    "indie", "horror", "scifi", "romantic", "x-rated", "pg",
                    "artistic", "documentary", "minimalist", "maximalist",
                    "vintage", "modern", "fantasy", "noir", "cyberpunk"
                ], {
                    "default": "auto"
                }),
                
                "color_mood": ([
                    "auto", "random", "none",
                    "vibrant", "muted", "monochrome", "warm tones", "cool tones",
                    "pastel", "high contrast", "desaturated", "neon", "earth tones"
                ], {
                    "default": "auto"
                }),
                
                "detail_level": ([
                    "auto",
                    "standard",
                    "highly detailed",
                    "intricate details",
                    "simplified",
                    "minimalist"
                ], {
                    "default": "auto"
                }),
                
                "prompt_length": ([
                    "auto",
                    "very_short",
                    "short",
                    "medium",
                    "long",
                    "very_long"
                ], {
                    "default": "auto"
                }),
                
                # Subject Controls
                "subject_framing": ([
                    "auto", "random", "none",
                    "extreme close-up", "close-up", "medium close-up",
                    "medium shot", "medium wide", "wide shot",
                    "full body", "cowboy shot", "bust shot",
                    "head and shoulders", "three-quarter"
                ], {
                    "default": "auto"
                }),
                
                "subject_pose": ([
                    "auto", "random", "none",
                    "standing", "sitting", "lying down", "kneeling", "crouching",
                    "action pose", "portrait pose", "dynamic", "static",
                    "asymmetric", "contrapposto", "relaxed", "tense",
                    "walking", "running", "jumping", "dancing"
                ], {
                    "default": "auto"
                }),
                
                "quality_emphasis": ("BOOLEAN", {
                    "default": True
                }),
                
                # Keywords
                "positive_keywords": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Additional keywords, LoRA triggers, specific details"
                }),
                
                "negative_keywords": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Things to avoid"
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
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "settings_used", "status")
    
    FUNCTION = "enhance_prompt"
    CATEGORY = "Eric Prompt Enhancers"
    OUTPUT_NODE = True
    
    def enhance_prompt(
        self,
        text_prompt: str,
        target_platform: str,
        llm_backend: str,
        model_name: str,
        api_endpoint: str,
        temperature: float,
        camera_angle: str,
        composition: str,
        lighting_source: str,
        lighting_quality: str,
        time_of_day: str,
        weather: str,
        art_style: str,
        genre_style: str,
        color_mood: str,
        detail_level: str,
        prompt_length: str,
        subject_framing: str,
        subject_pose: str,
        quality_emphasis: bool,
        positive_keywords: str,
        negative_keywords: str,
        save_to_file: bool,
        filename_base: str,
        reference_image_1: Optional[torch.Tensor] = None,
        reference_image_2: Optional[torch.Tensor] = None
    ) -> Tuple[str, str, str, str]:
        """Main processing function"""
        
        try:
            # STEP 0: Process alternations first (before LLM)
            text_prompt = self._process_alternations(text_prompt)
            
            # STEP 0.5: Protect emphasis syntax
            text_prompt = self._preserve_emphasis_syntax(text_prompt)
            
            # STEP 1: Process reference images if provided
            image_descriptions = []
            if reference_image_1 is not None:
                desc = self._get_simple_image_description(reference_image_1, "Reference 1")
                image_descriptions.append(desc)
            
            if reference_image_2 is not None:
                desc = self._get_simple_image_description(reference_image_2, "Reference 2")
                image_descriptions.append(desc)
            
            # STEP 2: Resolve random/auto options
            resolved_settings = self._resolve_settings(
                camera_angle, composition, lighting_source, lighting_quality,
                time_of_day, weather, art_style, genre_style, color_mood, 
                detail_level, prompt_length, subject_framing, subject_pose,
                target_platform
            )
            
            # STEP 3: Build enhancement prompt
            platform_config = get_platform_config(target_platform)
            system_prompt = self._build_system_prompt(
                platform_config, resolved_settings, quality_emphasis
            )
            
            user_prompt = self._build_user_prompt(
                text_prompt, image_descriptions, resolved_settings, target_platform
            )
            
            # STEP 4: Call LLM
            llm = LLMBackend(
                backend_type=llm_backend,
                endpoint=api_endpoint,
                model_name=model_name,
                temperature=temperature
            )
            
            response = llm.send_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=800
            )
            
            if not response["success"]:
                return (
                    text_prompt,
                    "",
                    str(resolved_settings),
                    f"❌ LLM Error: {response['error']}"
                )
            
            # STEP 5: Parse and format response
            enhanced_prompt = self._parse_llm_response(response["response"], target_platform)
            
            # STEP 5.5: Restore emphasis syntax that was protected
            enhanced_prompt = self._restore_emphasis_syntax(enhanced_prompt)
            
            # STEP 6: Add custom keywords
            pos_kw_list = parse_keywords(positive_keywords)
            if pos_kw_list:
                enhanced_prompt = self._add_keywords(enhanced_prompt, pos_kw_list, target_platform)
            
            # STEP 7: Add platform-specific required tokens
            enhanced_prompt = self._add_platform_requirements(enhanced_prompt, target_platform, quality_emphasis)
            
            # STEP 8: Generate negative prompt
            neg_kw_list = parse_keywords(negative_keywords)
            negative_prompt = get_negative_prompt_for_platform(target_platform, neg_kw_list)
            
            # STEP 9: Format settings display
            settings_display = self._format_settings_display(resolved_settings, platform_config)
            
            # STEP 10: Save if requested
            if save_to_file:
                metadata = {
                    "type": "text-to-image",
                    "platform": target_platform,
                    "platform_name": platform_config["name"],
                    "model": model_name,
                    "original_prompt": text_prompt,
                    "settings": resolved_settings
                }
                
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
            
            status = f"✅ Enhanced for {platform_config['name']} | {file_status}"
            
            return (
                enhanced_prompt,
                negative_prompt,
                settings_display,
                status
            )
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"ERROR in text-to-image enhancement: {error_detail}")
            return (
                text_prompt,
                "",
                "",
                f"❌ Error: {str(e)}"
            )
    
    def _get_simple_image_description(self, image: torch.Tensor, label: str) -> str:
        """Get description of reference image based on basic analysis"""
        try:
            # Convert tensor to numpy for analysis
            # ComfyUI images are typically [batch, height, width, channels] in range [0, 1]
            if isinstance(image, torch.Tensor):
                img_np = image.cpu().numpy()
                
                # Get first image if batch
                if len(img_np.shape) == 4:
                    img_np = img_np[0]
                
                # Get dimensions
                height, width = img_np.shape[:2]
                aspect_ratio = width / height if height > 0 else 1.0
                
                # Analyze colors (basic RGB analysis)
                mean_colors = img_np.mean(axis=(0, 1))
                brightness = mean_colors.mean()
                
                # Determine general characteristics
                orientation = "landscape" if aspect_ratio > 1.3 else "portrait" if aspect_ratio < 0.77 else "square"
                
                if brightness > 0.7:
                    tone = "bright"
                elif brightness > 0.4:
                    tone = "balanced"
                else:
                    tone = "dark"
                
                # Color dominance (simple heuristic)
                if len(mean_colors) >= 3:
                    r, g, b = mean_colors[0], mean_colors[1], mean_colors[2]
                    max_channel = max(r, g, b)
                    min_channel = min(r, g, b)
                    saturation = max_channel - min_channel
                    
                    if saturation < 0.1:
                        color_desc = "monochromatic or low saturation"
                    elif r > g and r > b:
                        color_desc = "warm tones, reddish hues"
                    elif b > r and b > g:
                        color_desc = "cool tones, bluish hues"
                    elif g > r and g > b:
                        color_desc = "greenish hues"
                    else:
                        color_desc = "balanced color palette"
                else:
                    color_desc = "grayscale"
                
                desc = f"{label}: {orientation} {width}x{height}, {tone} lighting, {color_desc}"
                return desc
                
        except Exception as e:
            print(f"Warning: Could not analyze reference image: {e}")
        
        return f"{label}: [Image provided as reference]"
    
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
        weather: str,
        art_style: str,
        genre_style: str,
        color_mood: str,
        detail_level: str,
        prompt_length: str,
        subject_framing: str,
        subject_pose: str,
        platform: str
    ) -> Dict[str, str]:
        """Resolve auto/random options to actual values"""
        
        resolved = {}
        
        # Camera angle
        if camera_angle == "random":
            resolved["camera_angle"] = random.choice(self.camera_angles)
        elif camera_angle not in ["auto", "none"]:
            resolved["camera_angle"] = camera_angle
        elif camera_angle == "auto":
            resolved["camera_angle"] = "auto (LLM decides)"
        
        # Composition
        if composition == "random":
            resolved["composition"] = random.choice(self.composition_styles)
        elif composition not in ["auto", "none"]:
            resolved["composition"] = composition
        elif composition == "auto":
            resolved["composition"] = "auto (LLM decides)"
        
        # Lighting source
        if lighting_source == "random":
            resolved["lighting_source"] = random.choice(self.lighting_sources)
        elif lighting_source not in ["auto", "none"]:
            resolved["lighting_source"] = lighting_source
        elif lighting_source == "auto":
            resolved["lighting_source"] = "auto (LLM decides)"
        
        # Lighting quality
        if lighting_quality == "random":
            resolved["lighting_quality"] = random.choice(self.lighting_quality)
        elif lighting_quality not in ["auto", "none"]:
            resolved["lighting_quality"] = lighting_quality
        elif lighting_quality == "auto":
            resolved["lighting_quality"] = "auto (LLM decides)"
        
        # Time of day
        if time_of_day == "random":
            resolved["time_of_day"] = random.choice(self.times_of_day)
        elif time_of_day not in ["auto", "none"]:
            resolved["time_of_day"] = time_of_day
        elif time_of_day == "auto":
            resolved["time_of_day"] = "auto (LLM decides)"
        
        # Weather
        if weather == "random":
            resolved["weather"] = random.choice(self.weather_conditions)
        elif weather not in ["auto", "none"]:
            resolved["weather"] = weather
        elif weather == "auto":
            resolved["weather"] = "auto (LLM decides)"
        
        # Art style
        if art_style not in ["auto", "none"]:
            resolved["art_style"] = art_style
        elif art_style == "auto":
            resolved["art_style"] = "auto (LLM decides)"
        
        # Color mood
        if color_mood == "random":
            resolved["color_mood"] = random.choice(["vibrant", "muted", "warm tones", "cool tones", "pastel", "high contrast"])
        elif color_mood not in ["auto", "none"]:
            resolved["color_mood"] = color_mood
        elif color_mood == "auto":
            resolved["color_mood"] = "auto (LLM decides)"
        
        # Detail level
        if detail_level != "auto":
            resolved["detail_level"] = detail_level
        else:
            resolved["detail_level"] = "auto (LLM decides)"
        
        # Genre style
        if genre_style == "random":
            resolved["genre_style"] = random.choice(self.genre_styles)
        elif genre_style not in ["auto", "none"]:
            resolved["genre_style"] = genre_style
        elif genre_style == "auto":
            resolved["genre_style"] = "auto (LLM decides)"
        
        # Prompt length
        if prompt_length != "auto":
            resolved["prompt_length"] = prompt_length
        else:
            resolved["prompt_length"] = "auto (based on platform)"
        
        # Subject framing
        if subject_framing == "random":
            resolved["subject_framing"] = random.choice(self.subject_framings)
        elif subject_framing not in ["auto", "none"]:
            resolved["subject_framing"] = subject_framing
        elif subject_framing == "auto":
            resolved["subject_framing"] = "auto (LLM decides)"
        
        # Subject pose
        if subject_pose == "random":
            resolved["subject_pose"] = random.choice(self.subject_poses)
        elif subject_pose not in ["auto", "none"]:
            resolved["subject_pose"] = subject_pose
        elif subject_pose == "auto":
            resolved["subject_pose"] = "auto (LLM decides)"
        
        return resolved
    
    def _build_system_prompt(
        self,
        platform_config: Dict,
        settings: Dict,
        quality_emphasis: bool
    ) -> str:
        """Build LLM system prompt with platform-specific instructions"""
        
        platform_name = platform_config["name"]
        platform = platform_config.get("prompt_style", "natural")
        
        prompt = f"""You are an expert prompt engineer for {platform_name} image generation.

CRITICAL OUTPUT RULES:
1. Output ONLY the final prompt text - no labels, explanations, or meta-commentary
2. Do NOT include phrases like "Here is...", "Prompt:", etc.
3. Start directly with the image description
4. Follow the platform-specific format precisely

TARGET PLATFORM: {platform_name}
Description: {platform_config['description']}
Prompting Style: {platform_config['prompt_style']}
Optimal Length: {platform_config['optimal_length']}

"""
        
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
        
        # Handle prompt length guidance
        prompt_length_guide = settings.get("prompt_length", "auto")
        if prompt_length_guide and "auto" not in prompt_length_guide:
            length_map = {
                "very_short": "20-40 tokens",
                "short": "40-80 tokens",
                "medium": "80-150 tokens",
                "long": "150-250 tokens",
                "very_long": "250-400 tokens"
            }
            target_length = length_map.get(prompt_length_guide, platform_config['optimal_length'])
            prompt += f"TARGET LENGTH: {target_length}\n\n"
        
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
                "cyberpunk": "neon, futuristic dystopia, tech, gritty urban"
            }
            style_desc = genre_guidance.get(genre, genre)
            prompt += f"STYLE/GENRE: {genre} - Infuse the prompt with {style_desc}\n\n"
        
        for key, value in settings.items():
            if key in ["prompt_length", "genre_style"]:  # Already handled above
                continue
            if value and "none" not in value.lower() and "auto" not in value.lower():
                label = key.replace("_", " ").title()
                prompt += f"- {label}: {value}\n"
        
        # Platform-specific format instructions
        if "pony" in platform_name.lower():
            prompt += """
PONY-SPECIFIC INSTRUCTIONS:
- START with: score_9, score_8_up, score_7_up
- Use danbooru tag format (underscores, not spaces)
- Tags should be comma-separated
- Quality tags at beginning
- Character/subject descriptions in tag format
- Example: score_9, score_8_up, score_7_up, 1girl, long_hair, blue_eyes, etc.
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
        image_descriptions: List[str],
        settings: Dict,
        platform: str
    ) -> str:
        """Build user prompt for LLM"""
        
        parts = [f"Base prompt: {text_prompt}"]
        
        # Emphasize reference images if provided
        if image_descriptions:
            ref_text = "Reference images provided - Use these characteristics to inform the enhanced prompt:\n"
            for desc in image_descriptions:
                ref_text += f"  - {desc}\n"
            ref_text += "Incorporate the visual characteristics (composition, lighting, color tones, mood) from these reference images into your enhancement."
            parts.append(ref_text)
        
        # Add explicit settings inline - NOT appended to final output
        explicit_settings = []
        for key, value in settings.items():
            if "auto" not in value.lower() and "none" not in value.lower():
                explicit_settings.append(f"{key.replace('_', ' ')}: {value}")
        
        if explicit_settings:
            parts.append(f"Required settings to incorporate: {'; '.join(explicit_settings)}")
        
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
        
        if platform in ["pony", "illustrious"]:
            # Tag format with underscores
            formatted_kw = [kw.replace(" ", "_") for kw in missing_keywords]
            return f"{prompt}, {', '.join(formatted_kw)}"
        else:
            # Natural language
            return f"{prompt}, {', '.join(missing_keywords)}"
    
    def _add_platform_requirements(self, prompt: str, platform: str, quality: bool) -> str:
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
    
    def _format_settings_display(self, settings: Dict, platform_config: Dict) -> str:
        """Format settings for display"""
        
        lines = [
            "=" * 60,
            "TEXT-TO-IMAGE PROMPT ENHANCEMENT",
            "=" * 60,
            f"\nTarget Platform: {platform_config['name']}",
            f"Prompting Style: {platform_config['prompt_style']}",
            f"Optimal Length: {platform_config['optimal_length']}",
            "\nSETTINGS APPLIED:"
        ]
        
        for key, value in settings.items():
            label = key.replace("_", " ").title()
            lines.append(f"  - {label}: {value}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
