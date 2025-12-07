#!/bin/bash
# Deploy fix to Google Cloud Run
# This script pushes the deployment fix

set -e

echo "═══════════════════════════════════════════════════════"
echo "📤 Pushing deployment fix to Cloud Run"
echo "═══════════════════════════════════════════════════════"

cd "$(dirname "$0")"

# Check git status
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ Working directory is clean"
else
    echo "⚠️ Warning: Uncommitted changes detected"
    git status
fi

# Push to origin
echo ""
echo "🚀 Pushing to origin/google-cloud-run..."
git push origin google-cloud-run

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ Push complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Cloud Build will automatically trigger and deploy."
echo "Monitor deployment at: https://console.cloud.google.com/cloud-build/builds"
echo ""
echo "Key changes in this deployment:"
echo "  • Webhook setup moved to background task (no blocking)"
echo "  • Async lazy loading for Google Services"
echo "  • Startup time: ~2.6 seconds (verified locally)"
echo "  • Thread-safe initialization with asyncio locks"
echo ""
