# Review and revision

The person who built the film can't see its flaws: they know what they meant, and their eye fills in the gaps. So the review goes to a clean context that **took no part in making it** (a helper agent, a fresh session or a headless run): its context holds only the film and the brief. The review then goes back to the builder for revision.

**If your agent can't start a helper**: the review still goes to a fresh context. Save the block below with its 【】 filled in as `check/评审提示-第N轮.md` and run it in a new session or a headless run of your agent's CLI (whatever starts a run that hasn't seen this conversation); have it write its review to `check/评审-第N轮.md`. If no fresh context is available at all, review it yourself looking only at the encoded film and `prompt.md` (not your code, not your notes), and put "not an independent review" at the top of `check/评审-第N轮.md`. Revision then works from that file. In the 10-06 test, the first review caught a climax that "looks like a rendering error"; after revision the average went from 5.6 to 7.1. In the 10-13 batch of 15 films, first reviews averaged 6.5, and the rounds went fastest where the review wrote each fix as a condition a script can check: the builder reported a measured number per condition, and the next reviewer only had to re-measure.

## The loop

1. The builder delivers the film and `check/报告.md`
2. Review (step 1 below) → `check/评审-第1轮.md`
3. Revision (step 2): the builder copies the current version to `versions/v1/`, revises, reports a number per condition
4. Round 2 is a full review again, opening with a check of every earlier fix
5. Another revision and review while any item is below 7 or anything is fatal. When the last revision only had to clear conditions, the review that follows is a short confirmation (template at the end)

## Step 1: review (give the block below to a clean context: a helper agent, a fresh session or a headless run)

Replace each 【】 with this job's paths and numbers.

```text
<role>
You are the reviewer of this film, not its author. You guard the visual quality of the user's channel, and you watch a lot of design-focused short video every day, so you know what makes a viewer stop and what reads instantly as a template. Your job is to find what stands between this film and "people who know design would share it", as specifically as possible, and to say what must change in a form the builder can measure. Politeness won't help the builder.
</role>

<context>
- Film: 【project folder/成片.mp4】 (for an overlay, 【透明.mov】 — view it over a dark and a light background)
- Brief: 【project folder/prompt.md】. <signature> is what makes the style recognizable, <specs> are the specs, and <context> says where it is used and who watches. If <task> quotes a prompt printed beside the film, viewers will check the film against that prompt line by line
- Size on the phone: the film is about 【620】 physical pixels wide on a viewer's phone (see <context> in prompt.md). Judge text, thin lines and small moves at that width; at full resolution everything looks fine
- Tools are in 【skill path/tools/】; run Python with ~/.venvs/mg-video/bin/python:
  - sheet.py 成片.mp4 out.png: one frame every 0.5 s; --around 3.2 gives every frame around that moment; --at 2,4.5 --width 【620】 gives frames at the embedded size; --at 3.6 --width 1920 --nolabel extracts full-resolution stills (without --nolabel a 26 px label strip shifts every y you read off the still); --crop x,y,w,h --zoom 3 for detail; --safe 0.05 draws the safe frame; --beats cues.json says how much each beat changes
  - spec.py 成片.mp4 --w --h --fps --duration --climax T --cues cues.json: specs, loudness, colour tags, edge reveal, motion in the end hold, where the loudest 0.4 s is (full-range and on a simulated phone speaker), the biggest frame-to-frame changes and the climax beat's rank
  - sync.py 成片.mp4 cues.json [--stems]: for each sound, how many ms the audio onset is off (unreliable within the first 0.1 s; "masked" means a louder sound buries it)
  - check.py (palette, hues, accents, drawings, flicker) and measure.py (margins, curve, colorfrac, overlap) measure with fixed definitions, so your numbers and the builder's can be compared. If the project has out/boxes.json (render.mjs --boxes), read positions from it instead of copying the camera into your own scripts
- Measure on the encoded film: extract stills from it. render.mjs --stills renders the code as it is now, which may no longer match the film. One exception: holes, slits and hairlines. H.264 4:2:0 leaves a 1–2 px colour edge where saturated colours meet, which a scan reads as an enclosed slit; check those on lossless frames (render.mjs --stills … --outdir check/评审-第N轮-图/无损, after confirming the still matches the film's frame), or ignore enclosed regions under 150 px on the film
- You may read the code in the project folder to find causes, but score only what you see and hear. In the project folder, write only under check/评审* (scripts in check/评审-第N轮-工具/, images in check/评审-第N轮-图/); everything else is read-only
</context>

<task>
1. Watch: look through the whole overview first, then make filmstrips for the fastest moves, every transition, and the climax; extract 5–8 full-resolution stills at key moments and zoom in (edges, type, aliasing, banding, things leaving the frame); then make one sheet at the embedded size
2. Prompt clauses (if <task> quotes a printed prompt): a table with every clause — each style item, the content sentence piece by piece, each "avoid" item — and the second(s) it is visible on screen (for "avoid" items, how it is avoided). A clause you can't point to on screen is a fatal problem
3. Measure: run spec.py and sync.py; does the loudest 0.4 s land on the visual climax, full-range and on the phone? Is the climax beat the biggest change apart from transitions and background swaps? Measure whatever the brief's <check> makes measurable
4. Score each of the eight items from 1 to 10. Anchors: 4 = has a hard flaw, can't be published; 5 = publishable but indistinguishable from online templates; 6 = better than a template, with one memorable moment; 7 = professional, no hard flaws; 8 = top of comparable accounts; 9–10 = the design community would share it. First drafts usually land at 5–7; score what you see, don't inflate to encourage
   - Recognizable: someone who knows motion design names the style within a second; is every <signature> item met?
   - Climax: is there one clear idea; a hook within 0.5 s; does the climax reveal something new; does the end frame hold up?
   - Motion: easing, rhythm, stagger, anticipation and follow-through, transitions; any dead spans, any jitter?
   - Layout: composition, hierarchy, alignment, type, palette, whitespace
   - Finish: texture, grain, light; any banding, aliasing, artifacts, stacked copies on a paused frame?
   - Sound: is the genre right, do effects line up with the picture, does the energy curve follow the picture, is it clear on phone speakers?
   - Specs: spec.py results, any fallback fonts, any flashing or skipped frames
   - Clarity (only if the film carries information): at the embedded size, can each screen's text be read in time, is the point clear at a glance?
   Deduct for each flaw only once, under the most relevant item: whether a <signature> item is present counts under "Recognizable"; how well it is executed counts under the matching item
5. Fixes, ordered by impact on the viewer, largest first: 5–10 in round 1; from round 2, only what keeps an item below 7 or a fatal problem unsolved (anything else is "optional, not required"). Each fix gives the timecode, what you observed, and why it matters, then 【condition】s the builder must meet and can measure, and 【example】s of one way to meet them, written as in "Writing fixes as acceptance conditions" in review.md. Fewer and bigger beats more and smaller; at least one fix must make the climax better, not just polish details
6. Before you send: check that all conditions can hold at the same time (path length ÷ speed ≤ time, safe margins, <signature>, the geometry, earlier rounds' conditions); give the priority order for conflicts; name the tool or attach the script that measures each condition. From round 2, add a regression table: conditions the current film already meets and must keep meeting
7. Fatal problems, listed separately: anything that looks like a rendering error on a paused frame, reads as a template at a glance, unnatural wording in the on-screen language, fallback fonts or missing-glyph boxes, failed specs, a printed-prompt clause not on screen, a recognizable brand logo or famous game sound, an on-screen fact or number without a source. If there are none, write "none" and say which you checked
8. For the user: list what only a human ear or eye can settle (does it sound like a famous tune, is the joke clear), with the machine measure you used in its place
</task>

<output>
Write the review in 【the user's language】 (the user reads it), in this order: score table → fatal problems → prompt clause table → fixes (conditions and examples) → regression table and priority order → for the user's ear or eye → one sentence each on the strongest and weakest points → skill issues (anything in the skill that was unclear or wrong; "none" if nothing). Save it as 【project folder/check/评审-第N轮.md】 and also give the full text in your reply.
</output>
```

## Writing fixes as acceptance conditions

A fix the builder can measure gets done in one pass; a fix that has to be interpreted gets done twice, often wrongly. Every dispute between builders and reviewers on 10-13 came from one of these gaps.

1. **Condition or example.** Mark every number. A 【condition】 must hold and is measured; an 【example】 is one way to get there and may be replaced. Put the result you want in the condition (where, how big, how fast, readable at what width) and the means in the example. "Rock the pencil ±4°" next to "its centroid moves ≤ 15 px/frame" contradicted itself (at an 8-frame period ±4° alone moves the centroid 21 px/frame) until the reviewer said ±4° was only an example.
2. **Time window.** Each condition names its frames or seconds (frame n = t × fps, counted from 0). Unless it says otherwise, a condition about motion or change doesn't cover the end hold (last 0.8–1.2 s) or the time viewers need to read the title: "every 2 s window shows ≥ 20 px of parallax" fought the still ending the brief asked for.
3. **Measuring window.** Say what is left out inside the window: "speed from each half-morph's first moving frame to the frame before landing; the landing frame is a deliberate one-frame impact" (24–46 px/frame there, ~15 elsewhere). Without it, builder and reviewer computed different ratios.
4. **Define the measure.** Resolution (full, half, embedded width), threshold, region and frames, or a tool whose definitions are fixed: `sheet.py --beats` counts a pixel as changed when any channel moves by more than 30 at half size and takes the maximum within the beat against its first frame (first-against-last reads 0% for a sway whose period divides the beat, and a builder added a 50 px drift to pass); `check.py drawings` counts a new drawing at more than 2000 px changing by more than 40 levels (x264 noise after a big change touches 300–500 px by more than 12). When you need a new measure, prefer the direct one: coverage ≥ 50% was a stand-in for "the climax fills the frame", and 47.3% held up at 620 px.
5. **Percentages state their base.** "Overshoot 12%" read as 12% of the travel collapsed the box to a point; write "12% of the settled width". Brightness "+15%" names its region and its reference.
6. **Colour is a share of pixels against a full palette.** Write "at frame 210, ≥ 85% of the pixels in (x, y, w, h) are within 30 (RGB distance) of the book's colours — its three faces and the highlight along its top edge — and < 1% are within 40 of the navy part". Never "the region's mean colour is within N of X": a region over two faces averages to a colour between them (32.9 against one face), and comparing it with the mean of its own pixels nearly proves itself (6.2). List every colour that belongs, edge highlights included; ~30 of tolerance covers anti-aliasing. Brightness is V measured on the film, not the shader's intensity (a light written as 0.42 came out at V 0.64).
7. **Encoded film, lossless for holes.** Conditions are measured on the film viewers get, except holes, slits and hairlines (see the review context). Encoder ringing also makes bright streaks 1 px wide and 20–30 px long: when counting dots or pen tips, require a core of at least 3 px in both directions.
8. **Name or attach the script.** Prefer the shared tools (`measure.py`, `check.py`, `spec.py`, `sync.py`, `sheet.py --beats`); otherwise put a script in `check/评审-第N轮-工具/` that prints value / limit / margin and PASS or FAIL per condition, runs on the film or on a folder of PNG test frames, and says how long it takes (the 3D review's `验收.py`: about 45 s on the film). Read positions from `out/boxes.json`, not from hand-copied camera maths or hand-picked coordinates, which go stale the moment the builder moves something. If a geometry change breaks your script, the builder keeps the original in `原版/` and lists every edit, and the next review checks that nothing was loosened.
9. **Check feasibility before sending.** On 10-13 four films were held up by a review's own numbers:
   - Path ÷ speed ≤ time: "retract the whole bike in 0.6–0.7 s" and "≤ 60 px/frame" on a 1,700 px path needs 87 px/frame; one of them had to give
   - Safe margins: "bounce up from 60 px below" put the first frame outside the 5% safe frame; 40 px fitted
   - The signature and the geometry: "8 columns, each flipping about its centre line" put the hinges on half-grid lines; a hop of 0.30 cells hit the shelf above; a window on the +x face was half hidden by the bookcase
   - Earlier rounds: round 3's "≥ 30% of each card shows light behind it" collided with round 2's "the other cards dim 20% at the climax"
   - What it might break: capping the climax's momentary loudness let the limiter and renormalisation lift the build-up, and the jump into the climax fell from 11.6 to 4.3 dB; the cap was dropped
   A regression table is feasible by construction (the current film meets all of it); conflicts hide in the new conditions.
10. **Priority order.** End the fixes with the order to follow when two conditions can't both hold. Default, highest first: (1) specs and the fatal list; (2) safe margins, overlaps, text size; (3) the style's structural conditions (one outline, no crossfade, palette); (4) beat and climax; (5) motion quality (speed, evenness); (6) change per beat, the end-hold move; (7) sound beyond the specs; (8) everything marked 【example】. Reorder for the film if needed and say why. A condition may carry a bounded allowance ("G2 may fail for at most 3 consecutive frames; beyond that, move the landing rather than give up G1"). If two conditions you didn't rank collide, the builder asks the user instead of choosing.
11. **Budget expensive renders.** For Blender, or anything over ~10 minutes, list the frames to re-render and the order: checks that need no render (the simulation) → about 20 test frames at 50% size and 16 samples → a short low-resolution preview of the moving parts → the full render only when everything passes. If two rounds of test frames still miss a condition by more than 10%, the builder stops and reports the numbers.
12. **Human ears and eyes.** A builder can't ask two people which game a sound reminds them of. Make the measurable substitute the condition (pitch sequence, intervals, waveform, spectrum; pixel counts, colour shares, outline area) and list, for the user, what still needs a person ("the sound score is from measurements only; please listen once").

### Worked example

Round-2 conditions for a 10-second shape-morph film (adapted from the 10-13 review to the shared tools; 30 fps, one beat = 16 frames):

| # | Condition | Window and measure | Now |
|---|---|---|---|
| R1 | One outline during each morph | frames 21–47, 101–127, 197–223 (landing frames 48, 128, 224 excluded); pixels within 120 of #FFD23F; connected areas ≥ 50 px: exactly 1 per frame | 1 |
| R2 | Inside the safe frame, overshoot frames included | every frame; `measure.py margins 成片.mp4 --color '#FFD23F' --tol 30`: x 96–1824, y 54–1026 | y 56–1023 |
| R3 | The climax is the biggest change | beat 14 (frames 208–224): `sheet.py --beats cues.json` max within the beat ≥ 30% and above every beat except background swaps; `spec.py --climax 7.4667` passes | 98.2% |
| R4 | Writing doesn't shake | frames 144–168: the pencil's centroid (`pencil` in `out/boxes.json`) moves ≤ 15 px/frame. 【Example】 rock ±2.3° about the tail | 13.1 px |
| R5 | Even speed | each half-morph from its first moving frame to the frame before landing: the two halves' peak speeds within 1.4×, all six within 1.6× | 1.15; 1.53 |
| R6 | The end moves | frames 264–299: the star's box width varies by ≥ 3% of its smallest width | 4.5% |

- Priority: R2 > R1 > R3 > R4, R5 > R6 > examples
- Feasibility: the round-1 example "±4°" alone breaks R4 at an 8-frame period, so it was only ever an example; "bounce up from 60 px below" breaks R2, so the landing starts 40 px below
- For the user: the sound score comes from measurements; please listen once

## Step 2: revision (send this back to the builder)

If your agent can still message the builder, continue it: it remembers its own code. Otherwise start a new builder (a helper agent or a fresh session) and give it `prompt.md`, the project folder path, and this block; if you built the film yourself, read this block as your own task.

```text
<context>
An independent reviewer has watched your film. The full review is in 【check/评审-第N轮.md】: average 【x】, lowest item 【item】. Its conditions are 【A–D / R1–R12】, measured with 【tools or check/评审-第N轮-工具/…】; its priority order is at the end of the fixes.
</context>

<task>
Raise the film, starting with the fatal problems and the lowest item:
1. First copy the current film and source to versions/v【N】/, so you can go back if a change makes it worse
2. Meet every 【condition】. 【Example】s are one way to get there: use them, or something you are confident is better, and say why. If a numeric example conflicts with a condition, with <signature> (grid, pivots, angles, palette) or with the film's geometry, follow the condition or the signature and say so. If two conditions can't both hold, follow the review's priority order and report the numbers; if a condition looks impossible, report the numbers instead of dropping it. Don't regress anything the reviewer praised or anything in the regression table
3. Measure every condition on the encoded film with the named tool or script, and look at stills and filmstrips until each fix actually shows on screen. Don't edit the reviewer's scripts; if a change of geometry breaks one, copy the original to 原版/ first and list every edit
4. Still in force: no multi-sample motion blur; never change the on-screen text or printed prompt quoted in <task> (you may append dated lines to Avoid in prompt.md); for a sound-only change, rerun audio.py and render.mjs --remux instead of a full render; for Blender, follow the review's render budget (test frames first). Rerun spec.py and sync.py at the end
</task>

<output>
Report in 【the user's language】: a table with each fix or condition → done / not done / done differently → the number measured on the encoded film, with frames, region and tool, so the reviewer only has to re-measure (one sentence on why for anything not done or done differently); the regression table re-measured; what weaknesses remain; how long this round took; anything in the skill that was unclear or awkward to use (write "none" if nothing).
</output>
```

## Round 2 and later

**Round 2 is a full review.** Reuse the review prompt and add a step before step 1 of `<task>`: first read `check/评审-第【N-1】轮.md` and mark each previous fix and fatal problem as done / not done / done differently (for "done differently", say whether the new solution works), then rescore, with the previous round's scores in the table for comparison. The previous reviewer can continue (it remembers what it flagged), or start a new one; a new one reads the previous `check/评审-第【N-1】轮.md`.

**A confirmation round is short.** Use it when the last revision only had to clear conditions. Send the reviewer the role and context from step 1 with this task and output:

```text
<task>
This is a confirmation, not a full review. The previous version is in versions/v【N-1】/.
1. Re-measure every condition in check/评审-第【N-1】轮.md, new and regression, on the encoded film, with the shared tools or your own script, not with the builder's numbers. If the builder edited your scripts (originals in 原版/), check that no condition was loosened
2. Regressions: diff the two films frame by frame; changes should appear only where the fixes are. Look at every changed area, and judge each weakness the builder flagged in its report
3. Re-check the fatal list (printed-prompt clauses, anything that looks like a rendering error, fonts, specs, unsourced facts, brand logos)
4. Rescore, with every earlier round's scores beside the new ones
</task>

<output>
In 【the user's language】, in this order: verdict (passes: every item ≥ 7 and nothing fatal / doesn't pass yet, and what is left) → a table: condition | requirement | builder's number | your re-measurement | result → script changes checked → regressions and the builder's flagged weaknesses, each judged acceptable or a fix → score table → fatal re-check → remaining fixes as conditions ("none" if none; optional ones marked "not required") → skill issues. Save it as check/评审-第N轮.md and also give the full text in your reply.
</output>
```

## How many rounds

By default one review and one revision. Another round while any item is below 7 or anything is fatal; once every item is at least 7 and nothing is fatal, the film passes, and optional suggestions don't trigger another round. When a condition fails twice, check the condition (feasibility, window, definition) before asking for another revision. Each round's review stays in `check/`, so the user can see how the scores moved.
