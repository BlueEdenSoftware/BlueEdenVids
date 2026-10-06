"""Mediterranean map scene in Blender (km units, vertical exaggeration EX)."""
import math
import numpy as np
import bpy
from scipy import ndimage
import common as C

EX = 25.0
UP = 2

D = np.load("/home/claude/pe/v2/terrain_big.npz")
TOPO0, LAT0, LON0, MED0 = D["topo"], D["lat"], D["lon"], D["med"]
TOPO = ndimage.zoom(TOPO0, UP, order=3).astype(np.float32)
MED = ndimage.zoom(MED0.astype(np.uint8), UP, order=0).astype(bool)
LAT = np.linspace(LAT0[0], LAT0[-1], TOPO.shape[0])
LON = np.linspace(LON0[0], LON0[-1], TOPO.shape[1])
LONG, LATG = np.meshgrid(LON, LAT)
KX = 111.32 * math.cos(math.radians(38.0)); KY = 111.32
X = (LONG - LON[0]) * KX
Y = (LATG - LAT[0]) * KY
ZT = TOPO / 1000.0 * EX


def xy(lon, lat):
    return (lon - LON[0]) * KX, (lat - LAT[0]) * KY


def lin(h):
    return np.array(C.hexc(h)[:3], np.float32)


PAL = {k: lin(v) for k, v in dict(
    grass="6aa84f", forest="3f7f46", rock="9a8a70", snow="f2f0ea", sand="e0bd78", dune="cf9d55",
    wet="8a7458", bed="c4a57a", bedpale="b99a70", salt="e9e2d3", shallow="2fc2cc", deep="0a3f73",
    salty="9fe3dc").items()}


def land_colors():
    t = np.clip(TOPO / 2600.0, 0, 1)[..., None]
    g = np.clip(t * 2.2, 0, 1)
    green = PAL["grass"] * (1 - g) + PAL["forest"] * g
    hi = np.clip((t - 0.45) / 0.55, 0, 1)
    col = np.where(t < 0.45, green, PAL["rock"] * (1 - hi) + PAL["snow"] * hi)
    desert = np.clip((35.0 - LATG) / 2.2, 0, 1)[..., None] * (LONG[..., None] < 36.5)
    dcol = PAL["sand"] * (1 - t) + PAL["dune"] * t
    return col * (1 - desert) + dcol * desert


LANDC = land_colors()
JIT = np.random.default_rng(5).uniform(0.93, 1.07, TOPO.shape)[..., None].astype(np.float32)


def terrain_colors(level_m):
    sea = TOPO < 0
    above = np.clip(TOPO - level_m, 0, None)               # metres the cell sits above current water
    depth = -TOPO
    bed = PAL["bed"] * (1 - np.clip(depth / 2500, 0, 1)[..., None]) + PAL["bedpale"] * np.clip(depth / 2500, 0, 1)[..., None]
    fresh = np.clip(1 - above / 120.0, 0, 1)[..., None]    # freshly exposed = wet & dark
    bed = bed * (1 - fresh) + PAL["wet"] * fresh
    salty = (np.clip((depth - 1200) / 900, 0, 1) * np.clip(above / 350, 0, 1))[..., None]
    bed = bed * (1 - salty) + PAL["salt"] * salty
    col = np.where((sea & MED)[..., None], bed, LANDC)
    col = np.where((sea & ~MED)[..., None], PAL["bed"], col)
    return (col * JIT).astype(np.float32)


def water_colors(level_m, z_m):
    depth = np.clip(z_m - TOPO, 0, 5000)
    t = np.clip(depth / 1800.0, 0, 1)[..., None] ** 0.55
    col = PAL["shallow"] * (1 - t) + PAL["deep"] * t
    # very salty remnant lakes go milky turquoise
    s = np.clip((-level_m - 1500) / 1200, 0, 1)
    col = col * (1 - 0.6 * s) + PAL["salty"] * (0.6 * s)
    return col.astype(np.float32)


