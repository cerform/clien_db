variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region (eg us-central1)"
  type        = string
  default     = "us-central1"
}

variable "env_prefix" {
  description = "Prefix used for resource names"
  type        = string
  default     = "tattoo"
}

variable "images" {
  description = "Container images for deployment (backend, bot, ai, frontend)"
  type = map(string)
  default = {
    backend  = "gcr.io/<PROJECT>/tattoo-backend:latest"
    bot      = "gcr.io/<PROJECT>/tattoo-bot:latest"
    ai       = "gcr.io/<PROJECT>/tattoo-ai:latest"
    frontend = "gcr.io/<PROJECT>/tattoo-frontend:latest"
  }
}

variable "repo_owner" {
  description = "GitHub repo owner (for Cloud Build triggers)"
  type        = string
  default     = "cerform"
}

variable "repo_name" {
  description = "GitHub repo name (for Cloud Build triggers)"
  type        = string
  default     = "clien_db"
}

variable "repo_branch" {
  description = "Branch pattern for triggers, e.g. ^main$ or ^release-.*$"
  type        = string
  default     = "^main$"
}

variable "github_app_installation_id" {
  description = "GitHub App installation ID or connections setup ID for GitHub App (required for triggers), supply via Terraform var" 
  type        = string
  default     = ""
}

variable "db_user" {
  description = "Database user name"
  type        = string
  default     = "tattoo_user"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "tattoo_salon"
}

variable "db_tier" {
  description = "Cloud SQL tier"
  type        = string
  default     = "db-custom-1-3840"
}

variable "initial_db_password" {
  description = "Initial database password for the user (recommended to use Secret Manager instead)"
  type        = string
  default     = ""
}

variable "create_secrets_from_vars" {
  description = "If true, create secret manager secrets from provided variables (CI should create secrets instead)"
  type        = bool
  default     = false
}

variable "bot_token" {
  description = "Telegram bot token (only when using create_secrets_from_vars)"
  type        = string
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API key (only when using create_secrets_from_vars)"
  type        = string
  default     = ""
}

variable "spreadsheet_id" {
  description = "Google Sheets ID (updates secret if create_secrets_from_vars set)"
  type        = string
  default     = ""
}
variable "project" {
  description = "GCP project id"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "db_instance_name" {
  description = "Cloud SQL instance name"
  type        = string
  default     = "tattoo-db"
}

variable "db_name" {
  description = "Postgres database name"
  type        = string
  default     = "tattoo_salon"
}

variable "db_user" {
  description = "DB user name"
  type        = string
  default     = "tattoo_user"
}

variable "db_user_password" {
  description = "Database user password (sensitive)"
  type        = string
  sensitive   = true
}


variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "tattoo-bot"
}

variable "image" {
  description = "Container image to deploy to Cloud Run"
  type        = string
}
