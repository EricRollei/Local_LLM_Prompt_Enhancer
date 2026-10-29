"""
Ideogram 4 Magic Prompt node.

Expands a plain-language idea (optionally guided by a reference image) into an
Ideogram 4 structured caption JSON, using a local LLM via LLMBackend and
Ideogram's official open-source magic-prompt system prompt.

Outputs:
  prompt_json : structured caption (minified JSON) - wire to an Ideogram sampler,
                or into the Ideogram 4 Composer's JSON import to refine on the canvas.
  high_level  : the high_level_description text (e.g. to feed the Composer's input).
  width/height: pixel dims from the committed aspect ratio x megapixels.
  report      : status + any guideline warnings.

Author: Eric Hiss (GitHub: EricRollei). System prompt: Apache-2.0, ideogram-oss.
"""

import io
import numpy as np

from . import ideogram_magic_core as core
from .llm_backend import LLMBackend
from .wildcard_support import (
    is_changed_token,
    llm_block,
    normalise_seed,
    report_lines,
    resolve_wildcards,
    filter_notes_of,
    lead_with_filter_notes,
    screen_output,
    wildcard_nsfw_input,
    wildcard_optional_inputs,
)

REF_INSTRUCTIONS = {
    "full": "Describe this reference image in detail: subjects, setting, composition, colors, lighting, and mood.",
    "style_only": "Describe ONLY the visual style, medium, lighting, and mood of this image - not the specific subjects or scene content.",
    "palette_only": "List the dominant colors of this image as a short palette (color names and approximate #RRGGBB hex), plus the overall color mood. Ignore subjects and composition.",
    "subject_only": "Describe ONLY the main subject(s) in this image - appearance, clothing, pose, distinguishing features - not the background, style, or lighting.",
}

# Application labels (keep in sync with web/ideogram_magic.js templates). Picking one
# prefills the idea box (UI) and nudges the expander toward that format.
APPLICATIONS = [
    "(custom)", "Portrait (photo)", "Product (photo)", "Lifestyle flat-lay (photo)",
    "Fashion editorial (photo)", "Logo", "Event poster", "Vintage travel poster",
    "Movie one-sheet", "T-shirt design", "Packaging / label", "Instagram post",
    "YouTube thumbnail", "Book cover", "Album cover", "Editorial illustration",
    "Comic / manga panel", "Infographic", "Business card", "Sticker",
    "Sign / storefront", "Greeting card", "Menu",
]


