# 📧 Cómo Configurar Gmail para Alertas de Stock

## 🎯 Objetivo
Configurar tu cuenta de Gmail para enviar alertas automáticas de stock bajo desde el sistema de inventario.

---

## 📋 Requisitos Previos
- Cuenta de Gmail activa
- Acceso a la configuración de seguridad de Google
- 5 minutos de tiempo

---

## 🔐 Paso 1: Activar Verificación en 2 Pasos

### 1.1 Acceder a Seguridad de Google
1. Ir a: https://myaccount.google.com/security
2. Iniciar sesión con tu cuenta de Gmail
3. Buscar la sección **"Cómo inicias sesión en Google"**

### 1.2 Activar 2FA
1. Click en **"Verificación en 2 pasos"**
2. Click en **"Comenzar"**
3. Seguir los pasos:
   - Verificar tu número de teléfono
   - Ingresar código de verificación
   - Confirmar activación

✅ **Verificación en 2 pasos activada**

---

## 🔑 Paso 2: Generar Contraseña de Aplicación

### 2.1 Acceder a Contraseñas de Aplicaciones
1. Volver a: https://myaccount.google.com/security
2. En la sección **"Cómo inicias sesión en Google"**
3. Click en **"Contraseñas de aplicaciones"**
   - Si no aparece, asegúrate de que 2FA esté activado

### 2.2 Crear Nueva Contraseña
1. En "Selecciona la app", elegir: **"Correo"**
2. En "Selecciona el dispositivo", elegir: **"Otro (nombre personalizado)"**
3. Escribir: **"Sistema Inventario PPG"**
4. Click en **"Generar"**

### 2.3 Copiar Contraseña
- Google mostrará una contraseña de 16 caracteres
- Ejemplo: `abcd efgh ijkl mnop`
- **¡IMPORTANTE!** Copia esta contraseña, no la podrás ver de nuevo

✅ **Contraseña de aplicación generada**

---

## ⚙️ Paso 3: Configurar el Sistema

### 3.1 Crear/Editar archivo .env

En la carpeta raíz del proyecto, crea o edita el archivo `.env`:

```bash
# Configuración de correo Gmail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=abcd efgh ijkl mnop
MAIL_DEFAULT_SENDER=tu-email@gmail.com

# Destinatarios de alertas (separados por comas)
STOCK_ALERT_RECIPIENTS=admin@empresa.com,gerente@empresa.com,almacen@empresa.com

# Configuración de alertas
STOCK_ALERT_ENABLED=true
STOCK_ALERT_FREQUENCY_HOURS=24
```

### 3.2 Reemplazar Valores

**MAIL_USERNAME**: Tu dirección de Gmail completa
```bash
MAIL_USERNAME=inventario.ppg@gmail.com
```

**MAIL_PASSWORD**: La contraseña de 16 caracteres (sin espacios)
```bash
MAIL_PASSWORD=abcdefghijklmnop
```

**MAIL_DEFAULT_SENDER**: Mismo que MAIL_USERNAME
```bash
MAIL_DEFAULT_SENDER=inventario.ppg@gmail.com
```

**STOCK_ALERT_RECIPIENTS**: Emails que recibirán las alertas
```bash
STOCK_ALERT_RECIPIENTS=admin@ppg.com,gerente@ppg.com,almacen@ppg.com
```

---

## 🧪 Paso 4: Probar Configuración

### 4.1 Iniciar la Aplicación
```bash
# Activar entorno virtual
venv\Scripts\activate

# Iniciar aplicación
python app.py
```

### 4.2 Acceder al Panel de Pruebas
1. Abrir navegador: http://localhost:5000
2. Login: `/admin/login`
   - Usuario: `admin`
   - Contraseña: `admin123`
3. Menú → **"Alertas de Stock"**

### 4.3 Enviar Correo de Prueba
1. Click en botón **"Configuración"**
2. En la sección "Prueba de Correo"
3. Ingresar tu email
4. Click en **"Enviar Prueba"**
5. Revisar tu bandeja de entrada

✅ **Si recibes el correo, ¡la configuración es correcta!**

---

## ❌ Solución de Problemas

### Error: "Username and Password not accepted"

**Causa**: Contraseña incorrecta o 2FA no activado

**Solución**:
1. Verificar que 2FA esté activado
2. Generar nueva contraseña de aplicación
3. Copiar sin espacios: `abcdefghijklmnop`
4. Actualizar `.env`

### Error: "SMTP Authentication Error"

**Causa**: Configuración incorrecta del servidor

