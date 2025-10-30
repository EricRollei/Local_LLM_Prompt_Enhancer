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
        aesthetic_controls: Optional[Dict] = None,
        shot_structure: str = "3_shot_structure",
        creativity_mode: str = "balanced",
        vision_caption: str = "",
        reference_mode: str = "recreate_exact"
    ) -> Tuple[str, str, Dict]:
        """
        2-PASS EXPANSION:
        Pass 1: Vision analysis already done (vision_caption parameter)
        Pass 2: This function - expand prompt using vision caption + reference_mode
        
        Expand a basic prompt with wildcard support, aesthetic controls, and optional vision context
        
        Wildcards syntax:
        - {animal:cat|dog|bird} - picks one randomly
        - {animal} - if you have predefined categories
        
        tier parameter accepts both old and new names:
        - Old: auto, basic, enhanced, advanced, cinematic
        - New: concise, moderate, detailed, exhaustive
        
        vision_caption: Comprehensive image description from Pass 1 (Qwen3-VL)
        reference_mode: How to apply vision_caption (recreate_exact, style_only, etc.)
        
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
        
        # STEP 5: Build prompts (Pass 2 of 2-pass system)
        system_prompt = self._build_system_prompt(
            detected_tier,
            mode,
            preset_config,
            preset,
            variation_seed,
            aesthetic_controls,
            random_elements_selected,
            shot_structure,
            creativity_mode,
            vision_caption,
            reference_mode
        )
        
        user_prompt = self._build_user_prompt(
            processed_prompt,  # Use wildcard-processed prompt
            positive_keywords,
            mode,
            detected_tier,
            vision_caption,
            reference_mode
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
        random_elements: Optional[Dict] = None,
        shot_structure: str = "3_shot_structure",
        creativity_mode: str = "balanced",
        vision_caption: str = "",
        reference_mode: str = "recreate_exact"
    ) -> str:
        """Build system prompt with MAXIMUM detail requirements + vision context"""
        
        word_counts = {
            "basic": "150-250",
            "enhanced": "250-400",
            "advanced": "400-600",
            "cinematic": "600-1000"
        }
        
        # Determine structure format based on shot_structure parameter
        if shot_structure == "continuous_paragraph":
            structure_instructions = self._get_continuous_structure_instructions()
        elif shot_structure == "2_shot_structure":
            structure_instructions = self._get_2_shot_structure_instructions()
        elif shot_structure == "4_shot_structure":
            structure_instructions = self._get_4_shot_structure_instructions()
        else:  # Default: 3_shot_structure
            structure_instructions = self._get_3_shot_structure_instructions()
        
        prompt = f"""You are a cinematic prompt director for Wan 2.2, an AI video generation model that creates 5-9 second videos from text descriptions.

{structure_instructions}

=== CRITICAL REQUIREMENTS ===

1. {"ALWAYS use shot-based structure (not a single paragraph)" if "shot" in shot_structure else "Use a single flowing narrative paragraph"}
2. EVERY shot must specify camera framing AND camera movement
3. Shot 3 MUST include ending cue: "Final shot," "Final wide reveal," or "Final establishing shot"
4. Repeat character identity in each shot: "the same woman in white dress..."
5. Include atmospheric motion in EVERY shot (rain, mist, steam, particles, fabric movement)
6. Target length: {word_counts.get(tier, '200-400')} words MINIMUM across all sections

MODE: {mode}
PRESET: {preset_name}

"""
        
        # Special handling for random preset
        if preset_name == "random":
            prompt += self._format_random_instructions(random_elements, aesthetic_controls)
        elif preset_name != "custom":
            # Add STRONG preset emphasis BEFORE other instructions
            prompt += self._format_preset_requirements(preset_config, preset_name)
        
        prompt += self._get_detailed_tier_instructions(tier, mode, preset_name)
        
        # Add aesthetic controls if provided (for advanced node)
        if aesthetic_controls:
            prompt += self._format_aesthetic_controls(aesthetic_controls)
        
        # Add creativity mode instructions
        prompt += self._format_creativity_instructions(creativity_mode)
        
        # Add vision context and reference mode instructions (Pass 2 of 2-pass system)
        if vision_caption:
            prompt += self._format_reference_mode_instructions(vision_caption, reference_mode)
        
        # Add Wan 2.2 reference
        if tier in ["advanced", "cinematic"]:
            prompt += self._get_wan_guide_section(tier, preset_config)
        
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
        """Get tier instructions with Wan 2.2 shot structure requirements"""
        
        mode_note = "NOTE: For image-to-video, focus heavily on MOTION DESCRIPTION and CAMERA MOVEMENT.\n\n" if mode == "image-to-video" else ""
        
        atmospheric_requirements = """
