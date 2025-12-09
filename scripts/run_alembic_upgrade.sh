#!/usr/bin/env bash
set -euo pipefail

echo "Running alembic upgrade head"
alembic upgrade head
