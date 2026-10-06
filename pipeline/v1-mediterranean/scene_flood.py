"""Zanclean flood: the Atlantic pours through the Gibraltar gap into the dry Mediterranean basin.
Units: km horizontally, vertical exaggeration VX (BU = km * VX)."""
import math
import numpy as np
import bpy
import common as C

VX = 4.0
FLOOR = -3.3 * VX
RAMP_END = 46.0


def channel_y(x):
    return 2.5 * np.sin(x / 9.0) + 1.5 * np.sin(x / 3.7)


def channel_bottom(x):
    x = np.asarray(x, float)
    u = np.clip(x / RAMP_END, 0, 1)
    return np.where(x < 0, -0.25 * VX, -0.25 * VX + (FLOOR + 0.6 - -0.25 * VX) * (u ** 1.6))


def terrain(X, Y):
    rng = np.random.default_rng(4)
    yc = channel_y(X)
    d = np.abs(Y - yc)
    # ridges either side of the gap (Spain north, Morocco south), opening out east of the ramp
    width = 5.0 + np.clip(X - 20, 0, None) * 0.9
    ridge = np.clip((d - width) / 6.0, 0, 1) ** 0.8 * (1.3 * VX) * np.exp(-np.clip(X - 70, 0, None) / 60.0)
    ridge *= (1 + 0.35 * np.sin(X / 5.3 + Y / 4.1) * np.sin(Y / 7.7))
    base = np.where(X < 0, -0.5 * VX, 0.0)
    gorge = channel_bottom(X) - 0.15 * VX * np.exp(-(d / 2.2) ** 2)
    # basin floor: undulating, with salt-white low areas handled by the shader
    basin = FLOOR + 0.8 * np.sin(X / 13) * np.cos(Y / 11) + 0.4 * np.sin(Y / 4.3 + X / 6.1)
    east = np.clip((X - RAMP_END + 8) / 16, 0, 1)
    gorge_mix = np.exp(-(d / (width * 0.9)) ** 2)
    Z = np.where(X < 0, base, gorge * gorge_mix + (1 - gorge_mix) * np.maximum(gorge, 0.3 * VX) * (1 - east))
    Z = Z * (1 - east) + basin * east
    Z = np.maximum(Z, Z) + ridge
    Z += rng.normal(0, 0.05, Z.shape)
    return Z


