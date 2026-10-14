# Video #2: What if friction disappeared for 5 seconds?
# Run: Blender -b ~/ParallelEarth/renders/park_hero.blend -P pipeline/friction/animate.py
# Timeline (24 fps): 0-6 s normal park, 6-11 s friction = 0, 11 s friction returns, ends 22 s.
import bpy, os, math, random

FPS, DUR = 24, 22
T_OFF, T_ON = 6.0, 11.0
WALK = 1.3            # m/s
OUT = os.path.expanduser("~/ParallelEarth/renders/friction/f_")
random.seed(11)

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

walkers = [e for e in bpy.data.objects
           if e.instance_type == "COLLECTION" and e.instance_collection and action_of(e.instance_collection) == "Walk"]
print("walkers", len(walkers))

def key(e, f, loc, fall):
    e.location = loc; e.rotation_euler[0] = fall
    e.keyframe_insert("location", frame=f); e.keyframe_insert("rotation_euler", index=0, frame=f)

for e in walkers:
    yaw = e.rotation_euler[2]
    fwd = (math.sin(yaw), -math.cos(yaw))     # Quaternius rigs face local -Y
    x0, y0 = e.location.x, e.location.y
    def at(t):                                  # position if still moving at walking speed
        return (x0 + fwd[0] * WALK * t, y0 + fwd[1] * WALK * t, 0.0)
    slip = T_OFF + random.uniform(0.0, 0.35)    # each foot slips on its next step
    land = slip + random.uniform(0.45, 0.6)
    key(e, 1, at(0), 0)
    key(e, int(slip * FPS), at(slip), 0)
    lx, ly, _ = at(land)
    key(e, int(land * FPS), (lx, ly, 0.14), -math.pi / 2 * random.uniform(0.92, 1.0))   # flat on their back
    sx, sy, _ = at(T_ON)
    key(e, int(T_ON * FPS), (sx, sy, 0.14), -math.pi / 2)          # still sliding: nothing slows them
    ex, ey, _ = at(T_ON + 0.25)
    key(e, int((T_ON + 0.25) * FPS), (ex, ey, 0.14), -math.pi / 2)  # friction back: skid to a stop
    key(e, FPS * DUR, (ex, ey, 0.14), -math.pi / 2)

# slow push-in toward the fountain
cam = sc.camera
cam.location = (-0.4, -6, 8.0); cam.keyframe_insert("location", frame=1)
cam.location = (-0.4, 0.5, 6.8); cam.keyframe_insert("location", frame=FPS * DUR)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
if os.environ.get("TEST"):
    for f in (1, 140, 160, 230, 300):
        sc.frame_set(f); sc.render.filepath = f"{OUT}test_{f:04d}.png"
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print("FRICTION_DONE")
