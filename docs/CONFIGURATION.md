# Configuration Examples for AI Video Prompt Expander

## LM Studio Configuration
```
Backend: lm_studio
Endpoint: http://localhost:1234/v1
Model: llama3 (or whatever model you have loaded)
Temperature: 0.7 (recommended for balanced creativity)
```

## Ollama Configuration  
```
Backend: ollama
Endpoint: http://localhost:11434/api
Model: llama3 (or llama3.1, mistral, etc.)
Temperature: 0.7
```

## Remote LLM (if running on another machine)
```
Backend: lm_studio or ollama
Endpoint: http://192.168.1.100:1234/v1 (replace with your IP)
Model: [your model name]
Temperature: 0.7
```

## Local Qwen3-VL Vision Backend
```
Backend: qwen3_vl
Model: Qwen/Qwen3-VL-4B-Instruct@4bit (or local path)
Endpoint Overrides: quant=4bit;attn=sdpa;device=cuda:0
Temperature: 0.6 (captioning focused)
```
Set this backend inside the image-to-video or image-to-image nodes when you want to caption reference images without calling an HTTP server. Install `transformers`, `accelerate`, `huggingface_hub`, and (optionally) `bitsandbytes` beforehand.

## Preset Recommendations

### For Realistic Scenes
- Preset: **cinematic**
- Tier: **advanced** or **cinematic**
- Temperature: 0.5-0.7

### For Creative/Artistic Content
- Preset: **stylized** or **surreal**
- Tier: **enhanced** or **advanced**
- Temperature: 0.8-1.0

### For High-Energy Sequences
- Preset: **action**
- Tier: **advanced**
- Temperature: 0.6-0.8

### For Moody/Atmospheric
- Preset: **noir**
- Tier: **advanced** or **cinematic**
- Temperature: 0.5-0.7

### For Experimentation
- Preset: **random**
- Tier: **auto**
- Temperature: 1.0-1.5

## Temperature Guidelines

- **0.1-0.3**: Very focused, consistent, less creative
- **0.4-0.6**: Balanced, reliable, some creativity
- **0.7-0.9**: Creative, varied, good for exploration
- **1.0-1.5**: Highly creative, experimental, more random
- **1.5-2.0**: Very experimental, unpredictable

## Keyword Examples

### LoRA Triggers
```
Positive Keywords: myLoRA_style, detailed_face, high_quality
```

### Style Enforcement
```
Positive Keywords: cinematic, professional, 4k, high-end
```

### Character/Object Specific
```
Positive Keywords: red_hair, blue_eyes, leather_jacket
```

### Negative Keywords (Custom)
```
Negative Keywords: cartoonish, anime, illustration, painting
```

## Example Workflows

### Workflow 1: Quick Cinematic
```yaml
Basic Prompt: "woman walking in rain"
Preset: cinematic
Tier: auto (will detect "enhanced")
Variations: 1
Save: true
```

### Workflow 2: Multiple Style Variations
```yaml
Basic Prompt: "robot in futuristic city"
Preset: custom
Tier: advanced
Variations: 3
Save: true
```
Then manually try with different presets to compare.

### Workflow 3: Image-to-Video
```yaml
Basic Prompt: "slowly turns head and smiles"
Mode: image-to-video
Preset: cinematic
Tier: enhanced
Positive Keywords: [your lora trigger]
```

### Workflow 4: Action Sequence
```yaml
Basic Prompt: "superhero lands from sky"
Preset: action
Tier: cinematic
Temperature: 0.8
Variations: 2
```

## File Naming Strategies

### By Project
```
filename_base: project_alpha_scene01
filename_base: project_alpha_scene02
```

### By Style
```
filename_base: cinematic_city_night
filename_base: noir_detective_walk
```

### By Character
```
filename_base: character_hero_intro
filename_base: character_villain_reveal
```

## Tips for Best Results

1. **Let Auto-Detect Work**: The auto tier detection is quite good
2. **Start Small**: Begin with basic prompts and increase complexity as needed
3. **Use Presets**: They dramatically influence the output style
4. **Iterate**: Generate variations and pick the best
5. **Save Everything**: Build a library of good prompts for reference
6. **Keywords First**: Always include LoRA triggers in positive_keywords
7. **Temperature Matters**: Lower for consistency, higher for creativity
8. **Mode Matters**: image-to-video mode focuses on motion, not scene setup

## Troubleshooting Common Issues

### Prompts Too Long
- Lower the tier (cinematic → advanced → enhanced)
- Use more concise basic_prompt
- Some video models have token limits

### Not Enough Detail
- Increase tier (basic → enhanced → advanced)
- Use more descriptive basic_prompt
- Try higher temperature for more elaboration

### Keywords Not Included
- The node auto-appends missing keywords
- Check spelling and comma separation
- Verify in the output prompt

### Style Not Matching
- Try different presets
- Adjust temperature
- Add style terms to positive_keywords

### LLM Too Slow
- Use a smaller/faster model
- Reduce max_tokens (edit node if needed)
- Lower temperature slightly

## Model Recommendations

### Fast & Good Quality
- Llama 3 8B
- Mistral 7B

### Best Quality (Slower)
- Llama 3 70B
- Mixtral 8x7B

### Experimental
- Llama 3.1 variants
- Qwen models
- Custom fine-tuned models

## Integration with Video Nodes

The output connects directly to most video generation nodes:

```
[AI Video Prompt Expander]
    ↓ positive_prompt_1
[CogVideoX]
[Runway Gen-3]
[Pika Labs]
[Stable Video Diffusion]
    etc.
```

Remember to also connect the **negative_prompt** output!
