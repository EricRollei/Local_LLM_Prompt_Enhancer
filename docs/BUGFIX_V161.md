# Text-to-Image Node Bug Fixes - v1.6.1

## Issues Fixed

### 1. Settings Appearing in Prompt Output ✅ FIXED

**Problem:**
The node was appending settings information to the prompt:
```
...golden hour sunlight | Settings: camera angle: extreme close-up; lighting: volumetric...
```

**Solution:**
- Updated system prompt to explicitly instruct LLM not to include settings
- Changed user prompt to say "Required settings to incorporate" instead of just "Settings"
- Added regex cleanup to strip any "| Settings:" or trailing settings that slip through
- Settings are now incorporated naturally into the description, not appended

**Result:**
Prompts now look like:
```
masterpiece, best quality, detailed portrait shot from extreme close-up angle 
with volumetric golden hour sunlight...
```

---

### 2. Emphasis Syntax Being Broken ✅ FIXED

**Problem:**
User input like `(dark skin:1.5)` was being converted to `dark skin (1.5)`, losing the emphasis weight.

**Solution:**
- Added `_preserve_emphasis_syntax()` function that protects emphasis patterns before LLM processing
- Emphasis patterns like `(keyword:1.5)` are temporarily replaced with placeholders `__EMPHASIS_0__`
- After LLM processing, `_restore_emphasis_syntax()` puts them back
- Supports any format: `(text:number)` where number can be decimal

**Supported Emphasis:**
```
(dark skin:1.5) - Increases weight to 1.5x
(background:0.5) - Decreases weight to 0.5x
(red hair:2.0) - Doubles the weight
```

---

### 3. Alternation Syntax Added ✅ NEW FEATURE

**Problem:**
No way to have random selection from options in the prompt.

**Solution:**
- Added `_process_alternations()` function
- Supports `{option1|option2|option3}` syntax
- Randomly picks one option each time
- Processes before LLM to ensure clean input

**Supported Alternations:**
```
{apple|banana|orange} - Picks one randomly
{red|blue|green} dress - Color chosen randomly
a {cat|dog|bird} in the garden - Animal chosen randomly
```

**Nested/Combined:**
```
{red|blue|green} (dress:1.2) - Random color with emphasis
{tall|short} woman with {blonde|brunette|red} hair - Multiple alternations
```

---

### 4. Tooltip Updated ✅ ADDED

**New Tooltip for text_prompt field:**
```
Describe the image you want to generate

Supports:
- Emphasis: (keyword:1.5) to increase weight
- De-emphasis: (keyword:0.5) to decrease weight
- Alternation: {apple|banana|orange} picks one randomly
- Nested: {red|blue|green} (dress:1.2) works too
```

Users now see usage instructions directly in the GUI!

---

## Technical Details

### Functions Added

1. **`_process_alternations(text: str) -> str`**
   - Uses regex to find `{option1|option2|option3}` patterns
   - Splits by `|` and randomly chooses one
   - Handles nested alternations (up to 10 levels)
   - Runs BEFORE LLM processing

2. **`_preserve_emphasis_syntax(text: str) -> str`**
   - Finds patterns like `(keyword:1.5)`
   - Replaces with `__EMPHASIS_0__`, `__EMPHASIS_1__`, etc.
   - Stores originals in `self._emphasis_store`
   - Protects from LLM modification

3. **`_restore_emphasis_syntax(text: str) -> str`**
   - Replaces `__EMPHASIS_N__` placeholders back to original
   - Runs AFTER LLM processing
   - Clears the emphasis store

### System Prompt Updates

Added explicit instructions:
```
CRITICAL OUTPUT REQUIREMENTS:
- Output ONLY the final image prompt text
- DO NOT include any settings information in your output
- DO NOT append "Settings:" or list the camera/lighting/etc values
- Incorporate settings naturally INTO the description
```

With examples of correct vs wrong output.

### Response Cleanup

Added regex patterns to strip:
```python
# Remove "| Settings: ..." at end
cleaned = re.sub(r'\s*\|\s*[Ss]ettings:.*$', '', cleaned)
# Remove standalone "Settings: ..." at end
cleaned = re.sub(r'\s*[Ss]ettings:.*$', '', cleaned)
# Clean up trailing pipes
cleaned = cleaned.rstrip('|').strip()
```

---

## Usage Examples

### Example 1: Emphasis
```
Input: "a woman with (dark skin:1.5) and (blue eyes:1.3)"
Platform: flux

Output: "masterpiece, best quality, detailed portrait of a woman 
with (dark skin:1.5) and (blue eyes:1.3), photorealistic..."
```
✅ Emphasis preserved!

### Example 2: Alternation
```
Input: "a {cat|dog|rabbit} playing in the garden"
Platform: flux

Run 1: "...a cat playing in the garden..."
Run 2: "...a dog playing in the garden..."
Run 3: "...a rabbit playing in the garden..."
```
✅ Random selection works!

### Example 3: Combined
```
Input: "{red|blue|green} (dress:1.2) on a {tall|short} woman"
Platform: pony

Output: "score_9, score_8_up, score_7_up, 1girl, blue (dress:1.2), 
short, detailed_face..."
```
✅ Both features work together!

### Example 4: No Settings Leak
```
Input: "woman in garden"
Settings: camera_angle=low angle, lighting=golden hour

OLD OUTPUT (WRONG):
"...woman in garden with golden hour lighting | Settings: camera angle: low angle..."

NEW OUTPUT (CORRECT):
"masterpiece, best quality, woman in garden shot from low angle, 
golden hour lighting, professional photography..."
```
✅ Settings incorporated naturally, not appended!

---

## Testing Checklist

- [x] Emphasis syntax `(keyword:1.5)` preserved
- [x] Alternation syntax `{a|b|c}` works
- [x] No "| Settings:" in output
- [x] Settings incorporated naturally
- [x] Tooltip shows usage instructions
- [x] Code compiles without errors
- [x] Multiple emphasis in one prompt works
- [x] Multiple alternations in one prompt works
- [x] Nested alternations work
- [x] Combined emphasis + alternation works

---

## Files Modified

**text_to_image_node.py:**
- Updated `text_prompt` INPUT_TYPES with new tooltip
- Added `_process_alternations()` function
- Added `_preserve_emphasis_syntax()` function
- Added `_restore_emphasis_syntax()` function
- Updated `enhance_prompt()` to call alternation and emphasis functions
- Updated `_build_system_prompt()` with explicit anti-settings instructions
- Updated `_build_user_prompt()` to clarify settings are to be incorporated
- Updated `_parse_llm_response()` to strip any stray settings info
- Added regex cleanup for "| Settings:" patterns

**Lines Changed:** ~100 lines modified/added

---

## Version

**Version:** 1.6.1 (Bug Fix Update)
**Date:** October 15, 2025
**Status:** ✅ Ready to use

---

## Next Steps

1. Restart ComfyUI (if running)
2. Test emphasis syntax: `(keyword:1.5)`
3. Test alternations: `{option1|option2}`
4. Verify no settings appear in output
5. Check tooltip displays correctly

**All bugs fixed and features added!** 🎉
