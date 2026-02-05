# 📧 Sistema de Alertas de Stock Bajo

Sistema completo de notificaciones automáticas por correo electrónico para productos con stock por debajo del mínimo configurado.

## 🚀 Características Principales

### ✅ Funcionalidades Implementadas
- **Detección Automática**: Identifica productos con stock ≤ stock mínimo
- **Correos HTML**: Reportes profesionales con formato HTML y texto plano
- **Configuración Flexible**: Variables de entorno para fácil configuración
- **Interfaz de Administración**: Panel web completo para gestionar alertas
- **Historial de Alertas**: Registro de todas las alertas enviadas
- **Pruebas de Correo**: Función para verificar configuración
- **Edición Inline**: Modificar stock mínimo directamente desde la interfaz
- **Múltiples Destinatarios**: Envío a varios emails simultáneamente
- **Frecuencia Configurable**: Control de intervalos entre alertas

## 📋 Configuración

### 1. Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```bash
# Configuración de correo
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-contraseña-de-aplicacion
MAIL_DEFAULT_SENDER=tu-email@gmail.com

# Configuración de alertas
STOCK_ALERT_ENABLED=true
STOCK_ALERT_RECIPIENTS=admin@empresa.com,gerente@empresa.com,almacen@empresa.com
STOCK_ALERT_FREQUENCY_HOURS=24
```

### 2. Configuración de Gmail

Para usar Gmail necesitas una **contraseña de aplicación**:

1. Ir a [Google Account Security](https://myaccount.google.com/security)
2. Activar verificación en 2 pasos
3. Generar contraseña de aplicación
4. Usar esa contraseña de 16 caracteres (no tu contraseña normal)

### 3. Otros Proveedores

**Outlook/Hotmail:**
```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
```

**Yahoo:**
```bash
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=true
```

## 🎯 Uso del Sistema

### Acceso a la Interfaz

1. **Login de Administrador**: `/admin/login`
   - Usuario: `admin`
   - Contraseña: `admin123`

2. **Panel de Alertas**: `/admin/stock-alerts`
   - Desde el menú desplegable del administrador

### Funciones Principales

#### 📊 Dashboard de Alertas
- **Estado de Configuración**: Verificación visual de configuración
- **Productos con Stock Bajo**: Lista completa con detalles
- **Historial de Alertas**: Registro de alertas enviadas
- **Estadísticas**: Contadores y métricas

#### 📧 Envío de Alertas
- **Manual**: Botón "Enviar Alerta" para envío inmediato
- **Automático**: Verificación periódica según frecuencia configurada
- **Destinatarios Personalizados**: Especificar emails para envío específico

#### ⚙️ Configuración de Stock Mínimo
- **Edición Inline**: Click en stock mínimo para editar
- **Formulario de Productos**: Campo dedicado en crear/editar producto
- **Valores por Defecto**: Configuración automática por categoría

#### 🧪 Pruebas
- **Correo de Prueba**: Verificar configuración con email de prueba
- **Vista Previa**: Generar ejemplos de alertas sin enviar

## 📈 Gestión de Stock Mínimo

### Configuración por Producto

Cada producto tiene un campo `stock_minimo` que define el nivel de alerta:

- **0**: Sin alertas para este producto
- **1-5**: Stock bajo (amarillo)
- **6+**: Stock crítico si está por debajo (rojo)

### Configuración Automática

El sistema asigna valores por defecto basados en categoría:

- **Productos Críticos**: 10 unidades
- **Repuestos/Refacciones**: 5 unidades
- **Otros**: 3 unidades

### Edición Masiva

```sql
-- Actualizar stock mínimo por categoría
UPDATE productos 
SET stock_minimo = 10 
WHERE categoria_id IN (SELECT id FROM categorias WHERE nombre LIKE '%Crítico%');
```

## 📧 Formato de Alertas

### Contenido del Correo

Las alertas incluyen:

- **Resumen Ejecutivo**: Fecha, cantidad de productos afectados
- **Tabla Detallada**: 
  - Código y descripción del producto
  - Stock actual vs stock mínimo
  - Diferencia (faltante/bajo)
  - Categoría y subcategoría
  - Información del proveedor
  - Ubicaciones con stock
- **Recomendaciones**: Acciones sugeridas
- **Enlaces**: Acceso directo al sistema

### Ejemplo de Alerta

```
🚨 ALERTA DE STOCK BAJO - PPG Plásticos Plasa

Fecha: 05/02/2026 11:30
Productos Afectados: 15

PRODUCTOS QUE REQUIEREN ATENCIÓN:
1. [CRÍTICO] Válvula Neumática AS1201F
   Stock: 0 | Mínimo: 5 | Faltante: 5
   Proveedor: Festo (Tel: 555-1234)
   
2. [BAJO] Cilindro DNC-32-30
   Stock: 2 | Mínimo: 5 | Faltante: 3
   Proveedor: Festo (email@festo.com)
