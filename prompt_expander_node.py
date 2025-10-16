"""
Main ComfyUI Node for AI Video Prompt Expansion - VERSION 1.2.1
Fixed auto mode + shows detected tier
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


class AIVideoPromptExpander:
    """
    ComfyUI node that expands simple video ideas into detailed prompts
    using local LLMs (LM Studio or Ollama)
    """
    
    def __init__(self):
        self.expander = PromptExpander()
        self.type = "prompt_expansion"
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
                    "placeholder": "Enter comma-separated keywords (e.g., lora_trigger, specific_term)"
                }),
                
                "negative_keywords": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Enter comma-separated negative terms"
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
                    "default": "video_prompt",
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
        """Main processing function"""
        
        try:
            pos_kw_list = parse_keywords(positive_keywords)
            neg_kw_list = parse_keywords(negative_keywords)
            
            llm = LLMBackend(
                backend_type=llm_backend,
                endpoint=api_endpoint,
                model_name=model_name,
                temperature=temperature
            )
            
            conn_test = llm.test_connection()
            if not conn_test["success"]:
                error_msg = f"LLM Connection Failed: {conn_test['message']}"
                return (basic_prompt, "", "", "", f"ERROR: {error_msg}", f"❌ {error_msg}")
            
            positive_prompts = []
            breakdowns = []
            
            for var_num in range(num_variations):
                system_prompt, user_prompt, breakdown_dict = self.expander.expand_prompt(
                    basic_prompt=basic_prompt,
                    preset=preset,
                    tier=expansion_tier,
                    mode=mode,
                    positive_keywords=pos_kw_list,
                    variation_seed=var_num if num_variations > 1 else None
                )
                
                response = llm.send_prompt(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=3000
                )
                
                if not response["success"]:
                    error_msg = response["error"]
                    return (basic_prompt, "", "", "", f"ERROR: {error_msg}", f"❌ {error_msg}")
                
                parsed = self.expander.parse_llm_response(response["response"])
                enhanced_prompt = parsed["prompt"]
                
                # Validate we got output
                if not enhanced_prompt or len(enhanced_prompt) < 20:
                    return (
                        basic_prompt,
                        "",
                        "",
                        "",
                        f"ERROR: LLM returned empty or very short response. Raw: {response['response'][:200]}",
                        f"❌ LLM response too short - check your model"
                    )
                
                if pos_kw_list:
                    keywords_present, missing = validate_positive_keywords(pos_kw_list, enhanced_prompt)
                    if missing:
                        enhanced_prompt += f" {', '.join(missing)}"
                
                positive_prompts.append(enhanced_prompt)
                breakdowns.append(breakdown_dict)
            
            while len(positive_prompts) < 3:
                positive_prompts.append("")
            
            negative_prompt = self.expander.generate_negative_prompt(
                preset=preset,
                custom_negatives=neg_kw_list,
                mode=mode
            )
            
            breakdown_text = self._format_all_breakdowns(breakdowns, basic_prompt)
            
            if save_to_file and positive_prompts[0]:
                metadata = {
                    "preset": preset,
                    "tier": expansion_tier,
                    "detected_tier": breakdowns[0].get('detected_tier'),
                    "mode": mode,
                    "backend": llm_backend,
                    "model": model_name,
                    "temperature": temperature,
                    "variation_num": num_variations,
                    "original_prompt": basic_prompt
                }
                
                save_result = save_prompts_to_file(
                    positive_prompt=positive_prompts[0],
                    negative_prompt=negative_prompt,
                    breakdown=breakdown_text,
                    metadata=metadata,
                    filename_base=filename_base,
                    output_dir=self.output_dir
                )
                
                file_status = f"💾 Saved: {save_result['filepath']}" if save_result["success"] else f"⚠️ Save failed"
            else:
                file_status = "Not saved"
            
            # Build status - show detected tier if auto was used
            detected_tier = breakdowns[0].get('detected_tier')
            was_auto = breakdowns[0].get('was_auto_detected', False)
            
            if was_auto and detected_tier:
                tier_display = f"Tier: auto→{detected_tier}"
            else:
                tier_display = f"Tier: {expansion_tier}"
            
            status = f"✅ Generated {num_variations} variation(s) | {tier_display} | Preset: {preset} | {file_status}"
            
            return (
                positive_prompts[0],
                positive_prompts[1],
                positive_prompts[2],
                negative_prompt,
                breakdown_text,
                status
            )
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"ERROR in prompt expansion: {error_detail}")
            return (
                basic_prompt,
                "",
                "",
                "",
                f"ERROR: {str(e)}\n\n{error_detail}",
                f"❌ {str(e)}"
            )
    
    def _format_all_breakdowns(self, breakdowns: list, original: str) -> str:
        """Format breakdown information"""
        
        if not breakdowns:
            return "No breakdown available"
        
        lines = [
            "=" * 60,
            "PROMPT EXPANSION BREAKDOWN",
            "=" * 60,
            f"\nOriginal Input:\n{original}\n",
        ]
        
        # Show if auto-detected
        if breakdowns[0].get('was_auto_detected'):
            lines.append(f"Tier Setting: auto (detected: {breakdowns[0].get('detected_tier')})")
        else:
            lines.append(f"Detected Tier: {breakdowns[0].get('detected_tier', 'N/A')}")
        
        lines.extend([
            f"Applied Preset: {breakdowns[0].get('applied_preset', 'N/A')}",
            f"Mode: {breakdowns[0].get('mode', 'N/A')}",
        ])
        
        if breakdowns[0].get('positive_keywords'):
            lines.append(f"Required Keywords: {', '.join(breakdowns[0]['positive_keywords'])}")
        
        if breakdowns[0].get('preset_focus'):
            lines.append(f"Focus Areas: {', '.join(breakdowns[0]['preset_focus'])}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
