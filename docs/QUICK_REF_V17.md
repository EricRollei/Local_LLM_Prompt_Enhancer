# Text-to-Image Node v1.7 - Quick Reference

## What's New

### 🔧 Fixed
- **Reference Images**: Now properly analyzed and incorporated into prompts
  - Analyzes: dimensions, brightness, color tones
  - LLM receives detailed characteristics to match

### ✨ New Controls

#### Prompt Length
Control the output size:
- `very_short` - 20-40 tokens (minimal)
- `short` - 40-80 tokens (SDXL)
- `medium` - 80-150 tokens (Flux)
- `long` - 150-250 tokens (complex)
- `very_long` - 250-400 tokens (maximum detail)

#### Genre/Style
Infuse prompts with specific mood:
- Creative: `surreal`, `cinematic`, `dramatic`, `action`, `artistic`
- Horror: `horror`, `noir`
- Tech: `scifi`, `cyberpunk`
- Mood: `humorous`, `romantic`, `indie`
- Era: `vintage`, `modern`
- Content: `pg`, `x-rated`
- Aesthetic: `minimalist`, `maximalist`, `documentary`

#### Subject Framing
Control the shot composition:
- `extreme close-up` - Facial details
- `close-up` - Face and shoulders
- `medium shot` - Waist up
- `wide shot` - Full body with environment
- `full body` - Complete subject
- `cowboy shot` - Mid-thigh up
- Plus: `bust shot`, `head and shoulders`, `three-quarter`

#### Subject Pose
Control character positioning:
- Static: `standing`, `sitting`, `lying down`, `kneeling`
- Dynamic: `action pose`, `walking`, `running`, `jumping`, `dancing`
- Portrait: `portrait pose`, `contrapposto`, `asymmetric`
- Energy: `relaxed`, `tense`, `dynamic`, `static`

---

## Quick Examples

### Example 1: Cinematic Portrait
```
Prompt: "woman in evening dress"
Genre: cinematic
Length: medium
Framing: close-up
Pose: contrapposto
```
→ Film-quality portrait, dramatic lighting, classic pose

### Example 2: Horror Scene
```
Prompt: "abandoned mansion"
Genre: horror
Length: long
Framing: wide shot
```
→ Detailed atmospheric horror with ominous mood

### Example 3: Action Shot
```
Prompt: "superhero"
Genre: action
Length: short
Framing: wide shot
Pose: dynamic
```
→ Fast-paced, energetic, movement-focused

### Example 4: Cyberpunk Character
```
Prompt: "{male|female} hacker"
Genre: cyberpunk
Length: medium
Framing: medium shot
Pose: asymmetric
```
→ Neon, tech, gritty urban dystopia aesthetic

---

## Pro Tips

### Reference Images
- Use clear, well-lit references for best results
- Color/lighting characteristics transfer well
- Works with any ComfyUI-compatible image format

### Combining Features
- Alternation `{a|b|c}` + Emphasis `(keyword:1.5)` + Genre + Framing = powerful control
- All features work together seamlessly
- Random options provide variety across generations

### Platform Specific
- **SDXL**: Use `short` length, works with all genres
- **Flux**: `medium` length, natural language excels
- **Pony**: Any length converts to tags, genres adapt
- **Chroma**: `long` or `very_long` for complex scenes

### Length vs Detail
- **Shorter** = focused, concise, faster to generate
- **Longer** = complex scenes, multiple subjects, rich atmosphere
- Match length to scene complexity

---

## All New Inputs

| Input | Options | Default |
|-------|---------|---------|
| `genre_style` | 22 options | `auto` |
| `prompt_length` | 6 options | `auto` |
| `subject_framing` | 14 options | `auto` |
| `subject_pose` | 17 options | `auto` |

All support:
- `auto` - Intelligent defaults
- `random` - Variety across generations
- `none` - Disable the control
- Specific values for precise control

---

## Testing Checklist

- [ ] Reference image incorporated (check output mentions image characteristics)
- [ ] Prompt length matches target (count tokens ~words × 1.3)
- [ ] Genre style reflected (vocabulary/tone matches)
- [ ] Framing mentioned (shot type present)
- [ ] Pose described (body position clear)
- [ ] All features work together
- [ ] Platform formatting correct
- [ ] Emphasis syntax preserved `(keyword:1.5)`
- [ ] Alternation processed `{a|b|c}`
- [ ] No settings leakage in output

---

## Restart Required

**After update, restart ComfyUI completely to load new controls!**

---

## Files Updated
- `text_to_image_node.py` - Core functionality
- `UPDATE_V17_ENHANCED_CONTROLS.md` - Full documentation
- This file - Quick reference

**Version:** 1.7  
**Status:** ✅ Ready to use  
**Compatibility:** ✅ All existing workflows work