class MapScene:
    def __init__(self):
        sc = C.reset()
        self.sc = sc
        C.world(top="#2c66bd", bottom="#c6dbea", strength=1.5)
        C.sun(rot=(math.radians(55), 0, math.radians(200)), strength=4.5)
        self.cam = C.camera(lens=26, clip=(1.0, 30000))
        fog = ("#c6dbea", 1500.0, 7000.0, 1.0)
        self.fog_mat = None
        self.terrain = C.grid_mesh("Terrain", X, Y, ZT)
        C.set_colors(self.terrain, "Col", terrain_colors(0.0))
        self.terrain_mat = C.attr_material("TerrainM", "Col", rough=0.92, fog=fog, spec=0.2, bump=(0.06, 0.35, 2.0))
        self.terrain.data.materials.append(self.terrain_mat)
        # Med water: quads where the Med (dilated) is
        medd = ndimage.binary_dilation(MED, iterations=3)
        fm = medd[:-1, :-1] | medd[1:, 1:]
        self.medw = C.grid_mesh("MedWater", X, Y, np.zeros_like(ZT), face_mask=fm)
        wm = C.attr_material("WaterM", "WCol", rough=0.08, fog=fog, spec=0.6)
        self.mats = [self.terrain_mat, wm]
        self.medw.data.materials.append(wm)
        # Atlantic + Black Sea water at 0
        reg = (LONG < -5.55) | ((LONG > 26.0) & (LATG > 40.3)) | ((LONG > 32.3) & (LATG < 30.0)) | (LATG > 47.6)
        outer = (TOPO < 0) & ~MED & reg
        outer = ndimage.binary_dilation(outer, iterations=3) & reg
        fo = outer[:-1, :-1] & outer[1:, 1:]
        self.ocean = C.grid_mesh("Ocean", X, Y, np.zeros_like(ZT), face_mask=fo)
        C.set_colors(self.ocean, "WCol", water_colors(0.0, np.zeros_like(TOPO)))
        self.ocean.data.materials.append(wm)
        # Gibraltar dam
        x0, y0 = xy(-5.6, 35.84); x1, y1 = xy(-5.6, 36.16)
        bpy.ops.mesh.primitive_cube_add(size=1)
        dam = bpy.context.object; dam.name = "Dam"
        dam.dimensions = (12.0, y1 - y0 + 6, 0.4 * EX)
        dam.location = (x0, (y0 + y1) / 2, -0.4 * EX / 2 + 1.2)
        dam.data.materials.append(C.mat_basic("DamM", "#e9e5dc", rough=0.6, emit="#e8e4dc", emit_strength=1.6))
        self.dam = dam
        self.dam_full_z = dam.location.z
        self.level = None

    def set_level(self, level_m, dam=1.0):
        lv = float(level_m)
        if self.level is None or abs(lv - self.level) > 0.5:
            C.set_colors(self.terrain, "Col", terrain_colors(lv))
            zw = np.where(MED | ndimage.binary_dilation(MED, iterations=3), lv, 0.0)
            C.set_z(self.medw, zw / 1000.0 * EX)
            C.set_colors(self.medw, "WCol", water_colors(lv, np.full_like(TOPO, lv)))
            self.level = lv
        # dam rises from below (dam=0 hidden, 1 full)
        self.dam.location.z = self.dam_full_z - (1 - dam) * 1.0
        self.dam.hide_render = dam <= 0.001

    def set_camera(self, lon, lat, heading, pitch, dist, tz=0.0, fog=(1.0, 2.2)):
        tx, ty = xy(lon, lat)
        h, p = math.radians(heading), math.radians(pitch)
        cx = tx - dist * math.cos(p) * math.sin(h)
        cy = ty - dist * math.cos(p) * math.cos(h)
        cz = tz + dist * math.sin(p)
        C.look_at(self.cam, (cx, cy, cz), (tx, ty, tz))
        for m in self.mats:
            fr = m.node_tree.nodes["FogRange"]
            fr.inputs["From Min"].default_value = dist * fog[0]
            fr.inputs["From Max"].default_value = dist * fog[1]

    def render(self, path):
        self.sc.render.filepath = path
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    import time, sys
    s = MapScene()
    tests = [("gib", dict(lon=-4.9, lat=36.0, heading=72, pitch=45, dist=600), 0.0, 1.0),
             ("wide", dict(lon=10, lat=38, heading=80, pitch=30, dist=2100), -454, 1.0),
             ("abyss", dict(lon=19.0, lat=34.6, heading=40, pitch=16, dist=520, tz=-70, fog=(1.4, 4.0)), -3000, 1.0)]
    s.sc.cycles.samples = int(sys.argv[-1])
    for name, cam, lv, dm in tests:
        s.set_level(lv + 1, dm); s.set_camera(**cam)
        t = time.time(); s.render(f"/home/claude/pe/v2/t_{name}.png"); print(name, round(time.time() - t, 1), flush=True)


# ---------------- flood: the Atlantic pours back in through Gibraltar ----------------
from scipy.ndimage import map_coordinates as _mc

PATH = [(-5.75, 35.96), (-5.3, 35.97), (-4.6, 36.0), (-3.4, 35.98), (-2.2, 36.15), (-0.8, 36.6),
        (0.8, 37.1), (2.6, 37.5), (4.6, 37.9), (6.4, 38.3)]


def _sample_topo(lon, lat):
    fi = (np.asarray(lat) - LAT[0]) / (LAT[1] - LAT[0])
    fj = (np.asarray(lon) - LON[0]) / (LON[1] - LON[0])
    return _mc(TOPO, [fi, fj], order=1)


