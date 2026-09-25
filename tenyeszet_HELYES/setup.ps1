$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env -Force
Write-Host "Kész. Az admin jelszót az app.py környezeti változójával vagy a .env alapján állítsd be." -ForegroundColor Green
Write-Host "Indítás: .\run.ps1" -ForegroundColor Cyan
