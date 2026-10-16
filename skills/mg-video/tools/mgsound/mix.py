"""Mix: two buses (music, sfx), music automation, ducking under effects, and a master that hits a loudness
target with a true-peak ceiling. Exports a 24-bit 48 kHz WAV plus stems.

    m = Mix(6.0)
    music.bed(m, 'explainer', drop=3.5, outro=5.0)
    m.sfx(sfx.pop(), at=0.5)
    m.music_gain([(0, -6), (0.25, 0), (3.5, 2), (5.15, -5)])   # dB over time
    report = m.export('out/audio.wav', stems_dir='out/stems')   # also prints what the master limiter took, and where
"""
import json
import os

import numpy as np
import pyloudnorm
import soundfile as sf
from scipy import ndimage, signal

from .core import SR, Sound, hpf, n_of, place, reverb, sweep


def lufs(x):
    x = np.atleast_2d(x)
    if x.shape[1] < n_of(0.45):
        return -70.0
    v = pyloudnorm.Meter(SR).integrated_loudness(x.T)
    return float(v) if np.isfinite(v) else -70.0


def true_peak_db(x):
    """4x-oversampled peak in dBTP."""
    up = signal.resample_poly(np.atleast_2d(x), 4, 1, axis=1)
    return 20 * np.log10(max(np.abs(up).max(), 1e-9))


def _kweighted_energy(x):
    """Per-sample energy after the BS.1770 K-weighting (48 kHz coefficients), summed over channels: what LUFS sums."""
    y = signal.lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585], x, axis=-1)
    y = signal.lfilter([1.0, -2.0, 1.0], [1, -1.99004745483398, 0.99007225036621], y, axis=-1)
    return (y ** 2).sum(axis=0)


def limit(x, ceiling_db, lookahead=0.003, release=0.08):
    """Look-ahead peak limiter on 4x-oversampled peaks. Gain drops before a peak arrives and recovers slowly."""
    return x * limit_gain(x, ceiling_db, lookahead, release)