def add_torrent(scene):
    pts = np.array(PATH)
    seg = np.r_[0, np.cumsum(np.hypot(np.diff(pts[:, 0]) * KX, np.diff(pts[:, 1]) * KY))]
    s = np.linspace(0, seg[-1], 400)
    lon = np.interp(s, seg, pts[:, 0]); lat = np.interp(s, seg, pts[:, 1])
    # min of topo across the channel width so the river sits in the valley
    dlon = np.gradient(lon); dlat = np.gradient(lat)
    nx_, ny_ = -dlat * KY, dlon * KX
    nn = np.hypot(nx_, ny_); nx_ /= nn; ny_ /= nn
    half = np.interp(s, [0, 120, seg[-1]], [8.0, 10.0, 26.0])          # km half-width
    ks = np.linspace(-1, 1, 11)
    Xs = np.array([(lon - LON[0]) * KX + nx_ * half * k for k in ks])
    Ys = np.array([(lat - LAT[0]) * KY + ny_ * half * k for k in ks])
    LONs = np.array([lon + (nx_ * half * k) / KX for k in ks]); LATs = np.array([lat + (ny_ * half * k) / KY for k in ks])
    cross = _sample_topo(LONs.ravel(), LATs.ravel()).reshape(LONs.shape)
    bed = np.max(cross[4:-4], axis=0)                                   # follow the valley floor
    bed = np.minimum(bed, -5.0)
    bed = np.convolve(np.pad(bed, 6, mode='edge'), np.ones(13) / 13, mode='valid')
    scene.tor_s, scene.tor_bed, scene.tor_lon, scene.tor_lat = s, bed, lon, lat
    Z = np.array([_sample_topo(lon + (nx_ * half * k) / KX, lat + (ny_ * half * k) / KY).clip(None, -5) / 1000 * EX * 0.0 + bed / 1000 * EX + 1.0 * (1 - 0.7 * abs(k)) + 0.5 for k in ks])
    ob = C.grid_mesh("Torrent", Xs, Ys, Z, flat=False)
    uv = np.zeros((len(ks), len(s), 3), np.float32)
    uv[..., 0] = s[None, :] / 10.0
    uv[..., 1] = ks[:, None]
    C.set_colors(ob, "UVW", uv)
    m = bpy.data.materials.new("TorrentM"); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "UVW"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(at.outputs["Color"], sep.inputs[0])
    off = nt.nodes.new("ShaderNodeMath"); off.operation = "SUBTRACT"
    scene.tor_time = off
    nt.links.new(sep.outputs[0], off.inputs[0])
    cx = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(off.outputs[0], cx.inputs["X"])
    mg = nt.nodes.new("ShaderNodeMath"); mg.operation = "MULTIPLY"; mg.inputs[1].default_value = 3.0
    nt.links.new(sep.outputs[1], mg.inputs[0]); nt.links.new(mg.outputs[0], cx.inputs["Y"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 7
    nz.inputs["Distortion"].default_value = 1.2
    nt.links.new(cx.outputs[0], nz.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.40; cr.color_ramp.elements[0].color = C.hexc("#2a95b5")
    cr.color_ramp.elements[1].position = 0.60; cr.color_ramp.elements[1].color = C.hexc("#f7fcff")
    nt.links.new(nz.outputs["Fac"], cr.inputs[0])
    nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Emission Color"].default_value = C.hexc("#ffffff")
    em = nt.nodes.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 0.4
    nt.links.new(nz.outputs["Fac"], em.inputs[0]); nt.links.new(em.outputs[0], p.inputs["Emission Strength"])
    p.inputs["Roughness"].default_value = 0.3
    ob.data.materials.append(m)
    scene.torrent = ob
    # spray / mist where the river meets the rising sea
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0)
    sp = bpy.context.object; sp.name = "Spray"
    sm = bpy.data.materials.new("SprayM"); sm.use_nodes = True
    snt = sm.node_tree; snt.nodes.remove(snt.nodes["Principled BSDF"])
    vol = snt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = C.hexc("#ffffff")
    vol.inputs["Emission Color"].default_value = C.hexc("#ffffff"); vol.inputs["Emission Strength"].default_value = 0.25
    tc = snt.nodes.new("ShaderNodeTexCoord")
    ns = snt.nodes.new("ShaderNodeTexNoise"); ns.noise_dimensions = "4D"; ns.inputs["Scale"].default_value = 2.2
    scene.spray_noise = ns
    snt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    gr = snt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
    snt.links.new(tc.outputs["Object"], gr.inputs["Vector"])
    mu = snt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"
    snt.links.new(ns.outputs["Fac"], mu.inputs[0]); snt.links.new(gr.outputs["Fac"], mu.inputs[1])
    mu2 = snt.nodes.new("ShaderNodeMath"); mu2.operation = "MULTIPLY"; mu2.inputs[1].default_value = 0.25
    snt.links.new(mu.outputs[0], mu2.inputs[0]); snt.links.new(mu2.outputs[0], vol.inputs["Density"])
    snt.links.new(vol.outputs[0], snt.nodes["Material Output"].inputs["Volume"])
    sp.data.materials.append(sm)
    scene.spray = sp


def set_torrent(scene, level_m, t):
    scene.tor_time.inputs[1].default_value = t * 2.2
    scene.spray_noise.inputs["W"].default_value = t * 0.7
    wet = scene.tor_bed <= level_m
    i = int(np.argmax(wet)) if wet.any() else len(scene.tor_bed) - 1
    x, y = xy(scene.tor_lon[i], scene.tor_lat[i])
    z = level_m / 1000 * EX
    scene.spray.location = (x, y, z + 3)
    r = 22.0
    scene.spray.scale = (r, r, 6.0)
    scene.spray.hide_render = True
