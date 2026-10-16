#!/usr/bin/env python3
"""Style checks with fixed definitions, so builder and reviewer get the same numbers. Run with
~/.venvs/mg-video/bin/python (needs numpy, scipy, Pillow). Videos are decoded once at 960 px wide (--width); PNG stills
are read at full size. Limits are optional; with one, a PASS or FAIL line ends the run (exit code 1 on FAIL).

  check.py palette FILE… --colors '#hex,…' [--tol 30] [--max-stray 0.015]
      share of pixels on the palette (within --tol RGB distance of a colour), anti-aliasing (within --tol of the line
      between two palette colours) and stray; stray clusters of at least 3×3 px are listed (a sixth colour, a gradient).
      Videos and several files are aggregated; the worst frame is named
  check.py hues FILE… --allow 170-200,230-345 [--sat 0.35 --val 0.25] [--max-outside 0.01]
      coloured pixels (S > 0.35, V > 0.25) whose hue (degrees) is outside the allowed ranges; only clusters of at least
      3×3 px count (1 px colour fringes from offsets and 4:2:0 encoding always exist)
  check.py accents FILM --palette '#hex,…' --accents '#hex,…' [--tol 45] [--min-px 600] [--max 1]
      accent colours on screen per frame: a pixel belongs to its nearest colour in palette + accents (within --tol); an
      accent is on screen with at least --min-px film pixels ("≤ 3 colours" = white + ink + one accent: --max 1)
  check.py drawings FILM [--per-second 12] [--region x,y,w,h] [--min-px 2000]
      a new drawing is a frame where more than --min-px pixels (full size, scaled to the region) change by more than 40
      grey levels; x264 noise after a big change moves 300–500 px by more than 12, so lower thresholds count noise.
      Prints drawings per second and the frames held only once (and, with --per-second, holds outside 2–3 frames)
  check.py flicker FILM [--region x,y,w,h] [--max 1.5]
      mean V of the region per frame (levels) and its second difference: a light or shadow that jumps for a frame
      or two (an off-screen object's shadow sweeping a background) and the per-pixel frame-to-frame noise
  check.py colors STILL.png…        number of distinct colours in rendered PNGs (pixel art), per file and in all
  check.py loop LAST.png FIRST.png [A.png B.png]
      does a loop join: share of pixels that change from the last frame to the first, against two ordinary neighbours
"""
import argparse, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure import Report, WORK, frames, hexes, probe, ranges


def images(files, width, every=1):
    """(label, RGB array) for each PNG, and for each frame of each video at the working width."""
    for p in files:
        if p.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            yield p, np.asarray(Image.open(p).convert('RGB'))
        else:
            info = probe(p)
            pick = list(range(0, info['n'], every)) if every > 1 else None
            for n, f, _ in frames(p, width, pick=pick, info=info):
                yield f'{os.path.basename(p)} f{n}', f


def clusters(mask, f, label, out):
    """Connected areas of mask that contain a 3×3 core: (size, label, bbox x,y,w,h, mean colour)."""
    core = ndimage.binary_erosion(mask, np.ones((3, 3), bool))
    if not core.any():
        return
    lab, _ = ndimage.label(mask)
    objs = ndimage.find_objects(lab)
    for i in np.unique(lab[core]):
        sl = objs[i - 1]
        m = lab[sl] == i
        out.append((int(m.sum()), label, (sl[1].start, sl[0].start, sl[1].stop - sl[1].start, sl[0].stop - sl[0].start), f[sl][m].mean(0)))


