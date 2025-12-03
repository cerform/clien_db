#!/usr/bin/env bash
set -e
echo "[Bootstrap] Installing Python requirements..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "[Bootstrap] Ensuring Google credentials placeholder..."
if [ ! -f "${PWD}/credentials.json" ]; then
  cat > credentials.json <<'EOF'
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID",
    "project_id": "YOUR_PROJECT_ID",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob","http://localhost"]
  }
}
EOF
  echo "[Bootstrap] Wrote placeholder credentials.json — replace with real OAuth2 from Google Console."
else
  echo "[Bootstrap] Found credentials.json"
fi

echo "[Bootstrap] Done. Edit .env and run: python3 run.py"
