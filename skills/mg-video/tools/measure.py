#!/usr/bin/env python3
"""Generic measurements on the encoded film, for builders and reviewers alike (fixed definitions, so both get the same
numbers). Each line prints value, limit and margin, flags a margin under 10% of the limit, and the run ends with PASS or
FAIL when limits are given (exit code 1 on FAIL). The film is decoded once per call; frames are reduced to a working
width (--width, default 960 = half of 1920) with a box filter; positions and sizes are reported in film pixels.

  py measure.py margins 成片.mp4 --color '#FFD23F[,#hex…]' [--tol 30] [--safe 0.05] [--frames a-b] [--every n]
      bounding box of the pixels within --tol (RGB distance) of the colours, on every frame, overshoot frames included,
      and its distance to each edge; connected areas under --min-px working pixels (default 6) are ignored as specks
  py measure.py margins [成片.mp4] --boxes out/boxes.json [--names a,b] [--safe 0.05]
      the same from the boxes the page exported (render.mjs --boxes); size from the film, boxes.json or video.json
  py measure.py curve 成片.mp4 --region x,y,w,h [--from S] [--to S] [--min-rise S] [--max-jump L]
      mean V = max(R,G,B) of the region per frame (levels 0–255), 10→90% time of its rise (or fall) from the first frame
      to the extreme, and the largest one-frame jump: fades of big bright areas
  py measure.py colorfrac 成片.mp4 [--region x,y,w,h] --at t1,t2,… [--min-colour F] [--max-colour F] [--min-white F] [--max-white F]
      share of coloured (S > 0.35 and V > 0.25) and white (S < 0.15 and V > 0.70) pixels and the mean V (0–1);
      thresholds: --sat --val --white-sat --white-val
  py measure.py overlap --boxes out/boxes.json --a name[,name] --b name[,name] [--gap PX]
      frames where two exported boxes or polygons intersect, and the smallest gap between them

Common options: --width N (working width, 0 = full size), --frames a-b, --every n.
check.py, spec.py and sheet.py import the decoding and reporting helpers from this file, so keep them together.
"""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image

WORK = 960       # working width: half of a 1920 film
CHANGED = 30     # a pixel has changed when any channel moves by more than this (spec.py, sheet.py --beats)


# ---------------------------------------------------------------- shared helpers
def probe(path):
    """Size, fps, frame count, duration and colour tags of the first video stream ({} entries for an audio file)."""
    p = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path],
                                  capture_output=True, text=True, check=True).stdout)
    v = next((s for s in p['streams'] if s['codec_type'] == 'video'), None)
    info = {'dur': float(p['format'].get('duration', 0)), 'audio': [s for s in p['streams'] if s['codec_type'] == 'audio'],
            'video': v}
    if v:
        num, den = map(int, v['r_frame_rate'].split('/'))
        fps = num / den
        info.update(w=v['width'], h=v['height'], fps=fps, n=int(v.get('nb_frames') or round(info['dur'] * fps)))
    return info


