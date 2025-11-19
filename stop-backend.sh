#!/bin/bash
# Script para detener el backend del Sistema Bancario

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Deteniendo Backend...${NC}"
echo ""

# Función para matar proceso por PID file
kill_pid_file() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}   Deteniendo $service_name (PID: $pid)...${NC}"
            kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null
            rm "$pid_file"
            echo -e "${GREEN}   ✅ $service_name detenido${NC}"
        else
            rm "$pid_file"
            echo -e "${YELLOW}   ⚠️  $service_name ya no está corriendo${NC}"
        fi
    else
        echo -e "${YELLOW}   ⚠️  No se encontró PID file para $service_name${NC}"
    fi
}

# Función para matar proceso por puerto
kill_port() {
    local port=$1
    local service_name=$2
    local pid=$(lsof -ti:$port 2>/dev/null)
    
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}   Deteniendo $service_name en puerto $port (PID: $pid)...${NC}"
        kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null
        echo -e "${GREEN}   ✅ $service_name detenido${NC}"
    fi
}

# Detener servicios usando PID files
kill_pid_file ".socket_server.pid" "Socket Server"
kill_pid_file ".bridge.pid" "Flask Bridge"

echo ""

# Fallback: Detener por puerto si quedaron procesos
echo -e "${YELLOW}🧹 Limpiando puertos...${NC}"
kill_port 5000 "Socket Server"
kill_port 5001 "Flask Bridge"

echo ""
echo -e "${GREEN}✅ Backend detenido correctamente${NC}"
echo ""
