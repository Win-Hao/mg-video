"""Drums and instruments for the music beds. Each returns a Sound (sync = attack) at its natural level;
the mixer sets the balance. Notes are names ('A3') or MIDI numbers."""
import numpy as np

from .core import SR, Sound, ad, adsr, bpf, decay, drive, hpf, lpf, n_of, noise, saw, sine, square, sweep, times, tri
from .theory import hz

# ---------------------------------------------------------------- drums
_KICKS = {  # start Hz, end Hz, pitch tau, amp tau, click, drive
    'punchy': (160, 50, 0.030, 0.28, 0.25, 1.5),
    'soft': (110, 48, 0.040, 0.20, 0.08, 1.0),
    'techno': (140, 44, 0.025, 0.36, 0.20, 2.2),
    '808': (120, 42, 0.050, 0.90, 0.10, 1.2),
    'boombap': (130, 52, 0.030, 0.22, 0.30, 1.8),
    'chip': (220, 60, 0.020, 0.12, 0.00, 3.0),
}


def kick(kind='punchy', vel=1.0, seed=0):
    f0, f1, ptau, atau, click, dr = _KICKS[kind]
    n = n_of(atau * 5)
    t = times(n)
    f = f1 + (f0 - f1) * np.exp(-t / ptau)
    body = (square(f, n, 0.5) * 0.6 if kind == 'chip' else sine(f, n)) * decay(n, atau)
    clk = hpf(noise(n, seed), 2000) * decay(n, 0.004) * click
    return Sound(drive(body + clk, dr) * vel)


def snare(kind='tight', vel=1.0, seed=1):
    n = n_of(0.5)
    tone = sine(190 * (1 + 0.3 * decay(n, 0.01)), n) * decay(n, 0.06) * 0.5
    nz = noise(n, seed)
    if kind == 'chip':
        x = np.sign(lpf(nz, 6000)) * decay(n, 0.07) * 0.5
    elif kind == 'lofi':
        x = tone * 0.8 + lpf(bpf(nz, 900, 6000), 5000) * decay(n, 0.12) * 0.7
    elif kind == 'gated':  # 80s gated reverb snare
        body = tone + bpf(nz, 700, 9000) * decay(n, 0.2)
        gate = np.clip((0.24 - times(n)) / 0.015, 0, 1)   # close over 15 ms so the cut doesn't click
        x = Sound(body).reverb('plate', 0.9).data[0][:n] * gate
    else:
        x = tone + bpf(nz, 1500, 9000) * decay(n, 0.11 if kind == 'tight' else 0.17)
    return Sound(x * vel)


def clap(vel=1.0, seed=2):
    n = n_of(0.4)
    nz = bpf(noise(n, seed), 900, 3200)
    env = np.zeros(n)
    for k, off in enumerate((0.0, 0.011, 0.022, 0.031)):
        s = n_of(off)
        env[s:] += decay(n - s, 0.006 if k < 3 else 0.12)
    return Sound(nz * env * 0.8 * vel)


def hat(open_=False, vel=1.0, seed=3):
    n = n_of(0.35 if open_ else 0.08)
    metal = sum(square(f, n) for f in (3150, 4510, 5730, 7940)) * 0.15
    x = hpf(noise(n, seed) * 0.7 + metal, 7000) * decay(n, 0.12 if open_ else 0.022)
    return Sound(x * vel * 0.6)


def shaker(vel=1.0, seed=4):
    n = n_of(0.09)
    return Sound(bpf(noise(n, seed), 4500, 11000) * ad(n, 0.012, 0.03) * vel * 0.5)


def rim(vel=1.0):
    n = n_of(0.06)
    return Sound((sine(1750, n) * 0.5 + sine(820, n) * 0.4) * decay(n, 0.012) * vel)


def crash(dur=2.0, vel=1.0, seed=11):
    """Crash cymbal (the one the beds put on the drop)."""
    n = n_of(dur)
    x = hpf(noise(n, seed), 5000) * decay(n, 0.6) + bpf(noise(n, seed + 1), 3000, 8000) * decay(n, 0.2) * 0.5
    return Sound(x * vel)


