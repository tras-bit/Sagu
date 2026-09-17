#!/usr/bin/env bash
# SUBSISTENCE — пакетный хай-поли пасс (ANSWERS_V3 8а/13а).
# Использование: bash tools/hp_batch.sh [спека1 спека2 ...]
#   Спека = "Модель [--ключ значение ...]" — доп. аргументы перекрывают дефолты
#   (напр. "IT_apple --kind organic --size 1024"). Без аргументов — монстры спринта 1.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HOME/.cache/blender_env.sh"
export PYTHONUNBUFFERED=1

MODELS=("$@")
if [ ${#MODELS[@]} -eq 0 ]; then
  MODELS=(MN_smiler MN_hound MN_partygoer MN_skinstealer MN_whisperer MN_drowned MN_spark)
fi

for spec in "${MODELS[@]}"; do
  read -r -a parts <<< "$spec"
  m="${parts[0]}"
  extra=("${parts[@]:1}")
  echo "===== HP START $m ====="
  python3 -u "$HERE/bpy_run.py" "$HERE/blender/hp_pipeline.py" -- \
       --model "$m" --size 2048 --subdiv 2 --samples 24 ${extra[@]+"${extra[@]}"} 2>&1 \
       | grep --line-buffered -E "^\[hp\]|Error|Traceback|Killed"
  rc=${PIPESTATUS[0]}
  if [ "$rc" -eq 0 ]; then
    echo "===== HP DONE $m ====="
  else
    echo "===== HP FAIL $m (код $rc) ====="
  fi
  sleep 2
done
echo "===== BATCH COMPLETE ====="
