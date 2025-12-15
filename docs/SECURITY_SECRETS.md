# Security & Secrets Remediation Guide 🔒

This document describes immediate steps to bring secrets to production-grade hygiene: remove secrets from git, rotate secrets that may have been exposed, and import them into Google Secret Manager. Follow these steps carefully in order.

## 1) Identify secrets in the repo
- `.env` in the repository contains secrets. Use `git grep` to find other occurrences:

```bash
git grep -n "TELEGRAM_BOT_TOKEN\|OPENAI_API_KEY\|CLOUDSQL_PASSWORD\|BOT_TOKEN\|SPREADSHEET_ID"
```

## 2) Replace secrets in tracked files
- Replace real values in `.env` with placeholders (done). Commit the change.

## 3) Rotate any credentials that were committed
- Telegram Bot token: create a new token in @BotFather and update Secret Manager.
- OpenAI API key: revoke and create a new key in your OpenAI dashboard.
- Google Sheets service account / credentials: rotate keys if these were committed.

## 4) Import secrets into Google Secret Manager
Run the helper script `scripts/import_env_to_secrets.sh` (or follow the commands below) from a secure workstation that has `gcloud` configured with appropriate permissions.

Example manual steps:

```bash
# Create secret (if not exists)
gcloud secrets create BOT_TOKEN --data-file=- <<'EOF'
"the-bot-token-from-botfather"
EOF

# Add new version (if secret exists)
gcloud secrets versions add BOT_TOKEN --data-file=<(echo -n "the-bot-token-from-botfather")

# Grant access to service account
gcloud secrets add-iam-policy-binding BOT_TOKEN \
  --member="serviceAccount:inka-sa@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## 5) Update Cloud Run and CI to use Secret Manager references
- Use `--set-secrets` in `gcloud run deploy` or configure secret environment variables in your CI (Cloud Build / GitHub Actions) to point to `projects/$PROJECT/secrets/NAME:latest`.

## 6) Purge secrets from git history (if previously committed)
- If a secret was committed, follow these steps once the secret is rotated:

Option A (recommended): Use `git filter-repo` (faster & safer than git-filter-branch)

```bash
# Install: pip install git-filter-repo
git clone --mirror <repo-url> repo.git
cd repo.git
git filter-repo --path .env --invert-paths
git push --force --mirror
```

Option B: BFG Repo Cleaner

Important: rewriting history is disruptive. Coordinate with the team and prefer rotation of secrets first.

## 7) Prevent future leaks
- Enable the repository's pre-commit hooks (`git config core.hooksPath .githooks`) or install a pre-commit hook.
- Consider adding `git-secrets` or `detect-secrets` to CI to block pushes with secrets.

## 8) Verification
- After importing secrets to Secret Manager, verify that Cloud Run revisions use the secrets and that the running container has no hard-coded values.
- Validate by running smoke checks and by checking that logs no longer contain tokens.

---
If you'd like, I can: (A) run the `scripts/import_env_to_secrets.sh` (requires `gcloud` and permission), and/or (B) purge `.env` from the git history (I will coordinate and prepare instructions and PRs). Tell me which to do next.
