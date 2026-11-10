# Script de inicio PowerShell para VIGILA Cloud Surveillance
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "      INICIANDO SISTEMA DE VIDEOVIGILANCIA VIGILA CLOUD (AWS)        " -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan

Set-Location $PSScriptRoot

Write-Host "`n[1/3] Verificando dependencias..." -ForegroundColor Gray
python -m pip install -r requirements.txt --quiet

Write-Host "[2/3] Sembrando base de datos demo..." -ForegroundColor Gray
python scripts/seed_database.py

Write-Host "[3/3] Iniciando servidor FastAPI en http://localhost:8000 ...`n" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " Dashboard Principal: http://localhost:8000" -ForegroundColor White
Write-Host " Documentación Swagger: http://localhost:8000/docs" -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Cyan

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

