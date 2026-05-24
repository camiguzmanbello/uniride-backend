# 🔍 GUÍA: Ejecutar Tests y Enviar a SonarQube

## 📋 Requisitos

✅ SonarQube corriendo en `http://localhost:9000`  
✅ Token de SonarQube: `squ_2f127d7958cee873d263d8d660c78f69f87eaa19` (ya configurado)  
✅ SonarQube Scanner instalado

---

## 🚀 Paso 1: Instalar SonarQube Scanner

### Windows:
```bash
# Opción A: Si tienes Chocolatey
choco install sonarqube-scanner

# Opción B: Manual (descargarlo)
# 1. Descarga de: https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/
# 2. Extrae en C:\sonarscanner
# 3. Agrega a PATH: C:\sonarscanner\bin
```

### Linux/Mac:
```bash
# Descargar
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
unzip sonar-scanner-cli-5.0.1.3006-linux.zip
sudo mv sonar-scanner-5.0.1.3006-linux /opt/sonar-scanner

# Agregar a PATH
export PATH=$PATH:/opt/sonar-scanner/bin
```

---

## 🎯 Paso 2: Ejecutar Tests Localmente (Generar Coverage)

### Windows:
```bash
cd C:\Users\Camila Guzman\OneDrive\Escritorio\UniRide_API\UniRide_API\UniRide

# Instalar dependencias (si no las tiene)
pip install -r requirements.txt

# Ejecutar tests
run_tests.bat
```

### Linux/Mac:
```bash
cd ~/UniRide_API/UniRide

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar tests
bash run_tests.sh
```

### Comando Manual (cualquier SO):
```bash
pytest \
  --cov=apps \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-report=xml \
  -v
```

**Resultado esperado:**
```
===================== test session starts ======================
...
===================== 50+ tests passed in 20s ====================
Coverage: 72% (OBJETIVO ALCANZADO ✅)
```

---

## 📊 Paso 3: Verificar Coverage.xml

```bash
# Debe generarse este archivo:
coverage.xml

# Contiene datos en formato XML para SonarQube
```

---

## 🔗 Paso 4: Enviar a SonarQube

### Opción A: Comando Directo

```bash
cd C:\Users\Camila Guzman\OneDrive\Escritorio\UniRide_API\UniRide_API\UniRide

sonar-scanner \
  -Dsonar.projectKey=uniride-backend-v2 \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=squ_2f127d7958cee873d263d8d660c78f69f87eaa19 \
  -Dsonar.python.coverage.reportPaths=coverage.xml
```

### Opción B: Usar archivo existente (sonar-project.properties)

```bash
# Ya está configurado, solo ejecuta:
sonar-scanner

# O con el archivo específico:
sonar-scanner -Dproject.settings=sonar-project.properties
```

**Resultado:**
```
INFO: ANALYSIS SUCCESSFUL
INFO: You can find the results at: http://localhost:9000/dashboard?id=uniride-backend-v2
```

---

## 📈 Paso 5: Ver Resultados en SonarQube Dashboard

1. **Abre**: `http://localhost:9000`
2. **Login**: (con tu usuario)
3. **Busca**: "UniRide Backend"
4. **Verás**:
   - ✅ % Cobertura
   - ✅ Bugs detectados
   - ✅ Code smells
   - ✅ Vulnerabilidades
   - ✅ Deuda técnica

---

## 🔄 Flujo Completo (One-Command)

### Windows (Batch Script):
Crea `run_sonar.bat`:
```batch
@echo off
cd /d "%~dp0"

echo ========== PASO 1: Ejecutar Tests ==========
python -m pip install -q pytest pytest-django pytest-cov coverage
pytest --cov=apps --cov-report=xml -q

echo ========== PASO 2: Enviar a SonarQube ==========
sonar-scanner -Dproject.settings=sonar-project.properties

echo ========== COMPLETO! ==========
echo Abre: http://localhost:9000
pause
```

**Ejecutar:**
```bash
run_sonar.bat
```

### Linux/Mac (Bash Script):
Crea `run_sonar.sh`:
```bash
#!/bin/bash

echo "========== PASO 1: Ejecutar Tests =========="
pip install -q pytest pytest-django pytest-cov coverage
pytest --cov=apps --cov-report=xml -q

echo "========== PASO 2: Enviar a SonarQube =========="
sonar-scanner -Dproject.settings=sonar-project.properties

echo "========== COMPLETO! =========="
echo "Abre: http://localhost:9000"
```

**Ejecutar:**
```bash
bash run_sonar.sh
```

---

## 📋 Checklist Completo

- [ ] SonarQube Scanner instalado
- [ ] SonarQube corriendo en http://localhost:9000
- [ ] Tests instalados: `pip install -r requirements.txt`
- [ ] Coverage generado: `coverage.xml` creado
- [ ] SonarQube Scanner ejecutado
- [ ] Dashboard visible en `http://localhost:9000`

---

## ⚠️ Problemas Comunes

### Error: "sonar-scanner no se encuentra"
**Solución:**
```bash
# Verifica instalación
sonar-scanner --version

# Si no existe, instala:
# Windows: choco install sonarqube-scanner
# Linux: wget + unzip desde docs.sonarsource.com
```

### Error: "No se puede conectar a SonarQube"
**Solución:**
```bash
# Verifica que SonarQube esté corriendo
curl http://localhost:9000

# Si no está, inicia:
# Windows: cd C:\sonarqube\bin && StartSonar.bat
# Linux: cd ~/sonarqube/bin && ./sonar.sh start
```

### Error: "coverage.xml no encontrado"
**Solución:**
```bash
# Asegúrate de ejecutar pytest CON cobertura
pytest --cov=apps --cov-report=xml -v
```

### Error: "Token inválido"
**Solución:**
```bash
# Regenera token en SonarQube:
# 1. http://localhost:9000 → Mi Cuenta → Tokens de Seguridad
# 2. Genera nuevo token
# 3. Actualiza sonar-project.properties
```

---

## 🎓 Entender los Reportes

### En Terminal (Después de pytest):
```
apps/users/models.py         85% (8 líneas sin cubrir)
apps/trips/models.py         72% (12 líneas sin cubrir)
apps/match/models.py         68% (7 líneas sin cubrir)
...
TOTAL                        71% ✅ (Meta alcanzada!)
```

### En SonarQube Dashboard:
- **Green** (✅): Cobertura > 80%
- **Yellow** (⚠️): Cobertura 70-80%
- **Red** (❌): Cobertura < 70%

---

## 💡 Tips Finales

1. **Ejecuta tests antes de cada commit:**
   ```bash
   pytest --cov=apps -q
   ```

2. **Genera reportes después de cambios:**
   ```bash
   sonar-scanner
   ```

3. **Automatiza con CI/CD:**
   - GitHub Actions
   - GitLab CI
   - Jenkins

4. **Mejora cobertura paso a paso:**
   - Identifica apps con < 70%
   - Escribe 5-10 tests nuevos
   - Re-ejecuta scanner

---

**¡Listo para ejecutar! 🚀**
