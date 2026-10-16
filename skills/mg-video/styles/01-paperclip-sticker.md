# Paperclip-style sticker explainer (回形针贴纸科普)

The most established package in Chinese knowledge videos: real objects are photographed, cut out, and given a white sticker border, then laid out with minimal icons and data charts on one large, pale tabletop. The camera travels across the table stop by stop, and every stop adds one new thing. It reads like an animated infographic: calm, credible, information-dense.

**Good for**: evergreen topics and explainers — the workhorse style. "5 reasons X doesn't work" or "which AI for which job" can be laid out on one table in a single continuous shot, with the camera arriving wherever the narration is.
**Reference films (technique only)**: mg-styles-15 `demos/19-paperclip/` (the big-canvas camera); the October 2026 test batch's paperclip film added a 26× dive, the magnifier sticker, and object cut-outs (lessons below). Choose your own subject and layout.

<signature>
- One table, one camera: everything sits on a canvas several times larger than the frame, and the camera only pans and zooms — no cuts. Viewers always know they are on the same table, so where things sit tells them what relates to what.
- Real objects are stickers: every cut-out photo gets the same white border — the same width on screen (about 10px at 1080p) at the stop where it is read — and a faint drop shadow. The border unifies images from different sources into one set of stickers; this is what makes the style recognizable at a glance.
- One new thing per beat: every 0.5–1 s something is added (a sticker, a leader-line label, a bar, a number), so the viewer is never just waiting.
- Charts are true: bar lengths are proportional to their values, counters stop on the real number, and a number that appears twice is the same both times. Viewers will take these numbers at face value.
- Calm typography: pale blue-grey or off-white ground, dark grey text, exactly one accent color; sans-serif in two weights only; everything snaps to one grid.
</signature>

<style>
- Route: decide up front between travelling across the table stop by stop (the last frame is the whole table) and diving into one detail. A dive must leave that detail on the table at the end, or the last frame is one lonely sticker.
- Magnifier sticker (the fix for a dive, 10-13): as the pull-back passes the magnifier's ratio, the deep view's circle lifts off as a white-bordered sticker (on the take-off frame its content matches the table exactly), flies to an empty spot, and slaps down as the camera settles; two leader lines join it to the detail and follow its outline if it pulses. Pick the ratio so everything the circle has to prove fits inside it (at 7× the circle cut off the bar's end and 31.3% measured as 25.7%; 6× fit), and drop small text inside it.
- Build: Canvas 2D with your own world→screen transform each frame, line widths and text sizes set in screen pixels. A CSS transform on one big container rasterizes text at the wrong scale, and lines in world units turn into hairlines or blobs at another zoom. Interpolate zoom in log space and anchor it as `references/techniques.md` describes (linear x/y interpolation flung the first draft's pull-back onto empty table). Stickers seen deep in a zoom need high-resolution images. Charts read their values from `cues.json`, so on-screen numbers match `sources.md`.
- Camera: long ease-in-out moves of 0.6–1 s and no motion blur (viewers pause, and blur doubles text). Per-frame zoom ≤ 1.3×: a sine ease in log space peaks at π/2 × the average rate (1.275× on the 26× dive); if a move is faster, make it longer. Wait 0.2 s after it settles before adding anything, because text that appears while the camera moves goes unread.
- Sticker slap: drop from 1.25×, fully opaque (no fade-in); the contact frame is 1.03 wide × 0.95 tall, then 1.01, then 1.0; on that frame the shadow jumps from far and soft (blur 40, offset 27) to close (14, 5).
- Cut-outs: `hyperframes remove-background` is a human-segmentation model and fails on objects. Threshold by color or brightness, keep the largest connected parts, close the mask, then bake the border (techniques.md). White or pale objects (ice, snow, paper, white devices) swallow the white border: keep a strip of their dark background (the iceberg kept 29% dark sea) or cool them slightly. If the identifying part is small (a pump head), enlarge it.
- Beat skeleton: 0–0.5 s the first sticker slaps down with a question → each stop 1.5–2 s (camera arrives → sticker lands → leader line draws out from the sticker edge → label text wipes in) → pull back to the whole table and land one conclusion in large type, with its proof (the bar, the magnifier) still in frame.
- Sound: bed `explainer`; `sticker_slap` when stickers land, `pen` for leader lines, `swish` for camera moves, a rapid run of `tick` for counters; the conclusion is the loudest hit. The bed's drop puts a kick and sub on every bar, and that bass holds the master limiter down: after the drop's first kick, cut the music below about 180 Hz by about 9 dB (it raised the climax's lead on a phone from 1.6 to 2.8 dB; the knobs are in `references/audio.md`).
- Avoid: mixing bordered and borderless images, hard cuts, bars drawn out of proportion for looks, a second accent color, stickers arriving together, labels fading in from the center (draw them out from the sticker edge).
</style>

<check>
- Border: the same on-screen width (±2 px) on every sticker at its stop; at 300% (`sheet.py --crop x,y,w,h --zoom 3`) no gap or background halo between object and border.
- Every push and pull: no frame zooms more than 1.3× over the previous one, and no frame-to-frame change is more than twice its neighbours' (spec.py's top frame changes).
- Each stop holds long enough to read its text (about 4–5 Chinese characters per second); labels meet the text-size rule in techniques.md and read at the phone width set in prompt.md.
- No key text, magnifier, or leader line crosses the 5% safe frame on any frame, including while the camera moves and during pulses (`sheet.py --safe 0.05` on stills, `measure.py margins` per frame).
- Every number traces to `sources.md`; measure the bars on the encoded film, inside the magnifier too, to confirm they are proportional.
- The last frame holds the whole table and the proof of the conclusion.
</check>
