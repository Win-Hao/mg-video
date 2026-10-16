"""Music beds: a short arranged backing track in one of ten styles.

The grid is anchored so that a bar line falls exactly on `drop` (the picture's climax). Sections:
intro [0, build) → build [build, drop) → drop [drop, outro) → outro [outro, end]. Chords count from the drop bar:
bar k (k = 0 at the drop, negative before it) plays chord k mod n of the progression, so the drop and the ending play
its first chord (start `prog` on the tonic). At the outro that chord rings to the end (end='hold').

    m = Mix(6.0)
    form = music.bed(m, 'techno', drop=3.5, outro=5.0)    # returns the form (bpm, beat, bar, drop, ...)
    form = music.bed(m, 'explainer', drop=3.5, levels={'kick': -6, 'arp': -99}, pickup=True, end='pulse')

For a custom arrangement, lay parts on a Form yourself with pattern(), bassline(), chords(), arp(), crash(), vinyl()
(the helpers bed() uses; LEVEL holds their default dB per role).
"""
import numpy as np

from . import inst, sfx
from .core import Sound, bpf, n_of, noise
from .theory import midi, progression

STYLES = {
    'explainer':   dict(bpm=112, key='D', mode='major', prog='Imaj7 V vi7 IVmaj7'),
    'pop':         dict(bpm=122, key='C', mode='major', prog='I V vi IV'),
    'techno':      dict(bpm=124, key='A', mode='minor', prog='i7 i7 iv7 i7'),
    'ambient':     dict(bpm=78, key='E', mode='major', prog='Imaj7 vi7 IVmaj7 V'),
    'lofi':        dict(bpm=84, key='F', mode='major', prog='ii7 V7 Imaj7 vi7', swing=0.58),
    'variety':     dict(bpm=128, key='F', mode='major', prog='I vi ii V'),
    'chiptune':    dict(bpm=150, key='C', mode='major', prog='I V vi IV'),
    'synthwave':   dict(bpm=100, key='A', mode='minor', prog='i VI III VII'),
    'darksynth':   dict(bpm=110, key='D', mode='phrygian', prog='i II i VII'),
    'future_bass': dict(bpm=150, key='D', mode='major', prog='IVmaj7 V iii7 vi7'),
}


# levels= keys → the roles they set (a role name such as 'clap' or 'shaker' also works on its own)
LAYERS = {'kick': ('kick',), 'snare': ('snare', 'clap', 'rim'), 'hats': ('hat', 'shaker'), 'bass': ('bass',),
          'chords': ('chords', 'lead'), 'pad': ('pad',), 'arp': ('arp',), 'riser': ('fx',), 'crash': ('crash',),
          'vinyl': ('vinyl',), 'end': ('end',)}
ENDINGS = ('hold', 'pulse', 'stop')


class Form:
    def __init__(self, duration, bpm, drop, outro, chords, swing=0.5, levels=None, pickup=False):
        """levels: {layer: dB} added to the default level of each layer (LAYERS; -99 mutes it).
        pickup: sustained chords and bass notes that began before t0 (the grid counts back from the drop, so the first
        bar line is rarely at 0) still sound from t0 for the rest of their length, instead of leaving it empty."""
        self.duration, self.bpm = duration, bpm
        self.beat = 60.0 / bpm
        self.bar = 4 * self.beat
        self.drop = drop if drop is not None else round(duration * 0.42 / self.bar) * self.bar
        self.drop = min(max(self.drop, 0.0), duration)
        self.outro = outro if outro is not None else max(self.drop, duration - max(1.2, 2 * self.beat))
        self.build = max(0.0, self.drop - self.bar)
        self.chords, self.swing = chords, swing
        self.offsets = _offsets(levels)
        self.pickup, self.ending = bool(pickup), 'hold'

    def level(self, role):
        """dB a part in `role` is placed at: LEVEL[role] plus this form's levels= offset."""
        return _LEVEL[role] + self.offsets.get(role, 0)

    def t(self, bar, step):
        """Time of 16th-note `step` in bar index `bar` (bar 0 starts at the drop). Odd 8ths are swung."""
        s = step * self.beat / 4
        if self.swing != 0.5 and step % 4 == 2:
            s += (self.swing - 0.5) * self.beat
        return self.drop + bar * self.bar + s

    def bars(self, t0, t1):
        k0 = int(np.floor((t0 - self.drop) / self.bar))
        k1 = int(np.ceil((t1 - self.drop) / self.bar))
        return range(k0, k1)

    def chord(self, bar):
        return self.chords[bar % len(self.chords)]

    def summary(self):
        return dict(bpm=self.bpm, beat=round(self.beat, 4), bar=round(self.bar, 4), build=round(self.build, 3),
                    drop=round(self.drop, 3), outro=round(self.outro, 3), end=self.duration)


