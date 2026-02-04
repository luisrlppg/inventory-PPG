# 🚀 Scripts de Despliegue

Esta carpeta contiene todos los scripts para desplegar y gestionar la aplicación con Docker.

## 📁 Archivos Disponibles

### 🐧 Para Ubuntu/Linux:
- **`deploy_production.sh`** - Despliegue en producción con Nginx
- **`deploy_development.sh`** - Despliegue en desarrollo con auto-reload
- **`docker_management.sh`** - Menú interactivo completo de gestión

### 🪟 Para Windows:
- **`deploy_production.bat`** - Despliegue en producción (Batch)
- **`deploy_production.ps1`** - Despliegue en producción (PowerShell)
- **`deploy_development.bat`** - Despliegue en desarrollo (Batch)
- **`docker_management.bat`** - Menú interactivo (Batch)

## 🎯 Uso Rápido

### Ubuntu 24.04 (Producción):
```bash
# Hacer ejecutable (solo la primera vez)
chmod +x scripts/*.sh

# Desplegar en producción
./scripts/deploy_production.sh

# Menú interactivo
./scripts/docker_management.sh
```

### Windows:
```cmd
# Desplegar en producción
scripts\deploy_production.bat

# Menú interactivo
scripts\docker_management.bat
```

## 🔧 Funcionalidades

### Scripts de Producción:
1. ✅ Detienen contenedores actuales
2. 🔨 Construyen nueva imagen
3. 🚀 Inician con Nginx (puerto 80)
4. 📊 Verifican estado
5. 📝 Muestran logs

### Scripts de Desarrollo:
1. 🛠️ Modo debug activado
2. 🔄 Auto-reload habilitado
3. 📁 Código montado como volumen
4. 🚀 Puerto 5000 directo

### Menú de Gestión:
- Ver estado de contenedores
- Logs en tiempo real
- Reiniciar servicios
- Backup de base de datos
- Limpieza de recursos
- Información del sistema

## 🌐 Acceso Post-Despliegue

- **Producción**: http://localhost (Nginx) o http://localhost:5000 (directo)
- **Desarrollo**: http://localhost:5000
- **Admin**: admin / admin123 (cambiar después del primer login)

## 📋 Comandos Útiles

```bash
# Ver logs
docker-compose logs -f

# Estado de contenedores
docker-compose ps

# Detener todo
docker-compose down

# Reiniciar
docker-compose restart
```