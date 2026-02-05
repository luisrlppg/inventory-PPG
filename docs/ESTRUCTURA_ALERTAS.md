# 📁 Estructura del Sistema de Alertas de Stock

## 🗂️ Organización de Archivos

### 📂 Backend (Python)
```
app.py                                    # Funciones principales de alertas
├── get_productos_stock_bajo()           # Detecta productos con stock bajo
├── enviar_alerta_stock_bajo()           # Envía correos de alerta
├── generar_html_alerta_stock()          # Genera contenido HTML
├── generar_texto_alerta_stock()         # Genera contenido texto
└── verificar_y_enviar_alertas_stock()   # Verificación automática

config/
├── config.py                            # Configuración de correo y alertas
└── correo_ejemplo.env                   # Ejemplos de configuración SMTP
```

### 🎨 Frontend (Templates)
```
templates/
├── admin_stock_alerts.html              # Panel principal de alertas
├── base.html                            # Menú con enlace a alertas
├── productos.html                       # Columna de stock mínimo
└── producto_form.html                   # Campo de stock mínimo
```

### 🗄️ Base de Datos
```
migrations/
└── agregar_stock_minimo.py              # Migración para agregar campo

inventario.db
└── productos
    └── stock_minimo (INTEGER)           # Nuevo campo agregado
```

### 🧪 Pruebas y Ejemplos
```
tests/
├── test_stock_alerts.py                 # Suite completa de pruebas
└── ejemplos_alertas/
    ├── alerta_ejemplo.html              # Ejemplo de correo HTML
    └── alerta_ejemplo.txt               # Ejemplo de correo texto
```

### 🔧 Scripts de Utilidad
```
scripts/
└── configurar_demo_alertas.py           # Configurador de demostración
```

### 📚 Documentación
```
docs/
├── SISTEMA_ALERTAS_STOCK.md             # Documentación completa
├── GUIA_RAPIDA_ALERTAS.md               # Guía de inicio rápido
├── CONFIGURAR_GMAIL.md                  # Guía paso a paso Gmail
└── IMPLEMENTACION_ALERTAS_COMPLETADA.md # Resumen de implementación
```

### ⚙️ Configuración
```
.env.example                             # Variables de entorno de ejemplo
config/correo_ejemplo.env                # Ejemplos específicos de correo
```

### 📊 Datos
```
data/
├── inventario_backup_*.db               # Backups automáticos
└── [otros backups]
```

## 🔗 Flujo de Funcionamiento

### 1. Detección de Stock Bajo
```
productos (tabla)
    ↓
get_productos_stock_bajo()
    ↓
Compara: stock_actual ≤ stock_minimo
    ↓
Lista de productos con stock bajo
```

### 2. Generación de Alerta
```
Lista de productos
    ↓
generar_html_alerta_stock()
    ↓
Correo HTML profesional
    +
generar_texto_alerta_stock()
    ↓
Correo texto plano
```

### 3. Envío de Correo
```
Flask-Mail
    ↓
SMTP Server (Gmail/Outlook/etc)
    ↓
Destinatarios configurados
    ↓
Log de operación
```

### 4. Interfaz de Usuario
```
/admin/stock-alerts
    ↓
Dashboard con estado
    ↓
Lista de productos
    ↓
Acciones:
├── Enviar alerta manual
├── Probar correo
├── Editar stock mínimo
└── Ver historial
```

## 📋 Rutas Implementadas

### Rutas de Administración
```
GET  /admin/stock-alerts              # Panel principal
POST /admin/send-stock-alert          # Enviar alerta manual
POST /admin/test-email                # Probar configuración
```

### API REST
```
PUT  /api/productos/<id>/stock-minimo # Actualizar stock mínimo
```

## 🔧 Variables de Entorno

### Configuración de Correo
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=contraseña-de-aplicacion
MAIL_DEFAULT_SENDER=tu-email@gmail.com
```

### Configuración de Alertas
```bash
STOCK_ALERT_ENABLED=true
STOCK_ALERT_RECIPIENTS=admin@empresa.com,gerente@empresa.com
STOCK_ALERT_FREQUENCY_HOURS=24
```

## 📊 Estructura de Datos

### Tabla: productos
```sql
CREATE TABLE productos (
    id INTEGER PRIMARY KEY,
    descripcion TEXT,
    codigo TEXT,
    stock_minimo INTEGER DEFAULT 5,  -- ← NUEVO CAMPO
    -- ... otros campos
);
```

### Tabla: operation_logs
```sql
-- Registra todas las operaciones de alertas
operation_type = 'STOCK_ALERT'
operation_type = 'EMAIL_TEST'
operation_type = 'STOCK_MINIMO_UPDATE'
```

## 🎯 Puntos de Entrada

### Para Usuarios
1. **Panel Web**: `/admin/stock-alerts`
2. **Formulario de Productos**: Campo "Stock Mínimo"
3. **Lista de Productos**: Columna "Stock Mín."

### Para Desarrolladores
1. **Funciones Python**: `app.py`
2. **API REST**: `/api/productos/<id>/stock-minimo`
3. **Scripts**: `scripts/configurar_demo_alertas.py`
4. **Pruebas**: `tests/test_stock_alerts.py`

### Para Administradores
1. **Configuración**: `.env`
2. **Logs**: `logs/admin_operations.log`
3. **Base de datos**: `inventario.db`

## 📦 Dependencias

### Python Packages
```
Flask==3.1.2
Flask-Mail==0.9.1
```

### Servicios Externos
- SMTP Server (Gmail, Outlook, Yahoo, etc.)
- Servidor de correo configurado

## 🔍 Archivos Clave

### Más Importantes
1. `app.py` - Lógica principal (500+ líneas)
2. `templates/admin_stock_alerts.html` - Interfaz (400+ líneas)
3. `docs/SISTEMA_ALERTAS_STOCK.md` - Documentación completa

### Configuración
1. `.env` - Variables de entorno (usuario debe crear)
2. `config/config.py` - Configuración de aplicación
3. `config/correo_ejemplo.env` - Ejemplos

### Utilidades
1. `tests/test_stock_alerts.py` - Pruebas
2. `scripts/configurar_demo_alertas.py` - Demo
3. `migrations/agregar_stock_minimo.py` - Migración

## 🚀 Comandos Útiles

### Desarrollo
```bash
# Ejecutar pruebas
python tests/test_stock_alerts.py

# Configurar demo
python scripts/configurar_demo_alertas.py

# Iniciar aplicación
python app.py
```

### Mantenimiento
```bash
# Ver logs
type logs\admin_operations.log

# Backup de base de datos
copy inventario.db data\backup_$(date).db

# Verificar configuración
python -c "from app import app; print(app.config['MAIL_SERVER'])"
```

## 📈 Métricas del Sistema

### Archivos Creados
- **Backend**: 1 archivo principal modificado
- **Frontend**: 4 templates modificados/creados
- **Documentación**: 4 archivos nuevos
- **Pruebas**: 1 suite completa
- **Scripts**: 1 utilidad
- **Migración**: 1 script
- **Total**: ~2,800 líneas de código

### Funcionalidades
- **Rutas**: 3 nuevas rutas de admin
- **API**: 1 endpoint REST
- **Funciones**: 6 funciones principales
- **Templates**: 1 template completo nuevo
- **Campos BD**: 1 campo nuevo

---

**Sistema de Inventario PPG** | **Alertas de Stock Automatizadas** 📧