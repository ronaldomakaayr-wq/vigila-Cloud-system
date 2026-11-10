@echo off
title VIGILA Cloud Surveillance System - AWS Optimized
echo =====================================================================
echo       INICIANDO SISTEMA DE VIDEOVIGILANCIA VIGILA CLOUD (AWS)
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Verificando dependencias...
python -m pip install -r requirements.txt --quiet

echo [2/3] Inicializando base de datos y cargando datos demo...
python scripts/seed_database.py

echo [3/3] Iniciando servidor web VIGILA en http://localhost:8000 ...
echo.
echo =====================================================================
echo  Accede al dashboard en tu navegador:
echo  URL: http://localhost:8000
echo  Documentacion API (Swagger): http://localhost:8000/docs
echo =====================================================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause

