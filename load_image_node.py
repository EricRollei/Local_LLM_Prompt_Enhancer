
import os
import json
from PIL import Image, ImageOps
import torch
import numpy as np
try:
    import folder_paths
except ImportError:
    folder_paths = None

class EricLoadImageWithPrompt:
    """
    Loads an image and extracts generation metadata (prompt) if available.
    Supports standard ComfyUI image loading + metadata extraction.
    """
    
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True})
            }
        }

    CATEGORY = "Eric Prompt Enhancers"
    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("IMAGE", "MASK", "PROMPT_TEXT")
    FUNCTION = "load_image"

    def load_image(self, image):
        image_path = folder_paths.get_annotated_filepath(image)
        
        i = Image.open(image_path)
        i = ImageOps.exif_transpose(i)
        image = i.convert("RGB")
        
        # Process image for ComfyUI (Tensor)
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        
        # Create mask
        if 'A' in i.getbands():
            mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask)
        else:
            mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")
            
        # Extract Metadata
        prompt_text = ""
        
        # 1. Try standard PNG info (parameters/Comment)
        # A1111 stores generation info in 'parameters'
        if i.info:
            if 'parameters' in i.info:
                prompt_text = i.info['parameters']
            elif 'Comment' in i.info:
                # Some software uses Comment
                try:
                    # Try to parse JSON if it looks like it
                    comment = i.info['Comment']
                    if comment.strip().startswith('{'):
                        data = json.loads(comment)
                        prompt_text = data.get('prompt', comment)
                    else:
                        prompt_text = comment
                except:
                    prompt_text = i.info['Comment']
            
            # 2. Try ComfyUI workflow metadata (often in 'workflow' or 'prompt')
            # This is complex because it's the whole graph. We try to find a primitive string or positive prompt.
            # For now, we'll stick to the text-based 'parameters' which is the standard for sharing prompts.
            
        # Clean up A1111 'parameters' block to get just the positive prompt
        # Usually it's: "Positive Prompt\nNegative Prompt: ...\nSteps: ..."
        if prompt_text and "Negative prompt:" in prompt_text:
            prompt_text = prompt_text.split("Negative prompt:")[0].strip()
        elif prompt_text and "Steps:" in prompt_text:
             prompt_text = prompt_text.split("Steps:")[0].strip()
             
        return (image, mask, prompt_text)

    @classmethod
    def IS_CHANGED(s, image):
        image_path = folder_paths.get_annotated_filepath(image)
        m = os.path.getmtime(image_path)
        return m
