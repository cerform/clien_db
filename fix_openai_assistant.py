#!/usr/bin/env python3
"""
Fix OpenAI Assistant - удалить старый и создать новый
"""
import os
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')
old_assistant_id = os.getenv('OPENAI_ASSISTANT_ID', 'asst_LBGeLxauJ3nYbauR3pilbifN')

if not api_key:
    print("❌ OPENAI_API_KEY не установлен!")
    exit(1)

client = OpenAI(api_key=api_key)

# Удалить старый assistant
print(f"🗑️  Deleting old assistant {old_assistant_id}...")
try:
    client.beta.assistants.delete(old_assistant_id)
    print("✅ Old assistant deleted!")
except Exception as e:
    print(f"⚠️  Could not delete: {e}")

# Создать новый
print("\n📝 Creating new assistant...")
assistant = client.beta.assistants.create(
    name="INKA - Tattoo Salon Manager",
    description="Professional tattoo salon manager",
    model="gpt-4o-mini",
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_database_info",
                "description": "Get information from database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string", "description": "Table name"},
                        "filter_field": {"type": "string", "description": "Field to filter by"},
                        "filter_value": {"type": "string", "description": "Filter value"},
                        "limit": {"type": "integer", "description": "Limit results"}
                    },
                    "required": ["table"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "save_client",
                "description": "Save new client to database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "telegram_id": {"type": "integer", "description": "Telegram ID"},
                        "name": {"type": "string", "description": "Client name"},
                        "phone": {"type": "string", "description": "Phone number"},
                        "notes": {"type": "string", "description": "Notes about client"}
                    },
                    "required": ["telegram_id", "name"]
                }
            }
        }
    ]
)

print(f"✅ New assistant created!")
print(f"📋 Assistant ID: {assistant.id}")
print(f"\n🔄 Update .env.cloud-run:")
print(f"OPENAI_ASSISTANT_ID={assistant.id}")
