#!/usr/bin/env bash
# Shared setup logic — called by launch.sh and worktree_setup.sh.
# Checks if setup is needed, runs it if so.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# --- Check if setup was already done ---
if [ -f ".venv/bin/activate" ] && [ -x "frontend/node_modules/.bin/vite" ]; then
  echo "==> Dependencies already installed, skipping setup."
  exit 0
fi

SRC="${PASEO_SOURCE_CHECKOUT_PATH:-}"

echo "==> Setting up m3tacron dependencies..."

# --- Submodules ---
echo "==> Initializing submodules..."
if ! git submodule update --init --recursive 2>/dev/null; then
  echo "!! Submodule clone failed, retrying..."
  sleep 3
  if ! git submodule update --init --recursive 2>/dev/null; then
    echo "!! Submodule clone failed twice."
    if [[ -n "$SRC" && -d "$SRC/external_data" ]]; then
      echo "==> Copying external_data from source checkout instead..."
      rm -rf external_data
      cp -a "$SRC/external_data" external_data
    else
      echo "!! No source checkout to copy from. Submodules will be missing."
    fi
  fi
fi

# --- Python venv ---
echo "==> Setting up Python venv..."
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'

# --- Frontend npm ---
echo "==> Installing frontend dependencies..."
npm ci --prefix frontend

# --- Copy dev dump ---
echo "==> Copying dev dump..."
mkdir -p local-data/dumps
if [[ -n "$SRC" ]]; then
  cp "$SRC/local-data/dumps/dev_latest.dump" local-data/dumps/dev_latest.dump 2>/dev/null || true
fi

# --- Copy SSH key ---
if [[ -n "$SRC" ]]; then
  mkdir -p .ssh
  cp "$SRC/.agents/skills/m3tacron/ssh_key" .ssh/ssh_key 2>/dev/null || true
  chmod 600 .ssh/ssh_key 2>/dev/null || true
fi

echo "==> Setup complete."
