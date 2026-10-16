# Production prompt: template and two filled examples

Save it as `prompt.md` in the project folder. It has two readers: the user (reviews and edits it) and the builder — a subagent, a separate session, or you in a fresh context (it has not seen your conversation, so the prompt must be complete).

## Why these blocks

Following Anthropic's prompting guidance: XML tags keep background, requirements, and checks from blurring together; a reason on each instruction lets the model generalize to cases you didn't write down; quality beyond "it works" has to be asked for explicitly; and patterns to avoid must be named concretely (a vague "don't make it look AI-generated" just swaps one default for another).

Four blocks are written fresh for each job; three come from the style card:

| Tag | Source | Contents |
|---|---|---|
| `<role>` | written each time | who builds it and what they care about most |
| `<context>` | written each time | where it is used, how big it is on the phone, who watches, what they should remember, where the files are; phrased as "because …, so …" |
| `<task>` | written each time | what it says, and a beat sheet in seconds (hook, build, climax, ending) |
| `<specs>` | written each time | size, frame rate, duration, audio, licensing, sources for on-screen facts, what the builder may and may not edit |
| `<signature>` | style card, unchanged | what makes the style recognizable; the review scores against it, and it survives any change of subject |
| `<style>` | style card, adapted | recommended build, palette, beat skeleton, sound, avoid list; swap in this job's subject and colors. The builder appends to the avoid list as it learns |
| `<check>` | generic items + style card | the generic items in the template below, plus the style card's common failures |

Write the prompt in English. On-screen text stays in the film's language (Chinese in the examples below): put the exact copy in the prompt, in quotes, and say it is on-screen text.

When a prompt is printed beside the film (a compilation that shows its prompts), quote it verbatim in `<task>`, say that the film must visibly do every item in it, and say that it wins over the style card wherever they differ. On 10-13 a card allowed two kinds of transition, the printed prompt named one, and the builder did the other. If the card makes an exception the printed prompt doesn't (24 drawings/s for fast action, say), either print the exception or drop it.

## Template

````text
<role>
You are the motion designer for this film, and the code and sound are yours too. You care most about two things: anyone who knows motion design should recognize 【style name】 within a second, and every movement should say something rather than move for its own sake.
</role>

<context>
- Where it is used: 【the B-roll for the line "……" in episode N / an opener / a standalone short / a transparent overlay on the talking-head footage / one film in a compilation】
- Size on the phone: 【it fills the width of a portrait phone, about 1179 physical px / it plays as a 1340×754 card in a 2560×1440 frame, so on a portrait phone it is about 620 physical px wide (the film scaled ≈ 0.32×)】. So text, the subject, thin lines and small moves must read at that size; check with tools/sheet.py --at … --width 【620】
- Who watches: 【the audience described in the brief, e.g. people who already use, or are about to use, AI agents for real work】, scrolling on a phone. So keep one point per screen and type large, and something must move within the first 0.5 s, or they swipe away
- What they should remember: 【one sentence】
- Files: project folder 【path】; style card 【skill path/styles/xx.md】; techniques 【skill path/references/techniques.md】; music and sound 【skill path/references/audio.md】
- The user likes / doesn't want: 【their words; delete this line if none】
</context>

<task>
Make a 【N】-second 【style name】 piece about 【content】. The bar is portfolio quality, not "good enough".
【Only when a prompt is printed beside the film:】 This is the prompt viewers see printed beside the film (approved by the user; do not change it). The film must visibly do every item in it, and it wins over the style card wherever they differ — viewers will check:
```
【the printed prompt, verbatim】
```
Before building, list each clause → the beat that shows it → the second; a clause you can't place is a problem to raise now, not at the review.
Beat sheet (timings are suggestions; adjust them):
- 0–0.5 s hook: frame 0 already shows the subject (half-built is fine); 【……】
- 【……】 build: one new element per beat
- 【at N s】 climax: 【……】 — the subject becomes complete here for the first time
- the beat after the climax: an aftershock 【……】, so the film doesn't freeze straight after the hit
- last 0.8–1.2 s: hold the end frame with one small move that is visible at 【620】 px wide: 【……】
You may change the idea, the copy, and the beats, as long as the result is still the classic, instantly recognizable form of this style and every item in <signature> is met.
On-screen text (use exactly): 【"……"】
</task>

