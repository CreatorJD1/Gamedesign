# DIMENSIONLOCK: ASTROLABE — "Soul Drift" — Project Handoff

**For: Claude Code (or any dev) picking up this project.**
Read this top-to-bottom first. It captures the full state so you can continue without re-deriving anything.

---

## 1. What this is
A **mobile-first 2D anime sidescroller platformer**. Protagonist **Zally Matrodor** (purple hair, green bomber jacket) is pulled into **"The Endless"** — an interstitial void of floating cloud-islands — and must traverse it. Tone: vast, lonely, dreamlike. Exploration-led platforming over combat.

- **Engine:** Phaser **4.1.0**, inlined into the HTML (CDN was unreliable inside the chat preview; fine to switch back to a CDN/npm dependency now that you're local).
- **Delivery so far:** a **single self-contained `.html`** (~25 MB) with **every asset base64-embedded**. This was a constraint of the chat workflow — **the first thing you should do in Claude Code is de-monolith it** (see §7).
- **Canonical lore:** Google Doc, fileId `1LAZUIFHZg5k_FB44oxmlvJm1wPrW69zdps6TrgEvaCs`.

The current build file is `soul-drift.html` (this was "P4 . STEP 50" in the chat). The start screen shows a build stamp (`<div id="tag">`) — historically bumped every build to defeat mobile cache. You can drop that habit once you're on a local server.

---

## 2. Current architecture (inside `soul-drift.html`)

It's one big inline `<script>`. Key pieces:

- **Scenes:** `Prologue` (rainy-street intro → snatch → mp4 cinematic) and `Play` (the game). Plus `ComicIntro` and `SoulCutscene` helpers, and a start-screen DOM (`#start`) with BEGIN + a **ZALLY / DELDELIA character selector** (saved to `localStorage 'souldrift_char'`).
- **THE ACTIVE LEVEL SYSTEM — `Play.loadArtLevel(idx)`** (this is what matters now):
  - Each level = **3 parallax layers**: `bg` (opaque, slow parallax), `mid` (the **play-plane**, scrollFactor 1 — *the platforms live here*), `fg` (near edge-frame, in front).
  - **Collision is derived from the midground art.** The solid island shapes in the `mid` image become the platforms. Collision is placed on each island's **dense cloud crown** (not the wispy top) via width-based crown detection, and platforms are **one-way** (`checkCollision.down/left/right = false`) so the character lands on top but never snags sides/underside.
  - Advancement: collect the level's seed quota → `stageCleared()` → `beginTransition(idx+1)` → next level.
  - **No darkness overlay** on art levels (kept clean).
- **`LEVELS` config array** (defined near `const PLAT=...`):
  - `LEVELS[0]` = **Level 1, real art** (`L1_bg`/`L1_mid`/`L1_fg` + `rects`).
  - `LEVELS[1..5]` = `null` → fall back to Level 1's art as a **placeholder** (`var lv=(LEVELS[idx]&&LEVELS[idx].art)?LEVELS[idx]:LEVELS[0];`).
  - Routing: `enterRealm(idx)` has `if(idx<6){ return this.loadArtLevel(idx); }` — **all 6 active levels use the new system.**
- **Levels 7–12 are LOCKED** ("🔒 IN DEVELOPMENT"): `var WIP={6:1,7:1,8:1,9:1,10:1,11:1};` drives the nav state; `beginTransition` has a guard that blocks entering any WIP index.
- **DEPRECATED (still in code, unused for active levels):** the old "realm / void-hole / descent" system — `enterRealm` (realm branch), `buildLayer`, `buildCalibrated`, the 12-layer `LAYERS` ladder, per-layer darkness (`darkRT`), and `playLayerCutscene`. **The auto layer-cutscene was disabled** because it called `this.physics.pause()` and a non-completing callback froze the game. There's also a watchdog in `update()` that resumes physics if it's ever paused with nothing open. **Recommended: delete the dead realm/void-hole/buildLayer/buildCalibrated code in Claude Code** to shrink and simplify, keeping `LAYERS` only for level names/metadata.
- **Other systems present:** SOUL seed economy + XP/level, touch + keyboard controls, generative audio (`blip`, `window.__sfx`, `window.__music`), a SOUL ATTUNEMENT skills panel, an intro `.mp4` (base64).

---

## 3. How to add / build a level (the workflow we settled on)

The user **designs each level by uploading 3 layer images** — no platform coordinates needed, because **platforms ARE the midground**.

1. **bg** — opaque background (tileable preferred for parallax).
2. **mid** — the platform layer: **solid island shapes = standable platforms, transparent = gaps**. (Uploaded images stored "transparent" as flat **white**, so the pipeline keys white → alpha.)
3. **fg** — foreground edge-frame (transparent center).

**Pipeline (Python + Pillow + scipy):**
- Key white → alpha (graded, keeps faint mist).
- Detect island components (saturation mask + `scipy.ndimage.label`, filter by size).
- For each island, find the **crown** = first row from top reaching ~50% of the island's max width → collision top sits there.
- Emit **normalized rects** `[nx, ny, nw, nh]` (fractions of the mid image). Runtime maps them to world coords and makes thin (≥28 px) **one-way** static bodies.
- Encode bg/mid/fg as WebP base64; add to `ASSETS`; set `LEVELS[idx] = {art:1, bg, mid, fg, rects}`.

A reference implementation of crown-detection + encoding is in `pipeline/` (see README). Always **render a collision overlay preview** and eyeball it against the art before committing — that caught the "floating above the cloud" bug.

---

## 4. Assets

- **Player sprites (Zally):** `idle, run, jump, freefall, death, dash` (+ `transform, demonrun, attack` for demon form). Sheet dims in `SHEETS` (all 300 px tall strips). Player `SCALE=0.38`.
- **Second character (Deldelia):** `del_idle/run/jump/freefall/dash/death` (`DEL_SHEETS`), sliced from 4×4 grids, normalized to 120 px, scaled `SCALE*2.5` to match Zally's height; per-anim body via an `animationstart` hook.
- **Level 1 art:** `L1_bg` (55421), `L1_mid` (55424 — the island field), `L1_fg` (55420).
- **Misc:** `seed`, island platform cut-outs (`isl_big/mid/sml`, from the old island experiment), cloud deco.
- **The user's full art library** (multiple backgrounds, platform sets, foreground frames; plus 66 per-layer backgrounds and a 205 MB `MAPBGPACK.zip`) lives in their uploads/Google Drive but **was ephemeral in the chat** — re-collect the originals into `assets/source/` locally so they're not lost again.

> Drive `SoulDrift_Pipeline_step30` folder (`16BrUantJuYlvtP6xhLlZRNzxLxc1W7p_`) holds earlier handoffs + a pipeline zip. The 205 MB background pack and ~78 MB music library **cannot be embedded** in a single HTML — host on a CDN (HuggingFace/R2) and stream/lazy-load.

---

## 5. Build history (chat builds P4 STEP 31→50, condensed)
Footsteps/thunder/music → tiled→3-layer parallax → real music tracks → 12 real backgrounds → character select (Deldelia) → smaller char + softer layers → pale-haze parallax depth → **islands = platforms** → lock levels 7–12 → **fullscreen fix (removed a zoomed-out "window box")** → **per-level new system wired (your art, Level 1)** → **freeze fix (cutscene physics-pause)** → **all 6 levels on the new system** → **one-way floors (no sticking)** → **floors on the cloud crown**. Current = STEP 50.

---

## 6. Known gotchas / learnings
- **Safari/iOS is the most fragile target.** Test there.
- **One-way platforms** (top-only collision) are what stopped the character sticking — keep that.
- Keep collision on the **dense crown**, not the wispy island top, or the character floats.
- The chat container was **ephemeral** — that pain goes away in Claude Code; **commit early and often.**
- Phaser 4 r-notes that bit us in the chat: build stamps, base64 size limits, and that the old cutscene system could deadlock physics. All handled, but the dead code is worth removing.

---

## 7. Recommended FIRST tasks in Claude Code
1. **`git init` + first commit** of `soul-drift.html`. (Finally, version history.)
2. **De-monolith.** Extract the embedded base64 assets into `assets/` (a quick script can walk the `ASSETS={...}` object and write each `data:` URI to a file), split the inline `<script>`/`<style>` into `src/`, and add a tiny **build step** that re-embeds for a release `.html` (or just serve the assets normally for dev — you don't need them inlined locally). This makes every future edit fast and diffable.
3. **Local run:** `python3 -m http.server 8000` (or any static server) and open the page — no cache pain, no 25 MB re-download.
4. **Delete the dead realm/void-hole/`buildLayer`/`buildCalibrated`/darkness code** now that all levels use `loadArtLevel`.
5. Then continue content: **Levels 2–6 with real art**, using the §3 pipeline.

---

## 8. Roadmap (the user's plan, in priority-ish order)
- Build **Levels 2–6** with their own bg/mid/fg art (replace the placeholders).
- Tune Level 1: length (currently ~1.2 screens — repeat the field for a longer level), platform spacing, background choice.
- **S5** random events incl. a barreling-planet QTE • **S2** per-level story cutscenes (re-add cleanly, *without* the physics-pause deadlock) • **S6** SOUL Attunement skills (panel exists) • **S7** 3D Soul Protector upgrade device • **S8** outfits/gear • **S9** characters 3 & 4 (need their sheets; Zally + Deldelia done) • **S1** Astrolabe map.
- **Audio + full background library → CDN** (HuggingFace/R2); wire streaming music + lazy-loaded backgrounds (HTML stays small).
- **Android APK** via Capacitor 8 (app id `com.creatorjd.souldrift`); build locally (needs Node 20+, JDK 21, Android Studio). Consider **Godot 4.6** if you want first-class app-store builds — but finish the design loop first.
