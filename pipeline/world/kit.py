# Parallel Earth world kit: shared helpers for scene scripts. Load with exec(open(kit.py).read()).
import bpy, os, sys, math, random, time
from mathutils import Vector

ASSETS = os.path.expanduser("~/ParallelEarth/assets")
K = os.path.join(ASSETS, "kenney")
QM = os.path.join(ASSETS, "quaternius", "Ultimate Modular Men- Feb 2022", "Individual Characters", "glTF")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default):
    return args[args.index(name) + 1] if name in args else default
RES = int(arg("--res", "720"))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
lib = bpy.data.collections.new("_lib"); sc.collection.children.link(lib)
lib.hide_render = True; lib.hide_viewport = True
world_col = bpy.data.collections.new("world"); sc.collection.children.link(world_col)

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
    col["dx"] = (max(p.x for p in pts) - min(p.x for p in pts)) * s     # footprint after scaling
    col["dy"] = (max(p.y for p in pts) - min(p.y for p in pts)) * s
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