def frames(path, width=WORK, gray=False, pick=None, edge=0, info=None):
    """Decode once and yield (n, frame, edges) per frame. frame is reduced to `width` px wide with a box filter (0 or
    ≥ film width: full size); edges, when edge > 0, holds the outer `edge` px of each side at full size,
    {'L','R','T','B'} → (edge, length, 3) arrays with row 0 outermost. pick: frame numbers to keep (ffmpeg drops the rest).
    Untagged YUV is read as bt709 (what render.mjs encodes); tagged files are converted as tagged."""
    info = info or probe(path)
    W, H = info['w'], info['h']
    vf = []
    if pick is not None:
        pick = sorted(set(pick))
        runs, a = [], 0
        for i in range(1, len(pick) + 1):
            if i == len(pick) or pick[i] != pick[i - 1] + 1:
                runs.append(f'between(n\\,{pick[a]}\\,{pick[i - 1]})'); a = i
        vf.append(f"select='{'+'.join(runs)}'")
    if info['video'].get('color_space', 'unknown') == 'unknown' and info['video'].get('pix_fmt', '').startswith('yuv'):
        vf.append('scale=in_color_matrix=bt709:in_range=tv')
    cmd = ['ffmpeg', '-v', 'error', '-i', path, '-map', '0:v:0'] + (['-vf', ','.join(vf), '-fps_mode', 'passthrough'] if vf else []) \
        + ['-f', 'rawvideo', '-pix_fmt', 'gray' if gray else 'rgb24', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1 << 24)
    size, shape = W * H * (1 if gray else 3), (H, W) if gray else (H, W, 3)
    small = width and width < W
    numbers = iter(pick) if pick is not None else iter(range(1 << 30))
    try:
        while True:
            b = p.stdout.read(size)
            if len(b) < size:
                break
            n, a = next(numbers), np.frombuffer(b, np.uint8).reshape(shape)
            ed = None
            if edge:
                ed = {'L': a[:, :edge].swapaxes(0, 1), 'R': a[:, ::-1][:, :edge].swapaxes(0, 1), 'T': a[:edge], 'B': a[::-1][:edge]}
            if small:
                im = Image.frombuffer('L' if gray else 'RGB', (W, H), b, 'raw', 'L' if gray else 'RGB', 0, 1)
                f = W / width
                a = np.asarray(im.reduce(int(f)) if f == int(f) else im.resize((width, round(H * width / W)), Image.BOX))
            yield n, a, ed
    finally:
        p.stdout.close(); p.kill(); p.wait()


def changed(a, b, thr=CHANGED):
    """Mask of pixels where any channel differs by more than thr."""
    d = np.abs(a.astype(np.int16) - b.astype(np.int16))
    return (d.max(axis=-1) if d.ndim == 3 else d) > thr


def hexes(s):
    """'#FFD23F,#111' → (k, 3) float array."""
    out = []
    for h in s.split(','):
        h = h.strip().lstrip('#')
        h = ''.join(c * 2 for c in h) if len(h) == 3 else h
        out.append([int(h[i:i + 2], 16) for i in (0, 2, 4)])
    return np.array(out, float)


def nums(s, cast=float):
    return [cast(x) for x in s.split(',')]


def pick_frames(n, fps, frames_arg=None, every=1, t0=None, t1=None):
    """Frame numbers from --frames a-b / --from / --to / --every; None means every frame."""
    a, b = 0, n - 1
    if frames_arg:
        a, b = (int(x) for x in frames_arg.split('-'))
    if t0 is not None: a = max(a, round(t0 * fps))
    if t1 is not None: b = min(b, round(t1 * fps))
    if (a, b, every) == (0, n - 1, 1):
        return None
    return list(range(a, min(b, n - 1) + 1, every))


def ranges(fs):
    """[3,4,5,9] → 'f3–5, f9'."""
    fs, out, i = sorted(fs), [], 0
    while i < len(fs):
        j = i
        while j + 1 < len(fs) and fs[j + 1] == fs[j] + 1:
            j += 1
        out.append(f'f{fs[i]}' + (f'–{fs[j]}' if j > i else '')); i = j + 1
    return ', '.join(out)


class Report:
    """Rows of value / limit / margin; a margin under 10% of the limit is flagged; end() prints PASS or FAIL."""
    def __init__(self):
        self.limits = self.bad = 0

    def row(self, label, value, limit=None, kind='min', unit='', fmt='{:.1f}'):
        v = fmt.format(value) + unit
        if limit is None:
            print(f'      {label}: {v}')
            return True
        self.limits += 1
        margin = value - limit if kind == 'min' else limit - value
        ok, rel = margin >= 0, margin / abs(limit) if limit else float('inf')
        self.bad += not ok
        close = '  <- within 10% of the limit' if ok and rel < 0.1 else ''
        print(f"{'pass ' if ok else 'FAIL '} {label}: {v} (limit {'≥' if kind == 'min' else '≤'} {fmt.format(limit)}{unit}, "
              f"margin {'+' if margin >= 0 else '−'}{fmt.format(abs(margin))}{unit}"
              + (f', {rel:.0%}' if limit and ok else '') + f'){close}')
        return ok

    def end(self):
        if self.limits:
            print('PASS' if not self.bad else f'FAIL ({self.bad} of {self.limits} limits)')
        return 1 if self.bad else 0


def load_boxes(path):
    d = json.load(open(path, encoding='utf-8'))
    return d.get('fps', 30), d['frames']


