$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path .venv)) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Write-Host "Indítás: http://127.0.0.1:5000" -ForegroundColor Green
.\.venv\Scripts\python.exe app.py
