#!/usr/bin/env node
// Frame-by-frame renderer for mg-video. Extends code-video's render.mjs (same page contract) with
// parallel workers, motion blur, transparent output, low-res preview, exported boxes, and loud failure reporting.
//
// Page contract (tools/template/index.html already follows it):
//   window.render(t)  draws second t (may be async); may return a key — if it equals the previous frame's key,
//                     the previous screenshot is reused (for on-twos animation)
//   window.__ready = true when loaded;  window.__error = 'why' on failure. Checked on load and around every frame:
//                     the run stops with exit code 1 instead of hanging or writing blank frames
//   window.boxes(t)   optional: named boxes in film pixels, {name: [x, y, w, h]} or polygons {name: [[x, y], ...]},
//                     called right after render(t). Renders of the whole film then also write out/boxes.json:
//                     {"fps": 30, "width": 1920, "height": 1080, "frames": [{name: box, ...}, ...]} (one entry per frame)
// Size, fps, duration, motion blur come from video.json in the current folder:
//   {"width":1920,"height":1080,"fps":30,"duration":8,"motionBlur":{"samples":1,"shutter":0.5}}
//
// Run inside the project folder:
//   node <skill>/tools/render.mjs                               full film → 成片.mp4 (adds out/audio.wav if present)
//   node <skill>/tools/render.mjs --stills 0.5,2,4.25           stills → check/静帧/, after removing the old t*.png there (--keep keeps them)
//   node <skill>/tools/render.mjs --scale 0.5 --out check/预览.mp4   half-resolution preview
//   node <skill>/tools/render.mjs --alpha 透明.mov               transparent ProRes 4444 (page background must be transparent), no audio
//   node <skill>/tools/render.mjs --remux                       sound-only change: out/audio.wav (or --audio) onto the existing 成片.mp4
//                                                               (or --out); the video stream is copied, no browser
//   node <skill>/tools/render.mjs --boxes                       only out/boxes.json (every frame through render(t), no screenshots)
//   node <skill>/tools/render.mjs "index.html?layer=text" …     a query string reaches the page (the server ignores it):
//                                                               debug layers, variants side by side (?v=2)
// Other options: --page other.html  --mb 4 --shutter 0.5  --workers 3  --from 2 --to 4  --audio x.wav | --noaudio
//                --crf 16  --outdir dir
// Needs: `npm i playwright` in the project folder (browser: `npx playwright install chromium`), and ffmpeg.
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync, spawn } from 'node:child_process';
import { createRequire } from 'node:module';

const ROOT = process.cwd();
const FLAGS = new Set(['keep', 'boxes', 'remux', 'noaudio']);   // never take a value (so `--boxes page.html` works)
const argv = process.argv.slice(2), A = { _: [] };
for (let i = 0; i < argv.length; i++) {
  const k = argv[i];
  if (!k.startsWith('--')) { A._.push(k); continue; }
  const v = argv[i + 1];
  if (FLAGS.has(k.slice(2)) || v === undefined || v.startsWith('--')) A[k.slice(2)] = true; else { A[k.slice(2)] = v; i++; }
}
const cfg = fs.existsSync('video.json') ? JSON.parse(fs.readFileSync('video.json', 'utf8')) : {};
const W = +(A.width || cfg.width || 1920), H = +(A.height || cfg.height || 1080);
const FPS = +(A.fps || cfg.fps || 30), DUR = +(A.duration || cfg.duration || 8), TOTAL = Math.round(DUR * FPS);
const MB = Math.max(1, +(A.mb || cfg.motionBlur?.samples || 1)), SHUTTER = +(A.shutter ?? cfg.motionBlur?.shutter ?? 0.5);
const SCALE = +(A.scale || 1), ALPHA = A.alpha ? path.resolve(A.alpha) : null, PAGE = A.page || A._[0] || 'index.html';
const OW = Math.round(W * SCALE), OH = Math.round(H * SCALE);
if (!A.stills && !A.boxes && !A.remux && (OW % 2 || OH % 2)) { console.error(`H.264 needs even dimensions; got ${OW}x${OH}. Fix video.json or --scale.`); process.exit(1); }

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.svg': 'image/svg+xml', '.ttf': 'font/ttf', '.otf': 'font/otf', '.woff': 'font/woff', '.woff2': 'font/woff2',
  '.wasm': 'application/wasm', '.glb': 'model/gltf-binary', '.hdr': 'application/octet-stream', '.wav': 'audio/wav', '.mp4': 'video/mp4' };
