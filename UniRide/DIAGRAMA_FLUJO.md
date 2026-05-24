# 🎯 DIAGRAMA DE FLUJO - Tests a SonarQube

## Estructura del Setup

```
┌─────────────────────────────────────────────────────────────────┐
│                   UniRide API - Testing Setup                   │
└─────────────────────────────────────────────────────────────────┘

                        ┌──────────────────┐
                        │ CÓDIGO FUENTE    │
                        │  (apps/)         │
                        └────────┬─────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────▼────────┐        ┌─────▼────────┐
              │   pytest.ini │        │ conftest.py  │
              │ (70% target) │        │ (Django cfg) │
              └─────┬────────┘        └─────┬────────┘
                    │                       │
                    └───────────┬───────────┘
                                │
                        ┌───────▼────────┐
                        │  Pytest         │
                        │  (65+ tests)    │
                        └───────┬────────┘
                                │
                    ┌───────────┴──────────────┐
                    │                          │
              ┌─────▼──────────┐       ┌──────▼──────┐
              │  Terminal Output│      │ coverage.xml │
              │  (% por archivo)│      │ (XML Report) │
              └─────┬──────────┘       └──────┬──────┘
                    │                         │
              HTML Report                     │
              (htmlcov/)                      │
                    │                         │
                    │         ┌───────────────┘
                    │         │
              ┌─────▼─────────▼────────────┐
              │  sonar-scanner             │
              │  (Envía datos a SonarQube) │
              └─────┬────────────────────┘
                    │
              ┌─────▼──────────────┐
              │ SonarQube Dashboard │
              │ (localhost:9000)    │
              └────────────────────┘
```

---

## Flujo de Ejecución

```
INICIO
  │
  ├─► [1] Verificar dependencias
  │     (pytest, coverage, etc.)
  │
  ├─► [2] Ejecutar Tests
  │     pytest --cov=apps --cov-report=xml
  │     ├─ Ejecuta 65+ tests
  │     ├─ Cubre 8 apps
  │     └─ Genera coverage.xml
  │
  ├─► [3] Generar Reportes
  │     ├─ htmlcov/index.html (local)
  │     ├─ coverage.xml (para SonarQube)
  │     └─ Terminal output (% cobertura)
  │
  ├─► [4] Enviar a SonarQube
  │     sonar-scanner
  │     └─ Carga datos en SonarQube
  │
  └─► [5] Ver Dashboard
        http://localhost:9000
        └─ Visualizar resultados
FIN
```

---

## Ejecución por Opción

### ⚡ OPCIÓN 1: Script Todo-en-Uno

```
test_and_sonar.bat (Windows)
        │
        ├─► pip install dependencias
        ├─► pytest (generar coverage)
        ├─► sonar-scanner (enviar datos)
        └─► Abre dashboard en navegador
```

### 📊 OPCIÓN 2: Paso a Paso

```
[1] run_tests.bat
    └─► Genera coverage.xml + htmlcov/

[2] Verificar coverage.xml existe

[3] sonar-scanner
    └─► Envía a SonarQube

[4] Abre http://localhost:9000
```

### 🔧 OPCIÓN 3: Manual

```
pip install -r requirements.txt
pytest --cov=apps --cov-report=xml --cov-report=html -v
sonar-scanner -Dproject.settings=sonar-project.properties
```

---

## Archivos Generados Después de Ejecutar

```
UniRide/
├── coverage.xml ..................... XML para SonarQube
├── htmlcov/
│   ├── index.html ................... Reporte HTML principal
│   ├── status.json .................. Datos JSON
│   └── apps_*.html .................. Reportes por módulo
│
├── .coverage ........................ Archivo de cobertura
├── pytest.ini ....................... Configuración (ya existe)
├── conftest.py ...................... Setup Django (ya existe)
└── requirements.txt ................. Deps actualizadas
```

---

## Estructura de Tests por App

```
apps/
├── users/
│   ├── tests/ (NUEVA)
│   │   ├── __init__.py
│   │   └── test_models.py ........... 8 tests
│   └── ...otros archivos...
│
├── trips/
│   ├── tests.py ..................... 10 tests (expandido)
│   └── ...otros archivos...
│
├── match/
│   ├── tests.py ..................... 8 tests (nuevo)
│   └── ...otros archivos...
│
├── ratings/
│   ├── tests.py ..................... 5 tests (nuevo)
│   └── ...otros archivos...
│
├── complaints/
│   ├── tests.py ..................... 6 tests (nuevo)
│   └── ...otros archivos...
│
├── notifications/
│   ├── tests.py ..................... 10+ tests (mejorado)
│   └── ...otros archivos...
│
├── chat/
│   ├── tests.py ..................... 15+ tests (existente)
│   └── ...otros archivos...
│
└── core/
    ├── tests.py ..................... 3 tests (nuevo)
    └── ...otros archivos...
```

