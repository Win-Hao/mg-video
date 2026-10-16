"""Builds the whole scene from nothing, keys every frame, renders PNG frames with Cycles on the Metal GPU.
Run it through render.sh (nohup, frame ranges, resume), or by hand:

  blender -b --factory-startup -P scene.py -- --frames 1-300 --samples 28 --out out/frames
  options: --frames 1-300 | 1,31,61-65 | test (20 frames spread over the film)   --scale 50 (percent)
           --samples 16  --thr 0.03  --mb 0 (motion blur off)  --resume 1 (skip frames already written)
           --device CPU  --blend out/scene.blend (save the built scene to open in the UI)

Blender frame f shows t = (f - 1) / fps, so frame 1 is t = 0. Keys run from frame 0 to two frames past the end, so
motion blur has neighbours at both ends. Size, fps and duration come from video.json, times from cues.json.
Keep the simulation in its own sim.py (numpy, writes out/anim.npz) and lights/look in lights.json once they grow.
"""
import json
import math
import os
import sys
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V = json.load(open(os.path.join(HERE, 'video.json')))
CUES = json.load(open(os.path.join(HERE, 'cues.json'), encoding='utf-8'))
FPS, N = V['fps'], round(V['duration'] * V['fps'])
T = {e['id']: e['t'] for e in CUES.get('events', [])}

# ---------------------------------------------------------------- arguments after `--` (each option takes a value)
A = {'frames': f'1-{N}', 'samples': '28', 'thr': '0.03', 'scale': '100', 'mb': '1', 'out': 'out/frames', 'resume': '0',
     'device': 'METAL', 'blend': ''}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
for k, v in zip(argv[::2], argv[1::2]):
    if k.lstrip('-') not in A:
        sys.exit(f'unknown option {k}; options: {", ".join("--" + a for a in A)}')
    A[k.lstrip('-')] = v


def frame_list(spec):
    if spec == 'test':
        return sorted({1 + round(i * (N - 1) / 19) for i in range(20)})
    out = []
    for part in spec.split(','):
        a, _, b = part.partition('-')
        out += range(int(a), int(b or a) + 1)
    return out


# ---------------------------------------------------------------- keys (Blender 5: layered actions; Action.fcurves is gone)
_bags = {}


def key(idb, path, fn):
    """Key idb.<path> on every frame from 0 to N + 2 with fn(t), t = (f - 1) / fps, linear between frames. idb is an
    object or its data (light energy: key(lamp.data, 'energy', …)); fn returns a number or a tuple."""
    if (idb.id_type, idb.name) not in _bags:   # action → slot → layer → keyframe strip → channelbag, once per ID
        act = bpy.data.actions.new(idb.name)
        slot = act.slots.new(id_type=idb.id_type, name=idb.name)
        strip = act.layers.new('L').strips.new(type='KEYFRAME')
        ad = idb.animation_data_create()
        ad.action, ad.action_slot = act, slot
        _bags[idb.id_type, idb.name] = strip.channelbag(slot, ensure=True)
    frames = np.arange(0, N + 3, dtype=float)
    vals = np.array([np.atleast_1d(fn((f - 1) / FPS)) for f in frames], dtype=float)
    for j in range(vals.shape[1]):
        fc = _bags[idb.id_type, idb.name].fcurves.new(path, index=j)
        fc.keyframe_points.add(len(frames))
        fc.keyframe_points.foreach_set('co', np.column_stack([frames, vals[:, j]]).ravel())
        fc.keyframe_points.foreach_set('interpolation', np.ones(len(frames), dtype=np.int32))   # 1 = LINEAR
        fc.update()


def material(name, color, roughness=0.5, **inputs):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    for k, v in inputs.items():
        p.inputs[k.replace('_', ' ')].default_value = v
    return m


# ---------------------------------------------------------------- the scene (an example: a rubber ball drops on its cue)
T0 = time.time()
for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
    for d in list(coll):
        coll.remove(d)
scn = bpy.context.scene
scn.render.fps, scn.frame_start, scn.frame_end = FPS, 1, N

bpy.ops.mesh.primitive_plane_add(size=20)
bpy.context.object.data.materials.append(material('floor', (0.5, 0.47, 0.44), 0.9))
R, land = 0.1, T.get('title', 0.3) + 0.5
bpy.ops.mesh.primitive_uv_sphere_add(radius=R, segments=64, ring_count=32)
ball = bpy.context.object
bpy.ops.object.shade_smooth()
ball.data.materials.append(material('rubber', (0.9, 0.08, 0.03), 0.45, Subsurface_Weight=0.3))


def squash(t):   # 25 % on landing, recovering in about 0.15 s
    return 0.25 * math.exp(-(t - land) / 0.05) if t >= land else 0.0


