# Techniques and pitfalls

## Contents
- Environment
- Page contract and determinism
- Fonts
- Key frames first, low-res preview, frame-by-frame review
- Motion blur
- Common moves
- Camera
- Lines and outlines
- Canvas, CSS and WebGL pitfalls
- Light, grain and fades
- Measuring from the page
- Footage underneath
- Transparent output
- Reading on a phone
- Encoding
- Assets
- Reading the mg-styles-15 source
- Render speed and the shared machine

Lessons that belong to one style live on its card in `styles/`.

## Environment

Set up and measured on 10-13: Apple M4 (10-core GPU, 24 GB), macOS, Chromium 152 via Playwright 1.64, ffmpeg 9.0.2, Python 3.13 in `~/.venvs/mg-video`, Node 26, Blender 5.2.2 LTS.

- `brew install uv` hung for 10 minutes in Homebrew's auto-update; `HOMEBREW_NO_AUTO_UPDATE=1 brew install uv` finished in a minute. Without uv, `setup.sh` needs a system Python ≥ 3.11 (numpy 2.4); the macOS system python3 was 3.9
- `npx playwright install chromium` downloads both Chromium and its headless shell into `~/Library/Caches/ms-playwright/`
- ffmpeg 9 removed `-vsync` (use `-fps_mode passthrough`), and this build has no `drawtext`. It takes colour tags from the frames, so `-color_primaries`/`-color_trc` on the command line are ignored: end the filter chain with `setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709` (`render.mjs` does since 10-13 19:50, the Blender `encode.sh` too)
- Paths may contain non-ASCII characters (e.g. Chinese folder names): Node helper scripts resolve their own path with `fileURLToPath(import.meta.url)` (a `URL` pathname is percent-encoded and not found), and ES-module helpers need `"type": "module"` in `package.json` (`new.sh` writes it)
- Blender: `brew install --cask blender`; run headless with `blender -b --factory-startup -P scene.py -- <args>`; for the GPU set `prefs.compute_device_type = 'METAL'`, call `prefs.get_devices()`, enable the Metal device, then `scene.cycles.device = 'GPU'`. The whole 3D flow (settings, timings, pitfalls) is on `styles/15-3d-material.md`

## Page contract and determinism

The `index.html` that `tools/new.sh` creates already follows the contract: size, fps, and duration live in `video.json`; `window.render(t)` draws second t; the page sets `__ready` when loaded and `__error` on failure. `render.mjs` checks `__error` after every frame (since 10-13), prints the reason and exits instead of writing more frames. The template sets `__error` from `window.onerror`, `unhandledrejection` and `webglcontextlost`, and does module imports inside `build()`, so an exception in an imported module (say, a sprite row of the wrong width) reports instead of hanging.

Each frame must depend only on t, because `render.mjs` jumps around: parallel workers each start mid-clip, and sub-frames sample several moments inside one frame. So:

- No requestAnimationFrame, CSS animations or transitions, setTimeout, or Date.now; use the template's `rng(seed)` for randomness
- Physics, particles, and collisions are simulated from the start at a fixed step inside `build()` and stored; `render` only looks them up
- **Compare times by frame number**, with `frameOf(t)` and `at(t, sec)`: `t >= 3.6667` is one frame late, because 110/30 is smaller than 3.6667 (three of four captions in one film landed a frame late)
- WebGL: `getContext('webgl2', { preserveDrawingBuffer: true })`, or screenshots come out black. A lost context also writes black frames silently (one full render was black from 7.03 s, and `blackdetect` misses partial black areas): check `gl.isContextLost()` before and after drawing and throw
- Three.js: no `THREE.Clock` or `setAnimationLoop`; in `render`, pose the camera and objects, then call `renderer.render()`
- D3: only scales, shapes, and geo projections — not `d3.transition` (it runs on timers)
- Install npm packages in the project folder; bare imports (`import … from 'three'`) need an importmap pointing at `./node_modules/…`
- **Debug layers by query string**: `render.mjs "index.html?layer=text"` passes the query to the page (the server ignores it). Read it with `new URLSearchParams(location.search)` to render only the text layer (to measure its box on every frame), drop the background, or render two variants' stills side by side (`?v=2`)
- **Magenta page**: the template's `body` background is `#ff00ff`, so a frame where a shake or a moved stage reveals the page edge is obvious, and `spec.py` fails it (a #111 background hid a 2–14 px reveal against dark footage)

