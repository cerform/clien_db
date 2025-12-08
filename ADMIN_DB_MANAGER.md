# DB Manager - Admin Panel

This page implements a DB Manager UI with bulk and per-sheet management tools.

## Features
- List sheets (tabs) in the Google Spreadsheet
- Export sheet to JSON (headers & rows)
- Import JSON or array of objects into a sheet (append/replace)
- Backup entire DB (all sheets) as JSON
- Restore DB from JSON backup (replace mode)
- Audit logs saved to `Admin_Audit_Log` sheet

## Pages & API
- UI: `/admin/db-manager` - simple dashboard to perform exports/imports, backup/restore and view audit logs
- API endpoints:
  - GET `/api/sheets` → List sheet names
  - GET `/api/sheets/{sheet_name}` → Export sheet content (JSON)
  - POST `/api/sheets/{sheet_name}/import` → Import rows (append|replace) with body {rows, mode, admin_id}
  - GET `/api/db/backup` → Create and download JSON backup of all sheets
  - POST `/api/db/restore` → Restore DB from JSON backup {backup, mode, admin_id}
  - GET `/api/audit/logs` → List audit logs
  - POST `/api/audit/logs` → Append audit log {admin_id, action, sheet, details}

## Notes & Safety
- APIs are not fully authenticated; in web UI we pass `admin_id` (from the login token) to audit logs.
- Restoring the DB will replace sheet contents — use with caution and ideally test in staging.
- Import/Export support JSON only; CSV support can be added if needed.

## Implementation
- Backend changes in `src/services/admin_db_manager.py` (sheet management, audit)
- New API endpoints in `src/web/api/routers.py` for sheet operations and audit
- New UI page `src/web/pages.py` at `/admin/db-manager` to operate on sheets
- Added a card on the main dashboard in `src/web/app.py` for quick access

## CI / Automated Deployment
A GitHub Actions workflow (.github/workflows/deploy-cloud-run.yml) is included that can automatically deploy this repo to Google Cloud Run after successful tests.

Required GitHub Secrets:
- `GCP_PROJECT` — GCP project id
- `GCP_SA_KEY` — Service Account JSON

The workflow runs tests, deploys to Cloud Run, and does a basic /api/health check after deploy.

## Recommendations
- Add admin authentication checks for API endpoints to prevent unauthorized usage.
- Add CSV import/export and validation for large sheets.
- Add quota/size checks for backup/restore operations and better progress UI.
- Add unit/integration tests for import/export/backup endpoints.