=== ATMOSPHERIC MOTION & PARALLAX (REQUIRED IN EVERY SHOT) ===

You MUST include depth and motion cues:

Foreground Elements:
- particles drifting, rain streaks past lens, steam blowing across frame
- fabric rippling, hair flowing, cloth fluttering in wind
- sparks flying, dust motes floating, snow falling

Background Depth:
- mist rising from ground, clouds moving slowly
- reflections shimmering on water, shadows shifting
- distant objects moving at different speeds (parallax)

Environmental Animation:
- leaves falling, branches swaying, grass waving
- water flowing, smoke drifting, fire flickering
- light rays moving, steam venting, wind effects

Example phrases:
- "rain streaks diagonally past the lens, catching neon light"
- "low mist rises from the lake and drifts across the frame"
- "her long sleeves leave glowing trails as they sweep through air"
- "steam from street vents blows between camera and subject"

"""
        
        instructions = {
            "basic": f"""{mode_note}{atmospheric_requirements}
BASIC TIER (150-250 words minimum):

Shot Structure Requirements:
- Global Setup: 2 sentences (subject + environment)
- Shot 1: 2 sentences (close/medium framing + action + atmospheric motion)
- Shot 2: 2 sentences (different angle + development + depth cues)
- Shot 3: 2 sentences (reveal + "Final shot" ending cue)
- Style Footer: 1 sentence (fps, style, negatives)

Camera Moves to Use:
- Shot 1: close-up, medium shot, slow dolly in
- Shot 2: camera pans left/right, tracking shot
- Shot 3: camera pulls back, wide shot, overhead shot

Each shot must have atmospheric motion (mist, rain, particles, etc.)
""",

            "enhanced": f"""{mode_note}{atmospheric_requirements}
ENHANCED TIER (250-400 words minimum):

Shot Structure Requirements:
- Global Setup: 3-4 sentences (detailed subject, environment, mood, lighting)
- Shot 1: 3-4 sentences (framing, camera move, action, parallax, emotion)
- Shot 2: 3-4 sentences (new angle, escalation, depth, character development)
- Shot 3: 3-4 sentences (final reveal with "Final wide reveal" cue)
- Style Footer: 2 sentences (full tech specs + negative prompt)

Camera Choreography:
- Combine movements: "slow dolly in while camera pans right"
- Add motion feel: "gentle handheld shake," "smooth glide"
- Vary shot sizes across the three shots

Rich atmospheric detail required in every shot.
Repeat character identity: "the same character in..."
""",

            "advanced": f"""{mode_note}{atmospheric_requirements}
ADVANCED TIER (400-600 words minimum):

Shot Structure Requirements:
- Global Setup: 4-5 sentences (comprehensive scene establishment)
- Shot 1: 5-6 sentences (detailed framing, camera choreography, action, multiple parallax layers, emotional beat)
- Shot 2: 5-6 sentences (complex angle change, escalating action, foreground/midground/background depth)
- Shot 3: 5-6 sentences (dramatic final reveal, explicit "Final shot" or "Final wide reveal" termination)
- Style Footer: 2-3 sentences (complete technical specs, style bundle, negative prompt block)

Professional Camera Language:
- Use precise terms: "camera cranes up and tilts down," "smooth orbital arc," "tracking shot at shoulder height"
- Specify lens: "wide-angle lens," "telephoto compression," "fisheye distortion"
- Add depth of field: "shallow depth of field," "bokeh background," "sharp foreground"

Multiple depth layers per shot required.
Character identity repeated in each shot.
Professional cinematography terminology.
""",

            "cinematic": f"""{mode_note}{atmospheric_requirements}
