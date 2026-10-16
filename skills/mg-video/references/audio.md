# Music and sound effects

Audio comes from `tools/mgsound/`, our own library: every note and effect is synthesized with numpy/scipy (no samples), so the same script always produces the same sound, and a 10-second mix renders in about a second. This page covers how to use it in this workflow; the docstrings in each module are the full reference.

## Environment

Run `bash <skill>/tools/setup.sh` once; it installs to `~/.venvs/mg-video` (Python 3.13). Then, in the project folder:

```bash
~/.venvs/mg-video/bin/python -I audio.py      # → out/audio.wav, out/stems/music.wav, out/stems/sfx.wav
```

`render.mjs` picks up `out/audio.wav` automatically; when only the sound changed, `render.mjs --remux` puts it on the existing film.

## Workflow

1. **Beat sheet first**: `cues.json` (the template's `audio.py` places everything in it) has three parts. `"music"`: the `music.bed()` settings, `{"bed": "explainer", "bpm": 112.5, "drop": 6.5, "outro": 9.0}` (drop = the climax, outro = start of the end hold); any other `bed()` option (`levels`, `pickup`, `end`, `key`, `prog`, `flavor`) can go there too; `"bed": null` for clips that deliver only the effects stem. `"events"`: picture events with a sound, each checked by sync.py: `{"id", "t", "sfx": "pop", "args": {…}, "gain", "pan"}`; `"times": [t1, t2, …]` plays it at every time; `"sfx": [{"name": "impact", "args": {…}}, …]` layers several sounds. `"motion"`: whooshes, risers, swells, pen strokes (no sharp onset), same keys, played but not sync-checked. Picture and `audio.py` read the same file; change timings only there
2. **Pick the tempo**: a beat should be a whole number of frames, so every beat lands on a frame. At 30 fps: 150 BPM = 12 frames, 112.5 = 16, 90 = 20, 75 = 24 (multiples of 4 frames put every 16th note on a frame too); 120 = 15, 100 = 18, 138.46 = 13. Most bed defaults aren't (explainer's 112 is 16.07 frames: use 112.5). Then put the key events on bar lines (bar = 240 / BPM s, counted back from the drop); the HUD film in the October 2026 test batch (15 films, one per card) picked 97.3 BPM so the scan, the lock and the touchdown all fell on bar lines
3. **Pick a bed**: the style card's Sound line names one. `music.bed(m, style, drop=…, outro=…)` lays an arranged backing track with a bar line exactly on `drop` and returns the form (`bpm`, `beat`, `bar`, `build`, `drop`, `outro`); see "Beds" below
4. **Choose the bus**: an event without `"bus"` is a hit: `m.sfx(sound, at=t)` registers it as a cue and ducks the music `duck_db` (3 dB) under it. `"bus": "sfx"` (in code `m.add(sound, at=t, bus='sfx')`) places it on the effects bus without ducking: use it for runs of small hits (typing, ticks), which otherwise make the music pump (or set `Mix(…, duck_db=2)`). `motion` entries always go there. Accents and sustained sounds added by hand in `audio.py` go on `bus='sfx'` as well: `m.add` defaults to the music bus, and `"bus": "music"` mixes a sound into the bed, which is normalised as a whole (see "Limiter"). Pass the picture's time; each effect knows its own sync point: hits sync on the attack, whooshes on the pass-by, risers / swells / lock-ons on their end
5. **Export**: `m.export('out/audio.wav', stems_dir='out/stems')` masters to -14 LUFS with a -1.5 dBTP ceiling (AAC raised true peak by about 0.6 dB in testing: -1.2 in the master, -0.6 in the MP4), and prints what the master limiter took (see "Limiter")
6. **Energy follows the picture**: the loudest 0.4 s should be the visual climax, full-range and on a phone speaker (`spec.py --climax`). Shape the music bus with `m.music_gain([(t, dB), …])`: push the climax a little, pull the hold down, and keep sound under the hold (see "Endings"). Mind the normalisation (see "Limiter")
7. **When the picture pauses, the music makes room**: a breath before the climax with the music playing on at full level reads as "stuck". Close a filter over the pause with `m.music_lpf([(t, Hz), …])`; with a four-on-the-floor bed the kick sits below any cutoff, so mute the whole beat with `m.mute(at, dur)` and leave only a riser tail

