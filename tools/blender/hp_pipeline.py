#!/usr/bin/env python3
"""
SUBSISTENCE — hp_pipeline.py · хай-поли пасс одной модели (AAA-пайплайн, ANSWERS_V3 8а).

Вход:  игровой FBX   Assets/Subsistence/Models/<cat>/<model>.fbx
Выход: Assets/Subsistence/ModelsHP/<model>/<model>_hp.fbx      игровая сетка (LP)
       Assets/Subsistence/ModelsHP/<model>/<model>_lod1.fbx    LOD 55% (12а)
       Assets/Subsistence/ModelsHP/<model>/<model>_lod2.fbx    LOD 25% (12а)
       Assets/Subsistence/ModelsHP/<model>/<model>_normal.png  запечённые нормали (Tangent, 2K/1K — 11а)
       Assets/Subsistence/ModelsHP/<model>/<model>_ao.png      запечённый Ambient Occlusion
       docs/previews/_hp_<model>.png                           лист сравнения HP ↔ LP+baked

Использование (окружение должно быть поднято: bash tools/setup_blender.sh):
    python3 tools/bpy_run.py tools/blender/hp_pipeline.py -- --model MN_smiler --size 2048 --subdiv 3
"""
import bpy, os, sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(name, default):
    return argv[argv.index(name) + 1] if name in argv else default

MODEL    = opt("--model", "MN_smiler")
SIZE     = int(opt("--size", 2048))          # 11а: 2K крупные, 1K мелочь
SUBDIV   = int(opt("--subdiv", 3))           # глубина субдивизии HP
STRENGTH = float(opt("--strength", 0.022))   # сила органической детализации (метры)

ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTDIR = os.path.join(ROOT, "Assets", "Subsistence", "ModelsHP", MODEL)
os.makedirs(OUTDIR, exist_ok=True)

# ---------- 1. найти исходный FBX ----------
src = None
for cat in ("Characters", "Weapons", "Props", "Items"):
    p = os.path.join(ROOT, "Assets", "Subsistence", "Models", cat, MODEL + ".fbx")
    if os.path.exists(p):
        src = p
        break
assert src, "[hp] FBX не найден: " + MODEL
print(f"[hp] исходник: {src}")

# ---------- 2. чистая сцена, импорт LP ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert meshes, "[hp] в FBX нет мешей"
for o in meshes:                      # отвязать от пустышек-родителей FBX
    if o.parent:
        mwl = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mwl
lp = max(meshes, key=lambda o: len(o.data.vertices))
lp_tris = sum(len(p.vertices) - 2 for p in lp.data.polygons)
print(f"[hp] LP: {lp.name} · {len(lp.data.vertices)} вершин · {lp_tris} трис")

# ---------- 3. UV ----------
if not lp.data.uv_layers:
    bpy.context.view_layer.objects.active = lp
    lp.select_set(True)
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    print("[hp] UV не было — smart_project готов")

# ---------- 4. HP-копия: субдивизия + органический дисплейс ----------
hp = lp.copy()
hp.data = lp.data.copy()
hp.name = MODEL + "_HP"
bpy.context.collection.objects.link(hp)

sub = hp.modifiers.new("hp_sub", "SUBSURF")
sub.levels = SUBDIV
sub.subdivision_type = "SIMPLE"

def displace(name, tex_name, kind, scale, strength, **kw):
    t = bpy.data.textures.new(tex_name, kind)
    t.noise_scale = scale
    for k, v in kw.items():
        setattr(t, k, v)
    d = hp.modifiers.new(name, "DISPLACE")
    d.texture = t
    d.texture_coords = "LOCAL"
    d.strength = strength
    d.mid_level = 0.5
    return d

displace("hp_skin",  "hp_skin_tex",  "CLOUDS", 0.32, STRENGTH)                      # крупные неровности плоти
displace("hp_micro", "hp_micro_tex", "STUCCI", 1.7, STRENGTH * 0.45, stucci_type="PLASTIC")  # микрорельеф
displace("hp_pores", "hp_pores_tex", "VORONOI", 6.5, -STRENGTH * 0.30)              # поры-вмятины

dg = bpy.context.evaluated_depsgraph_get()
hp_eval = hp.evaluated_get(dg)
hp_tris = 0
for me_chunk in (hp_eval.to_mesh(),):
    hp_tris = sum(len(p.vertices) - 2 for p in me_chunk.polygons)
    hp_eval.to_mesh_clear()
print(f"[hp] HP: ~{hp_tris} трис (субдивизия ×{SUBDIV} + дисплейс)")

# ---------- 5. материал LP под запекание ----------
mat = bpy.data.materials.new(MODEL + "_HP_baked")
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Roughness"].default_value = 0.85

