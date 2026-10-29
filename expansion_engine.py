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
from .wildcard_support import llm_block, resolve_wildcards


class PromptExpander:
    """Main prompt expansion engine with wildcards and enhanced detail requirements"""
    
    def __init__(self):
        self.wan_guide = self._load_wan_guide()
        self.last_resolution = None  # core.wildcards Resolution from the most recent _process_wildcards call
        self._surreal_block = ""     # set per run when preset == "surreal": the surreal engine's instruction block
        self._surreal_note = ""
    
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
        reference_mode: str = "recreate_exact",
        wildcard_seed: Optional[int] = None,
        wildcard_llm_block: bool = True,
        wildcard_instructions: str = "",
        target_model: str = "wan22_video",
        duration_seconds: float = 0.0,
        shots_chosen_by_user: bool = False,
        nsfw: str = "off",
        violence_filter: str = "off"
    ) -> Tuple[str, str, Dict]:
        """
        target_model: a video profile id. "wan22_video" (the default here) is the original Wan 2.2 path,
        unchanged. Any other id builds the instructions from that model's profile; see _build_profile_prompts.
        duration_seconds: clip length, used by the profile path only. 0 = not stated.
        shots_chosen_by_user: True when the node has a shot_structure widget, so its value is a real choice.

        2-PASS EXPANSION:
        Pass 1: Vision analysis already done (vision_caption parameter)
        Pass 2: This function - expand prompt using vision caption + reference_mode
        
        Expand a basic prompt with wildcard support, aesthetic controls, and optional vision context
        
        Wildcards: full core/wildcards grammar (see wildcards/README.md), plus the v1 forms
        - {animal:cat|dog|bird} - picks one randomly
        - {animal} - a category that exists as a wildcard file

        wildcard_seed: None = fresh roll; an int = reproducible picks. When omitted, the old
        behaviour applies and variation_seed is used.
        wildcard_llm_block: append the selected-elements block to the user prompt so the LLM
        keeps the random picks (concepts by meaning, verbatim picks word for word).
        
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
        
        # STEP 1: Process wildcards in the input prompt - exactly once, before anything reads it
        effective_wildcard_seed = wildcard_seed if wildcard_seed is not None else variation_seed
        processed_prompt, wildcard_replacements = self._process_wildcards(
            basic_prompt, effective_wildcard_seed, upstream_instructions=wildcard_instructions, nsfw=nsfw,
            violence_filter=violence_filter
        )

        # Convert new names to old internal names
        if tier in tier_mapping:
            detected_tier = tier_mapping[tier]
        elif tier == "auto":
            detected_tier = detect_complexity(processed_prompt)
        else:
            # Old tier names still work
            detected_tier = tier
        
        # STEP 3: Get preset configuration
        preset_config = get_preset(preset)

        # STEP 3b: the `surreal` preset is a procedure now, not a list of style words. The surreal engine picks one
        # operation for this idea (seeded like the wildcards, so each variation gets its own) and its block replaces
        # the preset block. If the engine produces nothing, the old preset text is used as before.
        self._surreal_block, self._surreal_note = "", ""
        if preset == "surreal":
            try:
                from .surreal_support import preset_plan
                processed_prompt, self._surreal_block, self._surreal_note = preset_plan(
                    processed_prompt, effective_wildcard_seed, "video")
            except Exception as error:
                self._surreal_note = f"surreal engine unavailable ({error}); the preset's style words were used"
        
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
        
        # STEP 4b: any target other than Wan 2.2 is written from that model's profile
        profile_plan = self._build_profile_prompts(
            target_model, processed_prompt, detected_tier, mode, preset_config, preset, variation_seed,
            aesthetic_controls, random_elements_selected, shot_structure, shots_chosen_by_user,
            creativity_mode, vision_caption, reference_mode, positive_keywords, duration_seconds,
            llm_block(self.last_resolution, wildcard_llm_block),
        )
        if profile_plan is not None:
            system_prompt, user_prompt, target_info = profile_plan
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
                "wildcard_warnings": (self.last_resolution.warnings or None) if self.last_resolution else None,
                "original_prompt": basic_prompt if wildcard_replacements else None,
                "processed_prompt": processed_prompt if wildcard_replacements else None,
            }
            breakdown.update(target_info)
            if self._surreal_note:
                breakdown.setdefault("target_notes", []).append(self._surreal_note)
            return system_prompt, user_prompt, breakdown

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

        # STEP 5b: Tell the LLM which elements were picked at random, so it keeps them
        selected_elements = llm_block(self.last_resolution, wildcard_llm_block)
        if selected_elements:
            user_prompt = f"{user_prompt}\n\n{selected_elements}"
        
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
            "wildcard_warnings": (self.last_resolution.warnings or None) if self.last_resolution else None,
            "original_prompt": basic_prompt if wildcard_replacements else None,
            "processed_prompt": processed_prompt if wildcard_replacements else None,
            "target_model": "wan22_video",
            "target_name": "Wan 2.2 (this node's original path)",
            "target_task": "i2v" if mode == "image-to-video" else "t2v",
        }
        if target_model and target_model != "wan22_video":
            breakdown["target_notes"] = [f"no video profile named '{target_model}' was found; the Wan 2.2 path was used"]
        if self._surreal_note:
            breakdown.setdefault("target_notes", []).append(self._surreal_note)
        
        return system_prompt, user_prompt, breakdown

    # ------------------------------------------------------------------------------------------
    # Profile path: every target model except Wan 2.2
    # ------------------------------------------------------------------------------------------
    SHOT_REQUESTS = {
        "continuous_paragraph": "one continuous shot, no cuts",
        "2_shot_structure": "two shots (an opening and a final reveal)",
        "3_shot_structure": "three shots (opening, development, final reveal)",
        "4_shot_structure": "four shots (introduction, build, climax, resolution)",
    }

    def _build_profile_prompts(self, target_model, idea, tier, mode, preset_config, preset_name, variation_seed,
                               aesthetic_controls, random_elements, shot_structure, shots_chosen_by_user,
                               creativity_mode, vision_caption, reference_mode, positive_keywords,
                               duration_seconds, selected_elements):
        """
        (system_prompt, user_prompt, info) for a target model other than Wan 2.2, or None to use the Wan path.

        The model-specific part (format, length, rules, camera vocabulary, sound, the vendor's own rewriter
        prompt where one is published) comes from core/profiles. What this engine adds are the blocks that
        are about the USER's direction rather than about the model: preset, aesthetic controls, creativity
        mode, reference-image mode, shot count, variation. The Wan tier text, Wan shot format, Wan option
        list and the tier word minimums are not used here.
        """
        if not target_model or target_model == "wan22_video":
            return None
        try:
            from .core.profiles import RunFacts, plan_rewrite
            from .profile_support import CACHE_DIR, get_profile, tier_word_range
        except Exception as error:
            print(f"[Video Prompt Expander] profile support unavailable ({error}); using the Wan 2.2 path")
            return None
        profile = get_profile(target_model)
        if profile is None or profile.modality != "video":
            return None

        # An image that is the start frame makes this image-to-video. A reference used only for style,
        # colour, pose or character is still text-to-video as far as the target model is concerned.
        start_frame = mode == "image-to-video" and (not vision_caption or reference_mode == "recreate_exact")
        task = profile.resolve_task("i2v" if start_frame else "t2v")
        word_range = tier_word_range(profile, task, tier, duration_seconds)

        blocks = []
        if preset_name == "random":
            blocks.append(self._format_random_instructions(random_elements, aesthetic_controls))
        elif preset_name != "custom":
            blocks.append(self._format_preset_requirements(preset_config, preset_name))
        if aesthetic_controls:
            blocks.append(self._format_aesthetic_controls(aesthetic_controls))
        blocks.append(self._format_creativity_instructions(creativity_mode))
        if vision_caption and not (start_frame and task == "i2v"):
            blocks.append(self._format_reference_mode_instructions(vision_caption, reference_mode))
        if shots_chosen_by_user and shot_structure in self.SHOT_REQUESTS:
            blocks.append(
                f"=== SHOTS ===\nThe user asked for {self.SHOT_REQUESTS[shot_structure]}. Express that the way "
                f"{profile.name} expresses shots (see its format above), and only as far as the clip length allows.\n"
            )
        if variation_seed is not None:
            blocks.append(
                f"VARIATION {variation_seed + 1}: make this version differ from the others in camera approach, "
                f"lighting or the specific action, while keeping the user's concept.\n"
            )
        if positive_keywords:
            blocks.append(
                "=== REQUIRED TERMS ===\nThese exact strings must appear in the visual description, spelled as given "
                f"(they are trigger words): {', '.join(positive_keywords)}\n"
                "In a format with named fields they go inside the FIRST field, at the end of its text - never on a line "
                "of their own and never after the last field.\n"
            )
        direction = "=== THE USER'S DIRECTION FOR THIS PROMPT ===\n(The model's format rules above always win over anything below.)\n\n" + "\n".join(
            block.strip("\n") + "\n" for block in blocks if block and block.strip())
        extra_system = direction if not selected_elements else f"{direction}\n{selected_elements}"

        facts = RunFacts(
            duration_seconds=float(duration_seconds or 0.0),
            image_description=vision_caption if (start_frame and task == "i2v") else "",
            length_words=word_range,
        )
        plan = plan_rewrite(profile, idea, task=task, facts=facts, cache_dir=CACHE_DIR, extra_system=extra_system)
        notes = list(plan.notes)
        if mode == "image-to-video" and task != "i2v":
            notes.append(f"{profile.name} has no image-to-video task in its profile, or the image is a style reference; written as {task}")
        info = {
            "target_model": profile.id,
            "target_name": profile.name,
            "target_task": plan.task,
            "target_format": profile.caption_style,
            "target_words": word_range,
            "target_base": plan.base,
            "target_notes": notes,
            "target_api_note": profile.api_note,
        }
        return plan.system, plan.user, info
    
    def _process_wildcards(self, prompt: str, seed: Optional[int] = None,
                           upstream_instructions: str = "", nsfw: str = "off",
                           violence_filter: str = "off") -> Tuple[str, Dict]:
        """
        Resolve wildcards in the prompt with the shared engine (core/wildcards).

        Same signature and return shape as the v1 implementation, so callers are unchanged:
            Tuple of (processed_prompt, replacements_dict)
        replacements_dict maps a slot name to what was chosen, e.g. {"animal": "a barn owl"}.

        The full record (bindings, origins, warnings) is kept on self.last_resolution.
        Legacy syntax is on, so {animal} and {label:a|b|c} keep working.
        """
        self.last_resolution = None
        if not prompt:
            return prompt, {}

        # upstream_instructions: llm_instructions from a Wildcard Processor / Semantic Variation node earlier in the graph
        resolution = resolve_wildcards(prompt, seed=seed, legacy=True, upstream_instructions=upstream_instructions,
                                       nsfw=nsfw, violence_filter=violence_filter)
        self.last_resolution = resolution
        return resolution.text, resolution.legacy_replacements()
    
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

        if preset_name == "surreal" and self._surreal_block:
            return (f"\n{'='*60}\nPRESET MODE: SURREAL\n{'='*60}\n\n{self._surreal_block}\n\n"
                    "This premise defines the whole prompt. Camera, light and motion stay sober and ordinary so that the "
                    "one anomaly carries the picture.\n\n")
        
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
        visual_style: str = "photorealistic",
        target_model: str = "wan22_video"
    ) -> str:
        """Generate Wan 2.2-optimized negative prompt. Another target_model: that model's own negative, or none."""

        if target_model and target_model != "wan22_video":
            try:
                from .profile_support import legacy_negative
                from_profile = legacy_negative(target_model, custom_negatives)
                if from_profile is not None:
                    return from_profile
            except Exception as error:
                print(f"[Video Prompt Expander] profile negative unavailable ({error}); using the Wan 2.2 one")
        
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
    
    def parse_llm_response(self, response: str, target_model: str = "wan22_video", task: str = "",
                           word_range=None) -> Dict:
        """
        Parse and clean LLM response with SAFER fallback handling.
        For a target other than Wan 2.2 the profile's own checker is used instead: the Wan heuristics below
        (dropping a short first line, cutting at 'output:') would damage field and JSON formats.
        Returns {"prompt", "raw_response"} and, on the profile path, "warnings".
        """
        if target_model and target_model != "wan22_video":
            try:
                from .core.profiles import check
                from .profile_support import get_profile
                profile = get_profile(target_model)
                if profile is not None:
                    text, warnings = check(response, profile, task or profile.default_task(), word_range=word_range)
                    return {"prompt": text, "raw_response": response, "warnings": warnings}
            except Exception as error:
                print(f"[Video Prompt Expander] profile check unavailable ({error}); using the Wan 2.2 parser")

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
