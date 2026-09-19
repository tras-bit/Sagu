#!/usr/bin/env bash
# RETEX 1.2.0 — перезапекание ВСЕХ моделей с процедурными текстурами, всё в 2K.
# Маркер Assets/Subsistence/ModelsHP/<имя>/.retex2k = модель готова.
# Каждые 5 моделей — коммит (ресеты песочницы больше не теряют прогресс).
# Прервали/песочница упала → перезапуск продолжает с места остановки.
set -u
cd "$(dirname "$0")/.."
HP="Assets/Subsistence/ModelsHP"
BATCH=0
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
    BATCH=$((BATCH + 1))
    if [ $((BATCH % 5)) -eq 0 ]; then
      git add -A "$HP" docs/retex_wave.log tools 2>/dev/null
      git commit -q -m "RETEX 2K: партия $((BATCH / 5)) (последняя: $n)" 2>/dev/null \
        && git push -q origin arena/01a0af27-sagu 2>/dev/null \
        && echo "===== COMMIT+PUSH (партия $((BATCH / 5)), $BATCH готово) =====" \
        || echo "===== COMMIT FAIL (продолжаем) ====="
    fi
  else
    echo "===== RETEX FAIL $n (код $rc) ====="
  fi
done
# финальный коммит остатка
git add -A "$HP" docs/retex_wave.log 2>/dev/null
git commit -q -m "RETEX 2K: хвост волны" 2>/dev/null && git push -q origin arena/01a0af27-sagu 2>/dev/null
echo "===== RETEX WAVE COMPLETE ====="
