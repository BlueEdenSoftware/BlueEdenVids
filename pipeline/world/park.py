# Parallel Earth world kit: Central-Park-style hero scene.
# Run: Blender -b -P pipeline/world/park.py -- [--frame out.png] [--res 720] [--at 10]
import bpy, os, sys, math, random, time
from mathutils import Vector

ASSETS = os.path.expanduser("~/ParallelEarth/assets")
K = os.path.join(ASSETS, "kenney")
QM = os.path.join(ASSETS, "quaternius", "Ultimate Modular Men- Feb 2022", "Individual Characters", "glTF")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default):
    return args[args.index(name) + 1] if name in args else default
OUT = arg("--frame", os.path.expanduser("~/ParallelEarth/renders/park_hero.png"))
RES = int(arg("--res", "720"))
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
lib = bpy.data.collections.new("_lib"); sc.collection.children.link(lib)
lib.hide_render = True; lib.hide_viewport = True
world_col = bpy.data.collections.new("park"); sc.collection.children.link(world_col)

def find_glb(pack, name):
    hits = [os.path.join(r, name + ".glb") for r, _, f in os.walk(os.path.join(K, pack)) if name + ".glb" in f]
    if not hits: raise FileNotFoundError(f"{pack}/{name}")
    return sorted(hits, key=lambda p: "GLB" not in p)[0]

_cache = {}
def proto(pack, name, height, path=None, action=None, offset=0):
    """Import a model once into a hidden collection, normalized to a height (m), base at z=0.
    With action, the armature plays that clip on loop, shifted by offset frames so crowds desync."""
    key = (pack, name, height, action, offset)
    if key in _cache: return _cache[key]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path or find_glb(pack, name))
    objs = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in objs if o.name.startswith("Icosphere")]:   # stray helper mesh the importer adds
        objs.remove(o); bpy.data.objects.remove(o)
    col = bpy.data.collections.new(f"{name}_{height}"); lib.children.link(col)
    for o in objs:
        for c in o.users_collection: c.objects.unlink(o)
        col.objects.link(o)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    zmin = min(p.z for p in pts); zmax = max(p.z for p in pts)
    cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
    s = height / max(zmax - zmin, 1e-6)
    for r in (o for o in objs if o.parent is None):
        r.location = (r.location - Vector((cx, cy, zmin))) * s
        r.scale = r.scale * s
    if action:
        for arm in (o for o in objs if o.type == "ARMATURE"):
            ad = arm.animation_data_create(); ad.action = None
            strip = ad.nla_tracks.new().strips.new(action, 1 - offset, bpy.data.actions[action])
            strip.repeat = 60
    _cache[key] = col
    return col

def place(col, x, y, rot=None, z=0.0, scale=1.0):
    e = bpy.data.objects.new(col.name, None)
    e.instance_type = "COLLECTION"; e.instance_collection = col
    e.location = (x, y, z); e.rotation_euler[2] = random.uniform(0, 2 * math.pi) if rot is None else rot
    e.scale = (scale,) * 3
    world_col.objects.link(e)
    return e