```

## 🔧 Administración Avanzada

### API Endpoints

```python
# Actualizar stock mínimo
PUT /api/productos/{id}/stock-minimo
{
  "stock_minimo": 10
}

# Obtener productos con stock bajo
GET /api/productos/stock-bajo

# Enviar alerta manual
POST /admin/send-stock-alert
{
  "destinatarios": "admin@empresa.com,gerente@empresa.com"
}
```

### Scripts de Utilidad

```bash
# Configurar demo de alertas
python scripts/configurar_demo_alertas.py

# Ejecutar pruebas del sistema
python tests/test_stock_alerts.py

# Migración de stock mínimo
python migrations/agregar_stock_minimo.py
```

## 🔍 Monitoreo y Logs

### Logs de Operaciones

Todas las operaciones se registran en:
- **Base de datos**: Tabla `operation_logs`
- **Archivo**: `logs/admin_operations.log`

### Tipos de Log

- `STOCK_ALERT`: Alerta enviada
- `EMAIL_TEST`: Correo de prueba
- `STOCK_MINIMO_UPDATE`: Actualización de stock mínimo

### Consultas Útiles

```sql
-- Últimas alertas enviadas
SELECT * FROM operation_logs 
WHERE operation_type = 'STOCK_ALERT' 
ORDER BY timestamp DESC LIMIT 10;

-- Productos más problemáticos
SELECT p.descripcion, COUNT(*) as alertas
FROM operation_logs ol
JOIN productos p ON ol.description LIKE '%' || p.descripcion || '%'
WHERE ol.operation_type = 'STOCK_ALERT'
GROUP BY p.descripcion
ORDER BY alertas DESC;
```

## 🚨 Solución de Problemas

### Problemas Comunes

#### ❌ "Configuración de correo incompleta"
- Verificar variables `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
- Usar contraseña de aplicación para Gmail
- Verificar que el servidor SMTP sea correcto

#### ❌ "Error de autenticación SMTP"
- Gmail: Usar contraseña de aplicación, no contraseña normal
- Verificar que 2FA esté activado en Gmail
- Probar con otro proveedor de correo

#### ❌ "No hay productos con stock bajo"
- Verificar que los productos tengan `stock_minimo > 0`
- Ejecutar `python scripts/configurar_demo_alertas.py` para pruebas
- Revisar datos de inventario

#### ❌ "Alertas no se envían automáticamente"
- Verificar `STOCK_ALERT_FREQUENCY_HOURS`
- Comprobar última alerta en logs
- Ejecutar manualmente desde la interfaz

### Comandos de Diagnóstico

```bash
# Verificar configuración
python tests/test_stock_alerts.py

# Ver productos con stock bajo
sqlite3 inventario.db "
SELECT p.descripcion, 
       COALESCE(SUM(i.cantidad), 0) as stock,
       p.stock_minimo
FROM productos p 
LEFT JOIN inventario i ON p.id = i.producto_id 
WHERE p.stock_minimo > 0
GROUP BY p.id 
HAVING stock <= p.stock_minimo;"

# Ver logs de alertas
tail -f logs/admin_operations.log | grep STOCK_ALERT
```

## 📊 Métricas y Reportes

### KPIs del Sistema

- **Productos con Stock Bajo**: Cantidad actual
- **Alertas Enviadas**: Frecuencia y destinatarios
- **Tiempo de Respuesta**: Desde alerta hasta reabastecimiento
- **Productos Críticos**: Sin stock vs con stock bajo

### Reportes Disponibles

1. **Reporte de Stock Bajo**: Lista actual de productos
2. **Historial de Alertas**: Registro temporal de notificaciones
3. **Análisis de Proveedores**: Productos por proveedor con stock bajo
4. **Tendencias**: Productos frecuentemente en stock bajo

## 🔮 Próximas Mejoras

### Funcionalidades Planificadas

- **Alertas por WhatsApp**: Integración con API de WhatsApp Business
- **Dashboard en Tiempo Real**: Gráficos y métricas actualizadas
- **Predicción de Stock**: ML para predecir necesidades futuras
- **Integración con Proveedores**: Envío automático de pedidos
- **Alertas Personalizadas**: Diferentes niveles según criticidad
- **Reportes Programados**: Envío automático de reportes semanales/mensuales

### Mejoras Técnicas

- **Caching**: Redis para mejorar rendimiento
- **Queue System**: Celery para procesamiento asíncrono
- **Notificaciones Push**: Alertas en navegador
- **API REST Completa**: Integración con sistemas externos

---

## 📞 Soporte

Para soporte técnico o consultas:

- **Documentación**: `docs/`
- **Pruebas**: `tests/test_stock_alerts.py`
- **Configuración**: `config_correo_ejemplo.env`
- **Logs**: `logs/admin_operations.log`

**Sistema desarrollado para PPG - Plásticos Plasa** 🏭