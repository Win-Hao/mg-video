"""Contact sheets from a film, for checking it yourself and for the reviewer. Each frame is labelled below the image
(time, frame number), so a single still keeps its pixel coordinates; --nolabel drops the label.
  Overview: one frame every 0.5 s
    ~/.venvs/mg-video/bin/python sheet.py 成片.mp4 check/总览.png [--every 0.5] [--cols 5] [--width 480]
  Filmstrip: every frame around one moment — fastest moves, transitions, the climax (empty, skipped, off-frame frames)
    ~/.venvs/mg-video/bin/python sheet.py 成片.mp4 check/逐帧-3.2.png --around 3.2 [--span 0.2] [--cols 6] [--width 640]
  Chosen moments: at the embedded width (620 for a card in a 2560 compilation) to see if text reads, or as
  full-resolution stills (--width 1920 --nolabel; one column by default above 1000 px, else up to 4)
    ~/.venvs/mg-video/bin/python sheet.py 成片.mp4 check/手机.png --at 2,4.5 --width 620
  Detail: --crop x,y,w,h (film pixels) and --zoom N (nearest neighbour), e.g. a 54 px label frame by frame
    ~/.venvs/mg-video/bin/python sheet.py 成片.mp4 check/标签.png --around 6.2 --crop 1400,80,300,120 --zoom 3
  --safe 0.05 draws the 5% safe frame on every tile.
  Change per beat (a table, no image needed): beats from the bpm in cues.json counted from the drop (else from 0),
  or between events when there is no bpm. Per beat: first frame against last, the largest change of any frame against
  the beat's first (a sway whose period divides the beat reads 0% first-against-last), the largest single step.
  A pixel has changed when any channel moves by more than 30, at 960 wide (half of 1920). The beat that ends on the drop
  (the climax) is marked.
    ~/.venvs/mg-video/bin/python sheet.py 成片.mp4 --beats cues.json
"""
import argparse, json, math, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure import WORK, changed, frames, probe

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('out', nargs='?')
ap.add_argument('--every', type=float, default=0.5)
ap.add_argument('--around', type=float); ap.add_argument('--span', type=float, default=0.2)
ap.add_argument('--at', help='comma-separated times, e.g. 2,4.5')
ap.add_argument('--cols', type=int); ap.add_argument('--width', type=int)
ap.add_argument('--crop', help='x,y,w,h in film pixels'); ap.add_argument('--zoom', type=int, help='nearest-neighbour enlargement')
ap.add_argument('--safe', type=float, help='draw the safe frame at this share of each side, e.g. 0.05')
ap.add_argument('--nolabel', action='store_true')
ap.add_argument('--beats', help='cues.json: print the change per beat')
a = ap.parse_args()
if not (a.out or a.beats):
    ap.error('give an output image, or --beats cues.json')

info = probe(a.video)
fps, last, W, H = info['fps'], info['n'] - 1, info['w'], info['h']

