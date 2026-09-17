#!/usr/bin/env python3
"""SUBSISTENCE — make_hp_sheet.py · сводный лист хай-поли превью (без Blender, только PIL).
Использование: python3 tools/make_hp_sheet.py MN_smiler MN_hound ... → docs/previews/_hp_sheet_<группа>.png
"""
import sys, os
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
models = sys.argv[1:]
group = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith(("MN_", "W_", "CH_", "IT_", "PR_", "BD_", "DD_", "EX_", "LV_")) else "sheet"
if not models:
    sys.exit("укажи модели: python3 tools/make_hp_sheet.py MN_smiler MN_hound [имя_группы]")

thumbs = []
for m in models:
    p = os.path.join(ROOT, "docs", "previews", f"_hp_{m}.png")
    if os.path.exists(p):
        thumbs.append((m, Image.open(p).convert("RGB")))
    else:
        print("нет превью:", m)

if not thumbs:
    sys.exit("ни одного превью не найдено")

TW = 640  # ширина миниатюры (превью 960×540 → 640×360)
TH = int(TW * 540 / 960)
cols = 2
rows = (len(thumbs) + cols - 1) // cols
pad, label_h = 12, 26
W = cols * TW + (cols + 1) * pad
H = rows * (TH + label_h) + (rows + 1) * pad
sheet = Image.new("RGB", (W, H), (6, 18, 11))
draw = ImageDraw.Draw(sheet)

for i, (name, im) in enumerate(thumbs):
    r, c = divmod(i, cols)
    x = pad + c * (TW + pad)
    y = pad + r * (TH + label_h + pad)
    sheet.paste(im.resize((TW, TH), Image.LANCZOS), (x, y))
    draw.text((x + 4, y + TH + 5), name + "  (слева: игра с текстурами · справа: хай-поли)", fill=(92, 255, 146))

out = os.path.join(ROOT, "docs", "previews", f"_hp_sheet_{group}.png")
sheet.save(out, optimize=True)
print("лист:", out, sheet.size)
