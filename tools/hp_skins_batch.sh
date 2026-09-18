#!/usr/bin/env bash
# SUBSISTENCE — батч рендеров скинов (25а): 10 моделей × цвета скинов + 4 PIL-карточки.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/.."
source ~/.cache/blender_env.sh

# предмет → модель (как ModelLibrary). Пусто = модели нет, пойдёт PIL-карточка.
python3 - <<'EOF' > /tmp/skin_jobs.txt
import re, os
txt = open("Assets/Subsistence/Scripts/Progression/Skins.cs", encoding="utf-8").read()
MODEL_FOR = {
    "rifle.ak": "W_rifle_ak", "smg.mp5": "W_smg_mp5", "lmg.m249": "W_lmg_m249",
    "shotgun.pump": "W_shotgun_pump", "hazmatsuit": "CH_hazmat_suit",
    "cart.loot": "PR_loot_cart", "scooter": "PR_scooter",
    "metal.plate.torso": "", "exoskeleton.suit": "", "hatchet": "", "hammer": "",
}
# S("id", "имя", "itemId", scrap, token, r, g, b, "note")
for m in re.finditer(r'S\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*(\d+),\s*(\d+),\s*([\d.]+)f,\s*([\d.]+)f,\s*([\d.]+)f,\s*"([^"]*)"\)', txt):
    sid, name, item, r, g, b, note = m.group(1), m.group(2), m.group(3), m.group(6), m.group(7), m.group(8), m.group(9)
    model = MODEL_FOR.get(item, "")
    print(f"{sid}|{model}|{r},{g},{b}")
EOF

n=0
while IFS='|' read -r sid model rgb; do
  [ -z "$sid" ] && continue
  if [ -n "$model" ] && [ -d "Assets/Subsistence/ModelsHP/$model" ]; then
    echo "===== SKIN START $sid ($model) ====="
    if python3 tools/bpy_run.py tools/blender/skin_render.py -- --model "$model" --skin "$sid" --color "$rgb"; then
      echo "===== SKIN DONE $sid ====="; n=$((n+1))
    else
      echo "===== SKIN FAIL $sid ====="
    fi
  fi
done < /tmp/skin_jobs.txt

# карточки для скинов без моделей (PIL, 2048 мастер + 1024 игра)
python3 - <<'EOF'
import re, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
random.seed(11)
txt = open("Assets/Subsistence/Scripts/Progression/Skins.cs", encoding="utf-8").read()
MODEL_FOR = {"rifle.ak":1,"smg.mp5":1,"lmg.m249":1,"shotgun.pump":1,"hazmatsuit":1,"cart.loot":1,"scooter":1}
def font(sz, bold=True):
    for p in (("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
S = 2048
for m in re.finditer(r'S\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*(\d+),\s*(\d+),\s*([\d.]+)f,\s*([\d.]+)f,\s*([\d.]+)f,\s*"([^"]*)"\)', txt):
    sid, name, item, scrap, token, r, g, b, note = m.groups()
    if MODEL_FOR.get(item): continue          # у этих есть 3D-рендер
    col = (int(float(r)*255), int(float(g)*255), int(float(b)*255))
    im = Image.new("RGB", (S, S), (16, 20, 19))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 8, S-9, S-9], radius=64, outline=(92, 240, 146), width=8)
    # «свод-плита» цвета скина: скруглённый прямоугольник с полосами и зерном
    x0, y0, x1, y1 = 384, 512, S-384, S-512
    d.rounded_rectangle([x0, y0, x1, y1], radius=48, fill=col)
    for i in range(-S, S*2, 72):              # диагональные штрихи краски
        d.line([(i, 0), (i - S, S)], fill=tuple(min(255, c+18) for c in col), width=26)
    grain = Image.effect_noise((S, S), 22).convert("L")
    im = Image.composite(im, Image.new("RGB", (S, S), (10, 13, 12)), grain.point(lambda v: 235 + (v >> 5)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0, x1, y1], radius=48, outline=(0, 0, 0), width=10)
    d.text((96, 120), name, font=font(150), fill=(150, 255, 180))
    d.text((100, 330), f"предмет: {item}   ·   скрап {scrap}" + (f" + жетоны {token}" if int(token) else ""), font=font(64, False), fill=(120, 190, 140))
    d.text((96, S-260), "«" + note + "»", font=font(72, False), fill=(120, 190, 140))
    d.text((96, S-150), "КОНЦЕПТ-КАРТОЧКА · 3D-модели для этого предмета ещё нет", font=font(52, False), fill=(80, 130, 95))
    im.save(f"docs/previews/skins/{sid}_2048.png")
    im.resize((1024, 1024), Image.LANCZOS).save(f"Assets/Subsistence/Resources/skins/{sid}.png")
    print(f"[plate] {sid} ({name}) — карточка без модели")
EOF

echo "===== SKINS BATCH COMPLETE ($n рендеров + карточки) ====="
