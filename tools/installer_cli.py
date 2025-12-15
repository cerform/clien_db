#!/usr/bin/env python3
"""
Interactive CLI installer for Cloud Run + Secret Manager

This script performs the same operations as the Tk GUI but in an interactive terminal flow:
- Prompt for Project ID, Service name, Region, Secret name, Bot token, Image, Admin IDs
- Create secret (or add version) in Secret Manager
- Bind Secret Accessor role to Cloud Run service account
- Update Cloud Run service to reference secret
- Deploy image (optional)

Security: token input uses getpass so it will not echo. The script shells out to `gcloud`.
"""
from __future__ import annotations

import getpass
import json
import os
import shlex
import subprocess
import sys
from typing import Optional


def run(cmd: str, echo: bool = True) -> tuple[int, str]:
    if echo:
        print(f"$ {cmd}")
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        out = (proc.stdout or "") + (proc.stderr or "")
        if echo:
            print(out)
        return proc.returncode, out
    except Exception as e:
        return 1, str(e)


def ask(prompt: str, default: Optional[str] = None) -> str:
    if default:
        res = input(f"{prompt} [{default}]: ")
        return res.strip() or default
    return input(f"{prompt}: ").strip()


def is_valid_secret_name(name: str) -> bool:
    # Secret ID must match [a-zA-Z_0-9]+ per gcloud
    import re
    return bool(re.match(r'^[a-zA-Z0-9_]+$', name))


def looks_like_token(value: str) -> bool:
    # Rough heuristic: telegram tokens often are digits:alphanumeric
    import re
    return bool(re.match(r'^\d+:', value))


def yesno(prompt: str, default: bool = True) -> bool:
    d = 'Y/n' if default else 'y/N'
    r = input(f"{prompt} ({d}): ")
    if not r:
        return default
    return r.lower().startswith('y')


def ensure_gcloud() -> bool:
    code, out = run('gcloud --version', echo=False)
    if code != 0:
        print('gcloud CLI not found or errored; install and authenticate first')
        print(out)
        return False
    return True


def detect_project() -> Optional[str]:
    code, out = run('gcloud config get-value project --quiet', echo=False)
    if code == 0:
        return out.strip()
    return None


def detect_service_and_region(service_name: str = 'tattoo-bot') -> tuple[Optional[str], Optional[str]]:
    # List services and search for the one matching service_name
    code, out = run('gcloud run services list --platform=managed --format=json', echo=False)
    if code != 0:
        return None, None
    try:
        arr = json.loads(out)
        for s in arr:
            if s.get('metadata', {}).get('name') == service_name:
                # region may be in metadata.labels or resourceLocation
                region = s.get('metadata', {}).get('labels', {}).get('cloud.googleapis.com/location')
                if not region:
                    region = s.get('metadata', {}).get('annotations', {}).get('run.googleapis.com/region')
                return service_name, region
    except Exception:
        return None, None
    return None, None


def detect_image_for_service(service: str, region: str) -> Optional[str]:
    if not service or not region:
        return None
    cmd = f"gcloud run services describe {shlex.quote(service)} --region={shlex.quote(region)} --format='value(spec.template.spec.containers[0].image)'"
    code, out = run(cmd, echo=False)
    if code == 0:
        return out.strip()
    return None


def detect_secret_default(project: str) -> str:
    # prefer TELEGRAM_BOT_TOKEN if exists
    if project and secret_exists(project, 'TELEGRAM_BOT_TOKEN'):
        return 'TELEGRAM_BOT_TOKEN'
    return 'TELEGRAM_BOT_TOKEN'


def parse_env_file(path: str) -> dict:
    """Parse a simple .env file into dict of key->value (ignores comments)."""
    env = {}
    try:
        with open(path, 'r') as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                if '=' in s:
                    k, v = s.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    env[k] = v
    except FileNotFoundError:
        return {}
    return env


def default_secret_candidates(env: dict) -> list:
    """Return keys likely to be secrets based on heuristics."""
    candidates = []
    keywords = ['TOKEN', 'KEY', 'SECRET', 'PASSWORD', 'API', 'DB', 'DATABASE', 'CLOUDSQL']
    for k in env:
        up = k.upper()
        if any(kw in up for kw in keywords):
            candidates.append(k)
    return candidates


def secret_exists(project: str, secret: str) -> bool:
    code, out = run(f"gcloud secrets describe {shlex.quote(secret)} --project={shlex.quote(project)}", echo=False)
    return code == 0


def add_secret_version(project: str, secret: str, token: str) -> bool:
    # add version
    cmd = f"echo -n {shlex.quote(token)} | gcloud secrets versions add {shlex.quote(secret)} --data-file=- --project={shlex.quote(project)}"
    code, out = run(cmd)
    return code == 0


def create_secret(project: str, secret: str, token: str) -> bool:
    cmd = f"echo -n {shlex.quote(token)} | gcloud secrets create {shlex.quote(secret)} --data-file=- --replication-policy='automatic' --project={shlex.quote(project)}"
    code, out = run(cmd)
    return code == 0


