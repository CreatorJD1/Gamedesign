# Soul Drift — Claude Code project

This bundle moves the **DIMENSIONLOCK: ASTROLABE / "Soul Drift"** game out of the chat workflow and into Claude Code.

```
soul-drift.html        # the current build (was "P4 . STEP 50") — runnable as-is
HANDOFF.md             # READ FIRST — full project state, architecture, how the level system works
pipeline/build_level.py# reference: turn a midground image into one-way platform collision + embed a level
```

## Getting started in Claude Code

Claude Code is Anthropic's agentic coding tool. It runs in your terminal (and as VS Code / JetBrains extensions, and remotely from the Claude mobile/desktop apps). For the **current, exact install command and requirements**, see the official docs: **https://docs.claude.com** (Claude Code section). The common path is a global npm install run with a recent Node.js, then `claude` inside the project folder — but check the docs for today's specifics rather than trusting a pasted command.

Once installed:
1. Put this folder somewhere permanent and open a terminal there.
2. `git init && git add -A && git commit -m "import soul-drift step50"` — you finally have version history.
3. Run it locally: `python3 -m http.server 8000` then open `http://localhost:8000/soul-drift.html`. (No cache pain, no big re-downloads — just edit and refresh.)
4. Launch `claude` and point it at **HANDOFF.md** first. A good opening prompt:
   > "Read HANDOFF.md. This is a Phaser 4 sidescroller delivered as one self-contained HTML with base64 assets. First task: extract the embedded assets out of `soul-drift.html` into `assets/`, split the inline script/style into `src/`, and give me a small build step that re-embeds for release. Don't change game behavior."

## Why this is better than the chat workflow
- **Persistent files** — nothing vanishes between turns.
- **Git** — diff, branch, roll back across builds (you did 50 in chat with no history).
- **Fast iteration** — edit a real source tree and refresh a local server instead of regenerating/downloading a 25 MB HTML each time.
- **Real tooling** — linters, a debugger, and the ability to split the monolith into sane files.

## First things to do (also in HANDOFF.md §7)
1. Commit.
2. **De-monolith** the 25 MB HTML (extract assets, split src, add a re-embed build step).
3. Delete the dead "realm / void-hole / buildLayer / buildCalibrated / darkness" code — all 6 levels now use `loadArtLevel`.
4. Continue content: Levels 2–6 with real art via `pipeline/build_level.py`.

## Re-collect your art
The chat container was ephemeral, so your uploaded art library (backgrounds, platform sets, foreground frames, the 66 per-layer backgrounds, the 205 MB MAPBGPACK, the music) needs to be gathered into `assets/source/` locally so it's never lost again. The big background pack + music can't live inside the HTML — host them on a CDN (HuggingFace/R2) and stream/lazy-load.
