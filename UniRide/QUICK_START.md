# 🚀 INSTRUCCIONES RÁPIDAS - Setup de Tests 70% Cobertura

## En 3 Pasos:

### 1️⃣ Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2️⃣ Ejecutar Tests
**Windows:**
```bash
run_tests.bat
```

**Linux/Mac:**
```bash
bash run_tests.sh
```

**Comando directo (cualquier SO):**
```bash
pytest --cov=apps --cov-report=html --cov-report=term-missing -v
```

### 3️⃣ Ver Resultados
- **Navegador**: Abre `htmlcov/index.html`
- **Terminal**: Salida con % de cobertura
- **SonarQube**: Lee `coverage.xml`

---

## ✅ Qué se ha hecho:

| Tarea | Estado |
|-------|--------|
| Instalar pytest, coverage, etc. | ✅ |
| Crear pytest.ini y conftest.py | ✅ |
| Tests para Users | ✅ |
| Tests para Trips | ✅ |
| Tests para Match | ✅ |
| Tests para Ratings | ✅ |
| Tests para Complaints | ✅ |
| Tests para Notifications | ✅ |
| Tests para Chat | ✅ |
| Tests para Core | ✅ |
| Documentación completa | ✅ |

---

## 📦 Carpetas de Tests Creadas/Expandidas:

- `apps/users/tests/` - Nueva carpeta con test_models.py
- `apps/trips/tests.py` - Expandido con modelos
- `apps/match/tests.py` - Nuevos tests
- `apps/ratings/tests.py` - Nuevos tests
- `apps/complaints/tests.py` - Nuevos tests
- `apps/core/tests.py` - Nuevos tests

---

## 🎯 Meta: 70% Cobertura

Todos los tests están diseñados para:
- ✅ Cubrir lógica principal de modelos
- ✅ Probar relaciones entre tablas
- ✅ Validar constraints únicos
- ✅ Soportar SonarQube automáticamente

---

**¡Todo listo! Ejecuta los tests ahora 🎉**
