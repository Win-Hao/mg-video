"""Core DSP for mgsound: a Sound is a stereo float buffer at 48 kHz plus a sync point.

The sync point is the moment inside the buffer that should land on the cue time: the attack of a hit,
the pass-by of a whoosh, the end of a riser. Mix.add(sound, at=t) aligns that moment with t.
Everything is deterministic: noise comes from seeded generators.
"""
import zlib

import numpy as np
from scipy import signal

SR = 48000


def n_of(sec):
    return max(1, int(round(sec * SR)))


def times(n):
    return np.arange(n) / SR


def rng(seed):
    return np.random.default_rng(seed)


class Sound:
    """Stereo buffer of shape (2, n) and a sync point in seconds."""

    def __init__(self, data, sync=0.0):
        data = np.asarray(data, dtype=np.float64)
        if data.ndim == 1:
            data = np.vstack([data, data])
        self.data, self.sync = data, float(sync)

    @property
    def dur(self):
        return self.data.shape[1] / SR

    def gain(self, db):
        return Sound(self.data * 10 ** (db / 20), self.sync)

    def pan(self, p):
        """-1 = left, 0 = centre (unchanged), 1 = right. Equal-power."""
        a = (float(np.clip(p, -1, 1)) + 1) * np.pi / 4
        return Sound(self.data * np.array([[np.cos(a)], [np.sin(a)]]) * np.sqrt(2), self.sync)

    def fade(self, fade_in=0.0, fade_out=0.0):
        d = self.data.copy()
        n = d.shape[1]
        if fade_in > 0:
            k = min(n, n_of(fade_in)); d[:, :k] *= np.linspace(0, 1, k)
        if fade_out > 0:
            k = min(n, n_of(fade_out)); d[:, n - k:] *= np.linspace(1, 0, k)
        return Sound(d, self.sync)

    def lpf(self, hz, order=2):
        return Sound(lpf(self.data, hz, order), self.sync)

    def hpf(self, hz, order=2):
        return Sound(hpf(self.data, hz, order), self.sync)

    def reverb(self, size='room', mix=0.25):
        return Sound(reverb(self.data, size, mix), self.sync)

    def reverse(self):
        return Sound(self.data[:, ::-1].copy(), self.dur - self.sync)

    def tail(self, hold, decay=0.3):
        """Shorten a long sound: unchanged for `hold` s after the sync point, then a fade that is linear in dB and
        reaches -60 dB `decay` s later, where the buffer ends. For bells, chimes and reverb tails that would ring into
        the next event; fade() only touches the last seconds of the buffer, which for a 6 s bell is far too late."""
        n = self.data.shape[1]
        t = np.arange(n) / SR - self.sync
        decay = max(float(decay), 0.003)
        db = np.interp(t, [hold, hold + decay], [0.0, -60.0])   # 0 dB before the hold ends, -60 dB at the cut
        end = min(n, max(1, int(np.ceil((self.sync + hold + decay) * SR))))
        return Sound((self.data * 10 ** (db / 20))[:, :end], self.sync)


# ---------------------------------------------------------------- oscillators
def phase(freq, n):
    """Running phase in cycles; freq may be a number or a per-sample array (Hz)."""
    f = np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,))
    return np.cumsum(f) / SR


def _blep(p, dt):
    out = np.zeros_like(p)
    a = p < dt
    x = p[a] / dt[a]; out[a] = x + x - x * x - 1
    b = p > 1 - dt
    x = (p[b] - 1) / dt[b]; out[b] = x * x + x + x + 1
    return out


def sine(freq, n, ph0=0.0):
    return np.sin(2 * np.pi * (phase(freq, n) + ph0))


def saw(freq, n, ph0=0.0):
    """Band-limited sawtooth (polyBLEP), -1..1."""
    dt = np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,)) / SR
    p = (phase(freq, n) + ph0) % 1.0
    return 2 * p - 1 - _blep(p, dt)


def square(freq, n, duty=0.5, ph0=0.0):
    """Band-limited pulse wave (polyBLEP), -1..1."""
    dt = np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,)) / SR
    p = (phase(freq, n) + ph0) % 1.0
    y = np.where(p < duty, 1.0, -1.0)
    return y + _blep(p, dt) - _blep((p - duty) % 1.0, dt)


def tri(freq, n, ph0=0.0):
    p = (phase(freq, n) + ph0) % 1.0
    return 2 * np.abs(2 * p - 1) - 1


def noise(n, seed=0):
    return rng(seed).uniform(-1, 1, n)