class IdeogramMagicPrompt:
    CATEGORY = "Eric Prompt Enhancers/Ideogram"
    FUNCTION = "run"
    RETURN_TYPES = ("STRING", "STRING", "INT", "INT", "STRING")
    RETURN_NAMES = ("prompt_json", "high_level", "width", "height", "report")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "idea": ("STRING", {"multiline": True, "default": "",
                                    "tooltip": "Plain-language idea to expand into an Ideogram 4 caption."}),
                "application": (APPLICATIONS, {"default": "(custom)",
                                "tooltip": "Pick a use case to prefill the idea box with a starter template and steer the expander toward that format."}),
                "backend": (["lm_studio", "ollama", "qwen3_vl"], {"default": "lm_studio"}),
                "endpoint": ("STRING", {"default": "http://localhost:1234/v1",
                                        "tooltip": "LM Studio / Ollama base URL. For qwen3_vl, optionally a local model path."}),
                "model": ("STRING", {"default": "", "tooltip": "Blank = auto-detect the loaded model."}),
                "temperature": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "aspect_ratio": ("STRING", {"default": "auto",
                                            "tooltip": "W:H (e.g. 16:9) or 'auto' to let the model pick."}),
                "megapixels": ("FLOAT", {"default": 1.0, "min": 0.25, "max": 4.0, "step": 0.25,
                                         "tooltip": "Total output resolution; combined with the aspect ratio to set width/height."}),
                "keep_bboxes": ("BOOLEAN", {"default": True,
                                            "tooltip": "Keep element bounding boxes (for the Composer canvas). Off = let Ideogram place freely."}),
                "use_tailoring": ("BOOLEAN", {"default": True,
                                              "tooltip": "Apply Eric's documented tailoring addendum on top of the official prompt. See IDEOGRAM_NOTES.md."}),
                "max_tokens": ("INT", {"default": 16384, "min": 1024, "max": 32768}),
            },
            "optional": {
                "reference_image": ("IMAGE",),
                "reference_influence": (["full", "style_only", "palette_only", "subject_only"],
                                        {"default": "full",
                                         "tooltip": "How a connected reference image guides the caption (needs a vision-capable backend)."}),
                # New inputs are only ever APPENDED below this line, so saved workflows keep their widget order.
                **wildcard_optional_inputs(),
                **wildcard_nsfw_input(),
            },
        }

    @classmethod
    def IS_CHANGED(cls, wildcard_seed=-1, **kwargs):
        """wildcard_seed = -1 means a fresh roll each run, which must defeat ComfyUI's cache."""
        return is_changed_token(wildcard_seed)

    def run(self, idea, backend, endpoint, model, temperature, aspect_ratio,
            megapixels, keep_bboxes, use_tailoring, max_tokens,
            application="(custom)", reference_image=None, reference_influence="full",
            wildcard_seed=-1, wildcard_llm_block=True, wildcard_instructions="", nsfw="off",
            violence_filter="off"):

        # Resolve wildcards in the idea (core/wildcards). The parser leaves JSON braces alone.
        wildcard_resolution = resolve_wildcards(idea or "", seed=normalise_seed(wildcard_seed), legacy=True,
                                                upstream_instructions=wildcard_instructions, nsfw=nsfw,
                                                violence_filter=violence_filter)
        idea = wildcard_resolution.text

        if not (idea or "").strip() and reference_image is None:
            return ("", "", 0, 0, "Empty idea - nothing to expand.")

        ref_caption = ""
        if reference_image is not None:
            ref_caption = self._caption_reference(
                reference_image, reference_influence, backend, endpoint, model, temperature)

        r = core.expand(
            idea or "", backend=backend, endpoint=endpoint, model=model,
            temperature=temperature, aspect_ratio=aspect_ratio, megapixels=megapixels,
            keep_bboxes=keep_bboxes, use_tailoring=use_tailoring, max_tokens=max_tokens,
            reference_caption=ref_caption, application=application,
            extra_system=llm_block(wildcard_resolution, wildcard_llm_block),
        )

        if not r["ok"]:
            report = f"\u26a0 {r['error']}"
            print(f"[Ideogram Magic] {report}")
            return (r.get("prompt_json", ""), "", 0, 0, report)

        warns = r.get("warnings", [])
        report = ("\u2713 caption generated" if not warns else "\u26a0 " + "; ".join(warns))
        report += f"  [{r.get('aspect')}, {r['width']}\u00d7{r['height']}]"
        wildcard_report = report_lines(wildcard_resolution)
        if wildcard_report:
            report = f"{report}\n{wildcard_report}"
        print(f"[Ideogram Magic] {report}")
        caption, caption_note = screen_output(r["prompt_json"], "Ideogram Magic caption")
        summary, summary_note = screen_output(r["high_level"], "Ideogram Magic summary")
        report = lead_with_filter_notes(report, filter_notes_of(wildcard_resolution, caption_note, summary_note))
        if caption_note or summary_note:
            return ("", "", r["width"], r["height"], report)
        return (caption, summary, r["width"], r["height"], report)

    def _caption_reference(self, image, influence, backend, endpoint, model, temperature):
        try:
            from PIL import Image
            arr = image[0].detach().cpu().numpy()
            arr = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
            if arr.ndim == 2:
                arr = np.stack([arr] * 3, -1)
            buf = io.BytesIO()
            Image.fromarray(arr[..., :3]).save(buf, format="PNG")
            be = LLMBackend(backend, endpoint, model or None, temperature)
            if not be.supports_images():
                print("[Ideogram Magic] Reference image ignored: backend/model is not vision-capable.")
                return ""
            res = be.caption_image(buf.getvalue(), label="reference",
                                   prompt=REF_INSTRUCTIONS.get(influence, REF_INSTRUCTIONS["full"]))
            if res.get("success"):
                return res.get("caption", "") or ""
            print(f"[Ideogram Magic] Reference caption failed: {res.get('error')}")
            return ""
        except Exception as e:
            print(f"[Ideogram Magic] Reference caption error: {e}")
            return ""
