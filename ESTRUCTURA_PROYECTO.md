# 📁 Estructura del Proyecto

## 🏗️ Organización de Directorios

```
inventario-refacciones/
├── 📱 app.py                    # Aplicación principal Flask
├── 📋 requirements.txt         # Dependencias Python
├── 🐳 Dockerfile              # Configuración Docker
├── 🐳 docker-compose.yml      # Orquestación Docker
├── 🐳 docker-compose.dev.yml  # Desarrollo Docker
├── 🔧 iniciar_app.bat         # Script inicio Windows
├── 🗄️ inventario.db           # Base de datos principal
│
├── 📂 config/                  # Configuración
│   ├── config.py              # Configuración Flask
│   └── nginx.conf             # Configuración Nginx
│
├── 📂 data/                    # Datos y backups
│   ├── *.csv                  # Archivos de datos
│   └── *backup*.db            # Backups de base de datos
│
├── 📂 docs/                    # Documentación
│   ├── README.md              # Documentación principal
│   ├── DEPLOYMENT_CHECKLIST.md
│   ├── DOCKER_DEPLOYMENT.md
│   └── *.md                   # Otros documentos
│
├── 📂 imagenes/               # Imágenes de productos
│   └── [ID].jpg              # Imágenes por ID de producto
│
├── 📂 logs/                   # Archivos de log
│   └── *.log                 # Logs de la aplicación
│
├── 📂 migrations/             # Scripts de migración
│   ├── migrar_*.py           # Scripts de migración DB
│   ├── comparar_bases_datos.py
│   └── importar_datos.py
│
├── 📂 scripts/                # Scripts de despliegue
│   ├── deploy_*.sh           # Scripts Linux
│   ├── deploy_*.bat          # Scripts Windows
│   └── docker_management.*   # Gestión Docker
│
├── 📂 static/                 # Archivos estáticos web
│   └── style.css             # Estilos CSS
│
├── 📂 templates/              # Plantillas HTML
│   ├── base.html             # Plantilla base
│   ├── *.html                # Plantillas específicas
│   └── *_form.html           # Formularios
│
├── 📂 tests/                  # Pruebas
│   ├── test_*.py             # Scripts de prueba
│   └── README.md             # Documentación de pruebas
│
└── 📂 tools/                  # Herramientas adicionales
    └── README.md             # Documentación de herramientas
```

## 🚀 Comandos Principales

### Desarrollo
```bash
python app.py                    # Ejecutar en desarrollo
./scripts/docker_management.sh  # Gestión Docker (Linux)
scripts/docker_management.bat   # Gestión Docker (Windows)
```

### Migración
```bash
python migrations/migrar_*.py   # Scripts de migración
python migrations/comparar_bases_datos.py  # Comparar DBs
```

### Pruebas
```bash
python tests/test_*.py          # Ejecutar pruebas específicas
```

## 📋 Archivos Principales

- **`app.py`**: Aplicación Flask principal
- **`inventario.db`**: Base de datos SQLite
- **`requirements.txt`**: Dependencias Python
- **`Dockerfile`**: Configuración contenedor
- **`docker-compose.yml`**: Orquestación producción

## 🔧 Configuración

La configuración se encuentra en `config/config.py` y variables de entorno en `.env`.

## 📚 Documentación

Toda la documentación está organizada en la carpeta `docs/`.