# ---------------------------------------------------------------- envelopes
def decay(n, tau):
    """Exponential decay with time constant tau (s)."""
    return np.exp(-times(n) / max(tau, 1e-4))


def ad(n, attack, tau):
    """Linear attack, then exponential decay."""
    t = times(n)
    a = max(attack, 1e-4)
    return np.where(t < a, t / a, np.exp(-(t - a) / max(tau, 1e-4)))


def adsr(n, attack=0.005, dec=0.1, sustain=0.7, release=0.2, hold=None):
    """hold = seconds from start until release begins (default: release at the end)."""
    t = times(n)
    rel_at = (n / SR - release) if hold is None else hold
    a = max(attack, 1e-4)
    env = np.where(t < a, t / a, sustain + (1 - sustain) * np.exp(-(t - a) / max(dec, 1e-4)))
    level_at_release = sustain + (1 - sustain) * np.exp(-max(rel_at - a, 0) / max(dec, 1e-4))
    env = np.where(t >= rel_at, level_at_release * np.exp(-(t - rel_at) / max(release / 4, 1e-4)), env)
    return env


def bell_curve(n, peak_at, width):
    """Smooth swell that peaks at peak_at (0..1 of the length); used for whooshes."""
    x = np.linspace(0, 1, n)
    return np.exp(-0.5 * ((x - peak_at) / width) ** 2)


# ---------------------------------------------------------------- filters and effects
def _sos(kind, hz, order):
    nyq = SR / 2 * 0.98
    if kind == 'band':
        lo, hi = hz
        return signal.butter(order, [max(lo, 10), min(hi, nyq)], 'band', fs=SR, output='sos')
    return signal.butter(order, min(max(hz, 10), nyq), kind, fs=SR, output='sos')


def lpf(x, hz, order=2):
    return signal.sosfilt(_sos('low', hz, order), x, axis=-1)


def hpf(x, hz, order=2):
    return signal.sosfilt(_sos('high', hz, order), x, axis=-1)


def bpf(x, lo, hi, order=2):
    return signal.sosfilt(_sos('band', (lo, hi), order), x, axis=-1)


def sweep(x, hz, kind='low', order=2, block=256):
    """Time-varying filter: hz is a per-sample array of cutoffs (or (lo, hi) pairs for 'band').
    Processed in blocks with the filter state carried across, which is smooth enough for sweeps."""
    x = np.atleast_2d(x)
    out = np.zeros_like(x)
    zi = None
    for s in range(0, x.shape[1], block):
        e = min(x.shape[1], s + block)
        c = hz[(s + e) // 2]
        sos = _sos(kind, c, order)
        if zi is None:
            zi = np.zeros((x.shape[0], sos.shape[0], 2))
        for ch in range(x.shape[0]):
            out[ch, s:e], zi[ch] = signal.sosfilt(sos, x[ch, s:e], zi=zi[ch])
    return out


def drive(x, amount=2.0):
    """Soft saturation; amount 1 = gentle, 4 = gritty."""
    return np.tanh(x * amount) / np.tanh(amount)


_IRS = {}
_IR_SPECS = {'room': (0.45, 0.006, 6000), 'plate': (1.2, 0.012, 9000), 'hall': (2.2, 0.022, 7000)}


def _ir(size):
    if size not in _IRS:
        length, pre, tone = _IR_SPECS[size]
        n = n_of(length * 1.6)
        g = rng(zlib.crc32(size.encode()))   # not hash(): str hashes change between Python runs
        env = np.exp(-times(n) / (length / 6.9))   # -60 dB at `length`
        ir = g.uniform(-1, 1, (2, n)) * env
        ir = lpf(ir, tone, 1)
        ir = np.concatenate([np.zeros((2, n_of(pre))), ir], axis=1)
        _IRS[size] = ir / np.sqrt(np.sum(ir ** 2) / 2)
    return _IRS[size]


def reverb(x, size='room', mix=0.25):
    """Convolution reverb with a synthetic decaying-noise impulse. Output keeps the input length + tail."""
    x = np.atleast_2d(x)
    if x.shape[0] == 1:
        x = np.vstack([x, x])
    ir = _ir(size)
    wet = np.vstack([signal.fftconvolve(x[c], ir[c]) for c in range(2)])
    out = np.zeros_like(wet)
    out[:, :x.shape[1]] += x
    return out + wet * mix * 0.35


def place(buf, data, start):
    """Add data (2, k) into buf (2, n) at sample `start`, clipping to the buffer."""
    k = data.shape[1]
    a, b = max(0, start), min(buf.shape[1], start + k)
    if a < b:
        buf[:, a:b] += data[:, a - start:b - start]
