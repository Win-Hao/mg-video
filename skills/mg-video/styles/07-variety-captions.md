# Variety-show captions (综艺花字)

The emotional text that TV variety-show editors add: chunky outlined words bounce in, change color and shape with the speaker's mood, and come with a cartoon sound effect. Now standard in vlogs, interviews, and comedy clips.

**Good for**: rendered with a transparent background and laid over talking-head footage to mark emotions and reversals; it also works over other footage inside a film. Keep it separate from subtitles (a separate job): subtitles cover every line; variety captions appear only on punchlines, surprises, and turns.
**Reference films (technique only)**: mg-styles-15 `demos/18-hanazi/` (vertical; the October 2026 test batch added hole-free outlines and captions over stock footage).

<signature>
- Sticker text: a heavy, round, chubby typeface with at least two outlines (white inside, colored outside) plus a hard drop shadow, readable over any background. The text never glows.
- It pops: scales past full size and settles back in about 8 frames, or bounces in letter by letter with a 2-frame stagger. While holding it wobbles slightly rather than sitting dead.
- Emotion has symbols: surprise gets a burst frame and radial lines, embarrassment gets sweat drops and small text in parentheses, smugness gets sparkles, sarcasm gets tilted handwriting.
- It has sound: every appearance comes with a cartoon effect, and the text lands 2–3 frames after the beat it reacts to, which feels more natural.
- Loud color: high saturation, no more than three colors on screen at once.
</signature>

<style>
- Type: Resource Han Rounded CN Heavy (源樣圓體; GitHub CyanoHao/Resource-Han-Rounded v0.990, SIL OFL 1.1), used in the test film: round terminals and corners, strokes 0.16 em that the font itself thins to 0.11–0.13 em in dense characters. Never faux-bold it (+0.012 em turned 餐, 嫩, 焦 into ink blobs). ZCOOL KuaiLe is angular and medium weight, not chubby.
- Colors: white and dark ink are already in the outlines, so one accent is left, and the fill must differ from the outline next to it: ink by default (an accent fill reads as hollow; a white fill merges with the white inner outline). Layers that worked: ink fill, white inner outline 0.05 em, accent outer 0.09 em, ink outer 0.035 em, hard shadow 0.085 em straight down. At any moment: ink + white + one accent.
- Outlines come from the whole word, not each glyph: rasterize on canvas, close the glyphs slightly (1.5 px at 166 px, so strokes closer than ~4 px merge), dilate to the white layer, close it, and flood-fill from the canvas edge so every enclosed hole is filled; the accent and ink layers are dilations of that hole-free white layer. `paint-order: stroke`, or strokes of several widths stacked on one glyph, leave holes and hairlines wherever a counter or gap falls between two radii.
- A slam that worked: scale 1.25 → 1.12 → 0.92 → 0.97 → 1.05 → 1.02 → 1.0 while dropping 30 px, the burst frame one frame earlier (0.82 → 1.06 → 1.0). No motion blur; it ghosts the text.
- Small text in parentheses: if it doesn't fit under the main word, put it lower left or lower right within 20 px, about 40% of the main word's height, in the same accent outer ring, tilted −3° to −5°, popping 0.4–0.6 s after the main word with 1.08 overshoot and wobbling with it as one group; prefer the empty space under the action.
- Over the talking head: transparent page, `render.mjs --alpha` to ProRes 4444 at the footage's size and frame rate (2560×1440, 60fps); place captions in the space beside the head against a still of that exact moment, never over the face, never in the subtitle zone at the bottom.
- Over footage inside the film: decode and time it as techniques.md describes (bt709 conversion, `await img.decode()`, 25→30 fps). Captions keep clear of the action on every frame they hold, not just the landing frame. To make a reversal readable in one paused frame, freeze the footage 6–10 frames on it (shifting the earlier footage forward); a long still lead-in can be frozen or sped up so the climax lands where the brief wants it. Shake goes inside the zoomed footage's transform, with each edge's overflow larger than the shake (≥ 46 px against a 14 px shake); only the outer stage clips.
- At most 6 characters per caption, because it stays on screen for only a second or two. The text itself is Chinese.
- Sound: `boing`, `duang`, `pop`, `record_scratch`, `slide_whistle`; for a talking-head overlay deliver only the effects stem `out/stems/sfx.wav`. Soft-onset sounds (`squeak`, a low `boing`) need a `pop` or woodblock transient on top to be measurable; `sparkle` starts on a random note, so use `chime` where sync matters.
- Avoid: long sentences, thin type, faux bold, glowing text, an emotion that doesn't match the face or the action, fighting the subtitles for space.
</style>

<check>
- At 300% on the encoded film (`sheet.py --crop x,y,w,h --zoom 3`): no holes, white slivers, or hairlines in counters and between strokes.
- `check.py accents 成片.mp4 --palette <ink,white,accents> --accents <accents>`: never more than one accent, so never more than three colors, on screen.
- The whole caption layer, outlines, shadow, and overshoot frames included, stays inside the 5% safe frame on every frame: render only the text layer (a `?layer=text` switch in the page) and run `measure.py margins` per frame.
- No frame shows the page background at the edges (the template's magenta makes it obvious; spec.py flags it).
- Each caption lands 2–3 frames after its beat (`land` against `beat` in `cues.json`), and the beat has a sound onset.
- Composite one frame over the footage still: the face and the subtitle zone stay clear; over a dark and a light background, transparent edges show no black or white fringes.
- Each caption appears at its moment in the footage, and the emotion matches.
</check>
