#!/usr/bin/env bash
# SUBSISTENCE — спринт 1.3: персонажи (Bacteria-архив, хазмат, торговец) + все 37 предметов.
# Предметы: карты 1K (ANSWERS_V3 11а), лёгкий рендер превью; органическая мелочь — organic-профиль.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"

exec bash "$HERE/hp_batch.sh" \
  "MN_bacteria" \
  "CH_hazmat_suit" \
  "CH_trader_npc" \
  "IT_ammo_556 --size 1024 --samples 12" \
  "IT_ammo_shell --size 1024 --samples 12" \
  "IT_antidote --size 1024 --samples 12" \
  "IT_apple --kind organic --strength 0.002 --size 1024 --samples 12" \
  "IT_arrow_bundle --size 1024 --samples 12" \
  "IT_bandage --size 1024 --samples 12" \
  "IT_boots_hide --size 1024 --samples 12" \
  "IT_boots_rubber --size 1024 --samples 12" \
  "IT_bucket --size 1024 --samples 12" \
  "IT_can_beans --size 1024 --samples 12" \
  "IT_can_tuna --size 1024 --samples 12" \
  "IT_chlorine --size 1024 --samples 12" \
  "IT_chocolate --size 1024 --samples 12" \
  "IT_cloth_roll --size 1024 --samples 12" \
  "IT_diving_mask --size 1024 --samples 12" \
  "IT_duct_tape --size 1024 --samples 12" \
  "IT_flashlight --size 1024 --samples 12" \
  "IT_flippers --size 1024 --samples 12" \
  "IT_fuse_hi --size 1024 --samples 12" \
  "IT_geiger --size 1024 --samples 12" \
  "IT_glow_mushroom --kind organic --strength 0.002 --size 1024 --samples 12" \
  "IT_hide_vest --size 1024 --samples 12" \
  "IT_lamp_portable --size 1024 --samples 12" \
  "IT_meat_raw --kind organic --strength 0.002 --size 1024 --samples 12" \
  "IT_medkit_large --size 1024 --samples 12" \
  "IT_oxygen_tank --size 1024 --samples 12" \
  "IT_respirator --size 1024 --samples 12" \
  "IT_rubber_gloves --size 1024 --samples 12" \
  "IT_scrap_pile --size 1024 --samples 12" \
  "IT_stone_pile --size 1024 --samples 12" \
  "IT_sulfur_lump --kind organic --strength 0.0015 --size 1024 --samples 12" \
  "IT_torch_lantern --size 1024 --samples 12" \
  "IT_water_bottle --size 1024 --samples 12" \
  "IT_wood_chestplate --size 1024 --samples 12" \
  "IT_wood_helmet --size 1024 --samples 12" \
  "IT_wood_pile --size 1024 --samples 12" \
  "IT_wrench_insulated --size 1024 --samples 12"
