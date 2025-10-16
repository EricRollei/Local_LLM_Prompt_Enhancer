"""
Advanced AI Video Prompt Expander Node with Granular Aesthetic Controls
Provides dropdown menus for all Wan 2.2 elements
"""

import os
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
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Core inputs
                "basic_prompt": ("STRING", {
                    "multiline": True,
                    "default": "A cat playing piano in a cozy room"
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
                
                "expansion_tier": ([
                    "auto",
                    "basic",
                    "enhanced", 
                    "advanced",
                    "cinematic"
                ], {
                    "default": "auto"
                }),
                
                "mode": ([
                    "text-to-video",
                    "image-to-video"
                ], {
                    "default": "text-to-video"
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
                    "mixed lighting"
                ], {
                    "default": "auto"
                }),
                
                "lighting_type": ([
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
                    "high contrast lighting"
                ], {
                    "default": "auto"
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
                    "top-down shot"
                ], {
                    "default": "auto"
                }),
                
                "camera_movement": ([
                    "auto",
                    "none",
                    "static shot",
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
                    "handheld camera",
                    "steadicam",
                    "compound move",
                    "whip pan"
                ], {
                    "default": "auto"
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
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "positive_prompt_1",
        "positive_prompt_2", 
        "positive_prompt_3",
        "negative_prompt",
        "breakdown",
        "status"
    )
    
    FUNCTION = "expand_prompt"
    CATEGORY = "Eric Prompt Enhancers"
    OUTPUT_NODE = True
    
    def expand_prompt(
        self,
        basic_prompt: str,
        preset: str,
        expansion_tier: str,
        mode: str,
        light_source: str,
        lighting_type: str,
        time_of_day: str,
        shot_size: str,
        composition: str,
        lens: str,
        camera_angle: str,
        camera_movement: str,
        color_tone: str,
        visual_style: str,
        visual_effect: str,
        character_emotion: str,
        llm_backend: str,
        model_name: str,
        api_endpoint: str,
        temperature: float,
        positive_keywords: str,
        negative_keywords: str,
        num_variations: int,
        save_to_file: bool,
        filename_base: str
    ) -> Tuple[str, str, str, str, str, str]:
        """
        Main processing function with aesthetic controls
        """
        
        try:
            # Parse keywords
            pos_kw_list = parse_keywords(positive_keywords)
            neg_kw_list = parse_keywords(negative_keywords)
            
            # Gather aesthetic controls
            aesthetic_controls = self._gather_aesthetic_controls(
                light_source, lighting_type, time_of_day,
                shot_size, composition, lens, camera_angle,
                camera_movement, color_tone, visual_style,
                visual_effect, character_emotion
            )
            
            # Initialize LLM backend
            llm = LLMBackend(
                backend_type=llm_backend,
                endpoint=api_endpoint,
                model_name=model_name,
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
                    f"❌ {error_msg}"
                )
            
            # Generate variations
            positive_prompts = []
            breakdowns = []
            
            for var_num in range(num_variations):
                # Build expansion prompts with aesthetic controls
                system_prompt, user_prompt, breakdown_dict = self.expander.expand_prompt(
                    basic_prompt=basic_prompt,
                    preset=preset,
                    tier=expansion_tier,
                    mode=mode,
                    positive_keywords=pos_kw_list,
                    variation_seed=var_num if num_variations > 1 else None,
                    aesthetic_controls=aesthetic_controls
                )
                
                # Call LLM with longer max_tokens for detailed output
                response = llm.send_prompt(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=3000  # Increased for more detail
                )
                
                if not response["success"]:
                    error_msg = response["error"]
                    return (
                        basic_prompt,
                        "",
                        "",
                        "",
                        f"ERROR: {error_msg}",
                        f"❌ {error_msg}"
                    )
                
                # Parse response
                parsed = self.expander.parse_llm_response(response["response"])
                enhanced_prompt = parsed["prompt"]
                
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
            
            # Generate negative prompt
            negative_prompt = self.expander.generate_negative_prompt(
                preset=preset,
                custom_negatives=neg_kw_list,
                mode=mode
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
                    "tier": expansion_tier,
                    "mode": mode,
                    "backend": llm_backend,
                    "model": model_name,
                    "temperature": temperature,
                    "variation_num": num_variations,
                    "original_prompt": basic_prompt,
                    "aesthetic_controls": aesthetic_controls
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
            status = f"✅ Generated {num_variations} variation(s) | Tier: {expansion_tier} | Preset: {preset}\n{controls_summary}\n{file_status}"
            
            return (
                positive_prompts[0],
                positive_prompts[1],
                positive_prompts[2],
                negative_prompt,
                breakdown_text,
                status
            )
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            return (
                basic_prompt,
                "",
                "",
                "",
                f"ERROR: {error_msg}",
                f"❌ {error_msg}"
            )
    
    def _gather_aesthetic_controls(
        self,
        light_source: str,
        lighting_type: str,
        time_of_day: str,
        shot_size: str,
        composition: str,
        lens: str,
        camera_angle: str,
        camera_movement: str,
        color_tone: str,
        visual_style: str,
        visual_effect: str,
        character_emotion: str
    ) -> dict:
        """Gather all non-auto/none aesthetic controls"""
        
        controls = {}
        
        if light_source not in ["auto", "none"]:
            controls["light_source"] = light_source
        if lighting_type not in ["auto", "none"]:
            controls["lighting_type"] = lighting_type
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


# For testing
if __name__ == "__main__":
    node = AIVideoPromptExpanderAdvanced()
    print("Advanced node initialized with", len(node.INPUT_TYPES()["required"]), "parameters")
