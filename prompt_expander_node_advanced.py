"""
Advanced AI Video Prompt Expander Node with Granular Aesthetic Controls
Provides dropdown menus for all Wan 2.2 elements
"""

import os
import re
import random
from typing import Tuple
from .llm_backend import LLMBackend
from .expansion_engine import PromptExpander
from .utils import (
    save_prompts_to_file,
    parse_keywords,
    format_breakdown,
    validate_positive_keywords
)


class AIVideoPromptExpanderAdvanced:
    """
    Advanced ComfyUI node with granular control over all Wan 2.2 aesthetic elements
    """
    
    def __init__(self):
        self.expander = PromptExpander()
        self.type = "prompt_expansion_advanced"
        self.output_dir = "output/video_prompts"
        self._emphasis_store = []  # Store for emphasis syntax preservation
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Core inputs
                "basic_prompt": ("STRING", {
                    "multiline": True,
                    "default": "A cat playing piano in a cozy room",
                    "tooltip": "Enter your prompt. Supports emphasis (keyword:1.5) and alternations {opt1|opt2}"
                }),
                
                # NEW: Operation mode
                "operation_mode": ([
                    "expand_from_idea",
                    "refine_existing",
                    "modify_style",
                    "add_details"
                ], {
                    "default": "expand_from_idea",
                    "tooltip": (
                        "expand_from_idea: Take a short concept and expand it fully\n"
                        "refine_existing: Polish and improve an existing prompt\n"
                        "modify_style: Change the style/aesthetic of existing prompt\n"
                        "add_details: Add more descriptive details to existing prompt"
                    )
                }),
                
                "preset": ([
                    "custom",
                    "cinematic", 
                    "surreal",
                    "action",
                    "stylized",
                    "noir",
                    "random"
                ], {
                    "default": "cinematic"
                }),
                
                "detail_level": ([
                    "concise",      # ~150-200 words
                    "moderate",     # ~250-350 words  
                    "detailed",     # ~400-500 words
                    "exhaustive"    # ~600-1000 words
                ], {
                    "default": "detailed",
                    "tooltip": (
                        "concise: Brief, essential details only\n"
                        "moderate: Good balance of detail\n"
                        "detailed: Rich, comprehensive description\n"
                        "exhaustive: Maximum detail for cinematic quality"
                    )
                }),
                
                "creativity_mode": ([
                    "conservative",
                    "balanced",
                    "creative",
                    "highly_creative"
                ], {
                    "default": "balanced",
                    "tooltip": (
                        "Conservative: Focused, predictable (temp 0.5)\n"
                        "Balanced: Good variety (temp 0.7)\n"
                        "Creative: More experimental (temp 0.85)\n"
                        "Highly Creative: Maximum variety (temp 1.0)"
                    )
                }),
                
                # === REFERENCE IMAGE CONTROLS ===
                "reference_mode": ([
                    "recreate_exact",
                    "subject_only",
                    "style_only",
                    "color_palette_only",
                    "action_only",
                    "character_remix",
                    "reimagine"
                ], {
                    "default": "recreate_exact",
                    "tooltip": (
                        "recreate_exact: Use image as exact reference for character, costume, and setting\n"
                        "subject_only: Keep character identity, ignore background and lighting\n"
                        "style_only: Match aesthetic and mood, create new subject\n"
                        "color_palette_only: Extract and apply color scheme only\n"
                        "action_only: Use the pose/action, change everything else\n"
                        "character_remix: Keep character, place in new scenario\n"
                        "reimagine: Loosely inspired by image, creative reinterpretation"
                    )
                }),
                
                # === SHOT STRUCTURE CONTROLS ===
                "shot_structure": ([
                    "continuous_paragraph",
                    "2_shot_structure",
                    "3_shot_structure",
                    "4_shot_structure"
                ], {
                    "default": "3_shot_structure",
                    "tooltip": (
                        "continuous_paragraph: Single flowing description (no shot breaks)\n"
                        "2_shot_structure: Two distinct shots (Opening + Final Reveal)\n"
                        "3_shot_structure: Three shots (Setup, Development, Finale) [Recommended]\n"
                        "4_shot_structure: Four shots (Intro, Build, Climax, Resolution)"
                    )
                }),
                
                # === LIGHTING CONTROLS ===
                "light_source": ([
                    "auto",
                    "none",
                    "sunny lighting",
                    "artificial lighting",
                    "moonlighting",
                    "practical lighting",
                    "firelighting",
                    "fluorescent lighting",
                    "overcast lighting",
                    "mixed lighting",
                    "ambient lighting",
                    "reflected lighting",
                    "softbox lighting",
                    "camera flash",
                    "neon lights",
                    "striplight",
                    "computer screen glow",
                    "flashlight",
                    "candlelight",
                    "spotlight"
                ], {
                    "default": "auto",
                    "tooltip": "Primary source of illumination in the scene"
                }),
                
                "lighting_quality": ([
                    "auto",
                    "none",
                    "soft lighting",
                    "hard lighting",
                    "top lighting",
                    "side lighting",
                    "edge lighting",
                    "rim lighting",
                    "underlighting",
                    "silhouette lighting",
                    "backlighting",
                    "low contrast lighting",
                    "high contrast lighting",
                    "spotlight effect",
                    "dappled lighting",
                    "cinematic lighting",
                    "diffused lighting",
                    "dramatic lighting"
                ], {
                    "default": "auto",
                    "tooltip": "Quality and style of lighting"
                }),
                
                "time_of_day": ([
                    "auto",
                    "none",
                    "sunrise time",
                    "dawn time",
                    "daylight",
                    "daytime",
                    "dusk time",
                    "sunset time",
                    "night time"
                ], {
                    "default": "auto"
                }),
                
                # === CAMERA/SHOT CONTROLS ===
                "shot_size": ([
                    "auto",
                    "none",
                    "extreme close-up shot",
                    "close-up shot",
                    "medium close-up shot",
                    "medium shot",
                    "medium wide shot",
                    "wide shot",
                    "extreme wide shot",
                    "establishing shot"
                ], {
                    "default": "auto"
                }),
                
                "composition": ([
                    "auto",
                    "none",
                    "center composition",
                    "balanced composition",
                    "left-weighted composition",
                    "right-weighted composition",
                    "symmetrical composition",
                    "short-side composition",
                    "rule of thirds"
                ], {
                    "default": "auto"
                }),
                
                "lens": ([
                    "auto",
                    "none",
                    "wide-angle lens",
                    "medium lens",
                    "long-focus lens",
                    "telephoto lens",
                    "fisheye lens"
                ], {
                    "default": "auto"
                }),
                
                "camera_angle": ([
                    "auto",
                    "none",
                    "eye-level shot",
                    "high angle shot",
                    "low angle shot",
                    "dutch angle shot",
                    "aerial shot",
                    "bird's eye view",
                    "over-the-shoulder shot",
                    "top-down shot",
                    "first-person POV",
                    "profile close-up"
                ], {
                    "default": "auto"
                }),
                
                "camera_movement": ([
                    "auto",
                    "none",
                    "static shot",
                    "locked-off shot",
                    "camera pushes in",
                    "dolly in",
                    "camera pulls back",
                    "dolly out",
                    "camera pans right",
                    "camera pans left",
                    "camera tilts up",
                    "camera tilts down",
                    "tracking shot",
                    "arc shot",
                    "crane shot",
                    "camera cranes up",
                    "camera cranes down",
                    "handheld camera",
                    "steadicam",
                    "compound move",
                    "whip pan",
                    "camera orbits around subject",
                    "smooth glide",
                    "crash zoom in"
                ], {
                    "default": "auto",
                    "tooltip": "How the camera moves through the scene (Wan 2.2 optimized)"
                }),
                
                # === COLOR/STYLE CONTROLS ===
                "color_tone": ([
                    "auto",
                    "none",
                    "warm colors",
                    "cool colors",
                    "saturated colors",
                    "desaturated colors",
                    "monochromatic",
                    "black and white"
                ], {
                    "default": "auto"
                }),
                
                "art_style": ([
                    "auto",
                    "none",
                    "Picasso style",
                    "Van Gogh style",
                    "Monet style",
                    "Salvador Dali style",
                    "Banksy style",
                    "Andy Warhol style",
                    "Rembrandt style",
                    "Caravaggio style",
                    "Studio Ghibli style",
                    "Tim Burton style",
                    "Wes Anderson style",
                    "Pixar style",
                    "Norman Rockwell style",
                    "Edward Hopper style",
                    "Renaissance style",
                    "Baroque style",
                    "Art Nouveau style",
                    "Expressionist style",
                    "Impressionist style",
                    "Surrealist style",
                    "Cubist style",
                    "Pop Art style"
                ], {
                    "default": "auto",
                    "tooltip": "Apply the distinctive style of famous artists or art movements"
                }),
                
                "scene_detail": ([
                    "auto",
                    "none",
                    "simple scene",
                    "clean scene",
                    "detailed scene",
                    "cluttered scene",
                    "intricate detail",
                    "minimalist",
                    "maximalist"
                ], {
                    "default": "auto",
                    "tooltip": "Level of detail and complexity in the scene composition"
                }),
                
                "visual_style": ([
                    "auto",
                    "none",
                    "photorealistic",
                    "cinematic",
                    "3D cartoon style",
                    "2D anime style",
                    "pixel art style",
                    "claymation style",
                    "puppet animation",
                    "felt style",
                    "watercolor painting",
                    "oil painting style",
                    "pencil sketch",
                    "comic book style",
                    "line drawing"
                ], {
                    "default": "auto"
                }),
                
                "visual_effect": ([
                    "auto",
                    "none",
                    "tilt-shift photography",
                    "time-lapse",
                    "slow motion",
                    "motion blur",
                    "depth of field",
                    "bokeh",
                    "lens flare",
                    "film grain",
                    "vignette"
                ], {
                    "default": "auto"
                }),
                
                # === MOTION/EMOTION CONTROLS ===
                "character_emotion": ([
                    "auto",
                    "none",
                    "angry",
                    "fearful",
                    "happy",
                    "sad",
                    "surprised",
                    "confused",
                    "determined",
                    "thoughtful",
                    "pensive",
                    "excited",
                    "calm",
                    "anxious"
                ], {
                    "default": "auto"
                }),
                
                # LLM Configuration
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
                        "qwen3_vl: Leave default, or specify custom model path like 'local:A:\\path\\to\\model'"
                    )
                }),
                
                # Keywords
                "positive_keywords": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "lora_trigger, keyword1, keyword2"
                }),
                
                "negative_keywords": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "unwanted_term1, unwanted_term2"
                }),
                
                # Output options
                "num_variations": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 3,
                    "step": 1
                }),
                
                "save_to_file": ("BOOLEAN", {
                    "default": False
                }),
                
                "filename_base": ("STRING", {
                    "default": "video_prompt_advanced",
                    "multiline": False
                })
            },
            "optional": {
                # Optional image/video reference for image-to-video workflows
                "reference_image": ("IMAGE", {
                    "tooltip": "Optional: Provide an image to analyze and incorporate into the prompt using Qwen3-VL"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "positive_prompt_1",
        "positive_prompt_2", 
        "positive_prompt_3",
        "negative_prompt",
        "breakdown",
        "status",
        "vision_caption"
    )
    
    FUNCTION = "expand_prompt"
    CATEGORY = "Eric Prompt Enhancers"
    OUTPUT_NODE = True
    
    def expand_prompt(
        self,
        basic_prompt: str,
        operation_mode: str,
        preset: str,
        detail_level: str,
        creativity_mode: str,
        reference_mode: str,
        shot_structure: str,
        light_source: str,
        lighting_quality: str,
        time_of_day: str,
        shot_size: str,
        composition: str,
        lens: str,
        camera_angle: str,
        camera_movement: str,
        color_tone: str,
        art_style: str,
        scene_detail: str,
        visual_style: str,
        visual_effect: str,
        character_emotion: str,
        llm_backend: str,
        api_endpoint: str,
        positive_keywords: str,
        negative_keywords: str,
        num_variations: int,
        save_to_file: bool,
        filename_base: str,
        reference_image=None  # Optional image input
    ) -> Tuple[str, str, str, str, str, str, str]:
        """
        Main processing function with aesthetic controls
        """
        
        try:
            # Map creativity mode to temperature
            temperature_map = {
                "conservative": 0.5,
                "balanced": 0.7,
                "creative": 0.85,
                "highly_creative": 1.0
            }
            temperature = temperature_map.get(creativity_mode, 0.7)
            
            # Process alternations first (before LLM)
            basic_prompt = self._process_alternations(basic_prompt)
            
            # Preserve emphasis syntax before LLM processing
            basic_prompt = self._preserve_emphasis_syntax(basic_prompt)
            
            # === PASS 1: Vision Analysis (if image provided) ===
            vision_caption = ""
            mode = "text-to-video"  # Default
            
            if reference_image is not None:
                try:
                    print(f"[Advanced Node] PASS 1: Analyzing reference image with Qwen3-VL...")
                    
                    # Get comprehensive image caption (no mode filtering yet)
                    vision_caption = self._process_reference_image(reference_image)
                    
                    if vision_caption:
                        mode = "image-to-video"
                        print(f"[Advanced Node] ✓ Vision analysis complete: {len(vision_caption)} chars")
                        print(f"[Advanced Node] Caption preview: {vision_caption[:200]}...")
                    else:
                        print(f"[Advanced Node] ⚠ Vision analysis returned empty - continuing without image context")
                        
                except Exception as e:
                    print(f"[Advanced Node] ⚠ Warning: Could not process image: {e}")
                    print(f"[Advanced Node] Continuing with text-only mode...")
                    # Continue without image context - graceful degradation
            
            elif reference_mode != "recreate_exact":
                # User set a reference_mode but didn't attach image - warn but continue
                print(f"[Advanced Node] ⚠ Warning: reference_mode is '{reference_mode}' but no image attached")
                print(f"[Advanced Node] Continuing in text-only mode...")
            
            # Parse keywords
            pos_kw_list = parse_keywords(positive_keywords)
            neg_kw_list = parse_keywords(negative_keywords)
            
            # Gather aesthetic controls
            aesthetic_controls = self._gather_aesthetic_controls(
                light_source, lighting_quality, time_of_day,
                shot_size, composition, lens, camera_angle,
                camera_movement, color_tone, art_style, scene_detail,
                visual_style, visual_effect, character_emotion
            )
            
            # Initialize LLM backend (model_name auto-detected)
            llm = LLMBackend(
                backend_type=llm_backend,
                endpoint=api_endpoint,
                model_name=None,  # Auto-detect for all backends
                temperature=temperature
            )
            
            # Test connection
            conn_test = llm.test_connection()
            if not conn_test["success"]:
                error_msg = f"LLM Connection Failed: {conn_test['message']}"
                return (
                    basic_prompt,
                    "",
                    "",
                    "",
                    f"ERROR: {error_msg}",
                    f"❌ {error_msg}",
                    vision_caption if vision_caption else "No image provided"
                )
            
            # === PASS 2: Smart LLM Expansion ===
            print(f"[Advanced Node] PASS 2: Expanding prompt with LLM...")
            
            # Generate variations
            positive_prompts = []
            breakdowns = []
            
            for var_num in range(num_variations):
                # Build expansion prompts with:
                # - User's basic prompt
                # - Vision caption (if available)
                # - Reference mode instructions (how to apply vision caption)
                # - Aesthetic controls
                # - Creativity mode
                # - Shot structure
                system_prompt, user_prompt, breakdown_dict = self.expander.expand_prompt(
                    basic_prompt=basic_prompt,
                    preset=preset,
                    tier=detail_level,  # Map detail_level to tier
                    mode=mode,
                    positive_keywords=pos_kw_list,
                    variation_seed=var_num if num_variations > 1 else None,
                    aesthetic_controls=aesthetic_controls,
                    shot_structure=shot_structure,
                    creativity_mode=creativity_mode,
                    vision_caption=vision_caption,  # Pass 1 result
                    reference_mode=reference_mode   # How to apply vision caption
                )
                
                # Call LLM with longer max_tokens for detailed output
                response = llm.send_prompt(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=3000  # Increased for more detail
                )
                
                if not response["success"]:
                    error_msg = response["error"]
                    print(f"[Advanced Node] LLM expansion failed: {error_msg}")
                    print(f"[Advanced Node] Full response: {response}")
                    return (
                        basic_prompt,
                        "",
                        "",
                        "",
                        f"ERROR: {error_msg}",
                        f"❌ {error_msg}",
                        vision_caption if vision_caption else "No image provided"
                    )
                
                # Parse response
                parsed = self.expander.parse_llm_response(response["response"])
                enhanced_prompt = parsed["prompt"]
                
                # Restore emphasis syntax after LLM processing
                enhanced_prompt = self._restore_emphasis_syntax(enhanced_prompt)
                
                # Ensure positive keywords are included
                if pos_kw_list:
                    keywords_present, missing = validate_positive_keywords(pos_kw_list, enhanced_prompt)
                    if missing:
                        enhanced_prompt += f" {', '.join(missing)}"
                
                positive_prompts.append(enhanced_prompt)
                breakdowns.append(breakdown_dict)
            
            # Pad to 3 variations
            while len(positive_prompts) < 3:
                positive_prompts.append("")
            
            # Generate negative prompt with visual_style for Wan 2.2 optimization
            negative_prompt = self.expander.generate_negative_prompt(
                preset=preset,
                custom_negatives=neg_kw_list,
                mode=mode,
                visual_style=visual_style
            )
            
            # Format breakdown
            breakdown_text = self._format_advanced_breakdown(
                breakdowns, 
                basic_prompt, 
                aesthetic_controls
            )
            
            # Save to file if requested
            if save_to_file and positive_prompts[0]:
                metadata = {
                    "preset": preset,
                    "detail_level": detail_level,
                    "operation_mode": operation_mode,
                    "mode": mode,
                    "backend": llm_backend,
                    "model": llm.model_name or "auto-detected",
                    "creativity_mode": creativity_mode,
                    "temperature": temperature,
                    "variation_num": num_variations,
                    "original_prompt": basic_prompt,
                    "aesthetic_controls": aesthetic_controls,
                    "had_image_reference": reference_image is not None
                }
                
                save_result = save_prompts_to_file(
                    positive_prompt=positive_prompts[0],
                    negative_prompt=negative_prompt,
                    breakdown=breakdown_text,
                    metadata=metadata,
                    filename_base=filename_base,
                    output_dir=self.output_dir
                )
                
                if save_result["success"]:
                    file_status = f"💾 Saved to: {save_result['filepath']}"
                else:
                    file_status = f"⚠️ Save failed: {save_result['error']}"
            else:
                file_status = "Not saved"
            
            # Build status with aesthetic controls summary
            controls_summary = self._summarize_controls(aesthetic_controls)
            mode_display = f"Mode: {mode}" + (" (with image)" if reference_image is not None else "")
            vision_status = f" | Vision: {len(vision_caption)} chars" if vision_caption else ""
            status = f"✅ Generated {num_variations} variation(s) | {operation_mode} | Detail: {detail_level} | Preset: {preset}\n{mode_display}{vision_status}\n{controls_summary}\n{file_status}"
            
            return (
                positive_prompts[0],
                positive_prompts[1],
                positive_prompts[2],
                negative_prompt,
                breakdown_text,
                status,
                vision_caption if vision_caption else "No image provided"
            )
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            # Try to preserve vision_caption if it exists
            caption_output = vision_caption if 'vision_caption' in locals() and vision_caption else "No image provided"
            return (
                basic_prompt if 'basic_prompt' in locals() else "",
                "",
                "",
                "",
                f"ERROR: {error_msg}",
                f"❌ {error_msg}",
                caption_output
            )
    
    def _gather_aesthetic_controls(
        self,
        light_source: str,
        lighting_quality: str,
        time_of_day: str,
        shot_size: str,
        composition: str,
        lens: str,
        camera_angle: str,
        camera_movement: str,
        color_tone: str,
        art_style: str,
        scene_detail: str,
        visual_style: str,
        visual_effect: str,
        character_emotion: str
    ) -> dict:
        """Gather all non-auto/none aesthetic controls"""
        
        controls = {}
        
        if light_source not in ["auto", "none"]:
            controls["light_source"] = light_source
        if lighting_quality not in ["auto", "none"]:
            controls["lighting_quality"] = lighting_quality
        if time_of_day not in ["auto", "none"]:
            controls["time_of_day"] = time_of_day
        if shot_size not in ["auto", "none"]:
            controls["shot_size"] = shot_size
        if composition not in ["auto", "none"]:
            controls["composition"] = composition
        if lens not in ["auto", "none"]:
            controls["lens"] = lens
        if camera_angle not in ["auto", "none"]:
            controls["camera_angle"] = camera_angle
        if camera_movement not in ["auto", "none"]:
            controls["camera_movement"] = camera_movement
        if color_tone not in ["auto", "none"]:
            controls["color_tone"] = color_tone
        if art_style not in ["auto", "none"]:
            controls["art_style"] = art_style
        if scene_detail not in ["auto", "none"]:
            controls["scene_detail"] = scene_detail
        if visual_style not in ["auto", "none"]:
            controls["visual_style"] = visual_style
        if visual_effect not in ["auto", "none"]:
            controls["visual_effect"] = visual_effect
        if character_emotion not in ["auto", "none"]:
            controls["character_emotion"] = character_emotion
        
        return controls
    
    def _summarize_controls(self, controls: dict) -> str:
        """Create summary of applied controls"""
        if not controls:
            return "Controls: All Auto"
        
        summary_parts = []
        for key, value in controls.items():
            label = key.replace("_", " ").title()
            summary_parts.append(f"{label}: {value}")
        
        return "Controls: " + ", ".join(summary_parts)
    
    def _format_advanced_breakdown(
        self, 
        breakdowns: list, 
        original: str,
        aesthetic_controls: dict
    ) -> str:
        """Format breakdown with aesthetic controls"""
        
        if not breakdowns:
            return "No breakdown available"
        
        lines = [
            "=" * 70,
            "ADVANCED PROMPT EXPANSION BREAKDOWN",
            "=" * 70,
            f"\nOriginal Input:\n{original}\n",
            f"\nDetected Tier: {breakdowns[0].get('detected_tier', 'N/A')}",
            f"Applied Preset: {breakdowns[0].get('applied_preset', 'N/A')}",
            f"Mode: {breakdowns[0].get('mode', 'N/A')}",
        ]
        
        if breakdowns[0].get('positive_keywords'):
            lines.append(f"Required Keywords: {', '.join(breakdowns[0]['positive_keywords'])}")
        
        if aesthetic_controls:
            lines.append("\nUser-Specified Aesthetic Controls:")
            for key, value in aesthetic_controls.items():
                label = key.replace("_", " ").title()
                lines.append(f"  - {label}: {value}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
    
    def _process_alternations(self, text: str) -> str:
        """
        Process alternation syntax {option1|option2|option3}
        Replaces with randomly chosen option
        """
        import re
        import random
        
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
    
    def _apply_operation_mode(self, prompt: str, operation_mode: str, image_context: str = "") -> str:
        """
        Apply operation mode to modify how the prompt is processed
        """
        if operation_mode == "expand_from_idea":
            # Default behavior - treat as short concept to expand
            return prompt + image_context
        
        elif operation_mode == "refine_existing":
            # Polish and improve without major changes
            instruction = "\n\n[INSTRUCTION: This is an existing prompt to refine. Keep the core content but improve clarity, flow, and descriptive quality. Don't dramatically change the concept or add major new elements.]"
            return prompt + instruction + image_context
        
        elif operation_mode == "modify_style":
            # Change aesthetic/style while keeping subject
            instruction = "\n\n[INSTRUCTION: This is an existing prompt. Keep the main subject and action, but modify the style, mood, cinematography, and aesthetic treatment according to the selected preset and controls.]"
            return prompt + instruction + image_context
        
        elif operation_mode == "add_details":
            # Add more descriptive elements
            instruction = "\n\n[INSTRUCTION: This is an existing prompt that needs more detail. Keep everything that's already there and add richer descriptions, atmospheric details, and sensory elements.]"
            return prompt + instruction + image_context
        
        return prompt + image_context
    
    def _build_reference_mode_instruction(self, reference_mode: str) -> str:
        """
        Build explicit instruction for how to use the reference image based on mode
        Follows Wan 2.2 image-to-video best practices
        """
        mode_instructions = {
            "recreate_exact": (
                "[REFERENCE MODE: RECREATE EXACT]\n"
                "Use the provided image as the exact character and costume reference. "
                "Keep the same face, hair, outfit, lighting, and overall aesthetic. "
                "Animate this character/scene without changing identity or appearance. "
                "Match the visual style, mood, and composition of the reference image."
            ),
            "subject_only": (
                "[REFERENCE MODE: SUBJECT ONLY]\n"
                "Preserve ONLY the subject's face, body identity, and core appearance from the reference image. "
                "Ignore the original background, lighting, and environment. "
                "Place this character in the new scene described by the prompt with new lighting and atmosphere. "
                "Keep character identity consistent but change everything else."
            ),
            "style_only": (
                "[REFERENCE MODE: STYLE TRANSFER]\n"
                "Match the lighting, color palette, visual aesthetic, and cinematic mood of the reference image. "
                "Create a completely new subject, character, and scene, but apply the same artistic style, "
                "color grading, lighting quality, and atmospheric treatment seen in the reference."
            ),
            "color_palette_only": (
                "[REFERENCE MODE: COLOR PALETTE ONLY]\n"
                "Extract and apply the dominant color scheme from the reference image. "
                "Use the same hues, saturation levels, and color relationships. "
                "Create an entirely new subject and scene, but maintain color harmony with the reference palette. "
                "Ignore composition, lighting style, and subject matter from the reference."
            ),
            "action_only": (
                "[REFERENCE MODE: ACTION/POSE ONLY]\n"
                "Recreate the pose, gesture, body language, and action/movement from the reference image. "
                "Change the character identity, environment, lighting, costume, and visual style completely. "
                "Keep only the physical positioning and motion dynamic from the reference."
            ),
            "character_remix": (
                "[REFERENCE MODE: CHARACTER REMIX]\n"
                "Keep the character's core identity (face, build, personality traits) from the reference image. "
                "Place them in a completely new scenario, environment, time period, or genre as described in the prompt. "
                "Change their outfit, the lighting, the setting, and the mood, but maintain character recognition. "
                "Adapt the character to fit the new context while preserving their essential identity."
            ),
            "reimagine": (
                "[REFERENCE MODE: REIMAGINE]\n"
                "Use the reference image as loose inspiration for a creative reinterpretation. "
                "Take the core concept, mood, or theme and reimagine it in a new way. "
                "Feel free to change subject, style, setting, and execution while maintaining thematic connection. "
                "This is the most creative mode - interpret the essence freely and combine with the prompt."
            )
        }
        
        return mode_instructions.get(reference_mode, mode_instructions["recreate_exact"])
    
    def _process_reference_image(self, image_tensor):
        """
        PASS 1: Comprehensive Vision Analysis using Qwen3-VL
        Get complete image description without reference_mode filtering.
        The LLM will apply reference_mode logic in Pass 2.
        
        Returns: Complete image caption string or None if error
        """
        try:
            import torch
            import numpy as np
            from PIL import Image
            from .qwen3_vl_backend import caption_with_qwen3_vl
            
            # Convert ComfyUI image format (B,H,W,C) to PIL Image
            if isinstance(image_tensor, torch.Tensor):
                # Take first image if batch
                img_np = image_tensor[0].cpu().numpy()
                # Convert from 0-1 float to 0-255 uint8
                img_np = (img_np * 255).astype(np.uint8)
                pil_image = Image.fromarray(img_np)
            else:
                return None
            
            # Comprehensive analysis prompt - get ALL details
            # Reference mode filtering will happen in Pass 2 (LLM expansion)
            comprehensive_prompt = """Analyze this image in complete detail for video prompt generation. Provide a thorough description covering:

**SUBJECT/CHARACTER:**
- Facial features, expression, age, gender, distinctive traits
- Hair style, length, color, texture
- Body type, build, posture, pose
- Clothing: style, color, material, accessories, condition
- Personality or mood visible in expression
- Any actions or gestures being performed

**ENVIRONMENT/SETTING:**
- Location type and specific details
- Background elements and spatial layout
- Environmental context and atmosphere
- Props, objects, or decorative elements
- Scale and depth of space

**LIGHTING & COLOR:**
- Light source direction, quality, intensity
- Color temperature (warm/cool)
- Shadows, highlights, contrast
- Color palette: dominant colors, accents, saturation
- Overall color mood

**COMPOSITION & STYLE:**
- Camera angle and framing
- Compositional elements and balance
- Artistic style (photorealistic, illustrated, etc.)
- Visual quality and rendering
- Cinematic or aesthetic qualities
- Mood and emotional tone

Be comprehensive and detailed - this caption will be used to generate video prompts."""
            
            caption_result = caption_with_qwen3_vl(pil_image, comprehensive_prompt)
            
            if caption_result["success"]:
                return caption_result["caption"]
            else:
                print(f"[Advanced Node] Qwen3-VL error: {caption_result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"[Advanced Node] Error processing image: {e}")
            import traceback
            traceback.print_exc()
            return None


# For testing
if __name__ == "__main__":
    node = AIVideoPromptExpanderAdvanced()
    print("Advanced node initialized with", len(node.INPUT_TYPES()["required"]), "parameters")
