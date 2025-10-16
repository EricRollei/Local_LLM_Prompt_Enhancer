# Wildcard Support Guide

## What Are Wildcards?

Wildcards let you create **dynamic prompts** with random variations. Instead of typing the same prompt multiple times with different subjects, use wildcards for automatic randomization.

## Syntax

### Inline Wildcards (Recommended)
```
{category:option1|option2|option3}
```

**Example:**
```
A {animal:cat|dog|bird} playing {instrument:piano|guitar|drums} in a {location:park|studio|street}
```

**Generates one of:**
- "A cat playing piano in a park"
- "A dog playing guitar in a studio"  
- "A bird playing drums in a street"
- (Any combination of the options)

### Predefined Wildcards
```
{category}
```

**Example:**
```
A {person} using a {tool} to {action} the {object}
```

**Uses built-in categories:**
- {animal}, {person}, {profession}, {instrument}, {location}
- {weather}, {time}, {emotion}, {action}, {color}
- {vehicle}, {tool}, {object}

## Built-in Wildcard Categories

| Category | Options |
|----------|---------|
| {animal} | cat, dog, bird, horse, rabbit, fox, deer, wolf |
| {person} | man, woman, child, elder, teenager, artist, scientist |
| {profession} | detective, chef, doctor, teacher, engineer, musician, artist |
| {instrument} | piano, guitar, violin, drums, saxophone, flute |
| {location} | park, studio, street, forest, beach, city, room |
| {weather} | sunny, rainy, snowy, foggy, stormy, cloudy |
| {time} | morning, noon, afternoon, evening, night, midnight |
| {emotion} | happy, sad, angry, surprised, calm, excited, pensive |
| {action} | walking, running, dancing, working, playing, creating |
| {color} | red, blue, green, yellow, purple, orange, black, white |
| {vehicle} | car, motorcycle, bicycle, truck, bus, train, boat |
| {tool} | hammer, wrench, paintbrush, camera, telescope, microscope |
| {object} | book, ball, box, bottle, phone, computer, chair |

## Examples

### Example 1: Character Variations
```
Input: A {profession:detective|chef|scientist} in their {location:office|kitchen|laboratory} at {time:dawn|midnight|noon}

Possible outputs:
- "A detective in their office at dawn"
- "A chef in their kitchen at midnight"  
- "A scientist in their laboratory at noon"
```

### Example 2: Vehicle Scenes
```
Input: A {color:red|blue|black} {vehicle:sports car|motorcycle|truck} racing through a {weather:rainy|snowy|foggy} {location:city|mountain pass|desert}

Possible outputs:
- "A red sports car racing through a rainy city"
- "A blue motorcycle racing through a snowy mountain pass"
- "A black truck racing through a foggy desert"
```

### Example 3: Mixed Inline & Predefined
```
Input: A {person} {emotion:happily|sadly|angrily} holding a {color} {object}

Uses predefined {person} and {object} with inline emotions and colors.
```

### Example 4: Complex Scene
```
Input: {profession:astronaut|pilot|diver} explores {location:alien planet|underwater cave|arctic tundra} during {time:sunrise|sunset|night} with {tool:scanner|camera|equipment}

Creates varied exploration scenes automatically.
```

## How It Works

1. **Wildcard Detection**: Node scans your prompt for `{...}` syntax
2. **Random Selection**: Picks one option from each wildcard
3. **Replacement**: Substitutes wildcards with chosen options
4. **Expansion**: Sends processed prompt to LLM for detail expansion

## Breakdown Output

The node shows what was chosen:

```
Original Input:
A {animal:cat|dog|bird} playing {instrument:piano|guitar}

Wildcard Replacements:
- animal: cat
- instrument: piano

Processed Prompt:
A cat playing piano
```

## With Variations

When generating multiple variations, wildcards are re-rolled for each:

```
Variation 1: A cat playing piano in a park
Variation 2: A dog playing guitar in a studio  
Variation 3: A bird playing drums in a street
```

Each variation gets different random selections!

## Tips for Using Wildcards

### 1. Keep Options Related
✅ Good: `{location:park|beach|forest}` (all outdoor)
❌ Bad: `{location:park|spaceship|microscope}` (unrelated)

### 2. Match Grammar
✅ Good: `A {animal:cat|dog|bird}` (all singular)
❌ Bad: `A {animal:cat|dogs|birds}` (mixed singular/plural)

### 3. Use Inline for Custom Options
Use inline wildcards when you need specific options not in predefined lists:
```
{character:wizard|warrior|rogue|healer}
```

### 4. Combine with Presets
```
Input: A {profession} in a {location}
Preset: noir
Tier: advanced

Result: Noir-style expansion of the random profession/location combo
```

### 5. Use with Advanced Node Dropdowns
```
Input: A {vehicle} racing through {weather} conditions
Shot Size: wide shot
Camera Movement: tracking shot
Preset: action

Result: Action-style wide tracking shot of random vehicle/weather
```

## With Random Preset

Wildcards work GREAT with random preset:

```
Input: A {animal} {action}
Preset: random
Tier: enhanced

Result:
- Random animal chosen (e.g., "fox")
- Random action chosen (e.g., "dancing")
- Random cinematography applied
- Output: "A fox dancing" with random aesthetic choices
```

## Troubleshooting

### Wildcards Not Replaced
- Check syntax: `{name:opt1|opt2}` (colon and pipes)
- No spaces in curly braces: `{animal}` not `{ animal }`

### Same Options Every Time
- Not a bug! Each run picks randomly
- Use variations (num_variations: 3) to get multiple

### Wildcard in Output
If you see `{animal}` in the output:
- Typo in category name
- Category not in predefined list
- Use inline format: `{animal:cat|dog|bird}`

## Advanced: Nested Concepts

You can combine wildcards with concepts:

```
Input: {profession} using {tool} to fix a {object} in a {weather} {time}

Creates complex scenarios like:
"engineer using wrench to fix a computer in a rainy morning"
```

## Combining Features

### Wildcards + Keywords + Preset
```
Input: A {profession} in dramatic pose
Preset: cinematic
Positive Keywords: myLoRA_trigger
Tier: advanced

Result: Random profession, cinematic style, with LoRA trigger
```

### Wildcards + Advanced Node Controls
```
Input: A {vehicle} in motion
Preset: action
Shot Size: wide shot
Camera Movement: tracking shot
Time of Day: sunset time
Lens: wide-angle lens

Result: Random vehicle, but specific cinematography
```

## Summary

**Wildcards enable:**
- ✅ Dynamic prompt variations
- ✅ Quick batch generation with variety
- ✅ A/B testing different concepts
- ✅ Creative exploration
- ✅ Efficient prompt iteration

**Syntax:**
- Inline: `{name:opt1|opt2|opt3}`
- Predefined: `{category}`

**Works with:**
- All presets (especially good with "random")
- All tiers
- All modes (text-to-video, image-to-video)
- Both Standard and Advanced nodes
- Multiple variations

**Try it!**
```
Input: A {animal} {action} in a {location} during {time}
```

Generate 3 variations and see the variety!
