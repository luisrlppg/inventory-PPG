#!/bin/bash

# Script de despliegue en producción para Ubuntu 24
# Inventario PPG - Docker Deployment

set -e  # Exit on any error

echo "========================================"
echo "   DESPLIEGUE EN PRODUCCION - Docker"
echo "   Ubuntu 24.04 LTS"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}[$1] $2${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado. Instálalo primero:"
    echo "sudo apt update && sudo apt install -y docker.io docker-compose"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose no está instalado. Instálalo primero:"
    echo "sudo apt install -y docker-compose"
    exit 1
fi

# Check if user is in docker group
if ! groups $USER | grep -q '\bdocker\b'; then
    print_warning "Tu usuario no está en el grupo docker. Ejecuta:"
    echo "sudo usermod -aG docker $USER"
    echo "Luego cierra sesión y vuelve a entrar."
    echo
    echo "¿Continuar con sudo? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
    DOCKER_CMD="sudo docker-compose"
else
    DOCKER_CMD="docker-compose"
fi

print_step "1/6" "Verificando archivos necesarios..."
if [[ ! -f "docker-compose.yml" ]]; then
    print_error "docker-compose.yml no encontrado"
    exit 1
fi
if [[ ! -f "Dockerfile" ]]; then
    print_error "Dockerfile no encontrado"
    exit 1
fi
print_success "Archivos de configuración encontrados"

print_step "2/6" "Deteniendo contenedores actuales..."
$DOCKER_CMD down || true

print_step "3/6" "Construyendo nueva imagen..."
$DOCKER_CMD build --no-cache

print_step "4/6" "Iniciando contenedores en modo producción..."
$DOCKER_CMD --profile production up -d

print_step "5/6" "Verificando estado de contenedores..."
$DOCKER_CMD ps

print_step "6/6" "Mostrando logs recientes..."
$DOCKER_CMD logs --tail=20 inventario-app

echo
echo "========================================"
print_success "DESPLIEGUE COMPLETADO"
echo "========================================"
echo
echo "🌐 Aplicación disponible en:"
echo "   - Con Nginx: http://localhost"
echo "   - Con Nginx (IP): http://$(hostname -I | awk '{print $1}')"
echo "   - Directo: http://localhost:5000"
echo
echo "📋 Comandos útiles:"
echo "   - Ver logs: $DOCKER_CMD logs -f"
echo "   - Detener: $DOCKER_CMD down"
echo "   - Estado: $DOCKER_CMD ps"
echo "   - Reiniciar: $DOCKER_CMD restart"
echo
echo "🔐 Credenciales admin: admin / admin123"
echo "⚠️  Recuerda cambiar la contraseña por defecto"
echo

# Check if containers are running
if $DOCKER_CMD ps | grep -q "inventario"; then
    print_success "Contenedores ejecutándose correctamente"
    
    # Wait a moment and test health
    echo "Probando conectividad..."
    sleep 5
    if curl -f http://localhost:5000/health &>/dev/null; then
        print_success "Aplicación respondiendo correctamente"
    else
        print_warning "La aplicación puede tardar unos segundos en estar lista"
    fi
else
    print_error "Los contenedores no se iniciaron correctamente"
    echo "Revisa los logs con: $DOCKER_CMD logs inventario-app"
    exit 1
fi