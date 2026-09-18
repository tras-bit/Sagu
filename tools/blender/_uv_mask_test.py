#!/usr/bin/env python3
"""Диагностика: попадают ли UV LOD в заполненную область атласа LP (куда пеклись карты).
Старый LOD берём из git (HEAD), новый — текущий файл. Вывод: доля UV-петель внутри маски."""
import bpy, os, sys, subprocess
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HP = os.path.join(ROOT, "Assets", "Subsistence", "ModelsHP")
TMP = "/tmp/_lodtest"
os.makedirs(TMP, exist_ok=True)

def import_fbx(path):
    before = set(o.name for o in bpy.context.scene.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.context.scene.objects if o.name not in before and o.type == "MESH"]
    assert new, "нет мешей: " + path
    new.sort(key=lambda o: len(o.data.vertices), reverse=True)
    return new[0]

def uv_mask(obj, size=256):
    uv = obj.data.uv_layers.active
    assert uv, "нет UV"
    img = Image.new("1", (size, size), 0)
    dr = ImageDraw.Draw(img)
    for p in obj.data.polygons:
        idx = [l for l in p.loop_indices]
        pts = [(uv.data[l].uv[0]*size, (1.0-uv.data[l].uv[1])*size) for l in idx]
        if len(pts) == 3:
            dr.polygon(pts, fill=1)
        else:
            for k in range(1, len(pts)-1):
                dr.polygon([pts[0], pts[k], pts[k+1]], fill=1)
    return img

def inside_frac(obj, mask):
    w, h = mask.size
    uv = obj.data.uv_layers.active
    px = mask.load()
    hit = tot = 0
    for d in uv.data:
        x = min(w-1, max(0, int(d.uv[0]*w)))
        y = min(h-1, max(0, int((1.0-d.uv[1])*h)))
        tot += 1
        if px[x, y]: hit += 1
    return hit / max(1, tot)

def old_from_git(dirname, tag):
    rel = f"Assets/Subsistence/ModelsHP/{dirname}/{dirname}_{tag}.fbx"
    dst = os.path.join(TMP, f"{dirname}_{tag}_OLD.fbx")
    r = subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{rel}"], capture_output=True)
    if r.returncode != 0: return None
    open(dst, "wb").write(r.stdout)
    return dst

for name in sys.argv[1:] if len(sys.argv) > 1 else ["BD_door_armored", "MN_smiler", "PR_vending_machine"]:
    base = os.path.join(HP, name)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    lp = import_fbx(os.path.join(base, name + "_hp.fbx"))
    mask = uv_mask(lp)
    lp_in = inside_frac(lp, mask)
    line = f"{name}: LP внутри маски {lp_in*100:.0f}%"
    for tag in ("lod1", "lod2"):
        old = old_from_git(name, tag)
        if old:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            o = import_fbx(old)
            line += f" · {tag} СТАРЫЙ {inside_frac(o, mask)*100:.0f}%"
        bpy.ops.wm.read_factory_settings(use_empty=True)
        n = import_fbx(os.path.join(base, f"{name}_{tag}.fbx"))
        line += f" · {tag} НОВЫЙ {inside_frac(n, mask)*100:.0f}%"
    print(line, flush=True)
