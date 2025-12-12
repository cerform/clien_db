#!/bin/bash
set -e

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "No .env found. Copy .env.example to .env and update values." >&2
fi

docker compose up --build