def ball_z(t):   # falls from 0.5 m and lands at `land` (a cue), then damped bounces
    if t < land:
        return R + 0.5 * (1 - (max(t, land - 0.32) - land + 0.32) ** 2 / 0.32 ** 2)
    return R * (1 - squash(t)) + 0.12 * abs(math.sin(8 * (t - land))) * math.exp(-4 * (t - land))


key(ball, 'location', lambda t: (0, 0, ball_z(t)))
key(ball, 'scale', lambda t: (1 + squash(t) / 2, 1 + squash(t) / 2, 1 - squash(t)))   # same object: same channelbag

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scn.collection.objects.link(cam)
scn.camera = cam
cam.location, cam.rotation_euler = (0, -1.6, 0.35), (math.radians(82), 0, 0)
cam.data.lens = 85
cam.data.dof.use_dof, cam.data.dof.aperture_fstop, cam.data.dof.focus_object = True, 2.8, ball
lamp = bpy.data.objects.new('key', bpy.data.lights.new('key', 'AREA'))
scn.collection.objects.link(lamp)
lamp.location, lamp.rotation_euler = (0.8, -0.8, 1.4), (math.radians(45), 0, math.radians(45))
lamp.data.size, lamp.data.energy = 1.0, 120   # set power for the scene's size: a test scene's power overexposed 4 stops
scn.world = bpy.data.worlds.new('studio')
scn.world.use_nodes = True
scn.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.05, 0.05, 0.06, 1)

# ---------------------------------------------------------------- render settings (measured 10-13, styles/15-3d-material.md)
r = scn.render
r.resolution_x, r.resolution_y, r.resolution_percentage = V['width'], V['height'], int(A['scale'])
r.use_motion_blur, r.motion_blur_shutter, r.motion_blur_position = A['mb'] == '1', 0.5, 'CENTER'
r.use_persistent_data = True
r.image_settings.file_format, r.image_settings.color_depth, r.image_settings.compression = 'PNG', '8', 15
scn.view_settings.view_transform, scn.view_settings.look = 'AgX', 'AgX - Punchy'
r.engine = 'CYCLES'
c = scn.cycles
prefs = bpy.context.preferences.addons['cycles'].preferences
if A['device'] == 'METAL':   # compute_device_type first, then get_devices(), then enable the Metal device
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'METAL'
    if not any(d.use for d in prefs.devices):
        print('[scene] no Metal device found: rendering on the CPU')
c.device = 'GPU' if A['device'] == 'METAL' and any(d.use for d in prefs.devices) else 'CPU'
c.samples, c.use_adaptive_sampling, c.adaptive_threshold = int(A['samples']), True, float(A['thr'])
c.use_denoising, c.denoiser, c.denoising_input_passes, c.denoising_prefilter = True, 'OPENIMAGEDENOISE', 'RGB_ALBEDO_NORMAL', 'ACCURATE'
c.denoising_use_gpu = c.device == 'GPU'
c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces, c.transparent_max_bounces = 16, 3, 6, 12, 8
c.caustics_reflective = c.caustics_refractive = False
c.blur_glossy, c.sample_clamp_indirect = 0.6, 4.0
c.seed, c.use_animated_seed = 7, False
print(f'[scene] built in {time.time() - T0:.1f}s; {c.device}, {A["samples"]} samples, {A["scale"]} %, motion blur {A["mb"]}')
if A['blend']:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, A['blend']))

# ---------------------------------------------------------------- render, one PNG per frame, timed
out = os.path.join(HERE, A['out'])
os.makedirs(out, exist_ok=True)
todo = [f for f in frame_list(A['frames']) if not (A['resume'] == '1' and os.path.exists(os.path.join(out, f'f{f:04d}.png')))]
log = open(os.path.join(HERE, 'out', 'render_log.txt'), 'a')
t_start = time.time()
for i, f in enumerate(todo):
    scn.frame_set(f)
    part = os.path.join(out, f'f{f:04d}.part.png')   # renamed when complete, so a killed render never leaves a half frame
    r.filepath = part
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    os.replace(part, os.path.join(out, f'f{f:04d}.png'))
    eta = (time.time() - t_start) / (i + 1) * (len(todo) - i - 1)
    msg = f'frame {f} t={(f - 1) / FPS:.3f}s {time.time() - t1:.1f}s/frame  {i + 1}/{len(todo)}  eta {eta / 60:.1f} min  ({A["samples"]} samples, {A["scale"]} %)'
    print('[render]', msg, flush=True)
    log.write(time.strftime('%H:%M:%S ') + msg + '\n')
    log.flush()
print(f'[scene] done: {len(todo)} frames in {time.time() - T0:.0f}s')
