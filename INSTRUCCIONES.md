# 🚀 Instrucciones de Uso - Sistema de Inventario PPG

## ✅ Sistema Listo para Usar

Tu aplicación web de inventario está completamente configurada y funcionando.

## 🌐 Acceder a la Aplicación

**La aplicación está corriendo en:**
- **Local:** http://127.0.0.1:5000
- **Red local:** http://192.168.1.148:5000

### Para Iniciar la Aplicación:

1. **Método Rápido (Recomendado):**
   - Hacer doble clic en `iniciar_app.bat`
   - La aplicación se iniciará automáticamente

2. **Método Manual:**
   ```bash
   # Activar entorno virtual
   .\venv\Scripts\Activate.ps1
   
   # Iniciar aplicación
   python app.py
   ```

## 📊 Datos Importados

✅ **136 productos** importados desde tu catálogo  
✅ **118 registros de inventario** con ubicaciones  
✅ **84 ubicaciones** organizadas  
✅ **40 categorías** y **17 marcas** catalogadas  

## 🎯 Funcionalidades Disponibles

### 📋 Dashboard
- Estadísticas generales del inventario
- Productos con stock bajo
- Acciones rápidas

### 📦 Productos
- Lista completa con filtros por categoría y marca
- Búsqueda por descripción o código
- Formulario para agregar/editar productos
- **Imágenes automáticas:** `imagenes/[ID].jpg`

### 📍 Inventario
- Vista organizada por ubicaciones
- Control de stock en tiempo real
- Alertas de stock bajo
- Actualización de cantidades

### 🗺️ Ubicaciones
- Gestión de ubicaciones de almacenamiento
- Códigos únicos (A0, A1, B1, D1, etc.)
- Vista de productos por ubicación

### ⚙️ Configuración
- Gestión de categorías, marcas y máquinas
- Herramientas de administración

## 🖼️ Gestión de Imágenes

Las imágenes se almacenan en la carpeta `imagenes/` con el formato:
- `imagenes/1.jpg` - Producto ID 1
- `imagenes/23.jpg` - Producto ID 23
- etc.

**Para agregar imágenes:**
1. Guarda la imagen del producto en la carpeta `imagenes/`
2. Nómbrala con el ID del producto + `.jpg`
3. La imagen aparecerá automáticamente en la aplicación

## 🔧 Mantenimiento

### Respaldar Datos
- La base de datos está en `inventario.db`
- Respalda este archivo regularmente

### Actualizar Datos
- Modifica `Productos.csv` o `Inventario.csv`
- Ejecuta `python importar_datos.py` para reimportar

### Agregar Nuevos Productos
- Usa el formulario web (recomendado)
- O agrega al CSV y reimporta

## 🚨 Solución de Problemas

### La aplicación no inicia:
1. Verifica que el entorno virtual esté activado
2. Ejecuta `pip install -r requirements.txt`
3. Usa `iniciar_app.bat`

### No se ven las imágenes:
1. Verifica que las imágenes estén en `imagenes/`
2. Confirma que el nombre sea `[ID].jpg`
3. Verifica permisos de la carpeta

### Error de base de datos:
1. Elimina `inventario.db`
2. Ejecuta `python importar_datos.py`

## 📱 Uso Diario

1. **Consultar Stock:** Ve al Dashboard o Inventario
2. **Buscar Producto:** Usa la sección Productos con filtros
3. **Actualizar Cantidades:** Desde la vista de Inventario
4. **Agregar Producto:** Botón "Nuevo Producto"
5. **Gestionar Ubicaciones:** Sección Ubicaciones

## 🔒 Seguridad

- La aplicación corre en tu red local
- Los datos se almacenan localmente
- Haz respaldos regulares de `inventario.db`

## 📞 Soporte

Si necesitas ayuda:
1. Revisa este archivo de instrucciones
2. Consulta `README.md` para detalles técnicos
3. Verifica los logs en la consola de la aplicación

---

**¡Tu sistema de inventario está listo para usar!** 🎉

Abre tu navegador en http://127.0.0.1:5000 y comienza a gestionar tu inventario.