# Sci-fi HUD (HUD 科幻界面)

The heads-up display from science-fiction films: thin wireframes, tick-marked rings, scans, and ticking data on a dark ground, saying "the system is analyzing, the system is locking on".

**Good for**: showing what an agent is doing — scanning a file tree, locking onto the broken file, reading progress, the status flipping to "found it". When it shows the user's own work, file names, numbers, and statuses come from a run that actually happened.
**Reference films (technique only)**: mg-styles-15 `demos/22-hud/` (the October 2026 test batch added a scan band that survives the phone and world-anchored labels).

<signature>
- Two hues: a cool color draws the wireframes on a near-black, cyan-tinted ground; on a state change (lock, alert) everything switches to one warm color. Only these two hues — a third makes it look like game UI.
- Thin lines: 1–2px, at most two weights; elements carry instrument details such as tick marks, corner brackets, IDs, and small labels.
- Drawn on, not faded in: lines trace out, frames unfold from their corners, rings rotate into place — outer layers first, inner layers after.
- Live data: numbers scramble for a few frames before settling on the real value; status text types out with a blinking cursor.
- Lock-on: a bracket shrinks from large onto the target and lands with a brief overshoot or a double blink.
- Lines carry a light glow, plus scanlines, restrained enough not to hurt legibility; text never glows.
</signature>

<style>
- Build: SVG or Canvas 2D for the wireframes; JetBrains Mono for digits and IDs, Noto Sans SC medium/bold for Chinese status lines (no CJK monospace has the weight to read on a phone); Three.js wireframe only if you need a 3D globe or model.
- Layers: glow is a blurred copy of the line layer added underneath; text sits in its own layer on top, untouched by glow and scanlines — solid color, a dark outline, a hard downward shadow.
- Brightening: `lighter` (additive) on an already-saturated line clips its core toward yellow or white, a third hue. Raise the alpha of the white line layer before it is colored (cap 1.0) instead.
- Scanlines: a 3 px-period pattern is full-screen texture only and vanishes at phone width. To read as scanlines on a phone, roll a band (about 90 px tall, about 160 px/s) inside which only the line layer brightens (2.4× read; 1.8× with a 1 px edge didn't), with a 2 px leading edge; it also keeps the hold alive.
- Line width: if the prompt fixes it (1–2 px), skip the heavy-first opening from techniques.md, or state that exception in the prompt.
- Labels that follow world coordinates (candidate points, zone IDs) drift into boxes as things move: give them limits (the label's bottom, outline and shadow included, stays ≥ 14 px above the status box and slides along it).
- Typing: the cursor blinks about 2 Hz while idle and stays solid while typing; each character lands on a frame. Scramble: 4–8 frames of seeded random digits at the same width, then settle.
- Beat skeleton: boot (wireframes trace on layer by layer) → scan (radar or progress sweep) → data scrolls → lock onto the target → status changes color + one line of conclusion → an aftershock 1–2 beats later (the bracket releasing outward), so the hold isn't dead.
- Sound: bed `darksynth`, at a BPM that puts scan, lock, and climax on bar lines. It ends on the minor tonic; for a success state choose `prog` so the drop bar is major (chords count back from the drop; the test film used `prog='I i i II VII'`). `hud_open`, `hud_scan`, `hud_data`, `lock_on` (its sync point is the lock), `hud_alert`; info sounds at −8 to −14 dB, not −3 to −6. The climax gets a 1–4 kHz layer (a bright chord, a two-note confirm, a 3 kHz click), not more sub. A run of typing ticks goes on `bus='sfx'` or with `duck_db` about 2, or the music pumps.
- Avoid: large solid fills, gradient buttons, gibberish presented as content (viewers will try to read it), text so small it becomes noise on a phone, glow or bloom on text, a third hue from additive clipping.
</style>

<check>
- Content: on a HUD about a real run, every file name, number, and status matches the screenshots or logs of that run; on a fictional subject, every label is a real word and every number a plausible, consistent value (altitude only falls, units right). Nouns that set the scene still read in the last second.
- Hues: `check.py hues 成片.mp4 --allow` each main hue ±12° (e.g. `170-194,15-39` for cyan #46E3EA and orange #FF8A2B) finds no bright pixels outside the two hues (look at glow cores and the scan band).
- Text never collides: export label and box rectangles from `window.boxes(t)`; `measure.py overlap` for every label against every box reports 0 frames (a 7-frame collision slipped past the overview and filmstrips in the test film).
- The smallest text tier reads at the phone width set in prompt.md; anything that doesn't is texture only and carries no meaning.
- Zoom into every text element in a full-resolution still: no glow or halo; scanlines and the scan band don't touch text.
- A scan signal is visible at phone width during the hold.
</check>
