# 🧪 Scripts de Testing y Diagnóstico

Esta carpeta contiene herramientas para probar y diagnosticar la aplicación.

## 📁 Archivos Disponibles

### 🔍 **Diagnóstico y Verificación:**
- **`diagnose_slowness.py`** - Diagnostica problemas de rendimiento
- **`verify_docker_setup.py`** - Verifica que Docker esté listo para despliegue

### ⚡ **Testing de Rendimiento:**
- **`test_performance.py`** - Prueba rendimiento de API y base de datos
- **`test_entrada_material.py`** - Verifica funcionalidad de entrada de material

### 🏷️ **Testing de Funcionalidades:**
- **`test_categorias.py`** - Verifica gestión de categorías y subcategorías

## 🎯 Uso

### Antes del Despliegue:
```bash
# Verificar que todo esté listo para Docker
python tests/verify_docker_setup.py

# Diagnosticar problemas de rendimiento
python tests/diagnose_slowness.py
```

### Durante el Desarrollo:
```bash
# Probar rendimiento de la aplicación
python tests/test_performance.py

# Verificar entrada de material (después del fix)
python tests/test_entrada_material.py

# Probar gestión de categorías
python tests/test_categorias.py
```

## 📊 Qué Hacen los Tests

### `diagnose_slowness.py`:
- ✅ Verifica salud de la base de datos
- 📊 Analiza recursos del sistema
- 🔍 Revisa archivos de log
- ⚡ Simula operaciones problemáticas
- 📈 Compara rendimiento antes/después

### `verify_docker_setup.py`:
- 🐳 Verifica archivos Docker
- 📱 Confirma archivos de aplicación
- 📁 Revisa directorios necesarios
- 🐍 Valida dependencias Python
- 🗄️ Verifica base de datos
- 🔧 Confirma configuración Docker Compose

### `test_performance.py`:
- 🗄️ Prueba rendimiento de base de datos
- 🌐 Mide tiempo de respuesta de API
- ⚡ Simula actualización de stock
- 📊 Reporta métricas de rendimiento

### `test_categorias.py`:
- 🔍 Verifica estructura de base de datos
- 🧪 Prueba operaciones CRUD (crear, leer, actualizar, eliminar)
- 🌐 Verifica interfaz web y formularios
- 📊 Analiza consistencia de datos
- 🔗 Verifica relaciones categoría-subcategoría
- ✅ Confirma que las validaciones funcionan
- 🔍 Verifica productos sin stock
- 📦 Simula escenario: stock → 0 → re-agregar
- ✅ Confirma que el fix funciona
- 📋 Proporciona instrucciones de prueba manual

## 🚨 Cuándo Usar

### Antes de Desplegar:
1. `verify_docker_setup.py` - Siempre
2. `diagnose_slowness.py` - Si hay problemas de rendimiento

### Durante Desarrollo:
1. `test_performance.py` - Después de cambios importantes
2. `test_entrada_material.py` - Después de modificar inventario
3. `test_categorias.py` - Después de cambios en categorías

### Resolución de Problemas:
1. `diagnose_slowness.py` - Para lentitud
2. `test_performance.py` - Para problemas de API
3. `verify_docker_setup.py` - Para errores de despliegue

## 📋 Dependencias

Estos scripts requieren:
```bash
pip install psutil requests
```

## 🎯 Resultados Esperados

- **Base de datos**: Consultas < 50ms
- **API**: Respuestas < 500ms  
- **Actualizaciones**: < 200ms
- **Docker**: Todos los checks ✅

Si algún test falla, revisa los mensajes de error para identificar el problema específico.