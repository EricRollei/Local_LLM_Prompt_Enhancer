# Wan 2.2 Prompt Design Guide

## 0. TL;DR philosophy
Wan 2.2 is way better than 2.1 at (a) camera motion, (b) physical depth/parallax, and (c) consistent character animation. It can follow verbs like “dolly in,” “pan left,” “camera cranes up,” and “slow orbital arc,” and it respects cinematic framing terms like “close-up,” “medium shot,” “wide establishing shot,” etc. much more faithfully than 2.1. [Sources: turn0search0, turn0search1, turn0search3, turn0search11]

The model also responds well to ordered shot descriptions in time (“Shot 1… Shot 2… Shot 3…”), or a single continuous temporal flow (“The camera starts… then… finally…”). [Sources: turn0search1, turn0search5, turn0search6]

So: you’re not just describing a vibe. You’re directing.

---

## 1. Core building blocks of a good Wan 2.2 prompt
Wan 2.2 prompts that consistently work tend to include these ingredients (this exact breakdown shows up in multiple public guides and API docs). [Sources: turn0search1, turn0search5, turn0search11]

1. **Subject / Character**  
   Who are we looking at? Physical traits, outfit, vibe, species, mech, creature, etc.  
   - Example: “a graceful woman in flowing white Hanfu, long sleeves, luminous spirit energy in her fingertips”

2. **Environment / Setting**  
   Where are they? Time of day? Weather? Atmosphere?  
   - Example: “moonlit lakeshore at night, low mist rising from the water, soft blue rim light”

3. **Motion / Action**  
   What is moving? Subject motion AND environment motion.  
   - Example: “she raises her arms and dances slowly, summoning glowing birds of light that spiral around her sleeves” / “mist drifts across the frame, water ripples reflect the glow”  
   Wan 2.2 expects explicit motion language, not just a static tableau; otherwise it can generate something that looks like a pretty stabilized pan shot and very little character movement. [Sources: turn0search1, turn0search11]

4. **Camera Movement**  
   How does the camera move through that action?  
   - “slow dolly in”
   - “camera pans left”
   - “smooth handheld tracking shot at shoulder height behind him”
   - “the camera orbits around her in a smooth arc”
   - “the camera cranes up and tilts down for a final reveal”
   - “static shot / locked-off tripod / fixed shot”  
   These are high-value tokens in Wan 2.2. In 2.1 a lot of this was hit-or-miss; in 2.2 users report solid adherence to pan, dolly in / out, pull back, tilt, crash zoom, and even roll. [Sources: turn0search0, turn0search1, turn0search3, turn0search11]

5. **Cinematic Style / Lens / Grade**  
   “cinematic realism,” “24 fps,” “anamorphic lens flare,” “shallow depth of field,” “neon cyberpunk lighting,” “16mm film grain,” “soft volumetric dusk light,” “high-contrast noir,” “anime cel shading,” etc.  
   Wan 2.2 responds strongly to these style tags for lighting and texture. [Sources: turn0search1, turn0search4, turn0search5, turn0search6]

6. **Ending Beat**  
   Tell it how to end.  
   - “Final wide establishing shot, camera slowly cranes up and pulls back to reveal the entire neon city below.”  
   Explicit “final reveal” language helps it wrap up instead of looping aimlessly. [Sources: turn0search1, turn0search5, turn0search6]

7. **Technical hints (optional)**  
   Resolution / fps tags like “1280×720, 24 fps, cinematic realism” appear in public guidance and some preset recipes. [Sources: turn0search1, turn0search4, turn0search11]

8. **Negative prompt (optional)**  
   Wan 2.2 listens more than 2.1 to negatives like  
   “no subtitles, no on-screen text, no watermarks, no extra limbs, no distorted hands, no low quality, not cartoon unless explicitly described.”  
   Use this especially for photoreal humans. [Sources: turn0search1, turn0search5]

That’s the “what.” Now, “how do we package it?”

---

