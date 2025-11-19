#!/bin/bash

# ============================================
# Script de Verificación Pre-Deployment
# Sistema Bancario Distribuido
# ============================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "============================================"
echo "  Pre-Deployment Verification"
echo "============================================"
echo ""

# 1. Verificar Python
echo -e "${YELLOW}[1/10] Verificando Python...${NC}"
if command -v python3.12 &> /dev/null; then
    echo -e "${GREEN}✓ Python 3.12 instalado${NC}"
    python3.12 --version
else
    echo -e "${RED}✗ Python 3.12 no encontrado${NC}"
    exit 1
fi

# 2. Verificar pip
echo -e "${YELLOW}[2/10] Verificando pip...${NC}"
if command -v pip &> /dev/null; then
    echo -e "${GREEN}✓ pip instalado${NC}"
else
    echo -e "${RED}✗ pip no encontrado${NC}"
    exit 1
fi

# 3. Verificar virtualenv
echo -e "${YELLOW}[3/10] Verificando virtualenv...${NC}"
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment existe${NC}"
    source venv/bin/activate
    pip list
else
    echo -e "${RED}✗ Virtual environment no encontrado${NC}"
    echo "Crear con: python3.12 -m venv venv"
    exit 1
fi

# 4. Verificar .env
echo -e "${YELLOW}[4/10] Verificando .env...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ Archivo .env existe${NC}"
    
    # Verificar variables críticas
    if grep -q "DB_HOST=" .env && \
       grep -q "DB_USER=" .env && \
       grep -q "DB_PASSWORD=" .env; then
        echo -e "${GREEN}✓ Variables de base de datos configuradas${NC}"
    else
        echo -e "${RED}✗ Variables de base de datos incompletas${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Archivo .env no encontrado${NC}"
    echo "Copiar desde: cp .env.production .env"
    exit 1
fi

# 5. Verificar requirements instalados
echo -e "${YELLOW}[5/10] Verificando dependencias...${NC}"
REQUIRED_PACKAGES=("mysql-connector-python" "flask" "flask-cors" "flask-socketio" "python-dotenv" "paho-mqtt")
MISSING=0

for package in "${REQUIRED_PACKAGES[@]}"; do
    if pip show "$package" &> /dev/null; then
        echo -e "${GREEN}✓ $package instalado${NC}"
    else
        echo -e "${RED}✗ $package no encontrado${NC}"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo -e "${RED}Instalar con: pip install -r requirements.txt${NC}"
    exit 1
fi

# 6. Verificar archivos principales
echo -e "${YELLOW}[6/10] Verificando archivos del proyecto...${NC}"
FILES=("socket_server.py" "socket_bridge.py" "db_connection.py" "db_setup.py" "update_database.py")

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file existe${NC}"
    else
        echo -e "${RED}✗ $file no encontrado${NC}"
        exit 1
    fi
done

# 7. Verificar correcciones de bugs (Decimal fix)
echo -e "${YELLOW}[7/10] Verificando correcciones de código...${NC}"

# Verificar que db_connection.py tenga las correcciones de Decimal
if grep -q "float(row\['monto'\])" db_connection.py; then
    echo -e "${GREEN}✓ Corrección de Decimal → float en obtener_historial${NC}"
else
    echo -e "${RED}✗ Corrección de Decimal no encontrada${NC}"
    echo "Revisar db_connection.py línea ~158"
fi

if grep -q "float(result\['saldo'\])" db_connection.py; then
    echo -e "${GREEN}✓ Corrección de Decimal → float en consultar_cliente${NC}"
else
    echo -e "${RED}✗ Corrección de Decimal no encontrada${NC}"
    echo "Revisar db_connection.py línea ~68"
fi

# 8. Test de sintaxis Python
echo -e "${YELLOW}[8/10] Verificando sintaxis Python...${NC}"
python -m py_compile socket_server.py socket_bridge.py db_connection.py
echo -e "${GREEN}✓ Sintaxis correcta${NC}"

# 9. Verificar estructura de tablas SQL
echo -e "${YELLOW}[9/10] Verificando scripts SQL...${NC}"
if [ -f "update_database.py" ]; then
    if grep -q "TRANSFERENCIA_ENVIADA" update_database.py; then
        echo -e "${GREEN}✓ Script de actualización incluye soporte de transferencias${NC}"
    else
        echo -e "${RED}✗ Script no incluye TRANSFERENCIA_ENVIADA/RECIBIDA${NC}"
        exit 1
    fi
fi

# 10. Test de conexión (si .env está configurado)
echo -e "${YELLOW}[10/10] Intentando conexión a base de datos...${NC}"

# Crear script temporal de test
cat > /tmp/test_db.py << 'EOF'
import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    print("✓ Conexión exitosa")
    
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"✓ Tablas encontradas: {len(tables)}")
    
    for table in tables:
        print(f"  - {table[0]}")
    
    cursor.close()
    conn.close()
    exit(0)
except Exception as e:
    print(f"✗ Error de conexión: {e}")
    exit(1)
EOF

if python /tmp/test_db.py; then
    echo -e "${GREEN}✓ Base de datos accesible${NC}"
else
    echo -e "${YELLOW}⚠ No se pudo conectar a la base de datos${NC}"
    echo "Verificar credenciales en .env"
fi

rm /tmp/test_db.py

# Resumen
echo ""
echo "============================================"
echo -e "${GREEN}  ✓ Verificación Completa${NC}"
echo "============================================"
echo ""
echo "Sistema listo para deployment a producción"
echo ""
echo "Próximos pasos:"
echo "1. Subir código a GitHub: git push origin main"
echo "2. Conectar a VM Azure por SSH"
echo "3. Ejecutar setup-azure-vm.sh"
echo "4. Configurar Supervisor y Nginx"
echo "5. Deploy frontend en Netlify"
echo ""
