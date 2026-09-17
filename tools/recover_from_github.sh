#!/usr/bin/env bash
# SUBSISTENCE — восстановление песочницы Arena после сброса снапшота.
# Снапшот воркспейса имеет лимит (~128 МБ артефактов) и может откатиться к базе;
# источник истины — GitHub. Этот скрипт поднимает всё за пару минут.
#   bash tools/recover_from_github.sh
set -e
cd "$(dirname "$0")/.."
BRANCH="arena/01a0af27-sagu"

echo "[1/4] git: тянуть ветку $BRANCH..."
git fetch origin "refs/heads/$BRANCH:refs/remotes/origin/$BRANCH"
git reset --hard "origin/$BRANCH"
git log --oneline -1

echo "[2/4] python-пакеты песочницы (bpy, PIL, линтеры)..."
pip install -q --break-system-packages bpy pillow tree_sitter tree_sitter_c_sharp || true

echo "[3/4] Blender headless (sysroot из incoming/)..."
bash tools/setup_blender.sh

echo "[4/4] проверка ModelsHP..."
ls Assets/Subsistence/ModelsHP 2>/dev/null | wc -l
echo "[OK] песочница восстановлена. Незапушенное придётся перегенерить (см. docs/HIGHPOLY_TRACKER.md)."
