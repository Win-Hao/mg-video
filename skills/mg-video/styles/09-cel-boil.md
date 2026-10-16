# Hand-drawn line boil (手绘线条沸腾)

The texture of hand-drawn animation: lines are redrawn every few frames and wobble slightly, so the picture seems to breathe ("boil"); only 12 drawings per second, and effects like smoke and speed lines are drawn by hand too. Warm, deliberately un-digital.

**Good for**: a small story or a metaphor. An ink-line storybook look (blue-black ink, flat fills, slight line jitter) that blends easily with talking-head footage.
**Reference films (technique only)**: mg-styles-15 `demos/05-cel-boil/` (the October 2026 test batch settled on 12 drawings a second at 30 fps); `references/from-code-video/04-手绘.md`.

<signature>
- The lines boil: prepare 3–4 slightly different versions of each drawing and swap every 2–3 frames; even a still image keeps trembling.
- On twos, 12 drawings per second: all action except the smear frame runs at 12 a second (at 30 fps, alternating 2 and 3 frames per drawing); held shots may go on threes.
- Lines have weight: thin at the start and end of a stroke, fuller in the middle, like a real pen — not uniform vector lines.
- Smear frames on fast moves: for one frame a fast object is stretched into a streak.
- Hand-drawn effects: smoke puffs, sparks, speed lines, sweat drops, drawn frame by frame on top of the main subject.
- Paper: a faint paper texture over the whole frame.
</signature>

<style>
- Build: Canvas 2D with a variable-width brush (centerline + pressure → outline), or p5.brush (`references/from-code-video/技术栈.md` notes how to wire it in). Time drawings with the template's `drawingIndex(t, 12)` (the 2, 3, 2, 3 frame table) and seed each drawing's jitter with `jit(seed, drawing)` so every render matches; `onTwos` gives 15 a second at 30 fps, not 12.
- Cues on drawing boundaries: an event that falls between two drawing changes creates a single-frame drawing, so move it (e.g. land 1 frame before the beat). Compare times by frame with `at(t, sec)`: a cue written as 5.6667 s is later than frame 170, so `t >= 5.6667` shows the wrong drawing.
- Impacts: one smear frame, then hold the impact drawing 3 frames — it stays visible on a phone (133 ms in all) without adding single-frame drawings.
- Smoke and clouds: cool grey on warm paper (white smoke on beige barely registers, on screen or as change). Per drawing, union the lobes that touch and outline the union; overlapping lobes outlined one by one leave broken ink ends at the seams. Vary lobe count (2–4), size, and stretch instead of copying one template.
- Beat skeleton: an object enters → a character reacts (anticipation + squash) → the action bursts into hand-drawn effects → the effects regroup into the title, which keeps boiling during the hold. Give the climax something new (a new element, a new color, full-screen focus lines): on-twos shaking changes as many pixels as anything, so raw change won't single the climax out.
- Sound: bed `lofi` with `keys='piano'`, or `variety`; `paper`, `pen`, `pop`, `boing`. A groove that stops dead before a closing chord is beyond `music.bed`; build it from the public pieces audio.md documents (`music.Form`, chords, patterns, bassline).
- Avoid: lines that stop moving (it becomes plain vector), jitter so large it looks like signal noise, silky 30-drawings-per-second motion, any faster cadence the prompt doesn't announce (the card and the printed prompt must agree), effects that cover the hero.
</style>

<check>
- `check.py drawings 成片.mp4 --per-second 12`: 12 drawings a second, and the only single-frame drawings are smears. It counts a new drawing at > 40 levels on > 2000 px; x264 noise after a big change touches 300–500 px at > 12 levels, so lower thresholds overcount.
- Lines still boil during held shots.
- Jitter amplitude: 1–3px of displacement at 1080p; more looks like a glitch.
- Smear frames last exactly 1 frame; the impact drawing after one holds 3.
- Smoke and effects read at the phone width set in prompt.md.
</check>