def scale_of(files, width):
    v = [p for p in files if not p.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    w = probe(v[0])['w'] if v else 0
    return w / min(width, w) if v and width else 1.0


def palette(a, rep):
    pal = hexes(a.colors)
    tot, worst, found = np.zeros(3), (0, ''), []
    for label, f in images(a.files, a.width, a.every):
        p = f.reshape(-1, 3).astype(np.float32)
        on = np.sqrt(((p[:, None] - pal[None]) ** 2).sum(-1)).min(1) <= a.tol
        aa = np.zeros_like(on)
        rest = np.flatnonzero(~on)
        for i in range(len(pal)):
            for j in range(i + 1, len(pal)):
                d = pal[j] - pal[i]
                q = p[rest] - pal[i]
                t = np.clip(q @ d / (d @ d), 0, 1)
                aa[rest] |= np.sqrt(((q - t[:, None] * d) ** 2).sum(-1)) <= a.tol
        stray = ~on & ~aa
        tot += [on.sum(), aa.sum(), stray.sum()]
        if stray.mean() > worst[0]:
            worst = (stray.mean(), label)
        clusters(stray.reshape(f.shape[:2]), f, label, found)
    tot /= tot.sum()
    print(f'palette {a.colors} (±{a.tol:g} RGB): on the palette {tot[0]:.2%}, anti-aliasing {tot[1]:.2%}, stray {tot[2]:.2%}'
          + (f'; worst {worst[1]}: stray {worst[0]:.2%}' if worst[1] else ''))
    report_clusters(found, a.files, a.width, 'stray')
    rep.row(f'stray share on the worst frame ({worst[1] or "-"})', worst[0] * 100, None if a.max_stray is None else a.max_stray * 100, kind='max', unit='%', fmt='{:.2f}')


def report_clusters(found, files, width, what):
    s = scale_of(files, width)
    if not found:
        print(f'      no {what} clusters of 3×3 px or more'); return
    found.sort(key=lambda c: -c[0])
    print(f'      {what} clusters of 3×3 px or more on {len({c[1] for c in found})} frames or files; largest (film px): ' + '; '.join(
        f'{lab} at {x * s:.0f},{y * s:.0f} {w * s:.0f}x{h * s:.0f} ' + '#{:02X}{:02X}{:02X}'.format(*(int(v) for v in col))
        for n, lab, (x, y, w, h), col in found[:5]))


def hsv(f):
    g = f.astype(np.float32) / 255
    mx, mn = g.max(-1), g.min(-1)
    d = np.maximum(mx - mn, 1e-6)
    r, gg, b = g[..., 0], g[..., 1], g[..., 2]
    h = np.where(mx == r, (gg - b) / d % 6, np.where(mx == gg, (b - r) / d + 2, (r - gg) / d + 4)) * 60
    return h, np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0), mx


def hues(a, rep):
    allow = [tuple(float(x) for x in r.split('-')) for r in a.allow.split(',')]
    col_n = out_n = clus_n = 0
    hist, found, worst = np.zeros(36), [], (0, '')
    for label, f in images(a.files, a.width, a.every):
        h, s, v = hsv(f)
        col = (s > a.sat) & (v > a.val)
        ok = np.zeros_like(col)
        for lo, hi in allow:
            ok |= (h >= lo) & (h <= hi) if lo <= hi else (h >= lo) | (h <= hi)
        out = col & ~ok
        n0 = len(found)
        clusters(out, f, label, found)
        big = sum(c[0] for c in found[n0:])
        col_n += col.sum(); out_n += out.sum(); clus_n += big
        hist += np.histogram(h[out], bins=36, range=(0, 360))[0]
        if col.sum() and big / col.sum() > worst[0]:
            worst = (big / col.sum(), label)
    share, raw = clus_n / max(col_n, 1), out_n / max(col_n, 1)
    print(f'hues outside {a.allow}: {raw:.2%} of the coloured pixels (S > {a.sat:g}, V > {a.val:g}), {share:.2%} in clusters of 3×3 px or more')
    if out_n:
        top = np.argsort(-hist)[:4]
        print('      outside hues by 10°: ' + ', '.join(f'{k * 10}–{k * 10 + 10}° {hist[k] / out_n:.0%}' for k in top if hist[k]))
    report_clusters(found, a.files, a.width, 'off-hue')
    rep.row(f'clustered share on the worst frame ({worst[1] or "-"})', worst[0] * 100, None if a.max_outside is None else a.max_outside * 100,
            kind='max', unit='%', fmt='{:.2f}')


