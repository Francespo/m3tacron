#!/usr/bin/env bash
# Paseo worktree setup — runs once after worktree creation.
# Handles submodule init (with retry + fallback), Python venv, npm, dump, SSH key.
set -euo pipefail

SRC="${PASEO_SOURCE_CHECKOUT_PATH:-}"

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

echo "==> Setting up Python venv..."
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'

echo "==> Installing frontend dependencies..."
npm ci --prefix frontend

echo "==> Copying dev dump from source checkout..."
mkdir -p local-data/dumps
if [[ -n "$SRC" ]]; then
  cp "$SRC/local-data/dumps/dev_latest.dump" local-data/dumps/dev_latest.dump 2>/dev/null || true
fi

echo "==> Copying SSH key for seed.sh..."
if [[ -n "$SRC" ]]; then
  mkdir -p .ssh
  cp "$SRC/.agents/skills/m3tacron/ssh_key" .ssh/ssh_key 2>/dev/null || true
  chmod 600 .ssh/ssh_key 2>/dev/null || true
fi

echo "==> Worktree setup complete."
