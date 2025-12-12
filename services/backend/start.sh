#!/bin/bash
set -e
export PYTHONPATH="/app/src:$PYTHONPATH"
exec uvicorn src.web.app:create_app --host 0.0.0.0 --port 8080 --loop auto
