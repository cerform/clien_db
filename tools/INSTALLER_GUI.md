# Installer GUI (Tkinter)

This is a small Tkinter-based GUI helper to set up secrets and deploy the `tattoo-bot` Cloud Run service.

Features
- Create/add secret versions in Secret Manager
- Grant Secret Accessor role to the Cloud Run service account
- Update Cloud Run service to use the secret (via `--set-secrets`)
- Optionally deploy a new image to Cloud Run
- Logs shown in the GUI

Security & usage
- This tool runs locally and executes `gcloud` commands — it does not store secrets in the repository.
- Do not paste secrets into chats or public places. Prefer loading the token from a local file.
- You must have `gcloud` CLI installed and be authenticated with the intended project.

Run

1. Activate your Python environment (optional):

```bash
source .eco/bin/activate
```

2. Run the GUI:

```bash
python tools/installer_tk.py
```

3. Fill fields:
- GCP Project ID
- Cloud Run service name (default: `tattoo-bot`)
- Region (e.g. `europe-west1`)
- Secret name (default: `TELEGRAM_BOT_TOKEN`)
- Token (or press **Load token from file**)
- (Optional) Image to deploy

4. Use buttons in order: **Create/Add secret**, **Grant secret access to service SA**, **Set secret & deploy service**.

Advanced / Heads-up
- The GUI shells out to `gcloud` commands. You can run the same commands manually (see script for examples).
- If you prefer a headless installer, we can add a CLI wrapper and dry-run + rollback options.

Security note: this tool simplifies repetitive steps for convenience. For production, consider implementing additional auditing, secure storage of inputs, and CI-based secrets management.