## Hitting the frame

- Check alignment with `~/.venvs/mg-video/bin/python -I <skill>/tools/sync.py 成片.mp4 cues.json`. Onset detection is calibrated to about ±3 ms. Events in the first 0.1 s can't be measured (no lead-in), so don't move a sound because of that number
- **Four-on-the-floor beds** (pop, techno, darksynth) put a kick on every beat, so a missing or late hit on a beat still measures 0 ms on the mix: also run `sync.py --stems`, which measures on `out/stems/sfx.wav`
- **Soft onsets don't measure**: `squeak` (10 ms sine attack), a low `boing` or `gloop`, any swell; layer a short transient (`pop`, `tick`, `click`) under them so the landing has an onset. `sparkle` starts its notes at random, so it can't be a sync point: use `chime`. A hit 0.5–1 s after the climax sits in its tail and reads as `masked`: give it about 4 dB more
- No more than 3 effects on one frame. Repeated UI sounds get a little pitch variation (`sfx.pop(pitch=1 + 0.06 * i)`) and pan with the object (`pan=` -1…1)
- A whoosh's `dur` ≈ the object's travel time on screen; `direction=1` moves left → right
- For a run of sounds that follows eased motion (a ratchet, a counter), place each at the time the picture reaches that step: the template's `io2_inv(y)` inverts the `io2` easing

## Beds

Chords count back from the drop: bar k (k = 0 at the drop, negative before it) plays chord k mod n of `prog`, so the drop and the ending play `prog`'s first chord. **Start `prog` on the tonic.** `lofi` (ii7) and `future_bass` (IVmaj7) don't by default and end unresolved: pass e.g. `prog='Imaj7 V vi7 IVmaj7'`. The minor beds (techno, synthwave, darksynth) land on the minor tonic; for a success, start `prog` with an upper-case `'I'` (major), as the HUD film did with `'I i i II VII'`. Override `bpm`, `key`, `prog` per job; any duration works.

What each bed already plays (build = the bar before the drop; the ending is described under "Endings"):

| Bed | From 0 | From the build | From the drop | Cards |
|---|---|---|---|---|
| `explainer` | warm pad, marimba arpeggio (8ths) | + shaker | + soft kick (1, 3), rim (2, 4), sub bass on every beat | paperclip, isometric |
| `pop` | warm pad, plucked chords | + hats | kick on every beat, claps, saw bass, supersaw chords instead of the pad; **riser into the drop, crash on it** | flat vector, 3D |
| `future_bass` | warm pad, pluck arpeggio | – | chopped supersaw chords, 808, snare, hats; **riser into a half-beat gap of silence before the drop** | liquid, morph |
| `techno` | offbeat hats, dub stabs | + kick on every beat | + claps, offbeat sub bass | Bauhaus |
| `ambient` | pad, glockenspiel arpeggio; `flavor='glass'` glass pad, `'piano'` piano | – | `'product'` only: soft kick every half bar, shaker | glass, one line, 3D |
| `lofi` | vinyl, swung e-piano chords (`keys='piano'`) | + hats | boom-bap kick (`flavor='boombap'`), snare, sub bass | cel boil, collage |
| `variety` | plucked chords (`flavor='cute'`: kalimba), plucked bass on root and fifth | + shaker | + kick, claps, glockenspiel | variety captions |
| `synthwave` | 80s pad, pluck arpeggio (16ths) | + hats | + kick, gated snare, saw bass; **riser into the drop, crash on it** | synthwave |
| `darksynth` | dark pad, square arpeggio (phrygian) | + gritty 16th bass | + kick on every beat, snare | HUD |
| `chiptune` | square arpeggio (16ths), triangle bass | + noise hats | + chip kick and snare | pixel |

Don't add a second riser or crash where the bed has one. Every bed except ambient puts most of the drop's energy below 150 Hz (kick, sub, 808), which a phone barely plays and which trips the master limiter: the climax needs a 1–4 kHz layer of its own (see "Limiter").

