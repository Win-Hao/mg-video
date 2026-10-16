# Isometric 2.5D (等轴 2.5D)

A miniature world in isometric projection: nothing shrinks with distance and parallel lines stay parallel, like looking down at an animated sand table. The best way to lay out how several things connect.

**Good for**: diagrams of software systems — an agent, MCP servers, tools, files, and services. Each component is a small building or machine; data travels between them through pipes.
**Reference films (technique only)**: mg-styles-15 `demos/03-isometric/` (the October 2026 test batch added depth sorting, open-faced objects, and a measured shading order).

<signature>
- True isometric: no perspective; every diagonal on screen is 30° (a 2:1 pixel slope in pixel art); verticals stay vertical.
- Three faces, three values: each object has a top, left, and right face in three values of one hue (top brightest), and the light comes from the same side for the whole film.
- Things grow: the footprint lands first, the walls rise, and the top caps it last. Nothing fades in from nowhere.
- The camera never changes angle: it pans (foreground, midground, and background may pan at slightly different speeds for depth), and a final pull-back is an orthographic zoom, still without perspective.
- Relationships are visible: connections are pipes, rails, or lines that run along the grid, with small blocks flowing along them.
</signature>

<style>
- Build: SVG or Canvas with hand-computed coordinates (an `iso(x, y, z) → [screenX, screenY]` helper). Sorting back-to-front by x + y fails for long or stacked boxes (conveyors, shelves, a book on a tray): each frame, sort topologically — for two boxes whose screen outlines overlap, draw first the one that is behind along whichever of the (x−y), (x−z), (y−z) ranges separates them — or cut long boxes into unit cells. Use a Three.js orthographic camera only if you need shadows or ambient occlusion.
- Growth: the footprint slab drops (about 3 frames) and sits on the ground at least 4 frames before walls rise; posts ease out. Frame 0 must already show the subject, so the film may open half-grown; open furniture (a shelf) caps with its top board.
- Occlusion traps: a resident object with larger x and higher z covers the upper-right corner of anything behind it, and without shadows that reads as one passing through the other. Keep every nearer resident object's silhouette off the hero's screen path, leave openings in the hero's route (the first draft hid its climax behind a top board), and extend connectors (bridges, pushers) only while they are in use.
- Airborne objects (thrown, falling, flying in) have no depth cue: give them a solid, unblurred ground shadow, or route them over empty floor so their screen path never crosses another object.
- Open faces: a shaft, room, or cabinet open toward the viewer shows its inner walls, and they put the dark face where the light face should be — light from the wrong side. Openings (windows, exits, slots) are darker than their face throughout the film; inner walls seen through a front opening, area-averaged, sit between the front face and the darkest face, however wide the window (a window 72% of the face kept the order). An empty slot at the end of a row needs its own back and side walls, or the eye passes through to whatever is behind and it doesn't read as empty.
- Palette: a low-saturation light ground plus 3–4 soft main colors, one per component type.
- Beat skeleton: the ground spreads out → the hero component grows → the others grow in turn → pipes draw out and blocks start flowing → pull back for the whole picture, with the title set on the ground plane in isometric skew (outline each character in the ground color so grid lines stop short of the strokes).
- Sound: bed `explainer` (its drop keeps a full kick and sub on every bar, so a kick 1 s after the climax hits almost as hard; turn them down with `levels=`); a `pop` or `click` as each component lands, a run of `blip` for data flow; accents and per-row notes go on `bus='sfx'`, never on the normalized music bus.
- Avoid: any perspective, inconsistent face shading, rotating the view to show something better, resident bridges or boards across the hero's path.
</style>

<check>
- Occlusion on screen, not just in 3D: crop the hero's path frame by frame (`sheet.py --crop x,y,w,h`), and export boxes from `window.boxes(t)` so `measure.py overlap --boxes out/boxes.json --a <mover> --b <object>` finds 0 frames where a moving object crosses something it should pass clear of.
- Measure the diagonals: 30°, nothing skewed.
- Shading order, frame by frame at the phone width set in prompt.md: measure each object's own faces (polygons from the geometry or `out/boxes.json`, counting only that object's pixels), the same face order on every object, open ones and opened doors included, with a clear margin (≥ 15 levels held in the test film).
- Anything about to be filled reads as empty at phone width before it fills (a dark slot, an outline, or a contrasting color).
- One light direction throughout.
</check>
