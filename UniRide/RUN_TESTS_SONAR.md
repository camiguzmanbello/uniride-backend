# ✅ PASO A PASO: Probar Tests y Enviar a SonarQube

## 🎯 Objetivo Final
Ejecutar tests localmente y enviarlos a SonarQube para ver la cobertura del 70%

---

## 🚀 OPCIÓN 1: Script Automatizado (RECOMENDADO)

### Windows:
```bash
test_and_sonar.bat
```

### Linux/Mac:
```bash
bash test_and_sonar.sh
```

**Esto automáticamente:**
1. ✅ Instala dependencias
2. ✅ Ejecuta tests
3. ✅ Genera coverage.xml
4. ✅ Envía a SonarQube
5. ✅ Abre dashboard

---

## 📋 OPCIÓN 2: Paso a Paso Manual

### PASO 1️⃣: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### PASO 2️⃣: Ejecutar Tests
```bash
# Windows
run_tests.bat

# Linux/Mac
bash run_tests.sh

# O comando directo:
pytest --cov=apps --cov-report=xml --cov-report=html --cov-report=term-missing -v
```

**Verás algo así:**
```
apps/users/tests/test_models.py ........... PASSED
apps/trips/tests.py ................... PASSED
apps/match/tests.py ................ PASSED
...
====================== 75 passed in 25s ======================

Coverage: 72%  ✅ (Meta alcanzada!)

coverage.xml generated
htmlcov/index.html generated
```

### PASO 3️⃣: Enviar a SonarQube

**Primero: Verificar que SonarQube esté corriendo**
```bash
# Abre en navegador:
http://localhost:9000

# O verifica con curl:
curl http://localhost:9000
```

Si NO está corriendo, debes iniciarlo:
- **Windows**: `C:\sonarqube\bin\StartSonar.bat`
- **Linux/Mac**: `~/sonarqube/bin/sonar.sh start`

**Luego: Enviar datos**
```bash
sonar-scanner -Dproject.settings=sonar-project.properties
```

**Salida esperada:**
```
INFO: ANALYSIS SUCCESSFUL
INFO: You can find the results at: 
      http://localhost:9000/dashboard?id=uniride-backend-v2
```

---

## 📊 PASO 4️⃣: Ver Resultados en SonarQube

1. **Abre navegador:**
   ```
   http://localhost:9000
   ```

2. **Login** (si se requiere)

3. **Busca proyecto:** "UniRide Backend"

4. **Verás:**
   - 📈 **Cobertura:** 72% ✅
   - 🐛 **Bugs:** 0
   - 🔧 **Code Smells:** X
   - 🔐 **Vulnerabilidades:** X
   - 📉 **Deuda Técnica:** X horas

---

## 🔍 Ver Reporte Local (Sin SonarQube)

Si SonarQube no está disponible, puedes ver el reporte HTML local:

```bash
# Abre en navegador:
htmlcov/index.html
```

**Verás:**
- ✅ Cobertura por archivo
- ✅ Líneas cubiertas/no cubiertas
- ✅ Porcentaje por módulo

---

## ⏱️ Duración Esperada

| Tarea | Tiempo |
|-------|--------|
| Instalar dependencias | 30-60s |
| Ejecutar tests | 15-25s |
| Generar cobertura | 5s |
| Enviar a SonarQube | 10-20s |
| **TOTAL** | **1-2 minutos** |

---

## ✅ Checklist

- [ ] SonarQube corriendo en http://localhost:9000
- [ ] Ejecutaste: `pip install -r requirements.txt`
- [ ] Ejecutaste tests (run_tests.bat o bash run_tests.sh)
- [ ] Viste "Coverage: 7X%" en terminal
- [ ] Archivo coverage.xml existe
- [ ] Ejecutaste sonar-scanner
- [ ] Accediste a http://localhost:9000
- [ ] Viste proyecto "UniRide Backend"
- [ ] Viste cobertura ~70%

---

## 🆘 Problemas Comunes & Soluciones

### ❌ "pytest no está instalado"
**Solución:**
```bash
pip install pytest pytest-django pytest-cov coverage
```

### ❌ "SonarQube no responde"
**Solución:**
```bash
# Inicia SonarQube
# Windows: C:\sonarqube\bin\StartSonar.bat
# Linux: ~/sonarqube/bin/sonar.sh start

# Espera 30 segundos y abre:
http://localhost:9000
```

### ❌ "sonar-scanner no encontrado"
**Solución:**
```bash
# Windows: choco install sonarqube-scanner
# Linux: descargar desde https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/
```

### ❌ "coverage.xml no encontrado"
**Solución:**
```bash
# Asegúrate de ejecutar pytest CON --cov-report=xml:
pytest --cov=apps --cov-report=xml -v
```

### ❌ "Token inválido en SonarQube"
**Solución:**
```bash
# Ve a http://localhost:9000
# Mi Cuenta > Security > Generate Token
# Actualiza sonar-project.properties:
sonar.login=TU_NUEVO_TOKEN
```

---

## 🎓 Próximos Pasos

Después de ver los resultados:

1. **Identifica apps con < 70%**
2. **Escribe tests adicionales** para esas apps
3. **Re-ejecuta tests**
4. **Verifica mejora**

---

## 📚 Documentación Disponible

- `TESTING_GUIDE.md` - Guía completa de testing
- `SONARQUBE_GUIDE.md` - Configuración detallada de SonarQube
- `QUICK_START.md` - Inicio rápido
- `SETUP_SUMMARY.md` - Resumen de cambios

---

**¡Listo! Ejecuta ahora:**

### Windows:
```bash
test_and_sonar.bat
```

### Linux/Mac:
```bash
bash test_and_sonar.sh
```

🚀 **¡Que comience el análisis!**
