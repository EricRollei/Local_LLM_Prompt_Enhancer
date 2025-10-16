# LM Studio Configuration Guide for Prompt Expansion

## Quick Setup (5 Minutes)

### 1. Load a Good Model

**Recommended models for prompt expansion:**

**Best (Most capable):**
- `Meta-Llama-3.1-8B-Instruct` - Great instruction following
- `Qwen2.5-7B-Instruct` - Excellent at detailed descriptions
- `Mistral-7B-Instruct-v0.3` - Good balance of speed and quality

**Good (Faster):**
- `Meta-Llama-3-8B-Instruct` - Solid, widely compatible
- `Phi-3-medium-4k-instruct` - Good for shorter prompts

**Avoid:**
- Base models (non-instruct versions)
- Very small models (< 7B parameters)
- Chat-tuned models optimized for conversation rather than instruction following

### 2. Configure Server Settings

In LM Studio, go to **Local Server** tab:

#### A. Context Length
**Setting:** Context Length / Max Context
**Recommended:** `8192` or higher
**Why:** Our prompts can be long (especially cinematic tier)

```
Low context (2048) = May cut off instructions ❌
Good context (8192) = Handles all tiers comfortably ✅
High context (16384+) = Overkill but works ✅
```

#### B. GPU Layers
**Setting:** GPU Offload / GPU Layers
**Recommended:** As many as your GPU can handle
**Why:** Faster generation = better experience

```
CPU only (0 layers) = Very slow but works
Partial GPU (20-30 layers) = Good balance
Full GPU (all layers) = Fastest ✅
```

#### C. Server Configuration
**Setting:** Server Port
**Default:** `1234`
**Our node expects:** `http://localhost:1234/v1`

✅ Keep default unless you have a conflict

## Temperature Settings

**Temperature is CRITICAL for instruction following!**

### In ComfyUI Node:
You control temperature in the node interface (0.1 - 2.0)

### Recommended Temperatures:

| Use Case | Temperature | Why |
|----------|-------------|-----|
| **Maximum detail** | 0.3 - 0.5 | LLM follows instructions precisely |
| **Balanced** | 0.6 - 0.8 | Good creativity + instruction following |
| **Creative/Random** | 0.9 - 1.2 | More unexpected choices |
| **Wild experiments** | 1.3 - 2.0 | Very unpredictable |

**For prompt expansion, start with 0.6-0.7**

### What Temperature Does:

**Low (0.3):**
- Follows word count requirements better
- More predictable output
- Less creative descriptions
- Better for specific cinematography terms

**Medium (0.7):**
- Good balance
- Still follows instructions
- More varied language
- **Recommended starting point**

**High (1.2+):**
- Very creative
- May ignore word counts
- May not use exact technical terms
- Good for "random" preset

## Advanced Settings (Optional)

### In LM Studio Local Server:

#### 1. Repeat Penalty
**Setting:** Repeat Penalty / Repetition Penalty
**Recommended:** `1.1` to `1.15`
**Why:** Prevents repetitive descriptions

```
Too low (1.0) = May repeat same adjectives
Good (1.1) = Varied language ✅
Too high (1.3+) = May avoid important terms
```

#### 2. Top P (Nucleus Sampling)
**Setting:** Top P
**Recommended:** `0.9` to `0.95`
**Why:** Controls randomness

```
Lower (0.8) = More focused
Default (0.95) = Good balance ✅
Higher (0.99) = More random
```

#### 3. Top K
**Setting:** Top K
**Recommended:** `40` to `50`
**Why:** Limits vocabulary choices

```
Lower (20) = More predictable
Default (40-50) = Good ✅
Higher (100) = More varied
```

## System Prompt (DO NOT SET IN LM STUDIO)

**Important:** Our ComfyUI node sends the system prompt automatically!

❌ **Do NOT set a system prompt in LM Studio's "System Prompt" field**

Why?
- Our node sends detailed instructions already
- LM Studio's system prompt would conflict
- Could confuse the model

**Leave LM Studio's system prompt EMPTY** or use the default.

## Model-Specific Tips

### For Llama 3 / 3.1:
```
Context: 8192+
Temperature: 0.6-0.7
Repeat Penalty: 1.1
Works great with all presets ✅
```

### For Qwen:
```
Context: 8192+
Temperature: 0.5-0.7
Repeat Penalty: 1.05-1.1
Excellent at descriptive detail ✅
May need lower temperature for instruction following
```

### For Mistral:
```
Context: 8192+
Temperature: 0.7-0.8
Repeat Penalty: 1.1
Good balance of speed and quality ✅
```

### For Phi-3:
```
Context: 4096+ (has lower context)
Temperature: 0.6
Repeat Penalty: 1.1
Faster but may struggle with cinematic tier
Best for basic/enhanced tiers
```

## Troubleshooting

### Problem: Output Too Short

**Solutions:**
1. Lower temperature (try 0.4-0.5)
2. Use better model (Llama 3.1 > Llama 3 > smaller models)
3. Increase context length to 8192+
4. Try different model altogether

