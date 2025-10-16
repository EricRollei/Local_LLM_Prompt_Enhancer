# Testing Guide for v1.6.1 Bug Fixes

## Overview
Version 1.6.1 fixes three critical bugs in the Text-to-Image Prompt Enhancer node:
1. ✅ **Settings Leakage**: Fixed settings appearing in output with `| Settings:` separator
2. ✅ **Emphasis Syntax**: Fixed `(keyword:weight)` being broken by LLM processing
3. ✅ **Alternation Syntax**: Added support for `{option1|option2|option3}` random selection

## Testing Status
- ✅ All unit tests passed
- ✅ Code compilation verified
- ⏳ **User testing in ComfyUI required**

---

## Installation Steps

1. **Restart ComfyUI**
   - Close ComfyUI completely
   - Restart to load the updated node code

2. **Verify Node Appears**
   - Look for "Eric Prompt Enhancers" category
   - Should see "Text-to-Image Prompt Enhancer"

---

## Test Cases

### Test 1: Emphasis Syntax (Weight Preservation)
**What to test**: The node should preserve `(keyword:weight)` syntax exactly as entered

**Example prompts**:
```
a woman with (dark skin:1.5) and (detailed face:1.3)
```
```
(masterpiece:1.4), (best quality:1.2), portrait of a cat
```
```
forest landscape with (dramatic lighting:1.8) and (fog:0.6)
```

**Expected behavior**:
- ✅ Input: `a woman with (dark skin:1.5)`
- ✅ Output should contain: `(dark skin:1.5)` ← Weight syntax preserved
- ❌ **OLD BUG**: Would output `dark skin (1.5)` ← Weight broken

**How to verify**:
1. Enter a prompt with `(keyword:number)` emphasis
2. Run the node
3. Check the enhanced output
4. Verify the `(keyword:number)` format is **exactly preserved**

---

### Test 2: Alternation Syntax (Random Selection)
**What to test**: The node should randomly select one option from `{a|b|c}` expressions

**Example prompts**:
```
a {cat|dog|rabbit} in the garden
```
```
{red|blue|green|yellow} dress on a {tall|short} woman
```
```
portrait of a person with {blonde|brunette|red|black} hair and {blue|green|brown} eyes
```

**Expected behavior**:
- ✅ Input: `a {cat|dog|rabbit} in the garden`
- ✅ Output might be: `a cat in the garden` OR `a dog in the garden` OR `a rabbit in the garden`
- Each run should potentially give different random selections

**How to verify**:
1. Enter a prompt with `{option1|option2|option3}` syntax
2. Run the node multiple times
3. Observe different random selections each time
4. The `{}` brackets should be removed in output

---

### Test 3: Settings Cleanup (No Leakage)
**What to test**: The node should NOT include settings information in the prompt output

**Settings to test with**:
- Try different camera angles (low angle, high angle, eye level)
- Try different lighting options (golden hour, soft, dramatic)
- Try different shot types (close-up, full body, portrait)

**Example configuration**:
```
Prompt: a woman in a garden
Camera Angle: low angle
Lighting: golden hour
Shot Type: close-up
```

**Expected behavior**:
- ✅ Output: Enhanced prompt describing woman, garden, mood, details
- ❌ Output should **NOT contain**: `| Settings: camera angle: low angle` or similar

**OLD BUG example**:
```
beautiful woman in lush garden with detailed flowers and soft atmosphere | Settings: camera angle: low angle; lighting: golden hour; shot type: close-up
```
☝️ This should NO LONGER happen!

**How to verify**:
1. Enter any prompt
2. Change camera angle, lighting, and shot type settings
3. Run the node
4. Check the enhanced output
5. Verify NO settings information appears in the prompt

---

### Test 4: Combined Features
**What to test**: All three features should work together correctly

**Example prompts**:
```
{red|blue|purple} (dress:1.3) on a {tall|short} woman with (detailed face:1.5)
```
```
a {cat|dog} with (fluffy fur:1.4) in a {garden|park|field}
```

**Expected behavior**:
1. Alternations `{}` are processed first (random selection)
2. Emphasis `()` is preserved through LLM enhancement
3. Settings do NOT appear in output

