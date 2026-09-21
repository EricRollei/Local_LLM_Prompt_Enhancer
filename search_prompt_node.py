"""
Search Prompt Database Node
ComfyUI node for keyword / filtered search through the prompt database.

Author: Eric Hiss (GitHub: EricRollei)
"""

import logging
from .prompt_database import PromptDatabase, PLATFORMS, CATEGORIES

logger = logging.getLogger(__name__)


class SearchPromptDatabase:
    """
    Search the local prompt database by keyword, category, platform,
    rating, tags, or favorites.  Returns the top matching prompt as a
    string output that can be fed directly into a sampler or other node.
    """

    def __init__(self):
        self.db = PromptDatabase()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "search_query": ("STRING", {
                    "default": "",
                    "tooltip": (
                        "Keyword search.  Supports AND, OR, NOT, and "
                        "\"quoted phrases\".  Leave blank to browse all."
                    ),
                }),
                "category": (CATEGORIES, {
                    "default": "any",
                    "tooltip": "Filter by category (or 'any' for all).",
                }),
                "platform": (PLATFORMS, {
                    "default": "any",
                    "tooltip": "Filter by target platform (or 'any' for all).",
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
                    "tooltip": "Show only prompts marked as favorites.",
                }),
                "tags_filter": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated tags – all must be present in the result.",
                }),
                "order_by": (["newest", "oldest", "rating", "random"], {
                    "default": "newest",
                    "tooltip": "Sort order for results.",
                }),
                "result_index": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 9999,
                    "step": 1,
                    "tooltip": "Which result to output (1 = top match).",
                }),
                "page_size": ("INT", {
                    "default": 20,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "How many results to fetch per page.",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("prompt_text", "negative_prompt", "total_matches", "result_info", "all_results_summary")
    FUNCTION = "search_prompts"
    CATEGORY = "Eric Prompt Enhancers/Database"
    OUTPUT_NODE = True

    def search_prompts(
        self,
        search_query: str,
        category: str,
        platform: str,
        min_rating: int,
        favorites_only: bool,
        tags_filter: str,
        order_by: str,
        result_index: int,
        page_size: int,
    ):
        try:
            # Compute offset so result_index maps correctly
            offset = 0
            limit = max(result_index, page_size)

            results, total = self.db.search(
                query=search_query,
                category=category,
                platform=platform,
                min_rating=min_rating,
                favorites_only=favorites_only,
                tags_filter=tags_filter,
                limit=limit,
                offset=offset,
                order_by=order_by,
            )

            if not results:
                return ("", "", 0, "No matching prompts found.", "")

            # Pick the requested result
            idx = min(result_index - 1, len(results) - 1)
            chosen = results[idx]

            # Build info line
            info = (
                f"Result {idx + 1}/{total} | "
                f"ID #{chosen['id']} | "
                f"Category: {chosen['category']} | "
                f"Platform: {chosen['platform']} | "
                f"Rating: {'★' * chosen['rating']}{'☆' * (5 - chosen['rating'])} | "
                f"Tags: {chosen['tags'] or '(none)'} | "
                f"Saved: {chosen['created_at']}"
            )

            # Summary of all fetched results
            summary_lines = []
            for i, r in enumerate(results[:page_size], start=1):
                short = r["prompt_text"][:80].replace("\n", " ")
                if len(r["prompt_text"]) > 80:
                    short += "..."
                summary_lines.append(
                    f"[{i}] #{r['id']} ({'★' * r['rating']}) "
                    f"[{r['category']}/{r['platform']}] {short}"
                )
            summary = "\n".join(summary_lines)

            return (
                chosen["prompt_text"],
                chosen.get("negative_prompt", ""),
                total,
                info,
                summary,
            )

        except Exception as e:
            logger.error(f"Search error: {e}")
            return ("", "", 0, f"Error: {e}", "")
