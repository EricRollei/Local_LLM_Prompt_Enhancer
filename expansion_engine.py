"""
Core expansion engine - VERSION 1.3 - FIXED RANDOM + WILDCARDS
- Random now incorporates user's input concept
- Advanced node random respects dropdown selections
- NEW: Wildcard support {category:option1|option2|option3}
"""

import random
import re
from typing import Dict, List, Tuple, Optional
from .presets import get_preset, get_random_elements, RANDOM_POOLS
from .utils import detect_complexity, parse_keywords, clean_llm_output, extract_prompt_from_response


class PromptExpander:
    """Main prompt expansion engine with wildcards and enhanced detail requirements"""
    
    def __init__(self):
        self.wan_guide = self._load_wan_guide()
    
    def expand_prompt(
        self,
        basic_prompt: str,
        preset: str,
        tier: str,
        mode: str,
        positive_keywords: List[str],
        variation_seed: Optional[int] = None,
        aesthetic_controls: Optional[Dict] = None
    ) -> Tuple[str, str, Dict]:
        """
        Expand a basic prompt with wildcard support and aesthetic controls
        
        Wildcards syntax:
        - {animal:cat|dog|bird} - picks one randomly
        - {animal} - if you have predefined categories
        
        tier parameter accepts both old and new names:
        - Old: auto, basic, enhanced, advanced, cinematic
        - New: concise, moderate, detailed, exhaustive
        
        Returns:
            Tuple of (system_prompt, user_prompt, breakdown_dict)
        """
        # Map new detail_level names to old tier names for backward compatibility
        tier_mapping = {
            "concise": "basic",
            "moderate": "enhanced",
            "detailed": "advanced",
            "exhaustive": "cinematic"
        }
        
        # Convert new names to old internal names
        if tier in tier_mapping:
            detected_tier = tier_mapping[tier]
        elif tier == "auto":
            # STEP 1: Process wildcards in the input prompt
            processed_prompt, wildcard_replacements = self._process_wildcards(basic_prompt, variation_seed)
            detected_tier = detect_complexity(processed_prompt)
        else:
            # Old tier names still work
            detected_tier = tier
            processed_prompt, wildcard_replacements = self._process_wildcards(basic_prompt, variation_seed)
        
        # STEP 1b: Process wildcards if not done yet (for non-auto cases)
        if tier != "auto":
            processed_prompt, wildcard_replacements = self._process_wildcards(basic_prompt, variation_seed)
        
        # STEP 3: Get preset configuration
        preset_config = get_preset(preset)
        
        # STEP 4: Handle random preset - get random elements but use user's concept
        random_elements_selected = None
        if preset == "random":
            random_elements_selected = get_random_elements()
            
            # If advanced node provided aesthetic controls, respect them
            # Only randomize the ones set to "auto"
            if aesthetic_controls:
                random_elements_selected = self._merge_random_with_controls(
                    random_elements_selected, 
                    aesthetic_controls
                )
            
            preset_config = self._build_random_config(random_elements_selected)
        
        # STEP 5: Build prompts
        system_prompt = self._build_system_prompt(
            detected_tier,
            mode,
            preset_config,
            preset,
            variation_seed,
            aesthetic_controls,
            random_elements_selected
        )
        
        user_prompt = self._build_user_prompt(
            processed_prompt,  # Use wildcard-processed prompt
            positive_keywords,
            mode,
            detected_tier
        )
        
        # STEP 6: Build breakdown
        breakdown = {
            "detected_tier": detected_tier,
            "applied_preset": preset,
            "mode": mode,
            "positive_keywords": positive_keywords,
            "preset_focus": preset_config.get("focus_areas", []),
            "aesthetic_controls": aesthetic_controls,
            "was_auto_detected": (tier == "auto"),
            "random_elements": random_elements_selected if preset == "random" else None,
            "wildcard_replacements": wildcard_replacements if wildcard_replacements else None,
            "original_prompt": basic_prompt if wildcard_replacements else None,
            "processed_prompt": processed_prompt if wildcard_replacements else None
        }
        
        return system_prompt, user_prompt, breakdown
    
    def _process_wildcards(self, prompt: str, seed: Optional[int] = None) -> Tuple[str, Dict]:
        """
        Process wildcards in the prompt
        
        Supported formats:
        - {category:option1|option2|option3} - inline options
        - {category} - predefined categories
        
        Returns:
            Tuple of (processed_prompt, replacements_dict)
        """
        if not prompt or '{' not in prompt:
            return prompt, {}
        
        # Set random seed for reproducibility if provided
        if seed is not None:
            random.seed(seed)
        
        replacements = {}
        processed = prompt
        
        # Pattern for inline wildcards: {name:opt1|opt2|opt3}
        inline_pattern = r'\{([^:}]+):([^}]+)\}'
        
        for match in re.finditer(inline_pattern, prompt):
            full_match = match.group(0)
            category = match.group(1).strip()
            options_str = match.group(2)
            options = [opt.strip() for opt in options_str.split('|')]
            
            # Pick random option
            chosen = random.choice(options)
            replacements[category] = chosen
            
            # Replace in prompt
            processed = processed.replace(full_match, chosen, 1)
        
        # Pattern for predefined wildcards: {name}
        predefined_pattern = r'\{([^:}]+)\}'
        
        # Predefined wildcard categories
        predefined_wildcards = {
            "animal": ["cat", "dog", "bird", "horse", "rabbit", "fox", "deer", "wolf"],
            "person": ["man", "woman", "child", "elder", "teenager", "artist", "scientist"],
            "profession": ["detective", "chef", "doctor", "teacher", "engineer", "musician", "artist"],
            "instrument": ["piano", "guitar", "violin", "drums", "saxophone", "flute"],
            "location": ["park", "studio", "street", "forest", "beach", "city", "room"],
            "weather": ["sunny", "rainy", "snowy", "foggy", "stormy", "cloudy"],
            "time": ["morning", "noon", "afternoon", "evening", "night", "midnight"],
            "emotion": ["happy", "sad", "angry", "surprised", "calm", "excited", "pensive"],
            "action": ["walking", "running", "dancing", "working", "playing", "creating"],
            "color": ["red", "blue", "green", "yellow", "purple", "orange", "black", "white"],
            "vehicle": ["car", "motorcycle", "bicycle", "truck", "bus", "train", "boat"],
            "tool": ["hammer", "wrench", "paintbrush", "camera", "telescope", "microscope"],
            "object": ["book", "ball", "box", "bottle", "phone", "computer", "chair"]
        }
        
        for match in re.finditer(predefined_pattern, processed):
            full_match = match.group(0)
            category = match.group(1).strip().lower()
            
            # Skip if already processed (was inline format)
            if category in replacements:
                continue
            
            # Check if we have this category
            if category in predefined_wildcards:
                chosen = random.choice(predefined_wildcards[category])
                replacements[category] = chosen
                processed = processed.replace(full_match, chosen, 1)
        
        # Reset random state
        if seed is not None:
            random.seed()
        
        return processed, replacements if replacements else {}
    
    def _merge_random_with_controls(self, random_elements: Dict, user_controls: Dict) -> Dict:
        """
        Merge random selections with user's dropdown choices
        User's selections override random for those specific elements
        """
        merged = random_elements.copy()
        
        # Map aesthetic control keys to random pool keys
        control_to_pool_map = {
            "light_source": "lighting_types",
            "lighting_type": "lighting_quality",
            "time_of_day": "times_of_day",
            "shot_size": "shot_sizes",
            "composition": "compositions",
            "lens": "lenses",
            "camera_angle": "camera_angles",
            "camera_movement": "camera_movements",
            "color_tone": "color_tones",
            "visual_style": "visual_styles",
            "visual_effect": "visual_effects"
        }
        
        # Remove random selection if user specified it
        for control_key, pool_key in control_to_pool_map.items():
            if control_key in user_controls:
                user_value = user_controls[control_key]
                if user_value and user_value.lower() not in ["auto", "none"]:
                    # User specified this - remove from random elements
                    if pool_key in merged:
                        del merged[pool_key]
        
        return merged
    
    def _build_system_prompt(
        self,
        tier: str,
        mode: str,
        preset_config: Dict,
        preset_name: str,
        variation_seed: Optional[int],
        aesthetic_controls: Optional[Dict] = None,
        random_elements: Optional[Dict] = None
    ) -> str:
        """Build system prompt with MAXIMUM detail requirements"""
        
        word_counts = {
            "basic": "150-250",
            "enhanced": "250-400",
            "advanced": "400-600",
            "cinematic": "600-1000"
        }
        
        prompt = f"""You are an expert AI video prompt engineer for Wan 2.2 video generation.

CRITICAL OUTPUT RULES:
1. Output ONLY the enhanced prompt - no labels, no explanations, no meta-commentary
2. Do NOT repeat or echo the user's input at the start
3. Do NOT include phrases like "Here is...", "Expanded version:", etc.
4. Write as ONE continuous paragraph describing the scene
5. Start directly with the description

DETAIL REQUIREMENTS FOR {tier.upper()} TIER:
- Target length: {word_counts.get(tier, '200-400')} words MINIMUM
- Be EXHAUSTIVELY detailed - describe every visual element
- Do NOT summarize or abbreviate - expand fully
- Include specific details about: textures, materials, lighting quality, color nuances, motion characteristics, spatial relationships, emotional beats
- Every element should be richly described with multiple adjectives and specific details

MODE: {mode}
PRESET: {preset_name}

"""
        
        # Special handling for random preset
        if preset_name == "random":
            prompt += self._format_random_instructions(random_elements, aesthetic_controls)
        
        prompt += self._get_detailed_tier_instructions(tier, mode, preset_name)
        
        # Add aesthetic controls if provided (for advanced node)
        if aesthetic_controls:
            prompt += self._format_aesthetic_controls(aesthetic_controls)
        
        # Add Wan 2.2 reference
        if tier in ["advanced", "cinematic"]:
            prompt += self._get_wan_guide_section(tier, preset_config)
        
        # Add preset emphasis (skip for random as it's handled above)
        if preset_config.get("focus_areas") and preset_name not in ["custom", "random"]:
            prompt += f"\nPRESET EMPHASIS: {', '.join(preset_config['focus_areas'])}\n"
            if preset_config.get("style_hints"):
                prompt += f"Style keywords to incorporate: {', '.join(preset_config['style_hints'][:4])}\n"
        
        # Add variation instructions
        if variation_seed is not None:
            prompt += f"\nVARIATION {variation_seed + 1}: Create unique variation by changing camera approach, lighting setup, or specific action details while keeping core concept.\n"
        
        # Final reminders
        prompt += f"""\nFINAL REMINDERS:
- MINIMUM {word_counts.get(tier, '200')} words
- Be VERBOSE and DETAILED - more detail is always better
- Output ONLY the prompt paragraph - no other text
- Start directly with the description (not with the user's input)
- IMPORTANT: Use the user's concept/subject as the FOUNDATION - expand on THEIR idea
\n"""
        
        return prompt
    
    def _format_random_instructions(self, random_elements: Dict, user_controls: Optional[Dict]) -> str:
        """Format instructions for random preset"""
        
        instructions = "\n=== RANDOM PRESET MODE ===\n"
        instructions += "CRITICAL: Use the user's input concept as the FOUNDATION.\n"
        instructions += "Apply random aesthetic elements TO their idea.\n"
        instructions += "DO NOT ignore or replace the user's subject/concept.\n"
        instructions += "Instead, take their concept and enhance it with random cinematography choices.\n\n"
        
        if random_elements:
            instructions += "Apply these randomly selected aesthetic elements:\n"
            for category, value in random_elements.items():
                category_label = category.replace("_", " ").title()
                instructions += f"- {category_label}: {value}\n"
            instructions += "\n"
        
        if user_controls:
            # Show which were user-specified vs random
            user_specified = {k: v for k, v in user_controls.items() 
                            if v and v.lower() not in ["auto", "none"]}
            if user_specified:
                instructions += "User-specified controls (MUST use these exactly):\n"
                for key, value in user_specified.items():
                    label = key.replace("_", " ").title()
                    instructions += f"- {label}: {value}\n"
                instructions += "\n"
        
        instructions += "Combine the user's concept with these aesthetic choices into one cohesive, detailed prompt.\n\n"
        
        return instructions
    
    def _get_detailed_tier_instructions(self, tier: str, mode: str, preset: str) -> str:
        """Get tier instructions with emphasis on detail"""
        
        mode_note = "NOTE: For image-to-video, focus heavily on MOTION DESCRIPTION and CAMERA MOVEMENT.\n\n" if mode == "image-to-video" else ""
        
        instructions = {
            "basic": f"""{mode_note}BASIC TIER (150-250 words minimum):
Formula: Detailed Subject + Detailed Scene + Detailed Motion

YOU MUST INCLUDE:
- Subject: Describe appearance, clothing, features, expression (3-4 sentences)
- Scene: Describe environment, lighting, objects, atmosphere (3-4 sentences)
- Motion: Describe movement, pace, energy, progression (2-3 sentences)
- Basic cinematography: Shot size, basic lighting type, basic composition

IMPORTANT: Start with the user's concept and expand it with details.
""",

            "enhanced": f"""{mode_note}ENHANCED TIER (250-400 words minimum):
Formula: Rich Subject Details + Rich Scene Details + Rich Motion Details + Full Basic Aesthetics

YOU MUST INCLUDE:
- Subject: Complete appearance description with specific details (5-6 sentences)
- Scene: Comprehensive environment with foreground/midground/background (5-6 sentences)
- Motion: Detailed movement description with speed, fluidity, specific actions (3-4 sentences)
- Shot size, lighting type and source, time of day, color tone, basic composition

Match this level of exhaustive detail for enhanced tier.
""",

            "advanced": f"""{mode_note}ADVANCED TIER (400-600 words minimum):
Formula: Comprehensive Subject + Comprehensive Scene + Precise Motion + Complete Professional Cinematography

YOU MUST INCLUDE:
- Subject: Exhaustive description (8-10 sentences)
- Scene: Complete environmental description (8-10 sentences)
- Motion: Precise choreography (5-6 sentences)
- Professional cinematography: shot size, composition, lighting setup, camera angle, lens type, camera movement, color grading, time of day

Use professional terminology. Be MINIMUM 400 words.
""",

            "cinematic": f"""{mode_note}CINEMATIC TIER (600-1000 words minimum):
Formula: Director-Level Complete Vision

YOU MUST INCLUDE:
- Subject: Complete character description (10-15 sentences)
- Scene: Total environment (15-20 sentences)
- Motion: Choreographed sequence (8-10 sentences)
- Complete cinematography with lighting design, color grading, camera choreography, atmosphere

This is a COMPLETE director's shot description. Be MINIMUM 600 words - 800-1000 is ideal.
"""
        }
        
        return instructions.get(tier, instructions["enhanced"])
    
    def _format_aesthetic_controls(self, controls: Dict) -> str:
        """Format aesthetic controls for system prompt"""
        if not controls:
            return ""
        
        formatted = "\n=== USER-SPECIFIED AESTHETIC CONTROLS ===\n"
        formatted += "The user has specified these requirements. YOU MUST include them:\n\n"
        
        control_map = {
            "light_source": "Light Source",
            "lighting_type": "Lighting Type",
            "time_of_day": "Time of Day",
            "shot_size": "Shot Size",
            "composition": "Composition",
            "lens": "Lens",
            "camera_angle": "Camera Angle",
            "color_tone": "Color Tone",
            "camera_movement": "Camera Movement",
            "visual_style": "Visual Style",
            "visual_effect": "Visual Effect",
            "character_emotion": "Character Emotion"
        }
        
        for key, value in controls.items():
            if value and value.lower() not in ["auto", "none", ""]:
                label = control_map.get(key, key.replace("_", " ").title())
                formatted += f"- {label}: {value}\n"
        
        formatted += "\nIncorporate these specifications naturally into your description.\n\n"
        return formatted
    
    def _get_wan_guide_section(self, tier: str, preset_config: Dict) -> str:
        """Wan 2.2 reference"""
        
        guide = "\n=== WAN 2.2 AESTHETIC OPTIONS ===\n\n"
        
        guide += """**Lighting Sources:** sunny lighting, artificial lighting, moonlighting, practical lighting, firelighting, fluorescent lighting, overcast lighting, mixed lighting

**Lighting Types:** soft lighting, hard lighting, top lighting, side lighting, edge lighting, rim lighting, underlighting, silhouette lighting, backlighting, low contrast lighting, high contrast lighting

**Time of Day:** sunrise time, dawn time, daylight, dusk time, sunset time, night time

**Shot Sizes:** extreme close-up shot, close-up shot, medium close-up shot, medium shot, medium wide shot, wide shot, extreme wide shot

**Composition:** center composition, balanced composition, left-weighted, right-weighted, symmetrical composition, short-side composition

**Lenses:** wide-angle lens, medium lens, long-focus lens, telephoto lens, fisheye lens

**Camera Angles:** eye-level shot, high angle shot, low angle shot, dutch angle shot, aerial shot, over-the-shoulder shot

**Camera Movements:** camera pushes in, camera pulls back, camera pans right/left, camera tilts up/down, static shot, tracking shot, arc shot, handheld camera, compound move

**Color Tones:** warm colors, cool colors, saturated colors, desaturated colors

Select appropriate elements and use them naturally in your description.
\n"""
        
        return guide
    
    def _build_user_prompt(
        self,
        basic_prompt: str,
        positive_keywords: List[str],
        mode: str,
        tier: str
    ) -> str:
        """Build user prompt"""
        parts = [basic_prompt]
        
        if positive_keywords:
            parts.append(f"Required terms: {', '.join(positive_keywords)}")
        
        return " | ".join(parts)
    
    def _build_random_config(self, random_elements: Dict) -> Dict:
        """Build preset config from random elements"""
        return {
            "description": "Random aesthetic elements applied to user's concept",
            "focus_areas": ["creative_exploration", "random_aesthetics"],
            "style_hints": ["experimental", "unexpected"],
            "random_elements": random_elements
        }
    
    def _load_wan_guide(self) -> Dict:
        """Load Wan guide"""
        return {"version": "2.2", "loaded": True}
    
    def generate_negative_prompt(
        self,
        preset: str,
        custom_negatives: List[str],
        mode: str
    ) -> str:
        """Generate negative prompt"""
        
        base_negatives = [
            "blurry", "low quality", "distorted", "watermark", "text overlay",
            "subtitle", "logo", "poor lighting", "static", "frozen",
            "jittery motion", "compression artifacts", "duplicate frames",
            "morphing", "deformed", "disfigured", "unnatural movement"
        ]
        
        preset_negatives = {
            "cinematic": ["amateur", "low-budget", "poor cinematography", "flat lighting", "boring composition"],
            "action": ["slow", "static", "boring", "low energy", "stiff movement"],
            "stylized": ["realistic", "photographic", "bland style", "generic"],
            "noir": ["bright", "cheerful", "colorful", "flat lighting"]
        }
        
        negatives = base_negatives.copy()
        
        if preset in preset_negatives:
            negatives.extend(preset_negatives[preset])
        
        if preset == "noir":
            negatives = [n for n in negatives if n not in ["low quality", "poor lighting"]]
        
        if custom_negatives:
            negatives.extend(custom_negatives)
        
        return ", ".join(list(dict.fromkeys(negatives)))
    
    def parse_llm_response(self, response: str) -> Dict:
        """Parse and clean LLM response with SAFER fallback handling"""
        
        original_response = response
        cleaned = clean_llm_output(response)
        
        # Remove common artifacts
        artifacts = [
            "here is the expanded prompt:", "here's the expanded prompt:",
            "expanded prompt:", "enhanced prompt:", "here is the enhanced version:",
            "here's the enhanced version:", "enhanced version:",
            "expand this text-to-video prompt:", "expand this image-to-video prompt:",
            "output:", "result:", "final prompt:", "generated prompt:"
        ]
        
        cleaned_lower = cleaned.lower()
        for artifact in artifacts:
            if artifact in cleaned_lower:
                idx = cleaned_lower.index(artifact)
                cleaned = cleaned[idx + len(artifact):].strip()
                cleaned_lower = cleaned.lower()
        
        # Try to remove echoed input (first line if short and simple)
        lines = cleaned.split('\n')
        if len(lines) > 1 and len(lines[0]) < 200:
            if not any(term in lines[0].lower() for term in ['lighting', 'camera', 'shot', 'lens', 'composition', 'color', 'scene']):
                cleaned = '\n'.join(lines[1:]).strip()
        
        # CRITICAL FIX: If cleaning left us with nothing or very little, use the original
        if not cleaned or len(cleaned) < 50:
            print(f"WARNING: Aggressive parsing removed too much content. Using original response.")
            cleaned = original_response.strip()
            
            # At least try to remove obvious prefix markers
            for marker in ["expanded prompt:", "enhanced prompt:", "output:"]:
                if cleaned.lower().startswith(marker):
                    cleaned = cleaned[len(marker):].strip()
        
        return {
            "prompt": cleaned,
            "raw_response": original_response
        }
