# Cut-paper collage (拼贴)

Old photos, newsprint, and torn paper reassembled: proportions are deliberately wrong, a mouth flaps on its own scrap of paper, and motion comes in jerks, as if moved by hand on a table. Retro, surreal, a little absurd.

**Good for**: crossover topics and playful openers. Real people only from public-domain historical photos; never AI-generated faces.
**Reference films (technique only)**: mg-styles-15 `demos/06-collage/` (the October 2026 test batch added engraving cut-outs and a paper flip, with small prep scripts for edges and halftone).

<signature>
- Cut paper: every element has a scissor-cut white edge or a torn, fibrous edge and a little shadow, so you can see the layers stacked on top of each other.
- Print texture: photos become halftone or high-contrast black and white; the ground is newsprint or kraft paper.
- Wrong proportions: a big head on a small body, a hand larger than a person — things that could only exist as a collage.
- Jerky motion: positions update only 8–12 times per second, each with a pixel or two of random jitter, like hand-moved stop motion.
- Puppet joints: arms and jaws rotate around a pin, and mouths swap between two or three cut-outs.
- Transitions are hand actions: a hand slaps something down, or a sheet flips over to cover the frame.
</signature>

<style>
- Build: DOM or Canvas for the images. Prepare edges and halftone in advance: dilate the mask → trace its outline → simplify it into straight scissor cuts → jitter the vertices. `hyperframes remove-background` is a human-portrait model (and a slow first download): cut engravings and objects out with polygon masks drawn over a gridded enlargement (techniques.md).
- Timing: step with the template's `drawing(t, per)` (an integer drawing number) and jitter each element per drawing with `jit(seed, i)`; per = 3 gives 10 updates a second at 30 fps.
- Holes are paper too: mouths, tongues, and openings are cut black or red paper with white edges, never vector ellipses.
- A sheet flip that reads as paper: 5–7 pre-cut drawings (2 of them the back, 1 with a curled edge), shadows in 2–3 flat steps, a hand always pinching the edge. A CSS `rotateY` door with a gradient shadow doesn't read as paper; if you do use 3D CSS, set `perspective-origin` above the frame so the lifted edge shows obliquely, and put `drop-shadow` on a wrapper that doesn't rotate (techniques.md).
- After a sheet covers the frame, the new picture is still a sheet lying on the table, with tabletop showing around it; a full-screen sheet loses the paper.
- Short of a pose? Slice and recombine one source (four pieces of one engraved wing fanned out into a spread wing), and motivate transitions with something already in the frame (the top sheet of a flying stack).
- Sources: public-domain images from Wikimedia Commons, NASA, and similar; Commons answers rapid requests with 429 (batch queries, wait between them, send a descriptive User-Agent), and archives that refuse curl often have Commons copies. Old newspaper as texture: body text only, scrambled, mirrored, or shrunk until unreadable — no headlines, ads, or mastheads, since old scans can carry offensive copy.
- Beat skeleton: an old photo slaps onto the table → part of it opens and things spill out → a big title slaps in at an angle → a sheet flips over to close.
- Sound: bed `lofi` with `flavor='boombap'` (after its drop the low end runs 20 dB above 1–4 kHz: put a bright layer — snare, clap, a paper slap — on the hits); `paper`, `scissors`, `tape_rip`, `sticker_slap`, `record_scratch`.
- Avoid: smooth tweens (smoothness kills the look), clean digital photos, AI-generated portraits, geometric shapes standing in for cut paper.
</style>

<check>
- Every image has a source and license in `CREDITS.md`, with every slice's file name on its source's line.
- Filmstrips show motion in steps, not glides.
- White edges and halftone are consistent across all elements, mouths and holes included.
- After the covering transition, tabletop still shows around the sheet.
- Key elements stay inside the 5% safe frame on every frame (`sheet.py --safe 0.05` on stills, `measure.py margins` per frame).
</check>
