# 3D material (3D 质感)

Real materials and light: soft rubber, jelly, frosted glass, metal; broad soft light and shallow depth of field; objects have weight — they drop, squash, rebound — and fields of small objects ripple together.

**Good for**: openers and brand-style intros. The slowest style by far (the test film took about 6 hours over three rounds, nearly 4 of them GPU time); don't use it for fast-turnaround videos.
**Reference films (technique only)**: mg-styles-15 `demos/04-3d-render/` (Blender scripts in `blender/`; the October 2026 test batch's film split the work into `sim.py`, `scene.py`, `lights.json`, `render.sh`, as below).

<signature>
- Real materials: rubber lets a little light through, glass refracts, metal reflects its surroundings; you can name the material at a glance.
- Soft light: large soft light sources, soft-edged shadows, a seamless studio backdrop.
- Shallow depth of field: out-of-focus things are clearly blurred.
- Weight: dropped objects squash, rebound, and wobble before settling, and push other objects aside on contact.
- Arrays: a field of identical small objects (spheres, pills) rises and falls together like a wave.
- Motion blur on fast moves.
</signature>

<style>
- Build: Blender 5.2.2 LTS, Cycles on the Metal GPU, headless: `blender -b --factory-startup -P scene.py -- <args>`. Start from `bash <skill>/tools/new.sh --blender <dir>` (scene.py with argument parsing, Metal setup, a layered-action keyframe helper, and a per-frame timing log; render.sh with nohup, frame ranges, and resume; encode.sh). Keep three files apart: `sim.py` (numpy, deterministic) writes `out/anim.npz`; `scene.py` builds the scene from nothing and keys every frame; `lights.json` holds lights and look, so relighting doesn't rerun the simulation. EEVEE is faster but renders glass black and opaque.
- Render settings (first measured, 10-13): 24–28 samples, adaptive threshold 0.03, OIDN on the GPU with albedo + normal (prefilter accurate); bounces total 16 / diffuse 3 / glossy 6 / transmission 12 / transparent 8; caustics off; filter glossy 0.6; clamp indirect 4; fixed seed, not animated; persistent data; motion blur shutter 0.5 frame, centered; AgX with the Punchy look; 8-bit PNG. 24 fps reads as film, but the brief's frame rate wins (the test film ran at 30).
- Time on an Apple M4 (10-core GPU, 24 GB), 1920×1080 with ~1,300 glass marbles: 7–11 s a frame, about 50 minutes for 300 frames, rising to 18–26 s when a browser render shares the GPU, so render alone. Test frames at 50% and 16 samples: 1.5–2 s; previews at 40%, 8 samples, no blur: 0.5–1 s. The first frame compiles Metal kernels (169 s), and so does the first frame after a kernel feature is toggled (motion blur, light linking): minutes at 0% CPU, not a hang.
- Order: the simulation and its checks (no GPU) → about 20 test frames at half resolution, checked by script → a low-resolution preview of the critical range → the full render only when everything passes. If two rounds of test frames still miss a condition by more than 10%, stop and report the numbers.
- Encode: ffmpeg 9 copies the PNGs' sRGB transfer tag and `-color_trc` doesn't override it, so tag in the filter chain (encode.sh does): `ffmpeg -framerate 30 -i out/frames/f%04d.png -i out/audio.wav -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=color_trc=bt709:color_primaries=bt709:colorspace=bt709" -c:v libx264 -preset slow -crf 16 -movflags +faststart -c:a aac -b:a 256k -ar 48000 -ac 2 -t 10 成片.mp4`.
- Shadows with transparent objects (first measured settings, 10-13): in an all-glass array a soft shadow can't show as a darker band of glass, because each marble shows what it refracts and reflects (the floor below, the lit subject, the sea around), not the light falling on it; five setups and light angles of 24°, 44°, and 68° all failed. Land the shadow on a visible opaque surface (here the crater floor under the hovering word, lit by a floor-only light keyed on for those frames) and prove it with that light on and off. Light linking that keeps a light off the glass removes both its shadow and its glow; a low grazing back light (19°) turns every marble into a white window highlight and drains the color (colored pixels 13–34% → 2–14%). Color came back (58–70%) with the top-back light's glossy off and transmission on, a separate neutral-grey floor object at albedo 0.30, f/1.8, rubber sheen 0.10, and no steel in the shadow area (a mirror is a bright spot inside a shadow). With a low camera, a front key light's shadow hides behind the subject.
- Pitfalls:
  1. Set light power for the scene's size: the test scene's power overexposed the tabletop by about 4 stops.
  2. Glass lenses every bright light into a white dot that depth of field spreads into fog: turn lights' glossy visibility off (keep transmission on the light that lights the glass) and add a touch of roughness (0.008). Light linking may keep the subject's key and fill off the glass, never the light meant to shadow it.
  3. Steel in a dark room reads as black glass: give it an emission card behind the camera with emission sampling `NONE` (seen in reflections only, no render cost).
  4. With caustics off, glass casts black shadows, and fully transparent shadow rays nearly erase them: let the glass pass about 68% to shadow rays.
  5. Objects waiting off screen still cast shadows: one standing in the backdrop spot's beam swept a shadow across the backdrop as it dropped.
  6. Blender 5 removed `Action.fcurves`: key through action slots, layers, strips, and channelbags (new.sh's helper); `light.data.keyframe_insert('energy', frame=…)` keys light power.
  7. Blender frame f is t = (f − 1)/fps; key from frame 0 to two frames past the end, so motion blur has neighbors at both ends.
  8. AgX turns saturated red into salmon: start from a deeper red.
  9. Simulation: widen the contact search margin and cap speed (fast objects make contacts the pair table missed); test "back on the surface" against max(wave height, floor height), or thrown objects climb the backdrop's curve.
  10. Run long renders under nohup (tool timeouts kill background jobs). After a partial change, find the first changed frame by comparing `anim.npz`, re-render from there, and check the frame differences at the seams.
- Weight in an array: only the impact throws objects. Anything thrown falls under gravity (−9.81 m/s², about 0.1 s from 5 cm) and goes back to its spring only when it is back on the surface; a spring pulling it home looks like floating, and throws anywhere else look like glitches. Keep the subject's identifying parts above the front row (a hidden foot turned PLAY into PIAY).
- Extruded words: the bevel closes counters; offset the outline inward by the full bevel (−1.0 × bevel; −0.5 left the A's counter at 10%) and measure counters after beveling (≥ 15% of the glyph width). M PLUS Rounded 1c Black (OFL) with a 6.5 mm bevel worked in the test film; Sniglet's A and P counters are dots by design.
- Beat skeleton: the array ripples quietly → the subject (a word or icon) drops into the array, squashes, rebounds, pushes its neighbors aside (the first impact is the biggest splash) → the camera slowly pushes in → a second event before the hold (a swell lifting the word) → hold.
- Sound: bed `ambient` with `flavor='glass'` (`product` keeps a kick every half bar after the drop, heard as extra landings once the subject has stopped); `sfx.glass()` (`'clink'`, `'cluster'`), `boing`, `gloop` on contact. `impact('soft')` lives below 200 Hz and loses on a phone: layer a bright 1–4 kHz ring of about 0.4 s and keep tails short; a denser hit, not a sharper one, survives the limiter.
- Avoid: default plastic-looking materials, hard shadows, everything in focus, light-linking glass away from the light that should shadow it, a grazing light across a glass array.
</style>

<check>
- Point to one frame where a soft-edged shadow falls on a visible opaque surface, readable at the phone width set in prompt.md, and prove it with that light on and off (first measured, 10-13: inside the subject's outline projected from the light onto the visible floor, ≤ 0.75 of the floor beside it with the light on, ≥ 0.92 with it off). Shadow lights are soft: area lights ≥ 0.4 m, spot radius ≥ 0.15 m.
- Colored materials stay colored at phone width: `measure.py colorfrac --region <array> --at …` gives colored ≥ 20% and white ≤ 10% at every sample. Locate the subject for any measurement by projecting the simulation or scene data, not by color thresholds (lit amber marbles were taken for the coral word).
- Intersections: no object passes into another (check in the simulation).
- Noise and flicker: `check.py flicker 成片.mp4 --region x,y,w,h` on the backdrop and other still areas; brightness doesn't jump between frames.
- Materials: look at a still and ask "what is this made of?" If you can't answer, it isn't there yet.
</check>
