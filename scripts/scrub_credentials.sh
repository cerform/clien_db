#!/usr/bin/env bash
set -euo pipefail

# WARNING: This script rewrites git history. Coordinate with your team before running.
# It requires git-filter-repo installed: pip install git-filter-repo

if [[ $(git status --porcelain) ]]; then
  echo "Please ensure your working tree is clean before running this script."
  exit 1
fi

echo "Scrubbing credentials.json from git history..."

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "git-filter-repo not found. Install it: pip install git-filter-repo"
  exit 1
fi

git filter-repo --invert-paths --path credentials.json

echo "Done. The file credentials.json has been removed from history. Please force-push your branches and inform collaborators."
