/**
 * ideogram_magic.js - video_prompter
 *
 * Adds starter-template prefill to the "Ideogram 4 Magic Prompt" node
 * (EricIdeogramMagicPrompt). Picking an "application" fills the idea box with an
 * editable template and sets a sensible aspect ratio. Labels must stay in sync
 * with APPLICATIONS in ideogram_magic_node.py.
 *
 * Author: Eric Hiss (GitHub: EricRollei)
 */

import { app } from "../../scripts/app.js";

const NODE = "EricIdeogramMagicPrompt";

// label -> { idea, aspect }. Placeholders in {curly braces} are meant to be edited.
const TEMPLATES = {
  "Portrait (photo)": {
    aspect: "4:5",
    idea: "A close-up portrait of {SUBJECT}, soft window light from the left, shallow depth of field, warm honey tones, 85mm lens, photorealistic",
  },
  "Product (photo)": {
    aspect: "1:1",
    idea: "A studio product photograph of {PRODUCT} on a white marble surface, single directional side light, one soft shadow, editorial product photography, minimalist, shallow depth of field",
  },
  "Lifestyle flat-lay (photo)": {
    aspect: "4:5",
    idea: "A lifestyle flat-lay photograph of {ITEMS} arranged on white linen, morning window light from the left, soft warm shadows, clean aspirational aesthetic",
  },
  "Fashion editorial (photo)": {
    aspect: "2:3",
    idea: "A high-fashion editorial photograph of {SUBJECT} in {WARDROBE} at {LOCATION}, overcast daylight, the {ACCENT} as the only saturated element in an otherwise desaturated scene, 50mm lens",
  },
  "Logo": {
    aspect: "1:1",
    idea: "A clean geometric logo for {BRAND}, {a simple mark such as two overlapping triangles}, dark slate and white, sans-serif wordmark below the mark, flat vector style",
  },
  "Event poster": {
    aspect: "2:3",
    idea: "A bold typographic event poster for {EVENT}, {DATE} at {VENUE}, navy and electric-yellow palette, large condensed uppercase headline, geometric abstract shapes, minimal negative space",
  },
  "Vintage travel poster": {
    aspect: "2:3",
    idea: "A vintage travel poster for {PLACE}, {landmark} silhouette at dusk, {foreground motif}, deep indigo sky and gold accents, large serif headline reading \"{HEADLINE}\", screenprint style",
  },
  "Movie one-sheet": {
    aspect: "2:3",
    idea: "A {genre} movie one-sheet poster for \"{TITLE}\", {key art}, deep navy and cool-blue palette, thin extended sans-serif title, a stacked credit block along the bottom",
  },
  "T-shirt design": {
    aspect: "1:1",
    idea: "A t-shirt graphic of {SUBJECT or SLOGAN}, bold screenprint style, a tight three-color palette, centered composition on a transparent background",
  },
  "Packaging / label": {
    aspect: "4:5",
    idea: "A {product} label mockup for {BRAND}, kraft-paper texture, a bold wordmark and a small descriptor as separate text, a hand-drawn motif, burgundy and charcoal, artisan packaging aesthetic",
  },
  "Instagram post": {
    aspect: "4:5",
    idea: "A modern Instagram post for {BRAND}, warm terracotta background, an overhead hero shot of {SUBJECT}, minimal text space reserved at the bottom third, lifestyle editorial aesthetic",
  },
  "YouTube thumbnail": {
    aspect: "16:9",
    idea: "A bold YouTube thumbnail for {TOPIC}, dark charcoal background, a neon-green accent, a large bold text area on the right third, minimal geometric shapes, high contrast for small screens",
  },
  "Book cover": {
    aspect: "2:3",
    idea: "A {genre} book cover for \"{TITLE}\", {scene}, a subdued blue-grey palette, serif title set in the upper third",
  },
  "Album cover": {
    aspect: "1:1",
    idea: "A moody album cover for {ARTIST}, {scene}, dark-blue and silver palette, the title \"{TITLE}\" in delicate thin serif at the bottom center, cinematic and atmospheric",
  },
  "Editorial illustration": {
    aspect: "3:2",
    idea: "A detailed editorial illustration of {SUBJECT}, flat color areas with fine ink-style linework, a limited palette of deep teal, amber and off-white, graphic-novel aesthetic",
  },
  "Comic / manga panel": {
    aspect: "3:2",
    idea: "A manga panel of {scene}, cel-shaded with clean linework and bold outlines, dramatic angle, {speech: \"{LINE}\"}",
  },
  "Infographic": {
    aspect: "4:5",
    idea: "A clean infographic showing {DATA or TOPIC}, line-chart format, a soft blue and teal palette, clear axis labels, modern sans-serif typography, white background, editorial style",
  },
  "Business card": {
    aspect: "3:2",
    idea: "A clean business card layout for {BRAND}, off-white surface, a bold wordmark and contact details as separate text, blue and green accents, generous whitespace, flat vector design",
  },
  "Sticker": {
    aspect: "1:1",
    idea: "A die-cut sticker of {SUBJECT}, bold outline, flat colors, a simple bright palette, plain background",
  },
  "Sign / storefront": {
    aspect: "3:2",
    idea: "A vintage hand-painted sign reading \"{TEXT}\", aged wood surface, warm tungsten light, cream and gold palette",
  },
  "Greeting card": {
    aspect: "2:3",
    idea: "A {occasion} greeting card, {motif}, a warm palette, \"{GREETING}\" in hand-lettered script, warm and inviting",
  },
  "Menu": {
    aspect: "2:3",
    idea: "A {cuisine} cafe menu layout, kraft-paper background, menu sections as separate text blocks, an elegant restrained palette, refined typography",
  },
};

app.registerExtension({
  name: "Eric.IdeogramMagicTemplates",
  async nodeCreated(node) {
    if (node.comfyClass !== NODE) return;
    const appW = node.widgets?.find((w) => w.name === "application");
    const ideaW = node.widgets?.find((w) => w.name === "idea");
    const arW = node.widgets?.find((w) => w.name === "aspect_ratio");
    if (!appW || !ideaW) return;

    const orig = appW.callback;
    appW.callback = function (v) {
      try { orig?.apply(this, arguments); } catch (e) { /* noop */ }
      const t = TEMPLATES[v];
      if (!t) return; // "(custom)" or unknown -> leave the idea box alone
      const cur = (ideaW.value || "").trim();
      if (cur && !confirm(`Replace the idea box with the "${v}" starter template?`)) return;
      ideaW.value = t.idea;
      if (arW && t.aspect) arW.value = t.aspect;
      node.setDirtyCanvas?.(true, true);
    };
  },
});
