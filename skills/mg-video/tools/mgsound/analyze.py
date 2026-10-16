"""Analysis: load audio (WAV or the audio track of a video), detect onsets, check cue alignment."""
import os
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from scipy import ndimage, signal

from .core import SR

# Calibrated 10-07 on 80 synthetic hits (8 effect types over a music bed): the raw flux peak lands ~2.7 ms
# before the true attack, so it is shifted by +2.7 ms; residual error is within ±3 ms (one hop).
_ONSET_BIAS = 0.0027


def load(path):
    """(2, n) float array at 48 kHz. Videos are decoded with ffmpeg."""
    if not path.lower().endswith(('.wav', '.flac', '.aiff')):
        tmp = os.path.join(tempfile.mkdtemp(prefix='mgsound-'), 'a.wav')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-vn', '-ar', str(SR), '-ac', '2', tmp], check=True)
        path = tmp
    x, sr = sf.read(path, always_2d=True)
    x = x.T
    if sr != SR:
        x = signal.resample_poly(x, SR, sr, axis=1)
    if x.shape[0] == 1:
        x = np.vstack([x, x])
    return x


def onsets(x, hop=128, nfft=1024):
    """Onset times (s) by spectral flux with an adaptive threshold."""
    mono = np.atleast_2d(x).mean(axis=0)
    f, t, Z = signal.stft(mono, SR, nperseg=nfft, noverlap=nfft - hop)
    mag = np.log1p(100 * np.abs(Z))
    flux = np.maximum(0, np.diff(mag, axis=1)).sum(axis=0)
    flux = np.concatenate([[0], flux])
    if flux.max() <= 0:
        return np.array([])
    flux /= flux.max()
    w = max(3, int(0.15 * SR / hop))
    thresh = ndimage.median_filter(flux, size=w) + 0.06
    loc = ndimage.maximum_filter1d(flux, size=max(3, int(0.03 * SR / hop)))
    peaks = np.where((flux >= loc) & (flux > thresh))[0]
    return t[peaks] + _ONSET_BIAS


def align(path, cue_times, tol=0.04):
    """For each cue time: the nearest onset and the error. Cues in the first 0.1 s are unreliable (no lead-in)."""
    on = onsets(load(path))
    out = []
    for c in cue_times:
        if on.size == 0:
            out.append({'t': c, 'onset': None, 'err': None, 'ok': False}); continue
        k = int(np.argmin(np.abs(on - c)))
        e = float(on[k] - c)
        out.append({'t': c, 'onset': round(float(on[k]), 4), 'err': round(e, 4), 'ok': abs(e) <= tol})
    return out
