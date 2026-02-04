# 📁 Información del Repositorio Git

## 🎯 Repositorio Creado Exitosamente

**Nombre del Proyecto:** Sistema de Inventario PPG  
**Versión:** 1.0.0  
**Fecha de Creación:** $(Get-Date -Format "dd/MM/yyyy HH:mm")  
**Commit Inicial:** cd8a58a  

## 📊 Estadísticas del Repositorio

- **20 archivos** incluidos en el commit inicial
- **3,775 líneas de código** agregadas
- **Archivos temporales eliminados:** 11 scripts y CSVs de desarrollo
- **Estructura limpia** lista para producción

## 📁 Archivos Incluidos

### 🌐 Aplicación Principal
- `app.py` - Aplicación Flask principal
- `config.py` - Configuraciones del sistema
- `requirements.txt` - Dependencias Python

### 🎨 Frontend
- `templates/` - Plantillas HTML (6 archivos)
- `static/style.css` - Estilos personalizados

### 🗃️ Datos
- `inventario.db` - Base de datos SQLite
- `Productos.csv` - Catálogo de productos
- `Inventario.csv` - Registros de stock
- `importar_datos.py` - Script de importación

### 🚀 Deployment
- `iniciar_app.bat` - Script de inicio rápido
- `.gitignore` - Archivos excluidos del control de versiones

### 📚 Documentación
- `README.md` - Documentación técnica
- `INSTRUCCIONES.md` - Guía de usuario
- `RESUMEN_PROYECTO.md` - Resumen ejecutivo

## 🔧 Comandos Git Útiles

### Ver estado del repositorio
```bash
git status
```

### Ver historial de commits
```bash
git log --oneline
git log --graph --pretty=format:'%h -%d %s (%cr) <%an>'
```

### Crear nueva rama para desarrollo
```bash
git checkout -b desarrollo
git checkout -b feature/nueva-funcionalidad
```

### Agregar cambios y hacer commit
```bash
git add .
git commit -m "Descripción del cambio"
```

### Ver diferencias
```bash
git diff
git diff --staged
```

## 🌿 Estrategia de Ramas Recomendada

- **master/main** - Código en producción
- **desarrollo** - Rama de desarrollo principal
- **feature/nombre** - Nuevas funcionalidades
- **hotfix/nombre** - Correcciones urgentes
- **release/version** - Preparación de releases

## 📋 Próximos Pasos

1. **Desarrollo Continuo:**
   ```bash
   git checkout -b desarrollo
   # Hacer cambios
   git add .
   git commit -m "Mejora: descripción"
   git checkout master
   git merge desarrollo
   ```

2. **Respaldos Regulares:**
   - Hacer commits frecuentes
   - Crear tags para versiones importantes
   - Considerar repositorio remoto (GitHub, GitLab, etc.)

3. **Versionado:**
   ```bash
   git tag -a v1.0.0 -m "Versión 1.0.0 - Release inicial"
   git tag -a v1.1.0 -m "Versión 1.1.0 - Nuevas funcionalidades"
   ```

## 🔒 Archivos Excluidos (.gitignore)

- Entorno virtual (`venv/`)
- Archivos temporales de Python (`__pycache__/`, `*.pyc`)
- Logs del sistema (`logs/`, `*.log`)
- Archivos del sistema (`.DS_Store`, `Thumbs.db`)
- Configuraciones locales (`.env`, `config_local.py`)

## 📞 Información de Contacto

**Desarrollado para:** Plásticos Plasa (PPG)  
**Configuración Git:**
- Usuario: PPG Desarrollo
- Email: desarrollo@plasticosplasa.com

---

**¡Repositorio Git configurado y listo para desarrollo colaborativo!** 🚀