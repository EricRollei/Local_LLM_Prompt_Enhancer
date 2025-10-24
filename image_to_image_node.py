"""
Image-to-Image Prompt Expander Node
Platform-aware prompt generation for image-to-image workflows
"""

import torch
from typing import Tuple, Optional
from .llm_backend import LLMBackend
from .img2img_expansion_engine import ImageToImageExpander
from .platforms import get_platform_list, get_platform_config
from .utils import save_prompts_to_file, parse_keywords
from .qwen3_vl_backend import caption_with_qwen3_vl


class ImageToImagePromptExpander:
    """
    Advanced Image-to-Image prompt expansion with vision model and platform awareness
    1. Analyzes input image with vision model
    2. Takes user's change request
    3. Generates platform-optimized prompt
    """
    
    def __init__(self):
        self.expander = ImageToImageExpander()
        self.type = "image_to_image_expansion"
        self.output_dir = "output/img2img_prompts"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Image input
                "image": ("IMAGE",),
                
                # Change request
                "change_request": ("STRING", {
                    "multiline": True,
                    "default": "change dress to red, add sunset lighting",
                    "placeholder": "Describe what to change (or leave empty to enhance)"
                }),
                
                # Platform selection
                "target_platform": ([
                    "flux",
                    "sd_xl",
                    "wan22",
                    "hunyuan_image",
                    "qwen_image",
                    "qwen_image_edit"
                ], {
                    "default": "flux"
                }),
                
                # Vision model settings
                "use_vision_model": ("BOOLEAN", {
                    "default": True
                }),
                
                "vision_backend": ([
                    "lm_studio",
                    "ollama",
                    "qwen3_vl"
                ], {
                    "default": "lm_studio"
                }),
                
                "vision_model_name": ("STRING", {
                    "default": "llama-3.2-vision",
                    "multiline": False
                }),
                
                "vision_endpoint": ("STRING", {
                    "default": "http://localhost:1234/v1",
                    "multiline": False
                }),
                
                # Expansion model
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
                    "default": 0.6,
                    "min": 0.1,
                    "max": 2.0,
                    "step": 0.1
                }),
                
                # Aesthetic controls
                "art_style": ([
                    "auto",
                    "none",
                    "photorealistic",
                    "digital art",
                    "oil painting",
                    "watercolor",
                    "anime",
                    "sketch",
                    "3D render",
                    "illustration",
                    "concept art"
                ], {
                    "default": "auto"
                }),
                
                "lighting_type": ([
                    "auto",
                    "none",
                    "natural lighting",
                    "studio lighting",
                    "soft lighting",
                    "dramatic lighting",
                    "golden hour",
                    "blue hour",
                    "rim lighting",
                    "volumetric lighting"
                ], {
                    "default": "auto"
                }),
                
                "composition": ([
                    "auto",
                    "none",
                    "rule of thirds",
                    "centered",
                    "symmetrical",
                    "golden ratio",
                    "dynamic",
                    "minimalist"
                ], {
                    "default": "auto"
                }),
                
                "color_palette": ([
                    "auto",
                    "none",
                    "vibrant",
                    "muted",
                    "monochrome",
                    "warm",
                    "cool",
                    "pastel",
                    "high contrast"
                ], {
                    "default": "auto"
                }),
                
                "mood": ([
                    "auto",
                    "none",
                    "serene",
                    "dramatic",
                    "mysterious",
                    "cheerful",
                    "melancholic",
                    "epic",
                    "intimate"
                ], {
                    "default": "auto"
                }),
                
                "detail_level": ([
                    "auto",
                    "standard",
                    "highly detailed",
                    "intricate",
                    "simplified",
                    "minimalist"
                ], {
                    "default": "auto"
                }),
                
                "positive_keywords": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Additional keywords, LoRA triggers"
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
                    "default": "img2img_prompt",
                    "multiline": False
                })
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "image_description", "status")
    
    FUNCTION = "expand_img2img_prompt"
    CATEGORY = "Eric Prompt Enhancers"
    OUTPUT_NODE = True
    
    def expand_img2img_prompt(
        self,
        image: torch.Tensor,
        change_request: str,
        target_platform: str,
        use_vision_model: bool,
        vision_backend: str,
        vision_model_name: str,
        vision_endpoint: str,
        expansion_backend: str,
        expansion_model_name: str,
        expansion_endpoint: str,
        temperature: float,
        art_style: str,
        lighting_type: str,
        composition: str,
        color_palette: str,
        mood: str,
        detail_level: str,
        positive_keywords: str,
        negative_keywords: str,
        save_to_file: bool,
        filename_base: str
    ) -> Tuple[str, str, str, str]:
        """Main processing function"""
        
        try:
            # STEP 1: Analyze image with vision model
            if use_vision_model:
                image_desc_result = self._analyze_image_for_editing(
                    image,
                    vision_backend,
                    vision_model_name,
                    vision_endpoint,
                    temperature
                )
                
                if not image_desc_result["success"]:
                    return (
                        change_request,
                        "",
                        f"ERROR: {image_desc_result['error']}",
                        f"❌ Vision model failed"
                    )
                
                image_description = image_desc_result["description"]
            else:
                image_description = "[Vision analysis skipped]"
            
            # STEP 2: Gather aesthetic controls
            aesthetic_controls = {}
            if art_style not in ["auto", "none"]:
                aesthetic_controls["art_style"] = art_style
            if lighting_type not in ["auto", "none"]:
                aesthetic_controls["lighting_type"] = lighting_type
            if composition not in ["auto", "none"]:
                aesthetic_controls["composition"] = composition
            if color_palette not in ["auto", "none"]:
                aesthetic_controls["color_palette"] = color_palette
            if mood not in ["auto", "none"]:
                aesthetic_controls["mood"] = mood
            if detail_level not in ["auto", "standard"]:
                aesthetic_controls["detail_level"] = detail_level
            
            # STEP 3: Build expansion prompts
            pos_kw_list = parse_keywords(positive_keywords)
            neg_kw_list = parse_keywords(negative_keywords)
            
            system_prompt, user_prompt, breakdown_dict = self.expander.expand_img2img_prompt(
                image_description=image_description,
                change_request=change_request,
                platform=target_platform,
                aesthetic_controls=aesthetic_controls,
                custom_negatives=neg_kw_list
            )
            
            # STEP 4: Call expansion LLM
            expansion_llm = LLMBackend(
                backend_type=expansion_backend,
                endpoint=expansion_endpoint,
                model_name=expansion_model_name,
                temperature=temperature
            )
            
            response = expansion_llm.send_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=500  # Platform-optimized lengths
            )
            
            if not response["success"]:
                # Fallback: use basic combination
                platform_config = get_platform_config(target_platform)
                fallback = f"{image_description}, {change_request}" if change_request else image_description
                enhanced_prompt = fallback
            else:
                enhanced_prompt = self.expander.parse_llm_response(response["response"])
            
            # STEP 5: Add required keywords
            if pos_kw_list:
                enhanced_prompt += f", {', '.join(pos_kw_list)}"
            
            # STEP 6: Generate negative prompt
            negative_prompt = self.expander.generate_negative_prompt(
                platform=target_platform,
                custom_negatives=neg_kw_list
            )
            
            # STEP 7: Save if requested
            if save_to_file:
                metadata = {
                    "type": "image-to-image",
                    "platform": target_platform,
                    "platform_name": breakdown_dict.get("platform_name"),
                    "vision_model": vision_model_name if use_vision_model else "none",
                    "expansion_model": expansion_model_name,
                    "image_description": image_description,
                    "change_request": change_request
                }
                
                breakdown_text = self._format_breakdown(breakdown_dict)
                
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
            
            platform_name = get_platform_config(target_platform)["name"]
            status = f"✅ Image-to-Image | Platform: {platform_name} | {file_status}"
            
            return (
                enhanced_prompt,
                negative_prompt,
                image_description,
                status
            )
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"ERROR in img2img expansion: {error_detail}")
            return (
                change_request,
                "",
                f"ERROR: {str(e)}",
                f"❌ {str(e)}"
            )
    
    def _analyze_image_for_editing(
        self,
        image: torch.Tensor,
        backend: str,
        model_name: str,
        endpoint: str,
        temperature: float
    ) -> dict:
        """Analyze image with focus on edit-relevant details"""
        
        try:
            # Vision prompt focused on structure and key elements
            vision_system_prompt = """You are an expert at analyzing images for image-to-image generation.

Describe this image focusing on:
- Main subject(s): appearance, pose, expression
- Background/setting: environment, objects
- Style: artistic style, medium (photo/painting/etc)
- Lighting: type, direction, quality
- Colors: palette, saturation, temperature
- Composition: layout, focus, depth
- Overall mood/atmosphere

Be detailed but concise. Focus on elements that define the image structure.
Output ONLY the description."""
            
            vision_user_prompt = "Describe this image in detail for image-to-image generation."
            
            # Call vision model (reuse from img2vid)
            from .image_to_video_node import ImageToVideoPromptExpander
            img2vid_node = ImageToVideoPromptExpander()
            
            pil_image = img2vid_node._tensor_to_pil(image)

            if backend == "qwen3_vl":
                qwen_result = caption_with_qwen3_vl(
                    image=pil_image,
                    prompt=vision_user_prompt,
                    system_prompt=vision_system_prompt,
                    model_spec=model_name,
                    backend_hint=endpoint,
                    max_new_tokens=768,
                    temperature=temperature,
                )

                if not qwen_result.get("success"):
                    return {
                        "success": False,
                        "error": qwen_result.get("error", "Qwen3-VL caption failed")
                    }

                description = qwen_result.get("caption", "").strip()

                return {
                    "success": True,
                    "description": description
                }

            img_base64 = img2vid_node._pil_to_base64(pil_image)

            llm = LLMBackend(
                backend_type=backend,
                endpoint=endpoint,
                model_name=model_name,
                temperature=temperature
            )

            if backend == "lm_studio":
                response = img2vid_node._call_vision_lm_studio(
                    llm, vision_system_prompt, vision_user_prompt, img_base64
                )
            elif backend == "ollama":
                response = img2vid_node._call_vision_ollama(
                    llm, vision_system_prompt, vision_user_prompt, img_base64
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
    
    def _format_breakdown(self, breakdown_dict: dict) -> str:
        """Format breakdown for output"""
        
        lines = [
            "=" * 60,
            "IMAGE-TO-IMAGE PROMPT EXPANSION",
            "=" * 60,
            f"\nTarget Platform: {breakdown_dict.get('platform_name', 'N/A')}",
            f"Prompting Style: {breakdown_dict.get('prompt_style', 'N/A')}",
            f"Optimal Length: {breakdown_dict.get('optimal_length', 'N/A')}",
            "\nIMAGE DESCRIPTION:",
            breakdown_dict.get('image_description', 'N/A'),
            "\nCHANGE REQUEST:",
            breakdown_dict.get('change_request', 'None'),
        ]
        
        if breakdown_dict.get('aesthetic_controls'):
            lines.append("\nAESTHETIC CONTROLS:")
            for key, value in breakdown_dict['aesthetic_controls'].items():
                lines.append(f"  - {key.replace('_', ' ').title()}: {value}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
