# Granting Google Sheets access to the Cloud Run service account

This document explains how to share the production Google Spreadsheet with the Cloud Run service account used by the `tattoo-bot` service.

Key values in this repo:
- Cloud Run service name: `tattoo-bot` (see `deploy_cloudrun.sh`)
- Project ID: `tattoo-480007` (see `deploy_cloudrun.sh`)
- Cloud Run service account (intended): `tattoo-bot@tattoo-480007.iam.gserviceaccount.com`
- Production spreadsheet ID: look in your `.env` (example in repo): `SPREADSHEET_ID=1o-ipgcRgc6o4Gf0rcatcU9gky56UefS5_lx-df2KjCE`

Recommended sharing method (manual):
1. Open the spreadsheet in the browser:
   `https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>`
2. Click "Share" (top right)
3. Enter the service account email: `tattoo-bot@tattoo-480007.iam.gserviceaccount.com`
4. Give it `Editor` (or at least `Writer`) permission and click "Send".

Programmatic sharing (script):
- We include a small helper script: `scripts/share_sheet_with_service_account.py`.
- Requirements:
  - `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
  - Add an OAuth `credentials.json` (installed-app client) to project root.
- Run:
```bash
python3 scripts/share_sheet_with_service_account.py --spreadsheet-id <SPREADSHEET_ID> --service-account tattoo-bot@tattoo-480007.iam.gserviceaccount.com --role writer
```

Notes:
- Sharing with the service account gives the Cloud Run process (when using that service account) permission to read and write the spreadsheet.
- If you prefer more restricted access, share `Viewer` or `Commenter` (but code expects read/write for most operations).
- If you'd like, I can run the script for you if you provide OAuth credentials or run it in your environment and paste back the result.
