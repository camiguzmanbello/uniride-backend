# UniRide API - Testing & Code Coverage Guide

## Objetivo
Alcanzar **70% de cobertura de tests** para el API UniRide usando **pytest** y **SonarQube**.

## Estructura de Tests

Se han creado tests para las siguientes apps:

```
apps/
├── users/
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_models.py (nuevos tests)
│   └── tests.py (existentes)
├── trips/
│   └── tests.py (tests expandidos)
├── match/
│   └── tests.py (tests nuevos)
├── ratings/
│   └── tests.py (tests nuevos)
├── complaints/
│   └── tests.py (tests nuevos)
├── notifications/
│   └── tests.py (tests existentes)
├── chat/
│   └── tests.py (tests existentes)
└── core/
    └── tests.py (tests básicos)
```

## Dependencias Instaladas

Las siguientes dependencias se han agregado a `requirements.txt`:

- **pytest==8.0.0** - Framework de testing
- **pytest-django==4.7.0** - Plugin de Django para pytest
- **pytest-cov==5.0.0** - Plugin de cobertura para pytest
- **coverage==7.4.0** - Herramienta de cobertura de código
- **factory-boy==3.3.0** - Factories para crear datos de prueba
- **faker==22.5.0** - Generador de datos falsos

## Configuración

### pytest.ini
Archivo de configuración de pytest con las siguientes opciones:
- Módulo de Django: `UniRide.settings`
- Cobertura mínima requerida: 70%
- Reportes: HTML, terminal con líneas faltantes, XML (para SonarQube)

### conftest.py
Archivo de configuración de pytest que:
- Configura Django antes de ejecutar los tests
- Establece la base de datos SQLite en memoria para tests rápidos
- Registra todas las apps

## Ejecución de Tests

### Opción 1: Script Batch (Windows)
```bash
run_tests.bat
```

### Opción 2: Script Bash (Linux/Mac)
```bash
bash run_tests.sh
```

### Opción 3: Comando Manual
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar tests con cobertura
pytest --cov=apps --cov-report=html --cov-report=term-missing --cov-report=xml -v
```

## Interpretación de Resultados

Después de ejecutar los tests, verás:

1. **Salida en Terminal**:
   - Lista de tests ejecutados
   - Líneas no cubiertas por cada archivo
   - Porcentaje total de cobertura

2. **Reporte HTML**:
   - Ubicación: `htmlcov/index.html`
   - Abre en navegador para ver detalles visuales de cobertura
   - Identifica qué líneas de código necesitan tests

3. **Reporte XML**:
   - Ubicación: `coverage.xml`
   - Usado por SonarQube para análisis

## Tests Creados

### Users App
- ✅ Modelo `Role`: creación y unicidad
- ✅ Modelo `User`: creación, unicidad de email/teléfono, autenticación
- ✅ Modelo `PendingUser`: creación
- ✅ Autenticación: contraseñas, estados

### Trips App
- ✅ Modelo `PublicationType`: creación
- ✅ Modelo `Publication`: creación, relaciones
- ✅ Modelo `TripStatus`: creación
- ✅ Modelo `Trip`: creación, relaciones

### Match App
- ✅ Modelo `Route`: creación, direcciones
- ✅ Modelo `RoutePoint`: creación, ordenamiento
- ✅ Modelo `PublicationRoute`: relaciones
- ✅ Modelo `MatchSuggestion`: creación, scoring, constraints

### Ratings App
- ✅ Modelo `Rating`: creación, validación de estrellas, constraints

### Complaints App
- ✅ Modelo `ComplaintType`: creación
- ✅ Modelo `ComplaintStatus`: creación
- ✅ Modelo `Complaint`: creación, relaciones

### Notifications App
- ✅ Modelo `Notification`: creación, lectura
- ✅ Modelo `UserDevice`: creación, tokens

### Chat App
- ✅ Modelos de Chat y Message (tests existentes)
- ✅ Notificaciones en tiempo real
- ✅ Manejo de errores

### Core App
- ✅ Tests básicos de importación

## Mejoramiento Continuo

Para aumentar la cobertura por encima del 70%:

1. **Adicionar tests de vistas**:
   ```python
   class TestUserViews(APITestCase):
       def test_get_user_list(self):
           # Test GET /api/users/
   ```

2. **Adicionar tests de serializers**:
   ```python
   def test_user_serializer_validation(self):
       # Test validación de serializers
   ```

3. **Adicionar tests de servicios**:
   - Métodos de lógica de negocio
   - Cálculos de matching
   - Validaciones complejas

4. **Adicionar tests de permisos**:
   - Acceso no autorizado
   - Roles y permisos

## Integración con SonarQube

El proyecto ya tiene `sonar-project.properties` configurado. Para analizar:

```bash
sonar-scanner
```

Los reportes de cobertura se subirán automáticamente.

## Notas

- Tests usan **SQLite en memoria** para velocidad
- Cada test es **independiente** (usa `setUp`)
- Tests usan **pytest** como framework principal
- Compatible con **SonarQube** via `coverage.xml`
- Se pueden ejecutar tests individuales:
  ```bash
  pytest apps/users/tests/test_models.py::TestUserModel::test_create_user -v
  ```

## Próximos Pasos

1. Ejecutar `run_tests.bat` o `run_tests.sh`
2. Revisar el reporte HTML en `htmlcov/index.html`
3. Identificar áreas con baja cobertura
4. Escribir tests adicionales según sea necesario
5. Ejecutar SonarQube para análisis completo

---
*Última actualización: 2026-05-20*
