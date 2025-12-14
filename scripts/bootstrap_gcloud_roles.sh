#!/usr/bin/env bash
set -euo pipefail

# Simple GCloud bootstrap script to enable APIs, create service accounts (if needed),
# and grant roles required for Cloud Run + Cloud SQL + Secret Manager + Cloud Build.
# Usage: ./scripts/bootstrap_gcloud_roles.sh <PROJECT_ID> [--skip-create-sa]

PROJECT_ID=${1:-}
SKIP_CREATE_SA=false
if [ "${2:-}" == "--skip-create-sa" ]; then
  SKIP_CREATE_SA=true
fi

if [ -z "$PROJECT_ID" ]; then
  echo "Usage: $0 <PROJECT_ID> [--skip-create-sa]"
  exit 1
fi

# Required APIs
APIS=(
  run.googleapis.com
  cloudbuild.googleapis.com
  sqladmin.googleapis.com
  secretmanager.googleapis.com
  iam.googleapis.com
  container.googleapis.com
  artifactregistry.googleapis.com
)

# Default service accounts expected by this repo. These will be created by Terraform normally.
BOT_SA=${BOT_SA:-"${PROJECT_ID}@appspot.gserviceaccount.com"}
BACKEND_SA=${BACKEND_SA:-"${PROJECT_ID}@appspot.gserviceaccount.com"}
AI_SA=${AI_SA:-"${PROJECT_ID}@appspot.gserviceaccount.com"}
FRONTEND_SA=${FRONTEND_SA:-"${PROJECT_ID}@appspot.gserviceaccount.com"}
CLOUDRUN_SA=${CLOUDRUN_SA:-"${PROJECT_ID}@appspot.gserviceaccount.com"}

# Custom SAs used by scripts
TELEGRAM_SA=${TELEGRAM_SA:-"telegram-bot-sa@${PROJECT_ID}.iam.gserviceaccount.com"}
JENKINS_SA=${JENKINS_SA:-"${PROJECT_ID}-jenkins-sa@${PROJECT_ID}.iam.gserviceaccount.com"}

# List of roles to grant to each SA
COMMON_ROLES=(
  roles/secretmanager.secretAccessor
  roles/cloudsql.client
)

RUN_ROLES=(
  roles/run.invoker
  roles/run.admin
)

BUILD_ROLES=(
  roles/cloudbuild.builds.editor
)

GKE_ROLES=(
  roles/container.admin
)

IAM_ROLES=(
  roles/iam.serviceAccountUser
  roles/iam.serviceAccountAdmin
)

# Helper: enable APIs
enable_apis() {
  for api in "${APIS[@]}"; do
    echo "Enabling API: $api"
    gcloud services enable "$api" --project="$PROJECT_ID" || echo "Failed enabling $api (you may not have permission)"
  done
}

# Helper: ensure service account exists
ensure_service_account() {
  local sa_email=$1
  if gcloud iam service-accounts describe "$sa_email" --project="$PROJECT_ID" &> /dev/null; then
    echo "Service account $sa_email exists"
  else
    echo "Service account $sa_email not found; creating..."
    # Create with friendly account id
    local sa_name
    sa_name=$(echo "$sa_email" | cut -d'@' -f1)
    gcloud iam service-accounts create "$sa_name" --display-name="$sa_name" --project="$PROJECT_ID" || true
  fi
}

# Helper: grant roles
grant_roles() {
  local sa=$1
  shift
  for r in "$@"; do
    echo "Granting role $r to $sa"
    if ! gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$sa" --role="$r" --quiet; then
      echo "Failed to grant $r to $sa (maybe insufficient permissions)"
    fi
  done
}

# Create DB user and DB if Cloud SQL instance exists
create_db_resources() {
  INSTANCE_NAME=${DB_INSTANCE_NAME:-"tattoo-db"}
  DB_USER=${DB_USER:-"tattoo_user"}
  DB_PASS=${DB_PASS:-"$CLOUDSQL_PASSWORD"}
  DB_NAME=${DB_NAME:-"tattoo_salon"}

  echo "Checking Cloud SQL instance: $INSTANCE_NAME"
  if gcloud sql instances describe "$INSTANCE_NAME" --project="$PROJECT_ID" &> /dev/null; then
    echo "Instance $INSTANCE_NAME exists"
    echo "Creating DB if missing..."
    if ! gcloud sql databases describe "$DB_NAME" --instance="$INSTANCE_NAME" --project="$PROJECT_ID" &> /dev/null; then
      echo "Creating database $DB_NAME"
      gcloud sql databases create "$DB_NAME" --instance="$INSTANCE_NAME" --project="$PROJECT_ID" || true
    else
      echo "Database $DB_NAME already exists"
    fi
    echo "Creating DB user if missing..."
    if ! gcloud sql users list --instance="$INSTANCE_NAME" --project="$PROJECT_ID" | grep -q "$DB_USER"; then
      echo "Creating user $DB_USER"
      gcloud sql users create "$DB_USER" --instance "$INSTANCE_NAME" --password="$DB_PASS" --project="$PROJECT_ID" || true
    else
      echo "User $DB_USER already exists"
    fi
  else
    echo "Cloud SQL instance $INSTANCE_NAME not found; skipping DB creation (create via Terraform / console)"
  fi
}

# Main
main() {
  echo "Bootstrapping GCP project: $PROJECT_ID"
  enable_apis

  if [ "$SKIP_CREATE_SA" = false ]; then
    ensure_service_account "$TELEGRAM_SA"
    ensure_service_account "$JENKINS_SA"
    # TODO: service accounts from terraform will be created by terraform, so ensure only generic ones
  fi

  # Grant common roles to main service accounts
  for sa in "$TELEGRAM_SA" "$CLOUDRUN_SA"; do
    grant_roles "$sa" "${COMMON_ROLES[@]}"
  done

  # Grant additional roles
  grant_roles "$JENKINS_SA" "${GKE_ROLES[@]}" "${IAM_ROLES[@]}" "${BUILD_ROLES[@]}"

  # Make sure the bootstrap user has permissions too
  ACTIVE_ACCOUNT=$(gcloud config get-value account 2>/dev/null || true)
  if [ -n "$ACTIVE_ACCOUNT" ]; then
    echo "Granting roles to active account $ACTIVE_ACCOUNT for convenience"
    for r in "roles/owner" "roles/iam.serviceAccountAdmin" "roles/iam.serviceAccountUser"; do
      echo "Granting $r to $ACTIVE_ACCOUNT"
      gcloud projects add-iam-policy-binding $PROJECT_ID --member="user:$ACTIVE_ACCOUNT" --role="$r" --quiet || echo "Failed to give $r to $ACTIVE_ACCOUNT"
    done
  fi

  # Create DB resources if possible
  create_db_resources

  echo "Bootstrap complete — please review outputs and any failures above. If you lack permissions, please run this with an account having OWNER or IAM Admin role."
}

main "$@"
