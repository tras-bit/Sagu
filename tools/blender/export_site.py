#!/usr/bin/env python3
"""SUBSISTENCE — экспорт сайта-каталога моделей (site/).

Для каждой ModelsHP/<имя>/<имя>_hp.fbx:
  1) альбедо = color × AO × панч (та же формула, что в MakeAlbedoAo в Unity) → JPG 512;
  2) материал Principled с альбедо по UV;
  3) скрин-карточка 360×270 (Cycles) → JPG;
  4) GLB с ВШИТОЙ текстурой → site/models/<имя>.glb (вьюверу больше ничего не нужно).
Категории берутся из Assets/Subsistence/Models/<каталог>/<имя>.fbx.
В конце пишется site/data.js с метаданными (имя, категория, трисы, размер).

Запуск: bash tools/blender_bpy.sh tools/blender/export_site.py [-- имена...]
"""
import bpy, os, sys, json, math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import subs_common as S
from PIL import Image, ImageChops, ImageEnhance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HP = os.path.join(ROOT, "Assets", "Subsistence", "ModelsHP")
MODELS = os.path.join(ROOT, "Assets", "Subsistence", "Models")
SITE = os.path.join(ROOT, "site")
GLB_DIR = os.path.join(SITE, "models")
THUMB_DIR = os.path.join(SITE, "thumbs")
os.makedirs(GLB_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [a for a in sys.argv[1:] if not a.startswith("-")]
only = set(a for a in argv if not a.startswith("--")) or None

# категория по папке исходника
CATS = {}
for d in sorted(os.listdir(MODELS)):
    p = os.path.join(MODELS, d)
    if os.path.isdir(p):
        for f in os.listdir(p):
            if f.endswith(".fbx"):
                CATS[f[:-4]] = d

NAMES = sorted(n for n in os.listdir(HP)
               if os.path.exists(os.path.join(HP, n, n + "_hp.fbx"))
               and (only is None or n in only))


def make_albedo(name, size=512):
    """color × AO (floor 0.55) × панч — как в игре. Возвращает путь к JPG или None."""
    d = os.path.join(HP, name)
    cp, ap = os.path.join(d, name + "_color.png"), os.path.join(d, name + "_ao.png")
    if not os.path.exists(cp):
        return None
    c = Image.open(cp).convert("RGB")
    if os.path.exists(ap):
        a = Image.open(ap).convert("L").resize(c.size, Image.BILINEAR)
        ao = a.point(lambda v: int(max(0, min(255, (0.55 + 0.45 * v / 255.0) * 255))))
        c = ImageChops.multiply(c, Image.merge("RGB", (ao, ao, ao)))
    c = ImageEnhance.Contrast(c).enhance(1.13)
    c = ImageEnhance.Color(c).enhance(1.22)
    if c.width != size:
        c = c.resize((size, size), Image.LANCZOS)
    out = os.path.join(GLB_DIR, name + "_albedo.jpg")
    c.save(out, "JPEG", quality=82)
    return out


def process(name):
    d = os.path.join(HP, name)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(d, name + "_hp.fbx"))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        print(f"[site] {name}: НЕТ МЕШЕЙ, пропуск")
        return None
    for o in meshes:                      # отвязать от пустышек FBX (как hp_pipeline)
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
        lp = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    lp.name = name
    tris = S.tri_count(lp)

    alb = make_albedo(name)
    if alb:
        img = bpy.data.images.load(alb)
        img.name = name + "_albedo"
        mat = bpy.data.materials.new(name + "_M")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is None:
            bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
            mat.node_tree.links.new(bsdf.outputs["BSDF"], mat.node_tree.nodes["Material Output"].inputs["Surface"])
        bsdf.inputs["Roughness"].default_value = 0.85
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.interpolation = "Closest" if tris < 100 else "Smart"
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        lp.data.materials.clear()
        lp.data.materials.append(mat)

    # карточка: PNG (render_preview всегда пишет PNG) → JPG
    png_tmp = os.path.join(THUMB_DIR, name + ".png")
    S.render_fit(png_tmp, [lp], samples=16, res=(360, 270))
    try:
        t = Image.open(png_tmp).convert("RGB")
        t.save(os.path.join(THUMB_DIR, name + ".jpg"), "JPEG", quality=84)
        os.remove(png_tmp)
    except Exception as e:
        print(f"[site] {name}:.thumb {e}")

    glb = os.path.join(GLB_DIR, name + ".glb")
    S.export_glb([lp], glb)
    if alb:
        try: os.remove(alb)               # текстура вшита в GLB — отдельный файл не нужен
        except OSError: pass

    kb = max(1, os.path.getsize(glb) // 1024)
    return {"n": name, "c": CATS.get(name, "Models"), "t": tris, "k": kb}


data = []
for i, name in enumerate(NAMES, 1):
    try:
        rec = process(name)
        if rec:
            data.append(rec)
            print(f"[site] [{i}/{len(NAMES)}] {name}: {rec['t']} трис, {rec['k']} КБ", flush=True)
    except Exception as e:
        print(f"[site] [{i}/{len(NAMES)}] {name}: ОШИБКА {e}", flush=True)

with open(os.path.join(SITE, "data.js"), "w", encoding="utf-8") as f:
    f.write("// сгенерировано tools/blender/export_site.py\nconst MODELS = ")
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print(f"[site] ГОТОВО: {len(data)} моделей → {SITE}")
