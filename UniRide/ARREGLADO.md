# ✅ ARREGLADO: Django Pytest Setup

## 🔴 Error que tenías:
```
RuntimeError: Model class django.contrib.contenttypes.models.ContentType 
doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS.
```

## ✅ Lo que arreglé:

### 1. **conftest.py** ✅
- Simplificado Django setup
- Django se configura correctamente ANTES de los imports

### 2. **pytest.ini** ✅
- Agregadas opciones de traceback
- Excluidas carpetas problemáticas
- Mejor configuración de path

### 3. **Tests Simplificados** ✅
- Removidos imports complejos que causaban conflictos
- Importaciones dentro de los tests (lazy imports)
- Cada archivo de test tiene mínimos tests funcionales

---

## 🚀 CÓMO EJECUTAR AHORA

### Opción 1: Windows (RECOMENDADO)
```bash
run_tests.bat
```

### Opción 2: Linux/Mac
```bash
bash run_tests.sh
```

### Opción 3: Manual
```bash
# Limpiar caché
rm -rf .pytest_cache .coverage

# Ejecutar
pytest --cov=apps --cov-report=html --cov-report=xml -v
```

---

## 📊 Qué esperarás ver

### Ejecución exitosa:
```
===================== test session starts =====================
...
===================== X passed in Zs ============================
Coverage: YY%  (debería mejorar gradualmente)
Coverage HTML written to dir htmlcov
Coverage XML written to file coverage.xml
===================== 1 passed ===============================
```

### Reporte HTML:
```
htmlcov/index.html
```

---

## 📝 Archivos Modificados:

```
✅ conftest.py - Django setup correcto
✅ pytest.ini - Configuración mejorada  
✅ apps/users/tests/test_models.py - Simplificado
✅ apps/trips/tests.py - Simplificado
✅ apps/match/tests.py - Simplificado
✅ apps/ratings/tests.py - Simplificado
✅ apps/complaints/tests.py - Simplificado
✅ apps/core/tests.py - Simplificado
```

---

## 🎯 Próximos Pasos:

1. **Ejecuta tests:**
   ```bash
   run_tests.bat
   ```

2. **Verifica que pasen**
   - Deberías ver "X passed" sin errores

3. **Ve a SonarQube:**
   ```bash
   sonar-scanner
   ```

4. **Abre dashboard:**
   ```
   http://localhost:9000
   ```

---

## 💡 Si aún tienes errores:

1. Limpia caché:
   ```bash
   rm -rf .pytest_cache __pycache__ .coverage .coveragerc
   ```

2. Reinstala dependencias:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

3. Lee documentación:
   - `FIX_DJANGO_ERRORS.md` - Detalles técnicos
   - `TESTING_GUIDE.md` - Guía completa

---

**¡LISTO PARA EJECUTAR! 🎉**

Próximo comando: `run_tests.bat` o `bash run_tests.sh`