## Fonts

**A missing font file can hang the page**: when reproducing mg-styles-15 on 10-06, `document.fonts.load` threw on a 404, the page never set its ready flag, and the renderer waited five minutes before timing out. The template's `needFonts([...])` throws a clear error naming the font, and `render.mjs` stops on it.

- Put fonts in the project's `fonts/` and declare them with `@font-face` in `index.html`
- Pass `needFonts()` the strings actually on screen: a generic test string can't tell whether a glyph the film uses is missing
- Suggested open-source fonts (check each license): Noto Sans SC / Noto Serif SC (variable), LXGW WenKai, LXGW Marker Gothic, ZCOOL KuaiLe, Smiley Sans, Douyin Sans, Anton, JetBrains Mono, Fusion Pixel (pixel Chinese, woff2 only), Resource Han Rounded, M PLUS Rounded 1c
- Where to get them: the Google Fonts repo, `https://github.com/google/fonts/raw/main/ofl/<family-lowercase>/<File>.ttf` (Poppins was fetched this way on 10-06); fonts not in it (LXGW WenKai, Smiley Sans, Fusion Pixel, Resource Han Rounded, Douyin Sans…) from the releases page of the font's own GitHub repo
- Use only fonts whose license allows it (OFL, Apache, explicitly free for commercial use) and record them in `CREDITS.md`; system fonts listed by `fc-list :lang=zh family` (PingFang and others) render locally but may not be licensed for publishing

## Key frames first, low-res preview, frame-by-frame review

Make 6–10 key moments look like finished posters before animating anything. If the stills don't work, motion only makes them messier; a change at the still stage costs seconds, after a full render it costs minutes.

- Stills: `node <skill>/tools/render.mjs --stills 0.3,1.5,4,7.2,9.5` writes to `check/静帧/` and clears it first, so nothing stale stays mixed in (`--keep` keeps older stills); open each one
- Low-res preview of the whole clip: `--scale 0.5 --out check/预览.mp4`; layout coordinates are unchanged, screenshots are half size and much faster
- Filmstrips: `~/.venvs/mg-video/bin/python <skill>/tools/sheet.py check/预览.mp4 check/逐帧-3.2.png --around 3.2`. Lesson from an early test film: most real problems sit in the few frames of a transition, which evenly spaced sampling misses. Follow a small area (a 54 px label) with `--crop x,y,w,h --zoom 3`
- Coordinates read off a labelled sheet are 26 px too low (the label strip); use `--nolabel` for full-resolution stills
- The last frame: `ffmpeg -ss 9.967` may return nothing; select it by number, `-vf "select=eq(n\,299)"` (`sheet.py --at` does)

## Motion blur

**Default: no multi-sample blur.** `motionBlur.samples` in `video.json` (or `--mb N`) averages N moments across the shutter. On a paused frame that average is N stacked copies with soft bands between them: it reads as a rendering error, and in flat styles as a gradient. 4 samples show as 4 steps above ~150 px/frame, 8 samples at ~200 px/frame are 8 ghosts. Viewers pause (on compilations, tutorials, anything with text to read), so keep it at 1 and draw the speed:

- **Solid smear**: stretch the moving shape, or a word's silhouette, along its path into one opaque shape, or add 1–2 opaque copies in darker tones of its colour. Semi-transparent copies are ghosts again
- **Per-frame travel ≤ the object's own size**: an `io2` ease peaks at twice the average speed (850 px in 0.4 s moved 140 px/frame mid-way, more than the ball itself); use a sine ease or more frames
- **Per-frame zoom ≤ ~1.3×**: under a sine ease, a Z× zoom over N frames scales its fastest frame by exp(ln Z · π / 2N), so N ≥ 6 · ln Z (a 28× push needs at least 20 frames; at about 10 frames it jumped 1.7× and looked like a skipped frame)

