# Glassmorphism (玻璃拟态)

The look of a tech product launch: large soft clouds of colored light drift slowly on a dark ground, with translucent frosted-glass cards floating above. Quiet, airy, expensive.

**Good for**: openers for "first look at a new model or feature". Cards show fragments of the real product interface; never invent features it doesn't have.
**Reference films (technique only)**: mg-styles-15 `demos/12-aurora-glass/` (the October 2026 test batch added visible frost and a measured dark ground and fusion).

<signature>
- Light as the ground: a few large, blurred clouds of color on a dark ground, using only 2–3 neighboring hues on the color wheel, drifting slowly and blending. Complementary colors turn muddy.
- Cards are frosted glass: the light behind shows through, blurred; a thin bright edge; large corner radii.
- Slow: every move uses a soft sinusoidal ease and lasts at least 0.6 s as seen on screen; text only fades in with a small upward drift. One fast move breaks the mood.
- Depth layers: cards sit on two or three layers, and nearer ones move faster.
- One moment of light: a highlight sweeps across a card, or a lens glides over and magnifies what is behind it.
</signature>

<style>
- Build: light clouds on canvas or WebGL; cards in DOM with `backdrop-filter: blur()`, which works in the renderer and is cheap (4 glass layers with 48–64 px blur over WebGL: 0.17 s/frame at 1080p). Fade a glass element with its own opacity, never a parent's: under a parent below opacity 1, Chrome blurs nothing, then frosts on the last frame (techniques.md).
- Clouds: a flat center with a quick, visible soft edge (falloff exponent about 3.5–4, not 2.6), about 4 clouds of clearly different sizes, peeking out from behind card corners and edges. Clouds that are pure haze make the frost invisible, and the cards read as tinted plastic.
- Frost must be seen: behind every card keep at least one sharp-edged thing the blur visibly softens (a small light core, a far card's icon, a sun disc with a ~36 px edge).
- Fusion and a dark ground pull against each other: let clouds overlap and drift in sync, and leave whole areas dark rather than spreading the light evenly. Fusion is real when the darkest V on the line between two cloud centers is ≥ 0.6 × the dimmer cloud's peak V.
- Dark ground: clouds' tails must die out (long tails lifted #120A08 to about level 37). Add grain in the shader after tone mapping, monochrome, 2–4 levels in the near-blacks: normal-blended grain lifts black about 4 levels, and overlay grain at 0.43 levels let H.264 draw contour lines; ±5 levels looked right but raised the bitrate from 21.7 to 38 Mbps.
- Brightness is measured on the film, not set in the shader (an intensity of 0.42 came out as V 0.64). Large bright areas fade with sine in-out squared, so the tone shoulder doesn't squeeze a 0.7 s fade into 0.17 s on screen; plain sine fade-outs only for small text.
- Sweep: the band stays ≥ 0.6 s on each card and peaks at about 30 px/frame or less at 1080p (a 1.2 s sweep crossed each card in 0.3 s; 2.2 s with a 440 px band, a one-third core, and center brightness about 0.35 worked). Never darken the band along text rows (it makes stripes).
- Text on frost: milky frost washes white text out; give text a dark hard shadow (0 3–4 px 0), or deepen the glass under it — no glow.
- Warm hues: compress highlights by luminance and keep the hue; per-channel compression pushes amber to mustard, and darkening turns it brown, so shade toward peach and rose.
- Layout under a drifting camera: "overlap clearly or keep a gap" (a gap ≥ 40 px, no two edges parallel within 40 px) and "text clear of card edges" must hold on every frame, not just the last; stack cards perpendicular to the drift.
- Beat skeleton: the light comes up → cards float forward from depth → interface fragments appear inside them → the highlight sweeps → product name + one line, revealed by light (a glow rising behind the nameplate).
- Sound: bed `ambient` with `flavor='glass'`; `shimmer`, `sparkle`, `swell`; interface sounds nearly inaudible; a sound that follows the sweep can pan with it.
- Avoid: bounces, overshoot, complementary colors, an empty ground behind the glass (with nothing to see through, the glass means nothing), light spread evenly over the whole ground.
</style>

<check>
- Dark ground: on every frame of the film, ≥ 20% of pixels have V ≤ 0.10.
- Fusion: wherever the brief asks for it, the darkest V between two cloud centers (pixels not behind a card) is ≥ 0.6 × the dimmer cloud's peak.
- Every move lasts ≥ 0.6 s on screen: list each move's start and end in `cues.json` and have the page refuse to load if one is shorter; for big brightness changes, `measure.py curve --region …` shows 10→90% in ≥ 0.6 s; for the sweep, measure how long the band stays on each card.
- Text contrast against what is behind it: ≥ 4.5:1 at rest, ≥ 3:1 while the sweep passes; no glow on text.
- Hues stay within the 2–3 neighbors (`check.py hues 成片.mp4 --allow …`); zoom into gradients and dark areas of the encoded film for banding steps or contour lines.
</check>
