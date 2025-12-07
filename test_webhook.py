#!/usr/bin/env python3
"""
Simulate a user message to test the bot webhook
"""
import requests
import json
from datetime import datetime

BOT_URL = "https://tattoo-bot-408800151466.us-central1.run.app/webhook"

# Simulate a Telegram update with a user message
update = {
    "update_id": 999999,
    "message": {
        "message_id": 1,
        "date": int(datetime.now().timestamp()),
        "chat": {
            "id": 438407740,  # Different user ID for testing
            "type": "private",
            "first_name": "Тест"
        },
        "from": {
            "id": 438407740,
            "is_bot": False,
            "first_name": "Тест"
        },
        "text": "Хочу записаться на тату"
    }
}

print(f"🚀 Sending test message to {BOT_URL}")
print(f"📝 Update: {json.dumps(update, indent=2, ensure_ascii=False)}")

try:
    response = requests.post(BOT_URL, json=update, timeout=30)
    print(f"✅ Response status: {response.status_code}")
    print(f"📋 Response body: {response.text[:500]}")
except Exception as e:
    print(f"❌ Error: {e}")
