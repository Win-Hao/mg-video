# mg-video changelog

One line per change: date, file, what changed and why. Builders don't edit `tools/`; whoever changes a shared tool adds a line here and tells any builder who is mid-render.

## 2026-10-13 — October 2026 test batch (all 15 styles built, reviewed and revised end to end)

### Fixed during the batch
- 2026-10-13 tools/sheet.py: `-vsync 0` → `-fps_mode passthrough`; ffmpeg 9 removed `-vsync` and the script errored.
- 2026-10-13 tools/spec.py: `--climax T`: the loudest 0.4 s must land on the climax both full-range and on a simulated phone speaker (two 200 Hz high-passes); prints loudness by second.
- 2026-10-13 tools/render.mjs (19:50): no hang after a page error (browser registered at launch, leftover ffmpeg killed, temp dir removed); `__error` checked after every frame (a lost WebGL context stops the run instead of writing black frames); bt709 primaries/transfer/matrix via `setparams` (ffmpeg 9 ignored the `-color_*` flags; films rendered before this carry the matrix tag only, pixels identical).

### Renderer, template, setup
- 2026-10-13 tools/render.mjs: add --remux: puts out/audio.wav (or --audio) onto the existing film, copying the video stream, no browser, for sound-only changes.
- 2026-10-13 tools/render.mjs: --stills removes the old t*.png stills in its folder before writing (--keep keeps them); stale stills had piled up in check/静帧.
- 2026-10-13 tools/render.mjs: pages may define window.boxes(t); whole-film renders also write out/boxes.json and --boxes writes only it, so measuring scripts read positions instead of copying the camera.
- 2026-10-13 tools/render.mjs: audio is padded and cut to the video's length (apad + -t, not -shortest), so a short WAV no longer truncates the film; boolean flags never take the next argument; __error is also checked before each frame and after the last.
- 2026-10-13 tools/template/index.html: frame-number time helpers (frameOf, at, snap), drawingIndex/drawing/jit for drawings per second, onTwos fixed (switched a frame late at frames 123 and 246), backOut with a set overshoot.
- 2026-10-13 tools/template/index.html: __error set from window errors, rejected promises and webglcontextlost; module imports inside build(); needFonts(specs, text) finds missing glyphs in the on-screen strings; magenta page background; ?layer=text debug layer and a boxes(t) example.
- 2026-10-13 tools/template/cues.json, audio.py: music settings under "music"; per-event args, times, bus and layered sfx; a separate motion list (sfx bus, no ducking, not sync-checked).
- 2026-10-13 tools/new.sh: package.json gets "type": "module"; --blender creates a Blender project; refuses to overwrite an existing index.html, scene.py or cues.json.
- 2026-10-13 tools/template/blender/: new Blender skeleton: scene.py (args after --, Metal setup, Blender 5 layered-action keys, per-frame timing log, atomic frame writes), render.sh (nohup, ranges, resume, test/preview), encode.sh (bt709 setparams, refuses missing frames).
- 2026-10-13 tools/setup.sh: --check dry run; fails before installing when there is no uv and Python < 3.11 (HOMEBREW_NO_AUTO_UPDATE hint) or the venv's Python is too old; reports ffmpeg version (warn before 7), missing drawtext, node, Playwright Chromium and Blender.

### Checks and measuring
- 2026-10-13 tools/measure.py: new; margins (colour mask per frame, or out/boxes.json), curve, colorfrac, overlap; value / limit / margin, flags margins under 10%, PASS/FAIL; decodes once at 960 wide; also holds the shared decode and report helpers that spec.py, check.py and sheet.py import (copy it along with them).
- 2026-10-13 tools/spec.py: accepts a .wav (audio checks only).
- 2026-10-13 tools/spec.py: climax margin measured against everything outside T−0.1…T2 (T2 = --climax-end, else the outro/hold in --cues, else T+1.2); pass at ≥ 1 dB full-range and ≥ 3 dB on the phone (the phone is the real bar; the HUD film passed review at 1.7 dB full-range).
- 2026-10-13 tools/spec.py: prints unweighted RMS and RMS below 120 Hz of the climax against the rest, and the jump from the 1.5 s before the climax (warn under 6 dB).
- 2026-10-13 tools/spec.py: top-5 frame-to-frame changes and the climax's rank (warn when another frame changes more).
- 2026-10-13 tools/spec.py: stillness counted in changed pixels plus signed block means (thin-line films no longer read as static; fades still count as change).
- 2026-10-13 tools/spec.py: end hold: largest move in the last 1.2 s scaled to a 620 px card, warn under 2 px.
- 2026-10-13 tools/spec.py: edge reveal: template magenta in the outer 2 px FAILs; other uniform 2–23 px edge bands that differ from the inside warn.
- 2026-10-13 tools/spec.py: warns unless colour primaries, transfer and matrix are all bt709 (films before 19:50 lack two; metadata only).
- 2026-10-13 tools/spec.py: one video decode for every picture check (blackdetect/freezedetect dropped); re-runs itself with the venv python when numpy is missing.
- 2026-10-13 tools/sync.py: reads the new cues format (times per hit, sfx layers checked once per time, motion list skipped); --stems measures on out/stems/sfx.wav; "masked" when no onset within --window ms (default 100), naming the nearest onset instead of matching it.
- 2026-10-13 tools/sheet.py: --crop, --zoom (nearest neighbour), --safe, --nolabel; labels below the image so stills keep their coordinates; --at defaults to ≤ 4 columns, 1 above 1000 px wide.
- 2026-10-13 tools/sheet.py: --beats cues.json prints change per beat (first-last, max vs first, max step; > 30 levels at 960 wide), beats counted from the drop, climax beat marked.
- 2026-10-13 tools/check.py: new subcommands palette, hues, accents, drawings, flicker; colors totals several files; help and output in English; run with the venv python.