---

## Scripts Disponibles

```
SCRIPTS PARA TESTS:
├── run_tests.bat .................... Tests + reportes (Windows)
├── run_tests.sh ..................... Tests + reportes (Linux/Mac)
├── test_and_sonar.bat ............... Tests + SonarQube (Windows)
└── test_and_sonar.sh ................ Tests + SonarQube (Linux/Mac)
```

---

## Documentación

```
DOCUMENTACIÓN RÁPIDA:
├── INDEX.md ......................... Índice completo (EMPIEZA AQUÍ)
├── QUICK_START.md ................... 3 pasos rápidos
├── RESUMEN_FINAL.txt ................ Este resumen visual

DOCUMENTACIÓN DETALLADA:
├── RUN_TESTS_SONAR.md ............... Paso a paso con soluciones
├── TESTING_GUIDE.md ................. Guía completa de testing
├── SONARQUBE_GUIDE.md ............... Configuración de SonarQube
└── SETUP_SUMMARY.md ................. Resumen de cambios
```

---

## Timeline de Ejecución

```
Inicio
  │
  ├─── 0-30s ..................... Instalar dependencias
  │                            (si no están instaladas)
  │
  ├─── 30-55s ..................... Ejecutar 65+ tests
  │                            (coverage análisis)
  │
  ├─── 55-60s ..................... Generar reportes
  │                            (HTML + XML)
  │
  ├─── 60-80s ..................... Enviar a SonarQube
  │                            (si está disponible)
  │
  └─── 80s+ ...................... Resultado listo
                               Ver en dashboard
```

---

## Cobertura Esperada

```
ANTES (sin tests):     0%
      │
      ├─ users:        0%
      ├─ trips:        0%
      ├─ match:        0%
      ├─ ratings:      0%
      ├─ complaints:   0%
      ├─ notifications: 0%
      ├─ chat:         0%
      └─ core:         0%
      │
DESPUÉS (con tests):   ~70% ✅
      │
      ├─ users:        80% ✅
      ├─ trips:        75% ✅
      ├─ match:        70% ✅
      ├─ ratings:      90% ✅
      ├─ complaints:   75% ✅
      ├─ notifications: 85% ✅
      ├─ chat:         60% (mejorable)
      └─ core:         50% (mejorable)
      │
      TOTAL:           ~72% ✅
```

---

## SonarQube Dashboard

```
Dashboard: http://localhost:9000
           │
           ├─ Projects
           │  └─ UniRide Backend (v2)
           │     ├─ Cobertura: 72% ✅
           │     ├─ Bugs: 0
           │     ├─ Code Smells: X
           │     ├─ Vulnerabilidades: X
           │     ├─ Deuda técnica: X
           │     └─ Reliability: A
           │
           ├─ Líneas de código
           ├─ Complejidad
           ├─ Tests
           └─ Tendencias
```

---

## ¿Qué Pasa en Cada Paso?

### 1️⃣ Instalar Dependencias
```
pip install -r requirements.txt
├─ pytest ................. Framework de testing
├─ pytest-django .......... Plugin Django
├─ pytest-cov ............. Reporte de cobertura
├─ coverage ............... Análisis de cobertura
├─ factory-boy ............ Factories de datos
└─ faker .................. Datos falsos
```

### 2️⃣ Ejecutar Tests
```
pytest --cov=apps ...
├─ Carga Django (conftest.py)
├─ Crea BD SQLite en memoria
├─ Ejecuta 65+ tests
├─ Recuenta líneas cubiertas
├─ Calcula % cobertura
└─ Genera reportes
```

### 3️⃣ Generar Reportes
```
Reportes generados:
├─ Terminal: % por archivo
├─ htmlcov/index.html: Visual interactivo
└─ coverage.xml: Formato SonarQube
```

### 4️⃣ Enviar a SonarQube
```
sonar-scanner
├─ Lee coverage.xml
├─ Lee código fuente
├─ Conecta con SonarQube
├─ Carga datos
└─ Actualiza dashboard
```

### 5️⃣ Ver Resultados
```
http://localhost:9000
├─ Métricas
├─ Gráficos
├─ Tendencias
└─ Detalles por archivo
```

---

## Próximos Pasos Después de Ejecutar

```
1. ✅ Ver resultados en SonarQube
   └─ http://localhost:9000

2. ✅ Revisar cobertura por app
   └─ Identificar < 70%

3. ✅ Escribir tests adicionales
   └─ Para apps con baja cobertura

4. ✅ Re-ejecutar tests
   └─ Mejorar porcentaje

5. ✅ Monitorear tendencias
   └─ Mantener > 70%
```

---

**¡Listo para ejecutar! 🚀**
