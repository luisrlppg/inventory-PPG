#!/bin/bash

# Script de despliegue en desarrollo para Ubuntu 24
# Inventario PPG - Docker Development

set -e  # Exit on any error

echo "========================================"
echo "   DESPLIEGUE EN DESARROLLO - Docker"
echo "   Ubuntu 24.04 LTS"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check Docker availability
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado"
    exit 1
fi

# Determine docker command
if groups $USER | grep -q '\bdocker\b'; then
    DOCKER_CMD="docker compose"
else
    DOCKER_CMD="sudo docker compose"
    print_warning "Usando sudo para Docker"
fi

print_step "1/4" "Deteniendo contenedores actuales..."
$DOCKER_CMD down || true

print_step "2/4" "Construyendo imagen de desarrollo..."
$DOCKER_CMD build

print_step "3/4" "Iniciando contenedores en modo desarrollo..."
$DOCKER_CMD -f docker compose.yml -f docker compose.dev.yml up -d

print_step "4/4" "Verificando estado..."
$DOCKER_CMD ps

echo
echo "========================================"
print_success "DESARROLLO INICIADO"
echo "========================================"
echo
echo "🌐 Aplicación disponible en:"
echo "   - http://localhost:5000"
echo "   - http://$(hostname -I | awk '{print $1}'):5000"
echo
echo "🛠️  Modo desarrollo activo:"
echo "   - Auto-reload habilitado"
echo "   - Debug mode activo"
echo "   - Código montado como volumen"
echo
echo "📋 Para desarrollo:"
echo "   - Ver logs: $DOCKER_CMD logs -f"
echo "   - Detener: $DOCKER_CMD down"
echo

if $DOCKER_CMD ps | grep -q "inventario"; then
    print_success "Contenedor de desarrollo ejecutándose"
else
    print_error "Error iniciando contenedor"
    exit 1
fi