CINEMATIC TIER (600-1000 words minimum - DIRECTOR'S VISION):

Shot Structure Requirements:
- Global Setup: 6-8 sentences (complete world-building, atmosphere, character introduction, mood establishment)
- Shot 1: 8-10 sentences (exhaustive opening composition, precise camera choreography, detailed action, multiple atmospheric layers, emotional foundation)
- Shot 2: 8-10 sentences (complex camera transition, escalating drama, rich environmental detail, character arc development)
- Shot 3: 8-10 sentences (epic final reveal with explicit "Final wide reveal" or "Final establishing shot", emotional payoff, visual crescendo)
- Style Footer: 3-4 sentences (complete technical specifications, style bundles, comprehensive negative prompt)

Cinematic Requirements:
- Director-level camera choreography: compound moves, crane shots, complex tracking
- Lighting design details: key light, fill light, rim light, practical sources
- Color grading notes: "warm golden hour tones," "desaturated noir palette"
- Sound-visual synergy hints: "as if hearing distant thunder," "silent slow-motion moment"
- Emotional arc across all three shots

This is a COMPLETE shot list for a professional cinematographer.
Every visual element exhaustively described.
Rich atmospheric motion in every layer of every shot.
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
    
    def _format_preset_requirements(self, preset_config: Dict, preset_name: str) -> str:
        """Format STRONG preset requirements that LLM will actually follow"""
        
        section = f"\n{'='*60}\n"
        section += f"🎬 PRESET MODE: {preset_name.upper()}\n"
        section += f"{'='*60}\n\n"
        
        section += f"**Description:** {preset_config.get('description', '')}\n\n"
        
        # Core focus areas - make them MANDATORY
        if preset_config.get("focus_areas"):
            section += "**MANDATORY FOCUS AREAS** (prioritize these above all else):\n"
            for i, area in enumerate(preset_config["focus_areas"], 1):
                section += f"  {i}. {area.replace('_', ' ').title()}\n"
            section += "\n"
        
        # Style hints - make them required vocabulary
        if preset_config.get("style_hints"):
            section += "**REQUIRED STYLE VOCABULARY** (must use these terms/concepts):\n"
            section += f"  {', '.join(preset_config['style_hints'])}\n\n"
        
        # Camera preferences - specific instructions
        if preset_config.get("camera_preferences"):
            section += "**CAMERA REQUIREMENTS:**\n"
            for pref in preset_config["camera_preferences"][:3]:  # Top 3
                section += f"  • {pref}\n"
            section += "\n"
        
        # Lighting preferences - specific instructions  
        if preset_config.get("lighting_preferences"):
            section += "**LIGHTING REQUIREMENTS:**\n"
            for pref in preset_config["lighting_preferences"][:3]:  # Top 3
                section += f"  • {pref}\n"
            section += "\n"
        
        # Motion preferences
        if preset_config.get("motion_preferences"):
            section += "**MOTION STYLE:**\n"
            for pref in preset_config["motion_preferences"][:3]:  # Top 3
                section += f"  • {pref}\n"
            section += "\n"
        
        # Technical specs
        if preset_config.get("technical_specs"):
            section += "**TECHNICAL SPECIFICATIONS:**\n"
            for spec in preset_config["technical_specs"]:
                section += f"  • {spec}\n"
            section += "\n"
        
        # Special atmosphere for noir
        if preset_config.get("atmosphere"):
            section += "**ATMOSPHERE:**\n"
            section += f"  {', '.join(preset_config['atmosphere'])}\n\n"
        
        section += "⚠️  CRITICAL: This preset defines the ENTIRE aesthetic direction.\n"
        section += "    Every creative choice must align with this preset's requirements.\n\n"
        
        return section
    
    def _format_creativity_instructions(self, creativity_mode: str) -> str:
        """Format creativity mode instructions to guide LLM's creative choices"""
        
        creativity_instructions = {
            "conservative": """
=== CREATIVITY MODE: CONSERVATIVE ===
Approach: Focused and predictable

- Prioritize proven, effective creative choices
- Stay very close to the user's original concept
- Use established cinematic techniques
- Only add variations that clearly enhance the core idea
- Avoid experimental or unconventional choices
- Think: "What's the most reliable way to realize this vision?"

""",
            "balanced": """
=== CREATIVITY MODE: BALANCED ===
Approach: Mix proven with fresh

- Balance 70% established techniques with 30% creative variations
- Expand the concept while respecting the original intent
- Use some unexpected elements to add interest
- Favor interesting over purely safe choices
- Think: "How can I make this engaging while staying grounded?"

""",
            "creative": """
=== CREATIVITY MODE: CREATIVE ===
Approach: Bold and experimental

- Actively seek unexpected creative solutions
- Don't default to the most obvious choices
- Camera angles: Favor unusual perspectives (dutch angles, extreme low/high angles)
- Lighting: Try unconventional setups and dramatic contrasts
- Movement: Explore unexpected trajectories and dynamics
- Colors: Consider unusual palettes and combinations
- Think: "What would make a viewer think 'I haven't seen that before'?"

IMPORTANT: When choosing from options, sample from the MIDDLE and LOWER probability range.
Avoid always picking the "safest" or most common choice.

""",
            "highly_creative": """
=== 🎲 CREATIVITY MODE: HIGHLY CREATIVE ===
Approach: Maximum experimentation and bold choices

⚠️ CRITICAL DIRECTIVE: Actively AVOID obvious choices. Be BOLD.

Creative Selection Rules:
1. Camera Angles: Skip eye-level → Try dutch angles, extreme perspectives, disorienting views
2. Lighting: Skip standard three-point → Try single source, practical lights, unconventional angles
3. Movement: Skip typical paths → Try unexpected trajectories, unusual speeds, gravity-defying
4. Colors: Skip natural palettes → Try bold contrasts, unexpected combinations, stylized grading
5. Composition: Skip centered → Try asymmetrical, off-balance, rule-breaking frames

Probability Guideline:
- When you think of 3-5 options, DON'T pick the first one that comes to mind
- Actively choose from the LOWER 50% probability options
- Think: "What would surprise even an experienced cinematographer?"

Goal: Create something visually DISTINCTIVE and MEMORABLE.
Not weird for weird's sake, but intentionally unconventional.

"""
        }
        
        return creativity_instructions.get(creativity_mode, creativity_instructions["balanced"])
    
    def _format_reference_mode_instructions(self, vision_caption: str, reference_mode: str) -> str:
        """
        PASS 2: Apply reference_mode logic to integrate vision caption with user prompt.
        Vision caption is comprehensive - now we filter/apply based on mode.
        """
        
        mode_instructions = {
            "recreate_exact": f"""
=== REFERENCE IMAGE: RECREATE EXACT ===
You have a comprehensive image analysis below. Use it to RECREATE this scene as accurately as possible in video form.

**Your Task:**
- Match the CHARACTER/SUBJECT exactly (appearance, clothing, pose, expression)
- Match the ENVIRONMENT exactly (location, background, spatial layout)
- Match the LIGHTING exactly (direction, quality, color temperature)
- Match the COLOR PALETTE exactly (dominant colors, saturation, mood)
- Match the COMPOSITION and FRAMING
- Match the VISUAL STYLE and mood

**Image Analysis:**
{vision_caption}

**Apply this analysis:** Translate every detail into your video prompt. This is image-to-video - preserve visual consistency.

""",
            "subject_only": f"""
=== REFERENCE IMAGE: SUBJECT ONLY ===
Extract ONLY the character/subject identity from the image analysis. Ignore environment, lighting, and setting.

**Keep from image:**
- Character's facial features, expression, personality
- Hair style, color, length
- Body type, build, posture
- Current clothing (note it exists, but we can change it)
- Age, distinctive traits

**Ignore from image:**
- Background and environment
- Lighting setup
- Setting and location
- Props and objects

**Image Analysis:**
{vision_caption}

**Apply this mode:** Extract character identity, then place them in the scenario described in the user's prompt. New environment, new lighting, new context - same person.

""",
            "style_only": f"""
=== REFERENCE IMAGE: STYLE ONLY ===
Extract ONLY the visual style and aesthetic from the image analysis. Create a NEW subject/scene with this style.

**Keep from image:**
- Artistic style (photorealistic, illustrated, etc.)
- Lighting style and mood
- Color grading and palette treatment
- Atmospheric qualities
- Cinematographic style
- Visual effects and treatments

**Ignore from image:**
- The specific subject/character
- The scene content
- The story or narrative

**Image Analysis:**
{vision_caption}

**Apply this mode:** Use the user's subject/concept, but apply the visual style from the reference image.

""",
            "color_palette_only": f"""
=== REFERENCE IMAGE: COLOR PALETTE ONLY ===
Extract ONLY the color information from the image analysis. Apply this palette to a new scene.

**Extract from image:**
- Dominant colors (3-5 main colors)
- Color relationships and harmony
- Saturation levels
- Color temperature (warm/cool)
- Color mood and emotional tone

**Ignore from image:**
- Subject, composition, lighting style, environment

**Image Analysis:**
{vision_caption}

**Apply this mode:** Create the user's concept using ONLY this color palette. Everything else is original.

""",
            "action_only": f"""
=== REFERENCE IMAGE: ACTION/POSE ONLY ===
Extract ONLY the physical action, pose, and movement from the image analysis.

**Keep from image:**
- Body position and stance
- Arm/hand gestures
- Leg positions
- Head position and tilt
- Movement direction and energy
- Action being performed

**Ignore from image:**
- Character identity
- Clothing and appearance
- Environment and setting
- Lighting and colors

**Image Analysis:**
{vision_caption}

**Apply this mode:** Have the user's subject/character perform THIS SAME ACTION/POSE, but everything else is from the user's prompt.

""",
            "character_remix": f"""
=== REFERENCE IMAGE: CHARACTER REMIX ===
Extract the CHARACTER ESSENCE from the image, then place them in a NEW scenario from user's prompt.

**Keep from image:**
- Core character identity (facial features, expression, personality)
- Character archetype and personality traits
- Age, build, demeanor
- What makes THIS character unique

**Note but can change:**
- Their current outfit (can give them new clothes)
- Their current activity (can put them in new scenario)
- Their current location (can move them)

**Image Analysis:**
{vision_caption}

**Apply this mode:** Keep THIS CHARACTER, but remix everything else based on user's prompt. New clothes, new place, new action - same person.

""",
            "reimagine": f"""
=== REFERENCE IMAGE: REIMAGINE ===
Extract the ESSENCE and CONCEPT from the image, then create a CREATIVE REINTERPRETATION.

**Extract from image:**
- Core concept or theme
- Mood and emotional tone
- Narrative or story suggested
- Symbolic elements
- What makes it compelling
- The "feeling" or atmosphere

**Don't copy literally:**
- Not the exact subject
- Not the exact setting
- Not the exact composition

**Image Analysis:**
{vision_caption}

**Apply this mode:** Be INSPIRED by this image's essence. Create something that captures the same SPIRIT but is visually different. Artistic reinterpretation, not recreation.

"""
        }
        
        return mode_instructions.get(reference_mode, mode_instructions["recreate_exact"])
    
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
        tier: str,
        vision_caption: str = "",
        reference_mode: str = "recreate_exact"
    ) -> str:
        """Build user prompt - vision instructions are in system prompt, user prompt is simple"""
        parts = [basic_prompt]
        
        if positive_keywords:
            parts.append(f"Required terms: {', '.join(positive_keywords)}")
        
        # Note: Vision caption and reference_mode instructions are in SYSTEM prompt
        # User prompt stays clean with just the user's concept
        
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
        mode: str,
        visual_style: str = "photorealistic"
    ) -> str:
        """Generate Wan 2.2-optimized negative prompt"""
        
        # Wan 2.2 base negatives for all styles
        base_negatives = [
            "watermark", "subtitle", "text overlay", "low quality",
            "distorted", "morphing", "deformed", "jittery motion"
        ]
        
        # Style-specific negatives following Wan 2.2 guide
        if visual_style in ["photorealistic", "cinematic", "none", "auto"]:
            # Photoreal/cinematic negative block
            style_negatives = [
                "no subtitles", "no on-screen text", "no watermarks", "no logos",
                "no extra limbs", "no deformed hands", "no distortion", "not low quality",
                "no compression artifacts", "no static frames", "no frozen motion"
            ]
        elif "anime" in visual_style.lower() or "cartoon" in visual_style.lower() or "2D" in visual_style:
            # Anime/stylized negative block
            style_negatives = [
                "no photoreal skin texture", "no live-action lighting",
                "no watermarks", "no subtitles", "keep clean cel shading",
                "no flicker", "no jitter", "no 3D rendering"
            ]
        else:
            # Generic stylized
            style_negatives = [
                "no watermarks", "no subtitles", "no text overlay",
                "no distortion", "no low quality"
            ]
        
        # Preset-specific additions
        preset_negatives = {
            "cinematic": ["amateur cinematography", "poor composition", "flat lighting"],
            "action": ["slow motion", "static", "boring", "low energy"],
            "stylized": ["realistic photoreal", "bland style", "generic look"],
            "noir": ["bright cheerful", "colorful vibrant", "flat even lighting"],
            "surreal": ["realistic normal", "conventional", "mundane"]
        }
        
        negatives = base_negatives + style_negatives
        
        if preset in preset_negatives:
            negatives.extend(preset_negatives[preset])
        
        if custom_negatives:
            negatives.extend(custom_negatives)
        
        # Remove duplicates while preserving order
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
    
    def _get_3_shot_structure_instructions(self) -> str:
        """Get instructions for standard 3-shot structure (recommended for Wan 2.2)"""
        return """=== WAN 2.2 SHOT STRUCTURE FORMAT ===

You MUST use this exact structure:

[GLOBAL SETUP - 2-4 sentences]
Describe: subject/character, environment, overall mood, lighting atmosphere

Shot 1: [Framing + Camera Move]
Describe: starting composition, initial action, foreground/background depth, atmospheric motion, emotional tone
(2-3 sentences)

Shot 2: [New Angle + Camera Move]  
Describe: escalation or new detail, continued motion, parallax cues, character development
(2-3 sentences)

Shot 3: [Final Reveal + Camera Move]
Describe: ending beat, pullback/crane/reveal, MUST include "Final shot" or "Final wide reveal"
(2-3 sentences)

[STYLE/TECH FOOTER - 1-2 sentences]
Include: fps, resolution, style tags, negative prompt"""
    
    def _get_2_shot_structure_instructions(self) -> str:
        """Get instructions for 2-shot structure (opening + finale)"""
        return """=== WAN 2.2 TWO-SHOT STRUCTURE FORMAT ===

You MUST use this exact structure:

[GLOBAL SETUP - 2-4 sentences]
Describe: subject/character, environment, overall mood, lighting atmosphere

Shot 1: [Opening - Framing + Camera Move]
Describe: initial composition, primary action, atmospheric motion, emotional setup, depth cues
(3-4 sentences - longer than 3-shot since you only have 2 beats)

Shot 2: [Final Reveal - Framing + Camera Move]
Describe: escalation or reveal, ending beat, MUST include "Final shot" or "Final wide reveal"
(3-4 sentences - bring the scene to a satisfying conclusion)

[STYLE/TECH FOOTER - 1-2 sentences]
Include: fps, resolution, style tags, negative prompt"""
    
    def _get_4_shot_structure_instructions(self) -> str:
        """Get instructions for 4-shot structure (intro, build, climax, resolution)"""
        return """=== WAN 2.2 FOUR-SHOT STRUCTURE FORMAT ===

You MUST use this exact structure:

[GLOBAL SETUP - 2-4 sentences]
Describe: subject/character, environment, overall mood, lighting atmosphere

Shot 1: [Introduction - Framing + Camera Move]
Describe: establishing composition, initial setup, atmospheric introduction
(2 sentences)

Shot 2: [Build - Framing + Camera Move]
Describe: development, escalating action, new angle, depth and parallax
(2 sentences)

Shot 3: [Climax - Framing + Camera Move]
Describe: peak moment, dramatic beat, character expression or key action
(2 sentences)

Shot 4: [Resolution - Framing + Camera Move]
Describe: ending reveal, pullback or final framing, MUST include "Final shot" or "Final wide reveal"
(2 sentences)

[STYLE/TECH FOOTER - 1-2 sentences]
Include: fps, resolution, style tags, negative prompt"""
    
    def _get_continuous_structure_instructions(self) -> str:
        """Get instructions for continuous paragraph (no shot breaks)"""
        return """=== WAN 2.2 CONTINUOUS NARRATIVE FORMAT ===

You MUST write as ONE CONTINUOUS FLOWING PARAGRAPH with no shot breaks.

Structure your description with temporal progression:
- Opening: Start with establishing the scene and subject (2-3 sentences)
- Middle: Describe the main action and camera movement through it (3-4 sentences)
- Ending: Conclude with a final reveal or resolution, include "Final wide reveal" or ending cue (2-3 sentences)

Use phrases like:
- "The camera starts..." / "At first..." / "Opening on..."
- "Then..." / "As the scene develops..." / "The camera continues..."
- "Finally..." / "The shot concludes with..." / "Final wide reveal shows..."

Include atmospheric motion throughout (mist, rain, particles, fabric movement).
Specify camera movement explicitly (dolly in, pan left, crane up, etc.).
Maintain cinematic flow from beginning to end in one unified narrative.

[STYLE/TECH FOOTER - 1-2 sentences]
Include: fps, resolution, style tags, negative prompt"""

