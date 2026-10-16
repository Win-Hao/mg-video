# Flat vector (扁平矢量)

The baseline of explainer animation: everything is built from flat geometric shapes — round heads, box bodies, bar limbs — and the craft shows in elasticity and rhythm. Simple, friendly, fast to read.

**Good for**: "how a feature works" or "the steps of a task", tied together by one running idea (a dot, a sheet of paper, a small character). Without such a through-line, don't pick this style; it slides into template territory faster than any other.
**Reference films (technique only)**: mg-styles-15 `demos/01-flat-vector/` (the October 2026 test batch added shape-fill transitions and solid smears).

<signature>
- Flat color: solid fills only, no gradients or textures. Shadows are a darker solid shape of the same hue, never a blurred drop shadow.
- Geometric construction: people and objects break down into circles, rounded rectangles, and triangles; limbs are bars rotating at joints, like paper puppets.
- Elastic entrances: things overshoot their target by 5–10% and settle back, squashing about 10% on landing before springing back. Flat shapes have no volume of their own; this beat is where their weight comes from.
- One lead at a time: only one subject makes a big move at any moment; everything else follows in a 2–4 frame stagger.
- Transitions are carried by objects: a shape in the frame grows to fill it and becomes the next scene's background — not a camera whip, not a crossfade.
</signature>

<style>
- Build: SVG or Canvas 2D, with position, scale, and rotation computed in `render(t)`.
- No sub-frame motion blur: averaging sub-frames draws translucent bands (a gradient) and stacked ghosts (4 samples on a fast-growing circle made 4 rings), and viewers pause on them. Show speed with a solid smear — the shape stretched along its velocity as one opaque solid, from about 55 px/frame — plus speed lines in a palette color. Draw big color blocks and impact frames at whole-frame time (`snap(t)`).
- Palette: 4–6 saturated solids plus one dark color for lines, text, and small dark objects (sunglasses, tires, a pan), never for large areas. Few colors means each one reads as "this character" or "this idea". Keep the hero off any field of its own hue family (a red tomato never crosses red or orange).
- Overshoot: the template's `backOut(u, s)` peaks at 4s³/(27(s+1)²) — s = 1.3 gives 6.1%, s = 1.5 gives 8%. `spring()` at its defaults overshoots 12.6%, past what this style allows.
- Squash: hold about 10% squash for 2 frames, then recover over 4 frames with about 3% stretch past rest; a squash that lasts only 2 frames in total doesn't read as a sink.
- Shape-fill transition: ease in, with the end size just covering the frame, so it fills on the frame of its sound (ease-in-out with an oversized end shape fills several frames early). Keep the zoom center inside the frame and pan as little as possible (zooming while sliding reads as a wipe), and keep the object's recognizable outline (a cuff, a glove, a crate) in frame for 4–5 frames before it fills.
- Impact reveal: a circle opens from the contact point on a surface (a table, a plate), already 150–200 px on the impact frame so its content shows, and fills the frame in 8–10 frames. A circle that opens in mid-air reads as a bubble.
- Beat skeleton: an object opens the scene → a problem appears → a tool or character arrives and solves it → result icons pop in one by one → everything gathers into one conclusion.
- Sound: bed `pop`; a `pop` or `blip` per entrance, `swish` + `pop` for scene changes. The pop bed's drop sits almost entirely below 120 Hz: give the climax a 1–4 kHz layer (chord stab, clap, snare) and lift the drop's 300 Hz–4 kHz rather than adding low end.
- Avoid: gradients, inconsistent stroke weights, everything popping on the same frame, linear motion, crossfade transitions, camera whips as transitions, translucent ghost copies.
</style>

<check>
- Off-palette pixels ≤ 1.5% of every frame (`check.py palette 成片.mp4 --colors …`; anti-aliased edges fall inside its tolerance). This catches gradients, blur, and crossfades.
- Count the subjects making big moves in each filmstrip; if more than one, stagger them.
- Overshoot amount: above 15% looks cheap, below 3% is invisible; every landing shows its squash for at least 2 frames.
- Every scene change is carried by a shape in the frame, and the fill completes on the frame of its sound (filmstrip around each transition).
- Anything the brief keeps on screen throughout is there on every frame (count its color's pixels per frame).
</check>
