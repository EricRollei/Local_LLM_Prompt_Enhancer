"""
DeepSeek Prompt Rewriter Node
A fast, cost-effective prompt rewriting node using DeepSeek API.
Transforms simple prompts into detailed, structured image generation prompts.

Author: Eric Hiss (GitHub: EricRollei)
"""

import logging
import requests
import re
import json
import os
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Path to config file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config() -> Dict:
    """Load configuration from config.json"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config.json: {e}")
    return {}


class DeepSeekPromptRewriter:
    """
    Fast, cost-effective prompt rewriting node using DeepSeek API.
    Transforms simple prompts into detailed, structured image generation prompts.
    Uses configuration from config.json for API credentials.
    """
    
    # Enhanced system prompts based on professional instruction sets
    SYSTEM_PROMPTS = {
        "detailed_recaption": """You are a world-class image generation prompt expert. Your task is to rewrite a user's simple description into a **structured, objective, and detail-rich** professional-level prompt.

The final output must be wrapped in `<recaption>` tags.

### **Universal Core Principles**

1. **Absolute Objectivity**: Describe only what is visually present. Avoid subjective words like "beautiful," "stunning," or "sad." Convey aesthetic qualities through specific descriptions of color, light, shadow, texture, and composition.

2. **Physical and Logical Consistency**: All scene elements must strictly adhere to real-world physics and common sense. Light sources must cast appropriate shadows, reflections must be accurate, and spatial relationships must be logical.

3. **Structured Description Order**: Follow this sequence:
   - Subject/main element first (who/what, appearance, pose, expression)
   - Attire and visual details (colors, materials, textures)
   - Environment and background (location, time of day, weather)
   - Technical/stylistic notes (camera, lens, lighting, style)

4. **Use Present Tense**: Describe from an observer's perspective: "A woman stands...", "Light falls on..."

5. **Rich, Specific Language**: Use precise adjectives for quantity, size, shape, color, material, and texture. Avoid vague expressions entirely.

### **Style-Specific Guidelines**

**For Photography/Realism**: Use professional terminology (focal length, aperture, lighting setups). Detail material textures (skin pores, fabric weave, metal finish). Specify camera angle and shot type.

**For Illustration/Painting**: Specify artistic school or technique (cel-shading, impasto, watercolor wash). Describe medium characteristics like line quality, brushstroke texture.

**For Graphic/UI Design**: Define layout, elements, and color palette objectively. Enclose any text in double quotes "like this".

### **Output Requirements**

1. Single cohesive paragraph - NO line breaks, NO bullet points
2. Retain all core concepts from user input
3. Mention style 3-5 times throughout
4. NO self-reference ("This image shows...") - describe directly
5. Target 100-200 words of rich detail
6. Wrap output in `<recaption>your prompt here</recaption>` tags""",
        
        "think_and_recaption": """You will act as a top-tier Text-to-Image prompt engineer. Analyze the user's input deeply and transform it into a detailed, artistic image description.

Your workflow has two phases:

### Phase 1: Thinking (<think>)
Break down and enrich these dimensions:
- **Subject**: Core character(s)/object(s), appearance, posture, expression, emotion
- **Composition**: Camera angle, shot type (close-up, long shot, etc.), layout
- **Environment**: Location, time of day, weather, atmospheric conditions
- **Lighting**: Source type, direction, quality (soft/hard), color temperature
- **Color Palette**: Main tones, color scheme, saturation levels
- **Style/Quality**: Artistic style, camera parameters, rendering quality
- **Details**: Minute elements enhancing realism (accessories, textures, particles)

### Phase 2: Recaption (<recaption>)
Merge all details into a coherent, precise description following these principles:

1. **Absolutely Objective**: Only describe what is visually present
2. **Physically Consistent**: Follow real-world physics for light, shadow, reflections
3. **Structured Order**: Whole to part, background to foreground, primary to secondary
4. **Present Tense**: "A man stands," "light shines on..."
5. **Rich Vocabulary**: Precise adjectives, no vague expressions
6. **80-100 words** of dense, evocative detail

### Output Format
<think>Your analysis and planning here</think><recaption>Your refined image description here</recaption>

### Critical Rules
- Faithful to user intent, but creatively expand details
- If no style specified, default to ultra-realistic photographic
- Text in image must use "double quotes"
- NO explanations or meta-commentary""",

        "cinematic_expansion": """You are a professional cinematographer and visual storytelling expert. Transform simple prompts into cinematic, visually rich scene descriptions.

