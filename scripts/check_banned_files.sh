#!/usr/bin/env bash
set -euo pipefail

# Check for banned filenames (secrets, virtualenvs, etc.) in the repository.
# This is intended to be used in a CI action (pull_request/push) to block commits that add secrets.

BANNED_PATTERNS=(
  "(^|/)\.env$"
  "(^|/)env\.ya?ml$"
  "(^|/)\.env\..+"
  "(^|/)\.env\.cloud$"
  "(^|/)(\.venv|venv|\.deploy_venv)/"
  "\\.pem$"
  "\\.key$"
)

found=()
files=$(git ls-files --exclude-standard --cached --others | sed 's/^/\//')
for pat in "${BANNED_PATTERNS[@]}"; do
  matches=$(echo "$files" | grep -E "$pat" || true)
  if [[ -n "$matches" ]]; then
    found+=("$matches")
  fi
done

if [[ ${#found[@]} -gt 0 ]]; then
  echo "⚠️  Banned files detected in the commit/push:"
  printf '%s\n' "${found[@]}"
  echo "Please remove secrets and environment files from the repository, and add them to .gitignore."
  exit 1
fi

echo "No banned files detected."
exit 0
