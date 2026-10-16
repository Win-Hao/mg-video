"""Sound effects. Every function returns a Sound normalised to the same loudness (about -18 dBFS RMS over its
audible part, peak ≤ -1 dBFS), so at gain=0 all effects sit at one level; use `gain` only to express intent
(-6 subtle, +2 hero). The sync point is set per effect: attacks for hits, the pass-by for whooshes,
the end for risers and lock-ons — always pass the picture's event time and let the sync point do the rest.

Names used by the style cards: pop click tick blip ding chime sparkle shimmer swell whoosh swish riser
downlifter impact sub_drop sticker_slap paper pen tape_rip scissors stamp typing boing duang slide_whistle
squeak record_scratch coin jump powerup oneup hud_beep hud_scan hud_data lock_on hud_open hud_alert drip
gloop splash bubbles morph vhs_noise static laser glass

coin and oneup are our own motifs (10-13). Until then they copied a famous game's coin and extra-life sounds note
for note; references/audio.md lists those sequences and how to check a game-like sound against them.
"""
import numpy as np

from .core import (SR, Sound, ad, bell_curve, bpf, decay, drive, hpf, lpf, n_of, noise, reverb, saw, sine,
                   square, sweep, times, tri)
from .theory import hz
from . import inst


def _norm(x, sync=0.0, level=-18.0):
    x = np.atleast_2d(np.asarray(x, dtype=np.float64))
    if x.shape[0] == 1:
        x = np.vstack([x, x])
    mono = np.abs(x).max(axis=0)
    pk = mono.max()
    if pk <= 0:
        return Sound(x, sync)
    loud = x[:, mono > pk * 0.1]
    rms = np.sqrt(np.mean(loud ** 2))
    g = 10 ** (level / 20) / max(rms, 1e-9)
    g = min(g, 10 ** (-1 / 20) / pk)
    return Sound(x * g, sync)


def _note(n):
    return hz(n) if isinstance(n, str) else float(n)


# ---------------------------------------------------------------- UI and small hits
def pop(pitch=1.0, seed=0):
    n = n_of(0.12)
    f = 900 * pitch * (0.55 + 0.45 * decay(n, 0.015))
    x = sine(f, n) * ad(n, 0.0015, 0.03) + hpf(noise(n, seed), 3000) * decay(n, 0.003) * 0.15
    return _norm(x)


def click(kind='soft', seed=0):
    n = n_of(0.05)
    lo, hi, tau = {'soft': (900, 4000, 0.006), 'hard': (1500, 9000, 0.004), 'switch': (2500, 12000, 0.003)}[kind]
    x = bpf(noise(n, seed), lo, hi) * decay(n, tau)
    if kind == 'switch':
        x[n_of(0.018):] += (bpf(noise(n, seed + 1), lo, hi) * decay(n, tau))[:n - n_of(0.018)] * 0.6
    return _norm(x)


def tick(kind='wood'):
    n = n_of(0.06)
    f = {'wood': 1300, 'hi': 3400, 'clock': 2200}[kind]
    x = (sine(f, n) + 0.5 * sine(f * 2.3, n)) * decay(n, 0.008 if kind != 'wood' else 0.014)
    return _norm(x)


def blip(note='A5', wave='sine', dur=0.08, glide=1.0):
    n = n_of(dur + 0.03)
    f = _note(note) * (glide + (1 - glide) * np.clip(times(n) / dur, 0, 1))
    osc = {'sine': sine, 'square': lambda f, n: square(f, n, 0.5) * 0.5, 'tri': tri}[wave]
    return _norm(osc(f, n) * ad(n, 0.002, dur / 2.5))


def ding(note='E6'):
    return _norm(inst.mallet(note, 1.2, 'bell').data)


def chime(notes=('C6', 'E6', 'G6'), spread=0.06):
    n = n_of(2.0 + spread * len(notes))
    x = np.zeros((2, n))
    for i, nt in enumerate(notes):
        s = inst.mallet(nt, 1.5, 'glock').data
        a = n_of(i * spread)
        k = min(s.shape[1], n - a)
        x[:, a:a + k] += s[:, :k]
    return _norm(reverb(x, 'plate', 0.3))


