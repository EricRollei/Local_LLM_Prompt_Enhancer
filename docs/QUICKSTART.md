# Quick Start Guide

Get up and running with AI Video Prompt Expander in 5 minutes!

## Step 1: Install LLM Backend

### Option A: LM Studio (Recommended for Beginners)
1. Download from https://lmstudio.ai/
2. Install and open LM Studio
3. Go to "Models" tab → Search for "llama-3-8b"
4. Download a model (recommended: Meta-Llama-3-8B-Instruct)
5. Go to "Local Server" tab → Select your model → Click "Start Server"
6. Note the endpoint (default: http://localhost:1234)

### Option B: Ollama (Better for Advanced Users)
1. Download from https://ollama.ai/
2. Install Ollama
3. Open terminal/command prompt
4. Run: `ollama pull llama3`
5. Server starts automatically (endpoint: http://localhost:11434)

### Option C: Local Qwen3-VL Vision Backend (Optional)
Use this if you want the image-to-video or image-to-image nodes to caption images without calling LM Studio/Ollama.
1. Install Python packages: `pip install transformers accelerate huggingface_hub bitsandbytes`
2. Download a Qwen3-VL model (e.g., `Qwen/Qwen3-VL-4B-Instruct`)
3. In the node, set `vision_backend` to `qwen3_vl`
4. Set `vision_model_name` to the repo or local path (append `@4bit`/`@8bit` if desired)
5. Use the `vision_endpoint` field for optional overrides like `quant=4bit;attn=sdpa`

## Step 2: Verify Your LLM Backend

1. Confirm your server responds in a browser:
   - LM Studio: http://localhost:1234/v1
   - Ollama: http://localhost:11434
2. Make sure a model is loaded (LM Studio) or pulled (Ollama) and the server is running.

## Step 3: Restart ComfyUI

1. If ComfyUI is running, close it
2. Start ComfyUI
3. You should see the node load without errors

## Step 4: Add Node to Workflow

1. Right-click in ComfyUI → Add Node
2. Navigate to: **Eric Prompt Enhancers → Video Prompt Expander**
3. The node will appear with all inputs ready

## Step 5: Basic Usage

### Your First Prompt Expansion

**Simple Setup:**
```
basic_prompt: "A cat playing piano in a cozy room"
preset: cinematic
expansion_tier: auto
mode: text-to-video
llm_backend: lm_studio (or ollama)
model_name: llama3
api_endpoint: http://localhost:1234/v1 (LM Studio) or http://localhost:11434/api (Ollama)
temperature: 0.7
positive_keywords: (leave empty for now)
negative_keywords: (leave empty for now)
num_variations: 1
save_to_file: true
filename_base: my_first_prompt
```

**Click "Queue Prompt"**

The node will:
1. Connect to your LLM
2. Analyze your input
3. Expand it to a detailed cinematic prompt
4. Generate a negative prompt
5. Save everything to a file
6. Show status with file location

### Check Your Output

Look at the outputs:
- **positive_prompt_1**: Your enhanced prompt (connect to video generation)
- **negative_prompt**: Auto-generated negatives (connect to video generation)
- **status**: Shows success and file save location

Open the saved file in `ComfyUI/output/video_prompts/` to see the full breakdown!

## Step 6: Connect to Video Generation

```
[AI Video Prompt Expander]
    ↓ positive_prompt_1 → [Your Video Gen Node] → prompt
    ↓ negative_prompt → [Your Video Gen Node] → negative_prompt
```

Now generate your video!

## Common First-Time Issues

### "Cannot connect to LM Studio"
- Make sure LM Studio's server is running (green indicator)
- Check the endpoint matches (http://localhost:1234/v1)
- Try clicking "Test Connection" in LM Studio

### "Cannot connect to Ollama"
- Run `ollama serve` in terminal if needed
- Check if Ollama is running: `ollama list`
- Verify endpoint: http://localhost:11434/api

### "Model not found"
- In LM Studio: Make sure model is selected in Local Server tab
- In Ollama: Run `ollama list` to see available models
- Match the model_name exactly as shown

### Node doesn't appear in ComfyUI
- Restart ComfyUI completely
- Check for error messages in ComfyUI console
- Verify all files are in custom_nodes/video_prompter/

## Next Steps

Once you have basic expansion working:

1. **Try Different Presets**
   - Change preset to "noir", "action", "surreal"
   - See how dramatically the style changes

2. **Experiment with Tiers**
   - Compare "basic", "enhanced", "advanced", "cinematic"
   - See the detail increase with each tier

3. **Add Keywords**
   - If using LoRAs, add triggers to positive_keywords
   - Try style keywords like "professional, high-quality"

4. **Generate Variations**
   - Set num_variations to 2 or 3
   - Connect each output to different video gen nodes
   - Pick the best result

5. **Adjust Temperature**
   - Lower (0.3-0.5) for consistent style
   - Higher (0.8-1.2) for creative variations

## Example Workflows

### Workflow 1: Single Video
```
[AI Video Prompt Expander]
    ↓ (positive_prompt_1)
[CogVideoX Text2Video]
    ↓
[Save Video]
```

### Workflow 2: Multiple Variations
```
[AI Video Prompt Expander] (num_variations: 3)
    ↓ (positive_prompt_1) → [Video Gen] → [Save as version_1]
    ↓ (positive_prompt_2) → [Video Gen] → [Save as version_2]
    ↓ (positive_prompt_3) → [Video Gen] → [Save as version_3]
```

### Workflow 3: Image-to-Video
```
[Load Image]
    ↓
[AI Video Prompt Expander] (mode: image-to-video)
    ↓ (positive_prompt_1)
[Image2Video Node]
    ↓
[Save Video]
```

## Tips for Success

1. **Start Simple**: Let the node do the work
2. **Use Auto Tier**: It's smart about detecting complexity
3. **Save Prompts**: Build a library for reference
4. **Try Presets**: Each one is dramatically different
5. **Read Status**: It tells you exactly what happened
6. **Check Files**: Saved prompts include full breakdown

## Resources

- **Full Documentation**: See README.md
- **Configuration Guide**: See CONFIGURATION.md
- **Presets Reference**: See presets.py

## Getting Help

If something isn't working:

1. Check the **status** output - it shows errors clearly
2. Review your LLM backend connection
3. Check ComfyUI console for error messages
4. Verify model is loaded and endpoint is correct

## Success!

If you:
- ✅ See the node in ComfyUI
- ✅ Get a status message like "✅ Generated 1 variation(s)..."
- ✅ Have text in positive_prompt_1 output
- ✅ See a saved file in output/video_prompts/

**You're ready to create amazing video prompts!** 🎬

Now go make something awesome! 🚀