img_n = bpy.data.images.new(MODEL + "_normal", SIZE, SIZE, float_buffer=True)
img_a = bpy.data.images.new(MODEL + "_ao", SIZE, SIZE, float_buffer=True)
node_n = nt.nodes.new("ShaderNodeTexImage"); node_n.image = img_n; node_n.location = (-500, 260)
node_n.image.colorspace_settings.name = "Non-Color"
node_a = nt.nodes.new("ShaderNodeTexImage"); node_a.image = img_a; node_a.location = (-500, 20)
node_a.image.colorspace_settings.name = "Non-Color"
nmap = nt.nodes.new("ShaderNodeNormalMap"); nmap.location = (-220, 140)
nt.links.new(node_n.outputs[0], nmap.inputs[1])
nt.links.new(nmap.outputs[0], bsdf.inputs["Normal"])
nt.links.new(node_a.outputs[0], bsdf.inputs["Base Color"])

lp.data.materials.clear()
lp.data.materials.append(mat)

# ---------- 6. запекание ----------
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 96

def select_for_bake(active, selected):
    bpy.ops.object.select_all(action="DESELECT")
    for o in selected:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active

CAGE = max(STRENGTH * 4.0, 0.05)

nt.nodes.active = node_n
select_for_bake(lp, [hp])
bpy.ops.object.bake(type="NORMAL", use_selected_to_active=True, use_clear=True,
                    margin=16, normal_space="TANGENT", cage_extrusion=CAGE)
print("[hp] нормали запечены")

nt.nodes.active = node_a
select_for_bake(lp, [hp])
bpy.ops.object.bake(type="AO", use_selected_to_active=True, use_clear=True,
                    margin=16, cage_extrusion=CAGE)
print("[hp] AO запечён")

for img, fname in ((img_n, f"{MODEL}_normal.png"), (img_a, f"{MODEL}_ao.png")):
    img.filepath_raw = os.path.join(OUTDIR, fname)
    img.file_format = "PNG"
    img.save()
print(f"[hp] карты сохранены: {OUTDIR}/{MODEL}_normal.png, _ao.png")

# ---------- 7. LOD-ы (12а) ----------
def make_lod(src_obj, name, ratio):
    o = src_obj.copy()
    o.data = src_obj.data.copy()
    o.name = name
    bpy.context.collection.objects.link(o)
    d = o.modifiers.new("lod", "DECIMATE")
    d.ratio = ratio
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.object.modifier_apply(modifier="lod")
    t = sum(len(p.vertices) - 2 for p in o.data.polygons)
    print(f"[hp] {name}: {t} трис")
    return o

lod1 = make_lod(lp, MODEL + "_LOD1", 0.55)
lod2 = make_lod(lp, MODEL + "_LOD2", 0.25)

# ---------- 8. экспорт FBX ----------
def export(obj, fname):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUTDIR, fname), use_selection=True,
                             axis_forward="-Z", axis_up="Y", path_mode="COPY",
                             embed_textures=False, add_leaf_bones=False)

export(lp, f"{MODEL}_hp.fbx")
export(lod1, f"{MODEL}_lod1.fbx")
export(lod2, f"{MODEL}_lod2.fbx")
print("[hp] FBX экспортированы: _hp, _lod1, _lod2")

# ---------- 9. лист сравнения HP ↔ LP+baked ----------
for o in (lp, lod1, lod2, hp):
    o.hide_render = o.hide_viewport = False
lp.location.x -= 1.1
hp.location.x += 1.1

grey = bpy.data.materials.new(MODEL + "_grey")
grey.use_nodes = True
gb = next(n for n in grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
gb.inputs["Roughness"].default_value = 0.85
hp.data.materials.clear()
hp.data.materials.append(grey)

cam_data = bpy.data.cameras.new("Cam"); cam_data.lens = 50
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
import mathutils
cam.location = (0, -5.4, 1.15)
target = mathutils.Vector((0, 0, 0.95))
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()

sun_data = bpy.data.lights.new("Sun", "SUN"); sun_data.energy = 3.2
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (0.85, 0.15, 0.55)

world = bpy.data.worlds.new("HpWorld")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
sc.world = world
sc.camera = cam
sc.cycles.samples = 48
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
sc.render.filepath = os.path.join(ROOT, "docs", "previews", f"_hp_{MODEL}.png")
bpy.ops.render.render(write_still=True)
print(f"[hp] лист сравнения: {sc.render.filepath}")

print(f"[hp] ГОТОВО · {MODEL}: LP {lp_tris} трис + HP {hp_tris} трис + нормаль/AO {SIZE}px + 2 LOD")
