#!/usr/bin/env bash
# SUBSISTENCE — батч 3D-иконок 256px из HP-комплектов (ANSWERS_V3 24а).
# Рендерит docs/icons256_raw/<icon>.png для каждой иконки, мапящейся на модель;
# финальная сборка в Resources/icons — python3 tools/make_icons_256.py
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/.."
source ~/.cache/blender_env.sh

python3 - <<'EOF' > /tmp/icon_jobs.txt
import os
ROOT = "."
SMART = {
    "tool_geger": None,  # заглушка, реальный список ниже
}
EOF

python3 - <<'EOF' > /tmp/icon_jobs.txt
import os
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
ROOT = os.path.abspath(".")
icons = {f[:-4] for f in os.listdir(os.path.join(ROOT, "Assets/Subsistence/Resources/icons")) if f.endswith(".png")}
models = sorted(os.listdir(os.path.join(ROOT, "Assets/Subsistence/ModelsHP")))
msuf = {}
for m in models:
    msuf.setdefault(m.split("_", 1)[1], m)
for i in sorted(icons):
    m = SMART.get(i) or msuf.get(i)
    if m and m in models and os.path.exists(os.path.join(ROOT, f"Assets/Subsistence/ModelsHP/{m}/{m}_hp.fbx")) \
       and not os.path.exists(os.path.join(ROOT, f"docs/icons256_raw/{i}.png")):
        print(f"{m}|{i}")
EOF

n=$(wc -l < /tmp/icon_jobs.txt)
echo "===== ICONS BATCH: $n рендеров ====="
while read -r job; do
  [ -z "$job" ] && continue
  model="${job%%|*}"; icon="${job##*|}"
  echo "===== ICON START $icon ($model) ====="
  if python3 tools/bpy_run.py tools/blender/icons_hp.py -- --model "$model" --icon "$icon"; then
    echo "===== ICON DONE $icon ====="
  else
    echo "===== ICON FAIL $icon ====="
  fi
done < /tmp/icon_jobs.txt
echo "===== ICONS BATCH COMPLETE ====="
