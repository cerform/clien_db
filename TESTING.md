# Running tests

This repository includes multiple styles of tests:
- Unittest (built-in library) examples
- Pytest-based tests
- Selenium-based UI tests (optional, requires additional dependencies)

## Quick commands

Install dependencies (pytest etc):

```bash
python -m pip install -r requirements.txt
# Optional for selenium tests
python -m pip install selenium webdriver-manager
```

Run pytest for the whole test suite:

```bash
pytest -q
```

Run individual tests:

```bash
pytest -q tests/test_time_utils_pytest.py
```

Run selenium tests (skips if selenium or driver are missing):

```bash
pytest -q -m selenium
```

Notes:
- Selenium tests require a Chrome/Chromium binary and may require driver manager tooling.
- The tests write to a temporary path (tmp_path) and should not affect your repo files.
## RBAC automation

We've added a helper script to create RBAC roles and grant permissions in Postgres for INKA roles.

Use the script as follows (dry-run by default):

```bash
export DATABASE_URL=postgresql://admin:secret@127.0.0.1:5432/tattoo_salon
export RBAC_INKA_LLM_RUNTIME_PASS='secret'
export RBAC_INKA_BOOKING_AGENT_PASS='booking_secret'
python3 scripts/create_rbac_roles.py  # dry-run
python3 scripts/create_rbac_roles.py --apply  # apply to DB
```

Passwords are optional — if omitted the script will not change role passwords (use IAM or secret manager in production).

### Applying SQL migrations

You can execute the SQL migrations under `db/migrations/sql` using the helper script. Dry-run first:

```bash
export DATABASE_URL=postgresql://admin:secret@127.0.0.1:5432/tattoo_salon
python3 scripts/apply_sql_migrations.py  # dry-run
python3 scripts/apply_sql_migrations.py --apply  # actually apply
```

This is a convenience script for simple deployments; for production use a proper migration tool such as Alembic or Flyway.


