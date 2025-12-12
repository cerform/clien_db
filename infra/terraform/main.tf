locals {
  project_id = var.project_id
  name_prefix = var.env_prefix
}

resource "google_project_service" "enable_run" {
  project = local.project_id
  service = "run.googleapis.com"
}

resource "google_project_service" "enable_sql" {
  project = local.project_id
  service = "sqladmin.googleapis.com"
}

resource "google_project_service" "enable_secret" {
  project = local.project_id
  service = "secretmanager.googleapis.com"
}

resource "google_sql_database_instance" "postgres" {
  name             = "${local.name_prefix}-db"
  database_version = "POSTGRES_15"
  region           = var.region
  settings {
    tier = var.db_tier
    ip_configuration {
      # Allow private network or public ip as needed.
      # Use private_ip for production if you configure VPC and peering.
      ipv4_enabled = true
    }
  }
}

resource "google_sql_database" "app_db" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = var.initial_db_password
}

resource "google_service_account" "backend_sa" {
  account_id   = "${local.name_prefix}-backend-sa"
  display_name = "Backend service account"
}

resource "google_service_account" "bot_sa" {
  account_id   = "${local.name_prefix}-bot-sa"
  display_name = "Bot service account"
}

resource "google_service_account" "ai_sa" {
  account_id   = "${local.name_prefix}-ai-sa"
  display_name = "AI service account"
}

resource "google_service_account" "frontend_sa" {
  account_id   = "${local.name_prefix}-frontend-sa"
  display_name = "Frontend service account"
}

# Grant Secret Manager access & Cloud SQL client to each SA (least-privilege as necessary)
resource "google_project_iam_binding" "sa_secret_accessor" {
  project = local.project_id
  role    = "roles/secretmanager.secretAccessor"
  members = [
    "serviceAccount:${google_service_account.backend_sa.email}",
    "serviceAccount:${google_service_account.bot_sa.email}",
    "serviceAccount:${google_service_account.ai_sa.email}",
  ]
}

resource "google_project_iam_binding" "sa_cloudsql_client" {
  project = local.project_id
  role    = "roles/cloudsql.client"
  members = [
    "serviceAccount:${google_service_account.backend_sa.email}",
    "serviceAccount:${google_service_account.bot_sa.email}",
    "serviceAccount:${google_service_account.ai_sa.email}",
  ]
}

