# Parallel Earth world kit: Manhattan crosstown street (42nd-Street style), camera looking west.
# Run: Blender -b -P pipeline/world/street.py -- [--frame out.png] [--res 720]
import os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit.py")).read())
OUT = arg("--frame", os.path.expanduser("~/ParallelEarth/renders/street_hero.png"))
random.seed(42)

ROAD, WALK_W = 8.0, 5.0      # half road width, sidewalk width (m)
LEN = 420.0

ASPH = mat("asphalt", (0.07, 0.07, 0.075), 0.9)
SIDE = mat("sidewalk", (0.55, 0.53, 0.50), 0.9)
CURB = mat("curb", (0.7, 0.7, 0.68), 0.8)
LINE = mat("line", (0.95, 0.85, 0.2), 0.6)
WHITE = mat("white", (0.9, 0.9, 0.9), 0.6)

# ---------- road, sidewalks, markings (street runs along +Y; camera at y<0 looking +Y)
prim("cube", (0, LEN / 2, -0.05), (ROAD + WALK_W + 60, LEN / 2 + 30, 0.05), ASPH)
for s in (-1, 1):
    prim("cube", (s * (ROAD + WALK_W / 2), LEN / 2, 0.08), (WALK_W / 2, LEN / 2 + 30, 0.08), SIDE)
    prim("cube", (s * (ROAD + 0.1), LEN / 2, 0.09), (0.12, LEN / 2 + 30, 0.09), CURB)
for y in range(-20, int(LEN), 9):
    for x in (-0.12, 0.12): prim("cube", (x, y, 0.005), (0.06, 3.0, 0.005), LINE)       # double yellow
    for x in (-4.0, 4.0): prim("cube", (x, y, 0.005), (0.07, 1.5, 0.005), WHITE)        # lane dashes

# ---------- buildings packed along both sides, gaps at cross streets
mid = [proto("city-kit-commercial", f"building-{c}", h) for c, h in
       zip("abcdefghijklmn", (32, 40, 28, 45, 36, 30, 50, 38, 26, 42, 34, 48, 30, 44))]
towers = [proto("city-kit-commercial", f"building-skyscraper-{c}", h)
          for c, h in (("a", 140), ("b", 170), ("c", 120), ("d", 200), ("e", 150))]
CROSS = (70, 160, 250, 340)
for side in (-1, 1):
    y = -15.0
    while y < LEN:
        if any(c - 6 < y < c + 6 for c in CROSS): y += 12; continue
        col = random.choice(towers if y > 180 and random.random() < 0.4 else mid)
        sc_ = random.uniform(0.9, 1.15)
        dx, dy = col["dx"] * sc_, col["dy"] * sc_
        place(col, side * (ROAD + WALK_W + dx / 2), y + dy / 2, rot=0 if side < 0 else math.pi, scale=sc_)
        y += dy + random.uniform(0, 1.5)
# far skyline at the end of the street
for x in range(-120, 121, 22):
    place(random.choice(towers), x + random.uniform(-5, 5), LEN + 60 + random.uniform(0, 40), rot=0,
          scale=random.uniform(0.8, 1.2))

# ---------- street furniture (bolted down)
lights = proto("city-kit-roads", "light-square", 7.5)
tl = proto("city-kit-roads", "traffic-light", 5.5)
for y in range(0, int(LEN), 24):
    for s in (-1, 1): place(lights, s * (ROAD + 0.6), y + (12 if s > 0 else 0), rot=0 if s > 0 else math.pi)
for c in CROSS:
    for s in (-1, 1): place(tl, s * (ROAD + 0.8), c - 7 * s, rot=0 if s > 0 else math.pi)

# ---------- traffic: a jam of cars, lots of yellow taxis
cars = [proto("car-kit", n, h) for n, h in (("taxi", 1.6), ("taxi", 1.6), ("taxi", 1.6), ("sedan", 1.5),
                                             ("suv", 1.8), ("van", 2.2), ("delivery", 2.8), ("police", 1.6),
                                             ("hatchback-sports", 1.4), ("truck", 3.2))]
for lane_x, rot in ((-5.8, 0), (-2.0, 0), (2.0, math.pi), (5.8, math.pi)):
    y = random.uniform(-6, 2)
    while y < 300:
        if not any(c - 7 < y < c + 7 for c in CROSS):
            col = random.choice(cars)
            place(col, lane_x + random.uniform(-0.2, 0.2), y, rot=rot + random.uniform(-0.04, 0.04))
            y += max(col["dx"], col["dy"]) + random.uniform(1.5, 4.0)
        else:
            y += 14

# ---------- people on the sidewalks
OUTFITS = ["Casual_2", "Casual_Hoodie", "Suit", "Suit", "Punk", "Worker", "Casual_2"]
def person(action):
    o = random.choice(OUTFITS)
    return proto("quaternius", o, 1.78, path=os.path.join(QM, o + ".gltf"), action=action,
                 offset=random.choice((0, 7, 13, 19)))
for _ in range(150):
    s = random.choice((-1, 1))
    x = s * (ROAD + random.uniform(0.8, WALK_W - 0.6)); y = random.uniform(-6, 160)
    act = random.choice(("Walk", "Walk", "Walk", "Idle_Neutral", "Idle"))
    place(person(act), x, y, z=0.16, rot=random.choice((0, math.pi)) + random.uniform(-0.15, 0.15),
          scale=random.uniform(0.94, 1.06))
for c in CROSS[:2]:                   # crowds crossing at the crosswalks
    for _ in range(14):
        place(person("Walk"), random.uniform(-ROAD + 1, ROAD - 1), c + random.uniform(-3, 3),
              rot=random.choice((-1, 1)) * math.pi / 2 + random.uniform(-0.2, 0.2))

# ---------- sky, sun, camera
w = bpy.data.worlds.new("sky"); sc.world = w; w.use_nodes = True
nt = w.node_tree; env = nt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(ASSETS, "polyhaven", "park_sky.hdr"))
nt.links.new(env.outputs["Color"], nt.nodes["Background"].inputs["Color"])
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 3.5; sun.data.angle = math.radians(2)
sun.rotation_euler = (math.radians(40), 0, math.radians(20)); sc.collection.objects.link(sun)

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cam.data.lens = 24; sc.camera = cam
cam.location = (0, -14, 9)
cam.rotation_euler = (math.radians(78), 0, 0)

try: sc.render.engine = "BLENDER_EEVEE"
except TypeError: sc.render.engine = "BLENDER_EEVEE_NEXT"
for k, v in (("taa_render_samples", 32), ("use_shadows", True), ("use_raytracing", False)):
    if hasattr(sc.eevee, k): setattr(sc.eevee, k, v)
sc.render.resolution_x, sc.render.resolution_y = RES, RES * 16 // 9
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"
sc.render.filepath = OUT
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sc.frame_set(10)
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.splitext(OUT)[0] + ".blend")
print("STREET_DONE")