**Example flow**:
- **Input**: `{red|blue} (dress:1.3) on a woman`
- **After alternation**: `blue (dress:1.3) on a woman` (red randomly chosen)
- **Emphasis protected during LLM**: `(dress:1.3)` wrapped safely
- **After LLM**: Enhanced description with `(dress:1.3)` intact
- **Final output**: `elegant blue (dress:1.3) on a confident woman, detailed fashion photography` ← No settings info!

---

## Platform-Specific Testing

Test with different platforms to ensure compatibility:

### Flux (Natural Language)
```
Prompt: a {cat|dog} with (detailed fur:1.4)
Platform: flux
```

### Pony Diffusion (Booru Tags)
```
Prompt: 1girl, {red hair|blonde hair|black hair}, (detailed face:1.3)
Platform: pony
```

### SDXL (Detailed Descriptions)
```
Prompt: portrait of a {young|elderly} person with (dramatic lighting:1.5)
Platform: sdxl
```

---

## What to Report

If you find any issues, please note:

1. **Which bug occurred**:
   - Settings appearing in output?
   - Emphasis syntax broken?
   - Alternation not working?

2. **Your test prompt**: Exact text you entered

3. **Settings used**: Platform, camera angle, lighting, etc.

4. **Expected output**: What should have happened

5. **Actual output**: What actually happened

6. **Screenshot**: If possible, capture the node and output

---

## Known Behaviors (Not Bugs)

### Alternation is Random
- Each run with `{a|b|c}` will randomly pick one option
- This is intentional for variety in prompt generation
- If you want consistent results, don't use alternation syntax

### LLM May Rephrase
- The LLM will enhance and rephrase your prompt
- This is normal and expected behavior
- The emphasis weights `(keyword:1.5)` will be preserved even if surrounding text changes

### Settings Are Incorporated
- Settings (camera angle, lighting, shot type) ARE used by the LLM
- They influence the enhancement style and content
- They just shouldn't appear as literal text in the output

---

## Testing Checklist

Use this checklist when testing:

- [ ] Restart ComfyUI
- [ ] Node appears in "Eric Prompt Enhancers" category
- [ ] Test emphasis syntax: `(keyword:1.5)` preserved
- [ ] Test alternation syntax: `{a|b|c}` randomly selected
- [ ] Test settings cleanup: No `| Settings:` in output
- [ ] Test combined features: All work together
- [ ] Test with different platforms (Flux, Pony, SDXL)
- [ ] Test with complex prompts
- [ ] Multiple runs show variety (alternation randomness)

---

## Success Criteria

v1.6.1 is working correctly if:

1. ✅ **Emphasis weights are preserved exactly**: `(dark skin:1.5)` stays as `(dark skin:1.5)`
2. ✅ **Alternations are processed**: `{cat|dog}` becomes either `cat` or `dog`
3. ✅ **No settings leakage**: Output never contains `| Settings:` or `Settings:`
4. ✅ **All features work together**: Can use both emphasis and alternation in same prompt

---

## Quick Test Script

Copy-paste this into the node to test all features at once:

```
a {beautiful|stunning|elegant} woman with (detailed face:1.5) and {red|blonde|dark} (hair:1.3) in a {garden|forest|meadow}
```

**Platform**: flux  
**Camera Angle**: low angle  
**Lighting**: golden hour  

**Expected**: 
- One color chosen from each `{}`
- Both `(detailed face:1.5)` and `(hair:1.3)` preserved
- No settings text in output
- Enhanced natural language description

---

## Files Modified

- `text_to_image_node.py` - Main bug fixes
- `BUGFIX_V161.md` - Technical documentation
- `test_txt2img_bugfixes.py` - Unit tests (all passed ✅)

---

## Support

If issues persist after testing:
1. Check `BUGFIX_V161.md` for technical details
2. Verify ComfyUI was restarted
3. Check console for any error messages
4. Report findings with details listed above

---

**Version**: 1.6.1  
**Date**: 2025  
**Status**: Ready for User Testing  
**Previous Issues**: All resolved in unit tests ✅
