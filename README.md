<h1 align="center">mg-video</h1>

<p align="center">
  <em>Polished motion-graphics clips, made in code, in one of fifteen established styles.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-111111?style=flat-square" alt="MIT">
  <img src="https://img.shields.io/badge/works%20with-any%20SKILL.md%20agent-111111?style=flat-square" alt="Agents">
  <img src="https://img.shields.io/badge/render-Playwright%20%2B%20FFmpeg%20%7C%20Blender-111111?style=flat-square" alt="Render">
  <img src="https://img.shields.io/badge/styles-15%20cards-111111?style=flat-square" alt="Fifteen styles">
</p>

<p align="center">
  <sub><a href="README.zh-CN.md">简体中文</a></sub>
</p>

---

An agent skill for short motion-graphics (MG) clips: openers, B-roll segments, chapter cards, transparent overlays for talking-head footage, standalone shorts. The agent doesn't generate video; it writes a web page that draws second *t* of the film (Canvas, WebGL, SVG, Three.js) or a Blender scene, renders it frame by frame, and lays music and synthesized sound effects on the same beat sheet.

What the skill adds on top of "write some animation code":

- **Style cards.** Fifteen recognizable MG styles, each card in three tagged blocks: `<signature>` (what makes the style read at a glance), `<style>` (how to build it, with measured numbers), `<check>` (how it usually fails and how to measure that). The agent pastes them into the prompt for the job.
- **One beat sheet.** `cues.json` holds the hook, every entrance, the climax and the end hold. The page reads it, `audio.py` places sound effects and the music bed from it, and `sync.py` measures each sound against the picture to a few milliseconds.
- **Key frames first.** 6–10 stills have to stand up as posters before anything moves; changing a still costs seconds, changing a full render costs minutes.
- **Deterministic rendering.** Every frame depends only on *t*; `render.mjs` renders in parallel, with optional adaptive motion blur and ProRes 4444 transparent output.
- **Measured checks.** `spec.py`, `check.py`, `measure.py`, `sheet.py`, `sync.py` measure the encoded film with fixed definitions (margins, palette, hues, loudness, climax position, change per beat, end-hold motion, text size at phone width), so the builder and the reviewer get the same numbers.
- **Independent review.** A reviewer in a clean context, who didn't build the clip, scores it on eight items and writes every fix as a condition a script can check. Revise until every item is at least 7 and nothing is fatal.

## The fifteen styles

| Card | Recognized by |
|---|---|
| `01-paperclip-sticker` | white-bordered object stickers, one big table and one camera, true charts |
| `02-flat-vector` | flat geometry, elastic entrances, one lead at a time |
| `03-isometric` | true 30° isometric, depth-sorted objects, pipes between components |
| `04-hud` | two hues, wireframes, scans, locks |
| `05-glassmorphism` | frosted cards over drifting colour light |
| `06-bauhaus` | grid, primaries plus black, one action per beat |
| `07-variety-captions` | multi-outline chubby text, pops, emotion symbols |
| `08-pixel` | small canvas scaled up, limited palette, frame-by-frame sprites |
| `09-cel-boil` | lines that tremble every few frames, 12 drawings/s, hand-drawn effects |
| `10-one-line` | a single line drawn throughout, the line becomes fill |
| `11-morph` | one outline continuously becoming another |
| `12-collage` | scissor-cut edges, halftone, jerky motion |
| `13-liquid` | blobs that merge and split |
| `14-synthwave` | striped sunset, neon grid, chrome type, tape |
| `15-3d-material` | real materials, soft light, shallow focus (Blender + Cycles) |

## Workflow

1. **Clarify**: where the clip is used, what it says, what viewers should remember, style, length, orientation. One round of questions.
2. **Style and prompt**: pick a card (or two or three for the user to choose from) and fill in `prompt.md` from `references/prompt-template.md`.
3. **Folder and beat sheet**: `tools/new.sh` creates the project; write `cues.json` first.
4. **Key-frame stills**.
5. **Motion and sound**: `render(t)`, previews at half size, frame-by-frame filmstrips around every fast move and transition; `audio.py` from the beat sheet.
6. **Render and self-check** with the measuring scripts.
7. **Independent review → revision**, until it passes (`references/review.md`).
8. **Deliver**.

Steps 3–6 are self-contained, so the agent can hand them to a builder in a clean context (a subagent, a new session, a headless run) with nothing but `prompt.md` and the skill path.

## Install

Tell your agent:

```
Install the mg-video skill from https://github.com/Win-Hao/mg-video
```

skills CLI:

```bash
npx skills add Win-Hao/mg-video -g
```

Claude Code plugin:

```
/plugin marketplace add Win-Hao/mg-video
/plugin install mg-video@mg-video
```

Or copy `skills/mg-video/` into your agent's skills folder.

## Requirements

- Node (22 or later) and ffmpeg (tested on 9.x)
- Playwright's Chromium: `npx playwright install chromium` once; `new.sh` installs `playwright` into each project folder
- Python ≥ 3.11 for the sound library and the measuring scripts: `bash skills/mg-video/tools/setup.sh` creates `~/.venvs/mg-video` (with `uv` if present; `MG_VENV` changes the path) and checks the rest of the toolchain
- Optional: Blender 5.x for the 3D card; macOS for `tools/ocr.swift` (screenshot-and-OCR test)

Tested on an Apple M4 (macOS). Timings in the docs were measured there.

## Render without an agent

```bash
S=skills/mg-video
bash $S/tools/setup.sh
bash $S/tools/new.sh films/hello 1920 1080 30 8 explainer
cd films/hello
# edit index.html (render(t)) and cues.json
~/.venvs/mg-video/bin/python -I audio.py          # → out/audio.wav
node ../../$S/tools/render.mjs --stills 1,4,7      # key frames
node ../../$S/tools/render.mjs                     # → 成片.mp4
~/.venvs/mg-video/bin/python ../../$S/tools/spec.py 成片.mp4 --w 1920 --h 1080 --fps 30 --duration 8
```

## Credits

While building the style cards we studied [mg-styles-15](https://github.com/Vincentwei1021/mg-styles-15) (15 styles, one 10-second film each) for technique; every card names its reference film. All text, prompts and code here are our own. `render.mjs` extends the renderer from [code-video](https://github.com/Win-Hao/code-video).

## License

MIT
