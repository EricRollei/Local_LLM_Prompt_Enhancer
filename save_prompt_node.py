"""
Save Prompt to Database Node
ComfyUI node that saves prompts to the local SQLite prompt database.
Passthrough design – outputs the same prompt it receives so it can be
inserted into any workflow without breaking connections.

Author: Eric Hiss (GitHub: EricRollei)
"""

import logging
from .prompt_database import PromptDatabase, PLATFORMS, CATEGORIES

logger = logging.getLogger(__name__)


class SavePromptToDatabase:
    """
    Saves a prompt (and optional negative prompt) to the local prompt
    database.  The positive prompt is passed through unchanged so this
    node can sit between a prompt-generating node and a sampler.
    """

    def __init__(self):
        self.db = PromptDatabase()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "The prompt to save. Connect this to the output of any prompt enhancer node.",
                }),
                "category": (CATEGORIES, {
                    "default": "any",
                    "tooltip": "Subject category for organisation.",
                }),
                "platform": (PLATFORMS, {
                    "default": "any",
                    "tooltip": "Target generation platform (Flux, SDXL, Pony, etc.).",
                }),
                "tags": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated tags for easy searching later.",
                }),
                "rating": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 5,
                    "step": 1,
                    "tooltip": "Quality rating 0-5 (0 = unrated).",
                }),
                "save_enabled": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Toggle saving on/off without disconnecting the node.",
                }),
            },
            "optional": {
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "forceInput": True,
                    "tooltip": "Optional negative prompt to store alongside.",
                }),
                "notes": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Free-form notes about this prompt.",
                }),
                "favorite": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Mark this prompt as a favorite.",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = ("prompt_text", "negative_prompt", "prompt_id", "status")
    FUNCTION = "save_prompt"
    CATEGORY = "Eric Prompt Enhancers/Database"
    OUTPUT_NODE = True

    def save_prompt(
        self,
        prompt_text: str,
        category: str,
        platform: str,
        tags: str,
        rating: int,
        save_enabled: bool,
        negative_prompt: str = "",
        notes: str = "",
        favorite: bool = False,
    ):
        if not save_enabled:
            return (prompt_text, negative_prompt, 0, "Save disabled – passthrough only")

        if not prompt_text.strip():
            return (prompt_text, negative_prompt, 0, "Empty prompt – nothing saved")

        try:
            prompt_id = self.db.save_prompt(
                prompt_text=prompt_text,
                negative_prompt=negative_prompt,
                category=category,
                platform=platform,
                tags=tags,
                rating=rating,
                source="manual",
                notes=notes,
                favorite=favorite,
            )
            stats = self.db.stats()
            status = (
                f"Saved as #{prompt_id} | "
                f"DB total: {stats['total_prompts']} prompts"
            )
            logger.info(f"Prompt saved to database with id={prompt_id}")
            return (prompt_text, negative_prompt, prompt_id, status)

        except Exception as e:
            logger.error(f"Error saving prompt: {e}")
            return (prompt_text, negative_prompt, 0, f"Error: {e}")