class FloodScene:
    def __init__(self):
        sc = C.reset()
        self.sc = sc
        sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = -0.2
        C.world(top="#2a64c2", bottom="#c9dceb", strength=1.0, span=0.5)
        C.sun(rot=(math.radians(50), 0, math.radians(-60)), strength=4.0, color="#fff0dc")
        self.cam = C.camera(lens=24, clip=(0.05, 5000))
        xs = np.linspace(-80, 260, 341); ys = np.linspace(-90, 90, 181)
        X, Y = np.meshgrid(xs, ys)
        Z = terrain(X, Y)
        self.Z = Z
        t = C.grid_mesh("Terrain", X, Y, Z, flat=False)
        m = bpy.data.materials.new("TerrM"); m.use_nodes = True
        nt = m.node_tree; p = nt.nodes["Principled BSDF"]
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
        cr = nt.nodes.new("ShaderNodeValToRGB")
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = FLOOR; mr.inputs["From Max"].default_value = 1.4 * VX
        nt.links.new(sep.outputs["Z"], mr.inputs["Value"]); nt.links.new(mr.outputs[0], cr.inputs[0])
        el = cr.color_ramp.elements
        el[0].position = 0.0; el[0].color = C.hexc("#efe9dc")          # salt floor
        el[1].position = 0.12; el[1].color = C.hexc("#c9ad84")         # dry seabed
        for pos, col in [(0.55, "#a88d68"), (0.72, "#7f9b55"), (0.88, "#5f7f45"), (1.0, "#b8ab93")]:
            e = el.new(pos); e.color = C.hexc(col)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.4; nz.inputs["Detail"].default_value = 8
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.4; bm.inputs["Distance"].default_value = 0.3
        nt.links.new(nz.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], p.inputs["Normal"])
        cd = nt.nodes.new("ShaderNodeCameraData")
        fr = nt.nodes.new("ShaderNodeMapRange"); fr.inputs["From Min"].default_value = 40; fr.inputs["From Max"].default_value = 230
        fr.inputs["To Max"].default_value = 1.0
        nt.links.new(cd.outputs["View Distance"], fr.inputs["Value"])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
        nt.links.new(fr.outputs["Result"], mx.inputs["Factor"]); nt.links.new(cr.outputs["Color"], mx.inputs["A"])
        mx.inputs["B"].default_value = C.hexc("#c9dceb")
        nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
        p.inputs["Roughness"].default_value = 0.95
        t.data.materials.append(m)
        self.fog_nodes = [fr]

        # Atlantic (z = 0) west of the gap
        bpy.ops.mesh.primitive_plane_add(size=1, location=(-45, 0, 0))
        atl = bpy.context.object; atl.scale = (90, 200, 1)
        atl.data.materials.append(self._water_mat("AtlM", "#1a6aa8", "#0b3b6e"))

        # torrent: ribbon following the gorge, from x=-6 down to the basin
        n = 260
        xr = np.linspace(-6, RAMP_END + 6, n)
        yr = channel_y(xr)
        zr = channel_bottom(xr) + 0.22 * VX * (1 - np.clip(xr / RAMP_END, 0, 1)) + 0.05
        zr = np.where(xr < 0, -0.02 + xr * 0.0, zr)
        half = 2.4 + np.clip(xr, 0, None) * 0.03
        Xg = np.stack([xr] * 9); Yg = np.stack([yr + half * k for k in np.linspace(-1, 1, 9)])
        Zg = np.stack([zr + 0.25 * (1 - abs(k)) for k in np.linspace(-1, 1, 9)])
        self.torrent = C.grid_mesh("Torrent", Xg, Yg, Zg, flat=False)
        self.torrent.data.materials.append(self._torrent_mat())
        self.tor_x, self.tor_z = xr, zr

        # Mediterranean lake rising in the basin
        bpy.ops.mesh.primitive_plane_add(size=1, location=(150, 0, FLOOR))
        self.lake = bpy.context.object; self.lake.scale = (240, 200, 1)
        self.lake.data.materials.append(self._water_mat("LakeM", "#2bb5c4", "#0d4a80"))

        # spray cloud where the torrent hits the lake
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0)
        self.spray = bpy.context.object; self.spray.scale = (7, 6, 2.6)
        sm = bpy.data.materials.new("Spray"); sm.use_nodes = True
        snt = sm.node_tree; snt.nodes.remove(snt.nodes["Principled BSDF"])
        vol = snt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Color"].default_value = C.hexc("#ffffff")
        tcs = snt.nodes.new("ShaderNodeTexCoord")
        ns = snt.nodes.new("ShaderNodeTexNoise"); ns.noise_dimensions = "4D"; ns.inputs["Scale"].default_value = 2.5; ns.inputs["Detail"].default_value = 4
        self.spray_noise = ns
        snt.links.new(tcs.outputs["Object"], ns.inputs["Vector"])
        grad = snt.nodes.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
        snt.links.new(tcs.outputs["Object"], grad.inputs["Vector"])
        mul = snt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        snt.links.new(ns.outputs["Fac"], mul.inputs[0]); snt.links.new(grad.outputs["Fac"], mul.inputs[1])
        mul2 = snt.nodes.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"; mul2.inputs[1].default_value = 6.0
        snt.links.new(mul.outputs[0], mul2.inputs[0])
        snt.links.new(mul2.outputs[0], vol.inputs["Density"])
        snt.links.new(vol.outputs[0], snt.nodes["Material Output"].inputs["Volume"])
        self.spray.data.materials.append(sm)

    def _water_mat(self, name, a, b):
        m = bpy.data.materials.new(name); m.use_nodes = True
        nt = m.node_tree; p = nt.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = C.hexc(a)
        p.inputs["Roughness"].default_value = 0.08
        p.inputs["Specular IOR Level"].default_value = 0.6
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.8
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.1
        nt.links.new(nz.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], p.inputs["Normal"])
        return m

    def _torrent_mat(self):
        m = bpy.data.materials.new("Torrent"); m.use_nodes = True
        nt = m.node_tree; p = nt.nodes["Principled BSDF"]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping"); self.flow_map = mp
        mp.inputs["Scale"].default_value = (0.35, 1.6, 1.0)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.4; nz.inputs["Detail"].default_value = 6
        nz.inputs["Distortion"].default_value = 1.5
        nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        cr = nt.nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].position = 0.38; cr.color_ramp.elements[0].color = C.hexc("#2c9fb8")
        cr.color_ramp.elements[1].position = 0.62; cr.color_ramp.elements[1].color = C.hexc("#f4fbff")
        nt.links.new(nz.outputs["Fac"], cr.inputs[0])
        nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Emission Color"].default_value = C.hexc("#ffffff")
        em = nt.nodes.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 0.35
        nt.links.new(nz.outputs["Fac"], em.inputs[0]); nt.links.new(em.outputs[0], p.inputs["Emission Strength"])
        p.inputs["Roughness"].default_value = 0.35
        bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.6
        nt.links.new(nz.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], p.inputs["Normal"])
        return m

    def set_state(self, level_m, t):
        z = level_m / 1000.0 * VX
        self.lake.location.z = z
        self.flow_map.inputs["Location"].default_value = (-t * 9.0, 0, 0)
        self.spray_noise.inputs["W"].default_value = t * 0.8
        # impact point: where the torrent surface meets the lake
        i = int(np.argmax(self.tor_z <= z + 0.2)) if (self.tor_z <= z + 0.2).any() else len(self.tor_z) - 1
        xi = float(self.tor_x[i])
        self.spray.location = (xi + 3, float(channel_y(xi)), z + 0.8)
        s = 1.0 - 0.5 * min(max((z - FLOOR) / (-FLOOR), 0), 1)
        self.spray.scale = (7 * s, 6 * s, 2.6 * s)
        self.spray.hide_render = xi < 1.0

    def set_camera(self, loc, target, lens=24):
        self.cam.data.lens = lens
        C.look_at(self.cam, loc, target)

    def render(self, path):
        self.sc.render.filepath = path
        bpy.ops.render.render(write_still=True)


CAM = dict(loc=(-16, -2.0, 4.2), target=(45, 1.0, -9.5), lens=20)

if __name__ == "__main__":
    import time, sys
    s = FloodScene()
    s.sc.cycles.samples = int(sys.argv[-1])
    for name, lv in [("f0", -3200), ("f1", -1500), ("f2", -100)]:
        s.set_state(lv, 0.5); s.set_camera(**CAM)
        t = time.time(); s.render(f"/home/claude/pe/v2/t_{name}.png"); print(name, round(time.time() - t, 1), flush=True)
