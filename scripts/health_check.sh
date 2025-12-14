#!/bin/bash
set -euo pipefail

# Usage: ./scripts/health_check.sh <service_url>
SERVICE_URL=${1:-http://localhost:8080}
echo "Checking health for ${SERVICE_URL}"
resp=$(curl -s -w "\n%{http_code}" -X GET "${SERVICE_URL}/api/health")
body=$(echo "$resp" | sed -n '1,$p' | head -n -1)
code=$(echo "$resp" | tail -n1)
echo "HTTP status: ${code}"
echo "Body: ${body}"
if [ "$code" -ne 200 ]; then
    echo "Health check failed"
    exit 1
fi
echo "Health check OK"
