# Scripts

Useful repository scripts for DB seeding and migrations.

## Seeding services

To seed or update the tattoo services catalog in the database run:

```bash
# Use DATABASE_URL or Cloud SQL client environment
python3 scripts/seed_services.py
```

The script performs an idempotent upsert by service name (update when present, insert otherwise). It is safe to run multiple times.