def add_iam_binding(project: str, secret: str, service_account: str) -> bool:
    cmd = f"gcloud secrets add-iam-policy-binding {shlex.quote(secret)} --member=serviceAccount:{shlex.quote(service_account)} --role=roles/secretmanager.secretAccessor --project={shlex.quote(project)}"
    code, out = run(cmd)
    return code == 0


def update_cloud_run_set_secret(project: str, region: str, service: str, secret: str) -> bool:
    cmd = f"gcloud run services update {shlex.quote(service)} --region={shlex.quote(region)} --project={shlex.quote(project)} --set-secrets BOT_TOKEN={shlex.quote(secret)}:latest"
    code, out = run(cmd)
    return code == 0


def deploy_image(project: str, region: str, service: str, image: str) -> bool:
    cmd = f"gcloud run deploy {shlex.quote(service)} --image {shlex.quote(image)} --region={shlex.quote(region)} --project={shlex.quote(project)} --allow-unauthenticated"
    code, out = run(cmd)
    return code == 0


def main():
    print('Interactive Cloud Run / Secret Manager installer')
    if not ensure_gcloud():
        sys.exit(1)

    # Auto-detect common values
    detected_project = detect_project() or ''
    detected_service, detected_region = detect_service_and_region('tattoo-bot')
    detected_service = detected_service or 'tattoo-bot'
    detected_region = detected_region or 'europe-west1'
    detected_secret = detect_secret_default(detected_project)
    detected_image = detect_image_for_service(detected_service, detected_region) or ''

    print('Auto-detected values:')
    print(f'  Project: {detected_project or "(none)"}')
    print(f'  Service: {detected_service}')
    print(f'  Region: {detected_region}')
    print(f'  Secret: {detected_secret}')
    print(f'  Image: {detected_image or "(none)"}')

    project = ask('GCP Project ID', detected_project)
    service = ask('Cloud Run service name', detected_service)
    region = ask('Region', detected_region)
    secret_input = ask('Secret name (Secret Manager)', detected_secret)
    token_provided_early = False
    token_from_input = ''
    # If user accidentally pasted token into secret field, detect and fix
    if not is_valid_secret_name(secret_input) and looks_like_token(secret_input):
        token_provided_early = True
        token_from_input = secret_input
        secret = detected_secret
        print('Detected token input in secret field; using default secret name and treating input as token (not echoed).')
    else:
        secret = secret_input
    image = ask('Image to deploy (optional, e.g. gcr.io/project/image:tag)', detected_image)
    admins = ask('Admin IDs (comma-separated) (optional)', '')

    if token_provided_early:
        token = token_from_input
    else:
        token = getpass.getpass('Bot token (will not be shown): ').strip()
    if not token:
        print('No token provided - aborting')
        sys.exit(1)

    # Confirm
    print('\nSummary:')
    print(f'  Project: {project}')
    print(f'  Service: {service} (region {region})')
    print(f'  Secret: {secret}')
    print(f'  Image: {image or "(no image)"}')
    if not yesno('Proceed with these settings?', default=True):
        print('Aborted by user')
        sys.exit(0)

    # Create or add secret
    # Offer automated import from .env
    if yesno('Import secrets from .env file (will prompt to select keys)?', default=False):
        env_path = ask('Path to .env file', '.env')
        env = parse_env_file(env_path)
        if not env:
            print('No entries found in .env or file missing')
        else:
            candidates = default_secret_candidates(env)
            print('Found the following keys in .env:')
            for k in env:
                print(' ', k)
            print('\nSuggested secret candidates (auto-detected):')
            for k in candidates:
                print('  ', k)
            chosen = ask('Comma-separated keys to import (or ENTER to import suggested)', ','.join(candidates))
            keys = [x.strip() for x in chosen.split(',') if x.strip()]
            for key in keys:
                val = env.get(key)
                if val is None:
                    print(f'Key {key} not found in .env — skipping')
                    continue
                sname = key if is_valid_secret_name(key) else key.replace('-', '_')
                if secret_exists(project, sname):
                    print(f'Adding version for secret {sname} from .env')
                    add_secret_version(project, sname, val)
                else:
                    print(f'Creating secret {sname} from .env')
                    create_secret(project, sname, val)

    # Create or add secret for provided token (default single secret)
    if secret_exists(project, secret):
        print(f'Secret {secret} exists — adding new version')
        if not add_secret_version(project, secret, token):
            print('Failed to add secret version')
            sys.exit(1)
    else:
        print(f'Creating secret {secret}')
        if not create_secret(project, secret, token):
            print('Failed to create secret')
            sys.exit(1)

    # Bind service account
    sa = f"{service}@{project}.iam.gserviceaccount.com"
    print(f'Granting Secret Accessor to {sa}')
    if not add_iam_binding(project, secret, sa):
        print('Failed to add IAM binding (you can add it manually later)')

    # Update Cloud Run to reference secret
    print('Updating Cloud Run to reference secret...')
    if not update_cloud_run_set_secret(project, region, service, secret):
        print('Failed to update Cloud Run to use secret')
    else:
        print('Cloud Run updated with secret')

    # Deploy image if provided
    if image:
        print('Deploying image...')
        if not deploy_image(project, region, service, image):
            print('Deploy failed')
        else:
            print('Deploy succeeded')

    print('Done. Check logs and test /admin to confirm bot initializes properly.')


if __name__ == '__main__':
    main()
