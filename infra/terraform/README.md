# Terraform for Cloud Run + Cloud SQL (Postgres) for Tattoo Bot

This folder contains a minimal Terraform skeleton to provision the core infrastructure for the microservices deployment: Cloud SQL (Postgres), Secret Manager secrets, Cloud Run services, and service accounts.

This skeleton is intentionally minimal — it focuses on core considerations and can be extended with networking, domain records, GKE, or a production-ready setup.

IMPORTANT: Do not store secrets in your Terraform files. Use variables and Secret Manager for secret values.

Quickstart
----------
1) Set up gcloud auth and project:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

2) Initialize Terraform

```bash
cd infra/terraform
terraform init
terraform plan -var='project_id=YOUR_PROJECT_ID' -var='region=us-central1'
terraform apply -var='project_id=YOUR_PROJECT_ID' -var='region=us-central1'
```

3) After apply, Terraform prints outputs with Service URLs and Cloud SQL connection name.

Customization
-------------
- Provide your images for each service via variables (images are set by CI/Cloud Build).
- Create secrets in Google Secret Manager, then update Terraform variables to reference them or let Terraform create them (do not check in secret values).

Cloud Build triggers
--------------------
To enable Cloud Build triggers, create a GitHub App / connection in GCP and provide Terraform with the `repo_owner`, `repo_name`, and `repo_branch` variables. Cloud Build triggers are created by Terraform and will watch for pushes to the configured branch and run the corresponding `infra/terraform/cloudbuild/*.yaml` pipeline.

You must configure the GCP Cloud Build GitHub App integration or use a Cloud Source Repo and change the triggers accordingly. The Terraform GitHub triggers require a repo connection configured in GCP.

Extending for production
------------------------
- Add VPC connector, private IPs for Cloud SQL, and Cloud Armor.
- Add IAM restrictions and log sinks for central auditing.
- Add Terraform modules for each service so they can be reused by other projects.

Security
--------
- Least-privilege: scope service account permissions only to what they need (Secret Manager access + Cloud SQL client where needed).
- Keep secrets in Secret Manager only, rotate keys regularly.
# Jenkins & Workload Identity
---------------------------
This repo includes an optional Jenkins installation on GKE via Terraform+Helm.

Steps to enable Jenkins with GitHub OAuth and Workload Identity:

1. Create GitHub OAuth App in your GitHub Organization to use for Jenkins SSO. Set the callback URL to your Jenkins URL after a LoadBalancer IP or domain (e.g., https://jenkins.yourdomain.com/securityRealm/finishLogin).
2. Add `jenkins_github_oauth_client_id` and `jenkins_github_oauth_client_secret` to Terraform variables or make them available in CI. The terraform module will populate a Kubernetes secret `github-oauth` in the `jenkins` namespace and Jenkins will use this for OAuth.
3. After Jenkins is deployed, configure GitHub OAuth in Jenkins if not already configured via JCasC.
4. For GCP permissions, we create a GCP service account (`${var.env_prefix}-jenkins-sa`) and grant roles: `roles/secretmanager.secretAccessor`, `roles/run.admin`, `roles/iam.serviceAccountUser`, `roles/cloudsql.client`. Use least privilege: reduce roles as needed.

Workload Identity:
- The Terraform module configures a Kubernetes service account `jenkins` in namespace `jenkins` annotated with `iam.gke.io/gcp-service-account` linking to the GCP service account. This way Jenkins can access GCP resources without using service account keys.

Credentials and Secrets
----------------------
- Jenkins needs a GitHub token to seed jobs and to set up webhooks; add it to the `github-token` Kubernetes secret or configure Jenkins credentials via the UI.
- For secret management, prefer to create secrets in Secret Manager and grant the Jenkins GSA `roles/secretmanager.secretAccessor` so Jenkins can fetch secrets dynamically.

# Terraform setup for Tattoo Bot

This Terraform configuration sets up the basic infrastructure for Tattoo Bot on Google Cloud:
- Enables necessary APIs
- Creates a Cloud SQL Postgres instance and database
- Creates a service account for Cloud Run and grants Cloud SQL/Secret access
- Deploys a Cloud Run service using a provided container image

Usage:

1. Install terraform (v1.3+ recommended)
2. Initialize terraform in `infra/terraform`

```bash
cd infra/terraform
terraform init
```

3. Supply variables via `terraform.tfvars` or environment variables. At minimum set:

terraform.tfvars example:

```hcl
project = "tattoo-480007"
image   = "gcr.io/tattoo-480007/tattoo-bot:latest"
db_user_password = "<strong_password>"
```

4. Run `terraform apply` and confirm.

Notes:
- This terraform creates a `google_secret_manager_secret` resource for `BOT_TOKEN`, but does not set versions with actual values. Consider setting secret versions outside terraform using `gcloud secrets versions add` for security.
- For more advanced infra (VPC peering, private IP, replica), extend `google_sql_database_instance` settings.
