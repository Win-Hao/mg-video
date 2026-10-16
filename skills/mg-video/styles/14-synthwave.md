# Synthwave / VHS (Synthwave / 录像带)

1980s sci-fi posters and videotapes: a purple night sky, a striped sunset, a neon grid floor rolling toward the camera, chrome lettering, plus tape scanlines and color misregistration.

**Good for**: then-versus-now topics ("the computer of thirty years ago vs. AI today") and openers for crossover videos.
**Reference films (technique only)**: mg-styles-15 `demos/10-synthwave/` (the October 2026 test batch added the slam that powers the world on and picture driven by the music).

<signature>
- Sunset and grid: a gradient sun with horizontal slits sits on the horizon; the ground is a perspective grid scrolling toward the camera.
- Neon glow on lines: lines carry two layers of light, a bright narrow one hugging the line and a wide faint one around it.
- Chrome type: the title is a metallic gradient with highlights, and a flash of light sweeps across it as it slams in; the type itself never glows.
- Tape texture: scanlines, red and blue channels offset by a pixel or two, an occasional jolt or skipped frame.
- Palette: deep purple to magenta sky; neon in magenta and cyan.
</signature>

<style>
- Build: WebGL for the grid, sun, and mountains; the chrome type drawn on canvas with metallic gradients (a canvas gradient follows the transform in force when it fills: after a per-glyph `setTransform`, build the gradient in that glyph's coordinates, or the whole face takes the first stop; techniques.md); a final full-screen post pass for scanlines and channel offset. Type gets a dark outline and a hard shadow, no glow.
- Channel offset: shift only R against G+B, so fringes stay red and cyan. Shifting R and B in opposite directions puts yellow-green fringes on white highlights, outside the palette, worst on glitch frames.
- At phone width, scanlines and a 1–2 px offset disappear. The tape signals that survive are a tracking band, a rolling bright band, a tape jump, and head-switching noise along the bottom; keep at least one in the final hold. Give glitches a cause: the rolling band reaching the title triggers the jump.
- The slam: darken the world about 40% just before it, then power it on from the horizon toward the camera, row by row; brightening the whole screen at once swallows the "power on". The sweep across the chrome is a narrow, hard-edged band with a near-white core, not a soft wide glow.
- Speed without blur: smear the title as one opaque silhouette stretched along its motion, or 1–2 opaque copies in darker tones; translucent copies count as ghosting.
- Picture that breathes with the music: run `audio.py` first, export per-frame band energies (`out/eq.json`), and let the page read them, normalizing each band by its own 1-second mean; end the bed with `end='pulse'` so the motion doesn't die in the hold.
- Beat skeleton: tape-start noise → the camera skims low over the grid as the sun rises → the chrome title slams in → small neon script lights up stroke by stroke → keep flying, settle on the hero frame.
- Sound: bed `synthwave` (it already has a riser into the drop and a crash on it; don't add another); `vhs_noise` at the start. `impact('cinematic')` is almost all 90→32 Hz, and the master limiter erases its lead (6–10 dB on the stem, 0.1–0.6 dB after mastering): make the slam a saturated bright chord plus a metallic clang and a bright cymbal, with the impact high-passed around 45 Hz underneath, and don't push the music on the slam. A small sound right after the slam needs a few dB more (about 4) to clear the tail.
- Avoid: tape effects so heavy the text is unreadable, glow on or around the type, colors outside the purple–magenta–cyan range, translucent motion trails.
</style>

<check>
- Title and subtitle are readable at the phone width set in prompt.md.
- `check.py hues 成片.mp4 --allow 170-200,230-345` (cyan, purple to magenta) finds no patch of another hue (isolated 1 px fringes aside).
- Compare stills with the post pass on and off: is it adding or smearing?
- In the last second, at phone width, at least one tape signal is still visible.
- Zoom into the slam frames: opaque smears, no translucent ghosts, no glow on letters.
</check>