###### Secrets (optionally created by Terraform)
resource "google_secret_manager_secret" "bot_token" {
  count = var.create_secrets_from_vars && var.bot_token != "" ? 1 : 0
  secret_id = "BOT_TOKEN"
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "bot_token_version" {
  count    = length(google_secret_manager_secret.bot_token) > 0 ? 1 : 0
  secret   = google_secret_manager_secret.bot_token[0].id
  secret_data = var.bot_token
}

resource "google_secret_manager_secret" "openai_api_key" {
  count = var.create_secrets_from_vars && var.openai_api_key != "" ? 1 : 0
  secret_id = "OPENAI_API_KEY"
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "openai_api_key_ver" {
  count = length(google_secret_manager_secret.openai_api_key) > 0 ? 1 : 0
  secret = google_secret_manager_secret.openai_api_key[0].id
  secret_data = var.openai_api_key
}

resource "google_secret_manager_secret" "spreadsheet_id" {
  count = var.create_secrets_from_vars && var.spreadsheet_id != "" ? 1 : 0
  secret_id = "SPREADSHEET_ID"
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "spreadsheet_id_ver" {
  count = length(google_secret_manager_secret.spreadsheet_id) > 0 ? 1 : 0
  secret = google_secret_manager_secret.spreadsheet_id[0].id
  secret_data = var.spreadsheet_id
}

resource "google_secret_manager_secret" "cloudsql_password" {
  count = var.create_secrets_from_vars && var.initial_db_password != "" ? 1 : 0
  secret_id = "CLOUDSQL_PASSWORD"
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "cloudsql_password_ver" {
  count = length(google_secret_manager_secret.cloudsql_password) > 0 ? 1 : 0
  secret = google_secret_manager_secret.cloudsql_password[0].id
  secret_data = var.initial_db_password
}

###### Cloud Run services (annotations to attach Cloud SQL via cloudsql-instances)
resource "google_cloud_run_service" "backend" {
  name     = "${local.name_prefix}-backend"
  location = var.region

  template {
    spec {
      containers {
        image = var.images.backend
        env { name = "CLOUD_RUN_ENV" value = "true" }
        env { name = "CLOUDSQL_DB" value = var.db_name }
        env { name = "CLOUDSQL_USER" value = var.db_user }
      }
    }
    metadata {
      annotations = {
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.postgres.connection_name
      }
    }
  }

  traffics {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "backend_invoker" {
  service = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role    = "roles/run.invoker"
  member  = "allUsers" # optional: make public or restrict
}

resource "google_cloud_run_service" "bot" {
  name     = "${local.name_prefix}-bot"
  location = var.region
  template {
    spec {
      containers {
        image = var.images.bot
        env { name = "CLOUD_RUN_ENV" value = "true" }
        env { name = "CLOUDSQL_DB" value = var.db_name }
        env { name = "CLOUDSQL_USER" value = var.db_user }
      }
    }
    metadata {
      annotations = {
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.postgres.connection_name
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "bot_invoker" {
  service  = google_cloud_run_service.bot.name
  location = google_cloud_run_service.bot.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service" "ai" {
  name     = "${local.name_prefix}-ai"
  location = var.region
  template {
    spec {
      containers {
        image = var.images.ai
        env { name = "OPENAI_API_KEY" value = var.openai_api_key }
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "ai_invoker" {
  service  = google_cloud_run_service.ai.name
  location = google_cloud_run_service.ai.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service" "frontend" {
  name     = "${local.name_prefix}-frontend"
  location = var.region
  template {
    spec {
      containers {
        image = var.images.frontend
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "frontend_invoker" {
  service  = google_cloud_run_service.frontend.name
  location = google_cloud_run_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

###### Cloud Build Triggers for CI/CD
resource "google_cloudbuild_trigger" "backend_trigger" {
  filename = "infra/terraform/cloudbuild/backend.yaml"
  github {
    owner = var.repo_owner
    name  = var.repo_name
    push {
      branch = var.repo_branch
    }
  }
}

resource "google_cloudbuild_trigger" "bot_trigger" {
  filename = "infra/terraform/cloudbuild/bot.yaml"
  github {
    owner = var.repo_owner
    name  = var.repo_name
    push {
      branch = var.repo_branch
    }
  }
}

resource "google_cloudbuild_trigger" "ai_trigger" {
  filename = "infra/terraform/cloudbuild/ai.yaml"
  github {
    owner = var.repo_owner
    name  = var.repo_name
    push {
      branch = var.repo_branch
    }
  }
}

resource "google_cloudbuild_trigger" "frontend_trigger" {
  filename = "infra/terraform/cloudbuild/frontend.yaml"
  github {
    owner = var.repo_owner
    name  = var.repo_name
    push {
      branch = var.repo_branch
    }
  }
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

resource "google_project_service" "enable_apis" {
  for_each = toset([
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
  ])
  service = each.key
}

resource "google_service_account" "cloudrun_sa" {
  account_id   = var.service_name
  display_name = "Cloud Run Service Account for Tattoo Bot"
}

resource "google_project_iam_binding" "cloudsql_client" {
  project = var.project
  role    = "roles/cloudsql.client"
  members = ["serviceAccount:${google_service_account.cloudrun_sa.email}"]
}

resource "google_project_iam_binding" "secret_accessor" {
  project = var.project
  role    = "roles/secretmanager.secretAccessor"
  members = ["serviceAccount:${google_service_account.cloudrun_sa.email}"]
}

resource "google_sql_database_instance" "postgres_instance" {
  name             = var.db_instance_name
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-custom-1-3840"
    ip_configuration {
      ipv4_enabled = false
      private_network = null
    }
  }
}

resource "google_sql_database" "db" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres_instance.name
}

resource "google_sql_user" "db_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres_instance.name
  # password should be set using sensitive var via terraform.tfvars or env
  password = var.db_user_password
}

resource "google_secret_manager_secret" "bot_token" {
  secret_id = "BOT_TOKEN"
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "OPENAI_API_KEY"
  replication {
    automatic = true
  }
}

resource "google_cloud_run_service" "service" {
  name     = var.service_name
  location = var.region
  template {
    spec {
      containers {
        image = var.image
        env {
          name  = "CLOUD_RUN_ENV"
          value = "true"
        }
        env {
          name = "CLOUDSQL_CONNECTION_NAME"
          value = "${var.project}:${var.region}:${var.db_instance_name}"
        }
        secret_env {
          name = "BOT_TOKEN"
          value_from {
            secret_key_ref {
              secret = google_secret_manager_secret.bot_token.name
              version = "latest"
            }
          }
        }
        secret_env {
          name = "OPENAI_API_KEY"
          value_from {
            secret_key_ref {
              secret = google_secret_manager_secret.openai_api_key.name
              version = "latest"
            }
          }
        }
      }
      service_account_name = google_service_account.cloudrun_sa.email
    }
  }
  traffic {
    percent         = 100
    latest_revision = true
  }
}

output "cloud_run_url" {
  value = google_cloud_run_service.service.status[0].url
}