**Solución**:
```bash
# Verificar configuración en .env
MAIL_SERVER=smtp.gmail.com  # ← Debe ser exactamente esto
MAIL_PORT=587               # ← Puerto correcto
MAIL_USE_TLS=true          # ← Debe estar en true
```

### Error: "Connection refused"

**Causa**: Firewall o antivirus bloqueando

**Solución**:
1. Desactivar temporalmente antivirus
2. Verificar firewall de Windows
3. Probar con otra red (datos móviles)

### No recibo el correo

**Verificar**:
1. ✅ Revisar carpeta de SPAM
2. ✅ Verificar que el email destinatario sea correcto
3. ✅ Esperar 1-2 minutos (puede haber retraso)
4. ✅ Revisar logs: `logs/admin_operations.log`

---

## 📧 Ejemplo de Configuración Completa

```bash
# ============================================
# CONFIGURACIÓN DE CORREO - GMAIL
# ============================================

# Servidor SMTP de Gmail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false

# Credenciales (usar contraseña de aplicación)
MAIL_USERNAME=inventario.ppg@gmail.com
MAIL_PASSWORD=abcdefghijklmnop
MAIL_DEFAULT_SENDER=inventario.ppg@gmail.com

# ============================================
# CONFIGURACIÓN DE ALERTAS
# ============================================

# Activar/desactivar alertas
STOCK_ALERT_ENABLED=true

# Destinatarios (separados por comas, sin espacios)
STOCK_ALERT_RECIPIENTS=admin@ppg.com,gerente@ppg.com,almacen@ppg.com

# Frecuencia de alertas automáticas (en horas)
STOCK_ALERT_FREQUENCY_HOURS=24

# ============================================
# OTRAS CONFIGURACIONES
# ============================================

FLASK_ENV=production
SECRET_KEY=tu-clave-secreta-muy-segura-aqui
```

---

## 🔒 Seguridad

### ✅ Buenas Prácticas

1. **Nunca compartir** la contraseña de aplicación
2. **No subir** el archivo `.env` a Git (ya está en `.gitignore`)
3. **Usar cuenta dedicada** para el sistema (opcional pero recomendado)
4. **Revocar contraseñas** no utilizadas
5. **Cambiar contraseñas** periódicamente

### 🔐 Crear Cuenta Dedicada (Recomendado)

Para mayor seguridad, crea una cuenta Gmail específica:

1. Crear nueva cuenta: `inventario.ppg@gmail.com`
2. Activar 2FA en esta cuenta
3. Generar contraseña de aplicación
4. Usar esta cuenta solo para el sistema

**Ventajas**:
- Mayor seguridad
- Mejor organización
- Fácil auditoría
- Separación de responsabilidades

---

## 📊 Verificación Final

### Checklist de Configuración

- [ ] Verificación en 2 pasos activada en Gmail
- [ ] Contraseña de aplicación generada
- [ ] Archivo `.env` creado con configuración
- [ ] Contraseña copiada sin espacios
- [ ] Destinatarios configurados
- [ ] Aplicación iniciada sin errores
- [ ] Correo de prueba enviado
- [ ] Correo de prueba recibido
- [ ] Alerta de stock enviada (opcional)

### Comandos de Verificación

```bash
# Verificar configuración
python tests/test_stock_alerts.py

# Ver logs
type logs\admin_operations.log

# Probar conexión SMTP (Python)
python -c "import smtplib; s=smtplib.SMTP('smtp.gmail.com',587); s.starttls(); print('✅ Conexión exitosa')"
```

---

## 🎉 ¡Listo!

Tu sistema de alertas está configurado y funcionando. Ahora recibirás notificaciones automáticas cuando el stock esté bajo.

### Próximos Pasos

1. **Configurar stock mínimo** en tus productos
2. **Ajustar destinatarios** según necesidad
3. **Establecer rutina** de revisión de alertas
4. **Optimizar niveles** según experiencia

---

## 📞 ¿Necesitas Ayuda?

### Recursos Adicionales

- **Documentación completa**: `docs/SISTEMA_ALERTAS_STOCK.md`
- **Guía rápida**: `GUIA_RAPIDA_ALERTAS.md`
- **Pruebas**: `python tests/test_stock_alerts.py`

### Soporte de Google

- **Centro de ayuda**: https://support.google.com/accounts
- **Contraseñas de aplicaciones**: https://support.google.com/accounts/answer/185833
- **Verificación en 2 pasos**: https://support.google.com/accounts/answer/185839

---

**Sistema de Inventario PPG** | **Alertas de Stock Automatizadas** 📧