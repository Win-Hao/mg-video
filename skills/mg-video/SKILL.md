---
name: mg-video
description: Makes a polished motion-graphics (MG) clip in code, in one established style chosen from 15 style cards (paperclip-style sticker explainer, flat vector, isometric 2.5D, sci-fi HUD, glassmorphism, Bauhaus, variety-show captions, pixel art, hand-drawn line boil, one continuous line, shape morph, cut-paper collage, liquid, synthwave/VHS, 3D material). Each card states, in tags, what makes the style recognizable, how to build it, and how it usually fails. Picture, music bed and synthesized effects read one beat sheet; key frames come first; frames are rendered deterministically (motion blur and transparent output available); a reviewer who did not build the clip reviews it against measurable acceptance conditions, and revision repeats until every item scores at least 7. Use when the user asks for an MG animation or motion-graphics clip, names one of these styles (paperclip / sticker explainer, variety-show captions / 花字, HUD, Bauhaus, pixel art…), wants an animated opener or title, an MG B-roll segment or a transparent caption overlay for talking-head footage, a film in one of the mg-styles-15 styles, or an animation with music and sound effects synced to the beat (e.g. 「做个 MG 动画」「做个片头动效」「做个叠在口播上的花字」), even without naming the skill.
---

# MG video

Make a clip in one established motion-graphics style that someone who knows design recognizes at a glance and that reads on a phone. Four practices carry the quality:

- **Styles are recognized by their signatures**: each style card lists checkable features (how much overshoot, how many frames of stagger, how wide the sticker border), and the review scores against them
- **One beat sheet**: `cues.json` holds the time of every picture event; the picture code and the audio script both read it, so sound lines up with picture by construction
- **Key frames first**: stills must stand up as posters before anything moves
- **Independent review with measurable fixes**: a reviewer in a clean context, who took no part in building the clip, scores it and writes each fix as a condition a script can check; revise until every item is at least 7 and nothing is fatal

