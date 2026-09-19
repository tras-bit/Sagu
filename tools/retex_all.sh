#!/usr/bin/env bash
# RETEX 1.2.0 — перезапекание ВСЕХ моделей с процедурными текстурами, всё в 2K.
# Два параллельных воркера (по ядру), сэмплы 24 — ~3× быстрее.
# Маркер Assets/Subsistence/ModelsHP/<имя>/.retex2k = модель готова.
# Воркер A коммитит каждые 4 модели + пуш (ресеты песочницы не теряют прогресс).
# Прервали/песочница упала → перезапуск продолжает с места остановки.
set -u
cd "$(dirname "$0")/.."
HP="Assets/Subsistence/ModelsHP"

# --- собираем ожидающие модели и делим пополам (чёт/нечёт) ---
PENDING=()
for d in "$HP"/*/; do
  n="$(basename "$d")"
  [ -f "$d/${n}_hp.fbx" ] || continue
  [ -f "$d/.retex2k" ] && continue
  PENDING+=("$n")
done
echo "===== RETEX: ожидаает ${#PENDING[@]} моделей ====="
A_LIST=(); B_LIST=()
for i in "${!PENDING[@]}"; do
  if [ $((i % 2)) -eq 0 ]; then A_LIST+=("${PENDING[$i]}"); else B_LIST+=("${PENDING[$i]}"); fi
done

bake_one() {  # $1=модель, $2=ядро, $3=тег воркера
  local n="$1" core="$2" tag="$3"
  echo "===== [$tag] RETEX $n ====="
  taskset -c "$core" bash tools/blender_bpy.sh tools/blender/hp_pipeline.py -- \
      --model "$n" --size 2048 --subdiv 2 --retex --bake-samples 24 --no-sheet 2>&1 \
    | grep --line-buffered -E "^\[hp\]|Error|Traceback|Killed"
  local rc=${PIPESTATUS[0]}
  if [ "$rc" -eq 0 ]; then
    touch "$HP/$n/.retex2k"
    echo "===== [$tag] RETEX DONE $n ====="
    return 0
  fi
  echo "===== [$tag] RETEX FAIL $n (код $rc) ====="
  return 1
}

worker() {  # $1=список имён через пробел, $2=ядро, $3=тег, $4=коммитить?
  local core="$2" tag="$3" docommit="$4" cnt=0 n
  for n in $1; do
    [ -f "$HP/$n/.retex2k" ] && continue
    if bake_one "$n" "$core" "$tag"; then
      cnt=$((cnt + 1))
      if [ "$docommit" = "1" ] && [ $((cnt % 4)) -eq 0 ]; then
        git add -A "$HP" docs/retex_wave.log tools 2>/dev/null
        git commit -q -m "RETEX 2K: партия $((cnt / 4)) (последняя: $n)" 2>/dev/null \
          && git push -q origin arena/01a0af27-sagu 2>/dev/null \
          && echo "===== [$tag] COMMIT+PUSH ($cnt готово этим воркером) =====" \
          || echo "===== [$tag] COMMIT FAIL (продолжаем) ====="
      fi
    fi
  done
}

worker "${A_LIST[*]}" 0 A 1 &
WA=$!
worker "${B_LIST[*]}" 1 B 0 &
WB=$!
wait $WA $WB

git add -A "$HP" docs/retex_wave.log tools 2>/dev/null
git commit -q -m "RETEX 2K: хвост волны" 2>/dev/null && git push -q origin arena/01a0af27-sagu 2>/dev/null
echo "===== RETEX WAVE COMPLETE ====="
