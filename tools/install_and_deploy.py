#!/usr/bin/env python3
"""
Improved INKA one-click installer with non-interactive flags, dry-run and webhook setup.
"""
import argparse
import json
import logging
import os
import subprocess
import sys
from typing import Optional


def check_cmd(cmd: str) -> bool:
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False


def prompt(msg: str, default: Optional[str] = None) -> str:
    try:
        val = input(f"{msg} [{default}]: " if default else f"{msg}: ")
        return val.strip() or (default or "")
    except EOFError:
        return default or ""


def run_install(
    project_id: Optional[str] = None,
    region: str = "europe-west1",
    service_name: str = "inka-bot",
    docker_image: Optional[str] = None,
    sa_name: Optional[str] = None,
    set_webhook: bool = False,
    telegram_token: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    dry_run: bool = False,
):
    logger = logging.getLogger("installer")
    logger.info("Starting INKA installer. dry_run=%s", dry_run)

    # Check required tools
    for tool in ["gcloud", "docker"]:
        if not check_cmd(f"which {tool}"):
            logger.error("%s not found. Please install and retry.", tool)
            sys.exit(1)

    if sys.version_info < (3, 10):
        logger.error("Python >= 3.10 required.")
        sys.exit(1)

    # GCloud auth (interactive)
    if not check_cmd("gcloud auth print-access-token"):
        logger.info("gcloud auth is required. Running: gcloud auth login")
        if not dry_run:
            subprocess.run("gcloud auth login", shell=True, check=True)

    # Params (allow both interactive and non-interactive)
    project_id = project_id or prompt("GCP_PROJECT_ID")
    if not project_id:
        logger.error("GCP_PROJECT_ID is required")
        sys.exit(1)

    region = region or prompt("GCP_REGION", "europe-west1")
    service_name = service_name or prompt("Cloud Run SERVICE_NAME", "inka-bot")
    docker_image = docker_image or f"gcr.io/{project_id}/{service_name}:latest"
    sa_name = sa_name or prompt("Service account name (will be created if missing)", f"{service_name}-sa")
    sa_full = f"{sa_name}@{project_id}.iam.gserviceaccount.com"

    # Enable required APIs
    apis = [
        "run.googleapis.com",
        "cloudbuild.googleapis.com",
        "secretmanager.googleapis.com",
        "sheets.googleapis.com",
        "calendar.googleapis.com",
    ]
    for api in apis:
        logger.info("Enabling API: %s", api)
        if not dry_run:
            # Attempt to enable API but do not abort whole install if restricted by org policy
            res = subprocess.run(f"gcloud services enable {api} --project {project_id}", shell=True, capture_output=True)
            if res.returncode != 0:
                logger.warning("Could not enable API %s (rc=%s). Continuing, but API may be unavailable. stderr=%s", api, res.returncode, res.stderr.decode(errors='ignore')[:1000])

    # Check/create service account
    try:
        subprocess.run(f"gcloud iam service-accounts describe {sa_full} --project {project_id}", shell=True, check=True, stdout=subprocess.PIPE)
        logger.info("Service account %s exists", sa_full)
    except subprocess.CalledProcessError:
        logger.info("Creating service account %s", sa_full)
        if not dry_run:
            subprocess.run(f"gcloud iam service-accounts create {sa_name} --project {project_id} --display-name '{sa_name}'", shell=True, check=True)

    # Grant roles (best-effort)
    roles = [
        "roles/run.admin",
        "roles/iam.serviceAccountUser",
        "roles/secretmanager.admin",
        "roles/cloudbuild.builds.editor",
    ]
    for role in roles:
        logger.info("Granting role %s to %s", role, sa_full)
        if not dry_run:
            subprocess.run(f"gcloud projects add-iam-policy-binding {project_id} --member=serviceAccount:{sa_full} --role={role}", shell=True, check=False)

    # Build and push Docker image
    logger.info("Building Docker image: %s", docker_image)
    if not dry_run:
        subprocess.run(f"docker build -t {docker_image} .", shell=True, check=True)
        subprocess.run(f"docker push {docker_image}", shell=True, check=True)

    # Register secrets
    telegram_bot_token = telegram_token or prompt("TELEGRAM_BOT_TOKEN (paste)", "")
    llm_api_key = llm_api_key or prompt("LLM_API_KEY (paste)", "")

    def register_secret(name: str, value: str) -> None:
        if not value:
            return
        logger.info("Registering secret %s", name)
        if not dry_run:
            # Attempt to create; ignore if exists
            subprocess.run(f"gcloud secrets create {name} --project {project_id} --replication-policy automatic", shell=True, check=False)
            subprocess.run(f"echo -n '{value}' | gcloud secrets versions add {name} --data-file=- --project {project_id}", shell=True, check=True)

    register_secret("TELEGRAM_BOT_TOKEN", telegram_bot_token)
    register_secret("LLM_API_KEY", llm_api_key)

    # Prepare env vars
    env_vars = {
        "SPREADSHEET_ID": prompt("SPREADSHEET_ID (Google Sheets ID)", ""),
        "MASTER_CALENDAR_ID": prompt("MASTER_CALENDAR_ID (Salon calendar ID)", ""),
        "DEFAULT_TIMEZONE": prompt("DEFAULT_TIMEZONE", "Europe/Moscow"),
        "USE_WEBHOOK": "true",
    }
    env_pairs = ",".join(f"{k}={v}" for k, v in env_vars.items() if v)

    # Deploy to Cloud Run with secrets mapped
    logger.info("Deploying to Cloud Run: %s", service_name)
    secret_mappings = []
    if telegram_bot_token:
        # Cloud Run expects SECRET_NAME:VERSION (no projects/ prefix)
        secret_mappings.append(f"TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest")
    if llm_api_key:
        secret_mappings.append(f"LLM_API_KEY=LLM_API_KEY:latest")
    secrets_arg = " --set-secrets " + ",".join(secret_mappings) if secret_mappings else ""
    deploy_cmd = (
        f"gcloud run deploy {service_name} "
        f"--image {docker_image} --region {region} --platform managed "
        f"--allow-unauthenticated --project {project_id} --service-account {sa_full}"
        + (f" --set-env-vars {env_pairs}" if env_pairs else "")
        + secrets_arg
    )
    logger.info("Deploy command: %s", deploy_cmd if dry_run else "(hidden)")
    if not dry_run:
        subprocess.run(deploy_cmd, shell=True, check=True)

    # Get service URL
    if dry_run:
        url = f"https://{service_name}.{region}.example.com"
    else:
        url = subprocess.check_output(
            f"gcloud run services describe {service_name} --region {region} --format='value(status.url)' --project {project_id}",
            shell=True,
        ).decode().strip()
    logger.info("Deployed. URL=%s", url)

    # Set webhook
    if set_webhook and telegram_bot_token:
        set_cmd = f"curl -s -X POST \"https://api.telegram.org/bot{telegram_bot_token}/setWebhook\" -d url={url}/telegram/webhook"
        logger.info("Setting webhook via command: %s", set_cmd if dry_run else "(hidden)")
        if not dry_run:
            subprocess.run(set_cmd, shell=True, check=True)

    print(f"\n✅ Deploy completed. Visit {url}/setup to finish configuration")
    return url


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="INKA One-Click Installer")
    parser.add_argument("--project", "-p", help="GCP project id")
    parser.add_argument("--region", "-r", help="GCP region", default="europe-west1")
    parser.add_argument("--service", "-s", help="Cloud Run service name", default="inka-bot")
    parser.add_argument("--docker-image", help="Docker image name")
    parser.add_argument("--sa-name", help="Service account name")
    parser.add_argument("--set-webhook", action="store_true", help="Automatically set Telegram webhook after deploy")
    parser.add_argument("--telegram-token", help="Telegram bot token")
    parser.add_argument("--dry-run", action="store_true", help="Dry run, do not change cloud resources")
    args = parser.parse_args()

    run_install(
        project_id=args.project,
        region=args.region,
        service_name=args.service,
        docker_image=args.docker_image,
        sa_name=args.sa_name,
        set_webhook=args.set_webhook,
        telegram_token=args.telegram_token,
        dry_run=args.dry_run,
    )

if __name__ == "__main__":
    main()

