# Deploying to Google Cloud Run from a branch

This document describes how to build a container image and deploy to Google Cloud Run from a feature branch. It's safe to run locally for manual deployments, and typical CI uses the workflow in `.github/workflows/deploy-cloud-run.yml`.

Requirements
- Google Cloud SDK (`gcloud`) installed and authenticated
- A Google Cloud project and permission to deploy Cloud Run services
- A service account JSON key (for GitHub Actions: store as `GCLOUD_SA_KEY` secret)
- The GitHub Actions workflow expects the following secrets to be set:
  - `GCLOUD_PROJECT_ID` - your GCP project ID
  - `GCLOUD_SA_KEY` - base64-encoded service account key JSON
  - `GCLOUD_REGION` - e.g., `us-central1` (optional)

Manual Deployment (local)
1. Set environment variables
   ```bash
   export PROJECT_ID=my-gcp-project
   export REGION=us-central1
   export IMAGE_TAG=$(git rev-parse --short HEAD)
   ```
2. Build & deploy with script:
   ```bash
   ./scripts/deploy_cloud_run.sh tattoo-admin $IMAGE_TAG
   ```

Using GitHub Actions
- Push to a branch matching `new-migration/*` to trigger the workflow `deploy-cloud-run.yml`.
- The workflow builds the image with Cloud Build and deploys to Cloud Run using the `gcloud` action.

Note on Production Safety
- Consider creating a `staging` service for testing/validation before replacing the production service.
- Add a traffic-splitting or blue-green deployment strategy if necessary.
