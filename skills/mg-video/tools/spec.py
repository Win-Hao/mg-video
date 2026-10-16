#!/usr/bin/env python3
"""Check a film's specs: size, frame rate, duration, loudness, true peak, black frames, colour tags, edge reveal,
stillness, motion in the end hold, the biggest frame-to-frame changes, and where the loudest 0.4 s is.
Exit code 1 if anything FAILs; `warn` lines are leads to look at, not failures.
  py spec.py 成片.mp4 --w 1920 --h 1080 --fps 30 --duration 10 [--lufs -14] [--tp -1] [--noaudio]
             [--climax T [--climax-end T2]] [--cues cues.json]
  py spec.py out/audio.wav [--climax T] [--cues cues.json]       audio only, before the picture is rendered
--climax T (the second of the visual climax): the loudest 0.4 s must end within T…T+1 s full-range AND on a simulated
phone speaker (two 200 Hz high-passes: impacts, sub drops and kicks vanish there), at least 2 dB (full-range) and 3 dB
(phone) above everything outside T−0.1…T2. T2 is --climax-end, else the outro (or hold) in --cues, else T+1.2, so the
climax's own tail isn't counted against it. Also printed: unweighted RMS and RMS below 120 Hz of the climax against
the rest; the jump from the loudest moment in the 1.5 s before T into the climax (warn under 6 dB: the build-up is too
loud); the biggest frame-to-frame changes and the climax's rank among them.
Picture: decoded once, 960 px wide (edges at full size); a pixel has changed when any channel moves by more than 30.
Edge reveal: the template's magenta page (#ff00ff) in the outer 2 px of any edge FAILs; any other uniform band
2–23 px wide along an edge that differs from the picture inside is a warn. Static spans and the end hold are leads.
Run with ~/.venvs/mg-video/bin/python; under a python without numpy it re-runs itself there.
"""
import argparse, collections, json, os, re, subprocess, sys
try:
    import numpy as np
