#!/bin/bash

# Script de gestión completa de Docker para Ubuntu 24
# Inventario PPG - Docker Management

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Determine docker command
if groups $USER | grep -q '\bdocker\b'; then
    DOCKER_CMD="docker compose"
else
    DOCKER_CMD="sudo docker compose"
fi

print_header() {
    clear
    echo -e "${CYAN}========================================"
    echo -e "     GESTIÓN DE CONTENEDORES DOCKER"
    echo -e "     Inventario PPG - Ubuntu 24.04"
    echo -e "========================================${NC}"
    echo
}

print_menu() {
    echo -e "${BLUE}1.${NC} Desplegar en PRODUCCIÓN (con Nginx)"
    echo -e "${BLUE}2.${NC} Desplegar en DESARROLLO"
    echo -e "${BLUE}3.${NC} Ver estado de contenedores"
    echo -e "${BLUE}4.${NC} Ver logs en tiempo real"
    echo -e "${BLUE}5.${NC} Reiniciar contenedores"
    echo -e "${BLUE}6.${NC} Detener contenedores"
    echo -e "${BLUE}7.${NC} Limpiar contenedores e imágenes"
    echo -e "${BLUE}8.${NC} Backup de base de datos"
    echo -e "${BLUE}9.${NC} Información del sistema"
    echo -e "${BLUE}0.${NC} Salir"
    echo
}

wait_key() {
    echo
    echo -e "${YELLOW}Presiona Enter para continuar...${NC}"
    read
}

production_deploy() {
    echo -e "${GREEN}Desplegando en PRODUCCIÓN...${NC}"
    ./deploy_production.sh
    wait_key
}

development_deploy() {
    echo -e "${GREEN}Desplegando en DESARROLLO...${NC}"
    ./deploy_development.sh
    wait_key
}

show_status() {
    echo -e "${BLUE}Estado de contenedores:${NC}"
    $DOCKER_CMD ps
    echo
    echo -e "${BLUE}Imágenes disponibles:${NC}"
    docker images | grep -E "(inventario|nginx)" || echo "No hay imágenes del proyecto"
    echo
    echo -e "${BLUE}Uso de recursos:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "No hay contenedores ejecutándose"
    wait_key
}

show_logs() {
    echo -e "${BLUE}Mostrando logs en tiempo real (Ctrl+C para salir)...${NC}"
    echo
    $DOCKER_CMD logs -f
}

restart_containers() {
    echo -e "${YELLOW}Reiniciando contenedores...${NC}"
    $DOCKER_CMD restart
    echo
    $DOCKER_CMD ps
    echo -e "${GREEN}✅ Contenedores reiniciados${NC}"
    wait_key
}

stop_containers() {
    echo -e "${YELLOW}Deteniendo contenedores...${NC}"
    $DOCKER_CMD down
    echo -e "${GREEN}✅ Contenedores detenidos${NC}"
    wait_key
}

cleanup_docker() {
    echo -e "${RED}ADVERTENCIA: Esto eliminará contenedores e imágenes no utilizadas${NC}"
    echo -n "¿Estás seguro? (s/N): "
    read confirm
    if [[ "$confirm" =~ ^[Ss]$ ]]; then
        echo "Limpiando contenedores detenidos..."
        docker container prune -f
        echo "Limpiando imágenes no utilizadas..."
        docker image prune -f
        echo "Limpiando volúmenes no utilizados..."
        docker volume prune -f
        echo -e "${GREEN}✅ Limpieza completada${NC}"
    else
        echo "Operación cancelada"
    fi
    wait_key
}

backup_database() {
    echo -e "${BLUE}Creando backup de base de datos...${NC}"
    
    # Check if container is running
    if ! $DOCKER_CMD ps | grep -q "inventario-app"; then
        echo -e "${RED}❌ El contenedor no está ejecutándose${NC}"
        wait_key
        return
    fi
    
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S).db"
    
    # Create backup inside container
    $DOCKER_CMD exec inventario-app cp /app/inventario.db /app/$BACKUP_NAME
    
    # Copy backup to host
    docker cp inventario-ppg:/app/$BACKUP_NAME ./$BACKUP_NAME
    
    echo -e "${GREEN}✅ Backup creado: $BACKUP_NAME${NC}"
    echo "Archivo guardado en: $(pwd)/$BACKUP_NAME"
    wait_key
}

show_system_info() {
    echo -e "${BLUE}Información del sistema:${NC}"
    echo "OS: $(lsb_release -d | cut -f2)"
    echo "Kernel: $(uname -r)"
    echo "Docker: $(docker --version)"
    echo "Docker Compose: $(docker compose --version)"
    echo
    echo -e "${BLUE}Recursos del sistema:${NC}"
    echo "CPU: $(nproc) cores"
    echo "RAM: $(free -h | awk '/^Mem:/ {print $2}')"
    echo "Disco: $(df -h . | awk 'NR==2 {print $4 " disponible de " $2}')"
    echo
    echo -e "${BLUE}Red:${NC}"
    echo "IP local: $(hostname -I | awk '{print $1}')"
    echo "Hostname: $(hostname)"
    wait_key
}

# Main menu loop
while true; do
    print_header
    print_menu
    
    echo -n "Selecciona una opción (0-9): "
    read choice
    
    case $choice in
        1) production_deploy ;;
        2) development_deploy ;;
        3) show_status ;;
        4) show_logs ;;
        5) restart_containers ;;
        6) stop_containers ;;
        7) cleanup_docker ;;
        8) backup_database ;;
        9) show_system_info ;;
        0) 
            echo -e "${GREEN}¡Hasta luego!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Opción inválida${NC}"
            sleep 1
            ;;
    esac
done