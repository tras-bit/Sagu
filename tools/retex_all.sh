#!/usr/bin/env bash
# RETEX 1.2.0 — перезапекание ВСЕХ моделей с процедурными текстурами, всё в 2K.
# Два параллельных воркера (по ядру), сэмплы 24. ОБА воркера коммитят каждые 2 модели
# (через flock, без конфликтов) — ресеты песочницы теряют максимум текущую модель.
# Маркер Assets/Subsistence/ModelsHP/<имя>/.retex2k = модель готова.
# Прервали/песочница упала → перезапуск продолжает с места остановки.
set -u
cd "$(dirname "$0")/.."
HP="Assets/Subsistence/ModelsHP"
GLOCK="/tmp/retex_git.lock"

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

commit_progress() {  # $1 = имя последней модели (для сообщения)
  flock "$GLOCK" bash -c "
    cd '$PWD' &&
    git add -A '$HP' docs/retex_wave.log tools 2>/dev/null &&
    git commit -q -m 'RETEX 2K: $1' 2>/dev/null &&
    git push -q origin arena/01a0af27-sagu 2>/dev/null &&
    echo '===== COMMIT+PUSH (после $1) ====='
  " 2>/dev/null
  return 0
}

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

worker() {  # $1=список имён через пробел, $2=ядро, $3=тег
  local core="$2" tag="$3" cnt=0 n
  for n in $1; do
    [ -f "$HP/$n/.retex2k" ] && continue
    if bake_one "$n" "$core" "$tag"; then
      cnt=$((cnt + 1))
      commit_progress "$n"
    fi
  done
}

worker "${A_LIST[*]}" 0 A &
worker "${B_LIST[*]}" 1 B &
wait

flock "$GLOCK" bash -c "cd '$PWD' && git add -A '$HP' docs/retex_wave.log tools 2>/dev/null && git commit -q -m 'RETEX 2K: хвост волны' 2>/dev/null && git push -q origin arena/01a0af27-sagu 2>/dev/null"
echo "===== RETEX WAVE COMPLETE ====="
