#!/usr/bin/env bash
# RETEX 1.2.0 — перезапекание ВСЕХ моделей с процедурными текстурами, всё в 2K.
# Маркер Assets/Subsistence/ModelsHP/<имя>/.retex2k = модель готова.
# Прервали/песочница упала → перезапуск продолжает с места остановки.
set -u
cd "$(dirname "$0")/.."
HP="Assets/Subsistence/ModelsHP"
for d in "$HP"/*/; do
  n="$(basename "$d")"
  [ -f "$d/${n}_hp.fbx" ] || continue
  if [ -f "$d/.retex2k" ]; then continue; fi
  echo "===== RETEX $n ====="
  bash tools/blender_bpy.sh tools/blender/hp_pipeline.py -- --model "$n" --size 2048 --subdiv 2 --retex --bake-samples 48 --no-sheet 2>&1 \
    | grep --line-buffered -E "^\[hp\]|Error|Traceback|Killed"
  rc=${PIPESTATUS[0]}
  if [ "$rc" -eq 0 ]; then
    touch "$d/.retex2k"
    echo "===== RETEX DONE $n ====="
  else
    echo "===== RETEX FAIL $n (код $rc) ====="
  fi
done
echo "===== RETEX WAVE COMPLETE ====="
