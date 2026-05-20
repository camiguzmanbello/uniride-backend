@echo off
REM Script Automatizado: Tests + SonarQube en UNA sola ejecución
REM Para Windows

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo   UniRide API - Tests to SonarQube
echo ==========================================
echo.

REM Cambiar directorio
cd /d "%~dp0"

REM Color output
for /F %%A in ('copy /Z "%~f0" nul') do set "BS=%%A"

echo [PASO 1/3] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo !BS![ERROR] Python no está instalado
    exit /b 1
)

echo [PASO 2/3] Instalando dependencias...
python -m pip install -q pytest pytest-django pytest-cov coverage 2>nul
if errorlevel 1 (
    echo !BS![ADVERTENCIA] Algunos packages podrían no haberse instalado
)

echo.
echo [PASO 3/3] Ejecutando Tests...
echo ==========================================
pytest --cov=apps --cov-report=xml --cov-report=html --cov-report=term-missing -v

if errorlevel 1 (
    echo.
    echo !BS![ERROR] Tests fallaron
    exit /b 1
)

echo.
echo ==========================================
echo   TESTS COMPLETADOS ✅
echo ==========================================
echo.

REM Verificar si sonar-scanner existe
sonar-scanner --version >nul 2>&1
if errorlevel 1 (
    echo !BS![ADVERTENCIA] sonar-scanner no está instalado
    echo.
    echo Para instalar:
    echo   Windows: choco install sonarqube-scanner
    echo   O descarga desde: https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/
    echo.
    echo Archivos de cobertura listos en: coverage.xml
    echo Reporte HTML: htmlcov\index.html
    echo.
) else (
    echo.
    echo ==========================================
    echo   ENVIANDO A SONARQUBE...
    echo ==========================================
    echo.
    
    REM Verificar que coverage.xml existe
    if not exist "coverage.xml" (
        echo !BS![ERROR] coverage.xml no encontrado
        exit /b 1
    )
    
    REM Ejecutar SonarQube Scanner
    sonar-scanner -Dproject.settings=sonar-project.properties
    
    if errorlevel 1 (
        echo.
        echo !BS![ERROR] SonarQube Scanner falló
        echo Verifica que SonarQube esté corriendo en: http://localhost:9000
        exit /b 1
    ) else (
        echo.
        echo ==========================================
        echo   ✅ TODO COMPLETADO!
        echo ==========================================
        echo.
        echo 📊 Ver resultados en: http://localhost:9000
        echo 📈 Reporte local HTML: htmlcov\index.html
        echo.
    )
)

echo.
pause
