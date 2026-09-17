#!/usr/bin/env bash
# SUBSISTENCE — восстановление headless-Blender в песочнице Arena (bpy 5.0 + sysroot).
# Запускать после рестарта песочницы:  bash tools/setup_blender.sh
# (Старый вариант с полным бинарником Blender 4.3 — см. tools/setup_blender_binary.sh,
#  он качает ~350 МБ с cdn.blender.org, который в песочке Arena заблокирован.)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
CACHE="$HOME/.cache"

echo "[1/4] bpy (Blender как python-модуль, PyPI)..."
python3 -c "import bpy" 2>/dev/null || pip install --break-system-packages bpy

echo "[2/4] системные библиотеки из sysroot (Debian bookworm, libGL/X11)..."
mkdir -p "$CACHE/sysroot" "$CACHE/sysroot-stubs"
if [ -f "$ROOT/incoming/sysroot-bookworm.tar.gz" ]; then
  tar xzf "$ROOT/incoming/sysroot-bookworm.tar.gz" -C "$CACHE/sysroot"
else
  echo "!! не найден incoming/sysroot-bookworm.tar.gz (воркфлоу .github/workflows/fetch-sysroot.yml его создаёт)" >&2
  exit 1
fi

echo "[3/4] стабы GPU-библиотек (CUDA/HIP/LevelZero — не нужны для CPU-рендера)..."
cd "$CACHE/sysroot-stubs"
for lib in libcuda.so.1 libamdhip64.so.6 libze_loader.so.1; do
  [ -f "$lib" ] || echo "" | cc -shared -o "$lib" -Wl,-soname,"$lib" -x c -
done

BPY_DIR="$(python3 -c "import importlib.util,os;print(os.path.dirname(importlib.util.find_spec('bpy').origin))")"
cat > "$CACHE/blender_env.sh" <<ENV
# source ~/.cache/blender_env.sh  — окружение headless-Blender (bpy) для SUBSISTENCE
export LD_LIBRARY_PATH="$CACHE/sysroot/sysroot/usr/lib/x86_64-linux-gnu:$BPY_DIR/lib:$CACHE/sysroot-stubs"
ENV

echo "[4/4] проверка..."
source "$CACHE/blender_env.sh"
python3 - <<'PY'
import bpy
print("[OK] Blender", bpy.app.version_string, "— headless bpy работает")
PY

echo
echo "Готово. Как пользоваться:"
echo "  source ~/.cache/blender_env.sh"
echo "  python3 tools/bpy_run.py tools/blender/models_weapons.py -- --check   # самопроверка скрипта"
echo "  bash tools/blender_bpy.sh tools/blender/models_props.py              # обёртка со всем сразу"
