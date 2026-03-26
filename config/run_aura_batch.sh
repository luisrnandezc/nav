#!/usr/bin/env bash
# Entry point for scheduled tasks (e.g. PythonAnywhere).
# Running scheduled tasks with BASH, not Python:
#   PYTHON=/path/to/venv/bin/python bash /path/to/run_aura_batch.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

exec "$PYTHON_BIN" "$SCRIPT_DIR/aura/scripts/run_aura_batch.py"
