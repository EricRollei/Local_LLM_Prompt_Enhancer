"""
Import Prompts to Database Node
ComfyUI node that bulk-imports prompts from .txt, .csv, or .json files.

Author: Eric Hiss (GitHub: EricRollei)
"""

import os
import logging
from .prompt_database import PromptDatabase, PLATFORMS, CATEGORIES

logger = logging.getLogger(__name__)


class ImportPromptsToDatabase:
    """
    Bulk-import prompts from external files into the local prompt database.

    Supported formats:
      - .txt  (one prompt per line, or paragraph-separated)
      - .csv  (header row: prompt_text, negative_prompt, category, …)
      - .json (array of strings or array of objects with prompt_text key)

    Duplicate detection prevents the same prompt being imported twice.
    """

    def __init__(self):
        self.db = PromptDatabase()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {
                    "default": "",
                    "tooltip": (
                        "Absolute path to the file to import.  "
                        "Supports .txt, .csv, and .json."
                    ),
                }),
                "file_format": (["auto", "txt_line", "txt_paragraph", "csv", "json"], {
                    "default": "auto",
                    "tooltip": (
                        "auto = detect from extension.  "
                        "txt_line = one prompt per line.  "
                        "txt_paragraph = prompts separated by blank lines."
                    ),
                }),
                "default_category": (CATEGORIES, {
                    "default": "any",
                    "tooltip": "Category to assign when the file doesn't specify one.",
                }),
                "default_platform": (PLATFORMS, {
                    "default": "any",
                    "tooltip": "Platform to assign when the file doesn't specify one.",
                }),
                "default_tags": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated tags to apply to every imported prompt.",
                }),
                "skip_duplicates": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Skip prompts that already exist in the database.",
                }),
            },
        }

    RETURN_TYPES = ("INT", "INT", "STRING", "STRING")
    RETURN_NAMES = ("imported_count", "skipped_count", "status", "errors")
    FUNCTION = "import_prompts"
    CATEGORY = "Eric Prompt Enhancers/Database"
    OUTPUT_NODE = True

    def import_prompts(
        self,
        file_path: str,
        file_format: str,
        default_category: str,
        default_platform: str,
        default_tags: str,
        skip_duplicates: bool,
    ):
        file_path = file_path.strip()
        if not file_path:
            return (0, 0, "No file path provided.", "")

        if not os.path.isfile(file_path):
            return (0, 0, f"File not found: {file_path}", "")

        # Detect format from extension when set to auto
        fmt = file_format
        if fmt == "auto":
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".csv":
                fmt = "csv"
            elif ext == ".json":
                fmt = "json"
            elif ext in (".txt", ".text", ".md", ".prompt", ".prompts"):
                fmt = "txt_line"
            else:
                fmt = "txt_line"  # sensible fallback

        try:
            if fmt == "csv":
                imported, skipped, errors = self.db.import_from_csv(
                    file_path=file_path,
                    category=default_category,
                    platform=default_platform,
                    tags=default_tags,
                    skip_duplicates=skip_duplicates,
                )
            elif fmt == "json":
                imported, skipped, errors = self.db.import_from_json(
                    file_path=file_path,
                    category=default_category,
                    platform=default_platform,
                    tags=default_tags,
                    skip_duplicates=skip_duplicates,
                )
            elif fmt == "txt_paragraph":
                imported, skipped, errors = self.db.import_from_text_file(
                    file_path=file_path,
                    category=default_category,
                    platform=default_platform,
                    tags=default_tags,
                    delimiter="double_newline",
                    skip_duplicates=skip_duplicates,
                )
            else:  # txt_line
                imported, skipped, errors = self.db.import_from_text_file(
                    file_path=file_path,
                    category=default_category,
                    platform=default_platform,
                    tags=default_tags,
                    delimiter="newline",
                    skip_duplicates=skip_duplicates,
                )

            stats = self.db.stats()
            status = (
                f"Imported {imported} prompts, skipped {skipped} | "
                f"DB total: {stats['total_prompts']} prompts"
            )
            error_text = "\n".join(errors) if errors else ""

            logger.info(f"Import complete: {imported} added, {skipped} skipped from {file_path}")
            return (imported, skipped, status, error_text)

        except Exception as e:
            logger.error(f"Import error: {e}")
            return (0, 0, f"Import failed: {e}", str(e))