<specs>
- 【1920×1080】, 【30】fps, exactly 【N】 s; H.264 MP4, stereo AAC 48 kHz, -14 LUFS integrated, true peak ≤ -1 dBTP
  (for an overlay on the talking head: transparent ProRes 4444 with no audio, plus the effects stem out/stems/sfx.wav)
- Everything is drawn in code; follow the page contract in the skill's tools/template/index.html (each frame depends only on t)
- No multi-sample motion blur (motionBlur.samples and --mb stay 1): viewers pause, and averaged sub-frames show on a paused frame as stacked copies and soft bands that look like a rendering error. Show speed with solid smear frames and speed lines; if the style needs real blur, use adaptive in-page sub-frames (references/techniques.md, "Motion blur")
- Text: 【≥ 48】 px font size (for Chinese the floor is about 16 physical px on the phone: 48 px for a 1920 film on a 620 card, 35 px for a 2560 film that fills the phone width); brightness targets are V measured on the encoded film, not shader values
- Assets only under CC0 / public domain / OFL / commercial-use licenses, with source and license recorded in CREDITS.md; no real brand logos; no famous game sounds, even transposed; no AI-generated human faces
- On-screen facts and numbers have sources
- 【If other builders share the machine:】 full renders with --workers 2 at most, previews at --scale 0.5, never two GPU-heavy renders at once
- Edit only inside the project folder (to change a shared tool, copy it into the project and say so). Never change the on-screen text quoted in <task>; you may append dated lines to Avoid in <style> with what your drafts and reviews taught you. If a clause can't be met, report it instead of dropping it
- Write your report in 【the user's language】; the user reads it
</specs>

<signature>
【paste the style card's <signature> unchanged】
</signature>

<style>
These are recommendations, not rules. If you find a better approach, use it and explain why in your report.
【the style card's <style>, with subject, colors, and beat skeleton adapted to this job; add this job's fonts and the reason for them; extend "Avoid" with what the user doesn't want and any default pattern the first draft fell into】
- Avoid (added by the builder, 【date】, 【round】): 【the builder appends lines like this; nothing else in the prompt changes】
</style>

<check>
Check each item when done; fix anything that fails before handing over. Report each with the number measured on the encoded film, the frames, and the tool:
- 【Only when a prompt is printed:】 a table with every clause of the printed prompt (each style item, the content sentence piece by piece, each "avoid" item) → the second(s) it is visible; a clause you can't point to on screen is a fatal problem
- tools/spec.py passes with --climax: the loudest 0.4 s lands on the visual climax, full-range and on the simulated phone speaker; no edge reveal; the end hold moves
- Stills at 6–10 key moments each stand on their own: composition, hierarchy, whitespace, letter spacing, punctuation (full-width in Chinese), ≥ 5% margin from the frame edge; text readable at the embedded size (tools/sheet.py --at … --width 【620】)
- Margins and overlaps hold on every frame, overshoot frames included, not only on settled stills (tools/measure.py margins, overlap)
- Filmstrips (tools/sheet.py --around) for the two or three fastest moves, every transition, and the climax: no empty frames, skipped frames, stacked copies, elements leaving the frame, or parts flying off
- List the second at which each <signature> item shows up; in a compilation each also shows outside the first and last 0.5 s, which the transitions cover
- Frame 0 shows the subject; the nouns that set the scene are still recognizable in the last second (viewers pause on the end)
- Every visual hit lands on a sound onset (tools/sync.py); no more than 3 sound events on one frame (a layered hit designed as one sound counts once)
- No typos, missing-glyph boxes, or fallback fonts
- 【the items from the style card's <check>】
</check>
````

Infer whatever the user didn't say from the request; ask about what you can't infer. Replace every 【】 and delete lines that don't apply.