def sparkle(dur=0.8, seed=0, key_notes=('C7', 'E7', 'G7', 'B6', 'D7')):
    g = np.random.default_rng(seed)
    n = n_of(dur + 1.0)
    x = np.zeros((2, n))
    for k in range(int(dur * 14)):
        s = inst.mallet(key_notes[g.integers(len(key_notes))], 0.6, 'glock', vel=g.uniform(0.3, 1)).data
        a = n_of(g.uniform(0, dur))
        side = g.uniform(0.3, 1.0)
        m = min(s.shape[1], n - a)
        x[0, a:a + m] += s[0, :m] * side
        x[1, a:a + m] += s[1, :m] * (1.3 - side)
    return _norm(reverb(x, 'hall', 0.4))


def shimmer(note='E6'):
    """A bright bell hit with a long airy tail; for 'something just appeared' moments."""
    a = inst.mallet(note, 2.0, 'bell').data
    b = inst.mallet(_note(note) * 2, 1.5, 'glock').data * 0.5
    x = np.zeros((2, max(a.shape[1], b.shape[1])))
    x[:, :a.shape[1]] += a
    x[:, :b.shape[1]] += b
    return _norm(reverb(x, 'hall', 0.6))


def swell(dur=0.8, seed=0):
    """Reverse-reverb rise that ends on the hit (sync = end)."""
    n = n_of(dur)
    hit = lpf(noise(n_of(0.04), seed), 6000) * decay(n_of(0.04), 0.01)
    tail = reverb(hit, 'hall', 1.0)[:, :n]          # a reverb tail...
    if tail.shape[1] < n:
        tail = np.pad(tail, ((0, 0), (0, n - tail.shape[1])))
    return _norm(tail[:, ::-1] * np.linspace(0, 1, n), sync=dur)   # ...played backwards rises into the hit


# ---------------------------------------------------------------- motion
def whoosh(dur=0.6, kind='air', direction=1, seed=0):
    """Pass-by: sync is the loudest point (about 60% in). kind: air, swish (short, bright), sci (tonal), heavy."""
    n = n_of(dur)
    peak = 0.6
    env = bell_curve(n, peak, 0.18)
    nz = noise(n, seed)
    lo, hi = {'air': (300, 4000), 'swish': (1200, 9000), 'sci': (400, 3000), 'heavy': (80, 1200)}[kind]
    cut = lo + (hi - lo) * env
    x = sweep(nz, cut, 'low', 2)[0] * env
    if kind == 'sci':
        x = x * 0.6 + sine(220 + 900 * env, n) * env * 0.4
    if kind == 'heavy':
        x = drive(x * 2, 2)
    d = float(np.clip(direction, -1, 1))
    pan = np.linspace(-0.7 * d, 0.7 * d, n)
    a = (pan + 1) * np.pi / 4
    return _norm(np.vstack([x * np.cos(a), x * np.sin(a)]) * np.sqrt(2), sync=dur * peak)


def swish(dur=0.25, direction=1, seed=0):
    return whoosh(dur, 'swish', direction, seed)


def riser(dur=1.5, seed=0):
    """Noise + rising tone that ends on the hit (sync = end)."""
    n = n_of(dur)
    ramp = np.linspace(0, 1, n)
    x = sweep(noise(n, seed), 400 + 9000 * ramp ** 2, 'low')[0] * ramp ** 2
    x = x + saw(150 + 700 * ramp ** 1.5, n) * ramp ** 2 * 0.25
    return _norm(lpf(x, 12000), sync=dur)


def downlifter(dur=1.0, seed=0):
    n = n_of(dur)
    ramp = np.linspace(1, 0, n)
    x = sweep(noise(n, seed), 300 + 8000 * ramp ** 2, 'low')[0] * ramp ** 1.5
    return _norm(x)


