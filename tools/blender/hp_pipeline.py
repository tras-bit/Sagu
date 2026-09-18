#!/usr/bin/env python3
"""
SUBSISTENCE — hp_pipeline.py · хай-поли пасс одной модели (AAA-пайплайн, ANSWERS_V3 8а).

Профили (авто по префиксу, перекрывается --kind):
  · organic (MN_*, CH_*) — субдивизия + органический дисплейс (плоть, поры)
  · hard    (W_*, EX_*, остальное) — фаски на кромках (bevel) + микроцарапины + вмятины

Вход:  игровой FBX   Assets/Subsistence/Models/<cat>/<model>.fbx
Выход: Assets/Subsistence/ModelsHP/<model>/<model>_hp.fbx      игровая сетка (LP)
       Assets/Subsistence/ModelsHP/<model>/<model>_lod1.fbx    LOD 55% (12а)
       Assets/Subsistence/ModelsHP/<model>/<model>_lod2.fbx    LOD 25% (12а)
       Assets/Subsistence/ModelsHP/<model>/<model>_color.png   albedo 2K/1K (запечённый цвет)
       Assets/Subsistence/ModelsHP/<model>/<model>_normal.png  нормали Tangent 2K/1K
       Assets/Subsistence/ModelsHP/<model>/<model>_ao.png      Ambient Occlusion
       docs/previews/_hp_<model>.png                           сравнение: LP+текстуры ↔ HP+текстуры

Использование (окружение: bash tools/setup_blender.sh):
    python3 tools/bpy_run.py tools/blender/hp_pipeline.py -- --model MN_smiler --size 2048 --subdiv 3
"""
import bpy, os, sys
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(name, default):
    """Последнее вхождение побеждает (перекрытие дефолтов батча)."""
    vals = [argv[i + 1] for i, a in enumerate(argv) if a == name and i + 1 < len(argv)]
    return vals[-1] if vals else default

MODEL    = opt("--model", "MN_smiler")
SIZE     = int(opt("--size", 2048))          # 11а: 2K крупные, 1K мелочь
SUBDIV   = int(opt("--subdiv", 3))           # глубина субдивизии HP (органика)
STRENGTH = float(opt("--strength", 0.022))   # сила органической детализации (метры)
SAMPLES  = int(opt("--samples", 32))         # сэмплы финального рендера (сравнение)
KIND     = opt("--kind", "")                 # organic | hard (пусто = авто по префиксу)
LOD2R    = float(opt("--lod2", 0.25))        # коэффициент decimate LOD2 (0.25; трубы жмём сильнее)
DETAIL   = "--detail" in argv                # 20б: доп. слой строчек/швов (STUCCI WALL_IN)
if not KIND:
    KIND = "organic" if MODEL.startswith(("MN_", "CH_")) else "hard"

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
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
lp = max(meshes, key=lambda o: len(o.data.vertices))
if len(meshes) > 1:                   # несколько мешей → объединить в один
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = lp
    bpy.ops.object.join()
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    lp = meshes[0]
    print(f"[hp] мешей было несколько — объединены в {lp.name}")
lp_tris = sum(len(p.vertices) - 2 for p in lp.data.polygons)
print(f"[hp] LP: {lp.name} · {len(lp.data.vertices)} вершин · {lp_tris} трис")

# ---------- 3. UV ----------
if not lp.data.uv_layers:
    bpy.context.view_layer.objects.active = lp
    lp.select_set(True)
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    print("[hp] UV не было — smart_project готов")

# ---------- 4. HP-копия (профиль organic / hard) ----------
hp = lp.copy()
hp.data = lp.data.copy()
hp.name = MODEL + "_HP"
bpy.context.collection.objects.link(hp)

REF = max(lp.dimensions) if max(lp.dimensions) > 0.01 else 1.0   # габарит модели, м

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