### Focus Areas (in order of importance):

**1. Subject & Action**
- Core character(s)/object(s) and what they're doing
- Physical attributes, pose, expression, movement

**2. Camera Work**
- Shot type: extreme close-up, close-up, medium, cowboy, full, wide, establishing
- Camera angle: low angle, high angle, eye level, dutch angle, bird's eye, worm's eye
- Movement: static, dolly in/out, pan left/right, tilt up/down, tracking, orbital

**3. Lighting Setup**
- Source: natural/artificial, key light, fill light, rim light, practical lights
- Quality: soft, hard, diffused, direct
- Direction: front lit, back lit, side lit, Rembrandt, butterfly, split
- Color temperature: warm/cool, mixed, golden hour, blue hour

**4. Atmosphere & Environment**
- Time of day: dawn, morning, noon, afternoon, dusk, night
- Weather: clear, cloudy, rainy, foggy, misty, stormy
- Mood: dramatic, serene, tense, romantic, mysterious

**5. Color & Grade**
- Palette: warm, cool, neutral, monochromatic
- Contrast: high, low, medium
- Saturation: vivid, muted, desaturated, pastel

**6. Composition**
- Rule of thirds, centered, symmetrical, asymmetrical
- Leading lines, depth, foreground/background elements
- Negative space, frame within frame

### Output Format
Write in present tense, be specific and objective. Single paragraph, 100-150 words.
Wrap output in `<recaption>Your cinematic description here</recaption>` tags.

### Example
<recaption>Medium shot, low angle. A weathered detective in a rumpled trench coat stands silhouetted against a rain-streaked window, cigarette smoke curling upward. Hard side lighting from a flickering neon sign outside casts crimson and cyan across his angular face, deep shadows pooling in the hollows of his eyes. Camera static. The cramped office interior recedes into murky darkness, venetian blinds slicing the light into geometric patterns. Shallow depth of field isolates the figure against the bokeh of city lights beyond. High contrast, desaturated palette with isolated color accents. Film noir aesthetic, 35mm anamorphic lens characteristics, subtle film grain. Tense, contemplative atmosphere.</recaption>""",

        "photorealistic": """You are an expert in photorealistic image generation prompts. Create prompts that produce images indistinguishable from professional photographs.

### Core Principles for Realism

**1. Authentic Lighting**
- Simulate complex real-world lighting scenarios
- Prioritize natural light sources (windows, practicals, ambient)
- Realistic shadows and highlights that define form
- Accurate reflections on glass, mirrors, polished surfaces
- Specify light quality: soft, hard, diffused, direct

**2. High-Fidelity Textures**
- Materials with extreme detail: fabric weave, thread counts, natural drape
- Skin texture: pores, fine lines, imperfections, subsurface scattering
- Surface details: wood grain, metal finish, concrete texture
- Environmental textures: dust particles, water droplets, atmospheric haze

**3. Camera & Lens Characteristics**
- Focal length and its effect on perspective
- Aperture and depth of field (bokeh quality)
- Lens characteristics: chromatic aberration, vignetting, distortion
- Film/sensor qualities: grain, dynamic range, color science

**4. Natural Composition**
- Professional photography framing techniques
- Appropriate depth of field for subject isolation
- Foreground, middle ground, background layering
- Environmental storytelling through background details

**5. Subject Specifics**
- Precise physical descriptions: age, build, ethnicity, features
- Natural poses and authentic expressions
- Clothing details: fabric type, fit, condition, wear patterns
- Accessories and personal items that add authenticity

### Output Requirements
- Single paragraph, 120-180 words
- Present tense, objective language
- NO words like "beautiful," "stunning," "masterpiece"
- Focus on observable, measurable visual qualities
- Wrap in `<recaption>` tags

<recaption>Your photorealistic prompt here</recaption>""",

        "artistic_style": """You are an art director specializing in visual aesthetics. Transform prompts into artistically rich descriptions emphasizing style and technique.

### Focus Areas

**1. Artistic Medium & Technique**
- Photography styles: editorial, documentary, fine art, fashion, portrait
- Digital art: 3D render, digital painting, vector art, concept art
- Traditional: oil painting, watercolor, charcoal, ink wash, pastel
- Stylized: anime, cel-shading, art nouveau, art deco, pop art

