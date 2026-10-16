# Bauhaus geometric construction (包豪斯几何构成)

Circles, triangles, and squares on a grid, moving, turning, and flipping one beat at a time, in the three primaries plus black. Mechanical and rational, and a natural fit for musical beats.

**Good for**: chapter cards ("Step N"), number cards, key-point summaries. A chapter-card test film (10-06) and a poster film in the October 2026 test batch (10-13) were made in this style; their lessons are folded in below.
**Reference films (technique only)**: mg-styles-15 `demos/09-bauhaus/` (the test films added a tile-flip climax and a roll on the grid).

<signature>
- Basic shapes only: circle, half circle, quarter circle, triangle, rectangle — nothing else.
- Five colors only: red, yellow, blue, black, and one paper-colored ground. A sixth color (including a grey made by a translucent overlay) breaks the style.
- Everything on the grid: displacements are whole grid units, landing points sit on grid lines, rotation pivots sit on grid intersections; shape sizes may use half units.
- Mechanical motion: linear or symmetric ease-in-out, no bounce, no overshoot; rotations in multiples of 90°. The mechanical feel is the style, not a flaw.
- One action per beat: each action lands on a beat, and no two big actions share a beat.
- It ends as a poster: a complete composition with heavy geometric sans-serif type, flush left, strong size contrast.
</signature>

<style>
- Build: Canvas or SVG on a 120px grid unit (at 1080p), no motion blur. Ease long moves with a sine and stretch them until no frame moves farther than the object's own size: `io2` peaks at twice the average speed (850 px in 0.4 s moved 140 px a frame, more than the ball, and strobed).
- Paths and turns: things travel along grid lines in whole units and turn 90° about grid intersections. A one-cell object turning about its corner moves exactly one cell (its center rides a quarter circle of radius 0.71 units), so a one-cell "jump" stays on the grid only as that roll along the floor.
- Light grid without translucency: solid crosses at the intersections, like registration marks, not faint lines; stop drawing any cross a shape will cover from the moment that shape lands.
- Climax: build-up beats stay small, and the climax beat changes at least 2–3× as many pixels as the largest of them (41.6% against 3.1% in the poster test film); reveal by tile flip by default. The climax is the one beat where two things may land together; say so in the prompt, or phrase it as one action ("the ball goes in and flips '3 分' over").
- Tile flip: tiles an even number of cells wide, so each hinge (a tile's center line) sits on a grid line; each tile takes at least 3 frames (with 2, the middle frame is zero-width), staggered 1 frame; turn image smoothing off on squashed frames (2 px crosses smear to grey). See techniques.md.
- Recognition: a shape-built object keeps one identifying feature (the net a hollow half ring, the ball's curved side seams), and its landing orientation must still read after a turn (a ball turned 90° showed its seams as 丰).
- Type: the poster's heavy geometric sans-serif is a font, not shapes: 抖音美好体 Bold (Douyin Sans, OFL, from GitHub `bytedance/fonts`) for Chinese — flat-cut terminals, no brush tips — used in the poster test film, where a 分 built from quarter rings and rectangles read as a face at phone width. Build only simple glyphs such as digits from shapes, and add a same-color stroke where a glyph must match a shape's stroke width. Light small text on saturated red needs strokes ≥ 10 px (4:2:0 encoding tints thinner ones pink).
- Beat skeleton: frame 0 already shows the grid and the first shape → one part enters per beat → on the climax beat the subject (the number or keyword) becomes complete for the first time → the title is set into the layout beat by beat → the last second holds, with one small move visible on a phone. A beat that changes under 0.3% of the pixels at phone width is invisible; don't spend a beat on it.
- Sound: bed `techno` (no kick until the bar before the drop, so the opening runs 6–10 dB quiet; its 'dark' outro pad is inaudible on phones; most of its energy is below 120 Hz). A short `click` or `blip` per action. The climax frame carries at most three layers — `impact('punch')`, a sustained bright chord (supersaw), a rising tail — because one hit alone can't stand 5 LU above the rest. Mute the music for the whole pre-climax hold (a filter doesn't stop a four-on-the-floor kick); after the climax, set the poster section apart by cutting below 200 Hz, not by lowering the whole bed.
- Avoid: elastic overshoot, gradients, rounded corners, translucent overlays, several elements entering at once — and don't let the subject finish assembling before the climax (the lesson of the chapter-card test's first draft).
</style>

<check>
- Measure each landing point against the grid; scan filmstrips for any frame that overshoots.
- Colors on the encoded film: `check.py palette 成片.mp4 --colors <red,yellow,blue,black,paper>` — about 99.5% of pixels on the five colors, the rest 1 px anti-aliased edges, no patch of a sixth color.
- `sheet.py --beats cues.json`: the climax beat is the biggest change, at least 2–3× the largest build-up beat.
- Cover the text and look at the phone width set in prompt.md: every object can be named.
- The subject becomes complete on the climax beat, not before.
- Where the chapter-card test's reviews took points off: an opening grid so heavy it read as graph paper, visible steps where two shapes meet, and music that kept playing through the pre-climax pause.
</check>
