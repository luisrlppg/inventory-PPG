# Sistema de Inventario de Refacciones - PPG

Sistema web completo para la gestión de inventario de refacciones de Plásticos Plasa (PPG).

## 🚀 Características

- **Gestión de Productos**: Crear, editar y visualizar productos con imágenes
- **Control de Inventario**: Seguimiento de stock por ubicaciones
- **Organización**: Categorías, subcategorías, marcas y máquinas
- **Ubicaciones**: Sistema de ubicaciones jerárquico
- **Imágenes**: Soporte automático para imágenes de productos
- **Reportes**: Dashboard con estadísticas y alertas de stock bajo
- **Responsive**: Interfaz adaptable a dispositivos móviles

## 📋 Requisitos

- Python 3.7+
- Flask
- SQLite (incluido con Python)

## 🛠️ Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   cd inventario-refacciones
   ```

2. **Instalar dependencias**
   ```bash
   pip install flask
   ```

3. **Importar datos existentes**
   ```bash
   python importar_datos.py
   ```

4. **Iniciar la aplicación**
   ```bash
   python app.py
   ```

5. **Abrir en el navegador**
   ```
   http://localhost:5000
   ```

## 📁 Estructura del Proyecto

```
inventario-refacciones/
├── app.py                 # Aplicación principal Flask
├── importar_datos.py      # Script para importar datos CSV
├── inventario.db          # Base de datos SQLite
├── Productos.csv          # Catálogo de productos
├── Inventario.csv         # Stock por ubicaciones
├── imagenes/              # Imágenes de productos (ID.jpg)
├── templates/             # Plantillas HTML
│   ├── base.html
│   ├── dashboard.html
│   ├── productos.html
│   ├── inventario.html
│   ├── ubicaciones.html
│   ├── configuracion.html
│   └── producto_form.html
└── static/
    └── style.css          # Estilos personalizados
```

## 🖼️ Gestión de Imágenes

Las imágenes de productos se almacenan en la carpeta `imagenes/` con el formato:
- `imagenes/1.jpg` - Imagen del producto con ID 1
- `imagenes/23.jpg` - Imagen del producto con ID 23
- etc.

El sistema busca automáticamente la imagen basándose en el ID del producto.

## 📊 Funcionalidades Principales

### Dashboard
- Estadísticas generales del inventario
- Productos con stock bajo
- Acciones rápidas

### Productos
- Lista completa de productos con filtros
- Formulario para agregar/editar productos
- Campos: descripción, código, categoría, marca, máquina, etc.
- Vista previa de imágenes

### Inventario
- Vista por ubicaciones
- Control de stock por producto y ubicación
- Alertas de stock bajo
- Actualización de cantidades

### Ubicaciones
- Gestión de ubicaciones de almacenamiento
- Estructura jerárquica: Empresa > Área > Nivel > Sección
- Códigos únicos para cada ubicación

### Configuración
- Gestión de categorías, marcas y máquinas
- Herramientas de administración
- Información del sistema

## 🔧 Configuración

### Base de Datos
El sistema utiliza SQLite con las siguientes tablas:
- `productos` - Catálogo de productos
- `inventario` - Stock por ubicación
- `ubicaciones` - Ubicaciones de almacenamiento
- `categorias` - Categorías de productos
- `subcategorias` - Subcategorías
- `marcas` - Marcas de productos
- `maquinas` - Máquinas que usan los productos

### Importación de Datos
El script `importar_datos.py` lee los archivos CSV existentes y los importa a la base de datos:
- Convierte `Productos.csv` a la tabla de productos
- Convierte `Inventario.csv` a las tablas de inventario y ubicaciones
- Crea automáticamente categorías, marcas y máquinas

## 🌐 API Endpoints

- `GET /` - Dashboard principal
- `GET /productos` - Lista de productos
- `GET /inventario` - Vista de inventario
- `GET /ubicaciones` - Gestión de ubicaciones
- `GET /configuracion` - Configuración del sistema
- `POST /producto/guardar` - Guardar producto
- `GET /api/producto/<id>` - Detalles de producto (JSON)
- `GET /imagenes/<filename>` - Servir imágenes

## 📱 Uso

1. **Agregar Productos**: Usar el formulario de productos con todos los campos necesarios
2. **Gestionar Stock**: Actualizar cantidades desde la vista de inventario
3. **Organizar**: Crear categorías, marcas y ubicaciones según necesidades
4. **Monitorear**: Revisar el dashboard para alertas de stock bajo
5. **Configurar**: Ajustar categorías y configuraciones desde el panel de administración

## 🔒 Seguridad

- Validación de datos en formularios
- Manejo seguro de archivos de imagen
- Protección contra inyección SQL con SQLite

## 🚀 Próximas Mejoras

- [ ] Sistema de usuarios y autenticación
- [ ] Historial de movimientos de inventario
- [ ] Códigos de barras y QR
- [ ] Reportes en PDF/Excel
- [ ] Notificaciones automáticas
- [ ] API REST completa
- [ ] Integración con sistemas externos

## 📞 Soporte

Para soporte técnico o preguntas sobre el sistema, contactar al administrador del sistema.

---

**Desarrollado para Plásticos Plasa (PPG)**  
*Sistema de Inventario de Refacciones v1.0*