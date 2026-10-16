# Liquid (液态)

Shapes behave like thick liquid: two blobs merge when they get close, stretch into a thread when they part and then snap, get flung, squash on landing, and throw off droplets. Organic, satisfying, high energy.

**Good for**: transitions and openers. This is the hardest style to do well (the test film took three rounds, about 4.5 hours); skip it when time is short.
**Reference films (technique only)**: mg-styles-15 `demos/07-liquid/` (the October 2026 test batch added raymarched liquid metal, stroke-skeleton text, and adaptive sub-frames).

<signature>
- It merges: two blobs that come close join into one, with a smooth rounded neck at the join, never a hard crease.
- It strings: when blobs separate they pull a thread that thins until it snaps, and both ends recoil a little.
- It is flung: fast out, slow to stop, never constant speed; it squashes on landing and slowly recovers.
- It has followers: a few small droplets trail the main body, arriving 2–3 frames late.
- It has thickness: surface highlights and rim reflections make it read as liquid with volume, not a flat blob.
</signature>

<style>
- Build: a WebGL fragment shader that blends shapes into one with a smooth signed distance field; normals from the field's gradient, a specular highlight, and rim light. 2.5D (the field read as height) suits flat pours and blobs; to land on a tabletop with a reflection and a contact shadow, raymarch in true 3D.
- Blending: a cubic smooth-min (the quadratic one is only C1, and a mirror finish shows the curvature break as a line). Two bodies that meet always go through smin, never plain min (a hard seam). Within one stroke, compute one exact distance to the whole curve: smin between its own segments bulges at every joint and turns the highlight into a dashed line. Overlapping smins add their bulges and can bridge gaps you meant to keep. Don't skip evaluation by bounding sphere with a flat ellipsoid's approximate distance (it underestimates and cuts arc-shaped seams).
- Merging: smin joins two blobs once the gap is under about k/3, before they touch, so an approach that eases to a stop forms the neck several frames before its sound, like a crease. Rush in, stop with a gap, and jump the last bit on the cue.
- Threads: a waisted tube or segmented smin, never two segments joined with min (a hard kink at the midpoint). A neck lasts ≥ 4–5 frames at 30 fps; 1–2 frames read as nothing.
- Text as liquid: bold Chinese strokes melt into one blob in a distance field. Build a stroke-skeleton field (one round-cone tube per stroke), which also lets droplets run along the strokes, and save one structural stroke to land on the climax, so the character completes then.
- Metal: a large softbox with an internal gradient and a clipping budget (among metal pixels, V > 80, those at ≥ 250 stay ≤ 10%; a plain bright softbox clipped 45% of the letter face). Sweep with a light bar moving above the table, not a light at infinity (its highlight only slides across one stroke's cross-section). Blur reflections: 1 px bright edges turn to moiré under sub-frames. No radial function of |p − c| about a shape's center (its cusp shows as petals or a keyhole on chrome); environment lines at least 0.08 rad wide, soft-edged, faded near the zenith (thinner ones alias, stripe under blur, and become dark stars on small domes).
- Motion blur: adaptive sub-frames in the page (techniques.md), with displacement measured on squash, reflections, and thread tips as well as centers. First make every move continuous within the shutter, easing sudden changes over 2–4 frames: no number of sub-frames smooths a one-frame squash.
- Beat skeleton: one drop falls and splashes → blobs gather, string, and snap → a big wave sweeps the frame as a transition → the liquid gathers into the title → one last drop falls and ripples.
- Sound: bed `future_bass` with `prog='Imaj7 V vi7 IVmaj7'` (the default progression starts on IVmaj7, so the ending doesn't resolve). Its drop lifts mostly through the 808: accent a mid-range chord on the drop's first beat and lower the kick with `levels=`. `drip`, `gloop`, `splash`, `bubbles`; give each merge sound a short transient, since a low `gloop` starts too softly to sync.
- Avoid: hard edges, constant-speed motion, flat fills without highlights, liquid that appears from nowhere, plain min anywhere two bodies touch.
</style>

<check>
- Zoom into joins and edges, with 2× crops of the 10% of frames that change most, for aliasing, creases, stacked contours, and dashed highlights.
- In filmstrips, the snap of a thread shows a recoil, and every neck lasts ≥ 4 frames.
- Metal clipping ≤ 10% (pixels at ≥ 250 among those above 80) at the climax and in the hold.
- Text stays readable while merged with the liquid, at the phone width set in prompt.md.
- No black frames or black patches (a lost WebGL context renders black; check the near-black share of every frame, which spec.py's black-frame test misses for patches).
</check>
