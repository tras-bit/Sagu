#!/usr/bin/env python3
"""
SUBSISTENCE — fix_lod_uv.py · починка «перемешанных» текстур на LOD (2026-09-18).

ПРИЧИНА БАГА: hp_pipeline.make_lod жал меш Decimate'ом БЕЗ delimit — при collapse
Blender усредняет UV-острова, и на LOD1/LOD2 запечённые текстуры выглядели как
«перемешанное говно». В игре почти все пропсы видны на LOD1/LOD2 (пороги 60/30/10 %),
поэтому мусор был везде.

ЧТО ДЕЛАЕТ: пересобирает <модель>_lod1.fbx/_lod2.fbx из <модель>_hp.fbx (LP, UV целые,
именно под них пеклись карты) с Decimate delimit={'UV'} — швы UV не схлопываются,
выжившие фейсы держат исходные UV-координаты.

МЕТРИКА: доля UV-координат LOD, совпадающих с исходным набором LP (до 4 знака).
  старый LOD (без delimit) — обычно ~20–60 %; новый — ~85–99 %.

Использование:
    bash tools/blender_bpy.sh tools/blender/fix_lod_uv.py -- --model BD_door_armored
    bash tools/blender_bpy.sh tools/blender/fix_lod_uv.py -- --all
"""
import bpy, os, sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[argv.index("--model") + 1] if "--model" in argv else None
DO_ALL = "--all" in argv
if not ONLY and not DO_ALL:
    print("[fixlod] укажи --model <имя> или --all"); sys.exit(1)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HP = os.path.join(ROOT, "Assets", "Subsistence", "ModelsHP")


def uv_keys(mesh, ndigits=4):
    """Набор квантованных UV-координат (выжившие при UV-delimit фейсы держат точные копии)."""
    uv = mesh.uv_layers.active
    if not uv:
        return set()
    return {(round(d.uv[0], ndigits), round(d.uv[1], ndigits)) for d in uv.data}


def tris(mesh):
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def import_fbx(path):
    before = set(o.name for o in bpy.context.scene.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.context.scene.objects if o.name not in before and o.type == "MESH"]
    assert new, "[fixlod] в FBX нет мешей: " + path
    if len(new) > 1:                       # несколько мешей → берём самый большой (в HP-экспортах один)
        new.sort(key=lambda o: len(o.data.vertices), reverse=True)
    return new[0]


def decimate_uv_safe(obj, name, ratio, src_t):
    """Decimate с delimit={'UV'} (+знакомый фолбэк со сваркой, если не ужался)."""
    o = obj.copy(); o.data = obj.data.copy(); o.name = name
    bpy.context.collection.objects.link(o)
    d = o.modifiers.new("lod", "DECIMATE")
    d.ratio = ratio
    try:
        d.delimit = {"UV"}                 # ГЛАВНОЕ: не рвать швы UV-островов
    except Exception as e:
        print(f"   !! delimit не поддержан ({e}) — жму как есть")
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.object.modifier_apply(modifier="lod")
    t = tris(o.data)
    if t > src_t * 0.75:                   # разорванные оболочки (труба РПГ): сварить и повторить
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=1e-5)
        bpy.ops.object.mode_set(mode="OBJECT")
        d2 = o.modifiers.new("lod2", "DECIMATE")
        d2.ratio = ratio
        try:
            d2.delimit = {"UV"}
        except Exception:
            pass
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
            bpy.ops.object.modifier_apply(modifier="lod2")
        t = tris(o.data)
        print(f"   {name}: decimate упёрся — сварил оболочки → {t} трис")
    return o


def export(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True,
                             axis_forward="-Z", axis_up="Y", path_mode="COPY",
                             embed_textures=False, add_leaf_bones=False)


def process(dirname):
    base = os.path.join(HP, dirname)
    hp_fbx = os.path.join(base, dirname + "_hp.fbx")
    if not os.path.isfile(hp_fbx):
        return None
    bpy.ops.wm.read_factory_settings(use_empty=True)          # чистая сцена на каждую модель
    lp = import_fbx(hp_fbx)
    src_uv = uv_keys(lp.data)
    src_t = tris(lp.data)

    # старые LOD — только ради метрики (потом файлы перезапишем)
    report = {"name": dirname, "lp_tris": src_t, "old": {}, "new": {}}
    for tag in ("lod1", "lod2"):
        old_fbx = os.path.join(base, f"{dirname}_{tag}.fbx")
        if os.path.isfile(old_fbx):
            try:
                old = import_fbx(old_fbx)
                report["old"][tag] = (tris(old.data), len(uv_keys(old.data) & src_uv),
                                      len(uv_keys(old.data)))
            except Exception as e:
                report["old"][tag] = (0, 0, 0)
            bpy.ops.wm.read_factory_settings(use_empty=True)
            lp = import_fbx(hp_fbx)

    ratios = {"lod1": 0.55, "lod2": 0.25}
    for tag in ("lod1", "lod2"):
        lod = decimate_uv_safe(lp, dirname + "_" + tag.upper(), ratios[tag], src_t)
        keys = uv_keys(lod.data)
        report["new"][tag] = (tris(lod.data), len(keys & src_uv), len(keys))
        export(lod, os.path.join(base, f"{dirname}_{tag}.fbx"))
    return report


dirs = sorted(d for d in os.listdir(HP) if os.path.isdir(os.path.join(HP, d)))
if ONLY:
    dirs = [d for d in dirs if d == ONLY]
print(f"[fixlod] моделей к пересборке: {len(dirs)}")

bad = []
for i, d in enumerate(dirs, 1):
    try:
        r = process(d)
    except Exception as e:
        print(f"[{i}/{len(dirs)}] {d}: ОШИБКА {e}")
        bad.append(d)
        continue
    if r is None:
        continue
    line = f"[{i}/{len(dirs)}] {r['name']}: LP {r['lp_tris']} трис"
    for tag in ("lod1", "lod2"):
        o = r["old"].get(tag, (0, 0, 0))
        n = r["new"][tag]
        ofrac = o[1] / max(1, o[2])
        nfrac = n[1] / max(1, n[2])
        line += f" · {tag}: старый UV {ofrac*100:.0f}% ({o[0]} трис) → новый UV {nfrac*100:.0f}% ({n[0]} трис)"
        if nfrac < 0.80:
            bad.append(d)
    print(line)

print(f"[fixlod] ГОТОВО. Пересобрано {len(dirs)} моделей. Проблемные (UV<80%): {bad if bad else 'нет'}")