def impact(kind='soft', seed=0):
    """Hit on the attack. kind: soft (rounded thud), punch (tight and loud), cinematic (big, with a tail)."""
    n = n_of({'soft': 0.6, 'punch': 0.5, 'cinematic': 3.0}[kind])
    t = times(n)
    f0, f1, tau = {'soft': (120, 45, 0.18), 'punch': (180, 50, 0.16), 'cinematic': (90, 32, 0.9)}[kind]
    body = sine(f1 + (f0 - f1) * np.exp(-t / 0.04), n) * decay(n, tau)
    crack = bpf(noise(n, seed), 600, 8000) * decay(n, {'soft': 0.01, 'punch': 0.02, 'cinematic': 0.08}[kind])
    x = drive(body + crack * (0.3 if kind == 'soft' else 0.6), 1.8)
    if kind == 'cinematic':
        return _norm(reverb(x, 'hall', 0.7))
    return _norm(reverb(x, 'room', 0.25))


def sub_drop(dur=1.0):
    n = n_of(dur)
    return _norm(sine(80 * np.exp(-times(n) / 0.5) + 28, n) * decay(n, dur / 2.5))


# ---------------------------------------------------------------- paper and desk
def sticker_slap(seed=0):
    n = n_of(0.2)
    slap = bpf(noise(n, seed), 500, 7000) * decay(n, 0.018)
    thud = sine(110 * (1 + decay(n, 0.01)), n) * decay(n, 0.05) * 0.6
    return _norm(slap + thud)


def paper(kind='rustle', dur=0.5, seed=0):
    n = n_of(dur)
    g = np.random.default_rng(seed)
    grain = np.repeat(g.uniform(0.2, 1, int(dur * 60) + 1), n // (int(dur * 60) + 1) + 1)[:n]
    env = {'rustle': grain * bell_curve(n, 0.5, 0.3), 'flip': bell_curve(n, 0.35, 0.12)}[kind]
    return _norm(bpf(noise(n, seed), 1500, 9000) * env)


def pen(dur=0.6, seed=0):
    """A pen stroke; loudness wobbles like a hand. For lines being drawn on."""
    n = n_of(dur)
    g = np.random.default_rng(seed)
    wob = 0.6 + 0.4 * np.interp(np.arange(n), np.linspace(0, n, 12), g.uniform(0, 1, 12))
    x = bpf(noise(n, seed), 2500, 8000) * wob * ad(n, 0.02, dur)
    return _norm(x * np.clip((dur - times(n)) / 0.04, 0, 1))


def tape_rip(dur=0.35, seed=0):
    n = n_of(dur)
    teeth = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * np.cumsum(np.linspace(60, 140, n)) / SR))
    return _norm(bpf(noise(n, seed), 800, 7000) * teeth * ad(n, 0.01, dur / 2))


def scissors(seed=0):
    n = n_of(0.3)
    x = bpf(noise(n, seed), 2000, 9000) * decay(n, 0.02)
    x[n_of(0.12):] += (bpf(noise(n, seed + 1), 3000, 10000) * decay(n, 0.015))[:n - n_of(0.12)]
    return _norm(x + sine(4200, n) * decay(n, 0.01) * 0.2)


def stamp(seed=0):
    n = n_of(0.35)
    x = sine(85 * (1 + 0.5 * decay(n, 0.01)), n) * decay(n, 0.07) + bpf(noise(n, seed), 300, 3000) * decay(n, 0.02)
    return _norm(reverb(x, 'room', 0.2))


def typing(keys=6, rate=12, seed=0):
    g = np.random.default_rng(seed)
    n = n_of(keys / rate + 0.1)
    x = np.zeros(n)
    for k in range(keys):
        a = n_of(k / rate + g.uniform(-0.01, 0.01) + 0.01)
        c = click('hard', seed + k).data[0] * g.uniform(0.6, 1)
        m = min(len(c), n - a)
        x[a:a + m] += c[:m]
    return _norm(x)


# ---------------------------------------------------------------- cartoon / variety show
def boing(pitch=1.0):
    n = n_of(0.5)
    t = times(n)
    f = (180 + 140 * np.sin(2 * np.pi * 9 * t) * decay(n, 0.25)) * pitch * (1 + t)
    return _norm(sine(f, n) * ad(n, 0.003, 0.18) + tri(f * 2, n) * ad(n, 0.003, 0.1) * 0.2)


