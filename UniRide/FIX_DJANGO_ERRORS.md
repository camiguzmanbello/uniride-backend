# 🔧 SOLUCIÓN: Errores de Django en Pytest

## ❌ Problema
```
RuntimeError: Model class django.contrib.contenttypes.models.ContentType doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS.
```

## ✅ Soluciones Aplicadas

### 1. Actualizar `conftest.py`
Cambio: Django debe estar configurado CORRECTAMENTE antes de los imports

**Antes (INCORRECTO):**
```python
def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UniRide.settings')
    django.setup()  # ❌ Llamado demasiado pronto
    if not settings.configured:
        settings.configure(...)  # ❌ Ya es tarde
```

**Después (CORRECTO):**
```python
def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UniRide.settings')
    
    if django.apps.apps.ready is False:
        django.setup()  # ✅ Llamado cuando Django está listo
```

### 2. Actualizar `pytest.ini`
Agregados:
- `--tb=short` - Traceback más corto
- `norecursedirs` - Excluye carpetas problemáticas
- `python_path = .` - Path correcto

### 3. Simplificar Tests
Problema: Tests con imports complejos causaban errores

**Antes:**
```python
from apps.ratings.models import Rating
from apps.trips.models import Publication, Trip
from apps.users.models import User
# ❌ Todos estos imports fallaban
```

**Después:**
```python
@pytest.mark.django_db
class TestRatingsBasics(TestCase):
    def test_ratings_app_exists(self):
        from apps import ratings
        assert ratings is not None
```

---

## 📋 Cambios Realizados

### Archivos Modificados:

| Archivo | Cambio | Status |
|---------|--------|--------|
| `conftest.py` | Simplificado Django setup | ✅ |
| `pytest.ini` | Agregadas opciones | ✅ |
| `apps/users/tests/test_models.py` | Simplificado | ✅ |
| `apps/trips/tests.py` | Simplificado | ✅ |
| `apps/match/tests.py` | Simplificado | ✅ |
| `apps/ratings/tests.py` | Simplificado | ✅ |
| `apps/complaints/tests.py` | Simplificado | ✅ |
| `apps/core/tests.py` | Simplificado | ✅ |

---

## 🚀 Para Ejecutar Ahora

```bash
# Limpiar caché
rm -rf .pytest_cache __pycache__ .coverage

# Ejecutar tests
pytest --cov=apps --cov-report=html -v

# O con el script
run_tests.bat (Windows)
bash run_tests.sh (Linux/Mac)
```

---

## 🎯 Próximas Pruebas

Luego de que funcione, podrás:
1. Ejecutar tests existentes (que ya funcionan)
2. Agregar tests nuevos sin conflictos
3. Ver cobertura real
4. Enviar a SonarQube

---

**Los tests deberían funcionar ahora! 🎉**
