"""Shared Blender helpers."""
import bpy, math
import numpy as np

RES = (576, 1024)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 16
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 3
    sc.cycles.diffuse_bounces = 1
    sc.cycles.glossy_bounces = 1
    sc.cycles.transmission_bounces = 2
    sc.cycles.transparent_max_bounces = 4
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    return sc


def hexc(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(srgb_to_lin(v) for v in c) + (a,)


def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mat_basic(name, color, rough=0.8, metal=0.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = color if len(color) == 4 else hexc(color)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = hexc(emit)
        p.inputs["Emission Strength"].default_value = emit_strength
    return m


def world(top="#5d8fc9", bottom="#e8d9c4", strength=1.0, sun_dir=None, span=0.2):
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = hexc(bottom)
    ramp.color_ramp.elements[1].position = span
    ramp.color_ramp.elements[1].color = hexc(top)
    nt.links.new(ramp.outputs[0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs[0], out.inputs[0])
    return w


def sun(rot=(math.radians(50), 0, math.radians(140)), strength=4.0, color="#fff1dc", angle=2.0):
    d = bpy.data.lights.new("Sun", "SUN")
    d.energy = strength
    d.color = hexc(color)[:3]
    d.angle = math.radians(angle)
    o = bpy.data.objects.new("Sun", d)
    o.rotation_euler = rot
    bpy.context.scene.collection.objects.link(o)
    return o


def camera(lens=24, clip=(0.1, 20000)):
    c = bpy.data.cameras.new("Cam")
    c.lens = lens
    c.sensor_fit = "VERTICAL"
    c.clip_start, c.clip_end = clip
    o = bpy.data.objects.new("Cam", c)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.scene.camera = o
    return o


def look_at(cam_obj, loc, target, roll=0.0):
    from mathutils import Vector
    cam_obj.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    cam_obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam_obj.rotation_euler.rotate_axis("Z", roll)


def grid_mesh(name, X, Y, Z, flat=True, face_mask=None):
    """Build a quad grid mesh from 2D arrays (ny, nx). face_mask: (ny-1, nx-1) bool keeps quads."""
    ny, nx = X.shape
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1).astype(np.float32)
    idx = np.arange(ny * nx).reshape(ny, nx)
    a = idx[:-1, :-1].ravel(); b = idx[:-1, 1:].ravel(); c = idx[1:, 1:].ravel(); d = idx[1:, :-1].ravel()
    quads = np.stack([a, b, c, d], 1)
    if face_mask is not None:
        quads = quads[face_mask.ravel()]
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(quads.size)
    me.loops.foreach_set("vertex_index", quads.ravel().astype(np.int32))
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", (np.arange(len(quads)) * 4).astype(np.int32))
    me.update(calc_edges=True)
    me.validate()
    if not flat:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def set_z(ob, Z):
    me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    co[:, 2] = Z.ravel()
    me.vertices.foreach_set("co", co.ravel())
    me.update()


def set_colors(ob, name, cols):
    me = ob.data
    if name not in me.color_attributes:
        me.color_attributes.new(name, "FLOAT_COLOR", "POINT")
    a = me.color_attributes[name]
    rgba = np.ones((len(me.vertices), 4), np.float32)
    rgba[:, :cols.shape[-1]] = cols.reshape(-1, cols.shape[-1])
    a.data.foreach_set("color", rgba.ravel())
    me.update()


def attr_material(name, attr, rough=0.85, fog=None, spec=0.3, alpha_attr=False, bump=None):
    """Material reading a color attribute; optional aerial-perspective fog (color, start, end in BU)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = attr
    col = at.outputs["Color"]
    if fog:
        cd = nt.nodes.new("ShaderNodeCameraData")
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.name = "FogRange"
        mr.inputs["From Min"].default_value = fog[1]; mr.inputs["From Max"].default_value = fog[2]
        mr.inputs["To Max"].default_value = fog[3] if len(fog) > 3 else 0.75
        nt.links.new(cd.outputs["View Distance"], mr.inputs["Value"])
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        nt.links.new(mr.outputs["Result"], mix.inputs["Factor"])
        nt.links.new(col, mix.inputs["A"])
        mix.inputs["B"].default_value = hexc(fog[0])
        col = mix.outputs["Result"]
        # haze also glows slightly so distant land doesn't go dark in shadow
        em = nt.nodes.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 0.25
        nt.links.new(mr.outputs["Result"], em.inputs[0])
        p.inputs["Emission Color"].default_value = hexc(fog[0])
        nt.links.new(em.outputs[0], p.inputs["Emission Strength"])
    nt.links.new(col, p.inputs["Base Color"])
    if bump:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = bump[0]
        n1.inputs["Detail"].default_value = 6.0
        nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
        bn = nt.nodes.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = bump[1]
        bn.inputs["Distance"].default_value = bump[2] if len(bump) > 2 else 1.0
        nt.links.new(n1.outputs["Fac"], bn.inputs["Height"])
        nt.links.new(bn.outputs["Normal"], p.inputs["Normal"])
    p.inputs["Roughness"].default_value = rough
    p.inputs["Specular IOR Level"].default_value = spec
    return m