_LEVEL = {'kick': -3, 'snare': -8, 'clap': -9, 'hat': -15, 'shaker': -16, 'rim': -14, 'bass': -7, 'pad': -13,
          'chords': -12, 'arp': -13, 'lead': -12, 'fx': -14, 'crash': -16, 'vinyl': -26}
LEVEL = _LEVEL   # public name


def _offsets(levels):
    out = {}
    for k, db in (levels or {}).items():
        roles = LAYERS.get(k) or ((k,) if k in _LEVEL else None)
        if roles is None:
            raise ValueError(f'unknown layer {k!r} in levels; one of {sorted(LAYERS)} or a role in {sorted(_LEVEL)}')
        for r in roles:
            out[r] = out.get(r, 0) + db
    return out


def _lv(f, role):
    return _LEVEL[role] + getattr(f, 'offsets', {}).get(role, 0)


def _muted(f, role):
    return getattr(f, 'offsets', {}).get(role, 0) <= -99


def _vel(c):
    return {'x': 1.0, 'X': 1.0, 'o': 0.6, 'g': 0.3}.get(c, 0.0)


def pattern(m, f, role, make, pat, t0, t1, pan=None):
    """Place `make(vel)` on every non-'.' step of a 16-step pattern string ('x'/'X' full, 'o' 0.6, 'g' 0.3), for bars
    between t0 and t1 (never past the outro). Example: pattern(m, f, 'kick', lambda v: inst.kick('soft', v), 'x.......x.......', f.drop, f.outro)"""
    if _muted(f, role):
        return
    for k in f.bars(t0, t1):
        for i, c in enumerate(pat):
            v = _vel(c)
            t = f.t(k, i * 16 // len(pat))
            if v and t0 - 1e-6 <= t < min(t1, f.outro) - 1e-6:
                m.add(make(v), at=t, gain=_lv(f, role), pan=pan)


def _pickup(f, t, dur, t0, t1, pickup):
    """For a hit at t that is before t0: the length still to sound from t0 when pickup is on, else None."""
    on = f.pickup if pickup is None else pickup
    if on and t < t0 - 1e-6 and t + dur > t0 + f.beat / 2 and t0 < min(t1, f.outro) - 1e-6:
        return t + dur - t0
    return None


def bassline(m, f, kind, pat, t0, t1, octave=2, fifths=False, pickup=None):
    """The chord's root (in `octave`) on every non-'.' step of `pat`, each note held to the next; fifths=True puts the
    fifth on every other note. kind: inst.bass kinds (saw, sub, square, triangle, pluck, grit)."""
    if _muted(f, 'bass'):
        return
    step_len = f.beat / 4
    for k in f.bars(t0, t1):
        root = f.chord(k)[0] % 12 + 12 * (octave + 1)
        hits = [i for i, c in enumerate(pat) if c != '.']
        for j, i in enumerate(hits):
            t = f.t(k, i * 16 // len(pat))
            nxt = hits[j + 1] if j + 1 < len(hits) else len(pat)
            dur = (nxt - i) * (16 // len(pat)) * step_len * 0.9
            note = root + (7 if fifths and j % 2 else 0)
            if not (t0 - 1e-6 <= t < min(t1, f.outro) - 1e-6):
                rest = _pickup(f, t, dur, t0, t1, pickup)
                if rest:
                    m.add(inst.bass(note, rest, kind, _vel(pat[i])), at=t0, gain=_lv(f, 'bass'))
                continue
            m.add(inst.bass(note, dur, kind, _vel(pat[i])), at=t, gain=_lv(f, 'bass'))


def chords(m, f, make, t0, t1, rhythm='x...............', role='chords', octave_shift=0, pickup=None):
    """`make(notes, dur, vel)` on every non-'.' step of `rhythm`, with each bar's chord (Form.chord) and the length
    to the next hit. Example: chords(m, f, lambda ns, d, v: inst.pad(ns, d, 'warm', v), 0, f.outro, role='pad')"""
    if _muted(f, role):
        return
    for k in f.bars(t0, t1):
        notes = [n + 12 * octave_shift for n in f.chord(k)]
        hits = [i for i, c in enumerate(rhythm) if c != '.']
        for j, i in enumerate(hits):
            t = f.t(k, i * 16 // len(rhythm))
            nxt = hits[j + 1] if j + 1 < len(hits) else len(rhythm)
            dur = (nxt - i) * (16 // len(rhythm)) * f.beat / 4
            if not (t0 - 1e-6 <= t < min(t1, f.outro) - 1e-6):
                rest = _pickup(f, t, dur, t0, t1, pickup)
                if rest:
                    m.add(make(notes, rest, _vel(rhythm[i])), at=t0, gain=_lv(f, role))
                continue
            m.add(make(notes, dur, _vel(rhythm[i])), at=t, gain=_lv(f, role))


def arp(m, f, make, t0, t1, div=8, octave_shift=1, role='arp', order=(0, 1, 2, 3, 2, 1), vel=0.8):
    """`make(note, dur, vel)` `div` times a bar, walking the bar's chord in `order`."""
    if _muted(f, role):
        return
    step = 16 // div
    for k in f.bars(t0, t1):
        notes = [n + 12 * octave_shift for n in f.chord(k)]
        for j in range(div):
            t = f.t(k, j * step)
            if t0 - 1e-6 <= t < min(t1, f.outro) - 1e-6:
                nt = notes[order[j % len(order)] % len(notes)]
                m.add(make(nt, step * f.beat / 4, vel * (1.0 if j % 4 == 0 else 0.8)), at=t, gain=_lv(f, role))


def crash(m, at, gain=None, seed=11, bus='music'):
    """A crash cymbal at `at` (gain default: LEVEL['crash']). bus='sfx' keeps it out of the music bus's normalisation."""
    g = _LEVEL['crash'] if gain is None else gain
    if bus == 'music':
        m.add(inst.crash(seed=seed), at=at, gain=g)
    else:
        m.add(inst.crash(seed=seed), at=at, gain=g, bus=bus)


def _crash(m, at, seed=11):   # old name and signature
    crash(m, at, seed=seed)


def vinyl(m, f, seed=21):
    """Vinyl crackle over the whole film."""
    if _muted(f, 'vinyl'):
        return
    n = n_of(f.duration)
    g = np.random.default_rng(seed)
    x = bpf(noise(n, seed), 500, 6000) * 0.05
    for _ in range(int(f.duration * 12)):
        i = g.integers(0, n - 200)
        x[i:i + 60] += g.uniform(-1, 1) * np.hanning(60) * 0.6
    m.add(Sound(x), at=0, gain=_lv(f, 'vinyl') + 12)


def _final(m, f, make, kick_kind=None):
    """The outro: the first chord of the progression rings to the end."""
    if f.outro >= f.duration - 0.05 or _muted(f, 'end'):
        return
    notes = f.chords[0]
    end = getattr(f, 'offsets', {}).get('end', 0)
    # The ending resolves; it must not be louder than the drop (the picture's climax is at the drop).
    m.add(make(notes, f.duration - f.outro + 0.5, 1.0), at=f.outro, gain=_LEVEL['chords'] - 6 + end)
    if kick_kind:
        m.add(inst.kick(kick_kind, 0.6), at=f.outro, gain=_LEVEL['kick'] - 4 + end)


def _pulse(m, f, make, div=8, octave_shift=1, order=(0, 1, 2, 3, 2, 1), pat=None):
    """end='pulse': a light pulse under the held chord until the end, fading: the style's arpeggio on the first chord
    (make(note, dur, vel)), or with `pat` a drum pattern (make(vel))."""
    if f.outro >= f.duration - 0.05 or _muted(f, 'end'):
        return
    span, end = f.duration - f.outro, getattr(f, 'offsets', {}).get('end', 0)
    notes = [n + 12 * octave_shift for n in f.chords[0]]
    steps = [(i, _vel(c)) for i, c in enumerate(pat) if c != '.'] if pat else [(i * 16 // div, 0.0) for i in range(div)]
    j = 0
    for k in f.bars(f.outro, f.duration):
        for i, v in steps:
            t = f.t(k, i)
            if not (f.outro - 1e-6 <= t < f.duration - 0.05):
                continue
            fade = 1 - 0.65 * (t - f.outro) / span
            if pat:
                m.add(make(v * fade), at=t, gain=_LEVEL['hat'] + end)
            else:
                nt = notes[order[j % len(order)] % len(notes)]
                m.add(make(nt, 16 // div * f.beat / 4, (1.0 if j % 4 == 0 else 0.75) * fade), at=t, gain=_LEVEL['arp'] - 3 + end)
            j += 1


def _ending(m, f, parts, pulse=None):
    """The end hold, by f.ending: 'hold' rings the first chord from the outro (parts: (make, kick_kind) pairs);
    'pulse' adds a light, fading pulse (a callable); 'stop' places nothing, so the groove stops at the outro."""
    if f.ending == 'stop':
        return
    for make, kick in parts:
        _final(m, f, make, kick)
    if f.ending == 'pulse' and pulse is not None:
        pulse()


_pattern, _bassline, _chords, _arp, _vinyl = pattern, bassline, chords, arp, vinyl   # old names


# ---------------------------------------------------------------- styles
def _explainer(m, f, flavor):
    D, O, E = f.drop, f.outro, f.duration
    pad = lambda ns, d, v: inst.pad(ns, d, 'warm', v * 0.7)
    marimba = lambda n, d, v: inst.mallet(n, d, 'marimba', v)
    chords(m, f, pad, 0, O, role='pad')
    arp(m, f, marimba, 0, O, div=8, octave_shift=1)
    pattern(m, f, 'shaker', lambda v: inst.shaker(v), 'xoxoxoxoxoxoxoxo', f.build, O)
    pattern(m, f, 'kick', lambda v: inst.kick('soft', v), 'x.......x.......', D, O)
    pattern(m, f, 'rim', lambda v: inst.rim(v), '....x.......x...', D, O)
    bassline(m, f, 'sub', 'x...x...x...x...', D, O)
    _ending(m, f, [(lambda ns, d, v: inst.mallet(ns[0] + 12, d, 'vibes', v), 'soft'),
                   (lambda ns, d, v: inst.pad(ns, d, 'warm', 0.7), None)],
            lambda: _pulse(m, f, marimba, div=8))


def _riser(m, f, at):
    if f.drop > 0.6 and not _muted(f, 'fx'):
        m.add(sfx.riser(min(f.drop - 0.05, f.bar)), at=at, gain=_lv(f, 'fx'))


def _crash_on_drop(m, f):
    if not _muted(f, 'crash'):
        crash(m, f.drop, gain=_lv(f, 'crash'))


def _pop(m, f, flavor):
    D, O = f.drop, f.outro
    chords(m, f, lambda ns, d, v: inst.pad(ns, d, 'warm', 0.6), 0, D, role='pad')
    chords(m, f, lambda ns, d, v: Sound(sum(inst.pluck(n + 12, d, v).data for n in ns) / 2), 0, O, 'x..x..x...x..x..')
    pattern(m, f, 'hat', lambda v: inst.hat(False, v), 'x.x.x.x.x.x.x.x.', f.build, O)
    pattern(m, f, 'kick', lambda v: inst.kick('punchy', v), 'x...x...x...x...', D, O)
    pattern(m, f, 'clap', lambda v: inst.clap(v), '....x.......x...', D, O)
    bassline(m, f, 'saw', 'x.x.x.x.x.x.x.x.', D, O)
    chords(m, f, lambda ns, d, v: inst.supersaw(ns, d, v), D, O, role='pad')
    _riser(m, f, f.drop)
    _crash_on_drop(m, f)
    _ending(m, f, [(lambda ns, d, v: inst.supersaw(ns, d, 0.8), 'punchy')],
            lambda: _pulse(m, f, lambda n, d, v: inst.pluck(n, d * 1.5, v, 1.5), div=8))


def _techno(m, f, flavor):
    D, O = f.drop, f.outro
    pattern(m, f, 'hat', lambda v: inst.hat(False, v), '..x...x...x...x.', 0, O)
    pattern(m, f, 'kick', lambda v: inst.kick('techno', v), 'x...x...x...x...', f.build, O)
    pattern(m, f, 'clap', lambda v: inst.clap(v * 0.7), '....x.......x...', D, O)
    bassline(m, f, 'sub', '..x...x...x...x.', D, O)
    chords(m, f, lambda ns, d, v: inst.stab(ns, 0.18, 'dub', v), 0, O, '...x.....x....x.', pickup=False)
    _ending(m, f, [(lambda ns, d, v: inst.stab(ns, 0.6, 'dub', 1.0), 'techno'),
                   (lambda ns, d, v: inst.pad(ns, d, 'dark', 0.6), None)],
            lambda: _pulse(m, f, lambda v: inst.hat(False, v), pat='..x...x...x...x.'))


def _ambient(m, f, flavor):
    D, O = f.drop, f.outro
    chords(m, f, lambda ns, d, v: inst.pad(ns, d + f.beat, 'glass' if flavor == 'glass' else 'warm', 0.8), 0, O, role='pad')
    if flavor == 'piano':
        keys, octave = (lambda n, d, v: inst.piano(n, d * 2, v * 0.8)), 1
    else:
        keys, octave = (lambda n, d, v: inst.mallet(n, d * 3, 'glock', v * 0.6)), 2
    arp(m, f, keys, 0, O, div=4, octave_shift=octave, order=(0, 2, 1, 3))
    if flavor == 'product':
        pattern(m, f, 'kick', lambda v: inst.kick('soft', v), 'x.......x.......', D, O)
        pattern(m, f, 'shaker', lambda v: inst.shaker(v * 0.7), '..x...x...x...x.', D, O)
    _ending(m, f, [(lambda ns, d, v: inst.pad(ns, d, 'glass' if flavor == 'glass' else 'warm', 0.9), None),
                   (lambda ns, d, v: inst.mallet(ns[0] + 24, d, 'bell', 0.6), None)],
            lambda: _pulse(m, f, keys, div=4, octave_shift=octave, order=(0, 2, 1, 3)))


def _lofi(m, f, flavor, keys='epiano'):
    D, O = f.drop, f.outro
    play = inst.piano if keys == 'piano' else inst.epiano
    vinyl(m, f)
    chords(m, f, lambda ns, d, v: Sound(sum(play(n + 12, d, v * 0.8).data for n in ns) / 2), 0, O, 'x.....x.........')
    kick_pat = 'x.....x...x.....' if flavor == 'boombap' else 'x.......x.......'
    pattern(m, f, 'kick', lambda v: inst.kick('boombap', v), kick_pat, D, O)
    pattern(m, f, 'snare', lambda v: inst.snare('lofi', v), '....x.......x...', D, O)
    pattern(m, f, 'hat', lambda v: inst.hat(False, v * 0.8), 'x.o.x.o.x.o.x.o.', f.build, O)
    bassline(m, f, 'sub', 'x.....x...x.....', D, O)
    _ending(m, f, [(lambda ns, d, v: Sound(sum(play(n + 12, d, 0.8).data for n in ns) / 2), None)],
            lambda: _pulse(m, f, lambda v: inst.hat(False, v * 0.8), pat='x.o.x.o.x.o.x.o.'))


def _variety(m, f, flavor):
    D, O = f.drop, f.outro
    make = (lambda n, d, v: inst.mallet(n, d, 'kalimba', v)) if flavor == 'cute' else (lambda n, d, v: inst.pluck(n, d * 0.6, v, 1.4))
    glock = lambda n, d, v: inst.mallet(n, d * 2, 'glock', v * 0.5)
    chords(m, f, lambda ns, d, v: Sound(sum(make(n + 12, d, v).data for n in ns) / 2), 0, O, '..x...x...x...x.')
    pattern(m, f, 'kick', lambda v: inst.kick('punchy', v), 'x.......x.......', D, O)
    pattern(m, f, 'clap', lambda v: inst.clap(v), '....x.......x...', D, O)
    pattern(m, f, 'shaker', lambda v: inst.shaker(v), 'xoxoxoxoxoxoxoxo', f.build, O)
    bassline(m, f, 'pluck', 'x..x..x.x..x..x.', 0, O, fifths=True)
    arp(m, f, glock, D, O, div=4, octave_shift=2)
    _ending(m, f, [(lambda ns, d, v: Sound(sum(inst.mallet(n + 12, d, 'glock', 0.8).data for n in ns) / 2), 'punchy')],
            lambda: _pulse(m, f, glock, div=4, octave_shift=2))


def _chiptune(m, f, flavor):
    D, O = f.drop, f.outro
    chip = lambda n, d, v: inst.lead(n, d * 0.9, 'chip', v)
    arp(m, f, chip, 0, O, div=16, octave_shift=1, order=(0, 1, 2, 3))
    bassline(m, f, 'triangle', 'x.x.x.x.x.x.x.x.', 0, O, fifths=True)
    pattern(m, f, 'kick', lambda v: inst.kick('chip', v), 'x.......x.......', D, O)
    pattern(m, f, 'snare', lambda v: inst.snare('chip', v), '....x.......x...', D, O)
    pattern(m, f, 'hat', lambda v: inst.chip_noise(0.04, v * 0.6), 'x.x.x.x.x.x.x.x.', f.build, O)
    _ending(m, f, [(lambda ns, d, v: Sound(sum(inst.lead(n + 12, d, 'chip', 0.7).data for n in ns) / 2), 'chip')],
            lambda: _pulse(m, f, chip, div=8, order=(0, 1, 2, 3)))


def _synthwave(m, f, flavor):
    D, O = f.drop, f.outro
    pluck = lambda n, d, v: inst.pluck(n, d * 1.5, v, 1.5)
    chords(m, f, lambda ns, d, v: inst.pad(ns, d, '80s', 0.8), 0, O, role='pad')
    arp(m, f, pluck, 0, O, div=16, octave_shift=1, order=(0, 1, 2, 1))
    pattern(m, f, 'kick', lambda v: inst.kick('punchy', v), 'x.......x.......', D, O)
    pattern(m, f, 'snare', lambda v: inst.snare('gated', v), '....x.......x...', D, O)
    pattern(m, f, 'hat', lambda v: inst.hat(False, v * 0.7), 'x.x.x.x.x.x.x.x.', f.build, O)
    bassline(m, f, 'saw', 'x.x.x.x.x.x.x.x.', D, O)
    _riser(m, f, f.drop)
    _crash_on_drop(m, f)
    _ending(m, f, [(lambda ns, d, v: inst.pad(ns, d, '80s', 1.0), 'punchy')],
            lambda: _pulse(m, f, pluck, div=16, order=(0, 1, 2, 1)))


def _darksynth(m, f, flavor):
    D, O = f.drop, f.outro
    square = lambda n, d, v: inst.lead(n, d * 0.8, 'square', v * 0.7)
    chords(m, f, lambda ns, d, v: inst.pad(ns, d, 'dark', 0.9), 0, O, role='pad')
    arp(m, f, square, 0, O, div=8, octave_shift=1, order=(0, 0, 2, 0))
    pattern(m, f, 'kick', lambda v: inst.kick('techno', v), 'x...x...x...x...', D, O)
    pattern(m, f, 'snare', lambda v: inst.snare('tight', v), '....x.......x...', D, O)
    bassline(m, f, 'grit', 'xxxxxxxxxxxxxxxx', f.build, O, octave=1)
    _ending(m, f, [(lambda ns, d, v: inst.pad(ns, d, 'dark', 1.0), 'techno')],
            lambda: _pulse(m, f, square, div=8, order=(0, 0, 2, 0)))


def _future_bass(m, f, flavor):
    D, O = f.drop, f.outro
    pluck = lambda n, d, v: inst.pluck(n, d * 1.2, v, 1.6)
    chords(m, f, lambda ns, d, v: inst.pad(ns, d, 'warm', 0.6), 0, D, role='pad')
    arp(m, f, pluck, 0, O, div=8, octave_shift=1, order=(0, 2, 3, 1))
    chords(m, f, lambda ns, d, v: inst.supersaw(ns, d * 0.7, v), D, O, 'x.x.x.x.x.x.x.x.', role='pad')   # chopped
    pattern(m, f, 'kick', lambda v: inst.kick('808', v), 'x.........x.....', D, O)
    pattern(m, f, 'snare', lambda v: inst.snare('tight', v), '........x.......', D, O)
    pattern(m, f, 'hat', lambda v: inst.hat(False, v * 0.8), 'x.x.x.x.x.x.x.x.', D, O)
    if f.drop > 0.6:
        _riser(m, f, f.drop - f.beat / 2)
        m.mute(f.drop - f.beat / 2, f.beat / 2 - 0.01)   # the classic gap right before the drop
    _ending(m, f, [(lambda ns, d, v: inst.supersaw(ns, d, 0.8), '808')],
            lambda: _pulse(m, f, pluck, div=8, order=(0, 2, 3, 1)))


_BUILDERS = {'explainer': _explainer, 'pop': _pop, 'techno': _techno, 'ambient': _ambient, 'lofi': _lofi,
             'variety': _variety, 'chiptune': _chiptune, 'synthwave': _synthwave, 'darksynth': _darksynth,
             'future_bass': _future_bass}


def bed(mix, style, drop=None, outro=None, bpm=None, key=None, prog=None, flavor=None, levels=None, pickup=False,
        end='hold', **opts):
    """Lay a backing track for `style` onto `mix`. Returns the Form (bpm, beat, bar, build/drop/outro times).
    flavor: ambient → 'glass' | 'piano' | 'product';  lofi → 'chill' | 'boombap' (and keys='piano'|'epiano');
            variety → 'bouncy' | 'cute'.
    levels: dB per layer, added to the bed's own balance (-99 mutes): kick, snare (with clap, rim), hats (with shaker),
            bass, chords, pad, arp, riser, crash, vinyl, end (the ending). The music bus is normalised afterwards, so
            turning one layer down brings the others up.
    pickup: sound chords and bass from 0 even when the first bar line comes later (see Form).
    end: 'hold' the first chord rings from the outro; 'pulse' it rings under a light, fading pulse (the style's
         arpeggio, or hats); 'stop' nothing from the outro on (bring your own ending, or let the effects carry it)."""
    if style not in STYLES:
        raise ValueError(f'unknown style {style!r}; one of {sorted(STYLES)}')
    if end not in ENDINGS:
        raise ValueError(f'unknown end {end!r}; one of {ENDINGS}')
    s = dict(STYLES[style])
    prog_chords = progression(prog or s['prog'], key or s['key'], s['mode'], octave=3)
    f = Form(mix.duration, bpm or s['bpm'], drop, outro, prog_chords, s.get('swing', 0.5), levels=levels, pickup=pickup)
    f.ending = end
    if style == 'lofi':
        _lofi(mix, f, flavor, opts.get('keys', 'epiano'))
    else:
        _BUILDERS[style](mix, f, flavor)
    mix.form = f
    return f
