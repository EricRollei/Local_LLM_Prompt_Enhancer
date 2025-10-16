"""
Utility functions for file saving and text processing
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional


def save_prompts_to_file(
    positive_prompt: str,
    negative_prompt: str,
    breakdown: str,
    metadata: Dict,
    filename_base: str,
    output_dir: str = "output/video_prompts"
) -> Dict:
    """
    Save prompts and metadata to a text file
    
    Args:
        positive_prompt: Enhanced positive prompt
        negative_prompt: Generated negative prompt
        breakdown: Structured breakdown
        metadata: Dict with generation metadata
        filename_base: Base filename (will append timestamp)
        output_dir: Directory to save to
        
    Returns:
        Dict with success status and filepath
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_base = sanitize_filename(filename_base)
        filename = f"{safe_base}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Format content
        content = format_prompt_file(
            positive_prompt,
            negative_prompt,
            breakdown,
            metadata
        )
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "filepath": filepath,
            "error": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "filepath": None,
            "error": f"File save error: {str(e)}"
        }


def format_prompt_file(
    positive_prompt: str,
    negative_prompt: str,
    breakdown: str,
    metadata: Dict
) -> str:
    """Format the prompt file content"""
    
    separator = "=" * 70
    
    content = f"""{separator}
AI VIDEO PROMPT EXPANDER - GENERATED PROMPTS
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{separator}

POSITIVE PROMPT:
{positive_prompt}

{separator}

NEGATIVE PROMPT:
{negative_prompt}

{separator}

BREAKDOWN:
{breakdown}

{separator}

METADATA:
Preset: {metadata.get('preset', 'N/A')}
Expansion Tier: {metadata.get('tier', 'N/A')}
Mode: {metadata.get('mode', 'N/A')}
LLM Backend: {metadata.get('backend', 'N/A')}
Model: {metadata.get('model', 'N/A')}
Temperature: {metadata.get('temperature', 'N/A')}
Variation: {metadata.get('variation_num', 'N/A')}

{separator}

ORIGINAL INPUT:
{metadata.get('original_prompt', 'N/A')}

{separator}
"""
    return content


def sanitize_filename(filename: str) -> str:
    """Remove invalid filename characters"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    filename = filename[:50]
    # Ensure not empty
    if not filename:
        filename = "prompt"
    return filename


def parse_keywords(keyword_string: str) -> List[str]:
    """Parse comma-separated keywords into list"""
    if not keyword_string or keyword_string.strip() == "":
        return []
    
    # Split by comma and clean
    keywords = [kw.strip() for kw in keyword_string.split(',')]
    # Remove empty strings
    keywords = [kw for kw in keywords if kw]
    
    return keywords


def detect_complexity(prompt: str) -> str:
    """
    Analyze prompt complexity and suggest appropriate tier
    
    Returns: 'basic', 'enhanced', 'advanced', or 'cinematic'
    """
    word_count = len(prompt.split())
    
    # Technical cinematography terms
    technical_terms = [
        'shot', 'camera', 'lens', 'lighting', 'composition', 'angle',
        'close-up', 'wide shot', 'medium shot', 'tracking', 'dolly',
        'pan', 'tilt', 'bokeh', 'depth of field', 'frame', 'focal length',
        'aperture', 'exposure', 'soft light', 'hard light', 'backlight',
        'rim light', 'key light', 'fill light', 'practical', 'motivated'
    ]
    
    prompt_lower = prompt.lower()
    has_technical_terms = any(term in prompt_lower for term in technical_terms)
    
    # Check for detailed descriptions
    has_adjectives = len(re.findall(r'\b(very|extremely|highly|beautiful|stunning|dramatic|vivid)\b', prompt_lower)) > 2
    
    # Tier detection logic
    if word_count < 10 and not has_technical_terms:
        return "basic"
    elif word_count < 25 and not has_technical_terms:
        return "enhanced"
    elif word_count < 50 or (has_technical_terms and word_count < 80):
        return "advanced"
    else:
        return "cinematic"


def format_breakdown(breakdown_dict: Dict) -> str:
    """Format breakdown dictionary into readable text"""
    lines = []
    
    if "subject" in breakdown_dict:
        lines.append(f"Subject: {breakdown_dict['subject']}")
    if "scene" in breakdown_dict:
        lines.append(f"Scene: {breakdown_dict['scene']}")
    if "motion" in breakdown_dict:
        lines.append(f"Motion: {breakdown_dict['motion']}")
    if "aesthetic_control" in breakdown_dict:
        lines.append(f"Aesthetic Control: {breakdown_dict['aesthetic_control']}")
    if "camera" in breakdown_dict:
        lines.append(f"Camera: {breakdown_dict['camera']}")
    if "lighting" in breakdown_dict:
        lines.append(f"Lighting: {breakdown_dict['lighting']}")
    if "style" in breakdown_dict:
        lines.append(f"Style: {breakdown_dict['style']}")
    if "detected_tier" in breakdown_dict:
        lines.append(f"\nDetected Tier: {breakdown_dict['detected_tier']}")
    if "applied_preset" in breakdown_dict:
        lines.append(f"Applied Preset: {breakdown_dict['applied_preset']}")
    
    return "\n".join(lines)


def truncate_text(text: str, max_length: int = 500, add_ellipsis: bool = True) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    if add_ellipsis:
        truncated += "..."
    
    return truncated


def validate_positive_keywords(keywords: List[str], prompt: str) -> bool:
    """Check if positive keywords are already in the prompt"""
    prompt_lower = prompt.lower()
    missing_keywords = []
    
    for keyword in keywords:
        if keyword.lower() not in prompt_lower:
            missing_keywords.append(keyword)
    
    return len(missing_keywords) == 0, missing_keywords


def clean_llm_output(text: str) -> str:
    """Clean up LLM output (remove markdown, extra whitespace, etc.)"""
    # Remove markdown code blocks
    text = re.sub(r'```[\w]*\n?', '', text)
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_prompt_from_response(response: str) -> str:
    """
    Extract just the prompt from LLM response
    Handles cases where LLM adds explanations
    """
    # Look for common prompt markers
    markers = [
        "enhanced prompt:",
        "expanded prompt:",
        "final prompt:",
        "prompt:",
        "here's the prompt:",
        "here is the prompt:"
    ]
    
    response_lower = response.lower()
    
    for marker in markers:
        if marker in response_lower:
            # Find the marker and take everything after it
            idx = response_lower.index(marker)
            prompt = response[idx + len(marker):].strip()
            
            # Take only up to the first double newline (end of prompt)
            if '\n\n' in prompt:
                prompt = prompt.split('\n\n')[0]
            
            return prompt
    
    # If no marker found, return the whole response cleaned
    return clean_llm_output(response)