def accents(a, rep):
    pal, acc = hexes(a.palette), hexes(a.accents)
    allc = np.vstack([pal, acc])
    info = probe(a.film)
    s = info['w'] / min(a.width or info['w'], info['w'])
    need = a.min_px / s ** 2
    counts, over = [], []
    for n, f, _ in frames(a.film, a.width, info=info):
        d = np.sqrt(((f[:, :, None, :].astype(np.float32) - allc) ** 2).sum(-1))
        near, ok = d.argmin(-1), d.min(-1) <= a.tol
        k = sum(((near == len(pal) + i) & ok).sum() >= need for i in range(len(acc)))
        counts.append(k)
        if a.max is not None and k > a.max:
            over.append(n)
    counts = np.array(counts)
    print(f'accents {a.accents} on screen per frame (nearest of palette + accents within {a.tol:g}, ≥ {a.min_px} film px): '
          + ', '.join(f'{k}: {(counts == k).sum()} frames' for k in range(counts.max() + 1)))
    if over:
        print(f'      more than {a.max} on {ranges(over)}')
    rep.row('most accents on one frame', counts.max(), a.max, kind='max', fmt='{:.0f}')


def drawings(a, rep):
    info = probe(a.film)
    fps, W, H = info['fps'], info['w'], info['h']
    x, y, w, h = (int(v) for v in a.region.split(',')) if a.region else (0, 0, W, H)
    need = a.min_px * (min(w, W - x) * min(h, H - y)) / (1920 * 1080)
    new, n40, prev = [0], [], None
    for n, f, _ in frames(a.film, 0, gray=True, info=info):
        f = f[y:y + h, x:x + w].astype(np.int16)
        if prev is not None:
            c = int((np.abs(f - prev) > 40).sum())
            n40.append((n, c))
            if c > need:
                new.append(n)
        prev = f
    total = n40[-1][0] + 1 if n40 else 1
    runs = [(new[i], (new[i + 1] if i + 1 < len(new) else total) - new[i]) for i in range(len(new))]
    per = [sum(1 for f in new if s * fps <= f < (s + 1) * fps) for s in range(int(np.ceil(total / fps)))]
    print(f'drawings: a new drawing changes > {need:.0f} px by more than 40 levels' + (f' in {a.region}' if a.region else '')
          + f'; {len(new)} drawings in {total} frames, {len(new) / (total / fps):.1f}/s')
    print('      per second: ' + ' '.join(f'{s}s {k}' for s, k in enumerate(per)))
    singles = [f for f, e in runs if e == 1]
    print('      held one frame only: ' + (', '.join(f'f{f} {f / fps:.2f}s' for f in singles) if singles else 'none'))
    if a.per_second:
        ok = {int(fps // a.per_second), int(-(-fps // a.per_second))}
        odd = [(f, e) for f, e in runs[:-1] if e not in ok]
        if odd:
            print(f'warn  holds other than {sorted(int(o) for o in ok)} frames (at {a.per_second:g}/s): '
                  + ', '.join(f'f{f}×{e}' for f, e in odd[:20]) + (f' … {len(odd)} in all' if len(odd) > 20 else ''))
    border = [(f, c) for f, c in n40 if 30 < c <= need]
    if border:
        print(f'      borderline (30 < px ≤ {need:.0f}): ' + ', '.join(f'f{f} {c}' for f, c in border[:12]) + (' …' if len(border) > 12 else ''))
    rep.row('drawings per second', len(new) / (total / fps), None)


def flicker(a, rep):
    info = probe(a.film)
    s = info['w'] / min(a.width or info['w'], info['w'])
    x, y, w, h = (round(int(v) / s) for v in a.region.split(',')) if a.region else (0, 0, 10 ** 6, 10 ** 6)
    vs, noise, prev = [], [], None
    for n, f, _ in frames(a.film, a.width, info=info):
        v = f[y:y + h, x:x + w].max(axis=2).astype(np.float32)
        vs.append(v.mean())
        if prev is not None:
            noise.append(np.median(np.abs(v - prev)))
        prev = v
    vs = np.array(vs)
    d2 = vs[2:] - 2 * vs[1:-1] + vs[:-2]
    k = int(np.abs(d2).argmax()) + 1
    print(f'flicker: mean V of {a.region or "the whole frame"} per frame, {vs.min():.1f}–{vs.max():.1f} levels; '
          f'per-pixel frame-to-frame noise (median) {np.median(noise):.2f} levels')
    top = np.argsort(-np.abs(d2))[:5] + 1
    print('      largest second differences: ' + ', '.join(f'f{i} {d2[i - 1]:+.2f}' for i in top))
    rep.row(f'largest second difference (f{k})', abs(d2[k - 1]), a.max, kind='max', unit=' levels', fmt='{:.2f}')


def colors(files):
    allc = set()
    for p in files:
        c = np.asarray(Image.open(p).convert('RGB')).reshape(-1, 3).astype(np.uint32)
        u = np.unique(c[:, 0] << 16 | c[:, 1] << 8 | c[:, 2])
        allc.update(u.tolist())
        print(f'{p}: {len(u)} colours')
    if len(files) > 1:
        print(f'all {len(files)} files: {len(allc)} colours')


def loop(last, first, a=None, b=None):
    def share(p, q):
        x = np.asarray(Image.open(p).convert('RGB')).astype(np.int16)
        y = np.asarray(Image.open(q).convert('RGB')).astype(np.int16)
        return (np.abs(x - y).max(-1) > 8).mean()        # pixels that move by more than 8 levels
    seam = share(last, first)
    print(f'last → first: {seam:.2%} of the pixels change')
    if a and b:
        base = share(a, b)
        print(f'an ordinary frame: {base:.2%}')
        if seam <= max(2 * base, 0.001):
            print('→ the loop joins')
        else:
            print(f'→ it jumps: {seam / base:.1f}× an ordinary frame' if base else '→ it jumps: the picture is otherwise still')


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == 'colors':
        return colors(sys.argv[2:])
    if len(sys.argv) in (4, 6) and sys.argv[1] == 'loop':
        return loop(*sys.argv[2:])
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    def video(name, many=False):
        p = sub.add_parser(name)
        p.add_argument('files' if many else 'film', nargs='+' if many else None)
        p.add_argument('--width', type=int, default=WORK, help='working width for videos (0 = full size)')
        p.add_argument('--every', type=int, default=1, help='every n-th frame of a video')
        return p
    p = video('palette', True); p.add_argument('--colors', required=True); p.add_argument('--tol', type=float, default=30)
    p.add_argument('--max-stray', type=float, help='limit: stray share of the worst frame, e.g. 0.015')
    p = video('hues', True); p.add_argument('--allow', required=True)
    p.add_argument('--sat', type=float, default=.35); p.add_argument('--val', type=float, default=.25)
    p.add_argument('--max-outside', type=float, help='limit: clustered off-hue share of the coloured pixels on the worst frame')
    p = video('accents'); p.add_argument('--palette', required=True); p.add_argument('--accents', required=True)
    p.add_argument('--tol', type=float, default=45); p.add_argument('--min-px', type=float, default=600)
    p.add_argument('--max', type=int, help='limit: accents on one frame')
    p = video('drawings'); p.add_argument('--per-second', type=float); p.add_argument('--region')
    p.add_argument('--min-px', type=float, default=2000, help='changed pixels for a new drawing, per 1920×1080 frame')
    p = video('flicker'); p.add_argument('--region'); p.add_argument('--max', type=float, help='limit: largest |second difference|')
    a = ap.parse_args()
    rep = Report()
    {'palette': palette, 'hues': hues, 'accents': accents, 'drawings': drawings, 'flicker': flicker}[a.cmd](a, rep)
    sys.exit(rep.end())


if __name__ == '__main__':
    main()
