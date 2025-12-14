# PowerShell installer for Windows local dev
# Usage: Open PowerShell as Administrator (or with rights) and run:
#    ./install_windows.ps1

param (
    [switch]$InstallDocker,
    [switch]$StartPostgres
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $RepoRoot

function Ensure-Python {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error "Python not found. Please install Python 3.10+ and add it to PATH"
        exit 1
    }
    Write-Host "Python OK"
}

function Create-Venv {
    if (-not (Test-Path -Path .\.eco)) {
        python -m venv .eco
        Write-Host "Virtual environment created at .eco"
    } else {
        Write-Host "Virtual environment already exists"
    }
}

function Install-Requirements {
    .\.eco\Scripts\python -m pip install --upgrade pip
    .\.eco\Scripts\pip install -r requirements.txt
}

function Copy-Env {
    if (-not (Test-Path -Path .\.env)) {
        if (Test-Path .env.example) {
            Copy-Item .env.example .env
            Write-Host "Copied .env.example to .env"
        } else {
            @"
TELEGRAM_BOT_TOKEN=
OPENAI_API_KEY=
SPREADSHEET_ID=
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json
DEFAULT_TIMEZONE=Asia/Jerusalem
ADMIN_USER_IDS=
ENV=development
USE_WEBHOOK=false
WEBHOOK_URL=
PORT=8081
CLOUDSQL_USER=postgres
CLOUDSQL_PASSWORD=password
CLOUDSQL_DB=admin_messages
DATABASE_URL=
"@> .env
            Write-Host "Created basic .env"
        }
        Write-Host "Please edit .env with your credentials (you can use notepad .env)"
        notepad .env
    } else {
        Write-Host ".env already exists. Edit manually if needed."
    }
}

function Start-DockerCompose {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Warning "Docker not found; install Docker Desktop on Windows."
        return
    }
    docker compose -f .\setup\docker-compose.yml up -d
}

# Steps
Ensure-Python
Create-Venv
Install-Requirements
Copy-Env
if ($StartPostgres) { Start-DockerCompose }

Write-Host "Setup complete."
Write-Host "Run: .\.eco\Scripts\python run.py to start bot in polling or see run_production.py for production mode."
