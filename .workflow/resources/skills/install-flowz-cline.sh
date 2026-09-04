#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "FlowZ Cline installer requires Python 3 (looked for: $PYTHON_BIN)." >&2
  exit 127
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/install-flowz-cline-ubuntu.py" "$@"
