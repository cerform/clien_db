# Cloud Run and Cloud SQL Setup (GCP)

These instructions explain how to configure Google Cloud Platform (GCP) to run this bot in production using Cloud Run and Cloud SQL.

1. Create or pick a project in the Google Cloud Console.
2. Enable APIs:
   - Cloud Run
   - Cloud SQL Admin
   - Google Sheets API
   - Google Calendar API
   - (Optional) Secret Manager, IAM API

3. Create a Cloud SQL Postgres instance:
   a. In Cloud SQL > Create instance > PostgreSQL.
   b. Choose version (13+), set a password, and note the connection name: `<PROJECT>:<REGION>:<INSTANCE>`.
   c. For CI/CD or Cloud Build, you might want to allow a user to connect via Cloud SQL Proxy.

4. Create a service account for Cloud Run and grant access to Cloud SQL.
   - Add roles/cloudsql.client and Roles for required resources

5. Create OAuth credentials for Google APIs:
   - Console > APIs & Services > Credentials > Create Credentials > OAuth client ID
   - Choose 'Desktop' (for local) or 'Web application' for server-side.
   - Download `credentials.json` and save in your repo root (or an accessible path).

6. Update `.env` or Secret Manager:
   - `CLOUDSQL_CONNECTION_NAME` to the connection name
   - Set `CLOUDSQL_USER`, `CLOUDSQL_PASSWORD` and `CLOUDSQL_DB` accordingly
   - Add `GOOGLE_CREDENTIALS_PATH` with path to `credentials.json`
   - `BOT_TOKEN`, `OPENAI_API_KEY`, `GOOGLE_CREDENTIALS_PATH`, `SPREADSHEET_ID`

7. Deploy to Cloud Run (Quick):
    - Build and push docker image:
       ```bash
       gcloud builds submit --tag gcr.io/$PROJECT_ID/tattoo-bot
       ```
    - Deploy to Europe (example `europe-west1`):
       ```bash
       gcloud run deploy tattoo-bot \
             --image gcr.io/$PROJECT_ID/tattoo-bot \
             --platform managed \
             --region europe-west1 \
             --set-env-vars ENV=production,SPREADSHEET_ID=<id>,BOT_TOKEN=<token>,CLOUDSQL_CONNECTION_NAME=<conn>
       ```
    - Or use the provided automation script for EU:
       ```bash
       bash setup/deploy_cloudrun_europe.sh PROJECT_ID europe-west1 tattoo-bot your-cloudsql-instance
       ```

For more advanced deployments, see `deploy_cloudrun.sh` and `cloudbuild.yaml` in the project.
