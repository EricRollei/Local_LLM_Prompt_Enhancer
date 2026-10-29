/**
 * prompt_builder.js - video_prompter
 *
 * The panel on the Wildcard Prompt / Character Composer nodes: a composer where you type text between
 * wildcard pills, slot buttons that insert pills, one row of settings per pill, a live preview,
 * and a list viewer to fix, subset or exclude entries. A Find box searches every list by name
 * (and, through the catalog, by entries); "+ Button" / ☆ save your own buttons to
 * builders_user/my_buttons.yaml, shared by all builder nodes. The template bar saves the whole
 * composer to builders_user/templates/<name>.json and loads it back on any composer node.
 * "Merge lists…" in the list viewer folds a slot's lists into one list of your own
 * (<wildcards>/mine/<slot>/<name>.txt), shared entries first, for pruning by eye.
 * "More lists…" under the palette shows every usable list no button offers, grouped by path words.
 *
 * State lives as JSON in the node's hidden `composer` widget (format: core/builder/compose.py),
 * so it saves with the workflow. Everything the panel shows comes from the routes in
 * prompt_builder_support.py; the Python side builds the wildcard syntax, so preview and run match.
 *
 * Author: Eric Hiss (GitHub: EricRollei)
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const ROUTE = "/eric_prompt_builder";
const MODES = [
  ["random", "Random", "Any entry of the list."],
  ["fixed", "Fixed", "Always the first entry you picked, or your own text."],
  ["subset", "Subset", "Random among the entries you picked."],
  ["exclude", "Exclude", "Random, never the entries you picked."],
];
const KEEPS = [
  ["meaning", "Meaning", "The LLM polish may reword it but must keep the meaning."],
  ["exact", "Exact", "Kept word for word (names, LoRA triggers)."],
  ["loose", "Loose", "Inspiration only; the LLM may drop it."],
];
const MAX_COUNT = 8;
const MY_GROUP = "My buttons";
// Seed order of the sections (core/builder/compose.py SECTIONS): new sections are only appended.
const SEED_ORDER = ["subject", "action", "setting", "lighting", "style", "camera", "format", "composition", "text", "prompt"];
const FALLBACK_ORDER = ["format", "prompt", "subject", "action", "setting", "lighting", "composition", "camera", "style", "text"];
const SUBJECT_KINDS = [["", "Any type"], ["person", "Person"], ["animal", "Animal"], ["creature", "Creature"], ["object", "Object"],
  ["vehicle", "Vehicle"], ["food", "Food"], ["scene", "Scene only"]];
const PANELS = new Set();       // every open builder panel, so a saved button shows up on all of them

// ------------------------------------------------------------------ small helpers
const cache = { builders: null, sections: {}, platforms: null, slots: new Map(), templates: null };

async function templates(refresh = false) {
  if (refresh || !cache.templates) {
    cache.templates = getJSON(`${ROUTE}/templates`).then((d) => d.templates || []).catch((e) => { cache.templates = null; throw e; });
  }
  return cache.templates;
}

/** After a template is saved or deleted: every panel's template menu shows the new list. */
async function reloadTemplates() {
  await templates(true);
  for (const panel of PANELS) panel.renderTemplates();
}

async function getJSON(path) {
  const response = await api.fetchApi(path);
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.json();
}

async function postJSON(path, body) {
  const response = await api.fetchApi(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let detail = {};
    try { detail = await response.json(); } catch (e) { /* not JSON */ }
    const error = new Error(detail.error || `${path}: HTTP ${response.status}`);
    error.status = response.status;
    error.detail = detail;
    throw error;
  }
  return response.json();
}

async function builders() {
  if (!cache.builders) {
    const data = await getJSON(`${ROUTE}/builders`);
    cache.builders = Object.fromEntries(data.builders.map((b) => [b.id, b]));
    cache.sections = data.sections || {};
    cache.defaultOrder = data.default_order || FALLBACK_ORDER;
  }
  return cache.builders;
}

async function platforms() {
  if (!cache.platforms) {
    const data = await getJSON(`${ROUTE}/platforms`);
    cache.platforms = Object.fromEntries(data.platforms.map((p) => [p.id, p]));
  }
  return cache.platforms;
}

async function slotLists(builderId, slotId, nsfw, gender = "", violence = 0) {
  const key = `${builderId}|${slotId}|${nsfw}|${gender}|${violence}`;
  if (!cache.slots.has(key)) {
    cache.slots.set(key, getJSON(`${ROUTE}/slot?builder=${encodeURIComponent(builderId)}&slot=${encodeURIComponent(slotId)}&nsfw=${nsfw}&gender=${gender}&violence=${violence}`)
      .then((d) => d.lists)
      .catch((e) => { cache.slots.delete(key); throw e; }));
  }
  return cache.slots.get(key);
}

/** After a button is saved or deleted: fetch the definitions again and redraw every panel. */
async function reloadBuilders() {
  cache.builders = null;
  cache.slots.clear();
  const defs = await builders();
  for (const panel of PANELS) {
    if (!defs[panel.builderId]) continue;
    panel.def = defs[panel.builderId];
    panel.countsKey = null;
    panel.render();
    panel.loadSlotCounts();
  }
}

/** One line describing a list in a dropdown or the Find results. */
function listLabel(l) {
  return `${l.nsfw ? `${nsfwName(l.nsfw)} · ` : ""}${l.stars ? "★".repeat(l.stars) + " " : ""}${l.display || displayName(l.key)}${l.gender ? (l.gender === "female" ? " · women" : " · men") : ""}  (${l.count}${l.dialect === "tags" ? " · tags" : l.length ? ` · ${l.length}` : ""}${l.quality >= 0 ? ` · q${Math.round(l.quality * 100)}` : ""})`;
}

/** A short pill label from a list key: "pack_v10/black_female_names" -> "Black Female Names". */
function shortLabel(key) {
  return (displayName(key).split(" · ")[0] || key).slice(0, 28);
}

// NSFW levels, as the node's nsfw dropdown names them (core/wildcards/library.py NSFW_LEVELS).
const NSFW_LEVELS = ["off", "suggestive", "nudity", "explicit"];
const nsfwName = (rating) => NSFW_LEVELS[rating] || "";

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "style") node.style.cssText = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function titleCase(s) {
  return s.replace(/[_\-]+/g, " ").replace(/\s+/g, " ").trim().replace(/\b\w/g, (c) => c.toUpperCase());
}

/** "pack_v10/sub/cops_wc_hair-color" -> "Hair Color · Pack" */
function displayName(key) {
  const parts = key.split("/");
  const leaf = titleCase(parts[parts.length - 1].replace(/^cops_(bp_)?(male_|female_)?wc[-_]?/, "").replace(/^(cyber|bk|rd|fg3|vc|tr)_/, ""));
  if (parts.length === 1) return `${leaf} · top level`;
  const pack = parts[0].replace(/_v\d+.*$/, "").replace(/wildcards?/g, "").replace(/_+$/, "");
  return `${leaf} · ${titleCase(pack) || parts[0]}`;
}

