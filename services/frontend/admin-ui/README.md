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