### mgsound
- 2026-10-13 tools/mgsound/sfx.py: coin() and oneup() replaced with original motifs (one FM-bell strike with falling glints; a broken-thirds chip figure); the old ones copied a famous game's coin (B5→E6) and 1-UP (E6 G6 E7 C7 D7 G7) note for note. Optional coin(note=), oneup(transpose=).
- 2026-10-13 tools/mgsound/sfx.py: record_scratch() sync point moved to where it first reaches half its peak (≈21 ms at dur=0.35); it landed 20–27 ms late. Buffer unchanged.
- 2026-10-13 tools/mgsound/sfx.py: new glass(kind='clink'|'cluster', pitch, count, spread, seed), from the 3D film's glass clinks.
- 2026-10-13 tools/mgsound/mix.py: export() prints the master limiter's largest gain reduction and when, the reduction at each cue (cues=; default m.sfx hits + drop/outro) and on the climax (climax=), with a note (not a warning) when the climax loses > 3 dB over its first 0.4 s: 11 of 12 passed films lose 3.4–12.2 dB there; spec.py --climax stays the pass/fail test. Master audio unchanged.
- 2026-10-13 tools/mgsound/mix.py: Mix(music_hpf=Hz | [(t, Hz), …]): high-pass on the music bus before its normalisation.
- 2026-10-13 tools/mgsound/music.py: bed(levels={layer: dB}, pickup=False, end='hold'|'pulse'|'stop'); defaults render as before (14 of the 15 films re-render sample-identical; the collage differs only by the record_scratch fix).
- 2026-10-13 tools/mgsound/music.py: public pattern(), bassline(), chords(), arp(), vinyl(), crash(), LEVEL; underscored names kept as aliases.
- 2026-10-13 tools/mgsound/inst.py: new inst.crash() (the beds' cymbal); inst.bass() raises on a non-integer number (Hz passed by mistake played a wrong note).
- 2026-10-13 tools/mgsound/core.py: new Sound.tail(hold, decay): keeps `hold` s after the sync point, fades to −60 dB over `decay` s, cuts there.
- 2026-10-13 tools/mgsound/theory.py: midi() accepts numpy integers (they raised before).

### Docs
- 2026-10-13 SKILL.md, references/review.md, techniques.md, prompt-template.md, audio.md, styles/*.md (all 15), references/from-code-video/02-像素.md: rewritten with the batch's lessons — no multi-sample blur for films viewers pause on; climax position follows the brief; on twos vs 12 drawings/s at 30 fps; embedded size (a 1340×754 card shows a 1920 film at ~620 px on a phone); the review loop with machine-checkable conditions, priorities and regression tables; 15-3d-material gets the measured Blender flow (lighting numbers marked "first measured, 10-13").

### Known gaps (not done)
- No dedicated checks yet for: dark-ground share (glassmorphism), one-line line width / loose ends / enclosed paper regions / figure–ground contrast, morph intermediate self-intersection and half-morph speed, isometric per-object face light order; no `tools/cutout.py` (white border / torn edge / halftone) and no curated public-domain engraving list for collage. Reviewers wrote one-off scripts for these in each test film's `check/评审-*/` folder; none ship with the skill.
- `sfx.shimmer`'s octave glock layer has always been silent (it passes Hz into `inst.mallet`, read as MIDI); left as is to keep output identical.
