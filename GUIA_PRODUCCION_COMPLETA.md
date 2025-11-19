# 🚀 Guía Completa de Deployment a Producción

**Sistema Bancario Distribuido - Backend + Frontend**  
**Fecha:** 19 de Noviembre de 2025  
**Arquitectura:** Azure VM (Backend) + Netlify (Frontend) + Azure MySQL (Base de Datos)

---

## 📋 Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Paso 1: Base de Datos Azure MySQL](#paso-1-base-de-datos-azure-mysql)
3. [Paso 2: Máquina Virtual Azure](#paso-2-máquina-virtual-azure)
4. [Paso 3: Deploy del Backend](#paso-3-deploy-del-backend)
5. [Paso 4: Deploy del Frontend](#paso-4-deploy-del-frontend)
6. [Paso 5: Verificación Final](#paso-5-verificación-final)
7. [Troubleshooting](#troubleshooting)

---

## Pre-requisitos

### ✅ Cuentas Necesarias
- [ ] Cuenta de Azure (con créditos estudiantiles o suscripción)
- [ ] Cuenta de GitHub (repositorio del proyecto)
- [ ] Cuenta de Netlify (gratis)

### ✅ Archivos Preparados
- [ ] Código backend actualizado con últimos cambios
- [ ] Código frontend compilado y testeado localmente
- [ ] Variables de entorno documentadas

### ✅ Conocimientos Previos
- Comandos básicos de Linux (SSH, navegación)
- Git básico (clone, push, pull)
- Conceptos de networking (puertos, firewalls)

---

## Paso 1: Base de Datos Azure MySQL

> **⏱️ Tiempo estimado:** 15-20 minutos

### 1.1 Crear Azure Database for MySQL

1. **Ir a Azure Portal**
   - URL: https://portal.azure.com
   - Login con tu cuenta

2. **Crear Recurso**
   ```
   Buscar: "Azure Database for MySQL"
   → Click en "Create"
   → Seleccionar: "Flexible Server" (recomendado)
   ```

3. **Configuración Básica**
   ```
   Subscription: Tu suscripción
   Resource Group: Crear nuevo "rg-examen-distribuidos"
   Server name: examen-distribuidos-db
   Region: East US (o más cercano a ti)
   MySQL version: 8.0
   
   Compute + Storage:
   - Burstable, B1ms (1-2 vCores, 2 GiB RAM)
   - Storage: 20 GB
   - Backup retention: 7 días
   ```

4. **Credenciales Admin**
   ```
   Admin username: adminuser
   Password: [Tu password seguro]
   Confirmar password: [Repetir password]
   ```
   
   > ⚠️ **IMPORTANTE:** Guardar estas credenciales en un lugar seguro

5. **Networking**
   ```
   Connectivity method: "Public access"
   
   Firewall rules:
   ✅ Add current client IP address
   ✅ Allow public access from any Azure service
   
   Agregar regla personalizada:
   - Rule name: AllowAll (solo para testing, cambiar en prod)
   - Start IP: 0.0.0.0
   - End IP: 255.255.255.255
   ```

6. **Review + Create**
   - Revisar configuración
   - Click "Create"
   - **Esperar 5-10 minutos** mientras se aprovisiona

### 1.2 Configurar Base de Datos

1. **Conectar a MySQL**
   
   Opción A: Desde Azure Cloud Shell (recomendado)
   ```bash
   mysql -h examen-distribuidos-db.mysql.database.azure.com \
         -u adminuser \
         -p
   # Ingresar password cuando lo solicite
   ```

   Opción B: Desde tu PC con MySQL Workbench
   ```
   Connection Name: Azure Examen DB
   Hostname: examen-distribuidos-db.mysql.database.azure.com
   Port: 3306
   Username: adminuser
   Password: [tu password]
   ```

2. **Crear Base de Datos**
   ```sql
   CREATE DATABASE examen CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   USE examen;
   ```

3. **Crear Tablas**
   ```sql
   -- Tabla de clientes
   CREATE TABLE clientes (
       cedula VARCHAR(15) PRIMARY KEY,
       nombres VARCHAR(100) NOT NULL,
       apellidos VARCHAR(100) NOT NULL,
       saldo DECIMAL(10,2) DEFAULT 0.00,
       fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

   -- Tabla de transacciones (incluye transferencias)
   CREATE TABLE transacciones (
       id INT AUTO_INCREMENT PRIMARY KEY,
       cedula VARCHAR(15) NOT NULL,
       tipo ENUM('DEPOSITO', 'RETIRO', 'TRANSFERENCIA_ENVIADA', 'TRANSFERENCIA_RECIBIDA') NOT NULL,
       monto DECIMAL(10,2) NOT NULL,
       saldo_final DECIMAL(10,2) NOT NULL,
       fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       INDEX idx_cedula (cedula),
       INDEX idx_fecha (fecha),
       INDEX idx_tipo (tipo),
       FOREIGN KEY (cedula) REFERENCES clientes(cedula) ON DELETE CASCADE
   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
   ```

4. **Insertar Datos de Prueba**
   ```sql
   -- Cliente de prueba
   INSERT INTO clientes (cedula, nombres, apellidos, saldo) 
   VALUES ('1234567890', 'Usuario', 'Prueba', 1000.00);
   
   -- Verificar
   SELECT * FROM clientes;
   ```

5. **Anotar String de Conexión**
   ```
   Host: examen-distribuidos-db.mysql.database.azure.com
   Port: 3306
   Database: examen
   User: adminuser
   Password: [tu password]
   ```

---

## Paso 2: Máquina Virtual Azure

> **⏱️ Tiempo estimado:** 20-30 minutos

### 2.1 Crear VM Ubuntu

1. **Azure Portal → Virtual Machines**
   ```
   Click "Create" → "Azure virtual machine"
   ```

2. **Configuración Básica**
   ```
   Resource group: rg-examen-distribuidos (mismo que DB)
   VM name: vm-backend-examen
   Region: East US (misma región que DB)
   Image: Ubuntu Server 22.04 LTS - x64 Gen2
   Size: Standard_B1s (1 vCPU, 1 GiB RAM) - suficiente para testing
   ```

3. **Credenciales SSH**
   ```
   Authentication type: SSH public key
   Username: azureuser
   
   SSH public key source: 
   - Generate new key pair
   - Key pair name: vm-backend-examen_key
   
   ⚠️ DESCARGAR Y GUARDAR la clave privada (.pem)
   ```

4. **Networking**
   ```
   Virtual network: Crear nueva (default OK)
   Subnet: default
   Public IP: Crear nueva
   
   NIC network security group: Advanced
   Configure NSG: Crear nuevo
   
   Inbound rules:
   - SSH (22) - Tu IP
   - HTTP (80) - Any
   - Custom (5000) - Any (Socket Server)
   - Custom (5001) - Any (Flask Bridge)
   ```

5. **Review + Create**
   - Click "Create"
   - **DESCARGAR clave SSH** cuando aparezca
   - Esperar aprovisionamiento (5-10 min)

### 2.2 Conectar a la VM

1. **Obtener IP Pública**
   ```
   Azure Portal → Virtual Machines → vm-backend-examen
   → Overview → Public IP address
   
   Ejemplo: 20.185.123.45
   ```

2. **Conectar por SSH**
   
   **Windows (PowerShell):**
   ```powershell
   # Mover clave descargada a carpeta segura
   Move-Item "C:\Users\TU_USUARIO\Downloads\vm-backend-examen_key.pem" "$env:USERPROFILE\.ssh\"
   
   # Conectar
   ssh -i "$env:USERPROFILE\.ssh\vm-backend-examen_key.pem" azureuser@20.185.123.45
   ```

   **macOS/Linux:**
   ```bash
   # Mover y dar permisos
   mv ~/Downloads/vm-backend-examen_key.pem ~/.ssh/
   chmod 400 ~/.ssh/vm-backend-examen_key.pem
   
   # Conectar
   ssh -i ~/.ssh/vm-backend-examen_key.pem azureuser@20.185.123.45
   ```

3. **Verificar Conexión**
   ```bash
   # Deberías ver:
   azureuser@vm-backend-examen:~$
   ```

---

## Paso 3: Deploy del Backend

> **⏱️ Tiempo estimado:** 30-40 minutos

### 3.1 Preparar Entorno

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3.12 python3-pip python3.12-venv git supervisor nginx
```

### 3.2 Clonar Repositorio

```bash
# Ir a home
cd ~

# Clonar tu repositorio
git clone https://github.com/TU_USUARIO/ExamenDistribuidos.git

# Entrar al directorio
cd ExamenDistribuidos

# Verificar contenido
ls -la
```

### 3.3 Configurar Variables de Entorno

```bash
# Copiar template de producción
cp .env.production .env

# Editar con nano
nano .env
```

**Configurar con tus datos reales:**
```dotenv
# Base de Datos Azure MySQL
DB_HOST=examen-distribuidos-db.mysql.database.azure.com
DB_PORT=3306
DB_USER=adminuser
DB_PASSWORD=TU_PASSWORD_REAL_AQUI
DB_NAME=examen

# Servidores
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
BRIDGE_PORT=5001

# CORS (actualizar después con dominio de Netlify)
CORS_ORIGINS=https://localhost:3000,http://localhost:3000

# MQTT (opcional, dejar vacío si no usas)
MQTT_BROKER_HOST=
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Logging
LOG_LEVEL=INFO
DEBUG=False
```

**Guardar:** `Ctrl+X` → `Y` → `Enter`

### 3.4 Instalar Dependencias Python

```bash
# Crear entorno virtual
python3.12 -m venv venv

# Activar entorno
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar requirements
pip install -r requirements.txt

# Verificar instalación
pip list
```

### 3.5 Probar Conexión a Base de Datos

```bash
# Ejecutar setup (creará tablas si no existen)
python db_setup.py

# Ejecutar actualización de esquema (soporte transferencias)
python update_database.py

# Deberías ver:
# ✅ Tabla transacciones actualizada exitosamente
```

### 3.6 Probar Backend Manualmente

```bash
# Terminal 1: Socket Server
python socket_server.py

# Deberías ver:
# 🚀 Servidor Socket iniciado en 0.0.0.0:5000
# 📊 MQTT Publisher: Conectado al broker
```

**Presiona Ctrl+C para detener**

```bash
# Terminal 2: Flask Bridge (abrir nueva terminal SSH)
python socket_bridge.py

# Deberías ver:
# 🌐 Bridge Flask iniciado en 0.0.0.0:5001
# ✅ Socket conectado correctamente
```

**Presiona Ctrl+C para detener**

### 3.7 Configurar Supervisor (Auto-inicio)

```bash
# Crear configuración para Socket Server
sudo nano /etc/supervisor/conf.d/socket_server.conf
```

**Contenido:**
```ini
[program:socket_server]
command=/home/azureuser/ExamenDistribuidos/venv/bin/python socket_server.py
directory=/home/azureuser/ExamenDistribuidos
user=azureuser
autostart=true
autorestart=true
stderr_logfile=/var/log/socket_server.err.log
stdout_logfile=/var/log/socket_server.out.log
environment=PATH="/home/azureuser/ExamenDistribuidos/venv/bin"
```

```bash
# Crear configuración para Flask Bridge
sudo nano /etc/supervisor/conf.d/bridge.conf
```

**Contenido:**
```ini
[program:bridge]
command=/home/azureuser/ExamenDistribuidos/venv/bin/python socket_bridge.py
directory=/home/azureuser/ExamenDistribuidos
user=azureuser
autostart=true
autorestart=true
stderr_logfile=/var/log/bridge.err.log
stdout_logfile=/var/log/bridge.out.log
environment=PATH="/home/azureuser/ExamenDistribuidos/venv/bin"
```

```bash
# Recargar configuración de Supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar servicios
sudo supervisorctl start socket_server
sudo supervisorctl start bridge

# Verificar estado
sudo supervisorctl status

# Deberías ver:
# socket_server    RUNNING   pid 12345, uptime 0:00:05
# bridge           RUNNING   pid 12346, uptime 0:00:05
```

### 3.8 Configurar Nginx (Proxy Reverso)

```bash
# Crear configuración
sudo nano /etc/nginx/sites-available/backend
```

**Contenido:**
```nginx
server {
    listen 80;
    server_name _;  # Cambiar por tu dominio si tienes

    # Socket Bridge (API REST + WebSocket)
    location / {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts para WebSocket
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/

# Eliminar default (opcional)
sudo rm /etc/nginx/sites-enabled/default

# Probar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx

# Verificar estado
sudo systemctl status nginx
```

### 3.9 Verificar Backend en Producción

```bash
# Desde la VM
curl http://localhost:5001/api/stats

# Deberías ver JSON con estadísticas del servidor
```

**Desde tu PC (navegador):**
```
http://20.185.123.45/api/stats
```

Si ves JSON con estadísticas → ✅ **Backend funcionando**

---

## Paso 4: Deploy del Frontend

> **⏱️ Tiempo estimado:** 15-20 minutos

### 4.1 Preparar Código Frontend

**En tu PC local:**

```bash
# Ir al directorio Frontend
cd Frontend

# Crear archivo .env.production
nano .env.production
```

**Contenido:**
```env
NEXT_PUBLIC_API_URL=http://TU_IP_PUBLICA_AZURE
NEXT_PUBLIC_WS_URL=http://TU_IP_PUBLICA_AZURE

# Ejemplo:
# NEXT_PUBLIC_API_URL=http://20.185.123.45
# NEXT_PUBLIC_WS_URL=http://20.185.123.45
```

```bash
# Probar build localmente
pnpm build

# Deberías ver:
# ✓ Compiled successfully
# ✓ Linting and checking validity of types
# ✓ Collecting page data
```

### 4.2 Subir a GitHub

```bash
# Desde la raíz del proyecto
cd ..

# Agregar cambios
git add .

# Commit
git commit -m "chore: prepare for production deployment"

# Push
git push origin main
```

### 4.3 Deploy en Netlify

1. **Ir a Netlify**
   - URL: https://app.netlify.com
   - Login con GitHub

2. **Nuevo Sitio**
   ```
   Click "Add new site" → "Import an existing project"
   → "Deploy with GitHub"
   → Autorizar Netlify
   → Seleccionar repositorio "ExamenDistribuidos"
   ```

3. **Configuración Build**
   ```
   Branch to deploy: main
   
   Base directory: Frontend
   
   Build command: pnpm build
   
   Publish directory: Frontend/.next
   
   Environment variables:
   - NEXT_PUBLIC_API_URL = http://20.185.123.45
   - NEXT_PUBLIC_WS_URL = http://20.185.123.45
   ```

4. **Deploy**
   - Click "Deploy site"
   - Esperar 3-5 minutos
   - Netlify te dará una URL: `https://random-name-123456.netlify.app`

### 4.4 Actualizar CORS en Backend

**SSH a la VM Azure:**

```bash
ssh -i ~/.ssh/vm-backend-examen_key.pem azureuser@20.185.123.45

cd ~/ExamenDistribuidos

# Editar .env
nano .env
```

**Actualizar línea CORS_ORIGINS:**
```dotenv
CORS_ORIGINS=https://random-name-123456.netlify.app,http://20.185.123.45
```

**Guardar y reiniciar servicios:**
```bash
sudo supervisorctl restart bridge
sudo supervisorctl status
```

---

## Paso 5: Verificación Final

> **⏱️ Tiempo estimado:** 10-15 minutos

### 5.1 Checklist de Verificación

**Backend:**
- [ ] Azure MySQL funcionando y accesible
- [ ] VM Azure funcionando
- [ ] Socket Server corriendo (puerto 5000)
- [ ] Flask Bridge corriendo (puerto 5001)
- [ ] Nginx proxy funcionando (puerto 80)
- [ ] Supervisor auto-reinicia servicios
- [ ] Logs sin errores críticos

**Frontend:**
- [ ] Build exitoso en Netlify
- [ ] Sitio accesible en URL de Netlify
- [ ] Variables de entorno configuradas
- [ ] CORS permitiendo conexión desde Netlify

### 5.2 Pruebas Funcionales

**Abrir tu app Netlify en navegador:**

1. **Login**
   ```
   Cédula: 1234567890
   → Click "Iniciar Sesión"
   → Deberías ver Dashboard
   ```

2. **Crear Cuenta**
   ```
   Click "Crear nueva cuenta"
   Cédula: 0999888777
   Nombre: Test Usuario
   → Click "Crear Cuenta"
   → ✅ Alerta verde de éxito
   ```

3. **Depósito**
   ```
   Monto: 100
   → Click "Depositar"
   → ✅ Saldo actualizado a $100.00
   ```

4. **Transferencia**
   ```
   Cédula Destino: 1234567890
   Monto: 50.50
   → Click "Transferir"
   → ✅ Alerta verde de éxito
   → Saldo actualizado
   ```

5. **WebSocket Real-Time**
   ```
   Abrir 2 navegadores:
   - Browser 1: Login con cuenta A
   - Browser 2: Login con cuenta B
   
   Browser 1: Transferir a cuenta B
   Browser 2: Debería actualizar saldo automáticamente
   ```

6. **Historial**
   ```
   Verificar que aparezcan todas las transacciones:
   - DEPOSITO
   - TRANSFERENCIA_ENVIADA
   - TRANSFERENCIA_RECIBIDA
   ```

### 5.3 Verificar Logs

**SSH a VM:**
```bash
# Logs de Socket Server
sudo tail -f /var/log/socket_server.out.log

# Logs de Bridge
sudo tail -f /var/log/bridge.out.log

# Logs de errores
sudo tail -f /var/log/socket_server.err.log
sudo tail -f /var/log/bridge.err.log
```

### 5.4 Monitoreo

**Supervisor Status:**
```bash
sudo supervisorctl status

# Ambos deberían mostrar RUNNING
```

**Uso de Recursos:**
```bash
# CPU y RAM
htop

# Disco
df -h

# Conexiones activas
sudo netstat -tlnp | grep python
```

---

## Troubleshooting

### ❌ Problema: No puedo conectar a Azure MySQL

**Solución:**
```bash
# Verificar reglas de firewall en Azure Portal
# Agregar tu IP pública actual
# Verificar credenciales en .env
```

### ❌ Problema: Backend no inicia

**Diagnóstico:**
```bash
# Ver logs
sudo supervisorctl tail -f socket_server stderr
sudo supervisorctl tail -f bridge stderr

# Probar manualmente
cd ~/ExamenDistribuidos
source venv/bin/activate
python socket_server.py
```

### ❌ Problema: Frontend no se conecta al backend

**Verificar:**
1. Variables de entorno en Netlify
2. CORS configurado correctamente en backend
3. Puertos abiertos en NSG de Azure
4. IP pública correcta

### ❌ Problema: WebSocket no funciona

**Solución:**
```bash
# Verificar configuración Nginx
sudo nano /etc/nginx/sites-available/backend

# Asegurar que tenga:
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";

# Reiniciar Nginx
sudo systemctl restart nginx
```

### ❌ Problema: Decimal is not JSON serializable

**Ya está corregido en el código actual**, pero si aparece:
```bash
# Verificar que db_connection.py tenga las conversiones a float
grep -A 5 "def obtener_historial" db_connection.py
grep -A 5 "def consultar_cliente" db_connection.py
```

### ❌ Problema: Alertas no aparecen en frontend

**Verificar:**
1. Componente `AlertToast` está importado
2. Animaciones CSS están en `globals.css`
3. No hay errores en consola del navegador

---

## 📊 Arquitectura Final

```
┌─────────────────────────────────────────────────────────┐
│                    USUARIO FINAL                        │
│                  (Navegador Web)                        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   NETLIFY CDN                           │
│              (Frontend Next.js)                         │
│     https://random-name-123456.netlify.app              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ HTTP/WS
                       ▼
┌─────────────────────────────────────────────────────────┐
│              AZURE VM (Ubuntu 22.04)                    │
│              IP: 20.185.123.45                          │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │            Nginx (Puerto 80)                     │  │
│  │         (Proxy Reverso + Load Balancer)         │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       │                                 │
│         ┌─────────────┴──────────────┐                 │
│         │                            │                 │
│         ▼                            ▼                 │
│  ┌─────────────────┐        ┌─────────────────┐       │
│  │  Flask Bridge   │        │  Socket Server  │       │
│  │  (Puerto 5001)  │◄──────►│  (Puerto 5000)  │       │
│  │  REST + WS      │        │  TCP Sockets    │       │
│  └─────────────────┘        └─────────────────┘       │
│         │                            │                 │
│         └────────────┬───────────────┘                 │
│                      │                                 │
└──────────────────────┼─────────────────────────────────┘
                       │
                       │ MySQL Protocol
                       ▼
┌─────────────────────────────────────────────────────────┐
│       AZURE DATABASE FOR MYSQL (Flexible Server)       │
│     examen-distribuidos-db.mysql.database.azure.com    │
│                                                          │
│  ┌──────────────┐  ┌─────────────────────┐             │
│  │   clientes   │  │   transacciones     │             │
│  │  (usuarios)  │  │    (historial)      │             │
│  └──────────────┘  └─────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 🎉 Deployment Completo

**Si llegaste hasta aquí:**
- ✅ Base de datos Azure MySQL funcionando
- ✅ Backend en VM Azure con auto-restart
- ✅ Frontend en Netlify con CDN global
- ✅ WebSocket real-time funcionando
- ✅ Todas las funcionalidades operativas:
  - Login
  - Crear cuenta
  - Depósito/Retiro
  - Transferencias
  - Historial
  - Alertas visuales

**URLs de tu aplicación:**
- Frontend: `https://random-name-123456.netlify.app`
- Backend API: `http://20.185.123.45/api/`
- WebSocket: `ws://20.185.123.45/socket.io/`

---

## 📝 Notas Finales

### Seguridad
- Cambiar firewall de MySQL de 0.0.0.0/0 a solo IP de la VM
- Configurar HTTPS con Let's Encrypt (opcional)
- Rotar credenciales regularmente

### Costos Estimados (Azure)
- MySQL Flexible Server B1ms: ~$12-15/mes
- VM Standard_B1s: ~$7-10/mes
- Storage: ~$1-2/mes
- **Total:** ~$20-27/mes

### Mejoras Futuras
- [ ] Configurar dominio personalizado
- [ ] Habilitar HTTPS (SSL/TLS)
- [ ] Configurar backups automáticos
- [ ] Implementar MQTT broker en producción
- [ ] Agregar monitoreo con Azure Monitor
- [ ] Configurar alertas de downtime

---

**¡Felicitaciones! 🎊 Tu sistema está en producción.**
