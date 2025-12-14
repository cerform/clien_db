#!/usr/bin/env bash
set -euo pipefail

echo "Running installer smoke test (dry-run)"
python3 tools/install_and_deploy.py --project test-project --region europe-west1 --service smoke-test --dry-run
echo "Installer smoke run completed (dry-run)"