function debounce(fn, ms) {
  let timer = null;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

// ------------------------------------------------------------------ styles (once)
function injectStyles() {
  if (document.getElementById("epb-styles")) return;
  const css = `
.epb{--epb-accent:#f0b454;--epb-accent-ink:#1b1b1f;--epb-sel:#6ea8fe;--epb-bg:var(--comfy-input-bg,#1e1e22);--epb-fg:var(--input-text,#ece8e1);
  --epb-muted:var(--descrip-text,#a8a39b);--epb-line:var(--border-color,#3a3a41);--epb-panel:var(--comfy-menu-bg,#232327);
  box-sizing:border-box;width:100%;height:100%;display:flex;flex-direction:column;gap:8px;padding:6px 8px;overflow:auto;
  font:12px/1.35 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--epb-fg)}
.epb *{box-sizing:border-box}
.epb h4{margin:0;font-size:10.5px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--epb-muted)}
.epb-sections{display:flex;flex-wrap:wrap;gap:4px;align-items:center}
.epb-chip{padding:2px 7px;border-radius:6px;border:1px dashed var(--epb-line);color:var(--epb-muted);font-size:11px}
.epb-chip.mine{border:1px solid var(--epb-line);color:var(--epb-fg);background:none}
.epb-arrow{color:var(--epb-muted);font-size:11px}
.epb-composer{display:flex;flex-wrap:wrap;gap:4px;align-items:center}
.epb-gap{height:26px;min-width:2.2ch;padding:0 5px;border-radius:5px;border:1px dashed var(--epb-line);background:transparent;color:var(--epb-fg);font:inherit;font-size:12.5px}
.epb-gap.filled{border-style:solid;border-color:transparent;background:rgba(255,255,255,.04)}
.epb-gap.caret{border:1px solid var(--epb-accent);box-shadow:0 0 0 2px rgba(240,180,84,.18)}
.epb-gap:focus{outline:none;border-color:var(--epb-accent)}
.epb-pill{display:inline-flex;align-items:center;height:26px;border-radius:13px;border:1px solid #b98a3a;background:#3a3120;color:#f7d9a4;font-size:12px}
.epb-pill.sel{border-color:var(--epb-sel);background:#1f3350;color:#dce9ff}
.epb-pill[draggable=true]{cursor:grab}
.epb-pill.dragging{opacity:.35}
.epb-pill.drop-before{box-shadow:-3px 0 0 0 var(--epb-sel)}
.epb-gap.drop-here{border:1px solid var(--epb-sel)!important;background:rgba(110,168,254,.15)!important;min-width:4ch}
.epb-pill.missing{border-color:#b9565d;background:#3a2224;color:#f3c1c4}
.epb-pill button{background:none;border:0;color:inherit;font:inherit;cursor:pointer;height:100%}
.epb-pill .lab{padding:0 3px 0 9px;font-weight:600}
.epb-pill .badge{padding:0 4px 0 0;font-family:ui-monospace,Consolas,monospace;font-size:10.5px;opacity:.85}
.epb-pill .x{padding:0 7px 0 3px;opacity:.7}
.epb-groups{display:flex;flex-direction:column;gap:4px}
.epb-group{display:flex;flex-direction:column;gap:2px}
.epb-group-name{font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--epb-muted);opacity:.8}
.epb-seg.small button{height:18px;padding:0 5px;font-size:10.5px}
.epb-palette{display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:4px}
.epb-slot{height:26px;padding:0 7px;border-radius:6px;border:1px solid var(--epb-line);background:var(--epb-panel);color:var(--epb-fg);font:inherit;font-size:11.5px;text-align:left;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.epb-slot:hover{border-color:var(--epb-accent)}
.epb-rows{display:flex;flex-direction:column;gap:3px}
.epb-row{display:flex;align-items:center;gap:6px;padding:3px 6px;border-radius:6px;border:1px solid var(--epb-line);background:rgba(255,255,255,.02)}
.epb-row.sel{border-color:#4b76b3;background:rgba(110,168,254,.08)}
.epb-row .who{width:128px;flex-shrink:0;background:none;border:0;padding:0;color:inherit;text-align:left;cursor:pointer;font:inherit}
.epb-row .who b{display:block;font-size:12px}
.epb-row .who small{display:block;color:var(--epb-muted);font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:ui-monospace,Consolas,monospace}
.epb-seg{display:flex;padding:1px;border-radius:6px;border:1px solid var(--epb-line);background:var(--epb-bg)}
.epb-seg button{height:22px;padding:0 6px;border:0;border-radius:4px;background:none;color:var(--epb-muted);font:inherit;font-size:11px;cursor:pointer}
.epb-seg button.on{background:var(--epb-accent);color:var(--epb-accent-ink);font-weight:600}
.epb-count{display:flex;align-items:center;border:1px solid var(--epb-line);border-radius:6px;background:var(--epb-bg)}
.epb-count button{width:20px;height:22px;border:0;background:none;color:var(--epb-fg);cursor:pointer}
.epb-count span{width:18px;text-align:center;font-family:ui-monospace,Consolas,monospace;font-size:11px}
.epb-now{margin-left:auto;min-width:0;flex:1;text-align:right;color:var(--epb-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:11.5px}
.epb-preview{padding:6px 8px;border-radius:7px;border:1px solid #36513a;background:#1f2a1f;color:#eef6ee}
.epb-preview .bar{display:flex;align-items:center;gap:8px;margin-bottom:3px}
.epb-preview .bar h4{color:#bfe0bf}
.epb-preview .meta{color:#a9c7a9;font-family:ui-monospace,Consolas,monospace;font-size:10.5px}
.epb-preview p{margin:0;font-size:13px;line-height:1.45}
.epb-preview .warn{margin-top:3px;color:#f0b454;font-size:11px}
.epb-btn{height:24px;padding:0 9px;border-radius:6px;border:1px solid var(--epb-line);background:var(--epb-panel);color:var(--epb-fg);font:inherit;font-size:11.5px;cursor:pointer}
.epb-btn.primary{border-color:var(--epb-accent);color:#f7d9a4;background:#3a3120}
.epb-btn.green{border-color:#4d6f50;background:#2c3d2c;color:#e3f2e3;margin-left:auto}
.epb-empty{padding:8px;border:1px dashed var(--epb-line);border-radius:6px;color:var(--epb-muted)}
.epb-tabs{display:flex;gap:4px}
.epb-chip{cursor:default;background:none;font:inherit}
button.epb-chip{cursor:pointer}
.epb-chip.active{background:var(--epb-accent);color:var(--epb-accent-ink);border-color:var(--epb-accent);font-weight:600}
.epb-chip.filled:not(.active){border-color:#b98a3a;color:#f7d9a4;background:rgba(240,180,84,.08)}
.epb-frame{display:flex;flex-direction:column;gap:4px;padding:6px;background:var(--epb-bg);border:1px solid var(--epb-line);border-radius:8px}
.epb-lane{border:1px solid transparent;border-radius:6px;padding:3px 4px}
.epb-lane.active{border-color:#b98a3a;background:rgba(240,180,84,.05)}
.epb-lane .head{display:flex;align-items:center;gap:6px;min-height:20px}
.epb-lane .head .name{background:none;border:0;padding:0;color:var(--epb-muted);font:inherit;font-size:10.5px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;cursor:pointer}
.epb-lane.active .head .name{color:var(--epb-accent)}
.epb-lane .head .hint{color:var(--epb-muted);font-size:10.5px;opacity:.75;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.epb-toggle{height:18px;padding:0 6px;border-radius:9px;border:1px solid var(--epb-line);background:none;color:var(--epb-muted);font:inherit;font-size:10.5px;cursor:pointer;display:inline-flex;align-items:center;gap:3px}
.epb-toggle.on{border-color:var(--epb-sel);color:#dce9ff;background:#1f3350}
.epb-toggle.fill.on{border-color:#7fb77e;color:#e3f2e3;background:#2c3d2c}
.epb-lane .flow{display:flex;flex-wrap:wrap;gap:4px;align-items:center;min-height:30px}
.epb-lane .llm{color:#a9c7a9;font-size:11px;font-style:italic;padding:0 4px}
.epb-rowshead{display:flex;align-items:baseline;gap:8px}
.epb-dialog{position:fixed;z-index:10000;width:460px;max-height:80vh;display:flex;flex-direction:column;background:var(--comfy-menu-bg,#202024);
  color:var(--input-text,#ece8e1);border:1px solid var(--border-color,#3a3a41);border-radius:10px;box-shadow:0 16px 48px rgba(0,0,0,.55);
  font:12.5px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif}
.epb-dialog header{display:flex;align-items:baseline;gap:8px;padding:10px 12px 6px;cursor:move}
.epb-dialog header b{font-size:15px}
.epb-dialog header span{color:var(--descrip-text,#a8a39b);font-size:11.5px;flex:1}
.epb-dialog .close{background:none;border:0;color:inherit;font-size:16px;cursor:pointer}
.epb-dialog .body{padding:0 12px;display:flex;flex-direction:column;gap:6px}
.epb-dialog select,.epb-dialog input{width:100%;height:28px;padding:0 8px;border-radius:6px;border:1px solid var(--border-color,#44444c);background:var(--comfy-input-bg,#26262b);color:inherit;font:inherit}
.epb-dialog label{display:flex;flex-direction:column;gap:3px;color:var(--descrip-text,#a8a39b);font-size:11px}
.epb-dialog .two{display:flex;gap:8px}.epb-dialog .two label{flex:1}
.epb-dialog .info{display:flex;justify-content:space-between;color:var(--descrip-text,#a8a39b);font-size:11px;padding:4px 12px}
.epb-dialog .entries{flex:1;overflow:auto;padding:0 12px 8px;display:flex;flex-direction:column;gap:3px;min-height:120px}
.epb-entry{display:flex;align-items:center;gap:8px;min-height:28px;padding:4px 8px;border-radius:6px;border:1px solid transparent;background:rgba(255,255,255,.03);color:inherit;font:inherit;text-align:left;cursor:pointer}
.epb-entry .box{flex-shrink:0;width:16px;height:16px;border-radius:4px;border:1px solid #5a5a63;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700}
.epb-entry.on{border-color:#b98a3a;background:#3a3120}.epb-entry.on .box{background:#f0b454;border-color:#f0b454;color:#1b1b1f}
.epb-entry.off{border-color:#b9565d;background:#3a2224}.epb-entry.off .box{background:#e0747b;border-color:#e0747b;color:#1b1b1f}
.epb-dialog{--epb-accent:#f0b454;--epb-accent-ink:#1b1b1f;--epb-sel:#6ea8fe;--epb-fg:var(--input-text,#ece8e1);
  --epb-muted:var(--descrip-text,#a8a39b);--epb-line:var(--border-color,#3a3a41)}
.epb-entry-row{display:flex;gap:4px;align-items:stretch}
.epb-entry-row .epb-entry{flex:1;min-width:0}
.epb-entry-row.dropped .txt{text-decoration:line-through;opacity:.55}
.epb-drop{flex-shrink:0;width:56px;border-radius:6px;border:1px solid transparent;background:none;color:var(--descrip-text,#a8a39b);font:inherit;font-size:11px;cursor:pointer;opacity:.6}
.epb-entry-row:hover .epb-drop{opacity:1;border-color:var(--border-color,#44444c)}
.epb-stars{display:flex;align-items:center;gap:2px}
.epb-nsfw{margin-left:8px;padding:1px 6px;border-radius:5px;background:#5a2227;color:#f3c1c4;font-size:10.5px;font-weight:600}
.epb-nsfw select{margin-left:4px;background:#3a1a1d;color:#f3c1c4;border:1px solid #6a3036;border-radius:4px;font-size:10.5px}
.epb-rate{flex-shrink:0;max-width:96px;background:none;color:#e0a4a8;border:1px solid #5a2227;border-radius:5px;font-size:10.5px}
.epb-entry-row.above .epb-entry{opacity:.45}
.epb-entry-row.above .epb-entry .txt{text-decoration:line-through dotted}
.epb-more{padding:6px;text-align:center;color:var(--descrip-text,#a8a39b);font-size:11px}
.epb-stars button{background:none;border:0;padding:0 2px;font-size:16px;line-height:1;color:#5a5a63;cursor:pointer}
.epb-stars button.on{color:#f0b454}
.epb-stars .epb-toggle{margin-left:8px;font-size:11px}
.epb-stars .q{margin-left:auto;color:var(--descrip-text,#a8a39b);font-size:11px}
.epb-dialog footer{display:flex;flex-wrap:wrap;gap:6px;padding:10px 12px;border-top:1px solid var(--border-color,#3a3a41)}
.epb-tpl{display:flex;flex-wrap:wrap;gap:4px;align-items:center}
.epb-tpl select,.epb-tpl input{height:24px;padding:0 6px;border-radius:6px;border:1px solid var(--epb-line);background:var(--epb-bg);color:var(--epb-fg);font:inherit;font-size:11.5px}
.epb-tpl select{max-width:260px}
.epb-tpl input{width:200px}
.epb-tpl input:focus,.epb-tpl select:focus{outline:none;border-color:var(--epb-accent)}
.epb-tpl .msg{color:var(--epb-muted);font-size:11px;flex:1;min-width:120px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.epb-tpl .msg.warn{color:#f0b454}
.epb-tpl .epb-btn{height:24px}
.epb-dialog.epb-merge{width:660px;max-height:88vh}
.epb-merge .srcs{max-height:130px;overflow:auto;display:flex;flex-direction:column;gap:1px;padding:4px;border:1px solid var(--border-color,#3a3a41);border-radius:6px}
.epb-merge .srcs label{flex-direction:row;align-items:center;gap:6px;color:inherit;font-size:11.5px;cursor:pointer}
.epb-merge .srcs input{width:auto;height:auto}
.epb-merge .srcs small{color:var(--descrip-text,#a8a39b)}
.epb-merge .bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:11px;color:var(--descrip-text,#a8a39b)}
.epb-merge .bar input[type=search]{flex:1;min-width:140px}
.epb-merge .stats{font-size:11.5px;color:var(--descrip-text,#a8a39b)}
.epb-merge .stats b{color:var(--input-text,#ece8e1)}
.epb-merge .mrows{flex:1;overflow:auto;padding:0 12px 8px;display:flex;flex-direction:column;gap:2px;min-height:160px;max-height:46vh}
.epb-mrow{display:flex;align-items:center;gap:8px;min-height:24px;padding:2px 8px;border-radius:5px;border:1px solid transparent;background:rgba(255,255,255,.03);color:inherit;font:inherit;font-size:12px;text-align:left;cursor:pointer}
.epb-mrow .box{flex-shrink:0;width:15px;height:15px;border-radius:4px;border:1px solid #5a5a63;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;background:#f0b454;border-color:#f0b454;color:#1b1b1f}
.epb-mrow.off{opacity:.45}.epb-mrow.off .box{background:none;border-color:#5a5a63;color:transparent}.epb-mrow.off .txt{text-decoration:line-through}
.epb-mrow .txt{flex:1;min-width:0}
.epb-mrow .n{flex-shrink:0;font-family:ui-monospace,Consolas,monospace;font-size:10.5px;color:var(--descrip-text,#a8a39b)}
.epb-mrow .n.core{color:#f7d9a4}
.epb-merge footer input[type=text]{width:180px;height:26px}
.epb-merge footer label{flex-direction:row;align-items:center;gap:5px}
.epb-merge footer label input{width:auto;height:auto}
.epb-slot.more{border-style:dashed;color:var(--epb-muted);text-align:center}
.epb-mine.arr{cursor:grab}.epb-mine.arr .epb-slot{cursor:grab;border-color:var(--epb-line)}
.epb-mine.arr .edit{width:auto;padding:0 5px;font-size:10px;border-color:var(--epb-line)}
.epb-mine.arr.is-hidden{opacity:.45}
.epb-mine.drop-before{box-shadow:-3px 0 0 0 var(--epb-sel)}
.epb-group-name.drop-on,.epb-chip.drop-on{outline:1px dashed var(--epb-sel);outline-offset:2px}
.epb-kind{height:18px;border-radius:9px;border:1px solid var(--epb-line);background:var(--epb-bg);color:var(--epb-fg);font:inherit;font-size:10.5px;padding:0 4px}
.epb-more-groups{display:flex;flex-wrap:wrap;gap:4px;max-height:150px;overflow:auto;padding:2px}
.epb-more-groups button{height:22px;padding:0 8px;border-radius:11px;border:1px solid var(--border-color,#44444c);background:none;color:inherit;font:inherit;font-size:11px;cursor:pointer}
.epb-more-groups button.on{background:#f0b454;border-color:#f0b454;color:#1b1b1f;font-weight:600}
.epb-more-groups button small{opacity:.7;margin-left:4px}
.epb-more-list .row{display:flex;gap:4px;align-items:stretch}
.epb-more-list .add{flex:1;min-width:0;display:flex;gap:8px;align-items:baseline;padding:3px 8px;border-radius:5px;border:1px solid transparent;background:rgba(255,255,255,.03);color:inherit;font:inherit;font-size:12px;text-align:left;cursor:pointer}
.epb-more-list .add:hover{border-color:#b98a3a}
.epb-more-list .add b{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.epb-more-list .add small{color:var(--descrip-text,#a8a39b);font-family:ui-monospace,Consolas,monospace;font-size:10.5px;white-space:nowrap}
.epb-more-list .keep{flex-shrink:0;border-radius:5px;border:1px solid var(--border-color,#44444c);background:none;color:var(--descrip-text,#a8a39b);font:inherit;font-size:11px;cursor:pointer;padding:0 7px}
.epb-more-list .tag{padding:0 5px;border-radius:4px;background:#5a2227;color:#f3c1c4;font-size:10px;font-weight:600}
.epb-rowshead .epb-find{margin-left:auto;width:220px;height:24px;padding:0 8px;border-radius:6px;border:1px solid var(--epb-line);background:var(--epb-bg);color:var(--epb-fg);font:inherit;font-size:11.5px}
.epb-rowshead .epb-find:focus{outline:none;border-color:var(--epb-accent)}
.epb-rowshead{align-items:center}
.epb-found{display:flex;flex-direction:column;gap:2px;padding:4px;border:1px solid var(--epb-line);border-radius:6px;background:var(--epb-bg)}
.epb-found .row{display:flex;gap:4px;align-items:stretch}
.epb-found-list{display:flex;flex-direction:column;gap:2px;max-height:380px;overflow-y:auto;padding-right:2px}
.epb-found .add{flex:1;min-width:0;display:flex;gap:8px;align-items:baseline;padding:3px 7px;border-radius:5px;border:1px solid transparent;background:rgba(255,255,255,.03);color:var(--epb-fg);font:inherit;font-size:11.5px;text-align:left;cursor:pointer}
.epb-found .add:hover{border-color:var(--epb-accent)}
.epb-found .add b{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.epb-found .add small{color:var(--epb-muted);font-size:10.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:ui-monospace,Consolas,monospace}
.epb-found .keep{flex-shrink:0;border-radius:5px;border:1px solid var(--epb-line);background:none;color:var(--epb-muted);font:inherit;font-size:11px;cursor:pointer;padding:0 7px}
.epb-found .keep:hover{color:#f7d9a4;border-color:#b98a3a}
.epb-found .foot{display:flex;gap:6px;align-items:center;padding:3px 2px 0;color:var(--epb-muted);font-size:11px}
.epb-found .tag{padding:0 5px;border-radius:4px;background:#5a2227;color:#f3c1c4;font-size:10px;font-weight:600}
.epb-mine{display:flex;min-width:0}
.epb-mine .epb-slot{flex:1;min-width:0;border-top-right-radius:0;border-bottom-right-radius:0;border-color:#8a6a33}
.epb-mine .edit{width:22px;flex-shrink:0;border:1px solid #8a6a33;border-left:0;border-radius:0 6px 6px 0;background:var(--epb-panel);color:var(--epb-muted);cursor:pointer;font-size:11px}
.epb-mine .edit:hover{color:#f7d9a4}
.epb-mine.empty .epb-slot{opacity:.55;border-style:dashed}
.epb-dialog .kinds{display:flex;gap:6px}
.epb-dialog .keys{display:flex;flex-direction:column;gap:3px;max-height:160px;overflow:auto}
.epb-dialog .keys div{display:flex;gap:6px;align-items:center;padding:3px 7px;border-radius:5px;background:rgba(255,255,255,.04);font-family:ui-monospace,Consolas,monospace;font-size:11px}
.epb-dialog .keys div span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.epb-dialog .keys button{background:none;border:0;color:inherit;cursor:pointer;opacity:.7}
.epb-dialog .matches{color:var(--descrip-text,#a8a39b);font-size:11px;padding:2px 0 6px;max-height:120px;overflow:auto}
`;
  document.head.append(el("style", { id: "epb-styles", text: css }));
}

// ------------------------------------------------------------------ state helpers
function emptyState() {
  return { v: 1, parts: {}, tokens: {}, next: 1, locks: {}, fill: {} };
}

const baseSection = (section) => section.replace(/_\d+$/, "");

function parseState(raw) {
  if (!raw || !String(raw).trim()) return null;
  try {
    const s = JSON.parse(raw);
    if (s && typeof s === "object" && s.parts && s.tokens) {
      s.next = s.next || 1 + Math.max(0, ...Object.keys(s.tokens).map(Number).filter(Number.isFinite));
      s.locks = s.locks || {};
      s.fill = s.fill || {};
      return s;
    }
  } catch (e) { /* not JSON: shown as one text gap */ }
  return { v: 1, parts: { subject: [{ t: "text", v: String(raw) }] }, tokens: {}, next: 1 };
}

/** Keep every part as text, tok, text, tok, ..., text (merges neighbouring text, drops dead pills). */
function normalise(state, sections) {
  for (const section of sections) {
    const segs = state.parts[section] || [];
    const out = [];
    for (const seg of segs) {
      if (seg.t === "tok" && !state.tokens[String(seg.id)]) continue;
      const last = out[out.length - 1];
      if (seg.t !== "tok") {
        const v = seg.v || "";
        if (last && last.t !== "tok") last.v = [last.v, v].filter((x) => x.trim()).join(" ");
        else out.push({ t: "text", v });
      } else {
        if (!last || last.t === "tok") out.push({ t: "text", v: "" });
        out.push({ t: "tok", id: seg.id });
      }
    }
    if (!out.length || out[out.length - 1].t === "tok") out.push({ t: "text", v: "" });
    state.parts[section] = out;
  }
  const used = new Set(Object.values(state.parts).flat().filter((s) => s.t === "tok").map((s) => String(s.id)));
  for (const id of Object.keys(state.tokens)) if (!used.has(id)) delete state.tokens[id];
  return state;
}

// ------------------------------------------------------------------ the panel
class BuilderPanel {
  constructor(node, builderId) {
    this.node = node;
    this.builderId = builderId;
    this.def = null;
    this.state = emptyState();
    this.part = null;          // section shown in the composer
    this.caret = null;         // {section, index} of the text gap that receives new pills
    this.sel = null;           // selected token id
    this.preview = { text: "", picks: {}, warnings: [] };
    this.dialog = null;
    this.root = el("div", { class: "epb" });
    this.root.addEventListener("keydown", (e) => e.stopPropagation());
    this.root.addEventListener("wheel", (e) => { if (this.root.scrollHeight > this.root.clientHeight) e.stopPropagation(); }, { passive: true });
    this.schedulePreview = debounce(() => this.refreshPreview(), 250);
    this.find = { q: "", lists: [], busy: false, error: "" };
    this.runFind = debounce(() => this.doFind(), 300);
    this.editor = null;
    this.merge = null;
    this.more = null;
    this.arrange = false;      // Arrange mode: drag / hide buttons
    this.dragSlot = null;      // a button being dragged (Arrange)
    this.dragSection = null;   // a section chip being dragged
    this.tpl = { mode: "", name: "", msg: "", warn: false };   // mode: '' | 'save' | 'replace' | 'delete'
    this.undo = null;           // {state, platform} before the last template load
    this.lostKeys = new Set();  // list keys a loaded template names that this library lacks
    PANELS.add(this);
  }

  widget(name) { return this.node.widgets?.find((w) => w.name === name); }
  /** The node's nsfw level. When the nsfw input is wired, the value of the widget it is wired from. */
  get nsfw() {
    const own = this.widget("nsfw")?.value || "off";
    const input = this.node.inputs?.find((i) => i.name === "nsfw" || i.widget?.name === "nsfw");
    if (input?.link == null) return own;
    try {
      const graph = this.node.graph || app.graph;
      const link = graph?.links?.get ? graph.links.get(input.link) : graph?.links?.[input.link];
      const source = link ? graph.getNodeById(link.origin_id) : null;
      const value = source?.widgets?.find((w) => NSFW_LEVELS.includes(w.value))?.value;
      return value || own;
    } catch (e) {
      return own;
    }
  }
  /** The node's violence_filter level: 0 off .. 3 (index in the widget's options, as the backend numbers them). */
  get violence() {
    const w = this.widget("violence_filter");
    const values = w?.options?.values || [];
    return Math.max(0, values.indexOf(w?.value));
  }
  /** This builder's sections, plus any Subject 2, 3 ... the user added. */
  get sections() {
    const parts = this.def?.parts || [{ section: "subject" }];
    const all = parts.map((p) => p.section);
    const own = parts.filter((p) => !p.optional || (this.state?.parts || {})[p.section]).map((p) => p.section);
    const extra = Object.keys(this.state?.parts || {}).filter((k) => !all.includes(k) && all.includes(baseSection(k)));
    return [...own, ...extra];
  }

  /** Optional sections (Text) this node could add with "+ Section". */
  get addableSections() {
    return (this.def?.parts || []).filter((p) => p.optional && !(this.state?.parts || {})[p.section]).map((p) => p.section);
  }

  /** The node's order: its own (dragged) order first, then the platform's. */
  get sectionOrder() {
    const platform = cache.platforms?.[this.widget("platform")?.value]?.order || cache.defaultOrder || FALLBACK_ORDER;
    const own = (this.state?.order || []).filter((s) => SEED_ORDER.includes(s));
    return [...own, ...platform.filter((s) => !own.includes(s))];
  }

  kindOf(section) {
    return (this.state.kinds || {})[section] || "";
  }

  setKind(section, kind) {
    this.state.kinds = this.state.kinds || {};
    if (kind) this.state.kinds[section] = kind;
    else delete this.state.kinds[section];
    if (kind && kind !== "person") this.setGender(section, "");   // Woman / Man only for people
    this.save();
    this.render();
  }

  /** Drag a section chip onto another: this node gets its own order (saved with it and its templates). */
  moveSection(from, to) {
    const order = this.sectionOrder.filter((s) => s !== from);
    order.splice(order.indexOf(to), 0, from);
    this.state.order = order;
    this.save();
    this.render();
  }

  addSection(section) {
    this.state.parts[section] = [{ t: "text", v: "" }];
    this.save();
    this.setPart(section, true);
  }

  partDef(section) {
    return this.def?.parts.find((p) => p.section === baseSection(section)) || { section, label: section, slots: [section], hint: "" };
  }

  sectionLabel(section) {
    const m = section.match(/^(.+)_(\d+)$/);
    const base = this.partDef(section).label || cache.sections[baseSection(section)] || section;
    return m ? `${base} ${m[2]}` : base;
  }

  /** Sections in the platform's order; Subject 2, 3 ... right after Subject. */
  orderedSections() {
    const order = this.sectionOrder;
    const rank = (s) => {
      const i = order.indexOf(baseSection(s));
      const n = (s.match(/_(\d+)$/) || [0, 1])[1];
      return (i < 0 ? 99 : i) * 100 + Number(n);
    };
    return [...this.sections].sort((a, b) => rank(a) - rank(b));
  }

  setPart(section, focusEnd = false) {
    this.part = section;
    const segs = this.state.parts[section] || [];
    this.caret = { section, index: Math.max(0, segs.length - 1) };
    this.render();
    if (focusEnd) this.focusGap(section, this.caret.index);
  }

  addSubject() {
    let n = 2;
    while (this.state.parts[`subject_${n}`]) n++;
    this.state.parts[`subject_${n}`] = [{ t: "text", v: "" }];
    this.save();
    this.setPart(`subject_${n}`, true);
  }

  removeSection(section) {
    delete this.state.parts[section];
    delete this.state.locks[section];
    delete this.state.fill[section];
    if (this.state.kinds) delete this.state.kinds[section];
    if (this.part === section) this.part = "subject";
    this.caret = null;
    this.save();
    this.render();
  }

  toggleLock(section) {
    if (section in this.state.locks) {
      delete this.state.locks[section];
    } else {
      // Hold the seed the section last rolled with (same rule as section_seed_offset in core/builder/compose.py).
      let seed = this.preview.seeds?.[section];
      if (seed === undefined) {
        const canonical = SEED_ORDER;
        const n = Number((section.match(/_(\d+)$/) || [0, 1])[1]);
        seed = Number(this.widget("seed")?.value || 0) + Math.max(0, canonical.indexOf(baseSection(section))) + 100 * (n - 1);
      }
      this.state.locks[section] = seed;
    }
    this.save();
    this.render();
  }

  genderOf(section) {
    return (this.state.gender || {})[section] || "";
  }

  sectionOfToken(id) {
    for (const section of this.sections) {
      if ((this.state.parts[section] || []).some((g) => g.t === "tok" && String(g.id) === String(id))) return section;
    }
    return this.part;
  }

  /** Woman / Man / Any for one section: lists named for the other are left out, matching ones come first.
   *  Pills still on Random move to the best list for the new choice; pills with picks keep their list. */
  async setGender(section, gender) {
    this.state.gender = this.state.gender || {};
    if (gender) this.state.gender[section] = gender;
    else delete this.state.gender[section];
    const pills = (this.state.parts[section] || []).filter((g) => g.t === "tok").map((g) => this.state.tokens[String(g.id)]);
    for (const token of pills) {
      if (!token || !token.slot || token.mode !== "random" || token.picks.length) continue;
      try {
        const lists = await slotLists(this.builderId, token.slot, this.nsfw, gender, this.violence);
        if (lists[0]) token.key = lists[0].key;
      } catch (e) { /* keep its list */ }
    }
    this.save();
    this.render();
  }

  /** Lists behind each slot button (buttons with none are hidden). */
  async loadSlotCounts() {
    const key = `${this.builderId}|${this.nsfw}|${this.violence}`;
    if (this.countsKey === key) return;
    this.countsKey = key;
    try {
      const data = await getJSON(`${ROUTE}/slot_counts?builder=${encodeURIComponent(this.builderId)}&nsfw=${this.nsfw}&violence=${this.violence}`);
      if (this.countsKey === key) {
        this.slotCounts = data.counts || null;
        this.nsfwOnly = new Set(data.nsfw_only || []);   // your buttons whose lists are all rated above off: hidden at nsfw off
        this.render();
      }
    } catch (e) { this.slotCounts = null; }
  }

  toggleFill(section) {
    if (this.state.fill[section]) delete this.state.fill[section];
    else this.state.fill[section] = true;
    this.save();
    this.render();
  }

  async init() {
    injectStyles();
    try {
      this.def = (await builders())[this.builderId];
    } catch (e) {
      this.root.replaceChildren(el("div", { class: "epb-empty" }, `Builder routes unavailable: ${e.message}. Restart ComfyUI after installing.`));
      return;
    }
    if (!this.def) {
      this.root.replaceChildren(el("div", { class: "epb-empty" }, `No builder definition "${this.builderId}" (builders/*.yaml).`));
      return;
    }
    this.part = this.sections[0];
    for (const name of ["platform", "nsfw", "violence_filter", "seed"]) {
      const w = this.widget(name);
      if (!w) continue;
      const original = w.callback;
      w.callback = (...args) => {
        const r = original?.apply(w, args);
        if (name === "nsfw" || name === "violence_filter") { cache.slots.clear(); this.countsKey = null; this.loadSlotCounts(); }
        if (name === "nsfw") { this.dialog?.reload?.(); this.prompts?.reload?.(); }
        this.render();
        this.schedulePreview();
        return r;
      };
    }
    await this.loadFromWidget();
    this.loadSlotCounts();
  }

  /** Read the composer widget (after creation or after a workflow loads). */
  async loadFromWidget() {
    if (!this.def) return;
    const raw = this.widget("composer")?.value;
    let state = parseState(raw);
    if (!state) {
      try {
        state = await getJSON(`${ROUTE}/starter?builder=${encodeURIComponent(this.builderId)}&nsfw=${this.nsfw}&violence=${this.violence}`);
      } catch (e) {
        state = emptyState();
      }
    }
    this.state = state;
    normalise(this.state, this.sections);
    if (!this.state.tokens[String(this.sel)]) this.sel = null;
    this.save(false);
    this.render();
    this.refreshPreview();
  }

  save(preview = true) {
    normalise(this.state, this.sections);
    const w = this.widget("composer");
    if (w) w.value = JSON.stringify(this.state);
    this.node.setDirtyCanvas?.(true, true);
    if (preview) this.schedulePreview();
  }

  // -------------------------------------------------- edits
  /** Put a new pill at the amber gap. Returns {id, section, index of the gap after it}. */
  insertToken(fields) {
    const section = this.caret && this.caret.section === this.part ? this.caret.section : this.part;
    const segs = this.state.parts[section] || (this.state.parts[section] = [{ t: "text", v: "" }]);
    let at = this.caret && this.caret.section === section ? this.caret.index : segs.length - 1;
    if (!segs[at] || segs[at].t === "tok") at = segs.length - 1;
    const id = this.state.next++;
    this.state.tokens[String(id)] = { slot: "", key: "", mode: "random", picks: [], count: 1, keep: "meaning", ...fields };
    segs.splice(at + 1, 0, { t: "tok", id }, { t: "text", v: "" });
    this.caret = { section, index: at + 2 };
    this.sel = id;
    return { id, section, at };
  }

  /** A pill straight from a Find result: that one list, no slot button behind it. */
  addList(info) {
    const { section, at } = this.insertToken({ key: info.key, label: info.label || shortLabel(info.key) });
    this.save();
    this.render();
    this.focusGap(section, at + 2);
  }

  async addSlot(slot) {
    const { id, section, at } = this.insertToken({ slot: slot.id });
    this.save(false);
    this.render();
    try {
      const lists = await slotLists(this.builderId, slot.id, this.nsfw, this.genderOf(section), this.violence);
      if (this.state.tokens[String(id)]) this.state.tokens[String(id)].key = lists[0]?.key || "";
    } catch (e) { console.warn("[Wildcard Composer]", e); }
    this.save();
    this.render();
    this.focusGap(section, at + 2);
  }

  removeToken(section, index) {
    const segs = this.state.parts[section];
    const token = segs[index];
    const before = segs[index - 1]?.v || "";
    const after = segs[index + 1]?.v || "";
    segs.splice(index - 1, 3, { t: "text", v: [before, after].filter((x) => x.trim()).join(" ") });
    delete this.state.tokens[String(token.id)];
    if (this.sel === token.id) this.sel = null;
    this.caret = { section, index: index - 1 };
    this.save();
    this.render();
    if (this.dialog && this.dialog.tokenId === token.id) this.closeDialog();
  }

  updateToken(id, patch) {
    const token = this.state.tokens[String(id)];
    if (!token) return;
    Object.assign(token, patch);
    this.save();
    this.render();
    this.dialog?.refresh();
  }

  focusGap(section, index) {
    requestAnimationFrame(() => {
      const input = this.root.querySelector(`input[data-section="${section}"][data-index="${index}"]`);
      input?.focus();
    });
  }

  // -------------------------------------------------- preview
  async refreshPreview() {
    if (!this.def) return;
    try {
      this.preview = await postJSON(`${ROUTE}/preview`, {
        builder: this.builderId,
        composer: this.widget("composer")?.value || "",
        seed: Number(this.widget("seed")?.value || 0),
        platform: this.widget("platform")?.value || "generic",
        nsfw: this.nsfw,
        violence: this.violence,
      });
    } catch (e) {
      this.preview = { text: "", picks: {}, warnings: [`preview failed: ${e.message}`] };
    }
    this.renderPreview();
    this.renderRows();
    this.fitNode();
  }

  // -------------------------------------------------- render
  render() {
    if (!this.def) return;
    if (!this.sections.includes(this.part)) this.part = this.sections[0];
    const shows = this.partDef(this.part).slots || [baseSection(this.part)];
    const counts = this.slotCounts;
    const kind = baseSection(this.part) === "subject" ? this.kindOf(this.part) : "";
    const slots = this.def.slots.filter((slot) => shows.includes(slot.section || "subject")
      && !(counts && counts[slot.id] === 0 && !slot.custom && !this.arrange)
      && !(this.nsfw === "off" && this.nsfwOnly?.has(slot.id))
      && (this.arrange || !slot.hidden)
      // The Subject type picks the subject buttons: Scene only shows none, other types their own.
      && !(kind && slot.section === "subject" && (kind === "scene" || ((slot.kinds || []).length && !slot.kinds.includes(kind)))));
    const find = el("input", {
      class: "epb-find", value: this.find.q, placeholder: "Find a list… (e.g. famous buildings)",
      title: "Search every wildcard list by name (and by entries, when the catalog is built). Click a result to insert it; ☆ saves it as a button.",
    });
    find.addEventListener("input", () => { this.find.q = find.value; this.runFind(); });
    find.addEventListener("keydown", (e) => { if (e.key === "Escape") { this.find = { q: "", lists: [] }; find.value = ""; this.renderFind(); } });
    this.root.replaceChildren(
      (this.tplBox = el("div", { class: "epb-tpl" })),
      this.sectionStrip(),
      this.composer(),
      el("div", { class: "epb-rowshead" }, el("h4", {}, `${this.sectionLabel(this.part)} · add a wildcard`), find,
        el("button", { class: "epb-btn", title: "Make your own button: one list, or every list whose name has some words", onclick: () => this.openEditor(this.find.q.trim() ? { search: this.find.q.trim(), label: titleCase(this.find.q.trim()) } : {}) }, "+ Button"),
        el("button", { class: `epb-btn${this.arrange ? " primary" : ""}`,
          title: "Arrange the buttons for every node: drag one onto another button, a group heading or a section chip; hide the ones you never use",
          onclick: () => { this.arrange = !this.arrange; this.render(); } }, this.arrange ? "Done" : "Arrange"),
        this.arrange ? el("button", { class: "epb-btn", title: "Back to the shipped layout (deletes builders_user/button_layout.yaml)",
          onclick: () => this.resetLayout() }, "Reset layout") : null),
      (this.findBox = el("div", { class: "epb-found", style: "display:none" })),
      this.palette(slots, counts),
      (this.rowsBox = el("div", { class: "epb-rows" })),
      (this.previewBox = el("div", { class: "epb-preview" })),
    );
    this.renderTemplates();
    this.renderFind();
    this.renderRows();
    this.renderPreview();
    this.fitNode();
  }

  // -------------------------------------------------- templates
  /** The template bar: load a saved template, save this composer as one, update, delete, undo a load. */
  async renderTemplates() {
    const box = this.tplBox;
    if (!box) return;
    let list = [];
    try { list = await templates(); } catch (e) { this.tpl.msg = `templates unavailable: ${e.message}`; this.tpl.warn = true; }
    if (box !== this.tplBox) return;          // redrawn meanwhile
    const current = this.state.template;      // {file, name} of the template this composer came from
    const select = el("select", {
      title: "Load a saved template (replaces what is on this node; Undo brings it back)",
      onchange: (e) => { if (e.target.value) this.loadTemplate(e.target.value); },
    },
      el("option", { value: "" }, list.length ? "Load template…" : "No saved templates yet"),
      list.map((t) => el("option", { value: t.file, selected: current?.file === t.file,
        title: `${t.starter ? "Starter template · " : ""}${t.sections.map((s) => cache.sections[s.replace(/_\d+$/, "")] || s).join(", ")} · ${t.pills} wildcards${t.saved ? ` · saved ${t.saved}` : ""}` },
        `${t.name}${t.starter ? " · starter" : ""}${t.builder && t.builder !== this.builderId ? ` (${t.builder})` : ""}`)));
    const items = [select];
    const mode = this.tpl.mode;
    if (mode === "save" || mode === "replace") {
      const name = el("input", { value: this.tpl.name, placeholder: "Template name" });
      name.addEventListener("input", () => { this.tpl.name = name.value; if (this.tpl.mode === "replace") { this.tpl.mode = "save"; this.renderTemplates(); } });
      name.addEventListener("keydown", (e) => { if (e.key === "Enter") this.saveTemplate(this.tpl.name, this.tpl.mode === "replace"); });
      items.push(name,
        el("button", { class: "epb-btn primary", onclick: () => this.saveTemplate(this.tpl.name, mode === "replace") }, mode === "replace" ? "Replace it" : "Save"),
        el("button", { class: "epb-btn", onclick: () => { this.tpl.mode = ""; this.tpl.msg = ""; this.renderTemplates(); } }, "Cancel"));
      requestAnimationFrame(() => { if (document.activeElement?.tagName !== "INPUT" || !this.root.contains(document.activeElement)) name.focus(); });
    } else if (mode === "delete") {
      items.push(el("span", { class: "msg warn" }, `Delete the template “${current?.name}”?`),
        el("button", { class: "epb-btn", onclick: () => this.deleteTemplate() }, "Delete"),
        el("button", { class: "epb-btn", onclick: () => { this.tpl.mode = ""; this.renderTemplates(); } }, "Keep"));
    } else {
      items.push(el("button", { class: "epb-btn", title: "Save everything on this node as a named template",
        onclick: () => { this.tpl = { mode: "save", name: "", msg: "", warn: false }; this.renderTemplates(); } }, "Save as…"),
        el("button", { class: "epb-btn", title: "Empty every field on this node, ready to start fresh (Undo brings it back)",
          onclick: () => this.clearComposer() }, "Clear"));
      if (current && !current.starter) {
        items.push(el("button", { class: "epb-btn", title: `Save the current node over “${current.name}”`, onclick: () => this.saveTemplate(current.name, true) }, "Update"),
          el("button", { class: "epb-btn", title: `Delete the template “${current.name}”`, onclick: () => { this.tpl.mode = "delete"; this.renderTemplates(); } }, "Delete"));
      }
      if (this.undo) items.push(el("button", { class: "epb-btn", title: "Put back what was on the node before the last template load or clear", onclick: () => this.undoTemplate() }, "Undo"));
    }
    if (mode !== "delete") items.push(el("span", { class: `msg${this.tpl.warn ? " warn" : ""}`, title: this.tpl.msg }, this.tpl.msg));
    box.replaceChildren(...items);
  }

  async saveTemplate(name, overwrite = false) {
    name = (name || "").trim();
    if (!name) { this.tpl.msg = "Give the template a name."; this.tpl.warn = true; this.renderTemplates(); return; }
    try {
      const data = await postJSON(`${ROUTE}/templates`, {
        action: "save", name, overwrite, builder: this.builderId,
        platform: this.widget("platform")?.value || "", composer: this.state,
      });
      this.state.template = { file: data.template.file, name: data.template.name };
      this.save(false);
      this.tpl = { mode: "", name: "", msg: `Saved “${data.template.name}”.`, warn: false };
      await reloadTemplates();
    } catch (e) {
      if (e.status === 409) this.tpl = { mode: "replace", name, msg: `“${name}” exists already.`, warn: true };
      else this.tpl = { ...this.tpl, msg: `Could not save: ${e.message}`, warn: true };
      this.renderTemplates();
    }
  }

  async deleteTemplate() {
    const current = this.state.template;
    if (!current || current.starter) return;
    try {
      await postJSON(`${ROUTE}/templates`, { action: "delete", file: current.file });
      delete this.state.template;
      this.save(false);
      this.tpl = { mode: "", name: "", msg: `Deleted “${current.name}”.`, warn: false };
    } catch (e) {
      this.tpl = { mode: "", name: "", msg: `Could not delete: ${e.message}`, warn: true };
    }
    for (const panel of PANELS) if (panel.state.template?.file === current.file && panel !== this) delete panel.state.template;
    await reloadTemplates();
  }

  /** Replace this node's composer with a saved template. Sections this node doesn't have are left out. */
  async loadTemplate(file) {
    let data;
    try {
      data = await getJSON(`${ROUTE}/template?file=${encodeURIComponent(file)}&nsfw=${this.nsfw}`);
    } catch (e) {
      this.tpl = { mode: "", name: "", msg: `Could not load: ${e.message}`, warn: true };
      this.renderTemplates();
      return;
    }
    const platformWidget = this.widget("platform");
    this.undo = { state: JSON.stringify(this.state), platform: platformWidget?.value };
    const state = parseState(JSON.stringify(data.composer || {})) || emptyState();
    const own = new Set((this.def.parts || []).map((p) => p.section));
    const left = Object.keys(state.parts).filter((section) => !own.has(baseSection(section))
      && (state.parts[section] || []).some((g) => g.t === "tok" || (g.v || "").trim()));
    for (const section of Object.keys(state.parts)) if (!own.has(baseSection(section))) delete state.parts[section];
    state.locks = {};
    for (const key of ["fill", "gender"]) {
      for (const section of Object.keys(state[key] || {})) if (!own.has(baseSection(section))) delete state[key][section];
    }
    state.template = { file, name: data.name || file, starter: !!data.starter };
    const choices = platformWidget?.options?.values;
    if (data.platform && platformWidget && (!Array.isArray(choices) || choices.includes(data.platform))) platformWidget.value = data.platform;
    this.lostKeys = new Set((data.missing || []).map((k) => k.toLowerCase()));
    this.state = state;
    normalise(this.state, this.sections);
    this.sel = null;
    this.caret = null;
    this.part = this.sections[0];
    const notes = [`Loaded “${state.template.name}”.`];
    if (left.length) notes.push(`Left out (not on this node): ${left.map((s) => cache.sections[baseSection(s)] || s).join(", ")}.`);
    if (this.lostKeys.size) notes.push(`${this.lostKeys.size} list${this.lostKeys.size > 1 ? "s" : ""} not in this library (red pills).`);
    this.tpl = { mode: "", name: "", msg: notes.join(" "), warn: left.length > 0 || this.lostKeys.size > 0 };
    this.save(false);
    this.render();
    this.refreshPreview();
  }

  undoTemplate() {
    if (!this.undo) return;
    const { state, platform } = this.undo;
    this.undo = null;
    this.state = parseState(state) || emptyState();
    const platformWidget = this.widget("platform");
    if (platformWidget && platform !== undefined) platformWidget.value = platform;
    this.lostKeys = new Set();
    normalise(this.state, this.sections);
    this.sel = null;
    this.caret = null;
    this.tpl = { mode: "", name: "", msg: "Undone.", warn: false };
    this.save(false);
    this.render();
    this.refreshPreview();
  }

  /** Empty every field, keeping the platform. Undo restores what was here. */
  clearComposer() {
    this.undo = { state: JSON.stringify(this.state), platform: this.widget("platform")?.value };
    this.state = emptyState();
    this.lostKeys = new Set();
    normalise(this.state, this.sections);
    this.sel = null;
    this.caret = null;
    this.part = this.sections[0];
    this.tpl = { mode: "", name: "", msg: "Cleared. Undo brings it back.", warn: false };
    this.save(false);
    this.render();
    this.refreshPreview();
  }

  // -------------------------------------------------- find
  async doFind() {
    const q = this.find.q.trim();
    if (q.length < 2) { this.find.lists = []; this.find.error = ""; this.renderFind(); return; }
    this.find.busy = true;
    this.renderFind();
    try {
      const gender = this.genderOf(this.part);
      const data = await getJSON(`${ROUTE}/find?q=${encodeURIComponent(q)}&nsfw=${this.nsfw}&gender=${gender}&limit=400&violence=${this.violence}`);
      if (this.find.q.trim() !== q) return;          // typed on meanwhile
      this.find.lists = data.lists || [];
      this.find.capped = !!data.capped;
      this.find.shown = 60;
      this.find.scroll = 0;
      this.find.error = "";
    } catch (e) {
      this.find.lists = [];
      this.find.error = e.message;
    }
    this.find.busy = false;
    this.renderFind();
    this.fitNode();
  }

  renderFind() {
    const box = this.findBox;
    if (!box) return;
    const q = this.find.q.trim();
    if (q.length < 2) { box.style.display = "none"; box.replaceChildren(); return; }
    box.style.display = "";
    const all = this.find.lists || [];
    const shown = this.find.shown || 60;
    const rows = all.slice(0, shown).map((l) => el("div", { class: "row" },
      el("button", { class: "add", title: `${l.key}\nInsert at the amber gap`, onclick: () => this.addList(l) },
        l.nsfw ? el("span", { class: "tag" }, nsfwName(l.nsfw)) : null,
        el("b", {}, l.display || displayName(l.key)),
        el("small", {}, `${l.count}${l.dialect === "tags" ? " · tags" : ` · ${l.length}`}${l.quality >= 0 ? ` · q${Math.round(l.quality * 100)}` : ""}${l.gender ? (l.gender === "female" ? " · women" : " · men") : ""}`)),
      el("button", { class: "keep", title: "Save this list as a button", onclick: () => this.openEditor({ lists: [l.key], label: shortLabel(l.key) }) }, "☆ Button")));
    const more = this.find.capped ? "+ lists \u00b7 the likeliest; add a word to narrow them" : " lists";
    // Every hit, in a box that scrolls; the next 60 rows load as you near the end.
    const list = el("div", { class: "epb-found-list" }, ...rows,
      all.length > shown ? el("div", { class: "foot" }, `scroll for more (${shown} of ${all.length})`) : null);
    list.addEventListener("wheel", (e) => e.stopPropagation(), { passive: true });
    list.addEventListener("scroll", () => {
      this.find.scroll = list.scrollTop;
      if (all.length > (this.find.shown || 60) && list.scrollTop + list.clientHeight > list.scrollHeight - 120) {
        this.find.shown = (this.find.shown || 60) + 60;
        this.renderFind();
      }
    });
    requestAnimationFrame(() => { list.scrollTop = this.find.scroll || 0; });
    box.replaceChildren(...(rows.length ? [list] : []),
      el("div", { class: "foot" },
        el("span", {}, this.find.busy ? "searching…" : this.find.error ? this.find.error
          : rows.length ? `${all.length}${more}` : "no list names have all these words"),
        el("button", { class: "epb-btn", style: "margin-left:auto", title: "A button that always offers every list whose name has these words",
          onclick: () => this.openEditor({ search: q, label: titleCase(q) }) }, `☆ Button for “${q}”`),
        el("button", { class: "epb-btn", onclick: () => { this.find = { q: "", lists: [] }; this.render(); } }, "Close")));
  }

  // -------------------------------------------------- my buttons
  /** Make or edit one of your buttons. initial: {id?, label, section?, lists?, search?, tokenId?}. */
  openEditor(initial = {}) {
    this.closeEditor();
    const panel = this;
    const b = {
      id: initial.id || "",
      label: initial.label || "",
      section: initial.section || baseSection(this.part || "subject"),
      lists: [...(initial.lists || [])],
      search: initial.search || "",
      kind: (initial.lists || []).length && !initial.search ? "lists" : "search",
      matches: null,
      error: "",
    };
    const box = el("div", { class: "epb-dialog", role: "dialog" });
    box.addEventListener("keydown", (e) => { e.stopPropagation(); if (e.key === "Escape") panel.closeEditor(); });
    const rect = this.root.getBoundingClientRect();
    box.style.left = `${Math.max(8, Math.min(window.innerWidth - 480, rect.right + 12))}px`;
    box.style.top = `${Math.max(8, Math.min(window.innerHeight - 460, rect.top + 40))}px`;
    document.body.append(box);
    this.editor = box;

    const countMatches = debounce(async () => {
      const q = b.search.trim();
      if (q.length < 2) { b.matches = null; draw(); return; }
      try {
        const data = await getJSON(`${ROUTE}/find?q=${encodeURIComponent(q)}&names=1&nsfw=${panel.nsfw}&limit=100&violence=${panel.violence}`);
        if (b.search.trim() === q) { b.matches = data.lists || []; draw(false); }
      } catch (e) { b.matches = null; }
    }, 300);

    const save = async () => {
      const button = { id: b.id, label: b.label.trim(), section: b.section };
      if (b.kind === "lists") button.lists = b.lists; else button.search = b.search.trim();
      try {
        const data = await postJSON(`${ROUTE}/buttons`, { action: "save", button });
        // A pill the button was made from now belongs to it.
        const token = initial.tokenId !== undefined ? panel.state.tokens[String(initial.tokenId)] : null;
        if (token && !token.slot) { token.slot = data.button.id; delete token.label; panel.save(); }
        panel.closeEditor();
        await reloadBuilders();
      } catch (e) { b.error = `could not save: ${e.message}`; draw(); }
    };
    const remove = async () => {
      try {
        await postJSON(`${ROUTE}/buttons`, { action: "delete", id: b.id });
        panel.closeEditor();
        await reloadBuilders();
      } catch (e) { b.error = `could not delete: ${e.message}`; draw(); }
    };

    const draw = (full = true) => {
      if (!full && box.querySelector(".matches")) {
        box.querySelector(".matches").replaceChildren(...matchLines());
        return;
      }
      const header = el("header", {}, el("b", {}, b.id ? "Edit button" : "New button"),
        el("span", {}, "Saved in builders_user/my_buttons.yaml, shared by every builder node"),
        el("button", { class: "close", "aria-label": "Close", onclick: () => panel.closeEditor() }, "✕"));
      makeDraggable(box, header);
      const label = el("input", { value: b.label, placeholder: "Button label" });
      label.addEventListener("input", () => { b.label = label.value; });
      const sectionSelect = el("select", { onchange: (e) => { b.section = e.target.value; } },
        (cache.defaultOrder || FALLBACK_ORDER).map((s) => el("option", { value: s, selected: s === b.section }, cache.sections[s] || s)));
      const kinds = el("div", { class: "epb-seg kinds" },
        el("button", { class: b.kind === "lists" ? "on" : "", disabled: !b.lists.length, title: b.lists.length ? "Always these lists" : "Add lists from Find with ☆ Button",
          onclick: () => { b.kind = "lists"; draw(); } }, `Specific list${b.lists.length > 1 ? "s" : ""} (${b.lists.length})`),
        el("button", { class: b.kind === "search" ? "on" : "", title: "Every list whose name has all these words, now and as you add packs",
          onclick: () => { b.kind = "search"; draw(); countMatches(); } }, "Category: name words"));
      let body;
      if (b.kind === "lists") {
        body = el("div", { class: "keys" }, b.lists.map((key) => el("div", {}, el("span", { title: key }, key),
          el("button", { title: "Remove", onclick: () => { b.lists = b.lists.filter((k) => k !== key); if (!b.lists.length) b.kind = "search"; draw(); } }, "✕"))));
      } else {
        const words = el("input", { value: b.search, placeholder: "e.g. famous buildings   or   black female names" });
        words.addEventListener("input", () => { b.search = words.value; countMatches(); });
        body = el("label", {}, el("span", {}, "Words that must all be in a list's name (folders count; 'female' / 'male' follow the list's gender)"), words);
      }
      box.replaceChildren(header,
        el("div", { class: "body" },
          el("div", { class: "two" }, el("label", {}, el("span", {}, "Label"), label), el("label", {}, el("span", {}, "Section"), sectionSelect)),
          kinds, body,
          b.kind === "search" ? el("div", { class: "matches" }, ...matchLines()) : null,
          b.error ? el("div", { class: "warn", style: "color:#f0b454" }, b.error) : null),
        el("footer", {},
          el("button", { class: "epb-btn primary", onclick: save }, "Save button"),
          b.id ? el("button", { class: "epb-btn", onclick: remove }, "Delete") : null,
          el("button", { class: "epb-btn", style: "margin-left:auto", onclick: () => panel.closeEditor() }, "Cancel")));
      if (full) (b.label ? null : label)?.focus();
    };
    const matchLines = () => {
      if (b.matches === null) return [b.search.trim().length < 2 ? "Type at least one word." : "counting…"];
      if (!b.matches.length) return ["No list names have all these words yet."];
      return [`${b.matches.length}${b.matches.length >= 100 ? "+" : ""} lists: `,
        b.matches.slice(0, 8).map((l) => l.display || displayName(l.key)).join(" · ") + (b.matches.length > 8 ? " …" : "")];
    };
    draw();
    if (b.kind === "search") countMatches();
  }

  closeEditor() {
    this.editor?.remove();
    this.editor = null;
  }

  // -------------------------------------------------- more lists
  closeMore() {
    this.more?.element.remove();
    this.more = null;
  }

  /** Every usable list no button offers for this part's sections, grouped by path words. */
  async openMore() {
    this.closeMore();
    const panel = this;
    const ownSections = this.partDef(this.part).slots || [baseSection(this.part)];
    let sections = ownSections;
    const m = { element: el("div", { class: "epb-dialog epb-merge", role: "dialog" }), data: null, group: 0, q: "", shown: 200, error: "", unsorted: false };
    this.more = m;
    m.element.addEventListener("keydown", (e) => { e.stopPropagation(); if (e.key === "Escape") panel.closeMore(); });
    m.element.style.left = `${Math.max(8, (window.innerWidth - 660) / 2)}px`;
    m.element.style.top = `${Math.max(8, window.innerHeight * 0.06)}px`;
    document.body.append(m.element);

    const lists = () => {
      const q = m.q.trim().toLowerCase();
      if (!m.data) return [];
      if (q) return m.data.groups.flatMap((g) => g.lists).filter((l) => (l.key + " " + (l.display || "")).toLowerCase().includes(q));
      return m.data.groups[m.group]?.lists || [];
    };
    const draw = () => {
      const label = m.unsorted ? "no clear section" : sections.map((s) => cache.sections[s] || s).join(" + ");
      const header = el("header", {}, el("b", {}, `More lists · ${label}`),
        el("span", {}, m.data ? `${m.data.total} lists no button offers, in ${m.data.groups.length} groups` : m.error || "sorting your lists…"),
        el("button", { class: "close", "aria-label": "Close", onclick: () => panel.closeMore() }, "✕"));
      makeDraggable(m.element, header);
      const d = m.data;
      const search = el("input", { type: "search", value: m.q, placeholder: "filter by name…" });
      search.addEventListener("input", () => { m.q = search.value; m.shown = 200; drawList(); });
      const chips = el("div", { class: "epb-more-groups" }, (d?.groups || []).map((g, i) => el("button", {
        class: !m.q && i === m.group ? "on" : "",
        onclick: () => { m.group = i; m.q = ""; m.shown = 200; draw(); },
      }, g.label, el("small", {}, String(g.count)))));
      const g = d?.groups[m.group];
      const groupBar = el("div", { class: "bar" },
        g && !m.q ? el("button", { class: "epb-btn", title: "A button that offers every list of this group (in My buttons)",
          onclick: () => panel.openEditor({ lists: g.lists.map((l) => l.key), label: g.label, section: ownSections[0] }) },
          `☆ Button for all ${g.count} “${g.label}” lists`) : null,
        d && (d.unsorted || m.unsorted) ? el("button", { class: "epb-btn", style: "margin-left:auto",
          title: "Lists whose name, folder and content don't point to one section",
          onclick: () => { m.unsorted = !m.unsorted; load(); } }, m.unsorted ? "← Back to this section" : `${d.unsorted} lists with no clear section →`) : null);
      m.listBox = el("div", { class: "mrows epb-more-list" });
      m.listBox.addEventListener("scroll", () => {
        const box = m.listBox;
        if (box.scrollTop + box.clientHeight > box.scrollHeight - 200 && m.shown < lists().length) { m.shown += 200; drawList(); }
      });
      m.element.replaceChildren(header, el("div", { class: "body" }, search, chips, groupBar), m.listBox,
        el("footer", {}, el("span", { class: "stats" }, "Click a list to insert it at the amber gap; ☆ saves one as a button."),
          el("button", { class: "epb-btn", style: "margin-left:auto", onclick: () => panel.closeMore() }, "Close")));
      drawList();
    };
    const drawList = () => {
      if (!m.listBox) return;
      const all = lists();
      const top = m.listBox.scrollTop;
      m.listBox.replaceChildren(...all.slice(0, m.shown).map((l) => el("div", { class: "row" },
        el("button", { class: "add", title: `${l.key}\nInsert at the amber gap`, onclick: () => panel.addList(l) },
          l.nsfw ? el("span", { class: "tag" }, nsfwName(l.nsfw)) : null,
          el("b", {}, l.display || displayName(l.key)),
          el("small", {}, `${l.count}${l.dialect === "tags" ? " · tags" : ` · ${l.length}`}${l.quality >= 0 ? ` · q${Math.round(l.quality * 100)}` : ""}${l.gender ? (l.gender === "female" ? " · women" : " · men") : ""}`)),
        el("button", { class: "keep", title: "Save this list as a button", onclick: () => panel.openEditor({ lists: [l.key], label: shortLabel(l.key), section: ownSections[0] }) }, "☆"))),
        all.length > m.shown ? el("div", { class: "epb-more" }, `scroll for more (${m.shown} of ${all.length})`) : null,
        m.data && !all.length ? el("div", { class: "epb-more" }, m.q ? "no list matches" : "nothing here") : null);
      m.listBox.scrollTop = top;
    };
    const load = async () => {
      sections = m.unsorted ? ["_unsorted"] : ownSections;
      m.data = null; m.group = 0; m.q = ""; m.shown = 200; m.error = "";
      draw();
      try {
        m.data = await getJSON(`${ROUTE}/more?builder=${encodeURIComponent(panel.builderId)}&sections=${sections.join(",")}&nsfw=${panel.nsfw}&violence=${panel.violence}`);
        if (m.data.note) m.error = m.data.note;
      } catch (e) { m.error = e.message; }
      if (panel.more === m) draw();
    };
    load();
  }

  // -------------------------------------------------- prompt files (_prompts): the Prompt line's browser
  closePrompts() {
    this.prompts?.element.remove();
    this.prompts = null;
  }

  /**
   * Walk the prompt files (_prompts/<pack>/<theme>/...), look at a file's prompts, and insert a file or a whole
   * folder at the amber gap. replaceId: swap that pill's file instead (from the pill dialog).
   */
  async openPrompts(replaceId = null) {
    this.closePrompts();
    if (!document.getElementById("epb-prompts-css")) {
      document.head.append(el("style", { id: "epb-prompts-css" }, `
        .epb-crumbs { display: flex; flex-wrap: wrap; gap: 4px; margin: 4px 0; }
        .epb-prompt-preview { max-height: 240px; overflow: auto; margin: 0 0 8px 18px; padding: 4px 8px;
          border-left: 2px solid rgba(255,190,80,.6); font-size: 11px; line-height: 1.35; }
        .epb-prompt-line { padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,.07); white-space: normal; }
        .epb-prompt-line.above { opacity: .4; }
        .epb-prompt-line.gone { text-decoration: line-through; opacity: .5; }`));
    }
    const panel = this;
    const p = { element: el("div", { class: "epb-dialog epb-merge", role: "dialog" }), folder: "prompts", q: "",
      data: null, error: "", open: null, preview: null, listBox: null, stats: null };
    this.prompts = p;
    p.reload = () => load(true);
    p.element.addEventListener("keydown", (e) => { e.stopPropagation(); if (e.key === "Escape") panel.closePrompts(); });
    p.element.style.left = `${Math.max(8, (window.innerWidth - 660) / 2)}px`;
    p.element.style.top = `${Math.max(8, window.innerHeight * 0.06)}px`;
    document.body.append(p.element);

    const leafName = (key) => titleCase(key.split("/").pop() || key);
    const choose = (key, label) => {
      const id = replaceId === null ? null : String(replaceId);
      if (id !== null && panel.state.tokens[id]) {
        panel.updateToken(replaceId, { key, label, picks: [], mode: "random" });
        if (panel.dialog && String(panel.dialog.tokenId) === id) panel.openDialog(replaceId);
      } else {
        panel.addList({ key, label });
      }
      panel.closePrompts();
    };
    const statsText = () => {
      const d = p.data;
      if (!d) return p.error || "reading your prompt files\u2026";
      if (p.q.trim()) return `${d.here} files match${d.more ? ` (first ${d.lists.length} shown)` : ""}`;
      return `${d.folders.length} folders \u00b7 ${d.lists.length} files here${d.more ? ` (+${d.more} more)` : ""} \u00b7 ${d.here} files in all`;
    };
    const previewBox = () => {
      const pr = p.preview;
      if (!pr) return el("div", { class: "epb-prompt-preview" }, "loading\u2026");
      return el("div", { class: "epb-prompt-preview" },
        pr.entries.map((e) => el("div", { class: `epb-prompt-line${e.above ? " above" : ""}${e.dropped ? " gone" : ""}`,
          title: e.above ? `left out at ${panel.nsfw}` : "" }, e.text)),
        pr.total > pr.entries.length ? el("div", { class: "epb-more" },
          `${pr.entries.length} of ${pr.total}. Use the file, then click its pill to see, search and pick from all of them.`) : null,
        !pr.total ? el("div", { class: "epb-more" }, "no prompts at this NSFW level") : null);
    };
    const togglePreview = async (key) => {
      if (p.open === key) { p.open = null; drawList(); return; }
      p.open = key;
      p.preview = null;
      drawList();
      try {
        p.preview = await getJSON(`${ROUTE}/list?key=${encodeURIComponent(key)}&limit=40&nsfw=${panel.nsfw}`);
      } catch (e) {
        p.preview = { entries: [], total: 0 };
        p.error = e.message;
      }
      if (panel.prompts === p && p.open === key) drawList();
    };
    const drawList = () => {
      if (!p.listBox) return;
      if (p.stats) p.stats.textContent = statsText();
      const d = p.data;
      const rows = [];
      if (d && !p.q.trim() && d.here && d.folder !== "prompts") {
        rows.push(el("div", { class: "row" },
          el("button", { class: "add", title: `${d.folder}/*\nEach roll draws a prompt from any file in this folder`,
            onclick: () => choose(`${d.folder}/*`, `${leafName(d.folder)} (all)`) },
            el("b", {}, `Use the whole folder: ${leafName(d.folder)}`), el("small", {}, `${d.here} files`))));
      }
      for (const f of d?.folders || []) {
        rows.push(el("div", { class: "row" },
          el("button", { class: "add", title: `${f.key}\nOpen this folder`, onclick: () => { p.folder = f.key; p.q = ""; load(true); } },
            el("b", {}, `\u{1F4C1} ${titleCase(f.name)}`), el("small", {}, `${f.lists} files`))));
      }
      for (const l of d?.lists || []) {
        rows.push(el("div", { class: "row" },
          el("button", { class: "add", title: `${l.key}\nClick to read its prompts`, onclick: () => togglePreview(l.key) },
            l.nsfw ? el("span", { class: "tag" }, nsfwName(l.nsfw)) : null,
            el("b", {}, p.q.trim() ? l.name : titleCase(l.name)), el("small", {}, `${l.count} prompts`)),
          el("button", { class: "keep", title: replaceId === null ? "Insert this file at the amber gap" : "Use this file for the pill",
            onclick: () => choose(l.key, shortLabel(l.key)) }, "Use")));
        if (p.open === l.key) rows.push(previewBox());
      }
      if (d && !rows.length) rows.push(el("div", { class: "epb-more" }, p.q.trim() ? "no prompt file matches" : "nothing here"));
      const top = p.listBox.scrollTop;
      p.listBox.replaceChildren(...rows);
      p.listBox.scrollTop = top;
    };
    const draw = () => {
      p.stats = el("span", {}, statsText());
      const header = el("header", {}, el("b", { title: "The node's nsfw setting: files and prompts above it are left out" },
        `${replaceId === null ? "Prompt files" : "Prompt files \u00b7 swap this pill"} \u00b7 browsing at: ${panel.nsfw}`), p.stats,
        el("button", { class: "close", "aria-label": "Close", onclick: () => panel.closePrompts() }, "\u00d7"));
      makeDraggable(p.element, header);
      const search = el("input", { type: "search", value: p.q, placeholder: "find prompt files by name, in every folder\u2026" });
      search.addEventListener("input", debounce(() => { p.q = search.value; load(false); }, 250));
      const parts = p.folder.split("/");
      const crumbs = el("div", { class: "epb-crumbs" }, parts.map((part, i) => el("button", {
        class: `epb-btn${i === parts.length - 1 ? " primary" : ""}`,
        onclick: () => { p.folder = parts.slice(0, i + 1).join("/"); p.q = ""; load(true); },
      }, i ? titleCase(part) : "All prompts")));
      p.listBox = el("div", { class: "mrows epb-more-list" });
      p.element.replaceChildren(header, el("div", { class: "body" }, search, crumbs), p.listBox,
        el("footer", {}, el("span", { class: "stats" }, "Click a file to read its prompts; Use inserts it. A whole folder draws from all its files."),
          el("button", { class: "epb-btn", style: "margin-left:auto", onclick: () => panel.closePrompts() }, "Close")));
      drawList();
    };
    const load = async (redraw) => {
      p.data = null; p.open = null; p.error = "";
      if (redraw) draw(); else drawList();
      try {
        p.data = await getJSON(`${ROUTE}/prompts?folder=${encodeURIComponent(p.folder)}&q=${encodeURIComponent(p.q.trim())}&nsfw=${panel.nsfw}`);
      } catch (e) { p.error = e.message; }
      if (panel.prompts === p) drawList();
    };
    load(true);
  }

  // -------------------------------------------------- merging a slot's lists
  closeMerge() {
    this.merge?.element.remove();
    this.merge = null;
  }

  /** Fold the lists behind a pill's slot into one list of your own (mine/<slot>/<name>). */
  async openMerge(tokenId, lists) {
    this.closeMerge();
    const panel = this;
    const token = this.state.tokens[String(tokenId)];
    if (!token?.slot) return;
    const slotDef = this.def.slots.find((s) => s.id === token.slot) || { id: token.slot, label: token.slot };
    if (!lists?.length) {
      try { lists = await slotLists(this.builderId, token.slot, this.nsfw, this.genderOf(this.sectionOfToken(tokenId)), this.violence); } catch (e) { lists = []; }
    }
    lists = lists.filter((l) => !l.key.startsWith(`mine/${token.slot}/`));   // not your earlier merges
    const m = {
      element: el("div", { class: "epb-dialog epb-merge", role: "dialog" }),
      chosen: new Set(lists.map((l) => l.key)),
      data: null, off: new Set(), min: 1, len: "any", q: "", shown: 300,
      name: "merged", hide: false, busy: false, error: "", exists: false,
    };
    this.merge = m;
    m.element.addEventListener("keydown", (e) => { e.stopPropagation(); if (e.key === "Escape") panel.closeMerge(); });
    m.element.style.left = `${Math.max(8, (window.innerWidth - 660) / 2)}px`;
    m.element.style.top = `${Math.max(8, window.innerHeight * 0.06)}px`;
    document.body.append(m.element);

    const lengthOf = (row) => (row.words <= 4 ? "short" : row.words <= 8 ? "medium" : "long");
    const kept = () => (m.data?.rows || []).filter((r) => r.lists >= m.min && (m.len === "any" || lengthOf(r) === m.len));
    const shown = () => { const q = m.q.trim().toLowerCase(); return q ? kept().filter((r) => r.text.toLowerCase().includes(q)) : kept(); };

    const build = async () => {
      m.busy = true; m.error = ""; draw();
      try {
        m.data = await postJSON(`${ROUTE}/merge/preview`, { builder: panel.builderId, slot: token.slot, keys: lists.filter((l) => m.chosen.has(l.key)).map((l) => l.key), nsfw: panel.nsfw });
      } catch (e) { m.data = null; m.error = e.message; }
      m.busy = false; m.shown = 300; draw();
    };
    const rebuild = debounce(build, 400);

    const save = async (overwrite = false) => {
      const entries = kept().filter((r) => !m.off.has(r.text)).map((r) => r.text);
      try {
        const result = await postJSON(`${ROUTE}/merge/save`, {
          builder: panel.builderId, slot: token.slot, name: m.name, entries, sources: m.data?.keys || [],
          hide_sources: m.hide, overwrite, nsfw: panel.nsfw,
        });
        cache.slots.clear();
        panel.closeMerge();
        panel.updateToken(tokenId, { key: result.key, picks: [], mode: "random" });
        panel.countsKey = null; panel.loadSlotCounts();
        panel.openDialog(tokenId);
      } catch (e) {
        m.exists = e.status === 409;
        m.error = m.exists ? `“${m.name}” exists for this button.` : `Could not save: ${e.message}`;
        draw();
      }
    };

    const rowButton = (r) => el("button", {
      class: `epb-mrow${m.off.has(r.text) ? " off" : ""}`,
      title: `${r.lists} of ${m.data.keys.length} lists: ${r.sources.slice(0, 6).map((i) => displayName(m.data.keys[i])).join(", ")}${r.sources.length > 6 ? " …" : ""}${r.variants.length ? `\nAlso spelled: ${r.variants.join(" | ")}` : ""}\nClick to leave it out`,
      onclick: (e) => {
        if (m.off.has(r.text)) m.off.delete(r.text); else m.off.add(r.text);
        e.currentTarget.classList.toggle("off", m.off.has(r.text));
        drawCounts();
      },
    }, el("span", { class: "box" }, "✓"), el("span", { class: "txt" }, r.text),
      r.variants.length ? el("span", { class: "n" }, `+${r.variants.length}`) : null,
      el("span", { class: `n${r.lists >= 3 ? " core" : ""}` }, `×${r.lists}`));

    const drawCounts = () => {
      const box = m.element.querySelector(".keepcount");
      if (!box) return;
      const k = kept();
      const saving = k.filter((r) => !m.off.has(r.text)).length;
      box.textContent = `Saves ${saving} of ${k.length} entries${m.min > 1 ? ` (in ${m.min}+ lists)` : ""}${m.len !== "any" ? `, ${m.len} only` : ""}`;
    };

    const draw = () => {
      const header = el("header", {}, el("b", {}, `Merge lists · ${slotDef.label}`),
        el("span", {}, "Shared entries first. Untick what you don't want; save as your own list."),
        el("button", { class: "close", "aria-label": "Close", onclick: () => panel.closeMerge() }, "✕"));
      makeDraggable(m.element, header);
      const srcs = el("div", { class: "srcs" }, lists.map((l) => {
        const box = el("input", { type: "checkbox" });
        box.checked = m.chosen.has(l.key);
        box.addEventListener("change", () => { if (box.checked) m.chosen.add(l.key); else m.chosen.delete(l.key); rebuild(); });
        return el("label", { title: l.key }, box, listLabel(l));
      }));
      const d = m.data;
      const stats = el("div", { class: "stats" }, m.busy ? "merging…" : m.error && !d ? m.error : d
        ? [el("b", {}, String(d.keys.length)), " lists · ", el("b", {}, String(d.entries)), " entries → ", el("b", {}, String(d.rows.length)),
          " unique · ", el("b", {}, String(d.rows.filter((r) => r.lists >= 3).length)), " in 3+ lists · ", el("b", {}, String(d.shared)), " in 2+"]
        : "");
      const search = el("input", { type: "search", value: m.q, placeholder: "find in the merged list…" });
      search.addEventListener("input", () => { m.q = search.value; m.shown = 300; drawRows(); });
      const seg = (values, current, onSet) => el("div", { class: "epb-seg" }, values.map(([v, label]) =>
        el("button", { class: current === v ? "on" : "", onclick: () => { onSet(v); draw(); } }, label)));
      const bar = el("div", { class: "bar" }, search,
        "in", seg([[1, "any"], [2, "2+"], [3, "3+"], [5, "5+"]], m.min, (v) => { m.min = v; m.shown = 300; }), "lists",
        seg([["any", "Any"], ["short", "Short"], ["medium", "Medium"], ["long", "Long"]], m.len, (v) => { m.len = v; m.shown = 300; }));
      const bulk = el("div", { class: "bar" },
        el("button", { class: "epb-btn", title: "Leave out every entry shown (use with the search box)", onclick: () => { shown().forEach((r) => m.off.add(r.text)); drawRows(); } }, "Untick shown"),
        el("button", { class: "epb-btn", title: "Keep every entry shown", onclick: () => { shown().forEach((r) => m.off.delete(r.text)); drawRows(); } }, "Tick shown"),
        el("span", { class: "keepcount", style: "margin-left:auto" }));
      m.rowsBox = el("div", { class: "mrows" });
      m.rowsBox.addEventListener("scroll", () => {
        const box = m.rowsBox;
        if (box.scrollTop + box.clientHeight > box.scrollHeight - 200 && m.shown < shown().length) { m.shown += 300; drawRows(true); }
      });
      const name = el("input", { type: "text", value: m.name, title: "Saved as mine/<button>/<name>.txt in your wildcard folder" });
      name.addEventListener("input", () => { m.name = name.value; if (m.exists) { m.exists = false; m.error = ""; draw(); name.focus(); } });
      const hide = el("input", { type: "checkbox" });
      hide.checked = m.hide;
      hide.addEventListener("change", () => { m.hide = hide.checked; });
      m.element.replaceChildren(header,
        el("div", { class: "body" },
          el("div", { class: "bar" }, `Source lists (${m.chosen.size} of ${lists.length})`,
            el("button", { class: "epb-btn", onclick: () => { lists.forEach((l) => m.chosen.add(l.key)); draw(); rebuild(); } }, "All"),
            el("button", { class: "epb-btn", onclick: () => { m.chosen.clear(); draw(); rebuild(); } }, "None")),
          srcs, stats, bar, bulk),
        m.rowsBox,
        el("footer", {},
          el("label", {}, "Name", name),
          el("label", { title: "Hidden lists stop showing on every button (their exact __name__ still works). Undo per list with Hide list in the viewer." }, hide, "Hide the source lists"),
          m.error && d ? el("span", { style: "color:#f0b454;font-size:11px" }, m.error) : null,
          el("button", { class: "epb-btn primary", style: "margin-left:auto", disabled: !d || m.busy, onclick: () => save(m.exists) }, m.exists ? "Replace it" : "Save list"),
          el("button", { class: "epb-btn", onclick: () => panel.closeMerge() }, "Cancel")));
      drawRows();
    };

    const drawRows = (append = false) => {
      if (!m.rowsBox) return;
      if (!m.data) { m.rowsBox.replaceChildren(); drawCounts(); return; }
      const all = shown();
      const top = m.rowsBox.scrollTop;
      m.rowsBox.replaceChildren(...all.slice(0, m.shown).map(rowButton),
        all.length > m.shown ? el("div", { class: "epb-more" }, `scroll for more (${m.shown} of ${all.length})`) : null,
        !all.length ? el("div", { class: "epb-more" }, "nothing here") : null);
      if (append) m.rowsBox.scrollTop = top;
      drawCounts();
    };

    draw();
    build();
  }

  /** Slot buttons, under their group headings (Person, Face & hair, Clothing, ...) when the YAML gives groups. */
  palette(slots, counts) {
    const plain = (slot) => el("button", {
      class: "epb-slot",
      title: `${slot.tooltip ? slot.tooltip + "\n" : ""}Insert ${slot.label} at the amber gap${counts && counts[slot.id] ? ` (${counts[slot.id]} lists)` : ""}`,
      onclick: () => this.addSlot(slot),
    }, slot.label);
    const button = (slot) => {
      if (!slot.custom) return plain(slot);
      const none = counts && counts[slot.id] === 0;
      const what = slot.search ? `lists named with “${slot.search}”` : slot.lists.join(", ");
      const b = plain(slot);
      b.title = `${slot.label}: ${what}${none ? "\nNo list matches right now." : counts && counts[slot.id] ? ` (${counts[slot.id]} lists)` : ""}`;
      return el("div", { class: `epb-mine${none ? " empty" : ""}` }, b,
        el("button", { class: "edit", title: "Edit or delete this button", onclick: () => this.openEditor({ ...slot }) }, "✎"));
    };
    /** Arrange mode: every button can be dragged (onto another button, a group heading or a section chip) and hidden. */
    const arranged = (slot) => {
      const main = el("button", { class: "epb-slot", title: `${slot.label} · drag to move · ${slot.section}${slot.group ? " / " + slot.group : ""}` }, slot.label);
      const box = el("div", { class: `epb-mine arr${slot.hidden ? " is-hidden" : ""}`, draggable: "true" }, main,
        el("button", { class: "edit", title: slot.hidden ? "Show this button again" : "Hide this button (Arrange shows it)",
          onclick: () => this.hideSlot(slot.id, !slot.hidden) }, slot.hidden ? "show" : "hide"));
      box.addEventListener("dragstart", (e) => {
        this.dragSlot = slot.id;
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", `epb-slot:${slot.id}`);
      });
      box.addEventListener("dragend", () => { this.dragSlot = null; });
      box.addEventListener("dragover", (e) => { if (this.dragSlot && this.dragSlot !== slot.id) { e.preventDefault(); e.stopPropagation(); box.classList.add("drop-before"); } });
      box.addEventListener("dragleave", () => box.classList.remove("drop-before"));
      box.addEventListener("drop", (e) => {
        box.classList.remove("drop-before");
        if (!this.dragSlot || this.dragSlot === slot.id) return;
        e.preventDefault(); e.stopPropagation();
        this.moveSlot(this.dragSlot, { section: slot.section, group: slot.group || "", before: slot.id });
      });
      return box;
    };
    const make = this.arrange ? arranged : button;
    slots = [...slots.filter((s) => s.group === MY_GROUP), ...slots.filter((s) => s.group !== MY_GROUP)];
    const more = el("button", { class: "epb-slot more", title: "Every usable list no button above offers, grouped by the words in their paths", onclick: () => this.openMore() }, "More lists…");
    // The Prompt line: its button opens the prompt-file browser instead of More lists.
    const browse = baseSection(this.part) === "prompt" ? el("button", { class: "epb-slot more",
      title: "Your prompt files (_prompts), folder by folder: read a file's prompts and insert a file or a whole folder",
      onclick: () => this.openPrompts() }, "Browse prompts\u2026") : null;
    const groups = [];
    for (const slot of slots) {
      const name = slot.group || "";
      let group = groups.find((g) => g.name === name);
      if (!group) groups.push(group = { name, slots: [] });
      group.slots.push(slot);
    }
    const heading = (g) => {
      const head = el("span", { class: "epb-group-name" }, g.name || (this.arrange ? "(no heading)" : ""));
      if (this.arrange) {
        head.addEventListener("dragover", (e) => { if (this.dragSlot) { e.preventDefault(); head.classList.add("drop-on"); } });
        head.addEventListener("dragleave", () => head.classList.remove("drop-on"));
        head.addEventListener("drop", (e) => {
          head.classList.remove("drop-on");
          if (!this.dragSlot) return;
          e.preventDefault(); e.stopPropagation();
          this.moveSlot(this.dragSlot, { section: g.slots[0].section, group: g.name });
        });
      }
      return head;
    };
    if (groups.length <= 1 && !this.arrange) return el("div", { class: "epb-palette" }, slots.map(make), browse || more);
    return el("div", { class: "epb-groups" }, groups.map((g) => el("div", { class: "epb-group" },
      g.name || this.arrange ? heading(g) : null,
      el("div", { class: "epb-palette" }, g.slots.map(make)))),
      this.arrange ? null : el("div", { class: "epb-palette" }, browse || more));
  }

  // -------------------------------------------------- button layout (builders_user/button_layout.yaml)
  /** Move a button: to a section (its chip), under a group heading, or before another button. */
  async moveSlot(slotId, { section, group, before }) {
    this.dragSlot = null;
    const slot = this.def.slots.find((s) => s.id === slotId);
    if (!slot) return;
    const target = section || slot.section;
    const sectionIds = this.def.slots.filter((s) => s.section === target).map((s) => s.id);
    const payload = { action: "move", slot: slotId, section: target, before: before || null, section_ids: sectionIds };
    if (group !== undefined) payload.group = group;
    else if (target !== slot.section) payload.group = "";
    try { await postJSON(`${ROUTE}/layout`, payload); } catch (e) { console.warn("[Wildcard Composer]", e); }
    await reloadBuilders();
  }

  async hideSlot(slotId, hidden) {
    try { await postJSON(`${ROUTE}/layout`, { action: "hide", slot: slotId, hidden }); } catch (e) { console.warn("[Wildcard Composer]", e); }
    await reloadBuilders();
  }

  async resetLayout() {
    try { await postJSON(`${ROUTE}/layout`, { action: "reset" }); } catch (e) { console.warn("[Wildcard Composer]", e); }
    await reloadBuilders();
  }

  /** Grow the node so the whole panel shows without an inner scrollbar (never shrinks it). */
  fitNode() {
    requestAnimationFrame(() => {
      const missing = this.root.scrollHeight - this.root.clientHeight;
      if (missing > 2 && this.node.size[1] < 1600) {
        this.node.setSize([this.node.size[0], Math.min(1600, this.node.size[1] + missing + 4)]);
        this.node.setDirtyCanvas?.(true, true);
      }
    });
  }

  sectionStrip() {
    const platform = this.widget("platform")?.value || "generic";
    const info = cache.platforms?.[platform];
    if (!cache.platforms) platforms().then(() => this.render()).catch(() => {});
    const optional = new Set((this.def.parts || []).filter((p) => p.optional).map((p) => p.section));
    const mine = new Set(this.sections.map(baseSection));
    const own = (this.state.order || []).length > 0;
    const order = this.sectionOrder.filter((s) => mine.has(s) || !optional.has(s));
    const strip = el("div", { class: "epb-sections", title: own ? "This node's own order (drag the chips). Platform order puts it back."
      : `${info?.structure || "Generic order"}\nDrag a chip to give this node its own order.` });
    order.forEach((section, i) => {
      if (i) strip.append(el("span", { class: "epb-arrow" }, "→"));
      if (!mine.has(section)) {
        strip.append(el("span", { class: "epb-chip", title: "Filled by another node or the LLM" }, cache.sections[section] || section));
        return;
      }
      for (const name of this.orderedSections().filter((s) => baseSection(s) === section)) {
        const filled = (this.state.parts[name] || []).some((g) => g.t === "tok" || (g.v || "").trim());
        const chip = el("button", {
          class: `epb-chip mine${name === this.part ? " active" : ""}${filled ? " filled" : ""}`,
          draggable: "true",
          onclick: () => this.setPart(name, true),
        }, this.sectionLabel(name));
        chip.addEventListener("dragstart", (e) => {
          if (this.dragSlot) return;
          this.dragSection = section;
          e.dataTransfer.effectAllowed = "move";
          e.dataTransfer.setData("text/plain", `epb-section:${section}`);
        });
        chip.addEventListener("dragend", () => { this.dragSection = null; });
        chip.addEventListener("dragover", (e) => {
          if (this.dragSection || this.dragSlot) { e.preventDefault(); e.stopPropagation(); chip.classList.add("drop-on"); }
        });
        chip.addEventListener("dragleave", () => chip.classList.remove("drop-on"));
        chip.addEventListener("drop", (e) => {
          chip.classList.remove("drop-on");
          if (this.dragSlot) { e.preventDefault(); e.stopPropagation(); this.moveSlot(this.dragSlot, { section }); return; }
          if (!this.dragSection || this.dragSection === section) return;
          e.preventDefault(); e.stopPropagation();
          const from = this.dragSection;
          this.dragSection = null;
          this.moveSection(from, section);
        });
        strip.append(chip);
      }
    });
    if (this.def.parts.some((p) => p.multi)) {
      strip.append(el("button", { class: "epb-toggle", title: "Add another subject, kept with its own attributes", onclick: () => this.addSubject() }, "+ Subject"));
    }
    for (const section of this.addableSections) {
      strip.append(el("button", { class: "epb-toggle", title: this.partDef(section).hint || "", onclick: () => this.addSection(section) }, `+ ${cache.sections[section] || section}`));
    }
    if (own) {
      strip.append(el("button", { class: "epb-toggle", title: "Drop this node's own order and follow the platform again",
        onclick: () => { delete this.state.order; this.save(); this.render(); } }, "Platform order"));
    }
    return strip;
  }

  composer() {
    const frame = el("div", { class: "epb-frame", title: "Type between the pills. Click a gap to make it the insert point." });
    const toFill = new Set(this.preview.to_fill || []);
    for (const section of this.orderedSections()) {
      const segs = this.state.parts[section] || (this.state.parts[section] = [{ t: "text", v: "" }]);
      const active = section === this.part;
      const empty = !segs.some((g) => g.t === "tok" || (g.v || "").trim());
      const locked = section in (this.state.locks || {});
      const fill = !!this.state.fill?.[section];
      const lane = el("div", { class: `epb-lane${active ? " active" : ""}` });
      lane.addEventListener("mousedown", (e) => {
        if (this.part === section || e.target.closest("button")) return;
        // Switching sections redraws the palette and rows; put the cursor back where the user clicked.
        const gap = e.target.closest("input[data-index]");
        const index = gap ? Number(gap.dataset.index) : (this.state.parts[section] || []).length - 1;
        e.preventDefault();
        this.part = section;
        this.caret = { section, index };
        this.render();
        this.focusGap(section, index);
      });
      lane.append(el("div", { class: "head" },
        el("button", { class: "name", onclick: () => this.setPart(section, true) }, this.sectionLabel(section)),
        el("span", { class: "hint" }, this.partDef(section).hint || ""),
        baseSection(section) === "subject"
          ? el("select", { class: "epb-kind", title: "What the subject is: picks which buttons the palette shows. Scene only = no subject at all.",
            onchange: (e) => this.setKind(section, e.target.value) },
            SUBJECT_KINDS.map(([value, label]) => el("option", { value, selected: this.kindOf(section) === value }, label)))
          : null,
        (this.partDef(section).slots || [baseSection(section)]).includes("subject") && ["", "person"].includes(this.kindOf(section))
          ? el("div", { class: "epb-seg small", title: "Which lists the slot buttons use in this section: named for women, for men, or any" },
            ...[["", "Any"], ["female", "Woman"], ["male", "Man"]].map(([value, label]) => el("button", {
              class: this.genderOf(section) === value ? "on" : "",
              onclick: () => this.setGender(section, value),
            }, label)))
          : null,
        el("button", {
          class: `epb-toggle${locked ? " on" : ""}`,
          title: locked ? `Held at seed ${this.state.locks[section]}. Click to let it re-roll.` : "Keep this section's picks when re-rolling the rest",
          onclick: () => this.toggleLock(section),
        }, locked ? "Locked" : "Lock"),
        el("button", {
          class: `epb-toggle fill${fill ? " on" : ""}`,
          title: "When this section is empty, ask the LLM rewriter to write it (needs llm_instructions → wildcard_instructions)",
          onclick: () => this.toggleFill(section),
        }, "LLM fills"),
        /_\d+$/.test(section) || this.partDef(section).optional
          ? el("button", { class: "epb-toggle", title: /_\d+$/.test(section) ? "Remove this subject" : "Remove this section", onclick: () => this.removeSection(section) }, "✕") : null));
      const flow = el("div", { class: "flow" });
      segs.forEach((seg, index) => {
        if (seg.t === "tok") {
          flow.append(this.pill(section, index, seg));
          return;
        }
        const isCaret = this.caret ? this.caret.section === section && this.caret.index === index : active && index === segs.length - 1;
        const input = el("input", {
          class: `epb-gap${seg.v ? " filled" : ""}${isCaret ? " caret" : ""}`,
          placeholder: "+",
          "data-section": section,
          "data-index": String(index),
          "aria-label": `${this.sectionLabel(section)} text`,
          style: `width:${Math.max(2.2, (seg.v || "").length * 0.92 + 1.6)}ch`,
        });
        input.value = seg.v || "";
        input.addEventListener("focus", () => {
          if (!this.caret || this.caret.section !== section || this.caret.index !== index) {
            this.caret = { section, index };
            this.root.querySelectorAll(".epb-gap").forEach((g) => g.classList.toggle("caret", g === input));
          }
        });
        this.dropTarget(input, "drop-here", () => ({ section, seg }));
        input.addEventListener("input", () => {
          seg.v = input.value;
          input.style.width = `${Math.max(2.2, input.value.length * 0.92 + 1.6)}ch`;
          input.classList.toggle("filled", !!input.value);
          const w = this.widget("composer");
          if (w) w.value = JSON.stringify(this.state);
          this.schedulePreview();
        });
        flow.append(input);
      });
      if (this.kindOf(section) === "scene") flow.replaceChildren(el("span", { class: "llm" }, "Scene only: no subject (left out of the prompt; the LLM is told not to add one)"));
      else if (empty && fill) flow.append(el("span", { class: "llm" }, toFill.has(section) ? "the LLM writes this section" : "LLM fills (when empty)"));
      lane.append(flow);
      frame.append(lane);
    }
    return frame;
  }

  badge(token) {
    let b = "random";
    if (token.mode === "fixed" && token.picks.length) b = "fixed";
    else if (token.mode === "subset" && token.picks.length) b = `${token.picks.length} picked`;
    else if (token.mode === "exclude" && token.picks.length) b = `−${token.picks.length}`;
    if (token.count > 1 && token.mode !== "fixed") b += ` ×${token.count}`;
    return b;
  }

  slotLabel(token) {
    return this.def.slots.find((s) => s.id === token.slot)?.label || token.label || token.slot || "Wildcard";
  }

  pill(section, index, seg) {
    const token = this.state.tokens[String(seg.id)];
    const lost = !!token.key && this.lostKeys.has(token.key.toLowerCase());
    const missing = lost || (!token.key && !(token.mode === "fixed" && token.picks.length) && !(token.mode === "subset" && token.picks.length));
    const tip = `${token.key ? token.key + (lost ? "  (not in this library: pick another source list)" : "") : "no list found for this slot"}\nClick: open its list; new wildcards then go right after it.\nDrag: move it (drop on a gap or on another wildcard).`;
    const pill = el("span", {
      class: `epb-pill${this.sel === seg.id ? " sel" : ""}${missing ? " missing" : ""}`,
      draggable: "true",
      "data-token": String(seg.id),
      title: tip,
    },
      el("button", { class: "lab", onclick: () => this.select(seg.id, true, section, index) }, this.slotLabel(token)),
      el("button", { class: "badge", onclick: () => this.select(seg.id, true, section, index) }, missing ? (lost ? "missing" : "no list") : this.badge(token)),
      el("button", { class: "x", "aria-label": "Remove wildcard", title: "Remove", onclick: () => this.removeToken(section, index) }, "✕"));
    pill.addEventListener("dragstart", (e) => {
      this.dragging = seg.id;
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", `epb-token:${seg.id}`);
      requestAnimationFrame(() => pill.classList.add("dragging"));
    });
    pill.addEventListener("dragend", () => {
      this.dragging = null;
      pill.classList.remove("dragging");
      this.root.querySelectorAll(".drop-before,.drop-here").forEach((n) => n.classList.remove("drop-before", "drop-here"));
    });
    // Dropping on a wildcard puts the dragged one just before it.
    this.dropTarget(pill, "drop-before", () => {
      const segs = this.state.parts[section] || [];
      const at = segs.findIndex((g) => g.t === "tok" && g.id === seg.id);
      return at > 0 ? { section, seg: segs[at - 1] } : null;
    });
    return pill;
  }

  /** Make an element accept a dragged wildcard. where() -> {section, seg: the text gap to insert after}. */
  dropTarget(node, cssClass, where) {
    node.addEventListener("dragover", (e) => {
      if (this.dragging === null || this.dragging === undefined) return;
      e.preventDefault();
      e.stopPropagation();
      e.dataTransfer.dropEffect = "move";
      node.classList.add(cssClass);
    });
    node.addEventListener("dragleave", () => node.classList.remove(cssClass));
    node.addEventListener("drop", (e) => {
      if (this.dragging === null || this.dragging === undefined) return;
      e.preventDefault();
      e.stopPropagation();          // keep ComfyUI's own drop handler (workflow files) out of it
      node.classList.remove(cssClass);
      const target = where();
      const id = this.dragging;
      this.dragging = null;
      if (target) this.moveToken(id, target.section, target.seg);
    });
  }

  /** Move a wildcard to just after the text gap `targetSeg` (in any section). */
  moveToken(id, targetSection, targetSeg) {
    let fromSection = null;
    let fromIndex = -1;
    for (const section of this.sections) {
      const i = (this.state.parts[section] || []).findIndex((g) => g.t === "tok" && g.id === id);
      if (i >= 0) { fromSection = section; fromIndex = i; break; }
    }
    if (fromSection === null) return;
    const from = this.state.parts[fromSection];
    const before = from[fromIndex - 1];
    const after = from[fromIndex + 1];
    if (targetSeg === before || targetSeg === after) return;   // dropped where it already is
    // Take it out; the text on either side closes up, as when a wildcard is removed.
    const merged = { t: "text", v: [before?.v || "", after?.v || ""].filter((x) => x.trim()).join(" ") };
    from.splice(fromIndex - 1, 3, merged);
    const to = this.state.parts[targetSection];
    const at = to.indexOf(targetSeg);
    if (at < 0) return;
    to.splice(at + 1, 0, { t: "tok", id }, { t: "text", v: "" });
    this.part = targetSection;
    this.sel = id;
    this.caret = { section: targetSection, index: at + 2 };
    this.save();
    this.render();
  }

  /** Select a wildcard: its list opens, and new wildcards go right after it. */
  select(id, openList, section, index) {
    this.sel = id;
    if (section !== undefined && index !== undefined) {
      this.part = section;
      this.caret = { section, index: index + 1 };   // the gap just after this wildcard
    }
    this.render();
    if (openList) this.openDialog(id);
  }

  orderedTokens() {
    return [this.part].flatMap((section) => (this.state.parts[section] || [])
      .filter((s) => s.t === "tok").map((s) => [String(s.id), this.state.tokens[String(s.id)]]))
      .filter(([, t]) => t);
  }

  renderRows() {
    if (!this.rowsBox) return;
    const rows = this.orderedTokens().map(([id, token]) => {
      const seg = (values, current, onSet) => el("div", { class: "epb-seg" }, values.map(([value, label, tip]) =>
        el("button", { class: current === value ? "on" : "", title: tip, onclick: () => onSet(value) }, label)));
      const now = this.preview.picks?.[id];
      return el("div", { class: `epb-row${String(this.sel) === id ? " sel" : ""}` },
        el("button", { class: "who", onclick: () => {
          const segs = this.state.parts[this.part] || [];
          const at = segs.findIndex((g) => g.t === "tok" && String(g.id) === id);
          this.select(Number(id), true, this.part, at);
        }, title: "Open the list; new wildcards go right after this one" },
          el("b", {}, this.slotLabel(token)), el("small", {}, token.key ? displayName(token.key) : "no list")),
        seg(MODES, token.mode, (mode) => { this.updateToken(id, { mode }); }),
        el("div", { class: "epb-count", title: "How many different entries" },
          el("button", { onclick: () => this.updateToken(id, { count: Math.max(1, token.count - 1) }), "aria-label": "Fewer" }, "−"),
          el("span", {}, token.mode === "fixed" ? "1" : String(token.count)),
          el("button", { onclick: () => this.updateToken(id, { count: Math.min(MAX_COUNT, token.count + 1) }), "aria-label": "More" }, "+")),
        seg(KEEPS, token.keep === "concept" ? "meaning" : token.keep, (keep) => this.updateToken(id, { keep })),
        el("span", { class: "epb-now", title: now || "" }, now ? `“${now}”` : ""));
    });
    this.rowsBox.replaceChildren(...(rows.length ? rows : [el("div", { class: "epb-empty" }, `No wildcards in ${this.sectionLabel(this.part)} yet. Type text, or click a button above to insert one at the amber gap.`)]));
  }

  renderPreview() {
    if (!this.previewBox) return;
    const text = this.preview.text || "";
    const words = text ? text.split(/\s+/).length : 0;
    const platform = cache.platforms?.[this.widget("platform")?.value];
    const target = platform?.target_words?.length ? ` · full prompt target ${platform.target_words[0]}–${platform.target_words[1]}` : "";
    this.previewBox.replaceChildren(
      el("div", { class: "bar" },
        el("h4", {}, "Preview"),
        el("span", { class: "meta" }, `seed ${this.widget("seed")?.value ?? 0} · ${words} words${target}`),
        el("button", {
          class: "epb-btn green", title: "Next seed", onclick: () => {
            const w = this.widget("seed");
            if (w) { w.value = Number(w.value || 0) + 1; this.node.setDirtyCanvas?.(true, true); }
            this.refreshPreview();
          },
        }, "Re-roll")),
      el("p", {}, text || "…"),
      ...((this.preview.to_fill || []).length ? [el("div", { class: "meta", style: "margin-top:3px" },
        `LLM will write: ${(this.preview.to_fill || []).map((s) => this.sectionLabel(s)).join(", ")}`)] : []),
      ...(this.preview.warnings || []).slice(0, 4).map((w) => el("div", { class: "warn" }, w)));
  }

  // -------------------------------------------------- list viewer
  closeDialog() {
    this.dialog?.element.remove();
    this.dialog = null;
  }

  openDialog(tokenId) {
    this.closeDialog();
    const panel = this;
    const d = {
      tokenId,
      search: "",
      lists: [],
      entries: [],
      total: 0,
      matched: 0,
      element: el("div", { class: "epb-dialog", role: "dialog" }),
    };
    d.element.addEventListener("keydown", (e) => { e.stopPropagation(); if (e.key === "Escape") panel.closeDialog(); });
    this.dialog = d;
    const rect = this.root.getBoundingClientRect();
    const left = Math.min(window.innerWidth - 480, rect.right + 12);
    d.element.style.left = `${Math.max(8, left)}px`;
    d.element.style.top = `${Math.max(8, Math.min(window.innerHeight - 560, rect.top))}px`;
    document.body.append(d.element);

    const token = () => panel.state.tokens[String(d.tokenId)];
    const PAGE = 300;
    const loadEntries = async (more = false) => {
      const t = token();
      if (!t?.key) { d.entries = []; d.total = d.matched = 0; return; }
      const offset = more ? d.entries.length : 0;
      try {
        const data = await getJSON(`${ROUTE}/list?key=${encodeURIComponent(t.key)}&q=${encodeURIComponent(d.search)}&offset=${offset}&limit=${PAGE}&nsfw=${panel.nsfw}`);
        const texts = data.entries.map((e) => e.text);
        const gone = data.entries.filter((e) => e.dropped).map((e) => e.text);
        const rated = new Map(data.entries.filter((e) => e.rating || e.rated_by_you).map((e) => [e.text, e]));
        d.rated = more ? new Map([...(d.rated || []), ...rated]) : rated;
        d.listRating = data.list_rating || 0;
        d.listOverride = data.list_override || "";
        d.entries = more ? d.entries.concat(texts) : texts;
        d.dropped = more ? new Set([...(d.dropped || []), ...gone]) : new Set(gone);
        d.total = data.total;
        d.matched = data.matched;
        d.stars = data.stars || 0;
        d.hidden = !!data.hidden;
        d.catalog = data.catalog;
        d.folder = !!data.folder;
        d.files = data.files || 0;
        d.ratingLocked = data.rating_locked || 0;
        const sources = new Map(data.entries.map((e) => [e.text, e.list]));
        d.source = more ? new Map([...(d.source || []), ...sources]) : sources;
      } catch (e) {
        d.entries = [];
        d.error = e.message;
      }
    };
    const debouncedSearch = debounce(async () => { await loadEntries(); d.refresh(false); }, 200);
    d.reload = async () => { await loadEntries(); d.refresh(); };

    /** Save a rating to _catalog_user.yaml (stars, hidden, drop / undrop), then reload. */
    const rate = async (changes, listKey = null) => {
      const t = token();
      if (!t?.key) return;
      try {
        await postJSON(`${ROUTE}/rate`, { key: listKey || t.key, ...changes });
      } catch (e) {
        d.error = `could not save: ${e.message}`;
      }
      cache.slots.clear();
      if (t.slot) {
        try { d.lists = await slotLists(panel.builderId, t.slot, panel.nsfw, panel.genderOf(panel.sectionOfToken(d.tokenId)), panel.violence); } catch (e) { /* keep the old list */ }
      }
      await loadEntries();
      d.refresh();
      panel.schedulePreview();
    };

    d.refresh = (rebuild = true) => {
      const t = token();
      if (!t) { panel.closeDialog(); return; }
      const mode = MODES.find((m) => m[0] === t.mode);
      const custom = t.mode === "fixed" && t.picks.length && !d.entries.includes(t.picks[0]) && !d.search ? t.picks[0] : "";
      const header = el("header", {},
        el("b", {}, panel.slotLabel(t)),
        el("span", { title: "The node's nsfw setting: entries above it are greyed and never picked" }, `${mode ? `${mode[1]}: ${mode[2]} \u00b7 ` : ""}browsing at: ${panel.nsfw}`),
        el("button", { class: "close", "aria-label": "Close", onclick: () => panel.closeDialog() }, "✕"));
      makeDraggable(d.element, header);
      const select = el("select", { onchange: async (e) => { panel.updateToken(d.tokenId, { key: e.target.value, picks: [], mode: "random" }); await loadEntries(); d.refresh(); } },
        d.lists.map((l) => el("option", { value: l.key, selected: l.key === t.key, title: l.key + (l.also?.length ? `\nsame content: ${l.also.join(", ")}` : "") },
          listLabel(l))));
      if (!d.lists.some((l) => l.key === t.key) && t.key) select.prepend(el("option", { value: t.key, selected: true }, displayName(t.key)));
      const search = el("input", { value: d.search, placeholder: "type to filter…" });
      search.addEventListener("input", () => { d.search = search.value; debouncedSearch(); });
      const own = el("input", { value: custom, placeholder: "e.g. 7-year-old, 42-year-old" });
      own.addEventListener("change", () => {
        const v = own.value.trim();
        panel.updateToken(d.tokenId, v ? { mode: "fixed", picks: [v] } : { mode: "random", picks: [] });
      });
      const entryButtons = d.entries.map((text) => {
        const on = t.picks.includes(text);
        const excl = t.mode === "exclude";
        const gone = d.dropped?.has(text);
        const r = d.rated?.get(text);
        const rateBox = r ? el("select", {
          class: "epb-rate",
          title: `NSFW level of this entry: ${nsfwName(r.rating)}${r.rated_by_you ? " (set by you)" : " (from its words)"}.`
            + `${r.above ? ` Left out at ${panel.nsfw}.` : ""} Saved in _catalog_user.yaml.`,
          onchange: (e) => rate({ rate: { text, level: e.target.value } }, d.folder ? d.source?.get(text) : null),
        }, [["", r.rated_by_you ? "auto" : `auto: ${nsfwName(r.rating)}`], ...NSFW_LEVELS.map((n) => [n, n])].map(([v, label]) =>
          el("option", { value: v, selected: r.rated_by_you ? v === nsfwName(r.rating) : v === "" }, label))) : null;
        return el("div", { class: `epb-entry-row${gone ? " dropped" : ""}${r?.above ? " above" : ""}` },
          el("button", {
            class: `epb-entry${on ? (excl ? " off" : " on") : ""}`,
            onclick: () => {
              const cur = token();
              if (cur.mode === "fixed") { panel.updateToken(d.tokenId, { picks: [text] }); return; }
              const picks = cur.picks.includes(text) ? cur.picks.filter((p) => p !== text) : [...cur.picks, text];
              panel.updateToken(d.tokenId, { picks, mode: cur.mode === "random" ? "subset" : cur.mode });
            },
          }, el("span", { class: "box" }, on ? (excl ? "−" : "✓") : ""), el("span", { class: "txt" }, text)),
          el("button", {
            class: "epb-drop",
            title: gone ? "Dropped: never picked from this list. Click to bring it back." : "Drop: never pick this entry from this list (saved in _catalog_user.yaml)",
            "aria-label": gone ? "Restore entry" : "Drop entry",
            onclick: () => rate(gone ? { undrop: text } : { drop: text }, d.folder ? d.source?.get(text) : null),
          }, gone ? "restore" : "drop"),
          rateBox);
      });
      const starBar = el("div", { class: "epb-stars", title: "Your rating of this list. Starred lists come first for this slot and win ambiguous names." },
        ...[1, 2, 3, 4, 5].map((n) => el("button", {
          class: n <= (d.stars || 0) ? "on" : "",
          "aria-label": `${n} star${n > 1 ? "s" : ""}`,
          onclick: () => rate({ stars: d.stars === n ? 0 : n }),
        }, "★")),
        el("button", {
          class: `epb-toggle${d.hidden ? " on" : ""}`,
          title: "Hidden lists are never used by a bare name, glob or slot button; __their/exact/name__ still works.",
          onclick: () => rate({ hidden: !d.hidden }),
        }, d.hidden ? "Hidden" : "Hide list"),
        el("label", { class: "epb-nsfw", title: "This list's NSFW level (saved in _catalog_user.yaml). auto = from its folder and name. "
          + "A run uses lists and entries at its nsfw setting or lower; off is SFW." },
          "This list's rating",
          el("select", { disabled: d.ratingLocked ? true : null,
            title: d.ratingLocked ? `Set by its _nsfw folder: ${nsfwName(d.ratingLocked)}. Move the file to change it.` : null,
            onchange: (e) => rate({ nsfw: e.target.value }) },
            [["", `auto: ${nsfwName(d.listOverride ? 0 : d.listRating) || "off"}`], ...NSFW_LEVELS.map((n) => [n, n])].map(([v, label]) =>
              el("option", { value: v, selected: v === d.listOverride }, label)))),
        d.catalog ? el("span", { class: "q" },
          `quality ${Math.round(d.catalog.quality * 100)} · ${d.catalog.kind} · ${d.catalog.dialect}${d.catalog.dup_of ? " · duplicate" : ""}`) : null);
      const folderBar = d.folder ? el("div", { class: "epb-stars" },
        `Whole folder \u00b7 ${d.files} files \u00b7 each roll draws from all of them; drop and entry ratings go to each prompt's own file`) : null;
      d.element.replaceChildren(
        header,
        el("div", { class: "body" },
          el("label", {}, el("span", {}, t.slot ? `Source list \u00b7 ${d.lists.length} match this slot` : (t.key || "").startsWith("prompts/") ? "Prompt file \u00b7 click Browse prompts to swap it" : "Source list \u00b7 added from Find"), select),
          d.folder ? folderBar : starBar,
          el("div", { class: "two" },
            el("label", {}, el("span", {}, "Search this list"), search),
            el("label", {}, el("span", {}, "Or fix to your own value"), own))),
        el("div", { class: "info" },
          el("span", {}, d.error ? d.error : `Showing ${d.entries.length} of ${d.search ? `${d.matched} matching, ` : ""}${d.total}`),
          el("span", {}, `${t.picks.length ? `${t.picks.length} picked` : "nothing picked"}${d.dropped?.size ? ` · ${d.dropped.size} dropped` : ""}`)),
        (d.entriesBox = el("div", { class: "entries" }, entryButtons,
          d.entries.length < d.matched ? el("div", { class: "epb-more" }, `scroll for more (${d.entries.length} of ${d.matched})`) : null)),
        el("footer", {},
          el("button", { class: "epb-btn primary", onclick: () => panel.updateToken(d.tokenId, { mode: "fixed", picks: t.picks.slice(0, 1) }) }, "Fix to first pick"),
          el("button", { class: "epb-btn", onclick: () => panel.updateToken(d.tokenId, { mode: "subset" }) }, "Use picks as subset"),
          el("button", { class: "epb-btn", onclick: () => panel.updateToken(d.tokenId, { mode: "exclude" }) }, "Exclude picks"),
          t.slot ? el("button", { class: "epb-btn", title: "Fold this button's lists into one list of your own: shared entries first, prune the rest",
            onclick: () => panel.openMerge(d.tokenId, d.lists) }, "Merge lists…") : null,
          (t.key || "").startsWith("prompts/") ? el("button", { class: "epb-btn", title: "Pick another prompt file or folder for this pill",
            onclick: () => panel.openPrompts(d.tokenId) }, "Browse prompts\u2026") : null,
          el("button", { class: "epb-btn", title: "Save the list shown here as a button (in My buttons)",
            onclick: () => panel.openEditor({ lists: [t.key], label: t.slot ? shortLabel(t.key) : (t.label || shortLabel(t.key)), tokenId: d.tokenId, section: baseSection(panel.sectionOfToken(d.tokenId)) }) }, "☆ Button"),
          el("button", { class: "epb-btn", style: "margin-left:auto", onclick: () => panel.updateToken(d.tokenId, { mode: "random", picks: [] }) }, "Clear → random")));
      if (!rebuild) search.focus();
      // Long lists arrive a page at a time: scrolling near the end loads the next page.
      if (d.keepScroll) { d.entriesBox.scrollTop = d.keepScroll; d.keepScroll = 0; }
      d.entriesBox.addEventListener("scroll", async () => {
        const box = d.entriesBox;
        if (d.loadingMore || d.entries.length >= d.matched) return;
        if (box.scrollTop + box.clientHeight < box.scrollHeight - 200) return;
        d.loadingMore = true;
        const top = box.scrollTop;
        await loadEntries(true);
        d.keepScroll = top;
        d.loadingMore = false;
        d.refresh();
      });
    };

    d.refresh();
    (async () => {
      const t = token();
      if (t.slot) {
        try { d.lists = await slotLists(panel.builderId, t.slot, panel.nsfw, panel.genderOf(panel.sectionOfToken(d.tokenId)), panel.violence); } catch (e) { d.error = e.message; }
      }
      await loadEntries();
      if (!t.slot) d.lists = [{ key: t.key, count: d.total, display: d.catalog?.display || "", nsfw: d.listRating || 0, quality: d.catalog ? d.catalog.quality : -1, dialect: d.catalog?.dialect || "" }];
      d.refresh();
    })();
  }
}

function makeDraggable(box, handle) {
  handle.addEventListener("mousedown", (e) => {
    if (e.target.closest("button")) return;
    const startX = e.clientX, startY = e.clientY;
    const left = box.offsetLeft, top = box.offsetTop;
    const move = (ev) => { box.style.left = `${left + ev.clientX - startX}px`; box.style.top = `${top + ev.clientY - startY}px`; };
    const up = () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  });
}

function hideWidget(widget) {
  if (!widget) return;
  widget.hidden = true;
  widget.computeSize = () => [0, -4];
  if (widget.element) widget.element.style.display = "none";
  if (widget.inputEl) widget.inputEl.style.display = "none";
}

// ------------------------------------------------------------------ registration
app.registerExtension({
  name: "Eric.PromptBuilder",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    const builderId = nodeData?.input?.required?.composer?.[1]?.eric_builder;
    if (!builderId) return;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const result = onNodeCreated?.apply(this, arguments);
      hideWidget(this.widgets?.find((w) => w.name === "composer"));
      const panel = new BuilderPanel(this, builderId);
      this.__epbPanel = panel;
      this.addDOMWidget("builder_panel", "eric_builder", panel.root, {
        serialize: false,
        hideOnZoom: false,
        getMinHeight: () => 360,
      });
      const [w, h] = this.size;
      this.setSize([Math.max(w, 700), Math.max(h, 640)]);
      panel.init();
      return result;
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const result = onConfigure?.apply(this, arguments);
      // Widget values are restored after creation; read the saved composer once they are in.
      setTimeout(() => this.__epbPanel?.loadFromWidget(), 0);
      return result;
    };

    const onRemoved = nodeType.prototype.onRemoved;
    nodeType.prototype.onRemoved = function () {
      this.__epbPanel?.closeDialog();
      this.__epbPanel?.closeEditor();
      this.__epbPanel?.closeMerge();
      this.__epbPanel?.closeMore();
      PANELS.delete(this.__epbPanel);
      return onRemoved?.apply(this, arguments);
    };
  },
});
