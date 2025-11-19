#!/bin/bash

# Script de instalación y configuración automática para Azure VM
# Sistema Bancario Distribuido - Backend

set -e  # Salir si hay error

echo "=========================================="
echo "  Sistema Bancario - Setup Azure VM"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar si se ejecuta como root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}No ejecutar como root. Usa tu usuario normal.${NC}"
   exit 1
fi

# 1. Actualizar sistema
echo -e "${GREEN}[1/8] Actualizando sistema...${NC}"
sudo apt update && sudo apt upgrade -y

# 2. Instalar Python y dependencias
echo -e "${GREEN}[2/8] Instalando Python 3.12 y dependencias...${NC}"
sudo apt install -y python3.12 python3-pip python3.12-venv git supervisor

# 3. Crear directorio de trabajo
echo -e "${GREEN}[3/8] Configurando directorio de trabajo...${NC}"
cd ~
if [ -d "ExamenDistribuidos" ]; then
    echo -e "${YELLOW}Directorio ExamenDistribuidos ya existe. Saltando clonación.${NC}"
else
    echo -e "${YELLOW}Por favor, clona tu repositorio manualmente:${NC}"
    echo "git clone https://github.com/TU_USUARIO/ExamenDistribuidos.git"
    exit 1
fi

cd ExamenDistribuidos

# 4. Crear entorno virtual
echo -e "${GREEN}[4/8] Creando entorno virtual...${NC}"
python3.12 -m venv venv
source venv/bin/activate

# 5. Instalar requirements
echo -e "${GREEN}[5/8] Instalando dependencias Python...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 6. Configurar variables de entorno
echo -e "${GREEN}[6/8] Configurando variables de entorno...${NC}"
if [ ! -f ".env" ]; then
    cp .env.production .env
    echo -e "${YELLOW}Archivo .env creado. Por favor, editarlo con tus credenciales:${NC}"
    echo "nano .env"
    echo ""
    echo "Presiona Enter cuando hayas editado .env..."
    read
fi

# 7. Inicializar base de datos
echo -e "${GREEN}[7/8] Inicializando base de datos...${NC}"
python db_setup.py

# 8. Configurar Supervisor
echo -e "${GREEN}[8/8] Configurando Supervisor...${NC}"

# Socket Server
sudo tee /etc/supervisor/conf.d/socket_server.conf > /dev/null <<EOF
[program:socket_server]
command=$HOME/ExamenDistribuidos/venv/bin/python socket_server.py
directory=$HOME/ExamenDistribuidos
user=$USER
autostart=true
autorestart=true
stderr_logfile=/var/log/socket_server.err.log
stdout_logfile=/var/log/socket_server.out.log
environment=PATH="$HOME/ExamenDistribuidos/venv/bin"
EOF

# Bridge Flask
sudo tee /etc/supervisor/conf.d/bridge.conf > /dev/null <<EOF
[program:bridge]
command=$HOME/ExamenDistribuidos/venv/bin/python socket_bridge.py
directory=$HOME/ExamenDistribuidos
user=$USER
autostart=true
autorestart=true
stderr_logfile=/var/log/bridge.err.log
stdout_logfile=/var/log/bridge.out.log
environment=PATH="$HOME/ExamenDistribuidos/venv/bin"
EOF

# Recargar Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start socket_server bridge

echo ""
echo -e "${GREEN}=========================================="
echo "  ✅ Instalación Completada"
echo "==========================================${NC}"
echo ""
echo "Estado de servicios:"
sudo supervisorctl status
echo ""
echo -e "${YELLOW}Comandos útiles:${NC}"
echo "  Ver logs socket:  sudo tail -f /var/log/socket_server.out.log"
echo "  Ver logs bridge:  sudo tail -f /var/log/bridge.out.log"
echo "  Reiniciar:        sudo supervisorctl restart socket_server bridge"
echo "  Estado:           sudo supervisorctl status"
echo ""
echo -e "${GREEN}No olvides configurar el firewall de Azure para los puertos 5000 y 5001${NC}"
