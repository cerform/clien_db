#!/bin/bash
# Real-time log monitor for tattoo-bot

echo "🔍 Real-time Log Monitor for tattoo-bot"
echo "========================================"
echo "Press Ctrl+C to stop monitoring"
echo ""

LAST_TIMESTAMP=$(date -u -d '5 seconds ago' +"%Y-%m-%dT%H:%M:%SZ")

while true; do
    echo "⏱️  $(date '+%H:%M:%S') - Checking for new logs..."
    
    # Get logs since last check
    gcloud logging read \
        "resource.type=cloud_run_revision AND resource.labels.service_name=tattoo-bot AND timestamp>='${LAST_TIMESTAMP}'" \
        --limit 100 \
        --format='table(timestamp,severity,textPayload)' 2>/dev/null | tail -20
    
    # Update last timestamp
    LAST_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    echo ""
    echo "---"
    sleep 3
done
