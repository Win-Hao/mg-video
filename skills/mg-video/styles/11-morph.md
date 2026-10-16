# Shape morph (形变)

One shape turns smoothly into another, its outline continuous all the way. The basic grammar of telling a story with shapes: the change itself is the metaphor.

**Good for**: "A is really B" — a chat bubble becomes a terminal window, a file becomes a checklist. Also works as a transition between B-roll shots.
**Reference films (technique only)**: mg-styles-15 `demos/08-morph/` (the October 2026 test batch added radial interpolation and a measured morph speed).

<signature>
- No jumps, no knots: the outline stays one continuous shape from start to finish, and is a clean shape at every point mid-morph.
- Complex shapes don't morph directly: between two complex shapes, collapse to a simple intermediate (circle, capsule), then unfold into the next.
- The morph has a body: a little squash-and-stretch and a slight rotation while it changes, like something elastic transforming.
- On the beat: each morph completes on a beat, and the background color changes with it.
- It means something: the two shapes are related in meaning, and the viewer gets the metaphor.
</signature>

<style>
- Build: if each shape is star-shaped about a center (every ray from it crosses the outline once), sample the radius along fixed rays and interpolate the radii: no knots by construction, no vertex matching (flubber is the fallback for other shapes). Straight interpolation carries sharp corners into the middle states as kinks, so while morphing, pull the outline toward a copy of itself smoothed with a Gaussian over angle, most at the midpoint. Glyph outlines come from the font file via opentype.js.
- One morph = collapse N frames + hold 2–4 frames on the intermediate + unfold N frames, 8–12 frames per half, fastest in the middle, slow at both ends. Give the intermediate the average area of the two shapes (±15%), or the two halves run at visibly different speeds (2× in the first draft).
- Background: change it on the unfold's landing beat only, not on the intermediate; the intermediate's sound is a notch softer than the landing's.
- Decorations (rays, sparkles, a writing line) are not "the outline": place them from the shape's live bounding box, ≥ 24 px clear of it on every frame (at a fixed radius they touch the shape when it rebounds).
- The landing point is the stop point: after the climax lands, nothing slides to find its place. Keep the hold alive with breathing (≥ 3% scale) or a flash, scaled about the shape's own center, not its foot.
- A round-capped line can't get shorter than its width: thin it as it shrinks (below about 15% of its length it stops shrinking).
- Beat skeleton: an object → collapses to a circle → unfolds into the second → … → ends as the title or a conclusion icon; usually 4–6 morphs.
- Sound: bed `future_bass` with `prog='Imaj7 V vi7 IVmaj7'` (the default progression starts on IVmaj7, so the ending doesn't resolve). Its drop lifts mostly through the 808: lower the kick with `levels=` and give the climax a saturated bright chord; if chords must change as shapes land rather than on bar lines, build them with `inst` (audio.md). One `morph` or `whoosh(kind='sci')` per morph, rising in pitch each time. Pick a BPM where a beat is a multiple of 4 frames (112.5 BPM = 16 frames at 30 fps).
- Avoid: a crossfade passed off as a morph, morph speeds that vary for no reason, chains that look nice but mean nothing, any drift after the landing.
</style>

<check>
- Mid-morph outlines: test every frame's outline for self-intersection in code (a build-time assertion), and pull a still at each midpoint to look for knots and spikes. One blob per frame and no in-between colors from a crossfade (`check.py palette` on lossless stills; on the film, ignore enclosed slivers under 150 px, which 4:2:0 encoding leaves at saturated edges).
- Speed: measure each half from its first frame to the frame before landing (the landing frame is a deliberate one-frame impact, 24–46 px/frame here); halves and successive morphs run at similar speeds.
- Decorations keep ≥ 24 px from the shape and stay inside the 5% safe frame on every frame, measured on rendered pixels (`measure.py margins`): SVG `getBoundingClientRect` ignores stroke width and skips vertical lines.
- `sheet.py --beats cues.json`: every beat changes visibly, measured as the largest change within the beat (not first frame against last); the hold after the climax is exempt.
- Explain the metaphor to someone who hasn't seen it: can they say what it is about?
</check>
