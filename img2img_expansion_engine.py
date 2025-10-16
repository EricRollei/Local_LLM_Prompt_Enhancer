"""
Image-to-Image Expansion Engine
Platform-aware prompt expansion for image generation models
"""

from typing import Dict, Tuple, Optional
from .platforms import get_platform_config, format_for_platform, get_negative_prompt_for_platform


class ImageToImageExpander:
    """Expands image descriptions and change requests into platform-optimized prompts"""
    
    def __init__(self):
        self.platforms = {}
    
    def expand_img2img_prompt(
        self,
        image_description: str,
        change_request: str,
        platform: str,
        aesthetic_controls: Optional[Dict] = None,
        quality_emphasis: bool = True,
        custom_negatives: list = None
    ) -> Tuple[str, str, Dict]:
        """
        Expand image-to-image prompt with platform awareness
        
        Args:
            image_description: Vision model's description of input image
            change_request: User's description of desired changes
            platform: Target platform (flux, wan22, hunyuan_image, etc.)
            aesthetic_controls: Style, lighting, composition controls
            quality_emphasis: Add quality tokens
            custom_negatives: Additional negative terms
            
        Returns:
            Tuple of (positive_prompt, negative_prompt, breakdown_dict)
        """
        
        platform_config = get_platform_config(platform)
        
        # Build the system prompt for LLM expansion
        system_prompt = self._build_expansion_prompt(
            platform,
            platform_config,
            aesthetic_controls,
            quality_emphasis
        )
        
        # Build user prompt combining image desc + changes
        user_prompt = self._build_user_prompt(
            image_description,
            change_request,
            platform_config
        )
        
        # Build breakdown for user reference
        breakdown = {
            "platform": platform,
            "platform_name": platform_config["name"],
            "prompt_style": platform_config["prompt_style"],
            "optimal_length": platform_config["optimal_length"],
            "image_description": image_description,
            "change_request": change_request,
            "aesthetic_controls": aesthetic_controls,
            "quality_emphasis": quality_emphasis
        }
        
        return system_prompt, user_prompt, breakdown
    
    def _build_expansion_prompt(
        self,
        platform: str,
        config: dict,
        aesthetic_controls: Optional[Dict],
        quality_emphasis: bool
    ) -> str:
        """Build LLM system prompt with platform-specific instructions"""
        
        prompt = f"""You are an expert prompt engineer for {config['name']} image generation.

CRITICAL OUTPUT RULES:
1. Output ONLY the final prompt - no labels, explanations, or meta-commentary
2. Do NOT include phrases like "Here is...", "Prompt:", etc.
3. Write as a comma-separated list of descriptive elements
4. Start directly with the description

TARGET PLATFORM: {config['name']}
Platform Description: {config['description']}
Prompting Style: {config['prompt_style']}
Optimal Length: {config['optimal_length']}

"""
        
        # Add platform-specific preferences
        if config.get("preferences"):
            prompt += "\nPLATFORM PREFERENCES:\n"
            for pref in config["preferences"]:
                prompt += f"- {pref}\n"
        
        # Add quality tokens if enabled
        if quality_emphasis and config.get("quality_tokens"):
            prompt += f"\nQUALITY TOKENS TO USE: {', '.join(config['quality_tokens'][:5])}\n"
        
        # Add things to avoid
        if config.get("avoid"):
            prompt += "\nAVOID:\n"
            for avoid in config["avoid"]:
                prompt += f"- {avoid}\n"
        
        # Platform-specific instructions
        if platform == "qwen_image_edit":
            prompt += """
EDIT MODE INSTRUCTIONS:
- Be VERY concise (20-50 tokens max)
- Focus ONLY on what changes
- Use clear change language: "change X to Y", "add Z", "remove W"
- Do NOT re-describe unchanged elements
- Include preservation hints if needed: "keep background", "maintain composition"
"""
        
        elif platform == "flux":
            prompt += """
FLUX INSTRUCTIONS:
- Use natural, detailed language (75-150 tokens)
- Include style references when appropriate
- Use photography/artistic terms
- Front-load important concepts
- Quality modifiers are important
"""
        
        elif platform == "wan22":
            prompt += """
WAN 2.2 INSTRUCTIONS:
- Use technical cinematography terminology
- Structure: subject, setting, lighting, composition
- Be specific about lighting types and composition
- Medium length (50-100 tokens)
"""
        
        elif platform == "hunyuan_image":
            prompt += """
HUNYUAN INSTRUCTIONS:
- Clear, simple English (avoid complex vocabulary)
- Focus on photorealism
- Concise but descriptive (40-80 tokens)
- Direct, straightforward descriptions
"""
        
        elif platform == "qwen_image":
            prompt += """
QWEN INSTRUCTIONS:
- Natural, conversational language
- Balanced detail level (50-100 tokens)
- Good with diverse styles and cultural elements
- Professional but not overly technical
"""
        
        elif platform == "sd_xl":
            prompt += """
SDXL INSTRUCTIONS:
- Token-aware: 40-75 tokens optimal
- Front-load important concepts
- Quality tokens at the start
- Can use emphasis with (parentheses)
"""
        
        # Add aesthetic controls if provided
        if aesthetic_controls:
            prompt += self._format_aesthetic_controls(aesthetic_controls, platform)
        
        prompt += """
FINAL REMINDERS:
- Output ONLY the prompt text
- Follow platform-specific preferences
- Combine image description with requested changes seamlessly
- Use appropriate length for platform
"""
        
        return prompt
    
    def _build_user_prompt(
        self,
        image_description: str,
        change_request: str,
        config: dict
    ) -> str:
        """Build user prompt for LLM"""
        
        parts = []
        
        if image_description:
            parts.append(f"Current image: {image_description}")
        
        if change_request:
            parts.append(f"Requested changes: {change_request}")
        else:
            parts.append("No changes requested - enhance and optimize the description for generation")
        
        return " | ".join(parts)
    
    def _format_aesthetic_controls(self, controls: Dict, platform: str) -> str:
        """Format aesthetic controls for system prompt"""
        
        formatted = "\n=== AESTHETIC CONTROLS ===\n"
        formatted += "User has specified these requirements. You MUST incorporate them:\n\n"
        
        control_map = {
            "art_style": "Art Style",
            "lighting_type": "Lighting",
            "composition": "Composition",
            "color_palette": "Color Palette",
            "mood": "Mood/Atmosphere",
            "detail_level": "Detail Level",
            "quality_preset": "Quality Preset"
        }
        
        for key, value in controls.items():
            if value and value.lower() not in ["auto", "none", ""]:
                label = control_map.get(key, key.replace("_", " ").title())
                formatted += f"- {label}: {value}\n"
        
        formatted += "\nSeamlessly integrate these into the prompt.\n"
        return formatted
    
    def generate_negative_prompt(
        self,
        platform: str,
        custom_negatives: list = None
    ) -> str:
        """Generate platform-optimized negative prompt"""
        return get_negative_prompt_for_platform(platform, custom_negatives)
    
    def parse_llm_response(self, response: str) -> str:
        """Clean and parse LLM response"""
        
        cleaned = response.strip()
        
        # Remove common artifacts
        artifacts = [
            "here is the prompt:", "here's the prompt:",
            "prompt:", "final prompt:", "output:",
            "here is:", "here's:"
        ]
        
        cleaned_lower = cleaned.lower()
        for artifact in artifacts:
            if artifact in cleaned_lower:
                idx = cleaned_lower.index(artifact)
                cleaned = cleaned[idx + len(artifact):].strip()
                cleaned_lower = cleaned.lower()
        
        # Remove markdown code blocks if present
        if cleaned.startswith("```"):
            lines = cleaned.split('\n')
            cleaned = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned
        
        # Fallback: use original if cleaned is too short
        if len(cleaned) < 20:
            cleaned = response.strip()
        
        return cleaned
