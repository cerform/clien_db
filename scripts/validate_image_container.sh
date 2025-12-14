#!/usr/bin/env bash
set -euo pipefail

# Run a smoke test for the built image. Usage:
#   ./scripts/validate_image_container.sh <image> [port] [health_endpoint]

IMAGE=${1:-}
PORT=${2:-8080}
HEALTH_PATH=${3:-/api/health}

if [ -z "$IMAGE" ]; then
  echo "Usage: $0 <image> [port] [health_endpoint]"; exit 2
fi

CONTAINER_NAME=smoke_test_$(date +%s)

echo "Running container ${IMAGE} as ${CONTAINER_NAME} (port ${PORT})"
docker run -d --name ${CONTAINER_NAME} -p ${PORT}:${PORT} -e PORT=${PORT} -e BOT_MODE=inka ${IMAGE}

echo "Waiting for health endpoint ${HEALTH_PATH}..."
for i in {1..30}; do
  if curl -sS --fail http://localhost:${PORT}${HEALTH_PATH}; then
    echo "Health OK"; break
  fi
  sleep 1
done

if ! curl -sS --fail http://localhost:${PORT}${HEALTH_PATH}; then
  echo "Health check failed"; docker rm -f ${CONTAINER_NAME} || true; exit 1
fi

echo "Stopping container..."
docker rm -f ${CONTAINER_NAME}

echo "Container validation succeeded"