def duang(pitch=1.0):
    n = n_of(0.9)
    t = times(n)
    f = 95 * pitch * (1 + 0.04 * np.sin(2 * np.pi * 6 * t))
    x = (saw(f, n) + saw(f * 1.01, n)) * 0.5
    x = sweep(x, 300 + 2500 * decay(n, 0.25), 'low')[0] * ad(n, 0.005, 0.35)
    return _norm(reverb(drive(x, 1.5), 'room', 0.2))


def slide_whistle(up=True, dur=0.5):
    n = n_of(dur)
    r = np.linspace(0, 1, n) if up else np.linspace(1, 0, n)
    f = 500 + 1300 * r ** 1.3
    x = (sine(f, n) + 0.1 * noise(n)) * ad(n, 0.03, dur)
    return _norm(x * np.clip((dur - times(n)) / 0.05, 0, 1))


def squeak(pitch=1.0):
    n = n_of(0.18)
    f = 1800 * pitch * (1 + 0.3 * np.sin(np.pi * times(n) / 0.18))
    return _norm(sine(f, n) * ad(n, 0.01, 0.08))


def record_scratch(dur=0.35, seed=0):
    """Sync = where it first reaches half its peak level (about 21 ms in at dur=0.35): the scratch swells in with the
    hand's speed, so syncing on the buffer start made it land ~20-27 ms late."""
    n = n_of(dur)
    t = times(n)
    speed = np.sin(2 * np.pi * t / dur * 1.5)
    x = bpf(noise(n, seed), 300, 4000) * np.abs(speed) + saw(120 + 300 * np.abs(speed), n) * 0.2 * np.abs(speed)
    x = x * ad(n, 0.005, dur)
    k = n_of(0.005)
    env = np.sqrt(np.convolve(x ** 2, np.ones(k) / k, 'same'))
    return _norm(x, sync=int(np.argmax(env >= 0.5 * env.max())) / SR)


# ---------------------------------------------------------------- 8-bit
def coin(note='C7'):
    """A reward: ONE metallic strike that rings ~0.35 s (an FM bell with bar partials at 2.76x and 5.40x, chirping up
    from 70 cents below in its first 12 ms), then three faint glints that fall (an octave up, then a minor third and a
    tone lower). Long-then-short, one pitch: no short note leaping into a held one."""
    n = n_of(0.6)
    t = times(n)
    f0 = _note(note)
    f = f0 * 2 ** (-0.7 / 12 * np.clip(1 - t / 0.012, 0, 1))
    ph = np.cumsum(f) / SR
    index = 1.1 * np.exp(-t / 0.05) + 0.2                       # bright on the strike, purer as it rings; the carrier stays strongest
    x = np.sin(2 * np.pi * ph + index * np.sin(2 * np.pi * 1.41 * ph)) * ad(n, 0.0015, 0.11)
    x += np.sin(2 * np.pi * 2.76 * ph) * np.exp(-t / 0.05) * 0.3 * (1 - 0.3 * np.sin(2 * np.pi * 14 * t))   # a little spin
    x += np.sin(2 * np.pi * 5.40 * ph) * np.exp(-t / 0.02) * 0.12
    for i, (semi, db) in enumerate(((12, -15), (9, -18), (7, -21))):
        a, k = n_of(0.06 + 0.035 * i), n_of(0.03)
        x[a:a + k] += tri(f0 * 2 ** (semi / 12), k) * ad(k, 0.001, 0.01) * 10 ** (db / 20)
    return _norm(x)


def jump():
    n = n_of(0.22)
    return _norm(square(250 * (1 + 2 * np.linspace(0, 1, n)), n, 0.25) * decay(n, 0.08))