except ImportError:
    VENV = os.path.expanduser('~/.venvs/mg-video/bin/python')
    if os.path.exists(VENV):
        os.execv(VENV, [VENV, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    sys.exit('spec.py needs numpy: run tools/setup.sh, then ~/.venvs/mg-video/bin/python spec.py …')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure import WORK, changed, frames, probe, ranges

CARD = 620     # px: a 1920 film shown as a 1340 px card in a 2560 compilation, on a portrait phone
EDGE = 24      # px scanned at each edge for stripes
MAGENTA = np.array([255, 0, 255])

ap = argparse.ArgumentParser()
ap.add_argument('video', help='the film, or a .wav for the audio checks only')
ap.add_argument('--w', type=int); ap.add_argument('--h', type=int); ap.add_argument('--fps', type=float)
ap.add_argument('--duration', type=float)
ap.add_argument('--lufs', type=float, default=-14.0); ap.add_argument('--tp', type=float, default=-1.0)
ap.add_argument('--noaudio', action='store_true', help='the film is meant to be silent (e.g. a transparent overlay)')
ap.add_argument('--climax', type=float, help='second of the visual climax: the loudest moment must land there, also on a phone speaker')
ap.add_argument('--climax-end', type=float, help='end of the climax section (default: outro or hold in --cues, else climax + 1.2)')
ap.add_argument('--cues', help='cues.json: its outro (or hold) ends the climax section')
a = ap.parse_args()

bad, warns = [], []
def line(ok, text):
    print(('pass  ' if ok else 'FAIL  ') + text)
    if not ok: bad.append(text)
def warn(text):
    print('warn  ' + text); warns.append(text)
def note(text):
    print('      ' + text)

info = probe(a.video)
v, au, dur = info['video'], info['audio'], info['dur']
fps = info.get('fps', a.fps or 30)
def check(want, ok, text):
    if want is None: note(text + ' (no target given; reported only)')
    else: line(ok, text)
if v:
    check(a.w, a.w is not None and (v['width'], v['height']) == (a.w, a.h), f"size {v['width']}x{v['height']}" + (f' (want {a.w}x{a.h})' if a.w else ''))
    check(a.fps, a.fps is not None and abs(fps - a.fps) < 0.01, f'fps {fps:g}' + (f' (want {a.fps:g})' if a.fps else ''))
    note(f'video {v["codec_name"]} {v.get("pix_fmt", "")}')
    tags = [v.get(k, 'unknown') for k in ('color_space', 'color_primaries', 'color_transfer')]
    text = 'colour tags: matrix {}, primaries {}, transfer {}'.format(*tags)
    if all(t == 'bt709' for t in tags): line(True, text)
    else: warn(text + ' (want bt709 for all three; films rendered before 10-13 19:50 lack primaries and transfer: metadata only, the pixels are identical)')
else:
    note('audio only: picture checks skipped')
check(a.duration, a.duration is not None and abs(dur - a.duration) <= 1.0 / fps + 1e-3,
      f'duration {dur:.3f}s, {info.get("n", "?") if v else "audio"}' + (' frames' if v else '') + (f' (want {a.duration:g}s)' if a.duration else ''))

T = a.climax
T2 = a.climax_end
if T is not None and T2 is None and a.cues:
    c = json.load(open(a.cues, encoding='utf-8'))
    m = c['music'] if isinstance(c.get('music'), dict) else c
    T2 = next((float(x) for x in (m.get('outro'), m.get('hold'), c.get('hold')) if isinstance(x, (int, float)) and x > T), None)
if T is not None and T2 is None:
    T2 = T + 1.2

# ---------------------------------------------------------------- sound
if a.noaudio:
    line(not au, 'no audio track' if not au else 'has an audio track but should be silent')
elif not au:
    line(False, 'no audio track')
else:
    r = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', a.video, '-map', '0:a:0', '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    summary = r[r.rfind('Summary:'):]
    I = float(re.search(r'I:\s+(-?[\d.]+) LUFS', summary).group(1))
    tp = float(re.search(r'Peak:\s+(-?[\d.]+|-inf) dBFS', summary).group(1))
    line(abs(I - a.lufs) <= 1.0, f'loudness {I:.1f} LUFS (want {a.lufs:g} ±1)')
    line(tp <= a.tp + 0.05, f'true peak {tp:.1f} dBTP (want ≤ {a.tp:g})')
    MOM = r't:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+)'
    mm = [(float(t), float(m)) for t, m in re.findall(MOM, r)]
    # Phone speakers reproduce almost nothing below ~200 Hz: simulate with two 200 Hz high-passes (~24 dB/oct).
    rp = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', a.video, '-map', '0:a:0', '-af',
                         'highpass=f=200,highpass=f=200,ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ph = [(float(t), float(m)) for t, m in re.findall(MOM, rp)]
    if mm:
        t_end, m_max = max(mm, key=lambda x: x[1])
        note(f'loudest 0.4 s: {max(0, t_end - 0.4):.1f}–{t_end:.1f}s ({m_max:.1f} LUFS) — should be the visual climax; if it is on a hold or a pause, reshape the music')
    if ph:
        t_end, m_max = max(ph, key=lambda x: x[1])
        note(f'loudest 0.4 s on a phone speaker: {max(0, t_end - 0.4):.1f}–{t_end:.1f}s ({m_max:.1f} LUFS) — should also be the climax; '
             'if not, the hit lives below 200 Hz: give it a 1–4 kHz layer (chord, bright transient), don\'t add bass (it trips the limiter)')
    if mm and ph:
        def by_second(series):
            return [max([m for t, m in series if i < t <= i + 1] or [float('-inf')]) for i in range(int(round(dur)))]
        note('loudness by second, max momentary LUFS full-range / phone: '
             + '  '.join(f'{i}s {f:.0f}/{p:.0f}' for i, (f, p) in enumerate(zip(by_second(mm), by_second(ph)))))
    def climax_check(series, label, need):
        t_end, m_max = max(series, key=lambda x: x[1])
        others = [m for t, m in series if not (T - 0.1 <= t <= T2)]
        margin = m_max - max(others) if others else 99.0
        if T <= t_end <= T + 1.0:       # the 0.4 s window ending here contains the hit
            line(margin >= need, f'{label}: loudest 0.4 s ends at {t_end:.1f}s, on the climax ({T:g}s), {margin:.1f} dB above '
                 f'everything outside {T - 0.1:g}–{T2:g}s' + ('' if margin >= need else f' (want ≥ {need:g} dB)'))
        else:
            line(False, f'{label}: loudest 0.4 s is {max(0, t_end - 0.4):.1f}–{t_end:.1f}s ({m_max:.1f} LUFS), not the climax ({T:g}s)')
        pre = [m for t, m in series if T - 1.5 <= t <= T - 0.05]
        hit = [m for t, m in series if T <= t <= T + 1.0]
        if pre and hit:
            j = max(hit) - max(pre)
            (warn if j < 6 else note)(f'{label}: jump from the loudest moment in the 1.5 s before the climax {j:+.1f} dB'
                                      + (' (want ≥ 6 dB: the build-up is too loud)' if j < 6 else ''))
    if T is not None and mm and ph:
        climax_check(mm, 'climax full-range', 1.0)  # the phone check (3 dB) is the real bar; HUD passed review at 1.7
        climax_check(ph, 'climax on a phone speaker', 3.0)
        from scipy.signal import butter, sosfilt
        x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', a.video, '-map', '0:a:0', '-ac', '1', '-ar', '48000',
                                          '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32).astype(np.float64)
        for label, sig in (('unweighted RMS', x), ('RMS below 120 Hz', sosfilt(butter(4, 120, 'low', fs=48000, output='sos'), x))):
            cs = np.concatenate([[0], np.cumsum(sig ** 2)])
            ends = np.arange(19200, len(sig) + 1, 4800)          # 0.4 s windows every 0.1 s, like the momentary loudness
            t, db = ends / 48000, 10 * np.log10(np.maximum((cs[ends] - cs[ends - 19200]) / 19200, 1e-12))
            ci, oi = (t >= T) & (t <= T + 1.0), (t < T - 0.1) | (t > T2)
            if ci.any() and oi.any():
                note(f'{label}, loudest 0.4 s: climax {db[ci].max():.1f} dBFS, the rest {db[oi].max():.1f} dBFS ({db[ci].max() - db[oi].max():+.1f} dB)')
    print(f'      audio {au[0]["codec_name"]} {au[0].get("sample_rate")}Hz {au[0].get("channels")}ch')

# ---------------------------------------------------------------- picture
def spans(fs, most=8):
    r = ranges(fs).split(', ')
    return ', '.join(r[:most]) + (f' … ({len(fs)} frames in all)' if len(r) > most else f' ({min(fs) / fps:.2f}' + (f'–{max(fs) / fps:.2f}s)' if max(fs) > min(fs) else 's)'))

if v:
    chg, still, black, magenta, stripes = [0.0], [], [], collections.defaultdict(list), []
    tail, prev, B = collections.deque(maxlen=round(1.2 * fps)), None, 60
    for n, f, ed in frames(a.video, WORK, edge=EDGE, info=info):
        if ((f[::2, ::2] @ np.array([0.2126, 0.7152, 0.0722])) <= 15).mean() >= 0.98:   # blackdetect's 0.06 pixel / 98% picture
            black.append(n)
        for k, s in ed.items():
            s = s.astype(np.int16)
            if (np.abs(s[:2] - MAGENTA).max(-1) <= 40).sum() >= 8:
                magenta[n].append(k); continue
            ref, w = np.median(s[0], axis=0), 0
            while w < EDGE and (np.abs(s[w] - ref).max(-1) <= 14).mean() >= 0.9:
                w += 1
            if 2 <= w < EDGE and (np.abs(s[w] - ref).max(-1) <= 14).mean() < 0.5:      # the inside clearly differs
                stripes.append((n, k, w, '#%02X%02X%02X' % tuple(int(c) for c in ref)))
        if prev is not None:
            d = f.astype(np.int16) - prev
            m = np.abs(d).max(axis=2) > 30
            chg.append(m.mean() * 100)
            d = d.mean(axis=2)                                                   # signed: fades show, noise cancels
            h, w2 = d.shape[0] // B * B, d.shape[1] // B * B
            blocks = np.abs(d[:h, :w2].reshape(h // B, B, w2 // B, B).mean(axis=(1, 3))).max() if h and w2 else 0
            still.append(m.sum() < 10 and blocks < 1.5)
        prev = f.astype(np.int16); tail.append(f)
    N = len(chg)
    line(not black, 'no black frames' if not black else 'black frames: ' + spans(black))
    line(not magenta, 'edge reveal: no template magenta at the frame edges' if not magenta else
         'edge reveal: the template\'s magenta page shows at the frame edge on ' + spans(list(magenta))
         + ' (' + ', '.join(f'f{n} {"".join(e)}' for n, e in list(magenta.items())[:6]) + ')')
    if stripes:
        warn(f'edge stripes on {spans(sorted({s[0] for s in stripes}))}: a uniform band along the edge that differs from the picture inside '
             '(a camera shake or moved stage showing the page?): ' + ', '.join(f'f{n} {k} {w}px {c}' for n, k, w, c in stripes[:8])
             + (f' … {len(stripes)} in all' if len(stripes) > 8 else ''))
    runs, i = [], 0
    while i < len(still):
        j = i
        while j < len(still) and still[j]: j += 1
        if j - i >= round(0.8 * fps): runs.append((i, j))        # still[i] is the change into frame i+1
        i = j + 1
    if runs:
        note('nearly static ≥ 0.8 s (fewer than 10 px changed, no area brightening or dimming): '
             + ', '.join(f'{s / fps:.2f}–{e / fps:.2f}s' for s, e in runs) + ' — a lead only; deliberate end holds are fine')
    order = np.argsort(-np.array(chg), kind='stable')
    note('biggest frame-to-frame changes (% of pixels): ' + ', '.join(f'f{k} {k / fps:.2f}s {chg[k]:.1f}%' for k in order[:5]))
    if T is not None:
        fc = round(T * fps)
        win = [k for k in (fc - 1, fc, fc + 1) if 0 < k < N]
        cf = max(win, key=lambda k: chg[k])
        bigger = [int(k) for k in order if chg[k] > chg[cf] and k not in win]
        text = f'climax picture change {chg[cf]:.1f}% at f{cf}, rank {len(bigger) + 1} of {N - 1}'
        if bigger:
            warn(text + '; bigger: ' + ', '.join(f'f{k} {k / fps:.2f}s {chg[k]:.1f}%' for k in bigger[:5])
                 + ' (transitions and background swaps are the reviewer\'s call)')
        else:
            note(text)
    from scipy import ndimage
    best, at = 0.0, None
    for i, f in enumerate(list(tail)[1:], 1):
        m = changed(tail[0], f)
        if m.any():
            t = 2 * ndimage.distance_transform_edt(m).max() - 1                  # width of the widest changed band
            if t > best: best, at = t, N - len(tail) + i
    px = best * CARD / tail[0].shape[1]
    text = f'end hold (last 1.2 s, f{N - len(tail)}–{N - 1}): largest move ≈ {px:.1f} px on a {CARD} px card' + (f' (f{at})' if at else '')
    (warn if px < 2 else note)(text + (' — under 2 px: nothing moves visibly at the embedded size' if px < 2 else ''))

print(('all passed' if not bad else f'{len(bad)} failed') + (f', {len(warns)} warnings' if warns else ''))
sys.exit(1 if bad else 0)
