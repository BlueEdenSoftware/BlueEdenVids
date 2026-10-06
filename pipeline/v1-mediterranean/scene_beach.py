"""Tunisian beach (Hammamet-style) scene, metres. Sea level animates; sea floor slopes 1:40."""
import math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Euler
import common as C

SLOPE = 0.025          # seabed drop per metre offshore
SHORE_Y = 40.0         # waterline at level 0
RNG = random.Random(11)


def seabed_z(y):
    y = np.asarray(y, float)
    land = np.where(y < 0, 0.6 + (-y) * 0.035, 0.6 - 0.6 * y / SHORE_Y)
    sea = -(y - SHORE_Y) * SLOPE - np.clip(y - 2500, 0, None) * 0.02
    return np.where(y < SHORE_Y, land, sea)


def shoreline_y(level):
    if level >= 0:
        return SHORE_Y - level / (0.6 / SHORE_Y)
    y = SHORE_Y + (-level) / SLOPE
    if y > 2500:
        y = 2500 + (-level - 2460 * SLOPE) / (SLOPE + 0.02)
    return y


def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def node(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        n.inputs[k].default_value = v
    return n


class BeachScene:
    def __init__(self):
        sc = C.reset()
        self.sc = sc
        C.world(top="#2763c4", bottom="#c3dcef", strength=1.0, span=0.6)
        sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = -0.2
        C.sun(rot=(math.radians(62), 0, math.radians(-125)), strength=4.2, color="#ffe4c2", angle=1.0)
        self.cam = C.camera(lens=22, clip=(0.5, 20000))
        self._ground()
        self._water()
        self._town()
        self._palms()
        self._umbrellas()
        self._boats()
        self._people()
        self._headland()
        self.level = 0.0

    # ---------- ground with procedural sand / wet sand / seagrass ----------
    def _ground(self):
        xs = np.linspace(-1600, 1600, 161)
        ys = np.concatenate([np.linspace(-400, 0, 41), np.linspace(2, 300, 75)[0:], np.linspace(305, 4000, 140)])
        X, Y = np.meshgrid(xs, ys)
        rng = np.random.default_rng(2)
        Z = seabed_z(Y) + rng.normal(0, 0.12, Y.shape) * (Y > SHORE_Y + 20)
        # rocky reef bumps offshore
        hl = np.clip((-110 - X) / 70, 0, 1) * np.clip((520 - Y) / 120, 0, 1)
        Z = Z * (1 - hl) + hl * (3.0 + 6.0 * np.clip((-110 - X) / 200, 0, 1) + 0.002 * (Y + 400))
        self.HL = lambda x, y: 0.0
        Z += 1.2 * np.exp(-((X - 260) ** 2 + (Y - 700) ** 2) / 9000) + 0.9 * np.exp(-((X + 420) ** 2 + (Y - 1150) ** 2) / 14000)
        g = C.grid_mesh("Ground", X, Y, Z, flat=False)
        m = bpy.data.materials.new("GroundM"); m.use_nodes = True
        nt = m.node_tree; p = nt.nodes["Principled BSDF"]
        geo = node(nt, "ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
        self.lvl_node = nt.nodes.new("ShaderNodeValue"); self.lvl_node.outputs[0].default_value = 0.0
        # height above current water
        sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"
        nt.links.new(sep.outputs["Z"], sub.inputs[0]); nt.links.new(self.lvl_node.outputs[0], sub.inputs[1])
        wet = nt.nodes.new("ShaderNodeMapRange")
        wet.inputs["From Min"].default_value = 0.0; wet.inputs["From Max"].default_value = 2.5
        wet.inputs["To Min"].default_value = 1.0; wet.inputs["To Max"].default_value = 0.0
        nt.links.new(sub.outputs[0], wet.inputs["Value"])
        # original seabed (z<0.6) vs beach sand
        seab = nt.nodes.new("ShaderNodeMapRange")
        seab.inputs["From Min"].default_value = 0.6; seab.inputs["From Max"].default_value = -1.0
        nt.links.new(sep.outputs["Z"], seab.inputs["Value"])
        noise = node(nt, "ShaderNodeTexNoise", Scale=0.012, Detail=6.0)
        tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
        grass = nt.nodes.new("ShaderNodeMapRange")
        grass.inputs["From Min"].default_value = 0.56; grass.inputs["From Max"].default_value = 0.6
        nt.links.new(noise.outputs["Fac"], grass.inputs["Value"])
        g2 = nt.nodes.new("ShaderNodeMath"); g2.operation = "MULTIPLY"
        nt.links.new(grass.outputs[0], g2.inputs[0]); nt.links.new(seab.outputs[0], g2.inputs[1])
        g3 = nt.nodes.new("ShaderNodeMath"); g3.operation = "MULTIPLY"; g3.inputs[1].default_value = 0.7
        nt.links.new(g2.outputs[0], g3.inputs[0])

        def mix(fac, a, b):
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
            nt.links.new(fac, mx.inputs["Factor"])
            if isinstance(a, tuple): mx.inputs["A"].default_value = a
            else: nt.links.new(a, mx.inputs["A"])
            if isinstance(b, tuple): mx.inputs["B"].default_value = b
            else: nt.links.new(b, mx.inputs["B"])
            return mx.outputs["Result"]
        c = mix(seab.outputs[0], C.hexc("#e2bf82"), C.hexc("#b9a383"))       # beach sand -> seabed sand
        c = mix(g3.outputs[0], c, C.hexc("#6f7048"))                           # dead seagrass patches
        c = mix(wet.outputs[0], c, C.hexc("#8c7656"))                          # wet band at waterline
        # aerial haze
        cd = nt.nodes.new("ShaderNodeCameraData")
        fr = nt.nodes.new("ShaderNodeMapRange"); fr.name = "FogRange"
        fr.inputs["From Min"].default_value = 900; fr.inputs["From Max"].default_value = 6000
        fr.inputs["To Max"].default_value = 0.6
        nt.links.new(cd.outputs["View Distance"], fr.inputs["Value"])
        c = mix(fr.outputs["Result"], c, C.hexc("#f0dcc4"))
        nt.links.new(c, p.inputs["Base Color"])
        p.inputs["Roughness"].default_value = 0.95
        rip = node(nt, "ShaderNodeTexWave", Scale=0.12, Distortion=9.0, Detail=3.0)
        nt.links.new(tc.outputs["Object"], rip.inputs["Vector"])
        bmp = node(nt, "ShaderNodeBump", Strength=0.08, Distance=0.2)
        nt.links.new(rip.outputs["Fac"], bmp.inputs["Height"]); nt.links.new(bmp.outputs["Normal"], p.inputs["Normal"])
        g.data.materials.append(m)

    # ---------- water: colour by distance from shoreline, foam band, moving ripples ----------
    def _water(self):
        bpy.ops.mesh.primitive_plane_add(size=1)
        w = bpy.context.object; w.name = "Water"
        w.scale = (8000, 9000, 1); w.location = (0, 4500 - 300, 0)
        m = bpy.data.materials.new("WaterM"); m.use_nodes = True
        nt = m.node_tree; p = nt.nodes["Principled BSDF"]
        geo = node(nt, "ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
        self.shore_node = nt.nodes.new("ShaderNodeValue"); self.shore_node.outputs[0].default_value = SHORE_Y
        d = nt.nodes.new("ShaderNodeMath"); d.operation = "SUBTRACT"
        nt.links.new(sep.outputs["Y"], d.inputs[0]); nt.links.new(self.shore_node.outputs[0], d.inputs[1])
        deep = nt.nodes.new("ShaderNodeMapRange")
        deep.inputs["From Min"].default_value = 0; deep.inputs["From Max"].default_value = 260
        nt.links.new(d.outputs[0], deep.inputs["Value"])
        pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 0.6
        nt.links.new(deep.outputs[0], pw.inputs[0])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
        nt.links.new(pw.outputs[0], mx.inputs["Factor"])
        mx.inputs["A"].default_value = C.hexc("#5fd6cf"); mx.inputs["B"].default_value = C.hexc("#0e4f8a")
        # foam
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping"); self.wave_map = mp
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        fn = node(nt, "ShaderNodeTexNoise", Scale=60.0, Detail=4.0)
        nt.links.new(mp.outputs["Vector"], fn.inputs["Vector"])
        fb = nt.nodes.new("ShaderNodeMapRange")
        fb.inputs["From Min"].default_value = 0; fb.inputs["From Max"].default_value = 7
        fb.inputs["To Min"].default_value = 1; fb.inputs["To Max"].default_value = 0
        nt.links.new(d.outputs[0], fb.inputs["Value"])
        fm = nt.nodes.new("ShaderNodeMath"); fm.operation = "MULTIPLY"
        nt.links.new(fb.outputs[0], fm.inputs[0]); nt.links.new(fn.outputs["Fac"], fm.inputs[1])
        fs = nt.nodes.new("ShaderNodeMapRange")
        fs.inputs["From Min"].default_value = 0.25; fs.inputs["From Max"].default_value = 0.45
        nt.links.new(fm.outputs[0], fs.inputs["Value"])
        mx2 = nt.nodes.new("ShaderNodeMix"); mx2.data_type = "RGBA"
        nt.links.new(fs.outputs[0], mx2.inputs["Factor"])
        nt.links.new(mx.outputs["Result"], mx2.inputs["A"]); mx2.inputs["B"].default_value = C.hexc("#ffffff")
        cd = nt.nodes.new("ShaderNodeCameraData")
        fr = nt.nodes.new("ShaderNodeMapRange")
        fr.inputs["From Min"].default_value = 1500; fr.inputs["From Max"].default_value = 9000
        fr.inputs["To Max"].default_value = 0.55
        nt.links.new(cd.outputs["View Distance"], fr.inputs["Value"])
        mx3 = nt.nodes.new("ShaderNodeMix"); mx3.data_type = "RGBA"
        nt.links.new(fr.outputs["Result"], mx3.inputs["Factor"])
        nt.links.new(mx2.outputs["Result"], mx3.inputs["A"]); mx3.inputs["B"].default_value = C.hexc("#cfe0ea")
        nt.links.new(mx3.outputs["Result"], p.inputs["Base Color"])
        p.inputs["Roughness"].default_value = 0.06
        p.inputs["Specular IOR Level"].default_value = 0.7
        wn = node(nt, "ShaderNodeTexNoise", Scale=3.0, Detail=3.0)
        nt.links.new(mp.outputs["Vector"], wn.inputs["Vector"])
        bmp = node(nt, "ShaderNodeBump", Strength=0.12, Distance=0.2)
        nt.links.new(wn.outputs["Fac"], bmp.inputs["Height"]); nt.links.new(bmp.outputs["Normal"], p.inputs["Normal"])
        w.data.materials.append(m)
        self.water = w

    # ---------- whitewashed houses with blue doors / shutters ----------
    def _town(self):
        white = C.mat_basic("White", "#f4f1ea", rough=0.7)
        blue = C.mat_basic("Blue", "#1f5fa8", rough=0.5)
        dome = C.mat_basic("Dome", "#f7f5f0", rough=0.6)
        rnd = random.Random(4)
        for k in range(70):
            x = rnd.uniform(-420, -185); y = rnd.uniform(-200, 420)
            z0 = 3.0 + 6.0 * min(max((-110 - x) / 200, 0), 1) + 0.002 * (y + 400) - 0.3
            w_, d_, h_ = rnd.uniform(8, 18), rnd.uniform(8, 16), rnd.choice([4.5, 7.5, 10.5])
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z0 + h_ / 2))
            b = bpy.context.object; b.scale = (w_, d_, h_); b.data.materials.append(white)
            b.rotation_euler.z = math.radians(rnd.uniform(-8, 8))
            # door + two windows facing the sea (+y)
            for dy, dz, sy, sz in [(0, 1.1, 1.4, 2.2), (-d_ * 0.3, h_ - 2.2, 1.2, 1.2), (d_ * 0.3, h_ - 2.2, 1.2, 1.2)]:
                bpy.ops.mesh.primitive_cube_add(size=1, location=(x + w_ / 2 + 0.05, y + dy, z0 + dz))
                o = bpy.context.object; o.scale = (0.25, sy, sz); o.data.materials.append(blue)
            if rnd.random() < 0.18:
                bpy.ops.mesh.primitive_uv_sphere_add(radius=min(w_, d_) * 0.33, location=(x, y, z0 + h_), segments=16, ring_count=8)
                o = bpy.context.object; o.scale.z = 0.8; o.data.materials.append(dome)
        # promenade wall along the beach


    def _palms(self):
        trunk = C.mat_basic("Trunk", "#8a6a48", rough=0.9)
        leaf = C.mat_basic("Leaf", "#3f8a3a", rough=0.7)
        rnd = random.Random(7)
        spots = [(rnd.uniform(-100, 200), rnd.uniform(-70, -8)) for _ in range(22)] + [(rnd.uniform(-170, -120), rnd.uniform(0, 300)) for _ in range(10)]
        for x, y in spots:
            z0 = float(seabed_z(y)); h = rnd.uniform(8, 13); lean = rnd.uniform(-0.15, 0.15)
            bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.32, depth=h, location=(x + lean * h / 2, y, z0 + h / 2))
            t = bpy.context.object; t.rotation_euler.y = lean; t.data.materials.append(trunk)
            top = Vector((x + lean * h, y, z0 + h))
            for a in range(7):
                ang = a / 7 * 2 * math.pi + rnd.uniform(0, 0.5)
                bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.9, depth=5.5, location=top + Vector((math.cos(ang) * 2.4, math.sin(ang) * 2.4, -0.6)))
                l = bpy.context.object
                l.rotation_euler = Euler((math.radians(118), 0, ang - math.pi / 2), "XYZ")
                l.scale = (1, 0.25, 1); l.data.materials.append(leaf)

    def _umbrellas(self):
        straw = C.mat_basic("Straw", "#c9a467", rough=0.9)
        pole = C.mat_basic("Pole", "#6b5137", rough=0.9)
        towel_cols = ["#e85d5d", "#f2c14e", "#3fa7d6", "#59cd90", "#ffffff", "#ee6c4d"]
        towels = [C.mat_basic(f"T{k}", c, rough=0.9) for k, c in enumerate(towel_cols)]
        rnd = random.Random(9)
        self.beach_spots = []
        for k in range(44):
            x = rnd.uniform(-70, 110); y = rnd.uniform(3, 30)
            z0 = float(seabed_z(y))
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.06, depth=2.4, location=(x, y, z0 + 1.2))
            bpy.context.object.data.materials.append(pole)
            bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=1.6, depth=0.7, location=(x, y, z0 + 2.45))
            bpy.context.object.data.materials.append(straw)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x + 1.2, y - 0.5, z0 + 0.03))
            o = bpy.context.object; o.scale = (0.9, 1.9, 0.04); o.data.materials.append(rnd.choice(towels))
            self.beach_spots.append((x, y))

    def _boats(self):
        hull_w = C.mat_basic("HullW", "#f3f3f0", rough=0.5)
        hull_b = C.mat_basic("HullB", "#1d64b5", rough=0.5)
        self.boats = []
        rnd = random.Random(5)
        near = [(-5, 75), (30, 95), (55, 130), (-35, 160), (10, 210), (80, 250), (-60, 300), (40, 330), (120, 180)]
        for k in range(9):
            bm = bmesh.new()
            L, Wd, Hh = rnd.uniform(6, 9), rnd.uniform(2.2, 2.8), 1.1
            vs = [bm.verts.new(v) for v in [(-L/2, -Wd/2, Hh), (L/2 - 1.5, -Wd/2, Hh), (L/2, 0, Hh), (L/2 - 1.5, Wd/2, Hh), (-L/2, Wd/2, Hh),
                                             (-L/2 + 0.6, -Wd/2 + 0.6, 0), (L/2 - 1.8, -0.4, 0), (L/2 - 1.2, 0, 0.1), (L/2 - 1.8, 0.4, 0), (-L/2 + 0.6, Wd/2 - 0.6, 0)]]
            bm.faces.new(vs[:5]); bm.faces.new(vs[5:][::-1])
            for i in range(5):
                bm.faces.new([vs[i], vs[(i + 1) % 5], vs[5 + (i + 1) % 5], vs[5 + i]])
            me = bpy.data.meshes.new("Boat"); bm.to_mesh(me); bm.free()
            me.materials.append(hull_w); me.materials.append(hull_b)
            for i, f in enumerate(me.polygons):
                f.material_index = 1 if (i >= 2 and f.center.z < 0.55) else 0
            b = link(bpy.data.objects.new("Boat", me))
            bpy.ops.mesh.primitive_cube_add(size=1)
            cab = bpy.context.object; cab.scale = (1.6, 1.4, 1.1); cab.parent = b; cab.location = (-0.8, 0, 1.6)
            cab.data.materials.append(hull_w)
            x, y = near[k]
            b.rotation_euler.z = rnd.uniform(0, math.pi)
            self.boats.append([b, x, y, rnd.uniform(-0.35, 0.35), rnd.uniform(-0.2, 0.2)])

    def _people(self):
        skins = [C.mat_basic(f"S{k}", c, rough=0.6) for k, c in enumerate(["#8d5b3e", "#c68a62", "#e0b08c", "#6b4430"])]
        cloth = [C.mat_basic(f"C{k}", c, rough=0.8) for k, c in enumerate(["#d94848", "#2b6cb0", "#f2c14e", "#2f855a", "#ffffff", "#805ad5", "#ed8936", "#1a202c"])]
        # shared meshes
        bpy.ops.mesh.primitive_cube_add(size=1); body_me = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, segments=8, ring_count=6); head_me = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
        body_me.materials.append(skins[0]); head_me.materials.append(skins[0])
        rnd = random.Random(21)
        self.people = []
        for k in range(110):
            root = link(bpy.data.objects.new("P", None))
            sk = rnd.choice(skins); cl = rnd.choice(cloth)
            h = rnd.uniform(1.55, 1.85)
            for (sx, sy, sz, z, mat) in [(0.13, 0.13, h * 0.47, h * 0.235, sk), (0.13, 0.13, h * 0.47, h * 0.235, sk),
                                         (0.36, 0.2, h * 0.32, h * 0.62, cl)]:
                o = link(bpy.data.objects.new("Pb", body_me)); o.parent = root
                o.scale = (sx, sy, sz); o.location = (0, 0, z)
                o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = mat
            legs = root.children
            legs[0].location.x = -0.09; legs[1].location.x = 0.09
            hd = link(bpy.data.objects.new("Ph", head_me)); hd.parent = root; hd.location = (0, 0, h * 0.9)
            hd.material_slots[0].link = "OBJECT"; hd.material_slots[0].material = sk
            # spots: beach start, far-out position (year 10), walking speed
            if k < len(self.beach_spots) * 2:
                bx, by = self.beach_spots[k % len(self.beach_spots)]
                start = (bx + rnd.uniform(-3, 3), by + rnd.uniform(-2, 6))
            else:
                start = (rnd.uniform(-70, 120), rnd.uniform(26, 50))
            far = (rnd.uniform(-90, 140), rnd.uniform(45, 360))
            self.people.append(dict(root=root, start=start, far=far, rot=rnd.uniform(0, 2 * math.pi), v=rnd.uniform(0.6, 1.6)))

    def _headland(self):
        # Cap Bon style low hills far on the right horizon
        xs = np.linspace(1500, 9000, 60); ys = np.linspace(3500, 12000, 60)
        X, Y = np.meshgrid(xs, ys)
        Z = 180 * np.exp(-((X - 5200) ** 2) / 4e6) * np.clip((Y - 3500) / 2500, 0, 1) + 40 * np.sin(Y / 700) - 30
        h = C.grid_mesh("Headland", X, Y, Z, flat=False)
        h.data.materials.append(C.mat_basic("Hills", "#b9b69a", rough=0.95))

    # ---------- per-frame state ----------
    def set_state(self, level, t, mode):
        self.level = level
        self.lvl_node.outputs[0].default_value = level
        self.shore_node.outputs[0].default_value = shoreline_y(level)
        self.water.location.z = level
        self.wave_map.inputs["Location"].default_value = (t * 0.6, t * 1.1, 0)
        for b, x, y, rx, ry in self.boats:
            zb = float(seabed_z(y))
            if level > zb + 0.5:
                b.location = (x, y, level - 0.45 + 0.05 * math.sin(t * 2 + x))
                b.rotation_euler.x = 0.03 * math.sin(t * 1.3 + y); b.rotation_euler.y = 0.0
            else:
                b.location = (x, y, zb - 0.1)
                b.rotation_euler.x = rx; b.rotation_euler.y = ry
        for p in self.people:
            if mode == "far":
                x, y = p["far"]
            else:
                x, y = p["start"]
            z = float(seabed_z(y))
            vis = z > level + 0.2 or mode != "far"
            p["root"].location = (x, y, z)
            p["root"].rotation_euler.z = p["rot"]
            p["root"].hide_render = not vis
            for c in p["root"].children:
                c.hide_render = not vis

    def set_camera(self, loc, target, lens=22):
        self.cam.data.lens = lens
        C.look_at(self.cam, loc, target)

    def render(self, path):
        self.sc.render.filepath = path
        bpy.ops.render.render(write_still=True)


CAMS = {
    "beach_hook": dict(loc=(45, -48, 21), target=(-12, 130, -2), lens=26),
    "beach_far": dict(loc=(55, -20, 26), target=(-15, 420, -9), lens=28),
}

if __name__ == "__main__":
    import time, sys
    s = BeachScene()
    s.sc.cycles.samples = int(sys.argv[-1])
    for name, lv, mode, cam in [("b0", 0.0, "start", "beach_hook"), ("b1", -7.0, "start", "beach_hook"), ("b2", -23.0, "far", "beach_far")]:
        s.set_state(lv, 0.0, mode); s.set_camera(**CAMS[cam])
        t = time.time(); s.render(f"/home/claude/pe/v2/t_{name}.png"); print(name, round(time.time() - t, 1), flush=True)
