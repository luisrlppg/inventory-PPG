# 🐳 Docker Deployment Guide - Sistema de Inventario PPG

## 📋 Prerequisites

- Docker installed on your system
- Docker Compose installed
- At least 1GB of available disk space

## 🚀 Quick Start

### 1. Build and Run (Development)
```bash
# Build the Docker image
docker-compose build

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f inventario-app
```

### 2. Access the Application
- **Application:** http://localhost:5000
- **Admin Login:** admin / admin123

### 3. Stop the Application
```bash
docker-compose down
```

## 🏭 Production Deployment

### With Nginx Reverse Proxy
```bash
# Start with nginx (production profile)
docker-compose --profile production up -d

# Access via nginx
# HTTP: http://localhost
# Application direct: http://localhost:5000
```

## 📁 Volume Mounts

The following directories are mounted for data persistence:

- `./inventario.db` → `/app/inventario.db` (Database)
- `./imagenes` → `/app/imagenes` (Product images)
- `./logs` → `/app/logs` (Application logs)

## 🔧 Configuration

### Environment Variables
You can customize the deployment by setting these environment variables:

```bash
# In docker-compose.yml or .env file
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

### Database Initialization
The container will use the existing `inventario.db` file. If you need to start fresh:

1. Stop the container: `docker-compose down`
2. Remove the database: `rm inventario.db`
3. Run the import script: `python importar_datos.py`
4. Start the container: `docker-compose up -d`

## 🔒 Security Considerations

### Production Checklist
- [ ] Change default admin password
- [ ] Configure SSL certificates (uncomment HTTPS section in nginx.conf)
- [ ] Set up proper firewall rules
- [ ] Configure backup strategy
- [ ] Monitor logs regularly

### SSL Configuration (Production)
1. Obtain SSL certificates
2. Place them in `./ssl/` directory
3. Uncomment HTTPS server block in `nginx.conf`
4. Update server_name with your domain

## 📊 Monitoring

### Health Checks
- Container health: `docker-compose ps`
- Application health: `curl http://localhost:5000/health`
- Nginx status: `curl http://localhost/health`

### Logs
```bash
# Application logs
docker-compose logs inventario-app

# Nginx logs
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f
```

## 🔄 Backup and Restore

### Backup
```bash
# Create backup of database
docker-compose exec inventario-app cp /app/inventario.db /app/backup_$(date +%Y%m%d_%H%M%S).db

# Or use the web interface (Admin → Download Backup)
```

### Restore
1. Stop the container: `docker-compose down`
2. Replace `inventario.db` with your backup
3. Start the container: `docker-compose up -d`

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs inventario-app

# Check if ports are available
netstat -tulpn | grep :5000
```

### Database Issues
```bash
# Access container shell
docker-compose exec inventario-app bash

# Check database file
ls -la /app/inventario.db

# Test database connection
sqlite3 /app/inventario.db ".tables"
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R 1000:1000 ./inventario.db ./imagenes ./logs
```

### Network Issues
```bash
# Check container network
docker network ls
docker network inspect inventario-network
```

## 📈 Scaling

### Multiple Replicas (Advanced)
```yaml
# In docker-compose.yml
services:
  inventario-app:
    # ... existing config
    deploy:
      replicas: 3
```

**Note:** This application uses SQLite, which doesn't support multiple writers. For scaling, consider migrating to PostgreSQL.

## 🔧 Development

### Development Mode
```bash
# Run in development mode with live reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Accessing Container
```bash
# Shell access
docker-compose exec inventario-app bash

# Run commands inside container
docker-compose exec inventario-app python importar_datos.py
```

## 📋 Commands Reference

```bash
# Build only
docker-compose build

# Start in background
docker-compose up -d

# Start with nginx
docker-compose --profile production up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Remove everything (including volumes)
docker-compose down -v

# Restart specific service
docker-compose restart inventario-app

# Update and restart
docker-compose build && docker-compose up -d
```

## 🚨 Important Notes

1. **Data Persistence:** Database and images are stored in mounted volumes
2. **Admin Access:** Default credentials are admin/admin123 - change immediately
3. **Backups:** Use the web interface or manual file copying for backups
4. **Updates:** Rebuild the image when updating the application code
5. **Logs:** Check logs regularly for any issues or security events

---

**Your containerized inventory system is ready for deployment!** 🎉

For production use, ensure you follow the security checklist and configure SSL certificates.