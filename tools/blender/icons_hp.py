#!/usr/bin/env python3
"""
SUBSISTENCE — icons_hp.py · иконки 256px из хай-поли комплектов (ANSWERS_V3 24а).

Что делает: грузит игровую сетку <model>_hp.fbx (та же, что в Unity, с UV),
наводит материал с запечёнными картами (albedo×AO + нормали — как превью),
ставит ортографическую камеру в 3/4 и рендерит прозрачный PNG 1024×1024.
Финальную доводку (256, рамка редкости) делает tools/make_icons_256.py.

Вход:  Assets/Subsistence/ModelsHP/<model>/{<model>_hp.fbx, _color.png, _normal.png, _ao.png}
Выход: docs/icons256_raw/<icon_id>.png  (1024 RGBA, объект вписан в кадр)

Использование (окружение: source ~/.cache/blender_env.sh):
    python3 tools/bpy_run.py tools/blender/icons_hp.py -- --model IT_can_beans --icon can_beans
    (опции: --azim 32 --elev 18 --samples 64)
"""
import bpy, os, sys, math
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(name, default):
    vals = [argv[i + 1] for i, a in enumerate(argv) if a == name and i + 1 < len(argv)]
    return vals[-1] if vals else default

MODEL   = opt("--model", "IT_can_beans")
ICON    = opt("--icon", MODEL.split("_", 1)[1])
SAMPLES = int(opt("--samples", 64))
# ракурс по типу: оружие — почти сбоку (ствол по диагонали), органика — фронтально-сверху
if "--azim" in argv:
    AZIM = float(opt("--azim", 32))
elif MODEL.startswith(("W_", "EX_")):
    AZIM = 62.0
elif MODEL.startswith(("MN_", "CH_")):
    AZIM = 25.0
else:
    AZIM = 32.0
if "--elev" in argv:
    ELEV = float(opt("--elev", 18))
elif MODEL.startswith(("W_", "EX_")):
    ELEV = 12.0
elif MODEL.startswith(("MN_", "CH_")):
    ELEV = 10.0
else:
    ELEV = 18.0

ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HPDIR = os.path.join(ROOT, "Assets", "Subsistence", "ModelsHP", MODEL)
OUT   = os.path.join(ROOT, "docs", "icons256_raw")
os.makedirs(OUT, exist_ok=True)

# ---------- 1. чистая сцена, импорт игровой сетки ----------
mesh_fbx = os.path.join(HPDIR, MODEL + "_hp.fbx")
assert os.path.exists(mesh_fbx), "[icons] нет FBX: " + mesh_fbx
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=mesh_fbx)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert meshes, "[icons] в FBX нет мешей"
for o in meshes:                      # отвязать от пустышек-родителей FBX
    if o.parent:
        mwl = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mwl
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
lp = max(meshes, key=lambda o: len(o.data.vertices))
if len(meshes) > 1:                   # несколько мешей → объединить в один
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = lp
    bpy.ops.object.join()
    lp = bpy.context.view_layer.objects.active

# ---------- 2. материал: albedo×AO + нормали (рецепт превью) ----------
f_c = os.path.join(HPDIR, MODEL + "_color.png")
f_n = os.path.join(HPDIR, MODEL + "_normal.png")
f_a = os.path.join(HPDIR, MODEL + "_ao.png")
for f in (f_c, f_n, f_a):
    assert os.path.exists(f), "[icons] нет карты: " + f

mat = bpy.data.materials.new(MODEL + "_icon")
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Roughness"].default_value = 0.85

img_c = bpy.data.images.load(f_c)
img_n = bpy.data.images.load(f_n)
img_a = bpy.data.images.load(f_a)

