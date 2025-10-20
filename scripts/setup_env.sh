#!/usr/bin/env bash
# Create a virtual environment in .venv and install repository-level Python tools
set -euo pipefail

# Resolve script directory so paths work when the script is invoked from repo root via Makefile
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REQ="$REPO_ROOT/requirements.txt"
VENV_DIR="$REPO_ROOT/.venv"

if [ ! -f "$REQ" ]; then
  echo "requirements.txt not found at $REQ"
  exit 1
fi

python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -r "$REQ"

echo "Virtual environment created at $VENV_DIR and requirements installed."

echo "Activate with: source $VENV_DIR/bin/activate"
