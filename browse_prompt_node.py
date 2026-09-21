"""
Browse / Random Prompt from Database Node
ComfyUI node that retrieves prompts from the database for reuse –
either by browsing (with ID) or by pulling a filtered random prompt.

Author: Eric Hiss (GitHub: EricRollei)
"""

import logging
from .prompt_database import PromptDatabase, PLATFORMS, CATEGORIES

logger = logging.getLogger(__name__)


class BrowsePromptDatabase:
    """
    Browse or randomly select a prompt from the database.

    Two modes:
      - **Browse by ID**: Set prompt_id > 0 to fetch a specific saved prompt.
      - **Random / Filtered**: Set prompt_id = 0 and use the filters + seed
        to get a random prompt matching your criteria.

    The output can be wired directly into a sampler's positive prompt input.
    """

    def __init__(self):
        self.db = PromptDatabase()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["random", "browse_by_id", "newest", "highest_rated"], {
                    "default": "random",
                    "tooltip": (
                        "random = pick a random prompt matching filters. "
                        "browse_by_id = fetch a specific prompt by its ID. "
                        "newest = most recently saved. "
                        "highest_rated = best rated prompt matching filters."
                    ),
                }),
                "prompt_id": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 9999999,
                    "step": 1,
                    "tooltip": "Used in browse_by_id mode. Set to 0 for other modes.",
                }),
                "category": (CATEGORIES, {
                    "default": "any",
                    "tooltip": "Filter by category (ignored in browse_by_id mode).",
                }),
                "platform": (PLATFORMS, {
                    "default": "any",
                    "tooltip": "Filter by platform (ignored in browse_by_id mode).",
                }),
                "min_rating": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 5,
                    "step": 1,
                    "tooltip": "Only return prompts rated at least this value.",
                }),
                "favorites_only": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Only pick from prompts marked as favorites.",
                }),
                "tags_filter": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated tags – all must be present.",
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xFFFFFFFF,
                    "step": 1,
                    "tooltip": (
                        "Random seed.  In random mode, changing the seed "
                        "gives a different prompt from the matching set. "
                        "Set to 0 for true random."
                    ),
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("prompt_text", "negative_prompt", "prompt_id", "prompt_info", "db_stats")
    FUNCTION = "browse_prompt"
    CATEGORY = "Eric Prompt Enhancers/Database"
    OUTPUT_NODE = True

    def browse_prompt(
        self,
        mode: str,
        prompt_id: int,
        category: str,
        platform: str,
        min_rating: int,
        favorites_only: bool,
        tags_filter: str,
        seed: int,
    ):
        try:
            # ----------------------------------------------------------
            # Browse by ID
            # ----------------------------------------------------------
            if mode == "browse_by_id":
                if prompt_id <= 0:
                    return ("", "", 0, "Set prompt_id > 0 for browse_by_id mode.", self._stats_text())
                row = self.db.get_prompt(prompt_id)
                if row is None:
                    return ("", "", 0, f"No prompt found with ID #{prompt_id}.", self._stats_text())
                return self._format_result(row)

            # ----------------------------------------------------------
            # Filtered search (random / newest / highest_rated)
            # ----------------------------------------------------------
            order_map = {
                "random": "random",
                "newest": "newest",
                "highest_rated": "rating",
            }
            order = order_map.get(mode, "random")

            results, total = self.db.search(
                category=category,
                platform=platform,
                min_rating=min_rating,
                favorites_only=favorites_only,
                tags_filter=tags_filter,
                order_by=order,
                limit=1,
                offset=0,
            )

            if not results:
                return ("", "", 0, "No prompts match the current filters.", self._stats_text())

            return self._format_result(results[0], total=total)

        except Exception as e:
            logger.error(f"Browse error: {e}")
            return ("", "", 0, f"Error: {e}", "")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _format_result(self, row: dict, total: int = 1) -> tuple:
        info = (
            f"ID #{row['id']} | "
            f"Category: {row['category']} | "
            f"Platform: {row['platform']} | "
            f"Rating: {'★' * row['rating']}{'☆' * (5 - row['rating'])} | "
            f"Tags: {row['tags'] or '(none)'} | "
            f"Favorite: {'Yes' if row.get('favorite') else 'No'} | "
            f"Saved: {row['created_at']}"
        )
        if total > 1:
            info += f" | Matches: {total}"
        return (
            row["prompt_text"],
            row.get("negative_prompt", ""),
            row["id"],
            info,
            self._stats_text(),
        )

    def _stats_text(self) -> str:
        try:
            s = self.db.stats()
            parts = [f"Total: {s['total_prompts']} prompts, {s['favorites']} favorites"]
            if s["by_category"]:
                cats = ", ".join(f"{k}:{v}" for k, v in list(s["by_category"].items())[:6])
                parts.append(f"Categories: {cats}")
            if s["by_platform"]:
                plats = ", ".join(f"{k}:{v}" for k, v in list(s["by_platform"].items())[:6])
                parts.append(f"Platforms: {plats}")
            return " | ".join(parts)
        except Exception:
            return ""
