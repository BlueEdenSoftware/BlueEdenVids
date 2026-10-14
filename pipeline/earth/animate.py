# Video #3: What if Earth stopped spinning for 5 seconds?
# Run: Blender -b ~/ParallelEarth/renders/park_hero.blend -P pipeline/earth/animate.py
# Physics: in New York (40.7 N) the ground moves east at 1,674 * cos(40.7) = ~1,270 km/h (353 m/s).
# Earth stops, everything loose keeps that speed. Scene time 6-12 s is slow motion x50
# (0.12 s real), so the visible speed is 353 / 50 = ~7 m/s. At 12 s we cut to real time: all gone.
import bpy, os, math, random

FPS, DUR = 24, 24
T_STOP, T_SLOW_END = 6.0, 12.0
V = 353.0 / 50          # visible slow-motion speed, m/s, toward +X (east)
OUT = os.path.expanduser("~/ParallelEarth/renders/earth/f_")
random.seed(5)

sc = bpy.context.scene
bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = FPS * DUR
sc.render.filepath = OUT
sc.render.image_settings.file_format = "PNG"

def action_of(col):
    for o in col.all_objects:
        ad = o.animation_data
        if o.type == "ARMATURE" and ad and ad.nla_tracks:
            return ad.nla_tracks[-1].strips[0].action.name
    return None

loose = []
for e in bpy.data.objects:
    if e.instance_type == "COLLECTION" and e.instance_collection:
        name = e.instance_collection.name
        if name.startswith(("building", "low-detail")): continue        # skyline stays
        kind = "person" if action_of(e.instance_collection) else ("tree" if name.startswith("tree") else "prop")
        loose.append((e, kind))
    elif e.name.startswith("bench"):
        loose.append((e, "prop"))
print("loose", len(loose))

WALK = 1.3
def key(e, f):
    e.keyframe_insert("location", frame=f); e.keyframe_insert("rotation_euler", frame=f)

for e, kind in loose:
    x0, y0, z0 = e.location
    r0 = e.rotation_euler.copy()
    vx = V * random.uniform(0.85, 1.0)
    if kind == "person":
        yaw = r0[2]
        walking = action_of(e.instance_collection) == "Walk"
        fwd = (math.sin(yaw), -math.cos(yaw)) if walking else (0, 0)
        x0, y0 = x0, y0
        key(e, 1)
        e.location = (x0 + fwd[0] * WALK * T_STOP, y0 + fwd[1] * WALK * T_STOP, z0); key(e, int(T_STOP * FPS))
        x0, y0 = e.location.x, e.location.y
    else:
        key(e, int(T_STOP * FPS))
    delay = 0.0 if kind != "tree" else random.uniform(0.3, 1.2)   # roots hold a moment, then tear
    t = T_SLOW_END - T_STOP
    dist = vx * max(0.0, t - delay)
    if delay:
        e.location = (x0, y0, z0); key(e, int((T_STOP + delay) * FPS))
    e.location = (x0 + dist, y0 + random.uniform(-1, 1), z0 + (0.6 if kind == "person" else 1.5) * t)
    e.rotation_euler = (r0[0] + random.uniform(-1, 1) * 4, r0[1] + random.uniform(2, 6) * (1 if kind != "tree" else 0.4), r0[2])
    key(e, int(T_SLOW_END * FPS))
    e.location = (x0 + 5000, y0, z0); key(e, int(T_SLOW_END * FPS) + 1)   # real time: long gone
    key(e, FPS * DUR)

# slow push-in, then a hard shake when the planet stops
cam = sc.camera
cam.location = (-0.4, -6, 8.0); cam.keyframe_insert("location", frame=1)
cam.location = (-0.4, -4.5, 7.7); cam.keyframe_insert("location", frame=int(T_STOP * FPS))
for i in range(1, 30):
    f = int(T_STOP * FPS) + i
    a = 0.35 * (1 - i / 30)
    cam.location = (-0.4 + random.uniform(-a, a), -4.5 + random.uniform(-a, a), 7.7 + random.uniform(-a, a))
    cam.keyframe_insert("location", frame=f)
cam.location = (-0.4, -4.5, 7.7); cam.keyframe_insert("location", frame=int(T_STOP * FPS) + 31)
cam.location = (-0.4, -1.0, 7.2); cam.keyframe_insert("location", frame=FPS * DUR)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
if os.environ.get("TEST"):
    for f in (100, 160, 220, 280, 300):
        sc.frame_set(f); sc.render.filepath = f"{OUT}test_{f:04d}.png"
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print("EARTH_DONE")