def corners(v):
    """A box [x, y, w, h] or a polygon [[x, y], …] as an (n, 2) array."""
    v = np.asarray(v, float)
    if v.ndim == 1:
        x, y, w, h = v
        return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]])
    return v


def _cross(a, b):
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def _inside(p, P):
    X, Y = P[:, 0], P[:, 1]
    X2, Y2 = np.roll(X, -1), np.roll(Y, -1)
    hit = ((Y > p[1]) != (Y2 > p[1])) & (p[0] < (X2 - X) * (p[1] - Y) / np.where(Y2 != Y, Y2 - Y, 1e-12) + X)
    return hit.sum() % 2 == 1


def _vertex_dist(a, b):
    d = np.roll(b, -1, 0) - b
    v = a[:, None] - b[None]
    t = np.clip((v * d[None]).sum(-1) / np.maximum((d * d).sum(-1), 1e-12)[None], 0, 1)
    return np.sqrt(((v - t[..., None] * d[None]) ** 2).sum(-1)).min()


def gap(a, b):
    """Distance between two polygons; 0 when they touch, cross or one holds the other."""
    if _inside(a[0], b) or _inside(b[0], a):
        return 0.0
    r, s = np.roll(a, -1, 0) - a, np.roll(b, -1, 0) - b
    rxs, qp = _cross(r[:, None], s[None]), b[None] - a[:, None]
    with np.errstate(divide='ignore', invalid='ignore'):
        t, u = _cross(qp, s[None]) / rxs, _cross(qp, r[:, None]) / rxs
    if np.any((rxs != 0) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)):
        return 0.0
    return min(_vertex_dist(a, b), _vertex_dist(b, a))


def film_size(film, boxes, size):
    if film:
        i = probe(film); return i['w'], i['h']
    if size:
        return tuple(int(x) for x in size.lower().split('x'))
    b = json.load(open(boxes, encoding='utf-8'))
    if 'width' in b:
        return b['width'], b['height']
    vj = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(boxes))), 'video.json')
    if os.path.exists(vj):
        v = json.load(open(vj)); return v['width'], v['height']
    sys.exit('give the film or --size WxH so the right and bottom margins can be measured')


# ---------------------------------------------------------------- subcommands
def margins(a, rep):
    edges = ('left', 'right', 'top', 'bottom')
    if a.boxes:
        W, H = film_size(a.film, a.boxes, a.size)
        fps, fr = load_boxes(a.boxes)
        names = a.names.split(',') if a.names else sorted({k for f in fr for k in f})
        lo, hi = map(int, a.frames.split('-')) if a.frames else (0, len(fr) - 1)
        for name in names:
            worst = {e: (float('inf'), None) for e in edges}
            for i in range(lo, min(hi, len(fr) - 1) + 1, a.every):
                if name not in fr[i]:
                    continue
                c = corners(fr[i][name])
                d = dict(zip(edges, (c[:, 0].min(), W - c[:, 0].max(), c[:, 1].min(), H - c[:, 1].max())))
                for e in edges:
                    if d[e] < worst[e][0]:
                        worst[e] = (d[e], i)
            if worst['left'][1] is None:
                print(f'      {name}: not in {a.boxes}'); continue
            print(f'{name} ({a.boxes}, {W}x{H}):')
            for e in edges:
                lim = None if a.safe is None else a.safe * (W if e in ('left', 'right') else H)
                rep.row(f'  {e:6s} at f{worst[e][1]}', worst[e][0], lim, unit=' px', fmt='{:.0f}')
        return
    info = probe(a.film)
    W, H, ww = info['w'], info['h'], a.width or info['w']
    s = W / min(ww, W)
    cols, pick = hexes(a.color), pick_frames(info['n'], info['fps'], a.frames, a.every)
    from scipy import ndimage
    worst = {e: (float('inf'), None) for e in edges}
    present, missing, below = 0, [], {e: [] for e in edges}
    lims = {e: None if a.safe is None else a.safe * (W if e in ('left', 'right') else H) for e in edges}
    for n, f, _ in frames(a.film, a.width, pick=pick, info=info):
        d = np.sqrt(((f[:, :, None, :].astype(np.float32) - cols) ** 2).sum(-1)).min(-1)
        m = d <= a.tol
        if a.min_px > 1 and m.any():
            lab, k = ndimage.label(m)
            keep = np.bincount(lab.ravel()) >= a.min_px; keep[0] = False
            m = keep[lab]
        if not m.any():
            missing.append(n); continue
        present += 1
        r, c = np.flatnonzero(m.any(1)), np.flatnonzero(m.any(0))
        dist = dict(zip(edges, (c[0] * s, W - (c[-1] + 1) * s, r[0] * s, H - (r[-1] + 1) * s)))
        for e in edges:
            if dist[e] < worst[e][0]:
                worst[e] = (dist[e], n)
            if lims[e] is not None and dist[e] < lims[e]:
                below[e].append(n)
    print(f'margins of {a.color} (±{a.tol:g} RGB, areas ≥ {a.min_px} px at {min(ww, W)} wide, ±{s:.0f} px): '
          f'on {present} frames' + (f'; not on {ranges(missing)}' if missing else ''))
    if present:
        for e in edges:
            rep.row(f'  {e:6s} at f{worst[e][1]}', worst[e][0], lims[e], unit=' px', fmt='{:.0f}')
            if below[e]:
                print(f'        below the limit on {ranges(below[e])}')