**2. Visual Style & Movement**
- Hyperrealistic, impressionistic, expressionistic, surreal
- Minimalist, maximalist, baroque, brutalist
- Film movements: noir, nouvelle vague, German expressionism
- Contemporary: vaporwave, cyberpunk, cottagecore, dark academia

**3. Color Theory**
- Schemes: complementary, analogous, triadic, split-complementary
- Temperature: warm palette, cool palette, mixed
- Saturation: vivid, muted, pastel, neon
- Grading: high contrast, low key, high key, cross-processed

**4. Texture & Material Rendering**
- Surface qualities: glossy, matte, textured, rough, smooth
- Material properties: translucent, opaque, reflective, metallic
- Stylistic textures: brush strokes, halftone, noise, grain

**5. Composition & Visual Language**
- Balance: symmetrical, asymmetrical, radial
- Flow: diagonal, s-curve, spiral, triangular
- Space: negative space, filled frame, layered depth
- Focus: selective, deep, soft, tack-sharp

### Output Format
Use professional art terminology. Single paragraph, 100-150 words.
Be specific about artistic influences when relevant.
Wrap in `<recaption>Your artistic prompt here</recaption>` tags.""",

        "concise_enhancement": """You are a prompt optimization expert. Enhance prompts to be more effective while staying concise (under 80 words).

### Enhancement Rules

1. **Add Quality Indicators** (but not generic ones)
   - Specific technical quality: "8K resolution, sharp focus, professional color grading"
   - NOT generic: "beautiful, masterpiece, best quality"

2. **Specify Visual Elements Not Mentioned**
   - Lighting type and direction
   - Color palette or temperature
   - Camera angle or shot type
   - Time of day or atmosphere

3. **Strengthen Weak Descriptions**
   - Replace vague with specific: "nice dress" → "flowing silk evening gown in deep burgundy"
   - Add textures and materials
   - Include spatial relationships

4. **Maintain Original Intent**
   - Keep core subject and concept
   - Don't add conflicting elements
   - Preserve specified style if any

5. **Format for Image Generation**
   - Comma-separated descriptive phrases
   - Most important elements first
   - Under 80 words total

### Output
Wrap in `<recaption>` tags. Single line, comma-separated.
<recaption>Your enhanced prompt here</recaption>""",

        "video_prompt": """You are a professional video director. Rewrite prompts for video generation with emphasis on motion and temporal progression.

### Video-Specific Requirements

**1. Motion Description**
- Subject motion: walking, running, turning, gesturing, reaching
- Natural actions: hair blowing, clothes rippling, breathing
- Environmental motion: clouds moving, water flowing, leaves falling
- Use simple, direct verbs for motion

**2. Camera Movement**
- Static: locked-off, tripod shot
- Movement: dolly in/out, pan left/right, tilt up/down
- Complex: tracking shot, crane shot, orbital/arc shot
- Speed: slow push, rapid pull, smooth glide

**3. Temporal Structure**
For 5-second clips, describe progression:
- Opening frame (0-1s): Initial state and setup
- Development (1-4s): Action and motion unfolds
- Resolution (4-5s): Final state or continuation

**4. Lighting & Atmosphere (that supports motion)**
- Light quality: soft, hard, dappled, flickering
- Time: golden hour, blue hour, noon, night
- Weather: sunny, overcast, rainy, foggy, windy

**5. Technical Specifications**
- Shot type: close-up, medium, wide, establishing
- Angle: low, high, eye-level, dutch
- Depth of field: shallow (subject isolation), deep (environmental)

### Output Format
80-100 words describing the complete 5-second sequence.
Include subject, action, camera movement, lighting, atmosphere.
Wrap in `<recaption>` tags.

<recaption>Your video prompt here</recaption>""",

        "pony_diffusion": """You are an expert in Pony Diffusion prompt formatting. Create prompts optimized for Pony-based models.

### CRITICAL FORMAT REQUIREMENTS

**1. MUST START WITH SCORE TAGS (in this exact order):**
score_9, score_8_up, score_7_up

**2. AFTER SCORE TAGS: Use NATURAL LANGUAGE**
- NO danbooru tag format (no underscores)
- Comma-separated descriptive phrases
- Readable English sentences

**3. Description Order:**
- Score tags first
- Subject description (character, appearance, features)
- Pose and expression
- Clothing and accessories
- Setting and background
- Lighting and atmosphere
- Style notes

**4. Language Rules:**
- Use "long flowing hair" NOT "long_hair"
- Use "bright blue eyes" NOT "blue_eyes"
- Use "elegant red dress" NOT "red_dress"
- Natural phrases, rich detail