While building this skill we studied [mg-styles-15](https://github.com/Vincentwei1021/mg-styles-15) on GitHub (15 styles, one 10-second film each; to read the source, clone it as described in `references/techniques.md`); each style card names its reference film, for technique only. All text, prompts, and code in this skill are our own. In the October 2026 test batch all 15 cards were run (15 films, one per card, 10 seconds each, shown as cards in a compilation); the lessons are folded into this file, the cards and `references/`.

## Is this the right skill

- A whole knowledge video (research, script, images, storyboard) is more than one clip; if one segment of it should be in an MG style, make that segment here
- A finished talking-head video is edited elsewhere; this skill makes its B-roll segments, openers, or overlays
- Subtitles on every line are a separate job (variety-show captions appear only on punchlines and turns, and belong here)

## Workflow

Copy this checklist and tick it off as you go:

```
- [ ] 1 Clarify the request
- [ ] 2 Pick the style, write prompt.md, show the user
- [ ] 3 Create the project folder, write the beat sheet
- [ ] 4 Key-frame stills
- [ ] 5 Motion, music and effects
- [ ] 6 Render and self-check
- [ ] 7 Independent review → revision, until it passes
- [ ] 8 Deliver
```

**1 Clarify**: where it is used (B-roll for a line in a talking-head video / opener / standalone short / transparent overlay on talking-head footage / one film in a compilation), what it says, what viewers should remember, which style, how long, landscape or vertical. Don't re-ask what the user already said, use what can be inferred, and ask everything else in one round (use the question tool if available). Defaults: a standalone short is 1920×1080, 30fps, 10 s, with music (an mgsound bed by default, or a track the user brings); a clip embedded in a talking-head video matches the master (e.g. 2560×1440, 60fps) and delivers only the effects stem, because the video carries its own music. Also settle the **embedded size**: how wide the film is on a portrait phone, in physical pixels. About 1179 when it fills the screen width (a landscape film, or a vertical one); about 620 for a 1340×754 card in a 2560×1440 compilation (a 1920 film shown at ≈ 0.32×). Text, thin lines and small moves are judged at that size, not at full resolution (`references/techniques.md`, "Reading on a phone").

**2 Style and prompt**: if the user named a style, use that card; otherwise pick 2–3 cards from the table below by content and give one reason each so the user can choose. Write `prompt.md` in the project folder in English, following `references/prompt-template.md`: write `<role>`, `<context>`, `<task>`, `<specs>` for this job, and paste `<signature>`, `<style>`, `<check>` from the chosen card, adapted to this subject. On-screen copy in any other language (Chinese, say) goes into the prompt verbatim, in quotes; ask the builder to report in the user's language. When a prompt is printed beside the film (a compilation that shows its prompts), quote it verbatim in `<task>`, say it wins over the style card wherever the two differ, and check the pasted text against the source character by character before handing over. Show the user (skip if they said to go straight ahead). **Copying the look of a reference video the user supplied**: don't pick a card; derive the style from the video itself (frames, colour values, rhythm, transitions).

**3 Folder and beat sheet**: `bash <skill>/tools/new.sh <folder> width height fps seconds bed` (`new.sh --blender <folder> …` sets up a Blender project instead of a page, for the 3D card). **Music**: by default the bed comes from mgsound: the card's Sound line names the bed and the effects; pass the bed name to `new.sh` (it lands in `"music"` in `cues.json`) and put a bar line on the climax (`references/audio.md`). **Bring your own music track**: set `"bed": null` in `cues.json`, render or obtain a 48 kHz WAV at the film's BPM with a bar line on the climax, and load it in `audio.py` with `soundfile` and `m.add(Sound(x.T), at=0, bus='music')` (`references/audio.md` shows the snippet); the card's Sound line still picks the effects. Put the folder wherever the user keeps films, e.g. `films/<name>/`. Write the beats into `cues.json` first: the hook (within 0.5 s, with the subject already on screen at frame 0), each element's entrance, the climax (where the brief puts it; 60–75% is only the default when nothing else decides it), one aftershock event right after the climax, and the end hold (last 0.8–1.2 s, with one move visible at the embedded size). The template shows the format: sounds per event, `times` for repeated hits, a separate `motion` list for whooshes and risers (played, not sync-checked), music settings under `"music"`. Pick the tempo so a beat is a whole number of frames (`references/audio.md`).

**4 Key-frame stills**: build the look, render 6–10 key moments with `render.mjs --stills` (it removes the old stills there first; `--keep` keeps them), and look at each: composition, hierarchy, whitespace, type, against `<signature>`. Name any default pattern the first draft fell into (centered fade-ins, everything entering at once, purple gradients…) in the prompt's Avoid list, then fix it. The builder may append dated lines to Avoid (`- Avoid (added by the builder, 10-13, round 2): …`) but never edits the prompt quoted in `<task>`: the user approved it, and viewers may compare the film with it line by line. A clause that can't be met is reported, not dropped. A change at the still stage takes seconds; after a full render it takes minutes.

**5 Motion and sound**: write `render(t)`, preview at `--scale 0.5`, and inspect the fastest moves and every transition frame by frame with `sheet.py --around`. Compare times by frame number with the template's `at(t, sec)`: a cue written with 4 decimals lands one frame late with `t >= sec`. Drawing rates at 30 fps: "on twos" means 2 frames per drawing, which is 15 drawings/s; 12 drawings/s alternates 2- and 3-frame holds; use `drawingIndex(t, perSecond)` whenever a card asks for drawings per second. Write `audio.py` following `references/audio.md`.

**6 Render and check**: `node <skill>/tools/render.mjs` (`--workers 2` on a shared machine; `--alpha 透明.mov` for overlays; when only the sound changed, rerun `audio.py` and `render.mjs --remux`, which puts the new `out/audio.wav` on the existing film without a browser).

**No multi-sample motion blur in anything viewers pause on**: `motionBlur.samples` in `video.json` and `--mb` stay at 1. Averaged sub-frames show on a paused frame as stacked copies and soft bands; they read as a rendering error, and in flat styles as gradients (flat-vector review, 10-13; compilation viewers pause to read the prompt). Show speed with solid smear frames and speed lines instead. When a style needs real blur (liquid, fast camera moves), compute it in the page with adaptive sub-frames sized to each frame's on-screen motion (`references/techniques.md`, "Motion blur"); Blender's own motion blur is fine. Measured on 10-13 (Apple M4, 1080p, 10 s): a Canvas 2D film rendered in about 30 s with 4 samples and 60 s with 8, and 4 samples still showed as 4 copies on moves above ~150 px/frame; adaptive sub-frames rendered the liquid film in 2.5 min against 6 min with fixed 4 samples, and opening 128 sub-frames around every collision took it to 10 min.

Then check. Run every Python tool with `~/.venvs/mg-video/bin/python`, written `py` below:
- `py <skill>/tools/spec.py 成片.mp4 --w W --h H --fps FPS --duration S --climax T --cues cues.json` — specs, loudness, true peak, black frames, bt709 colour tags, edge reveal (the template's magenta page background showing at a frame edge fails), stillness, and the largest move in the last 1.2 s scaled to a 620 px card. With `--climax`, the loudest 0.4 s must land on T both full-range (at least 1 dB ahead of everything outside the climax) and on a simulated phone speaker (at least 3 dB); it also prints the jump from the build-up into the climax and the biggest frame-to-frame changes with the climax beat's rank. Given a `.wav`, it checks only the audio, before the picture is rendered
- `py <skill>/tools/sync.py 成片.mp4 cues.json` — sound against picture; `--stems` measures on `out/stems/sfx.wav` (a four-on-the-floor bed hides a missing hit on the mix); `masked` means a hit is buried under a louder neighbour
- `py <skill>/tools/sheet.py` for the overview; `--at … --width <embedded px>` to read text at the embedded size; `--beats cues.json` for how much each beat changes; `--crop x,y,w,h --zoom N` and `--safe 0.05` for detail and margins
- `check.py` and `measure.py` for whatever the card's `<check>` makes measurable: palette, hue census, accent count, drawings per second, margins on every frame, brightness curves, overlaps

Then go through the prompt's `<check>` item by item, and record each result as a number measured on the encoded film, with the frames and the tool.

**7 Review → revision**: follow `references/review.md`. This is the loop the October 2026 test batch ran:
- A reviewer in a clean context (a subagent, a new session or a headless run of your agent's CLI) that took no part in building reviews the encoded film against `prompt.md`: eight scores, a fatal list, and, when a prompt is printed beside the film, every clause mapped to the second it shows up (a clause it can't find is fatal)
- Fixes are acceptance conditions a script can check (what, which frames, measured how, threshold), kept apart from example ways to meet them, with a priority order for when two conflict and the script or tool that measures each. From round 2 the review also carries a regression table (R1, R2, …) of what already passes and must keep passing. What only an ear or an eye can settle goes on a separate list for the user
- The builder (the same one if your agent can still message it, otherwise a new one given `prompt.md` and the review file) copies the current version to `versions/vN/`, revises, and reports every condition with the number it measured on the encoded film
- One revision by default; another round while any item is below 7 or anything is fatal. A last revision that only had to clear conditions gets a short confirmation round: re-measure each condition, diff against the previous version for regressions, rescore. First reviews averaged 6.5 (5.75–7.0); about half the films passed after one revision and most of the rest after two
- Blender, or anything else that takes more than ~10 minutes to render: check ~20 test frames (50% size, 16 samples) against the conditions first, and render the whole film only when they pass; if two rounds of test frames still miss a condition by more than 10%, stop and report the numbers

**8 Deliver**: keep `成片.mp4` (or `透明.mov` + `out/stems/sfx.wav`), `prompt.md`, `cues.json`, `video.json`, the picture code, `audio.py`, `CREDITS.md`, `check/` (overview, reviews, `报告.md`), `versions/`, `package.json`. Delete `node_modules` (`npm i` restores it) unless the film may be re-rendered soon; full-resolution stills in `check/` and `out/stems/` can be regenerated from the film and `audio.py`, so delete them if space matters (for a 6-second test clip they came to over 100 MB). Report in the user's language, also written to `check/报告.md`: time spent, scores per review round, what changed, what weaknesses remain.

**Who does what**: steps 1–2 need back-and-forth with the user, so do them yourself. Steps 3–6 are heavy and self-contained: hand them to a builder in a clean context (a subagent if your agent can start one, otherwise a new session or a headless run of your agent's CLI) with the path to `prompt.md` and to this skill, and tell it to read steps 3–7 of this file plus `references/techniques.md` and `references/audio.md` first. It hasn't seen your conversation, so `prompt.md` must be complete. When it hands back, look at the overview yourself, then get the review from a different clean context (`references/review.md`); send the review back to the same builder if your agent can still message it (it remembers its code), otherwise start a new builder with `prompt.md`, the project folder and the review file. With no way to start a clean context, do it all yourself, and when reviewing look only at the film and `prompt.md`, not at what you meant to make. If steps 1–2 took many rounds of drafts in this session, hand steps 3–8 to a new session with a handoff doc (the brief, the approved `prompt.md`, the project folder, decisions made and open questions) rather than continuing here: the old context pollutes the build.

**Shared machine, shared tools**:
- On an Apple M4 (10-core GPU, 24 GB) run at most 3–4 builders at once, each with `--workers 2` and previews at `--scale 0.5`. Never run two GPU-heavy renders at the same time: next to a browser render, Blender went from 9–11 to 18–26 s/frame, and a page with many sub-frames per frame must batch its GPU work or it loses the WebGL context
- `tools/` is shared by every film in flight. Builders don't edit it: they copy a tool into their project, fix the copy, and say so in the report. Whoever changes a shared tool tells the builders that are running and adds one line to `CHANGELOG.md` at the skill root (date, file, what changed, why). On 10-13 `render.mjs` changed mid-batch (19:50: colour tags, no hang on page errors), and reviewers couldn't tell which films had been rendered before the change

## Style cards

In `styles/`, ordered roughly from most to least used. Each card opens with what the style is and what it is good for, followed by three tagged blocks — `<signature>`, `<style>`, `<check>` — ready to paste into `prompt.md`.

| Card | Recognized by | Good for |
|---|---|---|
| `01-paperclip-sticker` | white-bordered object stickers, one big table and one camera, true charts | workhorse for evergreen topics and explainers |
| `02-flat-vector` | flat geometry, elastic entrances, one lead at a time | how a feature works, the steps of a task |
| `03-isometric` | 30° miniature sand table, things grow, pipes connect | how tools, files, and services connect |
| `04-hud` | cool thin wireframes, numbers that scramble then settle, lock-on brackets | showing what an agent is doing |
| `05-glassmorphism` | neighboring-hue light, frosted cards, slow | openers for a first look at a new model or feature |
| `06-bauhaus` | grid, primaries plus black, one action per beat | chapter cards, number cards, summaries |
| `07-variety-captions` | multi-outline chubby text, pops, emotion symbols | transparent overlays over talking-head footage |
| `08-pixel` | small canvas scaled up, limited palette, frame-by-frame sprites | a character's quest-style walkthroughs |
| `09-cel-boil` | lines that tremble every few frames, 12 drawings/s (2- and 3-frame holds at 30 fps), hand-drawn effects | ink-line character pieces, hand-drawn explainers |
| `10-one-line` | a single line drawn throughout, glowing nib, line becomes fill | openers, chapter titles, defining a concept |
| `11-morph` | one outline continuously becoming another | "A is really B" metaphors, transitions |
| `12-collage` | scissor-cut edges, halftone, jerky motion | crossover topics, playful openers |
| `13-liquid` | merging, stringing, flung and squashed | transitions, openers (hardest: about 4.5 hours over three rounds on 10-13; skip when rushed) |
| `14-synthwave` | striped sunset, neon grid, chrome type, tape | then-vs-now topics, crossover openers |
| `15-3d-material` | real materials, soft light, shallow focus, weight | openers; Blender 5.2 with Cycles on the Metal GPU, about 7 s/frame at 1080p (`new.sh --blender`) |

## Non-negotiables

- **Each frame depends only on t**: the renderer jumps around (parallel workers start mid-clip, sub-frames sample several moments within one frame), so randomness must be seeded and there is no requestAnimationFrame, CSS animation, or Date.now. The contract is in `tools/template/index.html`
- **Every `<signature>` item is met**: if viewers can't tell which style it is, the clip has failed. Subject and palette can change; the signature can't
- **Assets and fonts are licensed for use**, with sources in `CREDITS.md`; no AI-generated human faces; no real brand logos or famous game sounds; if AI-generated images appear, label AI-generated content where the platform requires it
- **Kinetic and big text never glows**: solid fill, dark outline, hard drop shadow, and the accent colour must clash with every background it sits on. **Real photos the user supplies keep their original colour**, tied into the style with frames, borders and device shells instead of a duotone
- **On-screen facts and numbers have sources**; no real brand logos; product interfaces match the real product, and don't draw features it doesn't have
- **Before delivery, look at the overview and filmstrips yourself, and get at least one review**

## Tools

| Tool | What it does |
|---|---|
| `tools/setup.sh` | run once: Python environment for audio and checks in `~/.venvs/mg-video` (needs `uv`, or a system Python ≥ 3.11) |
| `tools/new.sh` | create a project folder: page skeleton, `video.json`, beat sheet, audio script, `CREDITS.md`, Playwright; `--blender` for a Blender project (`scene.py`, `render.sh`, `encode.sh`) |
| `tools/render.mjs` | run inside the project folder: full film / `--stills` (clears its folder; `--keep`) / `--scale 0.5` preview / `--from 3 --to 5 --out x.mp4` section / `--alpha` transparent / `--workers N` / `--remux` new audio onto the film / `--boxes` only `out/boxes.json` from the page's `window.boxes(t)`; a query string reaches the page (`render.mjs "index.html?layer=text"`) |
| `tools/sheet.py` | overview every 0.5 s; `--around 3.2` filmstrip; `--at 2,4.5 --width 620` frames at the embedded size; `--crop`, `--zoom`, `--safe 0.05`, `--nolabel`, `--cols`; `--beats cues.json` change per beat |
| `tools/spec.py` | size, fps, duration, loudness, true peak, black frames, colour tags, edge reveal, stillness, end-hold motion; `--climax T` loudness and picture change of the climax; a `.wav` checks audio only; exit code 1 on failure |
| `tools/sync.py` | for each sound in the beat sheet, how many ms the audio onset is off; `times` per hit; `--stems`; `masked` |
| `tools/check.py` | `palette`, `hues`, `accents`, `drawings`, `flicker`, plus `colors` and `loop` for PNG stills |
| `tools/measure.py` | `margins`, `curve`, `colorfrac`, `overlap` on the film: value, limit and margin, flags margins under 10%, ends with PASS/FAIL when given limits |
| `tools/mgsound/` | our effects library and mixer (numpy/scipy synthesis, no samples): 46 effects, 10 music beds, mixing and mastering (`Mix.export` reports how much the limiter takes off each cue) |
| `tools/ocr.swift` | macOS Vision OCR for reading on-screen text back from a still: `swift <skill>/tools/ocr.swift image.png` prints the recognized lines (Chinese and English) top to bottom |
| `CHANGELOG.md` | one line per change to `tools/` |

Run every Python tool with `~/.venvs/mg-video/bin/python`. Also needed: Node, ffmpeg (tested with 9.x: no `-vsync`, no `drawtext`), Playwright's Chromium (`npx playwright install chromium`), and for the 3D card Blender (`brew install --cask blender`).

## References

- `references/prompt-template.md`: the tagged template for `prompt.md` (embedded size, frame 0, end hold, measurable checks, an Avoid list the builder extends) and two filled examples (paperclip B-roll, variety-caption overlay)
- `references/review.md`: the review and revision prompts, how to write fixes as acceptance conditions (windows, priorities, feasibility, colour and text measures), the regression table, confirmation rounds, how many rounds
- `references/audio.md`: beat sheet → bed → effects → export; embedded clips deliver only the effects stem
- `references/techniques.md`: environment, determinism, fonts, key frames and filmstrips, motion blur and sub-frames, camera, lines, Canvas/CSS/WebGL pitfalls, light and grain, measuring from the page, footage, transparency, reading on a phone, encoding, assets, render speed
