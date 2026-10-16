# Pixel art (像素)

The look of old video games: the image is made of big square pixels, the palette is limited, and characters animate frame by frame.

**Good for**: "quest" walkthroughs where a character clears one level per step; any character built from blocks snaps to the grid and becomes pixel art.
**Reference films (technique only)**: mg-styles-15 `demos/20-pixel/` (the October 2026 test batch added climax tricks in whole pixels and an original reward sound). `references/from-code-video/02-像素.md` is older; where it differs (192×108, ≤ 16 colors, no gradients), this card wins.

<signature>
- Low resolution, integer upscale: draw on a small canvas, scale by a whole number with smoothing off; edges are hard squares.
- Limited palette: 16–32 colors for the whole film; gradients are dithered (interleaved pixels), never smooth.
- Frame-by-frame characters: walks and jumps cycle through a few fixed drawings at 8–12 per second, with no smooth tweening.
- Whole-pixel motion: every position is rounded; background layers scroll at their own speeds in whole pixels.
- Optional CRT: a few scanlines, with pixel edges still clearly visible.
</signature>

<style>
- Build: Canvas 2D with an indexed buffer — a `Uint8Array` of palette indices on an internal canvas that divides the output evenly (320×180 ×6 for 1920×1080, ×8 for 2560×1440) — converted through the palette and scaled up once, so the palette and whole-pixel positions hold by construction.
- Two rates: drawings swap 8–12 times a second, but positions update every frame in whole art pixels, as old games did. Moving only when the drawing changes (10 times a second, in 20 px steps) looks choppy.
- Type: Fusion Pixel for Chinese (OFL, from GitHub `TakWolf/fusion-pixel-font` releases; woff2 builds available), Press Start 2P for Latin. Draw a title's outline, shadow, and color bands on the font's own pixel grid, then scale the whole title up: a 1-art-pixel outline around a font already scaled 2× mixes pixel sizes (mixels).
- CRT: count colors before adding it; map scanlines to a darker entry of the palette (true darkening doubled 26 colors to 52); skip it when the film plays below 0.5× on a phone (moiré); any glow goes on lines and shapes, never on text.
- Accents: choose them against what is actually behind them (gold on purple, red on cyan); a gold coin in front of a gold-orange sunset band disappears.
- Climax tricks that stay in whole pixels and the palette: a 1-frame white flash (everything but the outlines drawn white), a 3-frame hit-stop (a separate background clock stops; only a 1–3 px screen shake moves), a boat that sinks +2/+1/−1/0 px after a landing, a backlit silhouette (a dark drawing with a 1 px gold rim as it passes the sun).
- Beat skeleton: title screen → the hero runs into level 1 (one step per level) → a reward on each clear → the last level opens a chest = the conclusion. Keep every signature item (parallax included) on screen outside the first and last 0.5 s, which a compilation's transition may cover.
- Sound: bed `chiptune`; `jump` for jumps and casts; a reward is a metallic "ting" (the library's `sfx.coin`, an original motif since 10-13), and any victory phrase is written fresh for the film. Famous game sounds are recognized by interval, rhythm, and timbre, so a transposed copy is still a copy: no very short note leaping up a perfect fourth into a held note (watch the seams between layers too, such as an arpeggio's last note into a bell), and no fanfare climbing a major triad from the dominant; audio.md has the pitch check. Put the climax on `bus='sfx'` so the music doesn't duck under it.
- Avoid: motion blur (it mixes in off-palette colors), sub-pixel positions, smoothly eased characters, mixels, CRT effects that cost legibility, any sound or sprite that recalls a real game or brand. Also avoid: spawning dark-outlined confetti from a single point inside a chest/door opening (the outlines clump into a black blob on the first 2 frames — spread launch points above the lid), using a non-black dark shade inside a backlit silhouette (scanlines turn it into stripes against the moon — fill the silhouette interior with pure outline ink), teleporting the character across the middle of the screen at level cuts (pan the camera or wrap at the screen edges), and two-tone dark brick borders whose RGB values sit within 28 of each other (their median stays within 14 RGB of both and triggers `spec.py`'s `edge stripes` warning — include a third higher-contrast tile along outer edges).
</style>

<check>
- Colors: `check.py palette 成片.mp4 --colors <palette>` (with the venv python; system python3 lacks Pillow) finds no stray color clusters; lossless stills use 16–32 colors in all, counted before CRT.
- Zoom in (`sheet.py --crop x,y,w,h --zoom 4`) for soft edges, half-pixel offsets, and mixels.
- In a filmstrip of the character (`sheet.py --around`), drawings change 8–12 times a second and nothing slides by interpolation.
- Every reward or fanfare sound's pitch sequence is written out and compared as audio.md describes; nothing matches a real game.
</check>
