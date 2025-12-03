#!/bin/bash
# Quick installation script

set -e

echo "🎨 TATTOO APPOINTMENT BOT - INSTALLATION"
echo "========================================"
echo ""

if [ ! -f ".env" ]; then
    echo "1️⃣ Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ Created .env - EDIT IT NOW and add:"
    echo "   BOT_TOKEN="
    echo "   SPREADSHEET_ID="
    echo "   ADMIN_USER_IDS="
else
    echo "✓ .env already exists"
fi

if [ ! -f "credentials.json" ]; then
    echo ""
    echo "2️⃣ credentials.json not found"
    echo "   - Go to https://console.cloud.google.com"
    echo "   - Create Desktop App OAuth credentials"
    echo "   - Save as credentials.json in this folder"
    echo ""
else
    echo "✓ credentials.json exists"
fi

echo ""
echo "3️⃣ Installing Python packages..."
python3 -m pip install --upgrade pip > /dev/null
python3 -m pip install -r requirements.txt > /dev/null
echo "✓ Packages installed"

echo ""
echo "4️⃣ Creating Google Sheets..."
python3 create_google_sheets_structure.py 2>/dev/null || echo "ℹ️ Skipped (needs valid credentials.json)"

echo ""
echo "✅ SETUP COMPLETE!"
echo ""
echo "NEXT STEPS:"
echo "1. Edit .env and add:"
echo "   - BOT_TOKEN (from @BotFather)"
echo "   - SPREADSHEET_ID (from previous output)"
echo "   - ADMIN_USER_IDS (your Telegram ID)"
echo ""
echo "2. Run: python3 run.py"
echo ""
