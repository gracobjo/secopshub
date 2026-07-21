# Compila el frontend para producción (Windows / desarrollo local)
$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

Write-Host "==> Compilando frontend..." -ForegroundColor Cyan
Set-Location "$Root\frontend"
npm ci
npm run build

Write-Host "==> Verificando backend..." -ForegroundColor Cyan
Set-Location "$Root\backend"
if (-not (Test-Path "venv")) { python -m venv venv }
& .\venv\Scripts\pip install -r requirements.txt -q

Write-Host ""
Write-Host "Listo. frontend/dist generado." -ForegroundColor Green
Write-Host "En produccion Linux: ver deploy/README.md (Nginx + Gunicorn + TLS)"