def curve(a, rep):
    info = probe(a.film)
    pick = pick_frames(info['n'], info['fps'], a.frames, a.every, a.t0, a.t1)
    s = info['w'] / min(a.width or info['w'], info['w'])
    x, y, w, h = (round(v / s) for v in nums(a.region)) if a.region else (0, 0, 10 ** 6, 10 ** 6)
    fs, vs = [], []
    for n, f, _ in frames(a.film, a.width, pick=pick, info=info):
        fs.append(n); vs.append(f[y:y + h, x:x + w].max(axis=2).mean())
    vs, fps = np.array(vs), info['fps']
    up = vs.max() - vs[0] >= vs[0] - vs.min()
    k = int(vs.argmax() if up else vs.argmin())
    sign = 1 if up else -1
    rel = sign * (vs - vs[0]) / max(abs(vs[k] - vs[0]), 1e-9)
    i10, i90 = int(np.argmax(rel >= 0.1)), int(np.argmax(rel >= 0.9))
    j = np.diff(vs)
    big = int(np.abs(j).argmax()) if len(j) else 0
    print(f'curve: mean V of region {a.region or "whole frame"} (levels 0–255, at {min(a.width or info["w"], info["w"])} wide), '
          f'f{fs[0]}–{fs[-1]} ({fs[0] / fps:.2f}–{fs[-1] / fps:.2f} s)')
    print(f'      start {vs[0]:.1f} (V {vs[0] / 255:.2f}), {"max" if up else "min"} {vs[k]:.1f} (V {vs[k] / 255:.2f}) at f{fs[k]} ({fs[k] / fps:.2f} s)')
    print(f'      10→90% of the {"rise" if up else "fall"}: f{fs[i10]}–f{fs[i90]}, {fs[i10] / fps:.2f}–{fs[i90] / fps:.2f} s')
    step = max(1, len(vs) // 24)
    print('      curve: ' + ' '.join(f'{fs[i] / fps:.2f}:{vs[i]:.0f}' for i in range(0, len(vs), step)))
    rep.row('10→90% time', (fs[i90] - fs[i10]) / fps, a.min_rise, unit=' s', fmt='{:.2f}')
    if len(j):
        rep.row(f'largest one-frame jump ({j[big]:+.1f} into f{fs[big + 1]})', abs(j[big]), a.max_jump, kind='max', unit=' levels')


def colorfrac(a, rep):
    info = probe(a.film)
    fps, n = info['fps'], info['n']
    want = [min(round(t * fps), n - 1) for t in nums(a.at)] if a.at else pick_frames(n, fps, a.frames, a.every) or list(range(n))
    s = info['w'] / min(a.width or info['w'], info['w'])
    x, y, w, h = (round(v / s) for v in nums(a.region)) if a.region else (0, 0, 10 ** 6, 10 ** 6)
    print(f'colorfrac of region {a.region or "whole frame"} at {min(a.width or info["w"], info["w"])} wide: coloured = S > {a.sat:g} '
          f'and V > {a.val:g}; white = S < {a.white_sat:g} and V > {a.white_val:g}')
    for nf, f, _ in frames(a.film, a.width, pick=want, info=info):
        g = f[y:y + h, x:x + w].astype(np.float32) / 255
        mx, mn = g.max(-1), g.min(-1)
        S = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        col, wht = ((S > a.sat) & (mx > a.val)).mean(), ((S < a.white_sat) & (mx > a.white_val)).mean()
        print(f'  f{nf} ({nf / fps:.2f} s): coloured {col:.1%}, white {wht:.1%}, mean V {mx.mean():.2f}')
        for lab, val, lim, kind in (('coloured', col, a.min_colour, 'min'), ('coloured', col, a.max_colour, 'max'),
                                    ('white', wht, a.min_white, 'min'), ('white', wht, a.max_white, 'max')):
            if lim is not None:
                rep.row(f'    {lab}', val * 100, lim * 100, kind=kind, unit='%')


def overlap(a, rep):
    fps, fr = load_boxes(a.boxes)
    A, B = a.a.split(','), a.b.split(',')
    hits, best = [], (float('inf'), None, '')
    for i, f in enumerate(fr):
        for p in A:
            for q in B:
                if p in f and q in f:
                    g = gap(corners(f[p]), corners(f[q]))
                    if g == 0:
                        hits.append(i)
                    if g < best[0]:
                        best = (g, i, f'{p}/{q}')
    print(f'overlap of {a.a} with {a.b} in {a.boxes} ({len(fr)} frames, {fps:g} fps)')
    print('      they intersect on ' + (ranges(set(hits)) if hits else 'no frame'))
    if best[1] is not None:
        rep.row(f'smallest gap ({best[2]} at f{best[1]})', best[0], a.gap, unit=' px', fmt='{:.0f}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    def common(p, film=True):
        if film:
            p.add_argument('film', nargs='?' if p.prog.endswith(('margins',)) else None)
        p.add_argument('--width', type=int, default=WORK, help='working width (0 = full size)')
        p.add_argument('--frames', help='frame range a-b'); p.add_argument('--every', type=int, default=1)
        return p
    m = common(sub.add_parser('margins'))
    m.add_argument('--color'); m.add_argument('--tol', type=float, default=30); m.add_argument('--min-px', type=int, default=6)
    m.add_argument('--boxes'); m.add_argument('--names'); m.add_argument('--size', help='WxH when no film is given')
    m.add_argument('--safe', type=float, help='limit: distance to each edge ≥ this share of the frame (0.05 = 5%%)')
    c = common(sub.add_parser('curve'))
    c.add_argument('--region'); c.add_argument('--from', dest='t0', type=float); c.add_argument('--to', dest='t1', type=float)
    c.add_argument('--min-rise', type=float, help='limit: 10→90%% time ≥ S seconds')
    c.add_argument('--max-jump', type=float, help='limit: largest one-frame change ≤ L levels')
    f = common(sub.add_parser('colorfrac'))
    f.add_argument('--region'); f.add_argument('--at', help='times in seconds, e.g. 2,4.5')
    for k, v in (('sat', .35), ('val', .25), ('white-sat', .15), ('white-val', .70)):
        f.add_argument('--' + k, type=float, default=v)
    for k in ('min-colour', 'max-colour', 'min-white', 'max-white'):
        f.add_argument('--' + k, type=float, help='limit as a share, e.g. 0.2')
    o = sub.add_parser('overlap')
    o.add_argument('--boxes', required=True); o.add_argument('--a', required=True); o.add_argument('--b', required=True)
    o.add_argument('--gap', type=float, help='limit: smallest gap ≥ PX on every frame where both are present')
    a = ap.parse_args()
    if a.cmd == 'margins' and not (a.boxes or (a.film and a.color)):
        ap.error('margins needs FILM --color HEX or --boxes out/boxes.json')
    rep = Report()
    {'margins': margins, 'curve': curve, 'colorfrac': colorfrac, 'overlap': overlap}[a.cmd](a, rep)
    sys.exit(rep.end())


if __name__ == '__main__':
    main()