Rules for the beat sheet in `<task>` (in the 10-06 test all three of the review's biggest deductions came from the beat sheet; the 10-13 batch added the rest):

- **The climax reveals something**: the subject (the number, the phrase, the logo) becomes complete only on the climax. If it is already assembled and the climax just adds a background or an effect, the viewer has no reason to say "wow". Whatever gets filled in must look empty before, at the embedded size (a dark slot, an outline, a contrasting colour). The climax beat should be the biggest change on screen apart from transitions and background swaps: in one first draft it changed 2.7% of the frame, less than two build-up beats.
- **One action per beat, said plainly**: if two things land together on the climax, say in the prompt that this is the only beat where that's allowed, or phrase it as one action ("the ball drops in and flips 「3 分」 over").
- **Where the climax goes is the brief's call**: 60–75% is a default when nothing else decides it; a story, footage or a printed prompt may put it at 45% or 36%. Fill the time after it.
- **The subject is on screen at frame 0**: on short-video platforms frame 0 often doubles as the cover, and in a compilation it is where the film opens out of the transition; faint grid lines and hairlines read as blank on a phone. Half-built counts (an isometric scene can start with its subject half grown).
- **Signature items get screen time**: none of them only in the first or last 0.5 s, which compilation transitions cover.
- **The ending holds but isn't dead**: the beat after the climax carries an aftershock event (one film stood still for 2 s after its landing), and the small move in the last 0.8–1.2 s is visible at the embedded size (`spec.py` reports the largest move in the last 1.2 s scaled to a 620 px card and warns under 2 px); the music resolves there instead of peaking there.

## Checks the builder can measure

Write requirements in `<task>`, `<specs>` and `<check>` the way a review writes conditions (`references/review.md`, "Writing fixes as acceptance conditions"): what, in which frames, measured how, against what threshold. A requirement that has to be interpreted gets built one way and reviewed another:

- Text size as font size in px ("≥ 48 px"), not "text height": a glyph's ink is about 0.9 of the font size, and 一 or 二 never reach any ink height
- Brightness as V measured on the encoded film; a value in the shader isn't what reaches the screen
- Durations as seen on screen, not as written in `cues.json`: a 1.0 s light sweep spent 0.5 s on the glass it crossed, and a 0.7 s fade-in showed as 0.17 s
- Colours as shares of pixels against the full palette, with ~30 of tolerance for anti-aliasing
- Every line width, size or count the prompt states is one the card's tricks can't override (a card's "thick start for thin lines" against a prompt's "1–2 px lines")

## Example 1: paperclip sticker style, a B-roll segment inside a talking-head video

```text
<role>
You are the motion designer for this film, and the code and sound are yours too. You care most about two things: anyone who knows motion design should recognize the paperclip-style sticker explainer within a second, and every movement should say something rather than move for its own sake.
</role>

<context>
- Where it is used: a talking-head episode about "what Claude Code actually does after you type one sentence". It is the full-screen B-roll right after the presenter says "it actually goes through five steps"
- Size on the phone: the landscape episode fills the width of a portrait phone, about 1179 physical px (the 2560 frame scaled ≈ 0.46×), so the terminal text and the stop labels must read at that size
- Who watches: developers who already use, or are about to use, Claude Code, scrolling on a phone. So keep one point per screen and type large, and something must move within the first 0.5 s
- What they should remember: one sentence goes in, and Claude Code reads files, makes a plan, edits code, runs tests, and reports back — it is a loop
- Files: project folder films/five-steps/; style card <skill>/styles/01-paperclip-sticker.md; techniques and sound docs in <skill>/references/
</context>

<task>
Make a 12-second paperclip sticker piece about Claude Code's five-step loop. The bar is portfolio quality, not "good enough". Beat sheet:
- 0–0.5 s hook: a terminal-window sticker slaps onto the center of the table, its cursor blinking, and types a request
- 0.5–9 s the camera travels across the big canvas through five stops, each adding one sticker and one leader-line label: read files (a folder sticker, file names popping out one by one) → plan (a sticky note, three plan items ticked) → edit code (a code-snippet sticker, red deletions and green additions) → run tests (a progress bar fills, the counter reaches 12/12) → report (a chat bubble)
- around 9 s climax: the camera pulls back, and an arrow draws out connecting the five stops into a closed loop — the loop exists only from this moment — with large type in the middle
- 10.8–12 s hold: the whole loop plus one small caption at the bottom; a dot of light travels slowly around the arrow
On-screen text (Chinese, use exactly): the request "帮我修一下登录页的 bug"; stop labels "读文件" "想计划" "改代码" "跑测试" "汇报"; the climax type "一个循环"
</task>

<specs>
- 2560×1440, 60fps, exactly 12 s (matching the talking-head master); the terminal text matches the real Claude Code interface — don't draw features it doesn't have
- Embedded in the talking head, whose music carries the scene: render a silent MP4 and deliver the effects stem out/stems/sfx.wav separately
- Everything else as in the template
</specs>

<signature>
- One table, one camera: everything sits on a canvas several times larger than the frame, and the camera only pans and zooms — no cuts. Viewers always know they are on the same table, so where things sit tells them what relates to what.
- Real objects are stickers: each cut-out photo gets the same white border (about 4% of the sticker's short side, roughly 10px at 1080p) and a faint drop shadow. The border unifies images from different sources into one set of stickers; this is what makes the style recognizable at a glance.
- One new thing per beat: every 0.5–1 s something is added (a sticker, a leader-line label, a bar, a number), so the viewer is never just waiting.
- Charts are true: bar lengths are proportional to their values, counters stop on the real number, and a number that appears twice is the same both times. Viewers will take these numbers at face value.
- Calm typography: pale blue-grey or off-white ground, dark grey text, exactly one accent color; sans-serif in two weights only; everything snaps to one grid.
</signature>

<style>
These are recommendations, not rules.
- Palette: blue-grey ground #E9EEF2 + slate, with Claude's terracotta #D97757 as the single accent, because the episode is about Claude Code, so the one accent ties the film to the product
- Fonts: Noto Sans SC in two weights; JetBrains Mono for the terminal text
- Avoid: stickers arriving together, linear camera moves, leader-line labels fading in from the center (they should draw out from the sticker's edge), any button in the terminal that isn't in the real interface
</style>

<check>
As in the template, plus:
- Every character and interface element in the terminal can be found in screenshots of the real interface
- While the camera moves, the stop being discussed stays within the middle third of the frame
</check>
```

## Example 2: variety-show caption, a transparent overlay on the talking head

```text
<role>
You are a variety-show caption designer, and the code and sound effects are yours too. You care most that the caption matches the presenter's emotion and lands at exactly the right moment.
</role>

<context>
- Where it is used: laid over the talking-head A-roll. At 01:12 the presenter says "它自己把 bug 修好了" (it fixed the bug by itself) and looks surprised; the caption goes in the empty space beside the presenter's head, never over the face
- Who watches: as above, scrolling on a phone. The caption adds fuel to the emotion; it is not a subtitle (subtitles are a separate job and sit at the bottom)
- Files: project folder films/caption-0112/; a still of the presenter at that moment in assets/ref.png (for positioning only, not part of the output)
</context>

<task>
Make a 2.5-second caption: first three question marks pop up, then 0.4 s later the main caption slams down inside a radial burst frame with sweat drops and sparkles; it wobbles gently while holding, and shrinks away in the last 0.3 s.
On-screen text (Chinese, use exactly): "？？？" then "自己修好了!!"
</task>

<specs>
- 2560×1440, 60fps, exactly 2.5 s, transparent ProRes 4444 (render.mjs --alpha), no audio in the video
- Deliver the effects stem out/stems/sfx.wav separately: record_scratch on the question marks, duang on the slam
- The caption's bounding box sits entirely within the empty space beside the presenter's head in ref.png, and stays out of the bottom 15% (subtitle zone)
- Write your report in the user's language
</specs>

<signature>
- Sticker text: a heavy rounded or chubby typeface with at least two outlines (white inside, colored outside) plus a hard drop shadow, readable over any background.
- It pops: scales past full size and settles back in about 8 frames, or bounces in letter by letter with a 2-frame stagger. While holding it wobbles slightly rather than sitting dead.
- Emotion has symbols: surprise gets a burst frame and radial lines, embarrassment gets sweat drops and small text in parentheses, smugness gets sparkles, sarcasm gets tilted handwriting.
- It has sound: every appearance comes with a cartoon effect, and the text lands 2–3 frames after the beat it reacts to, which feels more natural.
- Loud color: high saturation, no more than three colors on screen at once.
</signature>

<check>
- Composite a frame over ref.png: the face and the subtitle zone stay clear
- Transparent edges show no black or white fringes (zoom into the outer outline)
</check>
```