let chromium, server, URL0;
async function start() {   // Playwright and the page server, only for modes that open a browser (not --remux)
  try { ({ chromium } = createRequire(path.join(ROOT, 'package.json'))('playwright')); }
  catch { throw new Error('playwright is not installed here: run `npm i playwright` in the project folder (tools/new.sh does this)'); }
  server = http.createServer((req, res) => {
    const f = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    if (!f.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
    fs.readFile(f, (e, d) => {
      if (e) { res.writeHead(404); return res.end(); }
      res.writeHead(200, { 'Content-Type': MIME[path.extname(f).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      res.end(d);
    });
  });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  URL0 = `http://127.0.0.1:${server.address().port}/${PAGE}`;
}
const ARGS = ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--force-color-profile=srgb', '--hide-scrollbars',
  '--font-render-hinting=none', '--disable-lcd-text', '--disable-background-timer-throttling', '--disable-renderer-backgrounding'];

// One browser per worker: pages inside one browser share a compositor and don't render in parallel.
// Each browser goes into `opened` right away so `finally` closes it even when the page fails to load
// (otherwise the leftover browser keeps node alive and the run hangs instead of exiting).
async function openTab(tag = '') {
  const browser = await chromium.launch({ args: process.platform === 'darwin' ? ARGS : ARGS.slice(1) });
  opened.push(browser);
  const tab = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: SCALE });
  tab.on('pageerror', (e) => console.error(`${tag}[page error] ${e.message}`));
  tab.on('console', (m) => { if (m.type() === 'error' && !/favicon/.test(m.location()?.url || '')) console.error(`${tag}[console] ${m.text()}`); });
  tab.on('response', (r) => { if (r.status() >= 400 && !r.url().endsWith('/favicon.ico')) console.error(`${tag}[load failed ${r.status()}] ${r.url()}`); });
  await tab.goto(URL0);
  try { await tab.waitForFunction(() => window.__ready === true || !!window.__error, null, { timeout: 120000 }); }
  catch { throw new Error('the page never set __ready within 2 minutes: usually a font or asset 404 (see [load failed] above), a script error, or build() forgetting to set it'); }
  await healthy(tab, 'on load');
  return tab;
}
const healthy = async (tab, when) => { const e = await tab.evaluate(() => window.__error || null); if (e) throw new Error(`page reported __error ${when}: ${e}`); };
// __error is checked before and after every frame too, so a page that loses its WebGL context mid-film
// (webglcontextlost → __error, as the template does) stops the run instead of writing black frames.
// With `box`, also returns window.boxes(t), taken right after drawing.
const draw = (tab, t, box) => tab.evaluate(async ([t, box]) => {
  const check = () => { if (window.__error) throw new Error(`page reported __error at t=${t}: ${window.__error}`); };
  check();
  const key = (await window.render(t)) ?? null;
  check();
  return [key, box ? (await window.boxes(t)) ?? null : null];
}, [t, box]);
const shot = (tab) => tab.screenshot({ type: 'png', omitBackground: !!ALPHA });
const procs = [];
function ffmpeg(args) {
  const p = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...args], { stdio: ['pipe', 'inherit', 'inherit'] });
  procs.push(p);
  p.on('error', (e) => { console.error('ffmpeg failed to start (installed and on PATH?):', e.message); process.exit(1); });
  p.stdin.on('error', () => {});
  const done = new Promise((res, rej) => p.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg exit code ' + c)))));
  done.catch(() => {});   // a worker that failed never awaits its encoder; `finally` kills it
  return { p, done };
}
const write = (s, b) => new Promise((r) => (s.write(b) ? r() : s.once('drain', r)));
// Audio for the film: --audio x.wav, else out/audio.wav if present; a section (--from) starts it at the same second.
// apad + -t: a short WAV is padded with silence and the audio ends with the video (-shortest let ~1 s of padding
// through after a 2-frame video).
function audioIn(f0, dur) {
  const a = A.noaudio ? null : A.audio ? path.resolve(A.audio) : fs.existsSync('out/audio.wav') ? path.resolve('out/audio.wav') : null;
  if (a && !fs.existsSync(a)) throw new Error('no such audio file: ' + a);
  return a && { file: a, args: [...(f0 > 0 ? ['-ss', String(f0 / FPS)] : []), '-i', a, '-map', '0:v:0', '-map', '1:a:0',
    '-af', 'apad', '-t', String(dur), '-c:a', 'aac', '-b:a', '256k', '-ar', '48000'] };
}
function writeBoxes(frames) {   // one frame per line, numbers to 0.01 px
  const r = (k, v) => (typeof v === 'number' ? Math.round(v * 100) / 100 : v);
  fs.mkdirSync('out', { recursive: true });
  fs.writeFileSync('out/boxes.json', `{"fps": ${FPS}, "width": ${W}, "height": ${H}, "frames": [\n`
    + Array.from({ length: TOTAL }, (_, f) => JSON.stringify(frames[f] ?? null, r)).join(',\n') + '\n]}\n');
}

