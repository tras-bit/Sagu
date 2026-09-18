#!/usr/bin/env python3
"""
SUBSISTENCE — skin_render.py · рендеры скинов 2K (ANSWERS_V3 25а).

Каждый скин из Progression/Skins.cs — это HP-модель, умноженная на цвет скина
(в игре это делает ModelLibrary.Tint через _BaseColor). Здесь то же самое
рендерится в PNG: albedo × AO(floor 0.55) × цветСкина + нормали, ортокамера 3/4.

Выход: docs/previews/skins/<skin_id>_2048.png  (мастер 2K, прозрачный фон)
       Assets/Subsistence/Resources/skins/<skin_id>.png (1024, для магазина)

Использование:
    python3 tools/bpy_run.py tools/blender/skin_render.py -- --model W_rifle_ak --skin ak.asbestos --color 0.78,0.74,0.66
"""
import bpy, os, sys, math
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(name, default):
    vals = [argv[i + 1] for i, a in enumerate(argv) if a == name and i + 1 < len(argv)]
    return vals[-1] if vals else default

MODEL  = opt("--model", "W_rifle_ak")
SKIN   = opt("--skin", "test")
COLOR  = tuple(float(x) for x in opt("--color", "1,1,1").split(","))
SAMPLES = int(opt("--samples", 48))

if MODEL.startswith(("W_", "EX_")):   AZIM, ELEV = 62.0, 12.0
elif MODEL.startswith(("MN_", "CH_")): AZIM, ELEV = 25.0, 10.0
else:                                  AZIM, ELEV = 30.0, 22.0

ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HPDIR = os.path.join(ROOT, "Assets", "Subsistence", "ModelsHP", MODEL)
OUTD  = os.path.join(ROOT, "docs", "previews", "skins")
OUTG  = os.path.join(ROOT, "Assets", "Subsistence", "Resources", "skins")
os.makedirs(OUTD, exist_ok=True)
os.makedirs(OUTG, exist_ok=True)

# ---------- 1. сцена ----------
mesh_fbx = os.path.join(HPDIR, MODEL + "_hp.fbx")
assert os.path.exists(mesh_fbx), "[skin] нет FBX: " + mesh_fbx
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=mesh_fbx)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert meshes, "[skin] в FBX нет мешей"
for o in meshes:
    if o.parent:
        mwl = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mwl
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
lp = max(meshes, key=lambda o: len(o.data.vertices))
if len(meshes) > 1:
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = lp
    bpy.ops.object.join()
    lp = bpy.context.view_layer.objects.active

# ---------- 2. материал: albedo × AO(пол 0.55) × цветСкина + нормали ----------
f_c = os.path.join(HPDIR, MODEL + "_color.png")
f_n = os.path.join(HPDIR, MODEL + "_normal.png")
f_a = os.path.join(HPDIR, MODEL + "_ao.png")

mat = bpy.data.materials.new(MODEL + "_skin")
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Roughness"].default_value = 0.85

node_c = nt.nodes.new("ShaderNodeTexImage"); node_c.image = bpy.data.images.load(f_c); node_c.location = (-900, 420)
node_n = nt.nodes.new("ShaderNodeTexImage"); node_n.image = bpy.data.images.load(f_n); node_n.location = (-900, 160)
node_n.image.colorspace_settings.name = "Non-Color"
node_a = nt.nodes.new("ShaderNodeTexImage"); node_a.image = bpy.data.images.load(f_a); node_a.location = (-900, -80)
node_a.image.colorspace_settings.name = "Non-Color"

aofloor = nt.nodes.new("ShaderNodeMixRGB"); aofloor.location = (-700, -80)
aofloor.blend_type = "MIX"; aofloor.inputs[0].default_value = 0.45
aofloor.inputs["Color2"].default_value = (1.0, 1.0, 1.0, 1.0)

