#!/bin/bash
set -euo pipefail

echo "Installing repository hooks to .githooks and enabling them via git config..."

git config core.hooksPath .githooks
chmod +x .githooks/pre-commit || true

echo "Done. The pre-commit hook will now run for local commits."

exit 0