def _chip_seq(notes, step):
    n = n_of(step * len(notes) + 0.05)
    idx = np.minimum(np.arange(n) // n_of(step), len(notes) - 1)
    f = np.array([hz(x) for x in notes])[idx]
    return square(f, n, 0.5), n


def powerup():
    x, n = _chip_seq(['C5', 'E5', 'G5', 'C6', 'E6', 'G6', 'C7'], 0.06)
    return _norm(x * ad(n, 0.005, 0.4))


def oneup(transpose=0):
    """An extra life: a chip figure climbing in broken thirds (A5 C6 B5 D6 C6 E6, 40 ms each), a breath, then D6 into a
    held, vibrato E6. Steps and thirds only, uneven rhythm, ending on a held note approached by step."""
    seq = [('A5', 0.04), ('C6', 0.04), ('B5', 0.04), ('D6', 0.04), ('C6', 0.04), ('E6', 0.04), (None, 0.03),
           ('D6', 0.05), ('E6', 0.26)]
    n = n_of(sum(d for _, d in seq) + 0.12)
    x, a = np.zeros(n), 0
    for i, (nt, d) in enumerate(seq):
        k = n_of(d)
        if nt:
            last = i == len(seq) - 1
            m = k + n_of(0.12) if last else k
            f = hz(nt) * 2 ** (transpose / 12) * (1 + (0.01 * np.sin(2 * np.pi * 7 * times(m)) * np.clip(times(m) / 0.08, 0, 1) if last else 0))
            env = ad(m, 0.002, 0.16) if last else ad(m, 0.002, 0.05) * np.clip((d - times(m)) / 0.004, 0, 1)
            x[a:a + m] += (square(f, m, 0.25) * env)[:n - a]
        a += k
    return _norm(x)


# ---------------------------------------------------------------- HUD / sci-fi
def hud_beep(note='A6'):
    n = n_of(0.09)
    return _norm(square(_note(note), n, 0.5) * ad(n, 0.001, 0.03) * 0.5 + sine(_note(note) * 2, n) * decay(n, 0.02))


def hud_scan(dur=0.8, up=True):
    n = n_of(dur)
    r = np.linspace(0, 1, n) if up else np.linspace(1, 0, n)
    x = sine(800 + 2400 * r, n) * 0.4 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 24 * times(n))))
    return _norm(lpf(x, 6000) * bell_curve(n, 0.5, 0.3))