if KIND == "organic":
    # плоть: субдивизия + неровности + микрорельеф + поры
    sub = hp.modifiers.new("hp_sub", "SUBSURF")
    sub.levels = SUBDIV
    sub.subdivision_type = "SIMPLE"
    displace("hp_skin",  "hp_skin_tex",  "CLOUDS", 0.32, STRENGTH)                       # крупные неровности плоти
    displace("hp_micro", "hp_micro_tex", "STUCCI", 1.7, STRENGTH * 0.45, stucci_type="PLASTIC")  # микрорельеф
    displace("hp_pores", "hp_pores_tex", "VORONOI", 6.5, -STRENGTH * 0.30)              # поры-вмятины
    if DETAIL:                                                                          # 20б: строчки/швы (лёгкий апгрейд деталей)
        displace("hp_stitch", "hp_stitch_tex", "STUCCI", 12.0, STRENGTH * 0.12, stucci_type="WALL_IN")
        hp_note = f"субдивизия ×{SUBDIV} + органика + строчки"
    else:
        hp_note = f"субдивизия ×{SUBDIV} + органика"
else:
    # хард-сёрфейс: фаски на кромках (bevel) + микроцарапины + мелкие вмятины
    bv = hp.modifiers.new("hp_bevel", "BEVEL")
    bv.limit_method = "ANGLE"
    bv.angle_limit = 0.70            # ~40°
    bv.segments = 3
    bv.width = max(REF * 0.0022, 0.0003)
    displace("hp_scratch", "hp_scratch_tex", "STUCCI", 4.5, 0.0012, stucci_type="PLASTIC")  # микроцарапины
    displace("hp_dents",  "hp_dents_tex",  "VORONOI", 12.0, -0.0005)                        # мелкие вмятины
    hp_note = f"фаски {bv.width*1000:.2f} мм + царапины"
print(f"[hp] профиль: {KIND} ({hp_note})")

dg = bpy.context.evaluated_depsgraph_get()
hp_eval = hp.evaluated_get(dg)
me_tmp = hp_eval.to_mesh()
hp_tris = sum(len(p.vertices) - 2 for p in me_tmp.polygons)
hp_eval.to_mesh_clear()
print(f"[hp] HP: ~{hp_tris} трис ({hp_note})")

# ---------- 5. материал LP с картами под запекание ----------
mat = bpy.data.materials.new(MODEL + "_HP_baked")
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Roughness"].default_value = 0.85

