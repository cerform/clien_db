# DB Manager (PoC)

This document describes the Proof-of-Concept DB Manager and how to use it in the admin UI.

## Overview

A lightweight DB Manager UI has been added to the admin interface (`/admin/db-manager`) to allow admins to:

- List Postgres tables in the `public` schema
- Load a table (paginated) and view rows in a Tabulator table (read-only PoC)
- Export table data to CSV (client-side via Tabulator)

Backend endpoints (admin only):

- `GET /api/db/tables` — list tables
- `GET /api/db/table/{table_name}?limit=..&offset=..` — fetch rows (paginated)

These endpoints are protected by the existing admin token / RBAC system. Use `Authorization: Bearer admin_token_<id>` in requests (Test mode) or provide a valid admin token.

## Security

- The DB Manager is restricted to admins via `_is_admin(request)` which checks:
  - `Authorization: Bearer admin_token_<id>` tokens
  - runtime admin lookup via `src.services.admin_manager.is_admin`
  - `ADMIN_IDS` or config admin IDs

- This PoC does not provide a SQL runner or write/delete operations on Postgres; it is intentionally read-only to reduce risk. Additional actions must be gated by stricter RBAC and auditing.

## Local testing

1. Ensure your environment has a reachable Postgres (via `DATABASE_URL` or `CLOUDSQL_*` env vars). For local tests, you can run a Postgres container and set `DATABASE_URL` accordingly.
2. Start the app: `python run.py` or use the project's normal dev startup.
3. Open the Admin UI and navigate to `DB Manager` — refresh the table list and load a table to view rows.

## Future work

- Add server-side export (streaming CSV)
- Add safe write operations with audit/logging
- Add a pagination UI and column type formatting
- Optionally implement a full SPA management UI or integrate an external tool (pgweb/pgAdmin) for full DB administration

