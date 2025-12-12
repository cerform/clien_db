#!/bin/bash
set -e
export PYTHONPATH="/app/src:$PYTHONPATH"
exec python -m src.web.app
