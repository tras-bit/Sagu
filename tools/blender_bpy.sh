#!/usr/bin/env bash
# SUBSISTENCE — запуск Blender-скрипта проекта через bpy-модуль (headless).
# Использование: bash tools/blender_bpy.sh tools/blender/models_weapons.py [-- --only W_rifle_ak]
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
source "$HOME/.cache/blender_env.sh"
exec python3 "$ROOT/tools/bpy_run.py" "$@"
