# Tattoo Admin UI

This is a lightweight admin UI for the Tattoo project.

Run locally:

```bash
cd services/frontend/admin-ui
npm install
npm run dev
```

Build:

```bash
npm run build
```

Notes:
- Uses `Authorization: Bearer admin_token_1` in requests for local testing (mirrors server's `_is_admin` logic).
- Contains simple client/service pages with edit/delete modal and validation.
- Add Playwright tests in `tests/`.

E2E (Playwright) locally:

```bash
# Start backend (from repo root)
python -m uvicorn src.web.app:create_app --host 127.0.0.1 --port 8000 --factory

# In another shell: start dev frontend with proxy (vite)
cd services/frontend/admin-ui
npm install
npm run dev

# Run Playwright tests
npx playwright install --with-deps
npx playwright test
```
