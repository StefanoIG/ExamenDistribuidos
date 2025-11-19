#!/bin/bash
# Script de inicio para Backend - Sistema Bancario Distribuido
# Uso: 
#   ./start-backend.sh          # Setup completo + inicio
#   ./start-backend.sh --run    # Solo inicio (sin setup)

set -e  # Salir si hay error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================${NC}"
echo -e "${GREEN}🏦 Sistema Bancario - Backend${NC}"
echo -e "${CYAN}================================${NC}"
echo ""

# Verificar si solo queremos ejecutar (sin setup)
RUN_ONLY=false
if [[ "$1" == "--run" || "$1" == "-r" ]]; then
    RUN_ONLY=true
    echo -e "${YELLOW}⚡ Modo rápido: Solo inicio (sin setup)${NC}"
    echo ""
fi

# ========================================
# FASE 1: SETUP (solo si no es --run)
# ========================================

if [ "$RUN_ONLY" = false ]; then
    echo -e "${BLUE}📦 Fase 1: Configuración e instalación${NC}"
    echo ""

    # 1. Verificar Python
    echo -e "${YELLOW}🐍 Verificando Python...${NC}"
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 no está instalado${NC}"
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
    echo ""

    # 2. Crear entorno virtual si no existe
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}📦 Creando entorno virtual...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}✅ Entorno virtual creado${NC}"
    else
        echo -e "${GREEN}✅ Entorno virtual ya existe${NC}"
    fi
    echo ""

    # 3. Activar entorno virtual
    echo -e "${YELLOW}🔄 Activando entorno virtual...${NC}"
    source venv/bin/activate
    echo -e "${GREEN}✅ Entorno virtual activado${NC}"
    echo ""

    # 4. Actualizar pip
    echo -e "${YELLOW}📥 Actualizando pip...${NC}"
    pip install --upgrade pip -q
    echo -e "${GREEN}✅ pip actualizado${NC}"
    echo ""

    # 5. Instalar dependencias
    echo -e "${YELLOW}📚 Instalando dependencias desde requirements.txt...${NC}"
    pip install -r requirements.txt -q
    echo -e "${GREEN}✅ Dependencias instaladas${NC}"
    echo ""

    # 6. Verificar archivo .env
    echo -e "${YELLOW}⚙️  Verificando configuración (.env)...${NC}"
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  Archivo .env no encontrado, creando desde .env.example...${NC}"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${GREEN}✅ Archivo .env creado${NC}"
            echo -e "${RED}⚠️  IMPORTANTE: Edita .env con tus credenciales de base de datos${NC}"
        else
            echo -e "${RED}❌ No existe .env.example${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ Archivo .env existe${NC}"
    fi
    echo ""

    # 7. Verificar Docker (para MySQL y MQTT)
    echo -e "${YELLOW}🐳 Verificando Docker...${NC}"
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✅ Docker instalado${NC}"
        
        # Verificar si docker-compose está disponible
        if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
            echo -e "${GREEN}✅ Docker Compose disponible${NC}"
        else
            echo -e "${YELLOW}⚠️  Docker Compose no encontrado${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Docker no instalado (MySQL y MQTT deben estar corriendo externamente)${NC}"
    fi
    echo ""

    # 8. Inicializar base de datos
    echo -e "${YELLOW}🗄️  Inicializando base de datos...${NC}"
    python3 db_setup.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Base de datos inicializada${NC}"
    else
        echo -e "${RED}❌ Error inicializando base de datos${NC}"
        echo -e "${YELLOW}   Verifica que MySQL esté corriendo y las credenciales en .env sean correctas${NC}"
        exit 1
    fi
    echo ""

    echo -e "${GREEN}✅ Setup completado exitosamente${NC}"
    echo ""

else
    # Modo --run: solo activar venv
    source venv/bin/activate
fi

# ========================================
# FASE 2: INICIAR SERVICIOS
# ========================================

echo -e "${BLUE}🚀 Fase 2: Iniciando servicios del backend${NC}"
echo ""

# Función para verificar si un puerto está en uso
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Puerto en uso
    else
        return 1  # Puerto libre
    fi
}

# Función para matar proceso en un puerto
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}⚠️  Puerto $port en uso (PID: $pid), deteniendo...${NC}"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

# Limpiar puertos si están ocupados
echo -e "${YELLOW}🧹 Limpiando puertos previos...${NC}"
kill_port 5000  # Socket Server
kill_port 5001  # Flask Bridge
echo -e "${GREEN}✅ Puertos liberados${NC}"
echo ""

# Leer variables del .env
source .env 2>/dev/null || true

# 1. Verificar/Iniciar MySQL
echo -e "${YELLOW}🗄️  Verificando MySQL...${NC}"
if check_port ${DB_PORT:-3306}; then
    echo -e "${GREEN}✅ MySQL corriendo en puerto ${DB_PORT:-3306}${NC}"