**When the style needs blur** (liquid, fast camera moves), **compute adaptive sub-frames in the page.** Draw each frame as the average of n sub-frames, each at its own time inside the shutter and at its own sub-pixel offset (an R2 sequence), so one pass gives motion blur and anti-aliasing. Set n from the largest on-screen displacement during the shutter: one sub-frame per 1–1.6 px, between 4 and 40–64. The liquid film rendered in 2.5 min this way against 6 min with fixed 4 samples, with no stacked outlines. Pitfalls:

- Count everything that moves, not only centres: squash and stretch, reflections (they move against the body, about twice the relative speed), broken-thread tips, thin highlights. Hair-thin detail needs ≤ 1 px between sub-frames
- Around snaps, landings and contacts the shape changes faster than any centre moves, so go to the maximum there, but cap it: 128 sub-frames around every collision took the render from 2.5 to 10 min
- **Make the motion continuous inside the shutter first**: a squash completed in two frames, or a part going from rest to full speed in one, leaves one sharp copy plus one streak at any sub-frame count. Ease such moves over 2–4 frames
- **Batch the GPU**: `gl.flush()` after each sub-frame and `gl.finish()` every 8. 128 passes queued at once tripped the GPU watchdog on a shared machine and lost the context
- Check: the top 10% of frames by frame-to-frame change, cropped at 2×, show smooth streaks and no parallel outlines

