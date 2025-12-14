#!/usr/bin/env bash
set -euo pipefail

# This script builds a Windows EXE for the installer. It will attempt to run pyinstaller.
# If you're running on Linux and you want a Windows EXE, use Wine with a Windows Python.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "pyinstaller not found in PATH, please install it with: pip install pyinstaller"
  exit 1
fi

python3 $SCRIPT_DIR/build_installer.py

echo "Done. Look in dist/ for the generated exe (if built on Windows)."
