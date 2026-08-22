#!/usr/bin/env bash
# Paseo worktree setup — runs once after worktree creation.
# Delegates to ensure-setup.sh for the actual work.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/ensure-setup.sh"