## 2. High-control formats that work

Wan 2.2 tends to follow ordering. So we exploit that.

### Format A. Storyboard / Shot List
Great for narrative or multi-beat scenes.

**Structure:**
1. Global Setup paragraph (mood, subject, world, lighting)  
2. Shot 1 block  
3. Shot 2 block  
4. Shot 3 block  
5. (Optional) global tech + negatives at the end

**Why it works:**  
Wan 2.2 seems to interpret “Shot 1 / Shot 2 / Shot 3” as temporal progression in a single clip, and aligns camera movement with each block. This helps it “change angles” within one generated video instead of just drifting one camera move. It also helps you guarantee an ending beat. [Sources: turn0search1, turn0search5, turn0search6]

**Template:**
- Scene / Mood Setup (2–4 sentences)  
- Shot 1: [Framing, camera move, subject action, emotional beat]  
- Shot 2: [New angle / escalation, new camera move]  
- Shot 3: [Reveal / finale / pullback, explicitly marked “Final shot”]  
- Style / tech footer + negatives

**Worked Example (fantasy wuxia)**

A graceful woman in flowing white Hanfu dances at the edge of a moonlit lake at night. Soft blue rim light outlines her sleeves, and faint mist drifts across the water. Glowing spirit-bird particles gather around her hands as she moves. Cinematic realism, ethereal wuxia fantasy mood.  

Shot 1: Close-up, Slow Dolly In  
The camera starts in a close-up on her hands. She turns her wrists with elegant precision, and tiny birds of light blossom from her fingertips. Their wings glow softly and leave shimmering trails in the air. Slow dolly in toward her glowing fingertips, gentle handheld feel.  

Shot 2: Medium Shot, Orbital Arc  
The camera eases back to a medium shot of her upper body and begins a smooth orbital arc around her to the left. Her long sleeves sweep through the air, leaving ribbons of light. The spirit birds circle her in synchronized motion, tracing spirals above the dark lake. Her face is calm, focused, powerful.  

Shot 3: Overhead Crane Reveal (Final Shot)  
The camera cranes upward and tilts down to an overhead view. The glowing birds form a radiant halo around her on the lakeshore, their reflections flickering on the black water. Moonlight and spirit-light merge into a swirling galaxy around her. Final wide reveal, majestic and otherworldly.  

24 fps, 1280×720, cinematic realism, smooth motion.  
no subtitles, no on-screen text, no watermarks, no extra limbs, no distorted hands.  

Why this works:
- Shot labels + “Final wide reveal” give time progression and an ending.  
- Verbs like “slow dolly in,” “smooth orbital arc,” “camera cranes upward” are known-good camera instructions. [Sources: turn0search0, turn0search1, turn0search3, turn0search11]  
- Parallax cues (“mist drifts,” “reflections flickering”) guide depth. [Sources: turn0search1, turn0search5]

---

### Format B. Timed Beats / Continuous Shot
Use this when you want one continuous camera move instead of discrete “edits.”

**Structure:**
1. Global Setup  
2. 0–2s / Opening Move  
3. 2–4s / Escalation Move  
4. 4–6s / Final Reveal  
5. Style / tech footer + negatives

Timestamps sometimes help; Wan 2.2 also responds to “At first… Then… Finally…”. [Sources: turn0search1, turn0search5, turn0search6]

**Worked Example (cyberpunk alley chase)**

A hooded courier sprints through a neon-lit rain-soaked alley at night. Reflections of magenta and cyan kanji signs shimmer in puddles. Steam blows from street vents and drifts past the lens. Cinematic realism, gritty cyberpunk mood, shallow depth of field.  

0–2s (Opening / Tracking Shot):  
At first, the camera sits at shoulder height directly behind the courier, tracking forward smoothly as he runs. Rain streaks past the lens. Wet pavement glows with neon reflections. Subtle handheld shake adds urgency.  

