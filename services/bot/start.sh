#!/bin/bash
set -e
export PYTHONPATH="/app/src:$PYTHONPATH"
# For webhook mode, run run_production; for polling mode the repo uses run.py
exec python run_production.py
