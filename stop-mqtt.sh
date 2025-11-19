#!/bin/bash
# Script para detener todos los servicios del Sistema Bancario
# Incluye soporte para MQTT

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}================================${NC}"
echo -e "${YELLOW}🛑 Deteniendo Sistema Bancario${NC}"
echo -e "${CYAN}================================${NC}"
echo ""

# Función para detener proceso por PID file
stop_by_pid_file() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}🔴 Deteniendo $service_name (PID: $PID)...${NC}"
            kill -TERM $PID 2>/dev/null
            sleep 2
            
            # Si aún está corriendo, forzar
            if ps -p $PID > /dev/null 2>&1; then
                kill -KILL $PID 2>/dev/null
            fi
            
            echo -e "${GREEN}✅ $service_name detenido${NC}"
        else
            echo -e "${CYAN}ℹ️  $service_name no está corriendo${NC}"
        fi
        rm -f "$pid_file"
    fi
}

# Función para detener proceso por nombre
stop_by_name() {
    local process_name=$1
    local service_name=$2
    
    PIDS=$(pgrep -f "$process_name")
    if [ ! -z "$PIDS" ]; then
        echo -e "${YELLOW}🔴 Deteniendo $service_name...${NC}"
        pkill -TERM -f "$process_name"
        sleep 2
        
        # Si aún está corriendo, forzar
        if pgrep -f "$process_name" > /dev/null; then
            pkill -KILL -f "$process_name"
        fi
        
        echo -e "${GREEN}✅ $service_name detenido${NC}"
    else
        echo -e "${CYAN}ℹ️  $service_name no está corriendo${NC}"
    fi
}

cd "$PROJECT_DIR"

# Detener por PID files
stop_by_pid_file ".socket_server.pid" "Socket Server"
stop_by_pid_file ".bridge.pid" "Flask Bridge"
stop_by_pid_file ".frontend.pid" "Frontend"
stop_by_pid_file ".mqtt_monitor.pid" "Monitor MQTT"

# Detener por nombre de proceso (fallback)
echo ""
echo -e "${YELLOW}🔍 Buscando procesos adicionales...${NC}"

stop_by_name "python.*socket_server.py" "Socket Server (by name)"
stop_by_name "python.*socket_bridge.py" "Flask Bridge (by name)"
stop_by_name "python.*mqtt_subscriber.py" "Monitor MQTT (by name)"
stop_by_name "node.*next-server" "Frontend Next.js (by name)"

# Detener contenedores Docker
echo ""
echo -e "${YELLOW}🐳 Deteniendo contenedores Docker...${NC}"

if command -v docker-compose &> /dev/null; then
    docker-compose down 2>/dev/null
elif command -v docker &> /dev/null; then
    docker compose down 2>/dev/null
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Contenedores Docker detenidos${NC}"
else
    echo -e "${CYAN}ℹ️  No hay contenedores corriendo${NC}"
fi

# Limpiar archivos PID residuales
rm -f .socket_server.pid .bridge.pid .frontend.pid .mqtt_monitor.pid

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Sistema detenido completamente${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${CYAN}Para reiniciar:${NC}"
echo -e "  ./start-mqtt.sh --con-mqtt    ${CYAN}# Con MQTT${NC}"
echo -e "  ./start-backend.sh --run      ${CYAN}# Sin MQTT${NC}"
echo ""
