terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "~> 4.88"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google" {
  alias   = "us-central1"
  project = var.project_id
  region  = var.region
}
