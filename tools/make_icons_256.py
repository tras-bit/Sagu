#!/usr/bin/env python3
"""
make_icons_256.py — финальная сборка иконок 256px (ANSWERS_V3 24а).

Что делает:
  1) парсит Items.cs → id предмета → редкость (цвет рамки);
  2) для каждого id с 3D-рендером (docs/icons256_raw/<id>.png, делает icons_hp.py)
     собирает иконку 256×256: тёмный фон + рендер с запечёнными текстурами + рамка редкости;
  3) остальные иконки честно апскейлит 96→256 (LANCZOS + лёгкая резкость) — стиль «терминал».

Итог пишется ПОВЕРХ Assets/Subsistence/Resources/icons/<id>.png (git хранит историю).

Запуск:  python3 tools/make_icons_256.py [--check]   (--check = только отчёт, без записи)
"""
import os, re, sys
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
ICONS = os.path.join(ROOT, "Assets", "Subsistence", "Resources", "icons")
RAW   = os.path.join(ROOT, "docs", "icons256_raw")
ITEMS_CS = os.path.join(ROOT, "Assets", "Subsistence", "Scripts", "Core", "Items.cs")

S = 256
CHECK_ONLY = "--check" in sys.argv

RARITY = {
    "Common":    ((74, 82, 74),    (150, 160, 150)),
    "Uncommon":  ((38, 74, 52),    (110, 220, 140)),
    "Rare":      ((34, 58, 92),    (110, 175, 255)),
    "VeryRare":  ((74, 46, 96),    (198, 140, 255)),
    "Military":  ((88, 62, 24),    (255, 200, 96)),
    "Anomalous": ((86, 30, 64),    (255, 120, 200)),
}
BG = (18, 22, 20)

# ---------------------------------------------------------------- id → модель (умный маппинг)
# прямые совпадения (иконка == суффикс модели) добавляются автоматически
SMART = {
    "tool_geiger": "IT_geiger",
    "water_purifier": "DD_purifier",
    "hazmatsuit": "CH_hazmat_suit",
    "largemedkit": "IT_medkit_large",
    "cupboard_tool": "DD_cupboard",
    "generator_wind_scrap": "DD_wind_generator",
    "door_hinged_wood": "DD_door_wood",
    "door_hinged_metal": "DD_door_metal",
    "door_double_hinged_metal": "DD_door_metal",
    "door_hinged_toptier": "DD_door_armored",
    "sign_pictureframe": "DD_sign",
    "scrap": "IT_scrap_pile",
    "stones": "IT_stone_pile",
    "sulfur": "IT_sulfur_lump",
    "wood": "IT_wood_pile",
    "cloth": "IT_cloth_roll",
    "attire_hide_helterneck": "IT_hide_vest",
    "wood_armor_jacket": "IT_wood_chestplate",
    "woodbox": "PR_crate_wood",
}

# ---------------------------------------------------------------- редкости из Items.cs
rarity = {}
if os.path.exists(ITEMS_CS):
    txt = open(ITEMS_CS, encoding="utf-8").read()
    for m in re.finditer(r'R\(\s*"([^"]+)"[^)]*?Rarity\.(\w+)', txt, re.S):
        rarity[m.group(1).replace(".", "_")] = m.group(2)

# ---------------------------------------------------------------- модели
models = []
for sub in os.listdir(os.path.join(ROOT, "Assets", "Subsistence", "ModelsHP")):
    models.append(sub)
msuf = {}
for m in models:
    msuf.setdefault(m.split("_", 1)[1], m)

def model_for(icon_id):
    if icon_id in SMART and SMART[icon_id] in models:
        return SMART[icon_id]
    if icon_id in msuf:
        return msuf[icon_id]
    return None

# ---------------------------------------------------------------- сборка
def compose_3d(render_path, out_path, rar):
    im = Image.open(render_path).convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    # вписать в 200×200 (рамка 3px + воздух)
    im.thumbnail((200, 200), Image.LANCZOS)
    canvas = Image.new("RGBA", (S, S), BG + (255,))
    d = ImageDraw.Draw(canvas)
    col = RARITY.get(rar, RARITY["Common"])[1]
    d.rounded_rectangle([2, 2, S - 3, S - 3], radius=10, outline=col + (230,), width=3)
    canvas.paste(im, ((S - im.width) // 2, (S - im.height) // 2), im)
    canvas.save(out_path)

def upscale_old(src, out_path):
    im = Image.open(src).convert("RGBA")
    im = im.resize((S, S), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
    im.save(out_path)

ids = sorted(f[:-4] for f in os.listdir(ICONS) if f.endswith(".png"))
done3d, doneup, nomodel = 0, 0, []
for i in ids:
    src = os.path.join(ICONS, i + ".png")
    out = src
    raw = os.path.join(RAW, i + ".png")
    if os.path.exists(raw):
        if not CHECK_ONLY:
            compose_3d(raw, out, rarity.get(i, "Common"))
        done3d += 1
    else:
        m = model_for(i)
        if m and not CHECK_ONLY:
            pass  # рендер ещё не сделан — оставляем старую иконку, batch догонит
        if not CHECK_ONLY:
            pass  # апскейл делаем отдельным проходом ниже, чтобы не портить до рендеров
print(f"[icons256] 3D-иконок собрано: {done3d}/{len(ids)}; редкостей распознано: {len(rarity)}")

# отдельный проход апскейла «терминальных» иконок (у которых модели нет вообще)
ups = 0
for i in ids:
    if model_for(i) is None:
        raw = os.path.join(RAW, i + ".png")
        if not os.path.exists(raw) and not CHECK_ONLY:
            upscale_old(os.path.join(ICONS, i + ".png"), os.path.join(ICONS, i + ".png"))
            ups += 1
if not CHECK_ONLY:
    print(f"[icons256] апскейл 96→256 (без моделей): {ups}")