const opened = [], junk = [];
try {
  if (A.remux) {
    const film = path.resolve(A.out || '成片.mp4');
    if (!fs.existsSync(film)) throw new Error(`nothing to remux: ${path.relative(ROOT, film)} doesn't exist (render it first, or pass --out)`);
    const vdur = execFileSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=duration', '-of', 'csv=p=0', film], { encoding: 'utf8' }).trim();
    const au = audioIn(Math.round(+(A.from || 0) * FPS), vdur);
    if (!au) throw new Error('no audio to put on the film: run audio.py (out/audio.wav) or pass --audio x.wav');
    const tmpf = path.join(path.dirname(film), '.remux-' + path.basename(film));
    junk.push(tmpf);
    await ffmpeg(['-i', film, ...au.args, '-c:v', 'copy', '-movflags', '+faststart', tmpf]).done;
    fs.renameSync(tmpf, film);
    console.log(`done → ${film} (video copied, audio from ${path.relative(ROOT, au.file)})`);
  } else if (A.stills) {
    const dir = path.resolve(A.outdir || 'check/静帧'), times = String(A.stills).split(',').map(Number);
    if (times.some(isNaN)) throw new Error('--stills takes seconds separated by commas, e.g. --stills 0.5,2,4.25');
    fs.mkdirSync(dir, { recursive: true });
    await start();
    const tab = await openTab();
    if (!A.keep) {   // only the stills this command writes, so a stale one can't be mistaken for the current code
      const old = fs.readdirSync(dir).filter((f) => /^t-?\d+\.\d{3}\.png$/.test(f));
      for (const f of old) fs.rmSync(path.join(dir, f));
      if (old.length) console.log(`removed ${old.length} old still(s) from ${dir} (--keep keeps them)`);
    }
    for (const t of times) {
      await draw(tab, t, false);
      const f = path.join(dir, `t${t.toFixed(3)}.png`);
      fs.writeFileSync(f, await shot(tab));
      console.log(f);
    }
  } else {
    // --boxes: the whole film through render(t) and boxes(t), no screenshots, no video
    const f0 = A.boxes ? 0 : Math.round(+(A.from || 0) * FPS), f1 = A.boxes ? TOTAL : Math.min(TOTAL, Math.round(+(A.to ?? DUR) * FPS));
    if (f1 <= f0) throw new Error(`nothing to render: frames ${f0}-${f1}`);
    const WORKERS = Math.max(1, Math.min(+(A.workers || 1), f1 - f0)), SUB = A.boxes ? 1 : MB;
    const out = ALPHA || path.resolve(A.out || '成片.mp4');
    const started = Date.now(), boxes = [];
    let tmp = null, rec = false;
    if (!A.boxes) { tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'mg-render-')); junk.push(tmp); }
    console.log(A.boxes ? `boxes: frames 0-${TOTAL}, ${WORKERS} worker(s)` : `rendering ${OW}x${OH} ${FPS}fps frames ${f0}-${f1}${MB > 1 ? `, motion blur ${MB} samples` : ''}${ALPHA ? ', transparent' : ''}, ${WORKERS} worker(s)`);
    // Motion blur: each output frame is the average of MB sub-frame captures spread over the shutter interval.
    // ffmpeg averages each group of MB inputs (tmix) and keeps the last frame of every group.
    const blur = MB > 1 ? ['-vf', `tmix=frames=${MB},select='not(mod(n+1\\,${MB}))',setpts=N/${FPS}/TB`] : [];
    const segCodec = ALPHA ? ['-c:v', 'png'] : ['-c:v', 'libx264rgb', '-crf', '0', '-preset', 'ultrafast'];
    const per = Math.ceil((f1 - f0) / WORKERS), segs = [];
    let done = 0;
    await start();
    await Promise.all(Array.from({ length: WORKERS }, async (_, w) => {
      const a = f0 + w * per, b = Math.min(f1, a + per);
      if (a >= b) return;
      const tab = await openTab(WORKERS > 1 ? `[w${w}] ` : '');
      const has = await tab.evaluate(() => typeof window.boxes === 'function');
      if (A.boxes && !has) throw new Error('--boxes: the page defines no window.boxes(t) (see the page contract at the top of render.mjs)');
      rec = has && f0 === 0 && f1 === TOTAL;   // boxes only for the whole film, so out/boxes.json never mixes renders
      let ff = null;
      if (tmp) {
        segs[w] = path.join(tmp, `seg${String(w).padStart(2, '0')}.mkv`);
        ff = ffmpeg(['-f', 'image2pipe', '-framerate', String(FPS * MB), '-c:v', 'png', '-i', '-', ...blur, '-r', String(FPS), ...segCodec, segs[w]]);
      }
      let lastKey = null, buf = null;
      for (let f = a; f < b; f++) {
        for (let s = 0; s < SUB; s++) {
          const t = SUB > 1 ? Math.max(0, (f + SHUTTER * ((s + 0.5) / SUB - 0.5)) / FPS) : f / FPS;
          const [key, bx] = await draw(tab, t, rec && SUB === 1);
          if (rec && SUB === 1) boxes[f] = bx;
          if (!ff) continue;
          if (SUB > 1 || key === null || key !== lastKey || !buf) buf = await shot(tab);
          lastKey = key;
          await write(ff.p.stdin, buf);
        }
        if (rec && SUB > 1) boxes[f] = (await draw(tab, f / FPS, true))[1];   // at the frame's own time, after its sub-frames
        if (++done % 30 === 0) {
          const el = (Date.now() - started) / 1000;
          console.log(`  ${done}/${f1 - f0} frames  ${el.toFixed(0)}s  (${(el / done).toFixed(2)}s/frame)`);
        }
      }
      await healthy(tab, 'after the last frame');   // an error event that fired after the final render(t)
      if (ff) { ff.p.stdin.end(); await ff.done; }
    }));
    if (A.boxes) {
      writeBoxes(boxes);
      console.log(`done → out/boxes.json (${TOTAL} frames, ${((Date.now() - started) / 1000).toFixed(0)}s)`);
    } else {
      const list = path.join(tmp, 'list.txt');
      fs.writeFileSync(list, segs.filter(Boolean).map((s) => `file '${s}'`).join('\n'));
      fs.mkdirSync(path.dirname(out), { recursive: true });
      const enc = ['-f', 'concat', '-safe', '0', '-i', list];
      let au = null;
      if (ALPHA) {
        enc.push('-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', '-r', String(FPS), out);
      } else {
        au = audioIn(f0, (f1 - f0) / FPS);
        if (au) enc.push(...au.args);
        // ffmpeg 9 takes color tags from the frames, so -color_* alone leaves primaries and transfer "unknown";
        // setparams stamps all three on the frames.
        enc.push('-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv',
          '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-c:v', 'libx264', '-preset', 'slow', '-crf', String(A.crf || 16), '-r', String(FPS), '-movflags', '+faststart', out);
      }
      await ffmpeg(enc).done;
      if (rec) writeBoxes(boxes);
      console.log(`done → ${out} (${((Date.now() - started) / 1000).toFixed(0)}s, ${ALPHA ? 'transparent, silent' : au ? 'with ' + path.relative(ROOT, au.file) : 'silent'}${rec ? '; out/boxes.json' : ''})`);
    }
  }
} catch (e) {
  console.error(String(e.message || e));
  process.exitCode = 1;
} finally {
  for (const b of opened) await b.close().catch(() => {});
  for (const p of procs) if (p.exitCode === null && p.signalCode === null) p.kill('SIGKILL');
  for (const f of junk) fs.rmSync(f, { recursive: true, force: true });
  server?.close();
}
