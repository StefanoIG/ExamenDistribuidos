#!/bin/bash

# ============================================
# COMANDOS RÁPIDOS PARA PRODUCCIÓN
# Sistema Bancario Distribuido
# ============================================

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

function show_menu() {
    clear
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Sistema Bancario - Comandos Rápidos${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo "1.  Ver estado de servicios"
    echo "2.  Reiniciar todos los servicios"
    echo "3.  Ver logs en tiempo real"
    echo "4.  Test de conexión a MySQL"
    echo "5.  Ver IP pública de la VM"
    echo "6.  Test de API endpoints"
    echo "7.  Ver uso de recursos (CPU/RAM)"
    echo "8.  Actualizar código desde GitHub"
    echo "9.  Ver últimos 50 logs de errores"
    echo "10. Backup de base de datos"
    echo "0.  Salir"
    echo ""
    echo -n "Selecciona una opción: "
}

function check_services() {
    echo -e "${YELLOW}Verificando servicios...${NC}"
    sudo supervisorctl status
    echo ""
    echo -e "${YELLOW}Nginx status:${NC}"
    sudo systemctl status nginx --no-pager | head -10
}

function restart_services() {
    echo -e "${YELLOW}Reiniciando servicios...${NC}"
    sudo supervisorctl restart all
    sleep 2
    sudo supervisorctl status
}

function tail_logs() {
    echo -e "${YELLOW}Logs en tiempo real (Ctrl+C para salir)${NC}"
    echo ""
    echo "1. Socket Server (stdout)"
    echo "2. Flask Bridge (stdout)"
    echo "3. Socket Server (errores)"
    echo "4. Flask Bridge (errores)"
    echo "5. Nginx (access)"
    echo "6. Nginx (error)"
    echo ""
    read -p "Selecciona log: " log_choice
    
    case $log_choice in
        1) sudo tail -f /var/log/socket_server.out.log ;;
        2) sudo tail -f /var/log/bridge.out.log ;;
        3) sudo tail -f /var/log/socket_server.err.log ;;
        4) sudo tail -f /var/log/bridge.err.log ;;
        5) sudo tail -f /var/log/nginx/access.log ;;
        6) sudo tail -f /var/log/nginx/error.log ;;
        *) echo "Opción inválida" ;;
    esac
}

function test_mysql() {
    echo -e "${YELLOW}Test de conexión a MySQL...${NC}"
    
    # Cargar variables de .env
    if [ -f "$HOME/ExamenDistribuidos/.env" ]; then
        source <(grep -v '^#' $HOME/ExamenDistribuidos/.env | sed 's/^/export /')
        
        echo "Host: $DB_HOST"
        echo "User: $DB_USER"
        echo "Database: $DB_NAME"
        echo ""
        
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT COUNT(*) as total_clientes FROM clientes; SELECT COUNT(*) as total_transacciones FROM transacciones;"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Conexión exitosa${NC}"
        else
            echo -e "${RED}✗ Error de conexión${NC}"
        fi
    else
        echo -e "${RED}.env no encontrado${NC}"
    fi
}

function show_public_ip() {
    echo -e "${YELLOW}Obteniendo IP pública...${NC}"
    PUBLIC_IP=$(curl -s ifconfig.me)
    echo -e "${GREEN}IP Pública: $PUBLIC_IP${NC}"
    echo ""
    echo "URLs de tu aplicación:"
    echo "  API: http://$PUBLIC_IP/api/"
    echo "  Stats: http://$PUBLIC_IP/api/stats"
}

function test_api() {
    echo -e "${YELLOW}Testeando API endpoints...${NC}"
    echo ""
    
    echo -e "${BLUE}1. Stats:${NC}"
    curl -s http://localhost/api/stats | jq . || echo "Error"
    echo ""
    
    echo -e "${BLUE}2. Test crear cuenta:${NC}"
    curl -s -X POST http://localhost/api/crear \
        -H "Content-Type: application/json" \
        -d '{"cedula":"0TEST12345","nombre":"Test API"}' | jq .
    echo ""
    
    echo -e "${BLUE}3. Test consulta:${NC}"
    curl -s -X POST http://localhost/api/consulta \
        -H "Content-Type: application/json" \
        -d '{"cedula":"0TEST12345"}' | jq .
}

function show_resources() {
    echo -e "${YELLOW}Uso de recursos:${NC}"
    echo ""
    echo -e "${BLUE}CPU y RAM:${NC}"
    top -bn1 | head -20
    echo ""
    echo -e "${BLUE}Disco:${NC}"
    df -h | grep -v loop
    echo ""
    echo -e "${BLUE}Conexiones Python activas:${NC}"
    sudo netstat -tlnp | grep python
}

function update_code() {
    echo -e "${YELLOW}Actualizando código desde GitHub...${NC}"
    cd $HOME/ExamenDistribuidos
    
    echo "Haciendo backup de .env..."
    cp .env .env.backup
    
    echo "Haciendo git pull..."
    git pull origin main
    
    echo "Restaurando .env..."
    cp .env.backup .env
    
    echo "Activando venv..."
    source venv/bin/activate
    
    echo "Instalando dependencias..."
    pip install -r requirements.txt
    
    echo "Reiniciando servicios..."
    sudo supervisorctl restart all
    
    echo -e "${GREEN}✓ Actualización completa${NC}"
    sudo supervisorctl status
}

function show_error_logs() {
    echo -e "${YELLOW}Últimos 50 errores:${NC}"
    echo ""
    echo -e "${BLUE}Socket Server:${NC}"
    sudo tail -50 /var/log/socket_server.err.log
    echo ""
    echo -e "${BLUE}Flask Bridge:${NC}"
    sudo tail -50 /var/log/bridge.err.log
}

function backup_database() {
    echo -e "${YELLOW}Backup de base de datos...${NC}"
    
    # Cargar variables
    if [ -f "$HOME/ExamenDistribuidos/.env" ]; then
        source <(grep -v '^#' $HOME/ExamenDistribuidos/.env | sed 's/^/export /')
        
        BACKUP_DIR="$HOME/backups"
        mkdir -p $BACKUP_DIR
        
        BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
        
        echo "Creando backup en: $BACKUP_FILE"
        mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Backup creado exitosamente${NC}"
            echo "Tamaño: $(du -h $BACKUP_FILE | cut -f1)"
            
            # Comprimir
            gzip "$BACKUP_FILE"
            echo "Comprimido: ${BACKUP_FILE}.gz"
        else
            echo -e "${RED}✗ Error creando backup${NC}"
        fi
    else
        echo -e "${RED}.env no encontrado${NC}"
    fi
}

# Main loop
while true; do
    show_menu
    read choice
    
    case $choice in
        1) check_services ;;
        2) restart_services ;;
        3) tail_logs ;;
        4) test_mysql ;;
        5) show_public_ip ;;
        6) test_api ;;
        7) show_resources ;;
        8) update_code ;;
        9) show_error_logs ;;
        10) backup_database ;;
        0) echo "¡Hasta luego!"; exit 0 ;;
        *) echo -e "${RED}Opción inválida${NC}" ;;
    esac
    
    echo ""
    read -p "Presiona Enter para continuar..."
done
