# One continuous line (线条一笔画)

The whole film is a single line: it draws itself, turns corners, becomes the next shape, and finally the area it encloses fills with color. Minimal and refined; good for "from A to B".

**Good for**: openers, chapter titles, the "definition" moment of a concept (say, one line drawn from a cursor into a file, then into a chat bubble). Slow pacing; don't pack information into it.
**Reference films (technique only)**: mg-styles-15 `demos/02-line-art/` (the October 2026 test batch added a nib that reads on a light ground and curvature-based speed).

<signature>
- One line throughout: it always looks like the same line; each shape's tail is the next shape's start.
- Constant weight: one stroke width for the whole film, round caps.
- A glowing nib: the end being drawn carries a small point of light that the eye follows.
- Slow corners, fast straights: the draw decelerates into corners, like a hand turning.
- Line becomes fill: when the last shape closes, it fills outward from one point.
- Lots of empty space: most of the frame is blank, and the line is the only thing there.
</signature>

<style>
- Build: join the paths end to end, sample them yourself, and each frame draw on Canvas the stretch from the tail to the nib. SVG `stroke-dasharray` can't retract a tail while another part moves, or clip a shape where a later line passes over it.
- Design the path before the content: draw the whole route as one stroke first, then settle what the shapes are. Some figures can't be one line that ends in the right place (a full ring with a ridge inside became an arc on top with the ridge as its lower edge; a bike frame became a zigzag without a top tube).
- Nib on a light ground: about 60 px of saturated warm glow under the line (on top it washes the ink out, and crossings measure as breaks), and only a white-hot dot on the line, radius ≥ half the line width + 1 px (smaller, and the ink rings it into a paper-colored hole). A pale 25 px glow vanished at phone width. Glow belongs to the nib and lines, never to text.
- Speed: map smoothed curvature through a saturating log curve, put time nodes at corners, and cap the nib's travel per frame on screen, camera included (techniques.md). Braking by raw curvature makes small loops crawl while short straights jump 80–110 px a frame.
- Camera: follow the nib, but hold still while a shape scales or becomes another (with a fixed on-screen line width, zooming cancels the change); zoom only in a beat where the nib rests, and pull back at the end to reveal the whole drawing.
- A becomes B: retract the tail, turn on a hinge, or clip. A retracting tail is a second moving line end: stop the nib while it retracts, or keep it ≤ 1.5× the nib's speed; never more than two things moving at once.
- Occlusion: where a later line passes over an earlier shape, mask the shape only with the stretch of line already drawn — never with a vertical or horizontal edge at the nib (that thinned and broke the sun's line and left square stubs) — and cross at ≥ 25°: nearly parallel overlaps shave the line or open a gap a few pixels off. Simplest is to design the overlap away.
- Fill: after the fill, every named object and every neighbor across a line differ clearly in color (CIEDE2000 ≥ 20); paper-colored regions enclosed by lines read as holes (a paper sun among paper mountains read as a tunnel mouth).
- Palette: a dark ground with one bright line, or a light ground with one dark line, plus one fill color.
- Beat skeleton: a dot appears → it draws the first object → the line extends and morphs into a second and third → it closes into a mark or title and fills → text fades in.
- Sound: bed `ambient` with `flavor='piano'`; `chime` on the fill. `sfx.pen` is a fixed-length one-shot: for drawing, export the nib's per-frame speed from the page and synthesize a scratch that follows it in `audio.py`, on `bus='sfx'` so it doesn't duck the music.
- Avoid: breaking and restarting the line, changing its width, drawing several lines at once, a glow drawn over the line.
</style>

<check>
- One line per frame: one dark connected component (fills aside), a constant width, one nib (a light core ≥ 3 px in both directions; thinner bright streaks are encoding ringing).
- Nib speed on screen, camera included, from the exported nib point (`window.boxes(t)`): slowing into corners, no frame that jumps a long stretch.
- Joins between shapes have no gaps, thin spots, or dangling stubs.
- After the fill, each named object stands apart from its neighbors at the phone width set in prompt.md.
- Earlier lines stay clear as the drawing grows (dimming is fine, clutter is not).
</check>
