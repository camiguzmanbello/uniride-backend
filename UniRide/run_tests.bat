@echo off
REM Script para instalar dependencias de testing y ejecutar tests con cobertura

echo ==========================================
echo UniRide API - Test Coverage Setup
echo ==========================================

REM Cambiar a directorio del proyecto
cd /d "%~dp0"

REM Activar entorno virtual si existe
if exist "..\..\env\Scripts\activate.bat" (
    call "..\..\env\Scripts\activate.bat"
)

echo.
echo 1. Instalando dependencias de testing...
python -m pip install -q pytest pytest-django pytest-cov coverage factory-boy faker

echo 2. Ejecutando tests con cobertura...
pytest --cov=apps --cov-report=html --cov-report=term-missing --cov-report=xml -v

echo.
echo ==========================================
echo Tests completados!
echo Reporte HTML disponible en: htmlcov\index.html
echo ==========================================
pause
