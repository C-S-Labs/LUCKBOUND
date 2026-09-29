#!/usr/bin/env bash
# One-time setup for running Blender Python (bpy) scripts in a Claude Code cloud session.
# Put this at the root of your repo. Usage:  bash setup_cloud.sh
set -e

# bpy on PyPI requires one specific Python version (3.11 for Blender 4.x).
PY_VERSION="3.11"
BPY_VERSION="4.2.0"   # LTS; change if you use a newer Blender locally

echo "==> Checking for Python $PY_VERSION"
if command -v python$PY_VERSION >/dev/null 2>&1; then
  PY=python$PY_VERSION
else
  echo "==> python$PY_VERSION not found, trying uv to fetch it"
  pip install --quiet uv --break-system-packages || pip install --quiet uv
  uv python install $PY_VERSION
  PY="$(uv python find $PY_VERSION)"
fi

echo "==> Creating virtual environment in .venv"
$PY -m venv .venv
source .venv/bin/activate

echo "==> Installing bpy $BPY_VERSION (large download, ~300MB)"
pip install --quiet --upgrade pip
pip install --quiet "bpy==$BPY_VERSION"

# bpy needs a few system libraries for headless use; install if apt is available.
if command -v apt-get >/dev/null 2>&1; then
  (sudo apt-get install -y -qq libxrender1 libxi6 libxkbcommon0 libsm6 libgl1 >/dev/null 2>&1 \
   || apt-get install -y -qq libxrender1 libxi6 libxkbcommon0 libsm6 libgl1 >/dev/null 2>&1) || true
fi

echo "==> Verifying"
python -c "import bpy; print('bpy OK, Blender', bpy.app.version_string)"
echo "Done. Activate later with: source .venv/bin/activate"