**5. Length:**
- Target 150-200 words of detailed description
- Rich, evocative language throughout

### Example Format:
<recaption>score_9, score_8_up, score_7_up, a young woman with long flowing silver hair cascading over her shoulders, intense violet eyes with subtle catchlights, delicate features with high cheekbones, wearing an elegant off-shoulder evening gown in deep midnight blue with subtle shimmer, intricate silver embroidery along the neckline, standing in a moonlit garden, soft ambient lighting from paper lanterns, cherry blossom petals drifting through the air, shallow depth of field, romantic atmosphere, professional portrait composition</recaption>""",

        "flux_natural": """You are an expert in FLUX model prompt formatting. Create natural language prompts optimized for FLUX.

### FLUX Prompt Characteristics

**1. Natural Language Style**
- Write as flowing, descriptive prose
- 75-150 tokens optimal
- No tag-style formatting
- Complete sentences or rich phrases

**2. Effective Elements**
- Artistic terminology and references
- "In the style of [artist/movement]" works well
- Photography terms: focal length, aperture, lighting setups
- Quality modifiers: professional, high-end, masterful

**3. Structure**
- Lead with style/medium
- Subject description with key details
- Setting and atmosphere
- Technical/quality notes

**4. What Works Well**
- Specific artist style references
- Detailed lighting descriptions
- Material and texture specifications
- Composition and framing terms
- Emotional/mood descriptors

**5. What to Avoid**
- Generic quality tags (masterpiece, best quality)
- Excessive keyword lists
- Contradictory elements
- Overly long prompts (diminishing returns past 150 tokens)

### Output Format
Write as natural prose. 75-150 words.
Wrap in `<recaption>` tags.

<recaption>Your FLUX-optimized prompt here</recaption>""",

        "keyword_tags": """Generate comma-separated keywords only. No sentences. No explanations.
Generate a single line of comma-separated keywords describing the image.

### Keyword Categories to Cover (as relevant):

**Subject**: gender, age, build, skin tone, expression, distinguishing features
**Clothing**: garment types, fabrics, colors, accessories, state
**Hair**: length, texture, style, color, condition
**Environment**: location type, setting, time, weather, background style
**Lighting**: source, quality, direction, contrast, effects
**Color**: temperature, saturation, scheme, dominant colors
**Style**: artistic style, mood, genre, production quality
**Camera**: angle, framing, shot type, focus, composition
**Composition**: position, balance, flow, space, depth

### Rules:
1. One continuous line only
2. Only commas and spaces between keywords
3. No categories, bullets, or line breaks
4. No sentences or explanations
5. Only observed, relevant keywords
6. Most important keywords first

### Output
Wrap in `<recaption>` tags.
<recaption>keyword1, keyword2, keyword3, keyword4...</recaption>"""
    }
    
    # Platform-specific formatting instructions to append
    PLATFORM_INSTRUCTIONS = {
        "auto": "",  # No platform-specific instructions
        
        "flux": """
### FLUX Platform Format
- Natural language descriptions, 75-150 tokens optimal
- Use artistic terminology and style references
- "In the style of [artist/movement]" works well
- Photography terms effective (focal length, aperture)
- Quality modifiers important but not generic tags
- Avoid excessive keyword lists""",

        "flux2": """
### FLUX2 Platform Format
- Rich natural language, 150-220 words of cinematic prose
- Sensory detail, camera specs, and color cues
- Quote literal text with placement specifications
- Include exact hex colors when relevant
- Describe lighting setups in detail (three-point, softbox, etc.)
- Mention camera + lens metadata
- Can handle complex multi-subject scenes""",

        "sdxl": """
### SDXL Platform Format
- Token limit: 40-75 tokens optimal
- Front-load important concepts
- Quality tokens at start (masterpiece, best quality)
- Can use natural language or comma-separated tags
- Keep concise but descriptive
- Emphasis syntax supported: (keyword:1.2)""",

        "pony": """
### PONY DIFFUSION Platform Format (CRITICAL)
- MUST START with exactly: score_9, score_8_up, score_7_up
- After score tags, use NATURAL LANGUAGE descriptions
- NO danbooru tag format (no underscores like long_hair)
- Use readable text: "long flowing hair", "brown eyes", "red dress"
- Comma-separated detailed phrases
- Aim for 150-200 words of rich descriptive detail
- Example: score_9, score_8_up, score_7_up, a young woman with long flowing hair...""",

        "illustrious": """