`music.bed()` options:
- `levels={'kick': -6, 'arp': -99}`: dB added per layer, -99 mutes it. Layers: `kick`, `snare` (with clap, rim), `hats` (with shaker), `bass`, `chords`, `pad`, `arp`, `riser`, `crash`, `vinyl`, `end` (the ending); a single role such as `'clap'` also works. The music bus is normalised afterwards, so turning one layer down brings the rest up
- `pickup=True`: the grid counts back from the drop, so the first bar line is rarely at 0 (75 BPM with the drop at 7.0: 0.6 s with no chord). With pickup, the chords and bass notes that began before 0 sound from 0 for the rest of their length
- `end='hold' | 'pulse' | 'stop'`: see "Endings"

**Custom arrangements** (chords that change on picture events, a groove that stops dead, a bed with different parts): build on a `music.Form(duration, bpm, drop, outro, chords)` with the helpers `bed()` uses: `music.pattern(m, f, role, make, '16-step pattern', t0, t1)`, `music.bassline(…)`, `music.chords(…)`, `music.arp(…)`, `music.crash(m, at, gain=…, bus=…)`, `music.vinyl(m, f)`; `music.LEVEL` holds their default dB per role (the old underscored names still work). Chords that change off the bar lines: place them directly, e.g. `m.add(inst.pad(theory.chord('V', 'D'), t1 - t0, 'warm', 0.6), at=t0, gain=music.LEVEL['pad'])` per span. Instruments are in `mgsound.inst` (`kick`, `snare`, `clap`, `hat`, `crash`, `bass`, `mallet`, `epiano`, `piano`, `pluck`, `pad`, `supersaw`, `stab` with `kind='dub'|'bright'`, `lead`); notes are names or MIDI numbers, never Hz (`inst.bass(hz('D2'))` raises). The music bus is for the bed; one-off accents on it change its normalisation, so put those on `bus='sfx'`.

### Bring your own music track

To use a track from elsewhere instead of a bed: set `"bed": null` in `cues.json`, render or obtain a 48 kHz WAV at the film's BPM (step 2 above: a beat on a whole number of frames) with a bar line on the climax, put it in the project (e.g. `assets/music.wav`), and load it onto the music bus in `audio.py`, right after `m = Mix(...)`. Shape it with `m.music_gain` and `m.music_lpf` as for a bed.

```python
import soundfile as sf
from mgsound.core import Sound
x, sr = sf.read(os.path.join(HERE, 'assets', 'music.wav'), always_2d=True)
assert sr == 48000
m.add(Sound(x.T), at=0, bus='music')
```

## Endings

`outro` is the start of the end hold: put it on the picture's last small move, not on a time chosen for the music. The ending must stay below the drop, and the hold must not go silent: a chord that decays to nothing in 0.8 s reads as dead air on a frozen frame (pop bed, 10-13).

- `end='hold'` (default): the first chord of `prog` rings from the outro to the end, with a soft kick. Watch `techno` and `darksynth`: their ending pad is low-passed at 600 Hz and inaudible on a phone; add a mid-register chord
- `end='pulse'`: the same chord under a light pulse that fades out (the style's arpeggio; hats for `techno` and `lofi`), for pictures that keep breathing in the hold
- `end='stop'`: nothing from the outro on; bring your own ending (a closing chord on the last event, built with `inst`) or let the effects carry the hold
- "Groove, dead stop at the climax, closing chord": lay the bed, then `m.mute(drop, outro - drop)`; the ending still comes in at the outro

## Limiter

The master sums the two buses, high-passes at 25 Hz, normalises to -14 LUFS and runs a look-ahead limiter at -1.8 dBTP, repeating until both targets hold. Whenever a peak would cross the ceiling, the limiter pulls the whole mix down at that moment, and the renormalisation then lifts everything else. So the climax ends up at about the ceiling minus its own crest factor: making it louder or spikier doesn't help, and a hit whose peaks are low end (`impact('cinematic')`, `sub_drop`, the 808, the drop's kick and bass) pulls its own bright layers down with it. In the test batch this came up seven times: 6–13 dB of reduction on such hits, and a 6–10 dB lead on the stem shrank to 0.1–0.6 dB in the master.

