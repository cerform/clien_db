# Getting and Storing Secrets

This file explains where to get the secrets required by Tattoo Bot and how to store them safely using Google Secret Manager.

## Telegram Bot token

1. Open Telegram and send a message to @BotFather.
2. Use the command: `/newbot` and follow the prompts to create a bot. BotFather returns a token in the form:`123456789:AbCdEfGh...`.
3. Save this token as `BOT_TOKEN` in Secret Manager:

```bash
echo -n "<YOUR_BOT_TOKEN>" | gcloud secrets create BOT_TOKEN --replication-policy="automatic" --data-file=-
```

## OpenAI API Key

1. Go to https://platform.openai.com/account/api-keys and create a new API key.
2. Store it as `OPENAI_API_KEY` in Secret Manager:

```bash
echo -n "sk-..." | gcloud secrets create OPENAI_API_KEY --replication-policy="automatic" --data-file=-
```

## Cloud SQL credentials

1. Create your database user password manually or with openssl:

```bash
DB_PASSWORD="$(openssl rand -base64 24)"
```

2. Create a DB user for Postgres and store the password:

```bash
gcloud sql users create tattoo_user --instance=tattoo-db --password="$DB_PASSWORD"
echo -n "$DB_PASSWORD" | gcloud secrets create CLOUDSQL_PASSWORD --replication-policy="automatic" --data-file=-
```

3. Optionally create a `DATABASE_URL` secret to allow `init_postgres` to auto-run schema creation on Cloud Run:

```bash
DATABASE_URL="postgresql+psycopg2://tattoo_user:${DB_PASSWORD}@/tattoo_salon?host=/cloudsql/tattoo-480007:us-central1:tattoo-db"
echo -n "$DATABASE_URL" | gcloud secrets create DATABASE_URL --replication-policy="automatic" --data-file=-
```

## Admin user ids

Set `ADMIN_USER_IDS` env var to a comma-separated list of your Telegram numeric IDs. For example:

```bash
ADMIN_USER_IDS=438407739,457343487
```

## Important Security Tips

- Never commit secrets into source control. Always use Secret Manager or env vars that are not in the repo.
- Restrict service accounts with least privilege required to access these resources.
- Rotate keys periodically.