2–4s (Side Profile / Dolly In):  
Then, the camera swings to his left side in a fast pan and dollies in on his face in profile. Neon kanji signage flickers across his cheekbones. Steam drifts between camera and subject in slow motion, catching the neon light. His expression is focused and determined.  

4–6s (Overhead Crane Reveal / Final Shot):  
Finally, the camera cranes up and tilts down to an overhead wide view, pulling back to reveal the entire alley packed with glowing signage, hanging cables, and crowded silhouettes. The courier becomes a small figure sprinting through a canyon of neon. Final wide reveal.  

24 fps, 1280×720, cinematic realism.  
no subtitles, no text overlay, no watermarks.  

Notes:
- “tracking forward smoothly,” “subtle handheld shake,” “camera cranes up” are all verbs Wan tends to actually follow. [Sources: turn0search1, turn0search3, turn0search6, turn0search11, turn0search13]  
- “Final wide reveal” steers the clip’s ending. [Sources: turn0search1, turn0search5, turn0search6]

---

### Format C. Single Cinematic Paragraph (“Hero Shot”)
Great for short clips like product shots, weapons reveals, character intros.

**Template:**
- Start tight / intimate  
- Add motion word (“the camera pulls back…”)  
- Pull to context / reveal scale  
- Add style and negatives

**Worked Example (mountaineer reveal)**

Extreme close-up of an ice axe biting into blue ice, shards and sparks flying in slow motion. The camera pulls back and tilts up to reveal a lone mountaineer standing on a narrow alpine ridge at sunrise. Golden rim light silhouettes the figure against glowing clouds, lens flare streaking across frame, crisp cold air visible in their breath. Cinematic realism, 24 fps, 1280×720, dramatic expedition film style. no subtitles, no text overlay, no watermarks. [Sources: turn0search1, turn0search4, turn0search5, turn0search11]

---

## 3. Camera control keywords to whitelist
These are reliable verbs/phrases Wan 2.2 tends to obey. [Sources: turn0search0, turn0search1, turn0search3, turn0search11]

**Framing / angle:**
- “wide establishing shot”
- “medium shot”
- “close-up,” “extreme close-up”
- “over-the-shoulder shot”
- “profile close-up”
- “overhead shot,” “top-down shot,” “bird’s-eye view”
- “first-person POV”

**Camera movement:**
- “camera pans left / pans right”
- “camera tilts up / tilts down”
- “slow dolly in,” “dolly out,” “camera pulls back”
- “tracking shot following behind him at shoulder height”
- “the camera orbits around her in a smooth arc”
- “the camera cranes up and tilts down for a final reveal”
- “crash zoom in on her face”
- “camera slowly rolls”
- “static shot,” “locked-off camera,” “fixed shot,” “handheld shake,” “smooth glide”

**Motion feel / pacing:**
- “slow motion”
- “time-lapse”
- “fast whip-pan”
- “sudden jolt”
- “subtle handheld shake”
- “stabilized cinematic motion,” “smooth glide”  
These steer the energy level of the shot. [Sources: turn0search1, turn0search5]

Your LLM should ONLY use verbs from this set to avoid nonsense jargon that reduces control.

---

## 4. Style, lighting, lens, and atmosphere control
Current guidance for Wan 2.2 says styling and lighting cues are very literal. [Sources: turn0search1, turn0search4, turn0search5, turn0search6]

Use:
- realism bundle:  
  “cinematic realism, 24 fps, shallow depth of field, anamorphic lens flare, subtle film grain”
- anime / cel bundle:  
  “anime cel-shaded style, vivid saturated color, crisp line art, 2D animation look”
- painterly bundle:  
  “hand-painted fantasy illustration style, soft brush texture, glowing rim light, ethereal atmosphere”
- documentary bundle:  
  “handheld documentary style, natural daylight, light camera shake, muted color grade”
- surreal bundle:  
  “dreamlike slow motion, volumetric haze, glowing particles drifting in the air”