**Hard cuts, impacts and big flat blocks** whenever several moments are sampled in one frame: test hard cuts on frame-snapped time, `if (snap(t) >= cut)`, and draw big flat-colour blocks and the impact frame on snapped time too (or clamp the falling object's time at the hit). Otherwise sub-samples straddle the event: half the copies in the air and half landed, or a fast-growing circle as concentric rings.

Not for pixel art (it mixes off-palette colours); on-twos passages are holds anyway. Blender's own motion blur (Cycles, a 0.5-frame shutter) is true blur and fine.

## Common moves

The template provides `bezier`, `spring`, `backOut`, `io2`, `prog`, `snap`, `frameOf`, `at`, `drawingIndex`, `drawing`, `jit`, `onTwos`, `rng`:

- A curve from a style card such as `cubic-bezier(0.34, 1.56, 0.64, 1)`: `const e = bezier(0.34, 1.56, 0.64, 1)`, then `e(prog(t, start, end))`
- **Overshoot to a set amount**: `backOut(u, s)` peaks at 4s³ / 27(s+1)²: s = 1.5 → 8%, s = 1.3 → 6.1%. `spring()` at its defaults overshoots 12.6%, beyond the 5–10% the flat-vector card asks for, and `ease.back` about 9.8%
- Pop with overshoot: `spring(t - start)`, or scale 0 → 1.15 → 1.0
- Stagger: offset element i's start by `i * 3 / V.fps` (3 frames)
- **Drawings per second at 30 fps**: on twos (2 frames per drawing) is 15/s; 12/s alternates 2- and 3-frame holds; 24/s alternates 1, 1, 1, 2. `drawingIndex(t, perSecond)` follows that frame table, `drawing(t, per)` gives an integer index for a fixed hold, and `jit(seed, i)` a deterministic jitter per drawing; return the index as the render key so the renderer reuses screenshots. An event that falls inside a hold adds a one-frame drawing: move it to the nearest drawing boundary (land one frame early)
- **Hit-stop**: freeze the background on the climax with its own clock that stops for the freeze and resumes after (`const tb = t < h0 ? t : t < h1 ? h0 : t - (h1 - h0)`, with h0–h1 the freeze in seconds), while the shake or the flash keeps moving on top
- Big-canvas camera (paperclip style): see Camera
- Tile-flip wave (a general-purpose transition): draw sides A and B offscreen, cut the frame into a grid, and give each cell `scaleX` 1 → 0 → 1 with its own phase, switching to B at the halfway point; phases offset by distance from a point make a wave. Give each tile at least 3 frames (at 2, the middle frame is exactly zero wide and nothing seems to flip), switch image smoothing off on the squashed frames (a 2 px cross interpolates to grey), and make tiles an even number of grid cells wide so the hinges land on grid lines
- Cell-by-cell reveals (text or colour blocks appearing one cell at a time): put the remainder in the first cell so **the last cell lands on the beat**. A plain `Math.ceil(u * n) * step` finishes 2 frames before the beat and misses the sound's onset (seen on 10-06). Cut text by glyph, not into equal-width cells: an equal cut left the last cell with 15 px of ink, and the beat landed on nothing
- **Circle reveal on an impact**: start at a radius of 150–200 px, so the impact frame already shows what's inside, and fill the frame in 8–10 frames (ease in-out). Open it from the contact point on a surface (a table, a plate) so it reads as falling in, not as a bubble
- **Zoom through an object** as a transition: keep the zoom centre inside the frame and the pan small (a sleeve that zoomed while sliding to the centre read as a wipe), and keep the outline that names it (a cap, a cuff, a glove) on screen for 4–5 frames
- Thin opening lines and faint grids vanish on a phone: draw them heavier at first (e.g. 6px) and settle to the fine weight within 0.3 s, so the hook still reads. If the prompt states a line width, skip this or name it in the prompt as an exception
- **Picture following the music**: run `audio.py` first and export per-frame band energies (`out/eq.json`) for the page to read; normalise each band by its own mean over the surrounding second, or the loud drop flattens everything else. Re-render after every audio change

## Camera

- Big-canvas camera (paperclip style): draw everything into one large world; camera keyframes (x, y, zoom) live in `cues.json`; `render` interpolates them. Long eases for travel, a slight drift when settled
- **Large zooms in Canvas, not CSS**: a CSS transform on a big container rasterises text and lines at the wrong scale, and world-space line widths turn into threads or blobs at another zoom. Map world to screen yourself (`sx = (wx − cx) · z + W/2`) and give line widths in screen px
- **Zoom in log space about an anchor**: interpolate ln z, not z, and don't interpolate the camera centre linearly at the same time, which swings the target out of frame (an empty frame at 7.1 s). Take A, the camera centre of the more zoomed-in end; slide its screen offset s from (A − c₀) · z₀ to (A − c₁) · z₁ on the same ease as the zoom; the centre is c = A − s / z
- **Picture-in-picture and magnifiers**: write the scene as `drawScene(t, cam)`, drawing with whatever camera it is given; a lens is the same call with another camera, clipped to the lens
- **Shake**: put it inside the transform of the enlarged footage or stage, give every edge more overscan than the shake amplitude, and clip only at the outermost stage. Shaking a frame-sized `overflow: hidden` container revealed the page at the edges on the climax frames viewers pause on
- **Look-at cameras**: with a camera given as target + distance + pitch, changing only the pitch orbits the target; to tilt the head in place, fix the camera position and derive the new target
- **A moving camera adds to on-screen speed**: a pan under a retracting line made its tail move 77 px/frame on screen. Check tracked points in screen space (see Measuring from the page)

## Lines and outlines

- Line drawing, simple case: SVG `stroke-dasharray = total length`, `stroke-dashoffset = total length × (1 - progress)`
- **When the tail retracts too, or something hides part of the line**: sample the path yourself (an arc-length table) and draw on Canvas the segment from tail to nib
- **Pen speed from curvature**: slowing the pen in proportion to curvature makes small loops crawl and the short straights between them jump (80–110 px/frame). Smooth the curvature along the path (Gaussian, σ ≈ 16 px), pass it through a saturating log, slowness w = 1 + 0.62 · ln(1 + κ / 0.0045), κ in radians per px (a loop of 85 px radius runs at ~0.55× the straight speed, sharp corners at ~0.35×), pin times at corners and stage ends, then cap the screen speed (58 px/frame there) by raising the floor of w and iterating
- **A later line hiding an earlier one**: hide only with the part of the later line already drawn, its own stroke being the boundary. Never cut along an edge at the nib: that vertical edge thinned, broke and left square stubs on the line it crossed (a fatal problem in round 2). Let lines cross at 25° or more; nearly parallel overlaps leave a cut or a gap of a few px either way
- **Round caps can't shrink below the line width**: a round-capped line is never shorter than its width, so to retract it below ~15% of its length, thin it while it shrinks (rays that vanished at 30–45% of their length looked like a blink)
- **Outlines around overlapping shapes**: take the union, then stroke it. Stroking each lobe of a cloud left broken ink ends at the seams; stacking strokes of different widths on the same glyphs showed the lower layer through counters and narrow gaps. For multi-layer outlines on text, build every layer from the word's merged outline with its holes closed and filled (distance transform, closing, flood fill)
- Joining two solid shapes (a ring and a bar, a line and a block): don't put the endpoint exactly on the seam — antialiasing shows a notch or a gap. Extend the endpoint inside the other shape's inner edge and hide the join under it with a half-plane clip. When several dimensions constrain each other (endpoint, inner edge, radius), check the others before changing one

## Canvas, CSS and WebGL pitfalls

- **Huge coordinates**: points near a 3D camera project to tens of thousands of px, and the fill goes wrong (big black holes); clip at the near plane and draw only points that project within a sane range
- **Long, thin, self-intersecting polygons** (a 480-point terrain strip) fill wrongly on the GPU; split them into small quads
- **Full circles**: `arc(x, y, r, 0, 2 * Math.PI)`. A circle started at a rotated angle, `arc(x, y, r, a0, a0 + 2 * Math.PI)`, vanished on some frames
- **Gradients use the transform at fill time**: one gradient filled after a per-glyph `setTransform` gave each slanted chrome glyph its first colour stop only; build the gradient in the coordinates of the fill
- **`lighter` compositing on saturated colours clips to yellow or white** (a cyan line core turned gold); to brighten, raise the line layer's alpha before colouring it
- **`backdrop-filter` and opacity**: Chrome disables `backdrop-filter` on an element whose ancestor has opacity < 1; put opacity on the glass element itself, or the card fades in clear and frosts only at 1
- **CSS `drop-shadow`** on a rotating element rotates with it; put it on a non-rotating wrapper
- **Paper flips**: with `perspective-origin` above the frame the lifted edge shows obliquely; centred, the sheet swings like a door
- **SVG `getBoundingClientRect()` ignores stroke width** (a vertical line measures 0 wide); check margins on rendered pixels

## Light, grain and fades

- **Shader intensity isn't film brightness**: after blending and tone mapping, a light written as 0.42 came out at V 0.64, as bright as the lead. State and check brightness as V measured on the film (`measure.py curve`, `measure.py colorfrac`)
- **Fade big bright areas by screen brightness**: a 0.7 s fade-in passed the tone curve's shoulder and showed as 0.17 s. Use a sine in-out (squared if still abrupt) for big brightness changes and keep sine ease-out for small text, then measure the region with `measure.py curve` (10→90% rise time and largest one-frame jump, in V on the encoded film; the fixed sun measured 0.77 s and at most 4.5 levels per frame there)
- **Grain goes after tone mapping**: added before it, grain fades to 0.43 levels in near-black and H.264 draws contour bands there. Add monochrome grain after tone mapping, 2–4 levels in near-black; ±5 levels looked right but took the bitrate from 21.7 to 38 Mbps

## Measuring from the page

The page knows where everything is; a script guessing from pixels doesn't.

- **Boxes**: define `window.boxes(t)` returning `{name: [x, y, w, h]}` in output pixels (or polygons, `{name: [[x, y], …]}`); full renders then write `out/boxes.json`, and `render.mjs --boxes` writes only the JSON, fast. `measure.py margins` and `measure.py overlap` read it, and so can a reviewer's script. Reviewers who copied the camera into Python had to edit their scripts every time the builder moved something
- **Text boxes from glyph metrics**: export each label's box from `measureText()` (`actualBoundingBox*`) as you draw it: horizontally the text's own width, vertically its ink, not the DOM box or the line height (a centred full-width box flags overlaps that aren't there; measuring from pixels counted a box's border as text)
- **Tracked points**: export the screen position of anything whose speed matters (a nib, a tail, a ball) and measure px per frame on screen
- **Every frame, overshoot included**: margins measured on settled frames missed overshoot frames twice (78 px against a reported 102). Render the text layer alone (`?layer=text`), or run `measure.py margins` over every frame
- **Contrast under text**: render the frame once with the text hidden, measure the background under each text box, and compute the contrast ratio against the text colour
- **Chinese text size**: "≥ 48 px" means font size unless it says ink. Ink is measured on the encoded frame, on full-height characters only (digits, 三四五六日; not 一 or 二), without brackets, outlines or shadows: one caption measured 68–72 px per glyph and 56 px as a whole line, and builder and reviewer misread each other
- **One decode per check**: `measure.py` decodes the film once, at a working width of 960; separate scripts each decoding the 1080p film ran past a 120 s command timeout

## Footage underneath

For captions or graphics over real footage:

- Extract frames with an explicit conversion, or the colours shift: `ffmpeg -i in.mp4 -vf "scale=in_color_matrix=bt709:in_range=tv,format=rgb24" f%04d.png`
- `await img.decode()` before drawing a frame in `render(t)`, or the first draw can come out empty
- 25 → 30 fps: map frame to frame (plays 1.2× fast, no repeated frames) or keep real time (every fifth frame repeats); choose per shot
- Graphics stay off the action on every frame they are on screen, not only on the frame they land
- A long static stretch in the footage pushes the climax early (36% in one film): freeze or speed-ramp the footage and use the wait for build-up

## Transparent output

For overlays on the talking head (variety captions, labels, corner tags), render ProRes 4444 with `render.mjs --alpha 透明.mov`. Set the page's `html, body` background to `transparent` and paint no backdrop. The alpha channel was verified with DOM elements (10-06); a WebGL canvas needs `alpha: true` and a clear color with alpha 0, which hasn't been tested yet — check one frame first.

Check the edges: `ffmpeg -i 透明.mov -vf "select=eq(n\,30),alphaextract" -frames:v 1 a.png` shows the channel; then composite a frame over a dark and a light background and look for black or white fringes along the outlines.

## Reading on a phone

- **Judge at the embedded size**: the film's width on a portrait phone, in physical pixels, is about 1179 × (film width ÷ width of the frame it is published in). Filling the screen width (a landscape film, or a vertical one): ~1179. A 1340×754 card in a 2560×1440 compilation: ~620, the 1920 film scaled ≈ 0.32×. `prompt.md` states the number; sheets use it (`sheet.py --at … --width 620`)
- **Mind the units**: these are physical pixels seen from about 30 cm. A Retina desktop shows an image at "actual size" with 2×2 physical pixels per image pixel, about twice the phone's visual angle, which flatters small text. Look at embedded-size sheets at 1:1 physical pixels (50% zoom on a Retina screen, normal desk distance), which roughly matches the phone
- **Floor for Chinese**: about 16 physical px per character on the phone (~10′ of arc, near the lower limit for reading Chinese), e.g. a 48 px label in a 1920 film on a 620 card. What viewers must read in passing sits well above it; smaller text is texture and must not carry meaning
- **Thin and faint things vanish**: a 2 px line on a 620 card is 0.65 px, 3 px scanlines disappear, white smoke on cream paper barely registers. Whatever carries meaning must survive the embedded size (a bright scrolling band instead of scanlines, cold grey smoke on warm paper)
- Keep text at least 5% from the frame edge; in vertical video leave another 15% at the bottom for the platform's title and buttons; clips embedded in a talking-head episode also have the subtitle zone at the bottom
- One point per screen; the fewer things moving at once the better ("one lead at a time" from the flat-vector card helps every style)
- **Screenshot-and-OCR test** for text viewers will screenshot (a printed prompt, a list): encode like the platform (1080p, 2 Mbps), take the frame, scale it to the screenshot width (1179 for a landscape video on a portrait iPhone), run OCR (macOS Vision: `swift <skill>/tools/ocr.swift frame.png`) and compare without punctuation and spaces. Test every segment, not one still; average 3 encodes (x264 at 2 Mbps wasn't deterministic on an Apple M4) and a few 1–2 px offsets, because errors follow each glyph's sub-pixel position; report errors per 1000 characters, not "all correct". Text at 36 px in a 2560 frame (~17 physical px on the phone) still had about 2 errors per 1000, all look-alike glyphs (白→自, 页→贡), and 40 px didn't remove them

## Encoding

- H.264 4:2:0 halves colour resolution: light small text on saturated red comes out pinkish with a dark-red fringe that the PNG doesn't have; keep strokes there ≥ 10 px and check a zoomed frame of the encoded film
- Where saturated colours meet, 4:2:0 leaves a 1–2 px colour edge that hole scans read as an enclosed slit: look for holes on lossless frames, or ignore enclosed regions under 150 px on the film
- Encoder ringing makes bright streaks 1 px wide and 20–30 px long next to bright points: when counting dots or tips, require at least 3 px in both directions
- After a big change, x264 noise moves 300–500 px by more than 12 levels in the next frame: count a new drawing at more than 2000 px changing by more than 40 levels (`check.py drawings`)
- Colour tags are bt709 for primaries, transfer and matrix (`spec.py` checks). Films rendered before 10-13 19:50 lack the first two; their pixels are identical

## Assets

- Photos and textures: CC0 or public domain (Wikimedia Commons — check each file page's license; NASA public-domain images); record sources in `CREDITS.md`, with each cut piece's file name in its source's row
- No AI-generated human faces; if AI-generated images appear, label AI-generated content where the platform requires it
- No real brand logos; brand names in style demos are invented and searched for collisions first
- Product interfaces match the real product; don't draw features it doesn't have
- **Cutting out objects**: `hyperframes remove-background` uses `u2net_human_seg`, a people-only model (and downloads ~170 MB on first use; a stalled download left a 52 MB `.tmp` in `~/.cache/hyperframes/background-removal/models/`). For objects, threshold colour or brightness to find the subject, keep the right connected components, close the mask (or the border shows gaps), and bake the white border by circular dilation. For prints and engravings, draw polygon masks over an enlarged copy with a grid on it
- **Fetching**: Wikimedia Commons answers 429 on both its API and its image server when asked too fast: batch the queries, wait a few seconds between requests, retry, and send a descriptive User-Agent. USGS pages hung in WebFetch and in plain curl but answered `curl --http2` with browser headers; the Library of Congress and Chronicling America returned 403 to curl, and their copies on Commons worked
- **Old scans as texture**: old newspapers can carry legible text from another era; use body text only, shuffled, mirrored and scaled until unreadable, never headlines, adverts or mastheads

## Reading the mg-styles-15 source

The source is the public repo https://github.com/Vincentwei1021/mg-styles-15; clone it anywhere outside the project, e.g. `git clone --depth 1 https://github.com/Vincentwei1021/mg-styles-15 ~/mg-styles-15`, and read `demos/`. Read it for technique, don't copy it: subject and composition are designed fresh for each clip. Its demos use a different page contract (`window.renderAt(t)` and `window.DEMO`) and their own audio library; translate ideas, not code.

- Files are large (single HTML files up to 80 KB): `grep -n "renderAt\|cues"` to find the entry points, then read only the functions used
- Branches for `V5`, `?v5=1`, `linkAt`, `nolink` were added for a compilation reel; skip them
- Worth reading: `09-bauhaus/audio.py` (one sound per picture event), `19-paperclip/index.html` `cam()` (big-canvas camera), `05-cel-boil/js/engine.js` (hand-drawn brush and boil), `18-hanazi/index.html` (multi-outline caption text, `popOut`), `20-pixel/film.js` (sprites, indexed palette, CRT)
- The repo doesn't include its fonts (list in `assets/fonts/README.md`); to run a demo, add the fonts first or it hangs as described above

## Render speed and the shared machine

- `--workers N`: one browser per worker (pages inside one browser share a compositor and don't render in parallel); 2 when other builders share the machine
- Preview at low resolution and render only a section while adjusting (`--from 3 --to 5 --out check/片段.mp4` — without `--out` it overwrites the film), then render the whole clip; sections joined into one film break the audio at the joins
- Sound-only changes: rerun `audio.py`, then `render.mjs --remux` (copies the video stream, no browser)
- **One GPU-heavy render at a time**: next to a browser render, Blender went from 9–11 to 18–26 s/frame
- Long renders: start them with `nohup` (a background command can be cut off by a tool timeout) in frame ranges you can resume; the `render.sh` that `new.sh --blender` writes does both