def mat(name, rgb, rough=0.8, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def prim(kind, loc, size, m, **kw):
    if kind == "cyl": bpy.ops.mesh.primitive_cylinder_add(location=loc, **kw)
    elif kind == "cube": bpy.ops.mesh.primitive_cube_add(location=loc, **kw)
    elif kind == "sphere": bpy.ops.mesh.primitive_uv_sphere_add(location=loc, **kw)
    o = bpy.context.object; o.scale = size; o.data.materials.append(m)
    for c in o.users_collection: c.objects.unlink(o)
    world_col.objects.link(o)
    return o

# ---------- materials
GRASS = mat("grass", (0.16, 0.36, 0.10))
PAVE = mat("pave", (0.62, 0.58, 0.52), 0.9)
STONE = mat("stone", (0.75, 0.72, 0.66), 0.6)
WATER = mat("water", (0.12, 0.35, 0.45), 0.05)
WOOD = mat("wood", (0.35, 0.20, 0.10))
IRON = mat("iron", (0.05, 0.06, 0.06), 0.4)
LAMP = mat("lamp", (1.0, 0.85, 0.6), 0.5, emit=3.0)

# ---------- ground and paths (camera looks toward +Y)
prim("cube", (0, 150, -0.05), (500, 300, 0.05), GRASS)
prim("cube", (0, 30, 0.01), (4, 45, 0.02), PAVE)                 # main promenade
prim("cyl", (0, 32, 0.012), (13, 13, 0.02), PAVE, vertices=64)   # plaza around fountain
prim("cube", (0, 32, 0.011), (40, 3, 0.02), PAVE)                # cross path

# ---------- fountain (Bethesda-style)
prim("cyl", (0, 32, 0.35), (7, 7, 0.35), STONE, vertices=64)
prim("cyl", (0, 32, 0.62), (6.6, 6.6, 0.05), WATER, vertices=64)
prim("cyl", (0, 32, 1.4), (0.6, 0.6, 1.4), STONE, vertices=24)
prim("cyl", (0, 32, 2.8), (2.4, 2.4, 0.18), STONE, vertices=48)
prim("cyl", (0, 32, 3.6), (0.35, 0.35, 0.8), STONE, vertices=16)
prim("sphere", (0, 32, 4.6), (0.5, 0.5, 0.7), STONE)

# ---------- benches and lamp posts
def bench(x, y, rot):
    e = bpy.data.objects.new("bench", None); e.location = (x, y, 0); e.rotation_euler[2] = rot
    world_col.objects.link(e)
    prim("cube", (0, 0, 0.45), (0.9, 0.22, 0.04), WOOD).parent = e
    prim("cube", (0, 0.22, 0.75), (0.9, 0.03, 0.18), WOOD).parent = e
    for sx in (-0.8, 0.8):
        prim("cube", (sx, 0, 0.22), (0.04, 0.2, 0.22), IRON).parent = e

def lamp(x, y):
    prim("cyl", (x, y, 2.0), (0.07, 0.07, 2.0), IRON, vertices=12)
    prim("sphere", (x, y, 4.15), (0.22, 0.22, 0.26), LAMP)

for y in range(8, 52, 7):
    for side in (-1, 1):
        if 20 < y < 44: continue
        bench(side * 3.0, y, math.pi / 2 * side)
        lamp(side * 2.6, y + 3.5)
for a in range(0, 360, 45):
    lamp(11.5 * math.cos(math.radians(a + 22)), 32 + 11.5 * math.sin(math.radians(a + 22)))
    bench(12.3 * math.cos(math.radians(a)), 32 + 12.3 * math.sin(math.radians(a)), math.radians(a) + math.pi / 2)

# ---------- trees, bushes, flowers
trees = [proto("nature-kit", n, h) for n, h in
         (("tree_oak", 11), ("tree_default", 9), ("tree_fat", 10), ("tree_detailed", 12), ("tree_oak_dark", 12))]
bushes = [proto("nature-kit", n, h) for n, h in (("plant_bushLarge", 1.4), ("plant_bushDetailed", 1.1), ("plant_bush", 0.9))]
flowers = [proto("nature-kit", n, 0.45) for n in ("flower_redA", "flower_yellowA", "flower_purpleA", "flower_redB")]

def clear_of_paths(x, y, margin):
    if abs(x) < 4 + margin and -5 < y < 80: return False
    if math.hypot(x, y - 32) < 14 + margin: return False
    if abs(y - 32) < 3 + margin and abs(x) < 42: return False
    return True

n = 0
while n < 320:
    x, y = random.uniform(-90, 90), random.uniform(4, 160)
    if clear_of_paths(x, y, 3) and math.hypot(x, y + 4) > 22:   # keep big trees out of the camera's face
        place(random.choice(trees), x, y, scale=random.uniform(0.85, 1.2)); n += 1
n = 0
while n < 120:
    x, y = random.uniform(-25, 25), random.uniform(3, 60)
    if clear_of_paths(x, y, 0.5):
        place(random.choice(bushes), x, y); n += 1
for a in range(0, 360, 6):   # flower ring around the plaza
    r = 13.6 + random.uniform(-0.2, 0.3)
    place(random.choice(flowers), r * math.cos(math.radians(a)), 32 + r * math.sin(math.radians(a)))

# ---------- skyline (Manhattan-style wall far behind the trees)
towers = [proto("city-kit-commercial", f"building-skyscraper-{c}", h)
          for c, h in (("a", 120), ("b", 150), ("c", 95), ("d", 180), ("e", 130))]
blocks = [proto("city-kit-commercial", f"building-{c}", 55) for c in "abcdefghij"]
x = -420
while x < 420:
    place(random.choice(towers if random.random() < 0.55 else blocks), x, random.uniform(380, 430),
          rot=random.choice((0, math.pi)), scale=random.uniform(0.8, 1.25))
    x += random.uniform(12, 20)
x = -330
while x < 330:
    place(random.choice(blocks), x, random.uniform(330, 350), rot=0, scale=random.uniform(0.9, 1.3))
    x += random.uniform(16, 22)

# ---------- people (Quaternius Ultimate Modular Men, CC0)
OUTFITS = ["Casual_2", "Casual_Hoodie", "Suit", "Beach", "Punk", "Worker", "Farmer", "Adventurer"]
def person(action):
    o = random.choice(OUTFITS)
    return proto("quaternius", o, 1.78, path=os.path.join(QM, o + ".gltf"), action=action,
                 offset=random.choice((0, 7, 13, 19)))
def add(action, x, y, rot):
    place(person(action), x, y, rot=rot + random.uniform(-0.25, 0.25), scale=random.uniform(0.94, 1.06))
for _ in range(45):   # walking along the promenade and cross path
    if random.random() < 0.6: add("Walk", random.uniform(-3.3, 3.3), random.uniform(5, 55), random.choice((0, math.pi)))
    else: add("Walk", random.uniform(-38, 38), 32 + random.uniform(-2.2, 2.2), random.choice((-1, 1)) * math.pi / 2)
for _ in range(14):   # foreground: people close to camera so the bottom third is not empty
    add(random.choice(("Walk", "Walk", "Idle_Neutral")), random.uniform(-3.2, 3.2), random.uniform(1.5, 9), random.choice((0, math.pi)))
for _ in range(40):   # plaza: strolling around the fountain or standing
    a = random.uniform(0, 2 * math.pi); r = random.uniform(7.8, 12.5)
    act = random.choice(("Walk", "Walk", "Idle_Neutral", "Idle", "Wave", "Interact"))
    add(act, r * math.cos(a), 32 + r * math.sin(a), a + (math.pi if act == "Walk" else random.uniform(0, 6.28)))
for _ in range(25):   # on the lawns
    x, y = random.uniform(-22, 22), random.uniform(6, 60)
    if clear_of_paths(x, y, 0.5): add(random.choice(("Idle_Neutral", "Idle", "Wave")), x, y, random.uniform(0, 6.28))

# ---------- sky, sun, camera
w = bpy.data.worlds.new("sky"); sc.world = w; w.use_nodes = True
nt = w.node_tree; env = nt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(ASSETS, "polyhaven", "park_sky.hdr"))
nt.links.new(env.outputs["Color"], nt.nodes["Background"].inputs["Color"])
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 3.5; sun.data.angle = math.radians(2)
sun.rotation_euler = (math.radians(50), 0, math.radians(-35)); sc.collection.objects.link(sun)

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cam.data.lens = 24; sc.camera = cam
cam.location = (-0.4, -4, 7.5)
cam.rotation_euler = (math.radians(77), 0, math.radians(1.0))

# ---------- render settings: EEVEE, vertical
try: sc.render.engine = "BLENDER_EEVEE"
except TypeError: sc.render.engine = "BLENDER_EEVEE_NEXT"
for k, v in (("taa_render_samples", 32), ("use_shadows", True), ("use_raytracing", False)):
    if hasattr(sc.eevee, k): setattr(sc.eevee, k, v)
sc.render.resolution_x, sc.render.resolution_y = RES, RES * 16 // 9
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"
sc.render.filepath = OUT
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sc.frame_set(int(arg("--at", "10")))
t = time.time()
bpy.ops.render.render(write_still=True)
print(f"PARK_RENDER_SECONDS {time.time() - t:.1f}")
bpy.ops.wm.save_as_mainfile(filepath=os.path.splitext(OUT)[0] + ".blend")