`export()` reports it, e.g. a pop bed with `impact('cinematic')` at +4 dB on the climax:

```
[mgsound] limiter: max -5.8 dB at 3.601 s; climax 3.000: -5.3 dB peak, -3.9 dB over its first 0.4 s
[mgsound] limiter at cues: 1.500 -0.7 | 3.000 drop -5.2 | 5.000 outro -2.5  (1 more under 0.5 dB)
```

"Over its first 0.4 s" is the loss of momentary loudness (K-weighted, as in LUFS); above 3 dB it prints a note, not a warning: re-rendered on 10-13, 11 of the 12 films in the test batch that had a known climax lost 3.4–12.2 dB there and still passed `spec.py --climax`. The number explains why pushing a hit louder only feeds the limiter; the pass/fail test stays `spec.py --climax`. Cues default to the `m.sfx()` hits and the bed's drop and outro; pass `cues='cues.json'` for labels and `climax=T` when the climax isn't the bed's drop. The numbers are in the returned `rep['limiter']`, and `m.limiter_report()` gives them after `m.render()`.

What helps:
- **Weight in 1–4 kHz**, not below 150 Hz: a bright or saturated chord, clap and snare, a metallic clang, a 3 kHz click. Give the impact a high-pass around 45 Hz (`.hpf(45)`), turn the bed's low end down with `levels={'kick': -6, 'bass': -6}`, or thin the music bus with `Mix(…, music_hpf=60)` (or `[(t, Hz), …]` from some moment on)
- **Dense, not spiky**: a saturated chord or a 0.3–0.4 s bright ring keeps its loudness at a low crest factor; a single transient gets shaved off
- **Short tails**: `sound.tail(hold, decay)` keeps a sound for `hold` s after its sync point, then fades it to -60 dB over `decay` s and cuts it there
- Same test as above with the hit as a bright supersaw chord on `bus='sfx'`, the bed's kick and bass at -6 and `music_hpf=60`: 2.9 dB lost, no warning

**To lower the climax's peak loudness** (a cap on momentary loudness) without losing the jump into it: turn the build-up down first (its drums and low end) and let the master renormalise. Never thin the climax: the limiter then holds it in place while the renormalisation lifts the build-up (the test batch's morph film: the jump from the build-up into the climax fell from 11.6 to 4.3 dB, on a phone from 14.0 to 6.7). Re-check that jump after mastering; `spec.py --climax` prints it.

**The music bus is normalised too**, to `music_level` (-20 LUFS) before `music_gain`, `music_lpf` and mutes. A loud chord added to the music bus at the climax pulls the rest of the bed down (by 16 dB over the first 7 s in the isometric film); a layer turned down with `levels=` or `music_hpf` brings the others up. Set the bed's overall level with `music_level` or `music_gain`, and put accents on `bus='sfx'`. Don't assemble already-mastered stems with `Mix` (it renormalises them): use `place`, `limit` and `lufs` from `mgsound.core` / `mgsound.mix`.

## Clips embedded in a talking-head episode

The episode has its own music, sitting about 15 dB under the voice; a second music bed in the clip would fight it. So:

- Embedded clips deliver **only the effects stem**: `out/stems/sfx.wav`, at the master's gain before the limiter. Each stem file is scaled down on its own if it peaks above -1 dBFS, so don't compare levels between the two files; `x, stems = m.render()` gives both at one scale. Set the stem's level against the voice in the episode project
- Openers and standalone shorts use the full `out/audio.wav`

## Effects

All effects are normalized to one loudness, so at `gain=0` they sit together; use `gain` for intent (-6 subtle, +2 hero). A `Sound` also has `.gain()`, `.pan()`, `.hpf()`, `.lpf()`, `.reverb()`, `.fade()`, `.tail()`, `.reverse()`.