img_c = bpy.data.images.new(MODEL + "_color", SIZE, SIZE)            # albedo, sRGB
img_n = bpy.data.images.new(MODEL + "_normal", SIZE, SIZE)           # tangent, Non-Color
img_a = bpy.data.images.new(MODEL + "_ao", max(SIZE // 2, 512)) if False else bpy.data.images.new(MODEL + "_ao", max(SIZE // 2, 512), max(SIZE // 2, 512))  # AO — половинное разрешение (низкочастотная карта)

node_c = nt.nodes.new("ShaderNodeTexImage"); node_c.image = img_c; node_c.location = (-700, 420)
node_n = nt.nodes.new("ShaderNodeTexImage"); node_n.image = img_n; node_n.location = (-700, 160)
node_n.image.colorspace_settings.name = "Non-Color"
node_a = nt.nodes.new("ShaderNodeTexImage"); node_a.image = img_a; node_a.location = (-700, -80)
node_a.image.colorspace_settings.name = "Non-Color"
nmap = nt.nodes.new("ShaderNodeNormalMap"); nmap.location = (-300, 60)
mult = nt.nodes.new("ShaderNodeMixRGB"); mult.location = (-300, 300)
mult.blend_type = "MULTIPLY"; mult.inputs[0].default_value = 1.0

nt.links.new(node_c.outputs[0], mult.inputs[1])
nt.links.new(node_a.outputs[0], mult.inputs[2])
nt.links.new(mult.outputs[0], bsdf.inputs["Base Color"])
nt.links.new(node_n.outputs[0], nmap.inputs[1])
nt.links.new(nmap.outputs[0], bsdf.inputs["Normal"])

lp.data.materials.clear()
lp.data.materials.append(mat)

# ---------- 6. запекание: нормали → AO → цвет ----------
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

nt.nodes.active = node_c
select_for_bake(lp, [hp])
sc.render.bake.use_pass_direct = False
sc.render.bake.use_pass_indirect = False
sc.render.bake.use_pass_color = True
bpy.ops.object.bake(type="DIFFUSE", use_selected_to_active=True, use_clear=True,
                    margin=16, cage_extrusion=CAGE)
sc.render.bake.use_pass_direct = True
sc.render.bake.use_pass_indirect = True
print("[hp] albedo (цвет) запечён")

for img, fname in ((img_c, f"{MODEL}_color.png"), (img_n, f"{MODEL}_normal.png"), (img_a, f"{MODEL}_ao.png")):
    img.filepath_raw = os.path.join(OUTDIR, fname)
    img.file_format = "PNG"
    img.save()
print(f"[hp] карты: {MODEL}_color/_normal/_ao.png ({SIZE}px) → {OUTDIR}")

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
    src_t = sum(len(p.vertices) - 2 for p in src_obj.data.polygons)
    if t > src_t * 0.75:   # не ужался → разорванные оболочки (труба РПГ): сварить и повторить
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=1e-5)
        bpy.ops.object.mode_set(mode="OBJECT")
        d = o.modifiers.new("lod2", "DECIMATE")
        d.ratio = ratio
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
            bpy.ops.object.modifier_apply(modifier="lod2")
        t2 = sum(len(p.vertices) - 2 for p in o.data.polygons)
        print(f"[hp] {name}: decimate упёрся ({t} трис) — сварил оболочки → {t2} трис")
        t = t2
    print(f"[hp] {name}: {t} трис")
    return o

lod1 = make_lod(lp, MODEL + "_LOD1", 0.55)
lod2 = make_lod(lp, MODEL + "_LOD2", LOD2R)

# ---------- 8. экспорт FBX (LP + LOD) ----------
def export(obj, fname):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUTDIR, fname), use_selection=True,
                             axis_forward="-Z", axis_up="Y", path_mode="COPY",
                             embed_textures=False, add_leaf_bones=False)

export(lp, f"{MODEL}_hp.fbx")
export(lod1, f"{MODEL}_lod1.fbx")
export(lod2, f"{MODEL}_lod2.fbx")
print("[hp] FBX: _hp, _lod1, _lod2")

# ---------- 9. лист сравнения: обе версии С ТЕКСТУРАМИ ----------
for o in (lp, lod1, lod2, hp):
    o.hide_render = o.hide_viewport = False
# HP оставляем с оригинальными материалами (цвета из исходного FBX)
# LP уже с albedo×AO + нормалями

# расставить по размеру модели
bb = lp.matrix_world @ mathutils.Vector(lp.data.vertices[0].co)  # init
world_coords = [lp.matrix_world @ mathutils.Vector(v.co) for v in lp.data.vertices[:400]]
xs = [v.x for v in world_coords]; zs = [v.z for v in world_coords]
size = max(max(xs) - min(xs), max(zs) - min(zs), 0.5)
cy = (max(zs) + min(zs)) / 2
off = size * 0.62
lp.location.x -= off
hp.location.x += off
cam_dist = size * 2.6

cam_data = bpy.data.cameras.new("Cam"); cam_data.lens = 50
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (0, -cam_dist, cy + size * 0.12)
target = mathutils.Vector((0, 0, cy))
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
sc.cycles.samples = SAMPLES
sc.render.resolution_x = 960
sc.render.resolution_y = 540
sc.render.filepath = os.path.join(ROOT, "docs", "previews", f"_hp_{MODEL}.png")
bpy.ops.render.render(write_still=True)
print(f"[hp] лист сравнения (с текстурами): {sc.render.filepath}")

print(f"[hp] ГОТОВО · {MODEL}: LP {lp_tris} трис + HP {hp_tris} трис + color/normal/AO {SIZE}px + 2 LOD")