**Test:**
```
Input: "cat playing piano"
Tier: advanced
Temperature: 0.5
Expected: 400-600 words minimum
```

### Problem: LLM Not Following Instructions

**Solutions:**
1. Lower temperature to 0.5 or less
2. Use instruct-tuned model (must have "Instruct" in name)
3. Check you're not setting conflicting system prompt in LM Studio
4. Try different model

**Test:**
```
Input: "robot in city"
Preset: random
Expected: Output mentions "robot" and "city"
If not: Model not following instructions
```

### Problem: Output Ignores Aesthetic Controls (Advanced Node)

**Solutions:**
1. Lower temperature (0.4-0.6)
2. Use Llama 3.1 or Qwen (better instruction following)
3. Try "advanced" or "cinematic" tier
4. Check model is instruct-tuned

**Test:**
```
Input: "spaceship flying"
Shot Size: wide shot
Lighting: edge lighting
Expected: Output must mention "wide shot" and "edge lighting"
```

### Problem: Repeating Same Phrases

**Solutions:**
1. Increase repeat penalty to 1.15-1.2
2. Increase temperature slightly (0.7-0.8)
3. Generate multiple variations

### Problem: Wrong Format / Echoing Input

**Solutions:**
1. Lower temperature (0.5)
2. Use newer model (Llama 3.1, Qwen 2.5)
3. Check node is using latest version with better parsing
4. Try different model

## Performance Settings

### For Speed:
```
✅ Use quantized models (Q4_K_M or Q5_K_M)
✅ Full GPU offload
✅ Lower context (4096-8192)
✅ Batch size: 512
⚠️ Avoid F16/F32 models (slower)
```

### For Quality:
```
✅ Use Q6_K or higher quantization
✅ Higher context (16384)
✅ Lower temperature (0.5-0.6)
✅ Better models (Llama 3.1, Qwen 2.5)
```

### For Batch Generation:
```
✅ Use Q4_K_M quantization (faster)
✅ Temperature 0.7-0.8 (variety)
✅ Generate 3 variations per run
✅ Use wildcards for more variety
```

## Optimal Configuration (Recommended Starting Point)

```yaml
Model: Meta-Llama-3.1-8B-Instruct-Q5_K_M
Context Length: 8192
GPU Layers: Maximum available
Temperature: 0.7 (set in ComfyUI node)
Repeat Penalty: 1.1
Top P: 0.95
Top K: 40
System Prompt: EMPTY (let ComfyUI node handle it)
```

**In ComfyUI Node:**
```
llm_backend: lm_studio
model_name: llama3.1
api_endpoint: http://localhost:1234/v1
temperature: 0.7
```

## Testing Your Setup

### Quick Test Script:

1. **Start LM Studio** with recommended settings
2. **In ComfyUI**, use this test:

```
Input: "cat playing piano"
Preset: cinematic
Tier: advanced
Temperature: 0.6
Expected: 400-600 words, mentions cat, piano, professional cinematography terms
```

3. **Check output length:**
   - < 200 words = Model not following instructions
   - 200-400 words = Okay, but try lower temperature
   - 400+ words = Good! ✅

4. **Check quality:**
   - Mentions subject (cat, piano)? ✅
   - Uses cinematography terms? ✅
   - Flows naturally? ✅
   - Detailed descriptions? ✅

## Model Download Tips

### Where to Get Models:

**In LM Studio:**
1. Click Search icon (🔍)
2. Search for "Llama-3.1-8B-Instruct"
3. Download Q5_K_M or Q4_K_M version
4. Wait for download
5. Load model in Local Server tab

**Recommended downloads:**
```
Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf (6GB)
or
Meta-Llama-3-8B-Instruct-Q5_K_M.gguf (6GB)
```

**For faster generation (if GPU limited):**
```
Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf (4.5GB)
```

## Summary Checklist

Before using the prompt expansion node:

- [ ] Good model loaded (Llama 3.1 or Qwen 2.5)
- [ ] Context length: 8192+
- [ ] GPU layers: Maximum
- [ ] Server running on port 1234
- [ ] System prompt: EMPTY in LM Studio
- [ ] Temperature: 0.6-0.7 (in ComfyUI node)

**Then test:**
- [ ] Generate a prompt
- [ ] Check it's 400+ words (for advanced tier)
- [ ] Verify it mentions your input concept
- [ ] Confirm cinematography terms are used

## Getting Help

If things still aren't working:

1. **Check LM Studio console** for errors
2. **Check ComfyUI console** for errors
3. **Try the absolute simplest test:**
   - Input: "cat"
   - Tier: basic
   - Temperature: 0.5
   - Should get 150+ words about a cat

4. **Model issues?**
   - Try different model
   - Llama 3.1 is most reliable
   - Qwen 2.5 is best for detail

5. **Still problems?**
   - Check model is "Instruct" version
   - Verify server is running
   - Test with curl or another client

---

**Quick Start:** Load Llama 3.1, set context to 8192, leave system prompt empty, use temperature 0.7 in the node. That's it!