else
    echo -e "${YELLOW}⚠️  MySQL no detectado en puerto ${DB_PORT:-3306}${NC}"
    echo -e "${YELLOW}   Intentando iniciar con Docker...${NC}"
    
    if command -v docker &> /dev/null; then
        docker-compose up -d mysql 2>/dev/null || docker compose up -d mysql 2>/dev/null || true
        echo -e "${YELLOW}   Esperando a que MySQL esté listo...${NC}"
        sleep 5
    else
        echo -e "${RED}❌ Docker no disponible. Inicia MySQL manualmente${NC}"
        exit 1
    fi
fi
echo ""

# 2. Verificar/Iniciar MQTT Broker
echo -e "${YELLOW}📡 Verificando MQTT Broker...${NC}"
MQTT_PORT=${MQTT_BROKER_PORT:-1883}
if check_port $MQTT_PORT; then
    echo -e "${GREEN}✅ MQTT Broker corriendo en puerto $MQTT_PORT${NC}"
else
    echo -e "${YELLOW}⚠️  MQTT Broker no detectado en puerto $MQTT_PORT${NC}"
    echo -e "${YELLOW}   Intentando iniciar Mosquitto con Docker...${NC}"
    
    if command -v docker &> /dev/null; then
        docker-compose up -d mosquitto 2>/dev/null || docker compose up -d mosquitto 2>/dev/null || true
        echo -e "${YELLOW}   Esperando a que MQTT esté listo...${NC}"
        sleep 3
    else
        echo -e "${YELLOW}⚠️  Docker no disponible. MQTT opcional, continuando...${NC}"
    fi
fi
echo ""

# 3. Iniciar Socket Server
echo -e "${GREEN}🔌 Iniciando Socket Server (puerto ${SERVER_PORT:-5000})...${NC}"
python3 socket_server.py > logs/socket_server.log 2>&1 &
SOCKET_PID=$!
echo $SOCKET_PID > .socket_server.pid
sleep 2

if ps -p $SOCKET_PID > /dev/null; then
    echo -e "${GREEN}✅ Socket Server iniciado (PID: $SOCKET_PID)${NC}"
else
    echo -e "${RED}❌ Error iniciando Socket Server${NC}"
    echo -e "${YELLOW}   Ver logs/socket_server.log para detalles${NC}"
    exit 1
fi
echo ""

# 4. Iniciar Flask Bridge
echo -e "${GREEN}🌉 Iniciando Flask Bridge (puerto ${BRIDGE_PORT:-5001})...${NC}"
python3 socket_bridge.py > logs/bridge.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > .bridge.pid
sleep 2

if ps -p $BRIDGE_PID > /dev/null; then
    echo -e "${GREEN}✅ Flask Bridge iniciado (PID: $BRIDGE_PID)${NC}"
else
    echo -e "${RED}❌ Error iniciando Flask Bridge${NC}"
    echo -e "${YELLOW}   Ver logs/bridge.log para detalles${NC}"
    kill $SOCKET_PID 2>/dev/null || true
    exit 1
fi
echo ""

# ========================================
# RESUMEN
# ========================================

echo -e "${CYAN}================================${NC}"
echo -e "${GREEN}✅ Backend iniciado correctamente${NC}"
echo -e "${CYAN}================================${NC}"
echo ""
echo -e "${BLUE}📍 Servicios corriendo:${NC}"
echo -e "   ${GREEN}•${NC} MySQL:         localhost:${DB_PORT:-3306}"
echo -e "   ${GREEN}•${NC} MQTT Broker:   localhost:${MQTT_PORT:-1883}"
echo -e "   ${GREEN}•${NC} Socket Server: localhost:${SERVER_PORT:-5000} ${YELLOW}(PID: $SOCKET_PID)${NC}"
echo -e "   ${GREEN}•${NC} Flask Bridge:  localhost:${BRIDGE_PORT:-5001} ${YELLOW}(PID: $BRIDGE_PID)${NC}"
echo ""
echo -e "${BLUE}📊 Logs:${NC}"
echo -e "   ${CYAN}•${NC} Socket Server: logs/socket_server.log"
echo -e "   ${CYAN}•${NC} Flask Bridge:  logs/bridge.log"
echo ""
echo -e "${BLUE}📚 Comandos útiles:${NC}"
echo -e "   ${CYAN}•${NC} Ver logs Socket:  tail -f logs/socket_server.log"
echo -e "   ${CYAN}•${NC} Ver logs Bridge:  tail -f logs/bridge.log"
echo -e "   ${CYAN}•${NC} Monitor MQTT:     python3 mqtt_subscriber.py"
echo -e "   ${CYAN}•${NC} Detener backend:  ./stop-backend.sh"
echo ""
echo -e "${YELLOW}🛑 Para detener: Ejecuta ./stop-backend.sh o presiona Ctrl+C${NC}"
echo ""

# Mantener script corriendo para capturar Ctrl+C
trap "echo ''; echo -e '${YELLOW}🛑 Deteniendo backend...${NC}'; kill $SOCKET_PID $BRIDGE_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Esperar a que los procesos terminen
wait
