#!/bin/bash

# Script para instalar dependencias de testing y ejecutar tests con cobertura

echo "=========================================="
echo "UniRide API - Test Coverage Setup"
echo "=========================================="

# Cambiar a directorio del proyecto
cd "$(dirname "$0")"

# Activar entorno virtual si existe
if [ -f "../../env/Scripts/activate" ]; then
    source "../../env/Scripts/activate"
elif [ -f "../../env/bin/activate" ]; then
    source "../../env/bin/activate"
fi

echo ""
echo "1. Instalando dependencias de testing..."
pip install -q pytest pytest-django pytest-cov coverage factory-boy faker

echo "2. Instalando actualizar requirements.txt..."
pip freeze > requirements.txt

echo "3. Ejecutando tests con cobertura..."
pytest --cov=apps --cov-report=html --cov-report=term-missing --cov-report=xml -v

echo ""
echo "=========================================="
echo "Tests completados!"
echo "Reporte HTML disponible en: htmlcov/index.html"
echo "=========================================="