def limit_gain(x, ceiling_db, lookahead=0.003, release=0.08):
    """The limiter's gain curve (linear, ≤ 1, one value per sample) for x; limit() multiplies x by it."""
    ceil = 10 ** (ceiling_db / 20)
    n = x.shape[1]
    up = np.abs(signal.resample_poly(x, 4, 1, axis=1)).max(axis=0)
    peak = up[:4 * n].reshape(n, 4).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(peak, 1e-12))
    L = max(1, n_of(lookahead))
    ahead = ndimage.minimum_filter1d(need, size=L, origin=-(L // 2))   # min over the next L samples
    rel = np.exp(-1.0 / (release * SR))
    g = np.empty(n)
    env = 1.0
    for i in range(n):   # instant attack (the look-ahead already starts early), exponential release
        a = ahead[i]
        env = a if a < env else a + (env - a) * rel
        g[i] = env
    return np.convolve(g, np.ones(L) / L)[:n]   # average over the look-ahead window: smooth, still under the ceiling


class Mix:
    def __init__(self, duration, music_level=-20.0, duck_db=3.0, music_hpf=None):
        """music_level: LUFS the music bus is normalised to before automation (the master is normalised after).
        duck_db: how far the music dips under each m.sfx() hit. music_hpf: high-pass on the music bus, in Hz, or
        [(time, Hz), ...] to thin the low end from some moment on; applied before the bus is normalised, so the mids
        come up as the lows go down."""
        self.duration = float(duration)
        self.n = n_of(self.duration)
        self.music = np.zeros((2, self.n))
        self.sfx_bus = np.zeros((2, self.n))
        self.music_level, self.duck_db = music_level, duck_db
        self.hits, self._gain, self._lpf, self._mutes = [], [], [], []
        self._hpf = music_hpf
        self.form = None
        self.limiter = None   # after render(): the master limiter's gain per sample (linear) and the input energy

    def add(self, sound, at, gain=0.0, pan=None, bus='music', verb=None):
        """Place `sound` so its sync point lands on `at` (seconds). verb: None | 'room' | 'plate' | 'hall'."""
        s = sound if isinstance(sound, Sound) else Sound(sound)
        if pan is not None:
            s = s.pan(pan)
        data = s.data * 10 ** (gain / 20)
        if verb:
            data = reverb(data, verb, 0.35)
        place(self.music if bus == 'music' else self.sfx_bus, data, int(round((at - s.sync) * SR)))

    def sfx(self, sound, at, gain=0.0, pan=None, verb=None):
        """A sound effect on the picture event at `at`; the music ducks briefly around it."""
        self.add(sound, at, gain, pan, 'sfx', verb)
        self.hits.append(at)

    def music_gain(self, points):
        """[(time, dB), ...], linear in dB between points; applied to the music bus only."""
        self._gain = sorted(points)

    def music_lpf(self, points):
        """[(time, Hz), ...], e.g. close the filter before a drop: [(2.8, 18000), (3.4, 800), (3.5, 18000)]."""
        self._lpf = sorted(points)

    def mute(self, at, dur):
        self._mutes.append((at, dur))

    # ------------------------------------------------------------ render
    def _music(self):
        x = self.music.copy()
        t = np.arange(self.n) / SR
        if isinstance(self._hpf, (int, float)) and self._hpf > 0:
            x = hpf(x, self._hpf, 2)
        elif self._hpf:
            pts = np.array(sorted(self._hpf), dtype=float)
            x = sweep(x, np.exp(np.interp(t, pts[:, 0], np.log(np.maximum(pts[:, 1], 10)))), 'high', 2)
        L = lufs(x)
        if L > -69:
            x *= 10 ** ((self.music_level - L) / 20)
        if self._gain:
            pts = np.array(self._gain)
            x *= 10 ** (np.interp(t, pts[:, 0], pts[:, 1]) / 20)
        if self._lpf:
            pts = np.array(self._lpf)
            hzs = np.exp(np.interp(t, pts[:, 0], np.log(pts[:, 1])))
            x = sweep(x, hzs, 'low', 2)
        env = np.ones(self.n)
        for at, dur in self._mutes:   # 3 ms ramps so mutes don't click
            a, b, r = n_of(max(at, 0)), n_of(at + dur), n_of(0.003)
            env[a:b] = 0
            env[max(0, a - r):a] = np.minimum(env[max(0, a - r):a], np.linspace(1, 0, a - max(0, a - r)))
            env[b:b + r] = np.minimum(env[b:b + r], np.linspace(0, 1, len(env[b:b + r])))
        if self.hits and self.duck_db > 0:
            duck = np.zeros(self.n)
            for h in self.hits:
                a = n_of(max(0, h - 0.01))
                k = n_of(0.03)
                duck[a:a + k] = 1
            duck = np.maximum(duck, signal.lfilter([1 - np.exp(-1 / (0.2 * SR))], [1, -np.exp(-1 / (0.2 * SR))], duck))
            env *= 10 ** (-self.duck_db * np.clip(duck, 0, 1) / 20)
        return x * env

    def render(self, target_lufs=-14.0, tp=-1.5):
        music = self._music()
        fx = self.sfx_bus
        x0 = hpf(music + fx, 25, 2)
        x, gain_total, lim = x0, 1.0, np.ones(self.n)
        for _ in range(4):   # normalise → limit → re-measure until both targets hold
            L = lufs(x)
            g = 10 ** ((target_lufs - L) / 20) if L > -69 else 1.0
            y = x * g
            gl = limit_gain(y, tp - 0.3)
            x = y * gl
            lim *= gl
            gain_total *= g
            if abs(lufs(x) - target_lufs) < 0.3 and true_peak_db(x) <= tp + 0.05:
                break
        fi, fo = n_of(0.004), n_of(0.25)
        x[:, :fi] *= np.linspace(0, 1, fi)
        x[:, -fo:] *= np.linspace(1, 0, fo)
        stems = {'music': music * gain_total, 'sfx': fx * gain_total}
        self.limiter = (lim, x0)
        return x, stems

    # ------------------------------------------------------------ limiter report
    def _cues(self, cues):
        """[(t, label)] and the climax time from a cues.json path or dict, a list of times / (label, t) pairs,
        or None (this mix's own m.sfx() hits plus the bed's drop and outro)."""
        climax = self.form.drop if self.form is not None else None
        out = []
        if cues is None:
            out = [(t, '') for t in self.hits]
            if self.form is not None:
                out += [(self.form.drop, 'drop'), (self.form.outro, 'outro')]
        else:
            if isinstance(cues, str):
                cues = json.load(open(cues, encoding='utf-8'))
            if isinstance(cues, dict):
                mus = cues.get('music') if isinstance(cues.get('music'), dict) else cues
                if isinstance(mus.get('drop'), (int, float)):
                    climax = float(mus['drop'])
                for e in cues.get('events', []):
                    label = str(e.get('id') or e.get('sfx') or '')
                    if isinstance(e.get('t'), (int, float)):
                        out.append((float(e['t']), label))
                    out += [(float(t), label) for t in e.get('times', []) if isinstance(t, (int, float))]
                    out += [(float(s['t']), label) for s in (e['sfx'] if isinstance(e.get('sfx'), list) else [])
                            if isinstance(s, dict) and isinstance(s.get('t'), (int, float))]
                out += [(float(s['t']), str(s.get('name', ''))) for s in cues.get('sfx', [])
                        if isinstance(s, dict) and isinstance(s.get('t'), (int, float))]
            else:
                out = [(float(c), '') if isinstance(c, (int, float)) else (float(c[1]), str(c[0])) for c in cues]
        seen, uniq = set(), []
        for t, label in sorted(out, key=lambda c: (round(c[0], 3), c[1] == '')):   # a labelled cue wins a tie
            if round(t, 3) not in seen and 0 <= t <= self.duration:
                seen.add(round(t, 3)); uniq.append((t, label))
        return uniq, climax

    def limiter_report(self, cues=None, climax=None, window=0.4):
        """What the master limiter took (dB of gain reduction) at its worst moment, at each cue (largest value within
        100 ms after it) and on the climax (largest value, and the loss of K-weighted loudness, as in LUFS, over its
        first `window` seconds). Run after render() / export()."""
        lim, x0 = self.limiter
        gr = np.maximum(-20 * np.log10(np.maximum(lim, 1e-9)), 0.0)   # dB of reduction, ≥ 0 (no -0.0)
        gr[:n_of(0.004)] = 0   # the limiter's smoothing ramps in over its first 3 ms; the master fades in there anyway
        i = int(np.argmax(gr))
        at = lambda a, b: gr[max(0, n_of(a)):max(1, n_of(b))]
        found, auto_climax = self._cues(cues)
        climax = auto_climax if climax is None else climax
        rep = {'max_db': round(float(gr[i]), 2), 'at': round(i / SR, 3),
               'cues': [{'t': round(t, 3), 'id': lb, 'db': round(float(at(t - 0.005, t + 0.1).max()), 2)} for t, lb in found]}
        if climax is not None and 0 <= climax < self.duration:
            a, b = n_of(climax), n_of(min(self.duration, climax + window))
            pad = n_of(0.05)   # filter run-in
            pre, post = (_kweighted_energy(y[:, max(0, a - pad):b]) for y in (x0, x0 * lim))
            loss = max(0.0, 10 * np.log10(max(pre[-(b - a):].sum(), 1e-20) / max(post[-(b - a):].sum(), 1e-20))) if b > a else 0.0
            rep['climax'] = {'t': round(float(climax), 3), 'peak_db': round(float(at(climax - 0.005, climax + window).max()), 2),
                             'window_db': round(float(loss), 2)}
        return rep

    def export(self, path, lufs_target=-14.0, tp=-1.5, stems_dir=None, cues=None, climax=None):
        """Write the master (24-bit, 48 kHz). tp defaults to -1.5 because AAC encoding raises true peak by ~0.6 dB.
        stems_dir gets music.wav and sfx.wav at the master's gain, before the limiter; each file is scaled down on its own
        if it peaks above -1 dBFS, so compare bus levels with render(), not between the two files.
        Also prints the master limiter's gain reduction: its largest value and when, at each cue (cues: a cues.json path
        or dict, or a list of times; default: this mix's m.sfx() hits and the bed's drop/outro), and on the climax
        (climax=T; default: the cues' or the bed's drop), with a warning when the climax loses more than 3 dB."""
        x, stems = self.render(lufs_target, tp)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        sf.write(path, x.T, SR, subtype='PCM_24')
        if stems_dir:
            os.makedirs(stems_dir, exist_ok=True)
            for k, v in stems.items():
                pk = np.abs(v).max()
                if pk > 10 ** (-1 / 20):
                    v = v * 10 ** (-1 / 20) / pk
                sf.write(os.path.join(stems_dir, f'{k}.wav'), v.T, SR, subtype='PCM_24')
        L, P = lufs(x), true_peak_db(x)
        warnings = []
        if abs(L - lufs_target) > 0.6:
            warnings.append(f'loudness {L:.1f} LUFS, target {lufs_target}')
        if P > tp + 0.1:
            warnings.append(f'true peak {P:.1f} dBTP, ceiling {tp}')
        if not np.isfinite(x).all():
            warnings.append('non-finite samples')
        lr = self.limiter_report(cues, climax)
        c = lr.get('climax')
        # informational: most passed films lose 3-12 dB here and still peak at the climax (10-13 survey)
        if c and c['window_db'] > 3:
            print(f"[mgsound] note: the limiter takes {c['window_db']:.1f} dB off the climax ({c['t']:.3f}–{c['t'] + 0.4:.3f} s): "
                            'if the climax doesn\'t win on spec.py --climax: less low end, weight in 1–4 kHz, denser not spikier (references/audio.md, Limiter)')
        rep = {'path': path, 'duration': round(x.shape[1] / SR, 3), 'lufs': round(L, 2), 'true_peak': round(P, 2),
               'warnings': warnings, 'limiter': lr}
        print(f"[mgsound] {path}: {rep['duration']}s  {rep['lufs']} LUFS  {rep['true_peak']} dBTP  {'; '.join(warnings) or 'ok'}")
        line = f"[mgsound] limiter: max -{lr['max_db']:.1f} dB at {lr['at']:.3f} s"
        if c:
            line += f"; climax {c['t']:.3f}: -{c['peak_db']:.1f} dB peak, -{c['window_db']:.1f} dB over its first 0.4 s"
        print(line)
        if lr['cues']:
            big = [q for q in lr['cues'] if q['db'] >= 0.5]
            rest = len(lr['cues']) - len(big)
            print('[mgsound] limiter at cues: ' + (' | '.join(f"{q['t']:.3f} {q['id']} -{q['db']:.1f}".replace('  ', ' ') for q in big)
                                                    or 'none above 0.5 dB') + (f'  ({rest} more under 0.5 dB)' if big and rest else ''))
        return rep
