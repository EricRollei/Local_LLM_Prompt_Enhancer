# Version 1.3 Update - Fixed Random + NEW Wildcards!

## What's New

### 1. ✅ FIXED: Random Preset Now Uses Your Input
**Before:** Random preset generated completely unrelated content  
**After:** Random takes YOUR concept and applies random aesthetics to it

**Example:**
```
Input: "cat playing piano"
Preset: random

Before (WRONG): Generated something totally unrelated
After (CORRECT): "A fluffy orange tabby cat sits at a polished grand piano..." 
                 + random lighting, camera angles, color tones applied
```

### 2. ✅ FIXED: Advanced Node Random Respects Dropdowns
**Before:** Random ignored all your dropdown selections  
**After:** Random respects your selections, only randomizes "auto" ones

**Example:**
```
Input: "detective in office"
Preset: random
Shot Size: medium shot (YOU specified)
Lighting: auto (will randomize)
Camera Angle: low angle shot (YOU specified)

Result:
- MUST use medium shot ✅
- MUST use low angle shot ✅  
- Lighting randomized (maybe "edge lighting")
- Other auto elements randomized
- Core concept: detective in office preserved!
```

### 3. 🆕 NEW: Wildcard Support!

Create dynamic prompts with random variations!

**Syntax:**
```
{category:option1|option2|option3}
```

**Example:**
```
A {animal:cat|dog|bird} playing {instrument:piano|guitar|drums}
```

**Generates random combinations:**
- "A cat playing piano"
- "A dog playing guitar"
- "A bird playing drums"
- Etc.

## Wildcard Examples

### Basic Usage
```
Input: A {profession:detective|chef|scientist} in their {location:office|kitchen|lab}
Result: Random profession + random location
```

### With Presets
```
Input: A {animal} {action:running|flying|swimming}
Preset: cinematic
Result: Random animal doing random action, with cinematic aesthetics
```

### With Advanced Node
```
Input: A {vehicle:car|motorcycle|truck} in motion
Shot Size: wide shot
Camera Movement: tracking shot
Preset: action
Result: Random vehicle, but YOUR specified cinematography
```

### Predefined Categories
```
Input: A {person} using a {tool} to fix a {object}
```

**Built-in categories:**
- {animal}, {person}, {profession}, {instrument}
- {location}, {weather}, {time}, {emotion}
- {action}, {color}, {vehicle}, {tool}, {object}

See `WILDCARD_GUIDE.md` for complete list!

## How Random Preset Works Now

**Old Way (BROKEN):**
```
Input: "robot in city"
Preset: random
Result: Something completely unrelated ❌
```

**New Way (FIXED):**
```
Input: "robot in city"  
Preset: random
Result: "A sleek metallic robot with glowing blue circuits walks through a neon-lit city..."
        + random shot size (maybe "medium shot")
        + random lighting (maybe "mixed lighting")
        + random camera angle (maybe "low angle shot")
        + random color tone (maybe "saturated colors")
        ✅ Robot and city preserved!
```

## Random + Advanced Node

**Standard Node + Random:**
- Takes your input
- Applies fully random aesthetics

**Advanced Node + Random:**
- Takes your input
- Respects your dropdown selections
- Only randomizes the "auto" ones

**Example:**
```
Standard Node:
Input: "spaceship flying"
Preset: random
→ Everything randomized

Advanced Node:
Input: "spaceship flying"
Preset: random
Shot Size: wide shot (locked)
Lighting: auto (will randomize)
Lens: telephoto lens (locked)
Camera Movement: auto (will randomize)
→ Only "auto" elements randomized
```

## Breakdown Output Shows Everything

The breakdown now displays:

**For Random Preset:**
```
Applied Preset: random

Random Elements Applied:
- Lighting Quality: edge lighting
- Time of Day: dusk time
- Shot Sizes: medium close-up shot
- Camera Movement: tracking shot

User-Specified Controls (Advanced Node):
- Lens: telephoto lens
- Shot Size: wide shot
```

**For Wildcards:**
```
Original Input:
A {animal:cat|dog|bird} playing {instrument}

Wildcard Replacements:
- animal: cat (from: cat|dog|bird)
- instrument: piano (predefined)

Processed Prompt:
A cat playing piano
```

## Testing the Fixes

### Test 1: Random with Input
```
Input: "wizard casting spell"
Preset: random
Tier: enhanced

Expected:
- Output mentions wizard ✅
- Output mentions casting spell ✅
- Random cinematography applied ✅
- NOT something unrelated ✅
```

### Test 2: Advanced Node Random
```
Input: "car chase"
Preset: random
Shot Size: wide shot
Camera Movement: tracking shot
Everything else: auto

Expected:
- "wide shot" in output ✅
- "tracking shot" or "tracking" in output ✅
- Random lighting/color/time ✅
```

### Test 3: Wildcards
```
Input: "A {animal:cat|dog} playing {instrument:piano|guitar}"
Variations: 3

Expected:
- Variation 1: Maybe "cat" + "piano"
- Variation 2: Maybe "dog" + "guitar"
- Variation 3: Maybe "cat" + "guitar"
- Each different! ✅
```

## Files Modified

1. ✅ `expansion_engine.py` - Fixed random logic + added wildcards
2. ✅ `WILDCARD_GUIDE.md` - Complete wildcard documentation
3. ✅ `UPDATE_V13.md` - This file

## Restart Required

**YES - Restart ComfyUI** to load:
- Fixed random preset behavior
- Wildcard support
- Updated breakdown display

## Quick Start

### Try Random Fix:
```
Input: "robot in futuristic city"
Preset: random
Tier: advanced
```

Should get: Robot + city + random cinematography (NOT unrelated content)

### Try Wildcards:
```
Input: "A {animal:cat|dog|fox} in a {location:forest|city|desert}"
Preset: cinematic
Tier: enhanced
Variations: 3
```

Should get: 3 different animal/location combos with cinematic style

### Try Both:
```
Input: "A {profession} using a {tool}"
Preset: random
Tier: advanced
```

Should get: Random profession/tool + random cinematography!

## Summary

**Version 1.3 delivers:**
- ✅ Fixed random preset (uses your input!)
- ✅ Fixed advanced node random (respects dropdowns!)
- 🆕 Wildcard support for dynamic prompts!
- ✅ Better breakdown showing what was selected
- ✅ All previous fixes intact

**Key improvement:** "Random" now means "random AESTHETICS applied to YOUR concept", not "random unrelated prompt"!

---

**Ready to test!**
1. Restart ComfyUI
2. Try random preset with your own concept
3. Try wildcards: `{animal:cat|dog|bird}`
4. Try advanced node random with some dropdowns set
5. Check `WILDCARD_GUIDE.md` for more examples!
