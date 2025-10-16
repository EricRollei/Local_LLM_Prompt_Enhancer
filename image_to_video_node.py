"""
Image-to-Video Prompt Expander Node
Uses vision model to describe image, then expands motion prompt
"""

import torch
import numpy as np
from PIL import Image
import io
import base64
from typing import Tuple, Optional
from .llm_backend import LLMBackend
from .expansion_engine import PromptExpander
from .utils import (
    save_prompts_to_file,
    parse_keywords,
    validate_positive_keywords
)


class ImageToVideoPromptExpander:
    """
    Advanced Image-to-Video prompt expansion with vision model
    1. Analyzes the image with vision model
    2. Takes user's motion/action input
    3. Combines both into detailed video prompt
    """
    
    def __init__(self):
        self.expander = PromptExpander()
        self.type = "image_to_video_expansion"
        self.output_dir = "output/video_prompts"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Image input
                "image": ("IMAGE",),
                
                # Motion/Action input
                "motion_description": ("STRING", {
                    "multiline": True,
                    "default": "slowly turns head and smiles at camera",
                    "placeholder": "Describe the motion/action you want"
                }),
                
                # Core settings
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
                    "default": "enhanced"
                }),
                
                # Vision model settings
                "use_vision_model": ("BOOLEAN", {
                    "default": True
                }),
                
                "vision_backend": ([
                    "lm_studio",
                    "ollama"
                ], {
                    "default": "lm_studio"
                }),
                
                "vision_model_name": ("STRING", {
                    "default": "llama-3.2-vision",
                    "multiline": False,
                    "placeholder": "e.g., llama-3.2-vision, llava, minicpm-v"
                }),
                
                "vision_endpoint": ("STRING", {
                    "default": "http://localhost:1234/v1",
                    "multiline": False
                }),
                
                # Text expansion model (can be same or different)
                "expansion_backend": ([
                    "lm_studio",
                    "ollama"
                ], {
                    "default": "lm_studio"
                }),
                
                "expansion_model_name": ("STRING", {
                    "default": "llama3",
                    "multiline": False
                }),
                
                "expansion_endpoint": ("STRING", {
                    "default": "http://localhost:1234/v1",
                    "multiline": False
                }),
                
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.1,
                    "max": 2.0,
                    "step": 0.1
                }),
                
                # Camera/Motion controls
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
                    "handheld camera",
                    "steadicam"
                ], {
                    "default": "auto"
                }),
                
                "shot_size": ([
                    "auto",
                    "none",
                    "extreme close-up shot",
                    "close-up shot",
                    "medium close-up shot",
                    "medium shot",
                    "medium wide shot",
                    "wide shot"
                ], {
                    "default": "auto"
                }),
                
                "motion_speed": ([
                    "auto",
                    "very slow",
                    "slow",
                    "normal",
                    "fast",
                    "very fast"
                ], {
                    "default": "auto"
                }),
                
                # Lighting/Time
                "lighting_type": ([
                    "auto",
                    "none",
                    "soft lighting",
                    "hard lighting",
                    "edge lighting",
                    "rim lighting",
                    "natural lighting"
                ], {
                    "default": "auto"
                }),
                
                "time_of_day": ([
                    "auto",
                    "none",
                    "maintain current",
                    "sunrise",
                    "daytime",
                    "sunset",
                    "night"
                ], {
                    "default": "maintain current"
                }),
                
                # Keywords
                "positive_keywords": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "LoRA triggers, style keywords"
                }),
                
                "negative_keywords": ("STRING", {
                    "default": "",
                    "multiline": True
                }),
                
                # Output
                "save_to_file": ("BOOLEAN", {
                    "default": False
                }),
                
                "filename_base": ("STRING", {
                    "default": "img2vid_prompt",
                    "multiline": False
                })
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "image_description", "status")
    
    FUNCTION = "expand_img2vid_prompt"
    CATEGORY = "Eric Prompt Enhancers"
    OUTPUT_NODE = True
    
    def expand_img2vid_prompt(
        self,
        image: torch.Tensor,
        motion_description: str,
        preset: str,
        expansion_tier: str,
        use_vision_model: bool,
        vision_backend: str,
        vision_model_name: str,
        vision_endpoint: str,
        expansion_backend: str,
        expansion_model_name: str,
        expansion_endpoint: str,
        temperature: float,
        camera_movement: str,
        shot_size: str,
        motion_speed: str,
        lighting_type: str,
        time_of_day: str,
        positive_keywords: str,
        negative_keywords: str,
        save_to_file: bool,
        filename_base: str
    ) -> Tuple[str, str, str, str]:
        """
        Main processing: Analyze image → Combine with motion → Expand
        """
        
        try:
            # STEP 1: Get image description
            if use_vision_model:
                image_desc_result = self._analyze_image(
                    image,
                    vision_backend,
                    vision_model_name,
                    vision_endpoint,
                    temperature
                )
                
                if not image_desc_result["success"]:
                    return (
                        motion_description,
                        "",
                        f"ERROR: {image_desc_result['error']}",
                        f"❌ Vision model failed"
                    )
                
                image_description = image_desc_result["description"]
            else:
                image_description = "[Image description skipped - using motion only]"
            
            # STEP 2: Build combined prompt
            combined_input = self._build_combined_prompt(
                image_description,
                motion_description,
                motion_speed
            )
            
            # STEP 3: Gather aesthetic controls
            aesthetic_controls = {}
            if camera_movement not in ["auto", "none"]:
                aesthetic_controls["camera_movement"] = camera_movement
            if shot_size not in ["auto", "none"]:
                aesthetic_controls["shot_size"] = shot_size
            if lighting_type not in ["auto", "none"]:
                aesthetic_controls["lighting_type"] = lighting_type
            if time_of_day not in ["auto", "none", "maintain current"]:
                aesthetic_controls["time_of_day"] = time_of_day
            
            # STEP 4: Expand with expansion engine
            pos_kw_list = parse_keywords(positive_keywords)
            neg_kw_list = parse_keywords(negative_keywords)
            
            system_prompt, user_prompt, breakdown_dict = self.expander.expand_prompt(
                basic_prompt=combined_input,
                preset=preset,
                tier=expansion_tier,
                mode="image-to-video",
                positive_keywords=pos_kw_list,
                variation_seed=None,
                aesthetic_controls=aesthetic_controls
            )
            
            # STEP 5: Call expansion LLM
            expansion_llm = LLMBackend(
                backend_type=expansion_backend,
                endpoint=expansion_endpoint,
                model_name=expansion_model_name,
                temperature=temperature
            )
            
            response = expansion_llm.send_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2000
            )
            
            if not response["success"]:
                return (
                    combined_input,
                    "",
                    image_description,
                    f"❌ Expansion failed: {response['error']}"
                )
            
            # STEP 6: Parse and validate
            parsed = self.expander.parse_llm_response(response["response"])
            enhanced_prompt = parsed["prompt"]
            
            if not enhanced_prompt or len(enhanced_prompt) < 20:
                enhanced_prompt = combined_input
            
            # Add required keywords
            if pos_kw_list:
                keywords_present, missing = validate_positive_keywords(pos_kw_list, enhanced_prompt)
                if missing:
                    enhanced_prompt += f" {', '.join(missing)}"
            
            # STEP 7: Generate negative prompt
            negative_prompt = self.expander.generate_negative_prompt(
                preset=preset,
                custom_negatives=neg_kw_list,
                mode="image-to-video"
            )
            
            # STEP 8: Save if requested
            if save_to_file:
                metadata = {
                    "type": "image-to-video",
                    "preset": preset,
                    "tier": expansion_tier,
                    "vision_model": vision_model_name if use_vision_model else "none",
                    "expansion_model": expansion_model_name,
                    "image_description": image_description,
                    "motion_input": motion_description
                }
                
                breakdown_text = self._format_breakdown(
                    image_description,
                    motion_description,
                    combined_input,
                    aesthetic_controls,
                    breakdown_dict
                )
                
                save_result = save_prompts_to_file(
                    positive_prompt=enhanced_prompt,
                    negative_prompt=negative_prompt,
                    breakdown=breakdown_text,
                    metadata=metadata,
                    filename_base=filename_base,
                    output_dir=self.output_dir
                )
                
                file_status = f"💾 Saved" if save_result["success"] else "⚠️ Save failed"
            else:
                file_status = "Not saved"
            
            status = f"✅ Image-to-Video prompt | Vision: {use_vision_model} | {file_status}"
            
            return (
                enhanced_prompt,
                negative_prompt,
                image_description,
                status
            )
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"ERROR in image-to-video expansion: {error_detail}")
            return (
                motion_description,
                "",
                f"ERROR: {str(e)}",
                f"❌ {str(e)}"
            )
    
    def _analyze_image(
        self,
        image: torch.Tensor,
        backend: str,
        model_name: str,
        endpoint: str,
        temperature: float
    ) -> dict:
        """Use vision model to analyze the image"""
        
        try:
            # Convert tensor to PIL Image
            # ComfyUI image format: [batch, height, width, channels]
            img_np = image[0].cpu().numpy()  # Take first image from batch
            img_np = (img_np * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)
            
            # Convert to base64
            buffered = io.BytesIO()
            pil_image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Build vision prompt
            vision_system_prompt = """You are an expert at describing images in detail for video generation.

Describe this image comprehensively:
- Main subject(s): appearance, clothing, pose, expression
- Setting/environment: location, objects, background
- Lighting: quality, direction, mood
- Color palette: dominant colors, saturation
- Composition: arrangement of elements
- Atmosphere/mood: overall feeling

Be specific and detailed. Focus on visual elements that matter for video generation.
Output ONLY the description, no labels or meta-commentary."""
            
            vision_user_prompt = "Describe this image in detail for video generation purposes."
            
            # Call vision model
            llm = LLMBackend(
                backend_type=backend,
                endpoint=endpoint,
                model_name=model_name,
                temperature=temperature
            )
            
            # For vision models, we need to send the image
            if backend == "lm_studio":
                response = self._call_vision_lm_studio(
                    llm,
                    vision_system_prompt,
                    vision_user_prompt,
                    img_base64
                )
            elif backend == "ollama":
                response = self._call_vision_ollama(
                    llm,
                    vision_system_prompt,
                    vision_user_prompt,
                    img_base64
                )
            else:
                return {"success": False, "error": "Unknown backend"}
            
            if not response["success"]:
                return {"success": False, "error": response["error"]}
            
            description = response["response"].strip()
            
            return {
                "success": True,
                "description": description
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Image analysis failed: {str(e)}"
            }
    
    def _call_vision_lm_studio(self, llm, system_prompt: str, user_prompt: str, img_base64: str) -> dict:
        """Call LM Studio with vision (OpenAI-compatible format)"""
        import requests
        
        try:
            url = f"{llm.endpoint}/chat/completions"
            
            payload = {
                "model": llm.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": llm.temperature,
                "max_tokens": 1000
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            return {"success": True, "response": content, "error": None}
        
        except Exception as e:
            return {"success": False, "response": "", "error": str(e)}
    
    def _call_vision_ollama(self, llm, system_prompt: str, user_prompt: str, img_base64: str) -> dict:
        """Call Ollama with vision"""
        import requests
        
        try:
            url = f"{llm.endpoint}/api/generate"
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            payload = {
                "model": llm.model_name,
                "prompt": full_prompt,
                "images": [img_base64],
                "stream": False,
                "options": {
                    "temperature": llm.temperature,
                    "num_predict": 1000
                }
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            content = data.get('response', '')
            
            return {"success": True, "response": content, "error": None}
        
        except Exception as e:
            return {"success": False, "response": "", "error": str(e)}
    
    def _build_combined_prompt(
        self,
        image_description: str,
        motion_description: str,
        motion_speed: str
    ) -> str:
        """Combine image description and motion into expansion-ready prompt"""
        
        parts = []
        
        # Add image description
        if image_description and not image_description.startswith("ERROR") and not image_description.startswith("[Image"):
            parts.append(f"Scene: {image_description}")
        
        # Add motion with speed modifier
        motion = motion_description
        if motion_speed not in ["auto", "normal"]:
            motion = f"{motion_speed}, {motion}"
        
        parts.append(f"Motion: {motion}")
        
        return " | ".join(parts)
    
    def _format_breakdown(
        self,
        image_description: str,
        motion_input: str,
        combined_prompt: str,
        aesthetic_controls: dict,
        breakdown_dict: dict
    ) -> str:
        """Format breakdown for file output"""
        
        lines = [
            "=" * 60,
            "IMAGE-TO-VIDEO PROMPT EXPANSION",
            "=" * 60,
            "\nIMAGE ANALYSIS:",
            image_description,
            "\nMOTION INPUT:",
            motion_input,
            "\nCOMBINED PROMPT:",
            combined_prompt,
            f"\nExpansion Tier: {breakdown_dict.get('detected_tier', 'N/A')}",
            f"Preset: {breakdown_dict.get('applied_preset', 'N/A')}"
        ]
        
        if aesthetic_controls:
            lines.append("\nAesthetic Controls:")
            for key, value in aesthetic_controls.items():
                lines.append(f"  - {key.replace('_', ' ').title()}: {value}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
