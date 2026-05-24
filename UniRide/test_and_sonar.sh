#!/bin/bash

# Script Automatizado: Tests + SonarQube en UNA sola ejecución
# Para Linux/Mac

set -e

echo ""
echo "=========================================="
echo "   UniRide API - Tests to SonarQube"
echo "=========================================="
echo ""

# Cambiar a directorio del script
cd "$(dirname "$0")"

echo "[PASO 1/3] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 no está instalado"
    exit 1
fi

echo "[PASO 2/3] Instalando dependencias..."
python3 -m pip install -q pytest pytest-django pytest-cov coverage 2>/dev/null || true

echo ""
echo "[PASO 3/3] Ejecutando Tests..."
echo "=========================================="
python3 -m pytest --cov=apps --cov-report=xml --cov-report=html --cov-report=term-missing -v

echo ""
echo "=========================================="
echo "   TESTS COMPLETADOS ✅"
echo "=========================================="
echo ""

# Verificar si sonar-scanner existe
if ! command -v sonar-scanner &> /dev/null; then
    echo "[ADVERTENCIA] sonar-scanner no está instalado"
    echo ""
    echo "Para instalar:"
    echo "  1. Descarga de: https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/"
    echo "  2. Extrae y agrega a PATH"
    echo ""
    echo "Archivos de cobertura listos en: coverage.xml"
    echo "Reporte HTML: htmlcov/index.html"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "   ENVIANDO A SONARQUBE..."
    echo "=========================================="
    echo ""
    
    # Verificar que coverage.xml existe
    if [ ! -f "coverage.xml" ]; then
        echo "[ERROR] coverage.xml no encontrado"
        exit 1
    fi
    
    # Ejecutar SonarQube Scanner
    if sonar-scanner -Dproject.settings=sonar-project.properties; then
        echo ""
        echo "=========================================="
        echo "   ✅ TODO COMPLETADO!"
        echo "=========================================="
        echo ""
        echo "📊 Ver resultados en: http://localhost:9000"
        echo "📈 Reporte local HTML: htmlcov/index.html"
        echo ""
    else
        echo ""
        echo "[ERROR] SonarQube Scanner falló"
        echo "Verifica que SonarQube esté corriendo en: http://localhost:9000"
        exit 1
    fi
fi

echo ""
