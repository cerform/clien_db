#!/usr/bin/env python3
"""Test sending message to bot"""

import requests
import json
import time

# Telegram webhook URL
bot_url = "https://telegram-bot-408800151466.us-central1.run.app"

# Test update payload (simulating Telegram webhook)
update = {
    "update_id": 999999999,
    "message": {
        "message_id": 123,
        "date": int(time.time()),
        "chat": {
            "id": 438407739,
            "type": "private",
            "first_name": "Test"
        },
        "from": {
            "id": 438407739,
            "is_bot": False,
            "first_name": "Test"
        },
        "text": "Когда ближайший слот?"
    }
}

print("Sending test message to bot...")
print(f"URL: {bot_url}/webhook")
print(f"Message: {update['message']['text']}")

try:
    response = requests.post(
        f"{bot_url}/webhook",
        json=update,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    
    if response.status_code == 200:
        print("✅ Message sent successfully!")
        print("Check logs in: gcloud logging read \"resource.labels.revision_name=telegram-bot-00071-9rp\" --limit=100")
    else:
        print(f"❌ Error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Connection error: {e}")