| Family | Functions |
|---|---|
| UI and small hits | `pop(pitch)` `click(kind='soft'|'hard'|'switch')` `tick(kind='wood'|'hi'|'clock')` `blip(note, wave)` `ding(note)` `chime(notes)` `sparkle(dur)` `shimmer(note)` |
| Motion | `whoosh(dur, kind='air'|'swish'|'sci'|'heavy', direction)` `swish(dur)` `riser(dur)` `swell(dur)` `downlifter(dur)` |
| Hits | `impact(kind='soft'|'punch'|'cinematic')` `sub_drop(dur)` (both mostly below 150 Hz: layer a bright hit on top) |
| Paper and desk | `sticker_slap()` `paper(kind='rustle'|'flip')` `pen(dur)` `tape_rip()` `scissors()` `stamp()` `typing(keys, rate)` |
| Cartoon | `boing(pitch)` `duang(pitch)` `slide_whistle(up, dur)` `squeak()` `record_scratch()` |
| 8-bit | `coin(note)` a metallic "ting" `jump()` `powerup()` `oneup(transpose)` |
| Glass | `glass(kind='clink'|'cluster', pitch, count, spread)` around 3 kHz |
| HUD | `hud_beep(note)` `hud_scan(dur)` `hud_data(dur)` `lock_on(dur)` `hud_open()` `hud_alert()` `laser()` |
| Liquid | `drip(pitch)` `gloop(pitch)` `splash(size)` `bubbles(dur)` `morph(dur, up)` |
| Retro media | `vhs_noise(dur)` `static(dur)` |

`sfx.pen` is a fixed-length one-shot. A sound that follows the picture (a pen whose loudness tracks the nib's speed) is built in `audio.py` from band-passed `core.noise` shaped by a level curve exported from the page, and placed with `bus='sfx'`.

### Game-like sounds: check the motif

Famous game sounds are recognized by interval, rhythm and timbre, so a transposed copy is still a copy. Until 10-13 `coin` and `oneup` copied a famous game's coin and extra-life sounds note for note. Before shipping a reward or fanfare, write out its pitch sequence and rhythm and compare them with:

| Avoid | Notes | Shape |
|---|---|---|
| a coin | old `coin`: square, B5 (60 ms) → E6 held | a very short note leaping up a perfect fourth (+5) into a held note |
| an extra life | old `oneup`: square, E6 G6 E7 C7 D7 G7, 80 ms each | +3 +9 −4 +2 +5, even notes |
| a level-clear fanfare | G C E G C E G… rising | a major triad climbing from the dominant |

`powerup` (C5 E5 G5 C6 E6 G6 C7, 60 ms each, square) is a plain arpeggio from the tonic; don't start it on the dominant. The current motifs: `coin` is one FM-bell strike that reads as a single pitch (C7) from its first 10 ms and rings about 0.35 s, then three faint glints falling +12, +9, +7 semitones above it (long, short, short, short); `oneup` climbs in broken thirds, A5 C6 B5 D6 C6 E6 at 40 ms each, takes a breath, then D6 into a held E6 with vibrato (+3 −1 +3 −2 +4 −2 +2).

Check the stem, not just the effect, around each hit (±0.2 s), since the gesture can form across layers (the test batch's pixel film: an arpeggio's last note G6 into a bell's C7, a fourth). Take the strongest peak between 300 and 5000 Hz in 25 ms windows and read off the MIDI numbers (69 = A4; a difference of 5 is a fourth):

```python
import numpy as np; from mgsound import analyze
x = analyze.load('out/stems/sfx.wav').mean(0); T = 6.4; w = 1200            # hit time; 25 ms at 48 kHz
for a in range(int((T - 0.2) * 48000), int((T + 0.2) * 48000), w // 2):
    S = np.abs(np.fft.rfft(x[a:a + w] * np.hanning(w), 16384)); f = np.fft.rfftfreq(16384, 1 / 48000)
    k = np.argmax(S * ((f > 300) & (f < 5000)))
    print(f'{a / 48000:.3f}  midi {69 + 12 * np.log2(f[k] / 440):5.1f}  {20 * np.log10(S[k] + 1e-9):5.0f} dB')
```

A bell reads at its loudest partial, so check the shape (a short low reading, then a long high one) as well as the numbers. What only an ear can settle goes on the review's list for the user.

## Limits

The beds are short, simple arrangements meant to sit under 5–30 seconds of motion; they don't replace a composed track. For a longer piece with a real song, use any music source (see "Bring your own music track") and still place the effects with `m.sfx`.