Also describe lighting explicitly:
- “soft blue moonlit rim light,”
- “volumetric dusk light with god rays,”
- “neon cyberpunk backlight reflecting in puddles.”

Explicit lighting tags strongly affect final look. [Sources: turn0search1, turn0search4, turn0search5, turn0search6]

---

## 5. Image-to-video guidance (reference modes)
Wan 2.2 can animate an input frame or use an image as a style / identity source. You MUST say how to use that reference. [Sources: turn0search7, turn0search15, turn0search21]

We standardize four modes:

1. **Recreate / continue this exact image**  
   “Use the provided image as the exact character and costume reference. Keep the same face, hair, outfit, and lighting. Animate this character without changing identity.”

2. **Style transfer only**  
   “Match the lighting, color palette, and cinematic mood of the provided image, but create a new pose and new scene.”

3. **Re-imagine / remix**  
   “Loosely base the main character on the provided image, but change the outfit to post-apocalyptic scavenger gear and move the scene into a ruined city at dusk.”

4. **Subject only, new world / new lighting**  
   “Preserve ONLY the subject’s face and body identity from the provided image. Ignore the original background and lighting. Place this character in a neon-lit night market in heavy rain.”

If you don’t specify this, Wan may copy props/lighting you didn’t want or drift identity.

---

## 6. Negative prompts
From Wan 2.2 tips: negative prompts matter for polish. [Sources: turn0search1, turn0search5]

**Photoreal / cinematic block:**
- “no subtitles, no on-screen text, no watermarks, no logos, no extra limbs, no deformed hands, no distortion, not low quality”

**Anime / stylized block:**
- “no photoreal skin texture, no live-action lighting, no watermarks, no subtitles, keep clean cel shading, no flicker, no jitter”

Pick one that matches style.

---

## 7. Troubleshooting heuristics

**Scene looks static / dead**  
- Add explicit camera verbs per beat.  
- Add atmospheric motion (“steam drifts,” “rain streaks past the lens,” “fabric ripples”).  
Wan often animates those even if the character barely moves. [Sources: turn0search1, turn0search11]

**Too shaky / chaotic**  
- Add “smooth glide, stabilized cinematic motion” or “locked-off static shot.” [Sources: turn0search0, turn0search1, turn0search11]

**Bad hands / limbs**  
- Include the photoreal negative block.  
- Favor torso-up medium shots until you like the model’s hand quality.

**Identity drift across shots**  
- Repeat the same identity capsule in each Shot block: “the same woman in white Hanfu…”.  
This mirrors multi-shot consistency tricks from modern video diffusion pipelines, which repeat identity cues for each beat. [Sources: turn0search1, turn0search16, turn0search21]

**Abrupt cutoff ending**  
- Explicitly say “Final wide reveal,” “Final overhead shot,” “Final establishing shot.”  
Wan treats “Final” as a termination cue. [Sources: turn0search1, turn0search5, turn0search6]

---

## 8. Master Blueprint (what we’ll auto-generate)

**Wan 2.2 Cinematic Prompt Blueprint:**

1. (Optional, only if image provided) Reference Instruction Mode  
   - One of:  
     - recreate faithfully  
     - style only  
     - re-imagine  
     - subject only, new world

2. Global Setup Paragraph  
   - Subject / identity capsule  
   - Environment / lighting / atmosphere  
   - Overall mood and style bundle

3. Shot / Beat Blocks  
   Pick ONE style:  
   **Storyboard style:**  
   - Shot 1: [framing + camera move + subject action + parallax + emotion]  
   - Shot 2: escalation / new angle  
   - Shot 3: final reveal (“Final shot,” “Final wide reveal,” or “Final establishing shot”)  
   **OR Continuous style:**  
   - 0–2s / 2–4s / 4–6s with “At first / Then / Finally”

4. Technical Suffix  
   - fps, resolution, cinematic style tags  
   - negative prompt block (photoreal OR anime block)

Feed that blueprint to your local LLM and you’ll get consistent Wan 2.2 prompts with usable camera control.  