### ILLUSTRIOUS XL Platform Format
- Start with quality tags: masterpiece, best quality
- Use danbooru tag format with underscores
- Detailed character appearance tags
- Clothing and accessory tags with specifics
- Background and atmosphere tags
- Format: masterpiece, best quality, 1girl, detailed_face, etc.""",

        "chroma": """
### CHROMA/MEISSONIC Platform Format
- Natural, detailed language (100-200 tokens)
- Excellent with complex scenes and multiple subjects
- Describe spatial relationships clearly
- Compositional details important
- Can handle abstract and artistic concepts well""",

        "wan_image": """
### WAN Image Platform Format
- Technical cinematography terms
- Structured format: subject, setting, lighting, composition
- Specific lighting types (soft lighting, edge lighting, rim light)
- Professional photography language
- Medium length (60-120 tokens)""",

        "wan_video": """
### WAN Video Platform Format
- Emphasize motion and camera movement
- Camera movements: zoom in/out, pan left/right, tilt up/down, dolly, orbit
- Describe temporal progression (at 0s, at 2s, at 4s)
- Natural motion attributes with simple direct verbs
- Include subject actions and environmental motion
- 80-100 words describing 5-second sequence""",

        "hunyuan": """
### HUNYUAN Image Platform Format
- Structured, objective, detail-rich descriptions
- Follow order: subject → attire → environment → technical
- Present tense descriptions
- Rich specific language with precise adjectives
- Mention style 3-5 times throughout
- 100-200 words optimal""",

        "cogvideo": """
### COGVIDEO Platform Format
- Focus on motion and action descriptions
- Simple, clear subject and action statements
- Environmental context for movement
- Temporal flow descriptions
- Moderate length (60-100 words)""",

        "kolors": """
