# Enhancement v1.8.1: Expanded Creative Controls

## Date: October 24, 2025

## Summary
Enhanced the Advanced Prompt Expander node with significantly more creative options and better UI organization.

## Changes Made

### 1. New Parameter: `creative_randomness`
- **Type**: Float slider (0.0 to 1.0)
- **Default**: 0.5
- **Location**: Positioned right after `detail_level` for logical grouping
- **Purpose**: Controls how much creative liberty the LLM takes when expanding prompts
  - `0.0` = Stay very close to original prompt
  - `0.5` = Balanced expansion
  - `1.0` = Maximum creative interpretation

### 2. Expanded `light_source` Menu
**Added 10 new lighting source options:**
- ambient lighting
- reflected lighting
- softbox lighting
- camera flash
- neon lights
- striplight
- computer screen glow
- flashlight
- candlelight
- spotlight

**Total options**: 20 (including auto, none, and original 8)

### 3. Renamed & Expanded `lighting_type` → `lighting_quality`
**Added 5 new lighting quality options:**
- spotlight effect
- dappled lighting
- cinematic lighting
- diffused lighting
- dramatic lighting

**Total options**: 18 (including auto, none, and original 11)

### 4. New Parameter: `art_style`
**Added dropdown with 24 famous artists and art movements:**
- **Individual Artists**: Picasso, Van Gogh, Monet, Salvador Dali, Banksy, Andy Warhol, Rembrandt, Caravaggio, Norman Rockwell, Edward Hopper
- **Studio/Director Styles**: Studio Ghibli, Tim Burton, Wes Anderson, Pixar
- **Art Movements**: Renaissance, Baroque, Art Nouveau, Expressionist, Impressionist, Surrealist, Cubist, Pop Art

Models will recognize these styles and apply distinctive visual characteristics.

### 5. New Parameter: `scene_detail`
**Controls the level of detail and complexity in the scene:**
- simple scene
- clean scene
- detailed scene
- cluttered scene
- intricate detail
- minimalist
- maximalist

**Purpose**: Gives users control over composition complexity separate from prompt detail level.

## Technical Changes

### Function Signature Updates
- Added `creative_randomness: float` parameter
- Renamed `lighting_type` → `lighting_quality`
- Added `art_style: str` parameter
- Added `scene_detail: str` parameter

### Updated Methods
- `expand_prompt()`: Updated signature and parameter passing
- `_gather_aesthetic_controls()`: Now includes `art_style` and `scene_detail`
- All aesthetic controls properly collected and passed to expansion engine

## UI Organization Improvements

### Parameter Order (Top to Bottom):
1. `basic_prompt` - Core input
2. `operation_mode` - How to process the prompt
3. `preset` - Style preset
4. `detail_level` - Output verbosity
5. **`creative_randomness`** ⭐ NEW - Positioned logically after detail controls
6. Lighting controls (source, quality, time_of_day)
7. Camera controls (shot_size, composition, lens, angle, movement)
8. Style controls (color_tone, **art_style** ⭐, **scene_detail** ⭐, visual_style, visual_effect)
9. Character emotion
10. LLM configuration
11. Keywords
12. Output options

## Benefits

### For Users:
- **More Creative Control**: Fine-tune how adventurous the LLM should be
- **Richer Lighting Options**: Professional lighting setups (softbox, dappled, etc.)
- **Artistic Styles**: Apply famous artist aesthetics recognized by AI models
- **Scene Complexity**: Control clutter vs. minimalism independently
- **Better Organization**: `creative_randomness` positioned where users expect it

### For Prompt Quality:
- Artist names trigger model's learned associations with distinctive styles
- Specific lighting terms (dappled, softbox) produce more precise results
- Scene detail control prevents over/under-detailing
- Creative randomness allows balancing consistency vs. variation

## Backward Compatibility
✅ **Fully backward compatible**
- All existing parameters retained
- New parameters have sensible defaults (`auto` for dropdowns, `0.5` for creative_randomness)
- Old workflows will continue to work without modification
- `lighting_type` internally renamed to `lighting_quality` (parameter name updated)

## Testing Recommendations

1. **Test creative_randomness range**:
   - Try 0.0, 0.5, 1.0 with same prompt to see variation
   
2. **Test new lighting sources**:
   - "softbox lighting" for studio look
   - "neon lights" for cyberpunk scenes
   - "dappled lighting" for forest scenes

3. **Test art_style**:
   - "Van Gogh style" should add swirling, expressive brushwork
   - "Wes Anderson style" should add symmetrical, pastel compositions
   - "Studio Ghibli style" should add whimsical, hand-drawn anime aesthetics

4. **Test scene_detail**:
   - "minimalist" vs "intricate detail" with same subject
   - "cluttered scene" for busy environments

## Future Enhancement Ideas
- Add more contemporary artists (Zdzisław Beksiński, HR Giger, etc.)
- Add photography-specific styles (street photography, documentary, fashion)
- Consider adding time period styles (1920s, 1950s, 1980s, futuristic)
- Add weather conditions (foggy, rainy, snowy) as separate control

## Files Modified
- `prompt_expander_node_advanced.py` - All changes

## Version
- Previous: v1.8.0
- Current: v1.8.1 (enhancement)
