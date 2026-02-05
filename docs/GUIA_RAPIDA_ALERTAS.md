# 🚀 Guía Rápida - Sistema de Alertas de Stock

## ⚡ Inicio Rápido (5 minutos)

### 1️⃣ Instalar Dependencias
```bash
# Activar entorno virtual
venv\Scripts\activate

# Instalar Flask-Mail (ya instalado)
pip install Flask-Mail
```

### 2️⃣ Configurar Correo

Crea o edita tu archivo `.env` con tu configuración de Gmail:

```bash
# Para Gmail - Necesitas contraseña de aplicación
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx
MAIL_DEFAULT_SENDER=tu-email@gmail.com

# Destinatarios de alertas
STOCK_ALERT_RECIPIENTS=admin@empresa.com,gerente@empresa.com
```

**📝 Cómo obtener contraseña de aplicación de Gmail:**
1. Ir a https://myaccount.google.com/security
2. Activar "Verificación en 2 pasos"
3. Buscar "Contraseñas de aplicaciones"
4. Generar nueva contraseña para "Correo"
5. Copiar la contraseña de 16 caracteres

### 3️⃣ Iniciar la Aplicación
```bash
python app.py
```

### 4️⃣ Acceder al Panel de Alertas

1. Abrir navegador: http://localhost:5000
2. Login admin: `/admin/login`
   - Usuario: `admin`
   - Contraseña: `admin123`
3. Menú → "Alertas de Stock"

## 🎯 Funciones Principales

### Ver Productos con Stock Bajo
- Accede a `/admin/stock-alerts`
- Verás lista completa de productos que necesitan reabastecimiento
- Código de colores:
  - 🔴 Rojo: Stock crítico (0 unidades)
  - 🟡 Amarillo: Stock bajo (por debajo del mínimo)

### Enviar Alerta Manual
1. Click en "Enviar Alerta"
2. Confirmar destinatarios (o usar los configurados)
3. Click "Enviar"
4. ✅ Correo enviado con reporte completo

### Probar Configuración
1. Click en "Configuración"
2. Ingresar tu email en "Prueba de Correo"
3. Click "Enviar Prueba"
4. Revisar tu bandeja de entrada

### Editar Stock Mínimo
- **Desde la lista**: Click en el número de stock mínimo → editar → guardar
- **Desde productos**: Editar producto → campo "Stock Mínimo para Alertas"

## 📊 Configurar Stock Mínimo

### Valores Recomendados
- **Productos críticos**: 10-15 unidades
- **Repuestos comunes**: 5-8 unidades
- **Productos ocasionales**: 2-3 unidades
- **Sin alertas**: 0 (desactiva alertas para ese producto)

### Configuración Rápida
```bash
# Configurar demo con productos de ejemplo
python scripts/configurar_demo_alertas.py
```

## 🧪 Probar el Sistema

```bash
# Ejecutar pruebas completas
python tests/test_stock_alerts.py
```

Esto te mostrará:
- ✅ Productos con stock bajo detectados
- ✅ Estado de configuración de correo
- ✅ Generación de contenido de alertas
- ✅ Archivos de ejemplo generados

## 📧 Ejemplo de Correo

El correo incluye:

```
🚨 ALERTA DE STOCK BAJO - PPG

Fecha: 05/02/2026
Productos Afectados: 15

┌─────────────────────────────────────────┐
│ Código  │ Descripción    │ Stock │ Mín │
├─────────────────────────────────────────┤
│ 22696   │ Válvula 1/2"   │   0   │  5  │
│ AS1201F │ Cilindro 32mm  │   2   │  5  │
└─────────────────────────────────────────┘

Proveedor: Festo (Tel: 555-1234)
Ubicaciones: Almacén A: 0, Almacén B: 2
```

## 🔧 Solución Rápida de Problemas

### ❌ "Configuración de correo incompleta"
```bash
# Verificar variables en .env
MAIL_USERNAME=tu-email@gmail.com  # ← Debe estar configurado
MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx # ← Contraseña de aplicación
MAIL_DEFAULT_SENDER=tu-email@gmail.com
```

### ❌ "Error de autenticación"
- Usar **contraseña de aplicación**, no tu contraseña normal
- Verificar que 2FA esté activado en Gmail
- Probar con otro email

### ❌ "No hay productos con stock bajo"
```bash
# Configurar demo
python scripts/configurar_demo_alertas.py
```

## 📱 Uso Diario

### Rutina Recomendada

**Diario:**
- Revisar dashboard de alertas
- Verificar productos críticos (stock = 0)

**Semanal:**
- Enviar reporte de stock bajo
- Ajustar stock mínimo según necesidad
- Contactar proveedores

**Mensual:**
- Revisar historial de alertas
- Analizar productos frecuentemente bajos
- Optimizar niveles de stock mínimo

## 🎨 Personalización

### Cambiar Frecuencia de Alertas
```bash
# En .env
STOCK_ALERT_FREQUENCY_HOURS=24  # Cada 24 horas
# o
STOCK_ALERT_FREQUENCY_HOURS=12  # Cada 12 horas
```

### Agregar Más Destinatarios
```bash
# En .env - separar con comas
STOCK_ALERT_RECIPIENTS=admin@empresa.com,gerente@empresa.com,almacen@empresa.com,compras@empresa.com
```

### Desactivar Alertas Temporalmente
```bash
# En .env
STOCK_ALERT_ENABLED=false
```

## 📚 Documentación Completa

Para más detalles, consulta:
- **Documentación completa**: `docs/SISTEMA_ALERTAS_STOCK.md`
- **Configuración de correo**: `config_correo_ejemplo.env`
- **Pruebas**: `tests/test_stock_alerts.py`

## ✅ Checklist de Implementación

- [x] Migración de base de datos ejecutada
- [x] Flask-Mail instalado
- [ ] Variables de entorno configuradas en `.env`
- [ ] Contraseña de aplicación de Gmail generada
- [ ] Correo de prueba enviado exitosamente
- [ ] Stock mínimo configurado en productos
- [ ] Primera alerta enviada
- [ ] Destinatarios verificados

## 🎉 ¡Listo!

Tu sistema de alertas está configurado. Ahora recibirás notificaciones automáticas cuando el stock esté bajo.

**Próximos pasos:**
1. Configurar stock mínimo en todos tus productos
2. Agregar destinatarios relevantes
3. Establecer rutina de revisión
4. Optimizar niveles según experiencia

---

**¿Necesitas ayuda?** Revisa `docs/SISTEMA_ALERTAS_STOCK.md` para documentación completa.