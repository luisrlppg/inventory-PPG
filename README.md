# 🏭 Sistema de Inventario PPG

Sistema completo de gestión de inventario desarrollado en Flask con interfaz web moderna y funcionalidades avanzadas.

## 🚀 Inicio Rápido

### Desarrollo Local
```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python app.py
```

### Producción con Docker
```bash
# Gestión completa con menú interactivo
./scripts/docker_management.sh  # Linux
scripts\docker_management.bat   # Windows

# O comandos directos
docker compose --profile production up -d --build
```

## 📋 Funcionalidades

### ✅ Gestión Completa
- **🏢 Proveedores**: CRUD completo con información de contacto
- **📦 Productos**: Gestión con categorías, subcategorías y máquinas
- **📊 Inventario**: Control de stock por ubicaciones
- **🏭 Máquinas**: Relación muchos-a-muchos con productos
- **📋 Categorías**: Sistema jerárquico de clasificación
- **📍 Ubicaciones**: Gestión de almacenes y ubicaciones
- **📧 Alertas de Stock**: Sistema automático de notificaciones por correo

### 🔧 Características Técnicas
- **🔐 Sistema de Administración**: Login seguro con logs de auditoría
- **📤 Exportación CSV**: Para todos los módulos con filtros
- **🔍 Búsqueda Avanzada**: Filtros múltiples en tiempo real
- **📱 Interfaz Responsiva**: Bootstrap 5 con diseño moderno
- **🗄️ Base de Datos**: SQLite optimizada con índices
- **🐳 Docker**: Contenedorización completa con Nginx
- **📧 Correo Electrónico**: Alertas automáticas de stock bajo

## 📁 Estructura del Proyecto

```
inventario-refacciones/
├── 📱 app.py                    # Aplicación principal
├── 🗄️ inventario.db            # Base de datos
├── 📋 requirements.txt         # Dependencias
├── 🐳 Dockerfile              # Configuración Docker
│
├── 📂 config/                  # Configuración
├── 📂 data/                    # Datos y backups
├── 📂 docs/                    # Documentación completa
├── 📂 migrations/              # Scripts de migración
├── 📂 scripts/                 # Scripts de despliegue
├── 📂 static/                  # CSS y archivos web
├── 📂 templates/               # Plantillas HTML
└── 📂 tests/                   # Pruebas automatizadas
```

## 🔑 Credenciales por Defecto

- **Usuario**: `admin`
- **Contraseña**: `admin123`

⚠️ **Importante**: Cambiar credenciales en producción

## 📚 Documentación

La documentación completa está en [`docs/`](docs/):

- 📖 [README Completo](docs/README.md)
- 🚀 [Guía de Despliegue](docs/DEPLOYMENT_CHECKLIST.md)
- 🐳 [Docker Setup](docs/DOCKER_DEPLOYMENT.md)
- 🔄 [Migración Completada](docs/MIGRACION_PRODUCCION_COMPLETADA.md)
- 🏢 [Sistema de Proveedores](docs/SUPPLIERS_SYSTEM_COMPLETED.md)
- 📧 [Sistema de Alertas de Stock](docs/SISTEMA_ALERTAS_STOCK.md)

### 🆕 Guías Rápidas
- ⚡ [Guía Rápida de Alertas](docs/GUIA_RAPIDA_ALERTAS.md)
- 📧 [Configurar Gmail](docs/CONFIGURAR_GMAIL.md)
- 📋 [Implementación Completada](docs/IMPLEMENTACION_ALERTAS_COMPLETADA.md)
- 🔧 [Ejemplo de Configuración de Correo](config/correo_ejemplo.env)

## 🧪 Pruebas

```bash
# Ejecutar pruebas específicas
python tests/test_proveedores.py
python tests/test_maquinas.py
python tests/test_categorias.py

# Pruebas de rendimiento
python tests/test_performance.py
```

## 🔄 Migración de Datos

Si tienes datos existentes:

```bash
# Comparar bases de datos
python migrations/comparar_bases_datos.py

# Migración completa
python migrations/migrar_produccion_completa.py

# Intercambio seguro
python migrations/intercambiar_base_datos.py
```

## 🌐 Acceso

- **Desarrollo**: http://localhost:5000
- **Producción**: http://localhost (con Nginx)
- **Admin**: http://localhost/admin/login

## 🛠️ Tecnologías

- **Backend**: Flask (Python 3.12)
- **Frontend**: Bootstrap 5 + JavaScript
- **Base de Datos**: SQLite con optimizaciones
- **Contenedores**: Docker + Docker Compose
- **Proxy**: Nginx (producción)

## 📊 Estado del Proyecto

- ✅ **Funcional al 100%**
- ✅ **Datos de producción migrados**
- ✅ **Todas las pruebas pasando**
- ✅ **Listo para despliegue**

---

**Desarrollado para PPG** | **Sistema de Inventario Completo** 🏭