### KOLORS Platform Format
- Natural language descriptions
- Bilingual support (English works well)
- Detailed subject descriptions
- Style and atmosphere emphasis
- Medium length prompts (80-150 words)"""
    }
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True, 
                    "default": "A serene landscape with mountains",
                    "placeholder": "Enter your prompt to rewrite..."
                }),
                "rewrite_style": ([
                    "detailed_recaption",
                    "think_and_recaption",
                    "cinematic_expansion",
                    "photorealistic",
                    "artistic_style",
                    "concise_enhancement",
                    "video_prompt",
                    "keyword_tags",
                    "none"
                ], {"default": "detailed_recaption"}),
                "target_platform": ([
                    "auto",
                    "flux",
                    "flux2", 
                    "sdxl",
                    "pony",
                    "illustrious",
                    "chroma",
                    "wan_image",
                    "wan_video",
                    "hunyuan",
                    "cogvideo",
                    "kolors"
                ], {"default": "auto"}),
            },
            "optional": {
                "temperature": ("FLOAT", {
                    "default": 0.7, 
                    "min": 0.0, 
                    "max": 2.0, 
                    "step": 0.1,
                    "display": "slider"
                }),
                "max_tokens": ("INT", {
                    "default": 1000, 
                    "min": 100, 
                    "max": 4000, 
                    "step": 100
                }),
                "seed": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 0xffffffffffffffff
                }),
                "custom_system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Optional: Override with custom system prompt..."
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("rewritten_prompt", "full_response")
    FUNCTION = "rewrite_prompt"
    CATEGORY = "Eric's Nodes/Prompting"

    def rewrite_prompt(
        self, 
        prompt: str, 
        rewrite_style: str,
        target_platform: str = "auto",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        seed: int = 0,
        custom_system_prompt: str = ""
    ) -> Tuple[str, str]:
        """
        Rewrite a prompt using DeepSeek API.
        
        Args:
            prompt: The original prompt to rewrite
            rewrite_style: The style of rewriting to apply
            target_platform: Target image/video generation platform
            temperature: LLM temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            seed: Random seed for reproducibility (0 = random)
            custom_system_prompt: Optional custom system prompt override
            
        Returns:
            Tuple of (rewritten_prompt, full_response)
        """
        # Pass through if style is "none" or prompt is empty
        if rewrite_style == "none" or not prompt.strip():
            return (prompt, prompt)

        # Load config and get DeepSeek credentials
        config = load_config()
        
        if not config or "backends" not in config:
            logger.warning("No config.json found or missing backends section. Returning original prompt.")
            return (prompt, "Error: No configuration found")
            
        deepseek_config = config.get("backends", {}).get("deepseek", {})
        api_key = deepseek_config.get("api_key")
        
        if not api_key:
            logger.warning("No DeepSeek API key found in config.json. Returning original prompt.")
            return (prompt, "Error: No DeepSeek API key configured")

        # Get API settings
        base_url = deepseek_config.get("base_url", "https://api.deepseek.com/v1")
        model_name = deepseek_config.get("model", "deepseek-chat")
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        
        # Build system prompt: combine style + platform instructions
        if custom_system_prompt.strip():
            system_prompt = custom_system_prompt.strip()
        else:
            # Get base style prompt
            system_prompt = self.SYSTEM_PROMPTS.get(
                rewrite_style, 
                self.SYSTEM_PROMPTS["detailed_recaption"]
            )
            
            # Append platform-specific instructions if not "auto"
            platform_instructions = self.PLATFORM_INSTRUCTIONS.get(target_platform, "")
            if platform_instructions:
                system_prompt = system_prompt + "\n" + platform_instructions
        
        logger.info(f"Rewriting prompt using DeepSeek API (style: {rewrite_style}, platform: {target_platform})...")
        
        # Build request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add seed if provided (non-zero)
        if seed > 0:
            data["seed"] = seed

        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            content = result['choices'][0]['message']['content']
            full_response = content
            
            # Extract content between <recaption> tags
            match = re.search(r'<recaption>(.*?)</recaption>', content, re.DOTALL)
            if match:
                rewritten = match.group(1).strip()
                logger.info("Prompt rewritten successfully")
                return (rewritten, full_response)
            else:
                # Fallback: try to clean up any remaining tags
                cleaned = re.sub(r'</?think>|</?recaption>', '', content).strip()
                logger.warning("No <recaption> tags found in response, using cleaned content")
                return (cleaned, full_response)
                
        except requests.exceptions.Timeout:
            logger.error("DeepSeek API request timed out")
            return (prompt, "Error: Request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}")
            return (prompt, f"Error: {str(e)}")
        except KeyError as e:
            logger.error(f"Unexpected API response format: {e}")
            return (prompt, f"Error: Unexpected response format - {str(e)}")
        except Exception as e:
            logger.error(f"Prompt rewriting failed: {e}")
            return (prompt, f"Error: {str(e)}")


class DeepSeekChat:
    """
    General-purpose chat node using DeepSeek API.
    Useful for custom prompt engineering, brainstorming, or any text generation task.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "user_message": ("STRING", {
                    "multiline": True, 
                    "default": "",
                    "placeholder": "Enter your message..."
                }),
            },
            "optional": {
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "You are a helpful AI assistant.",
                    "placeholder": "System prompt to set AI behavior..."
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7, 
                    "min": 0.0, 
                    "max": 2.0, 
                    "step": 0.1,
                    "display": "slider"
                }),
                "max_tokens": ("INT", {
                    "default": 2000, 
                    "min": 100, 
                    "max": 8000, 
                    "step": 100
                }),
                "seed": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 0xffffffffffffffff
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "chat"
    CATEGORY = "Eric's Nodes/Prompting"

    def chat(
        self, 
        user_message: str,
        system_prompt: str = "You are a helpful AI assistant.",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        seed: int = 0
    ) -> Tuple[str]:
        """
        Send a message to DeepSeek and get a response.
        """
        if not user_message.strip():
            return ("",)

        # Load config
        config = load_config()
        
        if not config or "backends" not in config:
            return ("Error: No configuration found",)
            
        deepseek_config = config.get("backends", {}).get("deepseek", {})
        api_key = deepseek_config.get("api_key")
        
        if not api_key:
            return ("Error: No DeepSeek API key configured",)

        # Get API settings
        base_url = deepseek_config.get("base_url", "https://api.deepseek.com/v1")
        model_name = deepseek_config.get("model", "deepseek-chat")
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if seed > 0:
            data["seed"] = seed

        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            return (content,)
                
        except Exception as e:
            logger.error(f"DeepSeek chat failed: {e}")
            return (f"Error: {str(e)}",)


# Node mappings for this module
NODE_CLASS_MAPPINGS = {
    "DeepSeekPromptRewriter": DeepSeekPromptRewriter,
    "DeepSeekChat": DeepSeekChat
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DeepSeekPromptRewriter": "DeepSeek Prompt Rewriter",
    "DeepSeekChat": "DeepSeek Chat"
}