node_c = nt.nodes.new("ShaderNodeTexImage"); node_c.image = img_c; node_c.location = (-700, 420)
node_n = nt.nodes.new("ShaderNodeTexImage"); node_n.image = img_n; node_n.location = (-700, 160)
node_n.image.colorspace_settings.name = "Non-Color"
node_a = nt.nodes.new("ShaderNodeTexImage"); node_a.image = img_a; node_a.location = (-700, -80)
node_a.image.colorspace_settings.name = "Non-Color"
# AO с полом 0.55 (как в Unity-материале ModelPrefabBuilder): ao' = 0.55 + 0.45·ao
aofloor = nt.nodes.new("ShaderNodeMixRGB"); aofloor.location = (-500, -80)
aofloor.blend_type = "MIX"; aofloor.inputs[0].default_value = 0.45
aofloor.inputs["Color2"].default_value = (1.0, 1.0, 1.0, 1.0)
nmap = nt.nodes.new("ShaderNodeNormalMap"); nmap.location = (-300, 60)
mult = nt.nodes.new("ShaderNodeMixRGB"); mult.location = (-300, 300)
mult.blend_type = "MULTIPLY"; mult.inputs[0].default_value = 1.0

nt.links.new(node_c.outputs[0], mult.inputs[1])
nt.links.new(node_a.outputs[0], aofloor.inputs["Color1"])
nt.links.new(aofloor.outputs[0], mult.inputs[2])
nt.links.new(mult.outputs[0], bsdf.inputs["Base Color"])
nt.links.new(node_n.outputs[0], nmap.inputs[1])
nt.links.new(nmap.outputs[0], bsdf.inputs["Normal"])

lp.data.materials.clear()
lp.data.materials.append(mat)

# ---------- 3. ортокамера: авто-вписать объект в квадрат ----------
bpy.context.view_layer.update()
bb_max = mathutils.Vector((-1e9, -1e9, -1e9))
bb_min = mathutils.Vector((1e9, 1e9, 1e9))
for v in lp.data.vertices:
    w = lp.matrix_world @ mathutils.Vector(v.co)
    bb_max.x = max(bb_max.x, w.x); bb_min.x = min(bb_min.x, w.x)
    bb_max.y = max(bb_max.y, w.y); bb_min.y = min(bb_min.y, w.y)
    bb_max.z = max(bb_max.z, w.z); bb_min.z = min(bb_min.z, w.z)
center = (bb_max + bb_min) / 2
dims = bb_max - bb_min
md = max(dims.x, dims.y, dims.z)

cam_data = bpy.data.cameras.new("IconCam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = md * 1.16          # объект ~86% кадра
cam = bpy.data.objects.new("IconCam", cam_data)
bpy.context.collection.objects.link(cam)

az = math.radians(AZIM); el = math.radians(ELEV)
r = md * 3.0 + 1.0
cam.location = center + mathutils.Vector((math.sin(az) * math.cos(el) * r,
                                          -math.cos(az) * math.cos(el) * r,
                                          math.sin(el) * r))
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()

# ---------- 4. свет: ключ + заполняющий (фон прозрачный) ----------
key_data = bpy.data.lights.new("Key", "SUN"); key_data.energy = 4.6
key = bpy.data.objects.new("Key", key_data)
bpy.context.collection.objects.link(key)
key.rotation_euler = (0.85, 0.15, 0.55)

fill_data = bpy.data.lights.new("Fill", "SUN"); fill_data.energy = 1.7
fill = bpy.data.objects.new("Fill", fill_data)
bpy.context.collection.objects.link(fill)
fill.rotation_euler = (0.7, -0.3, math.pi - 0.55)

world = bpy.data.worlds.new("IconWorld")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.10, 0.10, 0.11, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.9

# ---------- 5. рендер 1024 RGBA ----------
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.world = world
sc.camera = cam
sc.cycles.samples = SAMPLES
sc.render.film_transparent = True
sc.render.resolution_x = 1024
sc.render.resolution_y = 1024
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
sc.render.filepath = os.path.join(OUT, ICON + ".png")
bpy.ops.render.render(write_still=True)
print(f"[icons] {MODEL} → {ICON}.png  (azim {AZIM:.0f}°, elev {ELEV:.0f}°, {md:.2f} м)")