def chip_noise(dur=0.08, vel=1.0, seed=5):
    n = n_of(dur)
    step = 12   # sample-and-hold makes it sound like an 8-bit noise channel
    nz = np.repeat(noise(n // step + 1, seed), step)[:n]
    return Sound(np.sign(nz) * decay(n, dur / 3) * 0.4 * vel)


# ---------------------------------------------------------------- pitched instruments
def bass(note, dur, kind='saw', vel=1.0):
    """note: a name ('D2') or a MIDI number. A number with a fraction is a frequency passed by mistake
    (hz('D2') = 73.4 would play C#5), so it raises instead of playing a wrong note."""
    if isinstance(note, float) and not note.is_integer():
        raise ValueError(f'inst.bass() got {note!r}: pass a note name or MIDI number, not Hz')
    n = n_of(dur + 0.08)
    f = hz(note)
    env = adsr(n, 0.004, 0.15, 0.6, 0.06, hold=dur)
    if kind == 'sub':
        x = sine(f, n)
    elif kind == 'square':
        x = lpf(square(f, n, 0.5), 1400)
    elif kind == 'triangle':
        x = tri(f, n)
    elif kind == 'pluck':
        x = sweep(saw(f, n), 250 + 2400 * decay(n, 0.07), 'low')[0]
        env = env * decay(n, 0.35)
    elif kind == 'grit':
        x = drive(sweep(saw(f, n) + saw(f * 1.006, n), 300 + 1800 * decay(n, 0.12), 'low')[0], 3)
    else:   # saw
        x = sweep(saw(f, n), 200 + 1600 * decay(n, 0.1), 'low')[0]
    return Sound(x * env * vel * 0.6)


_MALLETS = {   # partial ratios, partial decays (s), partial levels
    'marimba': ([1, 3.93, 9.2], [0.45, 0.10, 0.03], [1, 0.25, 0.08]),
    'vibes': ([1, 3.98, 10.1], [1.6, 0.4, 0.1], [1, 0.2, 0.05]),
    'glock': ([1, 2.76, 5.40, 8.93], [1.2, 0.6, 0.25, 0.1], [1, 0.4, 0.2, 0.1]),
    'kalimba': ([1, 5.93, 12.2], [0.9, 0.12, 0.04], [1, 0.3, 0.1]),
    'bell': ([1, 2.0, 2.76, 5.4], [2.4, 1.2, 0.8, 0.3], [1, 0.5, 0.35, 0.15]),
}


def mallet(note, dur=1.0, kind='marimba', vel=1.0):
    ratios, decays, levels = _MALLETS[kind]
    n = n_of(max(dur, max(decays) * 2.5))
    f = hz(note)
    x = sum(sine(f * r, n) * decay(n, d) * lv for r, d, lv in zip(ratios, decays, levels) if f * r < SR / 2.2)
    x = x * ad(n, 0.002, 10)
    if kind == 'vibes':
        x = x * (1 - 0.25 * (0.5 + 0.5 * np.sin(2 * np.pi * 5.5 * times(n))))
    return Sound(x * vel * 0.5)


def epiano(note, dur, vel=1.0):
    """FM electric piano: a sine carrier whose brightness fades as the note decays."""
    n = n_of(dur + 0.6)
    f = hz(note)
    idx = 1.6 * decay(n, 0.25) + 0.2
    mod = sine(f, n) * idx
    car = np.sin(2 * np.pi * np.cumsum(np.full(n, f)) / SR + mod)
    tine = sine(f * 4, n) * decay(n, 0.03) * 0.15
    env = adsr(n, 0.003, 0.9, 0.35, 0.3, hold=dur)
    return Sound((car + tine) * env * vel * 0.45)


def piano(note, dur, vel=1.0):
    n = n_of(dur + 0.8)
    f = hz(note)
    x = np.zeros(n)
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)   # slight string inharmonicity
        if fk > SR / 2.2:
            break
        x += sine(fk, n) * decay(n, 1.6 / k) / k ** 1.3
    x += lpf(noise(n, 9), 3000) * decay(n, 0.006) * 0.2   # hammer
    return Sound(x * adsr(n, 0.002, 2.0, 0.0, 0.25, hold=dur) * vel * 0.4)


def pluck(note, dur=0.5, vel=1.0, bright=1.0):
    """Plucked string: harmonics that fade faster the higher they are."""
    n = n_of(dur + 0.3)
    f = hz(note)
    x = np.zeros(n)
    for k in range(1, 12):
        if f * k > SR / 2.2:
            break
        x += sine(f * k, n) * decay(n, 0.5 / (k ** (1.2 / bright))) / k
    return Sound(x * ad(n, 0.001, 10) * adsr(n, 0.001, 1, 1, 0.08, hold=dur) * vel * 0.45)


def pad(notes, dur, kind='warm', vel=1.0, seed=7):
    """Sustained chord. kind: warm (detuned saws), glass (sines + shimmer), dark, 80s."""
    n = n_of(dur + 0.8)
    L = np.zeros(n)
    R = np.zeros(n)
    for i, nt in enumerate(notes):
        f = hz(nt)
        for d, side in ((-0.006, 0), (0.0, 2), (0.006, 1)):
            if kind == 'glass':
                v = sine(f * (1 + d), n) + 0.3 * sine(f * 2 * (1 + d), n) + 0.08 * sine(f * 3, n)
            else:
                v = saw(f * (1 + d), n, ph0=(i * 0.13 + d * 50) % 1)
            if side in (0, 2):
                L += v
            if side in (1, 2):
                R += v
    x = np.vstack([L, R]) / (len(notes) * 2)
    cutoff = {'warm': 1400, 'glass': 9000, 'dark': 600, '80s': 2600}[kind]
    x = lpf(x, cutoff, 2)
    env = adsr(n, 0.35, 0.5, 0.85, 0.7, hold=dur)
    return Sound(x * env * vel)


def supersaw(notes, dur, vel=1.0):
    n = n_of(dur + 0.3)
    x = np.zeros((2, n))
    for nt in notes:
        f = hz(nt)
        for j, d in enumerate((-0.012, -0.007, -0.003, 0, 0.003, 0.007, 0.012)):
            x[j % 2] += saw(f * (1 + d), n, ph0=j * 0.137)
    x = hpf(lpf(x / (len(notes) * 4), 7000), 180)
    return Sound(x * adsr(n, 0.01, 0.3, 0.8, 0.2, hold=dur) * vel)


def stab(notes, dur=0.3, kind='dub', vel=1.0):
    n = n_of(dur + 0.4)
    x = sum(saw(hz(nt), n) + saw(hz(nt) * 1.004, n) for nt in notes) / (2 * len(notes))
    cut = 400 + (2500 if kind == 'dub' else 5000) * decay(n, 0.08)
    x = sweep(x, cut, 'low')[0] * adsr(n, 0.003, 0.15, 0.3, 0.12, hold=dur)
    return Sound(x * vel).reverb('plate', 0.35 if kind == 'dub' else 0.1)


def lead(note, dur, kind='square', vel=1.0):
    n = n_of(dur + 0.15)
    f = hz(note) * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * times(n)) * np.clip(times(n) / 0.3, 0, 1))
    if kind == 'chip':
        x = square(f, n, 0.25)
        env = adsr(n, 0.002, 0.05, 0.8, 0.03, hold=dur)
    elif kind == 'saw':
        x = lpf(saw(f, n) + saw(f * 1.005, n), 3500) * 0.6
        env = adsr(n, 0.01, 0.2, 0.7, 0.1, hold=dur)
    else:
        x = lpf(square(f, n, 0.5), 2500)
        env = adsr(n, 0.005, 0.1, 0.7, 0.08, hold=dur)
    return Sound(x * env * vel * 0.35)
