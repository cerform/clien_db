# Migration plan: Google Sheets -> Cloud SQL (Postgres)

Goal: Move operational storage from Google Sheets to Cloud SQL (Postgres recommended) with minimal service interruption.

High-level plan
1. Add SQL models & client in the codebase (done: `src/db/sql_models.py`, `src/db/sql_client.py`).
2. Create a migration script that reads current sheets and inserts to SQL (done: `scripts/migrate_sheets_to_cloudsql.py`).
3. Validate migrated data in a staging DB.
4. Swap production config to use Cloud SQL (change `DATABASE_URL`) and perform smoke tests.
5. Switch production to use SQL database in the app and adapt any remaining sheet operations to write to both (write-through) for a transition window.
6. Remove write paths to Sheets and keep a small set of read-only fallback paths for legacy data.
7. Update docs and add backup & restore processes (daily SQL dumps + backup of Sheets export).

Quick developer checklist
- Install dependencies: `pip install -r requirements.txt`
- Run a local Postgres (e.g., Docker):
  ```bash
  docker run --rm -e POSTGRES_PASSWORD=pass -e POSTGRES_USER=pguser -e POSTGRES_DB=clien_db -p 5432:5432 postgres:15
  export DATABASE_URL=postgresql+psycopg2://pguser:pass@localhost:5432/clien_db
  ```
- Dry-run migration:
  ```bash
  python scripts/migrate_sheets_to_cloudsql.py
  ```
- Apply migration (confirm):
  ```bash
  python scripts/migrate_sheets_to_cloudsql.py --confirm
  ```

Recommended follow-ups
- Add Alembic to manage schema changes and provide an initial migration script.
- Replace `DatabaseManager` reference across the codebase with an adapter or join both backends via a thin abstraction so the app can be switched between providers without code changes.
- Add CI job that runs migration scripts against a test DB for regression testing.
- Add monitoring to Cloud SQL (connectivity, slow queries) and auditing.

Alembic & Running Migrations
1. Ensure `DATABASE_URL` is set (e.g., for local Docker Postgres):
  ```bash
  export DATABASE_URL=postgresql+psycopg2://pguser:pass@localhost:5432/clien_db
  ```
2. Run Alembic upgrade head to create initial schema from models:
  ```bash
  ./scripts/run_alembic_upgrade.sh
  ```
3. For subsequent schema changes, generate an Alembic revision and run autogenerate:
  ```bash
  alembic revision --autogenerate -m "Add new column"
  alembic upgrade head
  ```

E2E Playwright Tests
- Install Playwright and browsers: `pip install -r requirements.txt && playwright install`
- Run Playwright E2E tests (may be slow): `pytest -q tests/e2e -m slow`