if a.beats:
    c = json.load(open(a.beats, encoding='utf-8'))
    m = c['music'] if isinstance(c.get('music'), dict) else c
    drop = round(m['drop'] * fps) if isinstance(m.get('drop'), (int, float)) else None
    if m.get('bpm'):
        p, k0 = 60 * fps / m['bpm'], drop or 0
        cuts = sorted({round(k0 + i * p) for i in range(-int(k0 / p) - 1, int((last - k0) / p) + 2)} | {0, last})
    else:
        cuts = sorted({round(e['t'] * fps) for e in c.get('events', []) if 't' in e} | {0, last})
    cuts = [f for f in cuts if 0 <= f <= last]
    rows, first, prev, cur = [], None, None, None
    for n, f, _ in frames(a.video, WORK, info=info):
        if prev is not None:
            step, vs = changed(prev, f).mean() * 100, changed(first, f).mean() * 100
            cur['step'] = max(cur['step'], (step, n)); cur['max'] = max(cur['max'], (vs, n))
            if n in cuts:
                cur.update(b=n, fl=vs); rows.append(cur)
        if n in cuts:
            first, cur = f, {'a': n, 'step': (0, n), 'max': (0, n)}
        prev = f
    print(f'change per beat (% of pixels where a channel moves > 30, at {min(WORK, W)} wide); '
          + (f'{m["bpm"]:g} BPM from {"the drop" if drop else "0"}' if m.get('bpm') else 'beats between events'))
    print(' beat  frames     seconds        first-last   max vs first (at)   max step (at)')
    climax = next((i for i, r in enumerate(rows) if drop and r['a'] < drop <= r['b']), None)
    for i, r in enumerate(rows):
        print(f"{i + 1:4d}  {r['a']:3d}–{r['b']:3d}  {r['a'] / fps:5.2f}–{r['b'] / fps:5.2f}s  {r['fl']:8.1f}%   "
              f"{r['max'][0]:7.1f}% ({r['max'][1]:3d})   {r['step'][0]:6.1f}% ({r['step'][1]:3d})" + ('   <- climax' if i == climax else ''))
    if climax is not None:
        big = [i + 1 for i, r in enumerate(rows) if r['max'][0] > rows[climax]['max'][0]]
        print(f'climax beat {climax + 1}: ' + (f'beats {big} change more (transitions and background swaps are the reviewer\'s call)' if big else 'the largest change'))
    if not a.out:
        sys.exit(0)

if a.at:
    frames_ = sorted({min(round(float(x) * fps), last) for x in a.at.split(',')}); width = a.width or 360
    cols = a.cols or (1 if width > 1000 else min(4, len(frames_)))
elif a.around is not None:
    frames_ = list(range(max(0, round((a.around - a.span) * fps)), min(last, round((a.around + a.span) * fps)) + 1))
    cols, width = a.cols or 6, a.width or 640
else:
    frames_ = sorted({min(round(i * a.every * fps), last) for i in range(int(info['dur'] / a.every + 1e-6) + 1)})
    cols, width = a.cols or 5, a.width or 480
cx, cy, cw, ch = (int(v) for v in a.crop.split(',')) if a.crop else (0, 0, W, H)
if a.zoom:
    size = (cw * a.zoom, ch * a.zoom)
elif a.crop and not a.width:
    size = (cw, ch)
else:
    size = (width, round(ch * width / cw))
scale = size[0] / cw

tiles = []
for n, f, _ in frames(a.video, 0, pick=frames_, info=info):
    im = Image.fromarray(f[cy:cy + ch, cx:cx + cw])
    im = im.resize(size, Image.NEAREST if a.zoom else Image.LANCZOS) if im.size != size else im
    if a.safe:
        d = ImageDraw.Draw(im)
        x0, y0, x1, y1 = ((v - o) * scale for v, o in ((a.safe * W, cx), (a.safe * H, cy), ((1 - a.safe) * W, cx), ((1 - a.safe) * H, cy)))
        d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(0, 229, 255), width=max(1, round(size[0] / 640)))
    tiles.append((n, im))
if not tiles:
    sys.exit('no frames extracted: are the times beyond the film length?')
tw, th = size
pad = 0 if a.nolabel else 26
rows = math.ceil(len(tiles) / cols)
sheet = Image.new('RGB', (cols * tw, rows * (th + pad)), (24, 24, 24))
draw, font = ImageDraw.Draw(sheet), ImageFont.load_default(size=18)
for i, (n, img) in enumerate(tiles):
    x, y = (i % cols) * tw, (i // cols) * (th + pad)
    sheet.paste(img, (x, y))
    if pad:
        draw.text((x + 6, y + th + 3), f'{n / fps:6.3f}s  #{n}', fill=(255, 220, 90), font=font)
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
sheet.save(a.out)
print(f'{a.out}: {len(tiles)} frames, {fps:g}fps' + (f', crop {a.crop}' if a.crop else '') + (f', zoom {a.zoom}x' if a.zoom else ''))
