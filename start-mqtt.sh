#!/bin/bash
# Script de inicio completo - Sistema Bancario con MQTT
# Uso: ./start-mqtt.sh [--con-mqtt] [--solo-mqtt] [--monitor]

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
FRONTEND_DIR="$PROJECT_DIR/Frontend"
LOGS_DIR="$PROJECT_DIR/logs"

# Variables de control
CON_MQTT=false
SOLO_MQTT=false
MONITOR=false

# Procesar argumentos
for arg in "$@"; do
    case $arg in
        --con-mqtt)
            CON_MQTT=true
            ;;
        --solo-mqtt)
            SOLO_MQTT=true
            ;;
        --monitor)
            MONITOR=true
            ;;
        *)
            echo -e "${RED}Argumento desconocido: $arg${NC}"
            echo "Uso: $0 [--con-mqtt] [--solo-mqtt] [--monitor]"
            exit 1
            ;;
    esac
done

# Crear directorio de logs si no existe
mkdir -p "$LOGS_DIR"

# Banner
echo -e "${CYAN}================================${NC}"
echo -e "${GREEN}🏦 Sistema Bancario Distribuido${NC}"
echo -e "${YELLOW}   Con soporte MQTT${NC}"
echo -e "${CYAN}================================${NC}"
echo ""

# Función para matar procesos previos
cleanup_processes() {
    echo -e "${YELLOW}🧹 Limpiando procesos previos...${NC}"
    
    # Matar procesos Python
    pkill -f "python.*socket_server.py" 2>/dev/null
    pkill -f "python.*socket_bridge.py" 2>/dev/null
    pkill -f "python.*mqtt_subscriber.py" 2>/dev/null
    
    # Matar procesos Node
    pkill -f "node.*next-server" 2>/dev/null
    pkill -f "npm.*dev" 2>/dev/null
    
    sleep 2
}

# Modo: Solo MQTT
if [ "$SOLO_MQTT" = true ]; then
    echo -e "${GREEN}📡 Iniciando solo broker MQTT...${NC}"
    docker-compose up mosquitto
    exit 0
fi

# Modo: Monitor MQTT
if [ "$MONITOR" = true ]; then
    echo -e "${GREEN}👂 Iniciando monitor MQTT...${NC}"
    echo -e "${YELLOW}Presiona Ctrl+C para salir${NC}"
    echo ""
    
    # Activar entorno virtual
    source "$VENV_DIR/bin/activate"
    python mqtt_subscriber.py
    exit 0
fi

# Limpiar procesos previos
cleanup_processes

# Iniciar MQTT Broker con Docker
if [ "$CON_MQTT" = true ]; then
    echo -e "${GREEN}📡 Iniciando MQTT Broker (Mosquitto)...${NC}"
    echo -e "${YELLOW}   Si no tienes Docker, el sistema funcionará sin MQTT${NC}"
    
    # Verificar si Docker está disponible
    if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
        # Intentar iniciar con docker-compose
        if command -v docker-compose &> /dev/null; then
            docker-compose up -d mosquitto 2>/dev/null
        else
            docker compose up -d mosquitto 2>/dev/null
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ MQTT Broker iniciado${NC}"
            sleep 3
        else
            echo -e "${YELLOW}⚠️  No se pudo iniciar MQTT (Docker no disponible)${NC}"
            echo -e "${YELLOW}   El sistema funcionará sin MQTT${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Docker no encontrado${NC}"
        echo -e "${YELLOW}   El sistema funcionará sin MQTT${NC}"
    fi
else
    echo -e "${CYAN}ℹ️  MQTT deshabilitado (usa --con-mqtt para habilitar)${NC}"
fi

# Activar entorno virtual Python
echo -e "${GREEN}🐍 Activando entorno virtual...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ Error: Entorno virtual no encontrado en $VENV_DIR${NC}"
    echo -e "${YELLOW}   Ejecuta primero: ./start-backend.sh${NC}"
    exit 1
