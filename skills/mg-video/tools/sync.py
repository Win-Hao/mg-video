"""Picture/sound alignment: for each sound in cues.json, the audio onset nearest to its time and how many milliseconds
it is off.
  ~/.venvs/mg-video/bin/python -I sync.py 成片.mp4 cues.json [--tol 40] [--window 100] [--stems]
Works on the film or on out/audio.wav. Onset detection is accurate to about ±3 ms (calibrated 10-07).
Sounds: every event with "sfx" (a name, or a list of layers {"name", "args", …} that may override the event's keys),
once at its "t" or at each of its "times" for repeated hits (layers at the same time count once); the "motion" list
(whooshes, risers, swells) is played but not checked.
Anything beyond --tol (default 40 ms, a bit more than one frame at 30 fps) is flagged; an effect one frame early
(-33 ms) still reads as on the hit. No onset within --window ms (default 100) is reported as "masked": a louder
neighbour (named) buries it, or it is missing; the nearest onset is shown but not matched. Sounds in the first 0.1 s
can't be measured reliably and are only shown.
--stems measures on out/stems/sfx.wav (beside cues.json or the film) when it exists: a four-on-the-floor bed lands a
kick on every beat, so a missing hit still reads 0 ms on the mix.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mgsound import analyze

ap = argparse.ArgumentParser()
ap.add_argument('media'); ap.add_argument('cues')
ap.add_argument('--tol', type=float, default=40, help='allowed error in ms')
ap.add_argument('--window', type=float, default=100, help='search window in ms; no onset inside it reads as masked')
ap.add_argument('--stems', action='store_true', help='measure on out/stems/sfx.wav when it exists')
a = ap.parse_args()

cues = json.load(open(a.cues, encoding='utf-8'))
sounds = []          # (time, label): one per distinct time of an event; layers of one hit count once
for e in cues.get('events', []):
    s = e.get('sfx')
    if not s:
        continue
    layers = [e] if isinstance(s, str) else [dict(e, **x) for x in s]      # a layer may override "t" or "times"
    ts = sorted({round(float(t), 4) for l in layers for t in (l.get('times') or [l['t']])})
    name = str(e.get('id', s if isinstance(s, str) else s[0].get('name', '')))
    sounds += [(t, f'{name}#{k + 1}' if len(ts) > 1 else name) for k, t in enumerate(ts)]
skipped = len(cues.get('motion') or [])
if not sounds:
    sys.exit('no sounds with "sfx" in cues.json; nothing to check')
sounds.sort()

src = a.media
if a.stems:
    for d in (os.path.dirname(os.path.abspath(a.cues)), os.path.dirname(os.path.abspath(a.media))):
        for p in (os.path.join(d, 'out', 'stems', 'sfx.wav'), os.path.join(d, 'stems', 'sfx.wav')):
            if os.path.exists(p) and src == a.media:
                src = p
    print(f'measuring on {src}' if src != a.media else 'no out/stems/sfx.wav found: measuring the mix')
on = analyze.onsets(analyze.load(src))
off = masked = 0
for t, name in sounds:
    if on.size == 0:
        print(f'  {t:6.3f}s  {name:16s} no onset in the whole file'); masked += 1; continue
    k = int(np.argmin(np.abs(on - t)))
    ms = (on[k] - t) * 1000
    if t < 0.1:
        print(f'  {t:6.3f}s  {name:16s} {ms:+6.0f}ms  (first 0.1 s: not measurable, check the waveform)'); continue
    if abs(ms) > a.window:
        near = [n for u, n in sounds if abs(u - on[k]) * 1000 <= a.tol]
        print(f'  {t:6.3f}s  {name:16s} masked   no onset within ±{a.window:g} ms; nearest {on[k]:.3f}s ({ms:+.0f} ms, '
              + (f'"{near[0]}"' if near else 'not a cue: the bed?') + ') — louder there, or the hit is missing'); masked += 1
        continue
    flag = '' if abs(ms) <= a.tol else '  <- off'
    off += bool(flag)
    print(f'  {t:6.3f}s  {name:16s} {ms:+6.0f}ms{flag}')
tail = f'; {skipped} motion sounds not checked' if skipped else ''
if off or masked:
    print(f'{len(sounds)} sounds: {off} beyond ±{a.tol:g} ms, {masked} masked{tail}')
else:
    print(f'{len(sounds)} sounds, all within ±{a.tol:g} ms{tail}')
sys.exit(1 if off or masked else 0)