def hud_data(dur=0.6, seed=0):
    g = np.random.default_rng(seed)
    n = n_of(dur)
    step = n_of(0.025)
    f = np.repeat(g.choice([1200, 1600, 2000, 2400, 3200], n // step + 1), step)[:n]
    return _norm(square(f, n, 0.5) * 0.3 * (np.arange(n) % step < step * 0.6))


def lock_on(dur=0.6):
    """Accelerating beeps that end on the lock (sync = end)."""
    n = n_of(dur + 0.25)
    x = np.zeros(n)
    t, k = 0.0, 0
    while t < dur:
        b = hud_beep(hz('A6') * 2 ** (k / 24)).data[0] * 0.6
        a = n_of(t)
        m = min(len(b), n - a)
        x[a:a + m] += b[:m]
        t += max(0.03, 0.14 * (1 - t / dur))
        k += 1
    lock = square(hz('A7'), n_of(0.25), 0.5) * ad(n_of(0.25), 0.002, 0.08)
    x[n_of(dur):n_of(dur) + len(lock)] += lock[:n - n_of(dur)]
    return _norm(x, sync=dur)


def hud_open():
    n = n_of(0.4)
    return _norm(sine(400 + 1600 * np.linspace(0, 1, n) ** 0.5, n) * ad(n, 0.01, 0.15))


def hud_alert():
    n = n_of(0.6)
    f = np.where((times(n) * 6) % 1 < 0.5, 880, 660)
    return _norm(square(f, n, 0.5) * 0.5 * ad(n, 0.005, 0.5))


def laser():
    n = n_of(0.25)
    return _norm(square(2400 * np.exp(-times(n) / 0.05) + 200, n, 0.3) * decay(n, 0.08))


# ---------------------------------------------------------------- glass
def _clink(f0, seed=0, bright=1.0):
    """One glass touch: three inharmonic partials with millisecond decays and a tiny click (mono)."""
    g = np.random.default_rng(seed)
    n = n_of(0.16)
    x = sum(sine(f0 * r * g.uniform(0.985, 1.015), n) * decay(n, d) * lv
            for r, d, lv in ((1.0, 0.045, 1.0), (2.37, 0.022, 0.55 * bright), (4.11, 0.010, 0.3 * bright)))
    return x + hpf(noise(n, seed), 5000) * decay(n, 0.0015) * 0.5


def glass(kind='clink', pitch=1.0, count=4, spread=0.22, seed=0):
    """Glass touching glass, ringing around 3.1 kHz (x pitch), where a phone speaker is strongest.
    'clink': one touch. 'cluster': `count` touches over `spread` s, the first loudest, panned apart (marbles
    rolling against each other). Sync = the first touch."""
    g = np.random.default_rng(seed)
    if kind == 'clink':
        return _norm(reverb(_clink(3100 * pitch, seed), 'room', 0.15))
    if kind != 'cluster':
        raise ValueError(f"glass kind is 'clink' or 'cluster', not {kind!r}")
    n = n_of(spread + 0.2)
    out = np.zeros((2, n))
    ts = np.sort(np.concatenate([[0.0], g.uniform(0.02, spread, max(0, count - 1))]))
    for k, t0 in enumerate(ts):
        c = _clink(pitch * g.uniform(2600, 3800), seed * 31 + k) * (1.0 if k == 0 else g.uniform(0.35, 0.8))
        a, p = n_of(t0), (g.uniform(-0.6, 0.6) + 1) * np.pi / 4
        m = min(len(c), n - a)
        out[0, a:a + m] += c[:m] * np.cos(p)
        out[1, a:a + m] += c[:m] * np.sin(p)
    return _norm(reverb(out, 'room', 0.18))


# ---------------------------------------------------------------- liquid
def drip(pitch=1.0):
    n = n_of(0.2)
    f = 600 * pitch * (1 + 2.5 * (1 - decay(n, 0.02)))
    return _norm(sine(f, n) * ad(n, 0.002, 0.04))


def gloop(pitch=1.0, dur=0.3):
    n = n_of(dur)
    f = 180 * pitch * (1 + 1.5 * np.sin(np.pi * np.linspace(0, 1, n)))
    x = sine(f, n) * ad(n, 0.01, dur / 3)
    return _norm(sweep(x + 0.2 * saw(f, n) * ad(n, 0.01, dur / 3), 400 + 1500 * np.sin(np.pi * np.linspace(0, 1, n)), 'low')[0])


def splash(size=1.0, seed=0):
    n = n_of(0.8 * size)
    x = bpf(noise(n, seed), 400, 9000) * ad(n, 0.004, 0.18 * size)
    g = np.random.default_rng(seed)
    for _ in range(int(8 * size)):
        d = drip(g.uniform(0.8, 2.0)).data[0] * 0.3
        a = n_of(g.uniform(0.02, 0.4 * size))
        m = min(len(d), n - a)
        x[a:a + m] += d[:m]
    return _norm(x)


def bubbles(dur=1.0, density=10, seed=0):
    g = np.random.default_rng(seed)
    n = n_of(dur + 0.2)
    x = np.zeros(n)
    for _ in range(int(dur * density)):
        d = drip(g.uniform(0.7, 2.5)).data[0] * g.uniform(0.3, 1)
        a = n_of(g.uniform(0, dur))
        m = min(len(d), n - a)
        x[a:a + m] += d[:m]
    return _norm(x)


def morph(dur=0.4, up=True):
    """A pitched, filtered sweep for shapes turning into other shapes."""
    n = n_of(dur)
    r = np.linspace(0, 1, n) if up else np.linspace(1, 0, n)
    f = 200 * 2 ** (2 * r)
    x = (saw(f, n) + saw(f * 1.5, n)) * 0.5
    return _norm(sweep(x, 300 + 4000 * bell_curve(n, 0.6, 0.25), 'low')[0] * bell_curve(n, 0.6, 0.3), sync=dur * 0.6)


# ---------------------------------------------------------------- retro media
def vhs_noise(dur=1.0, seed=0):
    n = n_of(dur)
    hum = sine(60, n) * 0.2 + sine(15734 / 2, n) * 0.02
    return _norm(lpf(noise(n, seed), 5000) * 0.6 + hum, level=-24)


def static(dur=0.5, seed=0):
    n = n_of(dur)
    return _norm(hpf(noise(n, seed), 1000) * ad(n, 0.005, dur), level=-22)
