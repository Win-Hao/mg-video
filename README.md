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

One finished 10-second film per card, each built with this skill and revised through its review loop. Click a preview to play the 720p MP4 with sound, or watch all fifteen on the [gallery page](https://win-hao.github.io/mg-video/). Music and effects are all synthesized by the skill's `mgsound` library. On-screen text is Chinese because the test batch was made for a Chinese audience; the cards work in any language.

<table>
<tr>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/01-paperclip-sticker.mp4"><img src="docs/films/01-paperclip-sticker.gif" alt="01-paperclip-sticker: where Earth's water is" width="100%"></a><br><b><code>01-paperclip-sticker</code></b><br><sub>white-bordered object stickers, one big table and one camera, true charts</sub></td>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/02-flat-vector.mp4"><img src="docs/films/02-flat-vector.gif" alt="02-flat-vector: a tomato's journey" width="100%"></a><br><b><code>02-flat-vector</code></b><br><sub>flat geometry, elastic entrances, one lead at a time</sub></td>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/03-isometric.mp4"><img src="docs/films/03-isometric.gif" alt="03-isometric: a library returns machine" width="100%"></a><br><b><code>03-isometric</code></b><br><sub>true 30° isometric, depth-sorted objects, pipes between components</sub></td>
</tr>
<tr>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/04-hud.mp4"><img src="docs/films/04-hud.gif" alt="04-hud: a landing sequence" width="100%"></a><br><b><code>04-hud</code></b><br><sub>two hues, wireframes, scans, locks</sub></td>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/05-glassmorphism.mp4"><img src="docs/films/05-glassmorphism.gif" alt="05-glassmorphism: a weather widget" width="100%"></a><br><b><code>05-glassmorphism</code></b><br><sub>frosted cards over drifting colour light</sub></td>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/06-bauhaus.mp4"><img src="docs/films/06-bauhaus.gif" alt="06-bauhaus: a basketball poster" width="100%"></a><br><b><code>06-bauhaus</code></b><br><sub>grid, primaries plus black, one action per beat</sub></td>
</tr>
<tr>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/07-variety-captions.mp4"><img src="docs/films/07-variety-captions.gif" alt="07-variety-captions: captions over footage" width="100%"></a><br><b><code>07-variety-captions</code></b><br><sub>multi-outline chubby text, pops, emotion symbols</sub></td>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/08-pixel.mp4"><img src="docs/films/08-pixel.gif" alt="08-pixel: sunset fishing" width="100%"></a><br><b><code>08-pixel</code></b><br><sub>small canvas scaled up, limited palette, frame-by-frame sprites</sub></td>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/09-cel-boil.mp4"><img src="docs/films/09-cel-boil.gif" alt="09-cel-boil: an alarm clock wakes up" width="100%"></a><br><b><code>09-cel-boil</code></b><br><sub>lines that tremble every few frames, 12 drawings/s, hand-drawn effects</sub></td>
</tr>
<tr>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/10-one-line.mp4"><img src="docs/films/10-one-line.gif" alt="10-one-line: a cycling badge" width="100%"></a><br><b><code>10-one-line</code></b><br><sub>a single line drawn throughout, the line becomes fill</sub></td>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/11-morph.mp4"><img src="docs/films/11-morph.gif" alt="11-morph: a moon becomes an idea" width="100%"></a><br><b><code>11-morph</code></b><br><sub>one outline continuously becoming another</sub></td>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/12-collage.mp4"><img src="docs/films/12-collage.gif" alt="12-collage: an owl's newspaper" width="100%"></a><br><b><code>12-collage</code></b><br><sub>scissor-cut edges, halftone, jerky motion</sub></td>
</tr>
<tr>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/13-liquid.mp4"><img src="docs/films/13-liquid.gif" alt="13-liquid: liquid metal forms a word" width="100%"></a><br><b><code>13-liquid</code></b><br><sub>blobs that merge and split</sub></td>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/14-synthwave.mp4"><img src="docs/films/14-synthwave.gif" alt="14-synthwave: a midnight radio ident" width="100%"></a><br><b><code>14-synthwave</code></b><br><sub>striped sunset, neon grid, chrome type, tape</sub></td>
<td align="center" width="33%"><a href="https://win-hao.github.io/mg-video/films/15-3d-material.mp4"><img src="docs/films/15-3d-material.gif" alt="15-3d-material: a word rises from glass marbles" width="100%"></a><br><b><code>15-3d-material</code></b><br><sub>real materials, soft light, shallow focus (Blender + Cycles)</sub></td>
</tr>
</table>

Third-party material in the films: NOAA, Yellowstone and Wikimedia Commons photos (01, public domain and CC0), 19th-century engravings and newsprint (12, public domain), "Burnt Toast" footage by cottonbro studio via Pexels (07, Pexels license), a Poly Haven HDRI (15, CC0), and OFL fonts (Noto Sans/Serif SC, JetBrains Mono, Douyin Sans, Fusion Pixel, Resource Han Rounded, M PLUS Rounded 1c). Everything else is drawn and synthesized in code.

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
