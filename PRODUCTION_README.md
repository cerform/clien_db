# Production Readiness Checklist

This repository now includes local and CI support to prepare the Admin UI and backend for production deployments.

What was added
- `services/frontend/admin-ui/vite.config.js` — dev proxy for `/api` -> `http://127.0.0.1:8000` (useful for local e2e testing)
- `.github/workflows/playwright.yml` — starts the backend and frontend dev server and runs Playwright e2e tests
- Updated `.github/workflows/build-and-push.yml` to also build and push `admin-ui` Docker image to GHCR
- `services/frontend/admin-ui/README.md` — contains local steps to run Playwright e2e

Local quick start (production-like):

1. Build and push images (requires GHCR token configured in `GHCR_PAT`):

```bash
# build top-level image
docker build -t ghcr.io/<owner>/clien_db:latest .
# build admin-ui image
docker build -t ghcr.io/<owner>/clien_db:admin-ui-latest -f services/frontend/admin-ui/Dockerfile services/frontend/admin-ui
# push images to GHCR
docker push ghcr.io/<owner>/clien_db:latest
docker push ghcr.io/<owner>/clien_db:admin-ui-latest
```

2. Run backend locally (or in a container):

```bash
python -m uvicorn src.web.app:create_app --host 0.0.0.0 --port 8000 --factory
```

3. Serve admin UI (dev server with proxy for `/api`):

```bash
cd services/frontend/admin-ui
npm ci
npm run dev
```

4. Run Playwright tests

```bash
npx playwright install --with-deps
npx playwright test
```

CI notes
- The Playwright workflow will run on pull requests and starts a local backend and dev server (no external infra needed).
- Container builds are handled in `build-and-push.yml` — ensure `GHCR_PAT` secret is configured for pushing images.

If you want, next I can:
- Add a GitHub Action to run Playwright tests inside a matrix over Node + Python versions
- Add tests that run against the built Docker images (integration smoke tests)
- Add release and deployment workflows (Cloud Run or container registry promotion)
