# Vision Backend Guide

## Overview

The Text-to-Image Prompt Enhancer node now supports **three vision captioning backends** for analyzing reference images:

1. **Auto** (default) - Inherits from main LLM if it supports vision
2. **Qwen3-VL** - Local on-device vision model (no server needed)
3. **LM Studio / Ollama** - Use separate vision-capable LLM server

## Backend Options

### 1. Auto (Recommended for most users)

**What it does:**
- If your main LLM model supports vision (e.g., LLaVA, GPT-4 Vision), it will use that
- If your main LLM is text-only, vision captioning is disabled (falls back to heuristic analysis)

**When to use:**
- You're already running a vision-capable model in LM Studio/Ollama
- You want the simplest setup with no extra configuration

**What you need:**
- Nothing! Just select "auto" in the vision_backend dropdown

---

### 2. Qwen3-VL (Local, No Server Required)

**What it does:**
- Downloads and runs `Qwen/Qwen3-VL-4B-Instruct` directly on your GPU
- No LM Studio or Ollama server needed
- Fully integrated - just select and go

**When to use:**
- You want local vision captioning without running a separate LLM server
- You have ~8-16GB VRAM available for the vision model
- You want the best quality vision captions (Qwen3-VL is excellent at image description)

**What you need:**
1. Install the optional dependencies (if not already installed):
   ```bash
   pip install transformers>=4.41 torch torchvision Pillow huggingface-hub
   ```

2. **(Optional)** For quantization support (4-bit/8-bit to save VRAM):
   ```bash
   pip install bitsandbytes
   ```

3. Select `qwen3_vl` from the vision_backend dropdown

**First run behavior:**
- The model will auto-download to `ComfyUI/models/VLM/Qwen3-VL-4B-Instruct/`
- Download is ~9GB, happens once
- Subsequent runs load from disk (much faster)
- **Reuses models** from Granddyser nodes if already downloaded!

**Performance:**
- First inference: ~5-15 seconds (model loading)
- Subsequent inferences: ~2-5 seconds per image
- Memory: ~6-8GB VRAM (full precision), ~3-4GB (8-bit), ~2-3GB (4-bit)

---

### 3. LM Studio / Ollama (Separate Vision Model)

**What it does:**
- Uses the same LM Studio/Ollama endpoint as your main LLM
- Reuses the model name from your main LLM configuration
- Useful if you're running a vision model in LM Studio/Ollama

**When to use:**
- You're already running a vision-capable model server
- You want to explicitly specify LM Studio or Ollama for vision (even if main LLM is different)

**What you need:**
1. Run a vision-capable model in LM Studio or Ollama:
   - **LM Studio**: Load models like `llava`, `bakllava`, `moondream`, etc.
   - **Ollama**: `ollama run llava`, `ollama run bakllava`, etc.

2. Select `lm_studio` or `ollama` from the vision_backend dropdown

3. Make sure your **model_name** field matches your vision model

---

### 4. Disable

**What it does:**
- Turns off all vision captioning
- Reference images still analyzed using color/lighting heuristics
- Useful for testing or when you don't need detailed captions

**When to use:**
- Debugging or performance testing
- You only care about basic image statistics (colors, brightness, etc.)

---

## Usage Examples

### Example 1: Using Qwen3-VL (Simplest for quality captions)

```
vision_backend: qwen3_vl
```

That's it! No other fields needed. The node will:
- Auto-download Qwen3-VL-4B-Instruct if not present
- Load it into VRAM
- Generate detailed captions for your reference images

---

### Example 2: Using LM Studio with LLaVA

Main LLM settings:
```
llm_backend: lm_studio
model_name: llava-v1.6-mistral-7b
api_endpoint: http://localhost:1234/v1
```

Vision settings:
```
vision_backend: auto  (will detect LLaVA supports vision and use it automatically)
```

Or explicitly:
```
vision_backend: lm_studio
```

---

### Example 3: Mixed setup (Ollama for main LLM, Qwen3-VL for vision)

Main LLM settings:
```
llm_backend: ollama
model_name: llama3.1
api_endpoint: http://localhost:11434
```

Vision settings:
```
vision_backend: qwen3_vl  (uses local Qwen3-VL instead of Ollama)
```

---

## Troubleshooting

### "Vision backend init failed"
- Make sure your LM Studio/Ollama server is running
- Verify the endpoint URL is correct
- Check that the model name matches what's loaded in the server

### "Model does not advertise image support"
- Your selected model is text-only
- Switch to `qwen3_vl` or load a vision-capable model

### Qwen3-VL fails to load
- Check you have the required dependencies installed
- Verify you have enough VRAM (~6-8GB minimum)
- Check console for detailed error messages

### Slow performance with Qwen3-VL
- First run always slower (model loading)
- Consider using quantization (install `bitsandbytes`)
- Model stays loaded in memory between runs (faster subsequent uses)

---

## Advanced: Qwen3-VL Quantization

If you need to save VRAM, you can force quantization by modifying `qwen3_vl_backend.py` defaults, but currently the node uses auto-precision (lets Transformers decide based on available VRAM).

For 4-bit/8-bit quantization, ensure `bitsandbytes` is installed:
```bash
pip install bitsandbytes
```

---

## Model Download Locations

- **Qwen3-VL**: `ComfyUI/models/VLM/Qwen3-VL-4B-Instruct/`
- Downloads happen automatically on first use
- **Compatible with Granddyser nodes**: Uses the same location, so models are shared!
- You can pre-download using:
  ```python
  from huggingface_hub import snapshot_download
  snapshot_download("Qwen/Qwen3-VL-4B-Instruct", local_dir="ComfyUI/models/VLM/Qwen3-VL-4B-Instruct")
  ```

---

## Recommendations

- **For quality captions**: Use `qwen3_vl` - it's specifically trained for visual understanding
- **For speed**: Use `auto` with a fast vision model in LM Studio/Ollama
- **For low VRAM**: Use `auto` with Ollama (runs vision model on CPU if needed)
- **For no dependencies**: Stick with `disable` and use heuristic analysis

---

## Credits

Qwen3-VL integration inspired by [Granddyser's qwen3-vl-comfy-ui nodes](https://github.com/Granddyser/qwen3-vl-comfy-ui).
