"""Music and sound effects. Reads cues.json (the same beat sheet the picture reads) and writes out/audio.wav
(-14 LUFS, true peak ≤ -1.5 dBTP so it stays under -1 after AAC) plus out/stems/music.wav and out/stems/sfx.wav.
Run: ~/.venvs/mg-video/bin/python -I audio.py      API: __SKILL__/references/audio.md

What it reads from cues.json:
  "music"   music.bed() settings: {"bed": "explainer", "drop": 6.5, "outro": 9.0, "bpm": 112.5, ...}; "bed": null = no music
  "events"  picture events with a sound, checked by sync.py: {"id", "t", "sfx": "pop", "args": {...}, "gain": 0, "pan": 0}
            "times": [t1, t2, …] plays it at every time (each is checked); "sfx": [{"name": "impact", "args": {...}}, …]
            layers several sounds (each layer may override the event's keys). No "bus": the music ducks under the hit;
            "bus": "sfx" places it without ducking (dense small hits); "bus": "music" mixes it into the bed, which is
            loudness-normalised as a whole, so a loud accent there pulls the whole bed down
  "motion"  whooshes, risers, swells, pen strokes (no sharp onset): same keys, sfx bus without ducking, not sync-checked
"""
import json
import os
import sys

sys.path.insert(0, '__SKILL__/tools')
from mgsound import Mix, inst, music, sfx

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'cues.json'), encoding='utf-8'))
CUSTOM = {}   # sounds made in this file, by name, usable in "sfx": CUSTOM['clink_run'] = lambda dur=1.0: <a Sound>


def io2_inv(y):   # inverse of power2.inOut: when the picture, eased with io2, reaches fraction y. For ratchets/counters.
    return (y / 2) ** 0.5 if y < 0.5 else 1 - ((1 - y) / 2) ** 0.5


def place(e, duck):
    """Place every sound of one cues entry; effects take keyword arguments from "args" (sfx.whoosh(dur=0.4, kind='air'))."""
    s = e.get('sfx')
    for l in [] if not s else [dict(e, name=s)] if isinstance(s, str) else [dict(e, **x) for x in s]:
        snd = (CUSTOM.get(l['name']) or getattr(sfx, l['name']))(**l.get('args', {}))
        for t in l.get('times') or [l['t']]:
            if duck and 'bus' not in l:
                m.sfx(snd, at=t, gain=l.get('gain', 0), pan=l.get('pan'))
            else:
                m.add(snd, at=t, gain=l.get('gain', 0), pan=l.get('pan'), bus=l.get('bus', 'sfx'))


m = Mix(C['duration'])
M = {k: v for k, v in (C.get('music') or {}).items() if k != 'note' and not k.startswith('_')}
bed = M.pop('bed', '__RECIPE__')   # the style card's Sound line names the bed
form = music.bed(m, bed, **M) if bed else None
for e in C.get('events', []):
    place(e, duck=True)
for e in C.get('motion', []):
    place(e, duck=False)

# Accents and sustained sounds added by hand go on the sfx bus (m.add puts them on the music bus by default), e.g.
# m.add(inst.stab(['D5', 'F#5', 'A5'], 0.4, 'bright'), at=form.drop, gain=-6, bus='sfx')
# Shape the music so its loudest moment is the picture's climax, e.g.:
# m.music_gain([(0, -6), (0.25, 0), (form.drop, 2), (form.outro, -4)])

m.export(os.path.join(HERE, 'out', 'audio.wav'), stems_dir=os.path.join(HERE, 'out', 'stems'))
if form:
    print(form.summary())