fi
source "$VENV_DIR/bin/activate"

# Iniciar Base de Datos
echo -e "${GREEN}🗄️  Iniciando MySQL...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose up -d mysql 2>/dev/null
else
    docker compose up -d mysql 2>/dev/null
fi
sleep 5

# Iniciar Socket Server
echo -e "${GREEN}🔌 Iniciando Socket Server (Puerto 5000)...${NC}"
cd "$PROJECT_DIR"
nohup python socket_server.py > "$LOGS_DIR/socket_server.log" 2>&1 &
SOCKET_PID=$!
echo $SOCKET_PID > .socket_server.pid
echo -e "${CYAN}   PID: $SOCKET_PID${NC}"
sleep 3

# Iniciar Flask Bridge
echo -e "${GREEN}🌉 Iniciando Flask Bridge (Puerto 5001)...${NC}"
nohup python socket_bridge.py > "$LOGS_DIR/bridge.log" 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > .bridge.pid
echo -e "${CYAN}   PID: $BRIDGE_PID${NC}"
sleep 3

# Iniciar Frontend
echo -e "${GREEN}⚛️  Iniciando Frontend (Puerto 3000)...${NC}"
cd "$FRONTEND_DIR"
nohup npm run dev > "$LOGS_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > .frontend.pid
echo -e "${CYAN}   PID: $FRONTEND_PID${NC}"
cd "$PROJECT_DIR"
sleep 3

# Iniciar Monitor MQTT (en background)
if [ "$CON_MQTT" = true ]; then
    echo -e "${GREEN}👂 Iniciando Monitor MQTT...${NC}"
    nohup python mqtt_subscriber.py > "$LOGS_DIR/mqtt_monitor.log" 2>&1 &
    MQTT_PID=$!
    echo $MQTT_PID > .mqtt_monitor.pid
    echo -e "${CYAN}   PID: $MQTT_PID${NC}"
fi

# Resumen
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Sistema iniciado correctamente${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${CYAN}📍 Servicios disponibles:${NC}"
echo -e "   - Socket Server:  localhost:5000 ${CYAN}(PID: $SOCKET_PID)${NC}"
echo -e "   - Flask Bridge:   localhost:5001 ${CYAN}(PID: $BRIDGE_PID)${NC}"
echo -e "   - Frontend:       http://localhost:3000 ${CYAN}(PID: $FRONTEND_PID)${NC}"

if [ "$CON_MQTT" = true ]; then
    echo -e "   - MQTT Broker:    localhost:1883"
    echo -e "   - MQTT WebSocket: localhost:9001"
    echo -e "   - Monitor MQTT:   ${CYAN}(PID: $MQTT_PID)${NC}"
fi

echo ""
echo -e "${YELLOW}📚 Comandos útiles:${NC}"
echo -e "${CYAN}   ./start-mqtt.sh --con-mqtt     ${NC}# Iniciar con MQTT"
echo -e "${CYAN}   ./start-mqtt.sh --solo-mqtt    ${NC}# Solo broker MQTT"
echo -e "${CYAN}   ./start-mqtt.sh --monitor      ${NC}# Solo monitor MQTT"
echo -e "${CYAN}   ./stop-backend.sh              ${NC}# Detener todos los servicios"
echo ""
echo -e "${YELLOW}📄 Ver logs:${NC}"
echo -e "${CYAN}   tail -f logs/socket_server.log ${NC}# Socket Server"
echo -e "${CYAN}   tail -f logs/bridge.log        ${NC}# Flask Bridge"
echo -e "${CYAN}   tail -f logs/frontend.log      ${NC}# Frontend"
if [ "$CON_MQTT" = true ]; then
    echo -e "${CYAN}   tail -f logs/mqtt_monitor.log  ${NC}# Monitor MQTT"
fi
echo ""
echo -e "${RED}🛑 Para detener: ./stop-backend.sh${NC}"
echo ""
