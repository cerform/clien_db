# Database Admin UI & Admin Sync

This document explains the newly added Database Admin UI and the Admin Sync utility.

## DB Admin UI

URL: `/admin/db` (requires admin access)

Features:
- Browse sheets (`clients`, `masters`, `services`, `bookings`, `config`, `conversations`, `calendar`)
- Inline editing of rows (cell editing updates the sheet)
- Add new row, delete row
- Sync admins from Cloud SQL into `config` → `ADMIN_USER_IDS`

The UI uses Tabulator (CDN) for a modern, editable table experience. It calls the following API endpoints:
- `GET /api/admin/db/{sheet}` - list rows
- `PUT /api/admin/db/{sheet}/{row_id}` - update row
- `POST /api/admin/db/{sheet}` - append row
- `DELETE /api/admin/db/{sheet}/{row_id}` - delete row
- `POST /api/admin/sync-admins` - trigger admin sync from Cloud SQL

## Admin Sync

CLI: `python3 scripts/sync_admins.py --id <SPREADSHEET_ID> [--dry-run]`

Behavior:
- Tries to fetch admin telegram IDs from Cloud SQL (defaults to a few fallback queries).
- If SQL yields no results, it falls back to reading `masters` sheet and looks for rows where the `role` column contains `admin`.
- Writes a CSV string into `config` sheet as `ADMIN_USER_IDS` key.

Customization:
- If your DB schema differs, set `ADMIN_SYNC_SQL` env var to a SQL query that returns a column `telegram_id`.

Scheduling:
- You can schedule admin sync using Cloud Scheduler/Cron by invoking `scripts/cron_sync_admins.sh` with `SPREADSHEET_ID` env var set.
- Alternatively, call the webhook endpoint `POST /api/admin/sync-admins` (requires admin auth) from your deployment hooks after DB updates.
