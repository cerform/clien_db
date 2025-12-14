# Data Migration and Security Guide

This document covers recommended steps for backing up and migrating data and best practices for secure deployments.

## Backing up Postgres

Local (Docker) Postgres:
```bash
docker exec -t clien_db_postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql
```

Restore:
```bash
cat backup.sql | docker exec -i clien_db_postgres psql -U $POSTGRES_USER $POSTGRES_DB
```

Cloud SQL (GCP): Use automated backups or `gcloud`:
```bash
gcloud sql export sql <INSTANCE> gs://<BUCKET>/export.sql --database=<DB>
```

## Backing up Google Sheets
- The app stores primary data in Google Sheets. To export, open the Sheet and `File -> Download -> Microsoft Excel (.xlsx)`.
- For automated backup, you can use the Google API to export or copy the spreadsheet programmatically.

## Migration steps (High level)
1. Backup PostgreSQL (if present) and export sheet(s).
2. On the destination environment, restore the DB and import the spreadsheet data.
3. Update `.env` or Secret Manager with new credentials (BOT_TOKEN, SPREADSHEET_ID, DB credentials)
4. Redeploy and validate the deployment by checking logs and running `create_google_sheets_structure.py` only if needed.

## Secret management
- Never store secrets directly in Git. Use `.env` only locally and keep out of version control.
- For production, use cloud-native secrets manager:
  - GCP Secret Manager + Cloud Run: `gcloud secrets create` + `--set-secrets` during deploy
  - AWS: Secrets Manager
- If using Docker Swarm, use Docker secrets.

## Rotating secrets
- Rotate bot tokens, DB passwords and API keys regularly.
- Update your `.env`/secret store and trigger a rolling deploy.

## Sensitive configuration check-list
- Ensure `.env` is in `.gitignore`.
- `credentials.json` for Google must be stored securely; consider server secrets rather than file.
- Audit logs for cloud projects and enable access controls.
- Use HTTPS with valid TLS certs in production.

## Database access and firewall
- For cloud DBs, restrict CIDR ranges or use private connections.
- Avoid public IPs for production DB; use private connectivity or cloud proxy.

## Extra notes — migrating google data
- Google Sheets are not transactional. For large datasets, consider migrating to real DB to avoid race conditions.
- Export all tabs as CSV and import into Postgres tables as part of migration.

## Rollback plan
- Keep a cloud snapshot or DB dump before major changes.
- Test restoration in a staging environment before production migration.

## Example: Migrating to Cloud SQL from local Docker Postgres
- Export local DB:
  - `docker exec -t clien_db_postgres pg_dump -U postgres admin_messages > admin_messages.sql`
- Transfer `admin_messages.sql` to Cloud Storage and import to Cloud SQL:
  - `gcloud sql import sql <INSTANCE> gs://<BUCKET>/admin_messages.sql --database=admin_messages`
- Update `CLOUDSQL_CONNECTION_NAME` and credentials in `.env` or Cloud Run Secrets and deploy.
