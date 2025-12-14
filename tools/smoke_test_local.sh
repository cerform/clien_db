#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

echo "Building API stub image..."
docker build -t clien_api_stub:smoke ./tools/api_stub

echo "Building admin-ui image..."
docker build -t clien_admin_ui:smoke ./services/frontend/admin-ui

echo "Creating docker network 'smoke_net'..."
docker rm -f smoke_admin smoke_api || true
docker network rm smoke_net || true
docker network create smoke_net || true

echo "Starting api stub..."
docker run -d --name smoke_api --network smoke_net clien_api_stub:smoke

echo "Starting admin-ui (nginx) with custom conf..."
# Run admin-ui nginx image and mount our nginx config
docker run -d --name smoke_admin --network smoke_net -p 8081:80 \
  -v "$ROOT/tools/nginx/default.conf":/etc/nginx/conf.d/default.conf \
  clien_admin_ui:smoke

echo "Waiting for services to be ready..."
sleep 3

echo "Run Playwright tests (installing deps)..."
pushd services/frontend/admin-ui
npm install --no-audit --no-fund --silent
npx playwright install --with-deps
npx playwright test --config=playwright.config.js --project=chromium --reporter=list --workers=1 || {
  echo "Playwright tests failed"; popd; exit 2
}
popd

echo "Smoke tests succeeded"

echo "Cleaning up..."
docker rm -f smoke_admin smoke_api || true
docker network rm smoke_net || true