mult = nt.nodes.new("ShaderNodeMixRGB"); mult.location = (-500, 300)
mult.blend_type = "MULTIPLY"; mult.inputs[0].default_value = 1.0

tint = nt.nodes.new("ShaderNodeMixRGB"); tint.location = (-300, 300)   # цвет скина, как ModelLibrary.Tint
tint.blend_type = "MULTIPLY"; tint.inputs[0].default_value = 1.0
tint.inputs["Color2"].default_value = (COLOR[0], COLOR[1], COLOR[2], 1.0)

nmap = nt.nodes.new("ShaderNodeNormalMap"); nmap.location = (-300, 60)

nt.links.new(node_a.outputs[0], aofloor.inputs["Color1"])
nt.links.new(node_c.outputs[0], mult.inputs[1])
nt.links.new(aofloor.outputs[0], mult.inputs[2])
nt.links.new(mult.outputs[0], tint.inputs["Color1"])
nt.links.new(tint.outputs[0], bsdf.inputs["Base Color"])
nt.links.new(node_n.outputs[0], nmap.inputs[1])
nt.links.new(nmap.outputs[0], bsdf.inputs["Normal"])

lp.data.materials.clear()
lp.data.materials.append(mat)

# ---------- 3. ортокамера ----------
bpy.context.view_layer.update()
bb_max = mathutils.Vector((-1e9, -1e9, -1e9)); bb_min = mathutils.Vector((1e9, 1e9, 1e9))
for v in lp.data.vertices:
    w = lp.matrix_world @ mathutils.Vector(v.co)
    bb_max.x = max(bb_max.x, w.x); bb_min.x = min(bb_min.x, w.x)
    bb_max.y = max(bb_max.y, w.y); bb_min.y = min(bb_min.y, w.y)
    bb_max.z = max(bb_max.z, w.z); bb_min.z = min(bb_min.z, w.z)
center = (bb_max + bb_min) / 2
dims = bb_max - bb_min
md = max(dims.x, dims.y, dims.z)

cam_data = bpy.data.cameras.new("SkinCam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = md * 1.16
cam = bpy.data.objects.new("SkinCam", cam_data)
bpy.context.collection.objects.link(cam)
az = math.radians(AZIM); el = math.radians(ELEV)
r = md * 3.0 + 1.0
cam.location = center + mathutils.Vector((math.sin(az) * math.cos(el) * r,
                                          -math.cos(az) * math.cos(el) * r,
                                          math.sin(el) * r))
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()

key_data = bpy.data.lights.new("Key", "SUN"); key_data.energy = 4.6
key = bpy.data.objects.new("Key", key_data)
bpy.context.collection.objects.link(key)
key.rotation_euler = (0.85, 0.15, 0.55)
fill_data = bpy.data.lights.new("Fill", "SUN"); fill_data.energy = 1.7
fill = bpy.data.objects.new("Fill", fill_data)
bpy.context.collection.objects.link(fill)
fill.rotation_euler = (0.7, -0.3, math.pi - 0.55)

world = bpy.data.worlds.new("SkinWorld")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.10, 0.10, 0.11, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.9

# ---------- 4. рендер 2048 RGBA ----------
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.world = world
sc.camera = cam
sc.cycles.samples = SAMPLES
sc.render.film_transparent = True
sc.render.resolution_x = 2048
sc.render.resolution_y = 2048
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
sc.render.filepath = os.path.join(OUTD, SKIN + "_2048.png")
bpy.ops.render.render(write_still=True)
print(f"[skin] {SKIN}: {MODEL} × цвет {COLOR} → 2048")

# ---------- 5. игровая копия 1024 ----------
from PIL import Image
im = Image.open(sc.render.filepath).convert("RGBA")
im.resize((1024, 1024), Image.LANCZOS).save(os.path.join(OUTG, SKIN + ".png"))
print(f"[skin] {SKIN}: игровая 1024 → Resources/skins/{SKIN}.png")
