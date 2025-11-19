# 🎯 GUÍA PASO A PASO PARA PRODUCCIÓN

**Tu pregunta:** "primero seria prender la maquina de base y demas no?"

**Respuesta:** ¡Exactamente! Aquí está el orden correcto paso a paso.

---

## 📌 ORDEN CORRECTO (Muy Importante)

```
1. Base de Datos (Azure MySQL)
   ↓
2. Máquina Virtual (Azure VM)
   ↓
3. Backend (Socket Server + Flask Bridge)
   ↓
4. Frontend (Netlify)
   ↓
5. Pruebas y Verificación
```

---

## 🚀 PASO 1: PRENDER BASE DE DATOS (20 minutos)

### ¿Por qué primero?
- **El backend necesita conectarse a la DB para funcionar**
- Sin DB, el backend crashea al iniciar
- Es la base de todo el sistema

### Acciones:

#### 1.1 Crear Azure Database for MySQL

```
1. Ir a: https://portal.azure.com
2. Buscar: "Azure Database for MySQL"
3. Click: "Create" → "Flexible Server"

Configuración:
- Resource Group: Crear nuevo "rg-examen-db"
- Server name: examen-distribuidos-db
- Region: East US
- MySQL version: 8.0
- Compute: Burstable, B1ms (1 vCore, 2 GB RAM)
- Storage: 20 GB

Admin credentials:
- Username: adminuser
- Password: [tu password seguro - ANOTAR]

Networking:
- Public access
- Add current IP
- Allow Azure services

4. Click: "Review + Create"
5. Esperar: 5-10 minutos (Azure crea el servidor)
```

#### 1.2 Configurar Base de Datos

```bash
# Opción 1: Azure Cloud Shell (recomendado)
# Click en el icono ">_" en Azure Portal

mysql -h examen-distribuidos-db.mysql.database.azure.com \
      -u adminuser \
      -p
# Ingresar password

# Crear base de datos
CREATE DATABASE examen CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE examen;

# Crear tabla clientes
CREATE TABLE clientes (
    cedula VARCHAR(15) PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    saldo DECIMAL(10,2) DEFAULT 0.00,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# Crear tabla transacciones (CON SOPORTE DE TRANSFERENCIAS)
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

# Insertar usuario de prueba
INSERT INTO clientes (cedula, nombres, apellidos, saldo) 
VALUES ('1234567890', 'Usuario', 'Prueba', 1000.00);

# Verificar
SELECT * FROM clientes;
SHOW TABLES;

# Salir
exit;
```

#### 1.3 Anotar Credenciales

**MUY IMPORTANTE - Guardar esto:**
```
Host: examen-distribuidos-db.mysql.database.azure.com
Port: 3306
User: adminuser
Password: [tu password]
Database: examen
```

### ✅ Verificación Paso 1:
- [ ] MySQL server creado y running en Azure Portal
- [ ] Base de datos "examen" creada
- [ ] Tablas "clientes" y "transacciones" creadas
- [ ] ENUM de transacciones incluye TRANSFERENCIA_ENVIADA y TRANSFERENCIA_RECIBIDA
- [ ] Usuario de prueba insertado
- [ ] Credenciales anotadas

---

## 🖥️ PASO 2: PRENDER MÁQUINA VIRTUAL (30 minutos)

### ¿Por qué segundo?
- **Necesitas un servidor donde correr el backend**
- La VM tardará en aprovisionarse
- Mejor crearla mientras esperas

### Acciones:

#### 2.1 Crear Virtual Machine

```
1. Azure Portal → "Virtual Machines"
2. Click: "Create" → "Azure virtual machine"

Configuración básica:
- Resource Group: rg-examen-db (mismo que DB)
- VM name: vm-backend-examen
- Region: East US (MISMA región que DB)
- Image: Ubuntu Server 22.04 LTS - x64 Gen2
- Size: Standard_B1s (1 vCPU, 1 GiB RAM)

Authentication:
- Type: SSH public key
- Username: azureuser
- SSH key: Generate new key pair
- Key pair name: vm-backend-key

3. Click: Next hasta "Networking"

Networking:
- Virtual network: (nueva, default OK)
- Public IP: (nueva, default OK)
- NIC network security group: Advanced
- Configure NSG: Create new

Inbound rules (IMPORTANTE):
- SSH (22) - Source: My IP
- HTTP (80) - Source: Any
- Custom TCP (5000) - Source: Any - Socket Server
- Custom TCP (5001) - Source: Any - Flask Bridge

4. Click: "Review + Create"
5. Click: "Create"
6. **DESCARGAR CLAVE SSH** cuando aparezca (IMPORTANTE!)
7. Esperar: 5-10 minutos
```

#### 2.2 Obtener IP Pública

```
Azure Portal → Virtual Machines → vm-backend-examen
→ Overview → Public IP address

Ejemplo: 20.185.123.45

¡ANOTAR ESTA IP!
```

#### 2.3 Conectar por SSH

**Windows PowerShell:**
```powershell
# Mover clave a carpeta segura
Move-Item "$env:USERPROFILE\Downloads\vm-backend-key.pem" "$env:USERPROFILE\.ssh\"

# Conectar (reemplaza con TU IP)
ssh -i "$env:USERPROFILE\.ssh\vm-backend-key.pem" azureuser@20.185.123.45
```

**macOS/Linux:**
```bash
# Mover y dar permisos
mv ~/Downloads/vm-backend-key.pem ~/.ssh/
chmod 400 ~/.ssh/vm-backend-key.pem

# Conectar (reemplaza con TU IP)
ssh -i ~/.ssh/vm-backend-key.pem azureuser@20.185.123.45
```

**Deberías ver:**
```
azureuser@vm-backend-examen:~$
```

### ✅ Verificación Paso 2:
- [ ] VM creada y running en Azure Portal
- [ ] IP pública obtenida y anotada
- [ ] Clave SSH descargada
- [ ] Conexión SSH exitosa
- [ ] Puertos abiertos en NSG (22, 80, 5000, 5001)

---

## ⚙️ PASO 3: PRENDER BACKEND EN LA VM (40 minutos)

### ¿Por qué tercero?
- **Ya tienes DB funcionando**
- **Ya tienes VM accesible**
- Ahora puedes instalar y configurar el código

### Acciones (ejecutar en la VM vía SSH):

#### 3.1 Preparar Sistema

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3.12 python3-pip python3.12-venv git supervisor nginx

# Verificar instalación
python3.12 --version
git --version
```

#### 3.2 Clonar Repositorio

```bash
# Ir a home
cd ~

# Clonar tu repo (REEMPLAZAR CON TU USUARIO)
git clone https://github.com/TU_USUARIO/ExamenDistribuidos.git

# Entrar
cd ExamenDistribuidos

# Verificar archivos
ls -la

# Deberías ver:
# socket_server.py
# socket_bridge.py
# db_connection.py
# update_database.py
# requirements.txt
# .env.production
```

#### 3.3 Configurar Python

```bash
# Crear entorno virtual
python3.12 -m venv venv

# Activar
source venv/bin/activate

# Deberías ver (venv) en el prompt

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación (esto puede tardar 2-3 minutos)
pip list

# Deberías ver:
# mysql-connector-python
# flask
# flask-cors
# flask-socketio
# paho-mqtt
# python-dotenv
```

#### 3.4 Configurar Variables de Entorno

```bash
# Copiar template
cp .env.production .env

# Editar con nano
nano .env
```

**Editar con TUS credenciales reales:**
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

# CORS (actualizar después con Netlify)
CORS_ORIGINS=http://localhost:3000

# MQTT (dejar vacío si no usas)
MQTT_BROKER_HOST=
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Logging
LOG_LEVEL=INFO
DEBUG=False
```

**Guardar:** `Ctrl+X` → `Y` → `Enter`

#### 3.5 Verificar Conexión a DB

```bash
# Activar venv si no está activo
source venv/bin/activate

# Ejecutar setup (crea tablas si no existen)
python db_setup.py

# Deberías ver:
# ✅ Pool de conexiones creado
# ✅ Tabla clientes creada o ya existe
# ✅ Tabla transacciones creada o ya existe

# Ejecutar actualización (agrega soporte transferencias)
python update_database.py

# Deberías ver:
# ✅ Tabla transacciones actualizada exitosamente
# ✅ ENUM ahora incluye TRANSFERENCIA_ENVIADA y TRANSFERENCIA_RECIBIDA
```

**Si hay error de conexión:**
- Verificar credenciales en `.env`
- Verificar firewall de MySQL en Azure Portal
- Agregar IP de la VM a las reglas de firewall

#### 3.6 Probar Backend Manualmente

**Terminal 1 (SSH a la VM):**
```bash
cd ~/ExamenDistribuidos
source venv/bin/activate
python socket_server.py

# Deberías ver:
# 🚀 Servidor Socket iniciado en 0.0.0.0:5000
# 📊 Conexiones al pool de MySQL: OK
# Si MQTT está disponible:
#   📊 MQTT Publisher: Conectado al broker

# Si todo OK, presionar Ctrl+C para detener
```

**Terminal 2 (nueva conexión SSH):**
```bash
ssh -i ~/.ssh/vm-backend-key.pem azureuser@TU_IP

cd ~/ExamenDistribuidos
source venv/bin/activate
python socket_bridge.py

# Deberías ver:
# 🌐 Bridge Flask iniciado en 0.0.0.0:5001
# ✅ Socket conectado correctamente a localhost:5000
# * Running on all addresses (0.0.0.0)

# Si todo OK, presionar Ctrl+C para detener
```

#### 3.7 Configurar Auto-inicio con Supervisor

```bash
# Crear config para Socket Server
sudo nano /etc/supervisor/conf.d/socket_server.conf
```

**Pegar esto (ajustar rutas si es necesario):**
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

**Guardar:** `Ctrl+X` → `Y` → `Enter`

```bash
# Crear config para Flask Bridge
sudo nano /etc/supervisor/conf.d/bridge.conf
```

**Pegar esto:**
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

**Guardar:** `Ctrl+X` → `Y` → `Enter`

```bash
# Recargar Supervisor
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

**Si alguno dice FATAL:**
```bash
# Ver logs de error
sudo tail -100 /var/log/socket_server.err.log
sudo tail -100 /var/log/bridge.err.log

# Problemas comunes:
# 1. Path de venv incorrecto → verificar /etc/supervisor/conf.d/*.conf
# 2. .env no encontrado → verificar que existe en ~/ExamenDistribuidos/.env
# 3. Error de DB → verificar credenciales
```

#### 3.8 Configurar Nginx (Proxy Reverso)

```bash
# Crear configuración
sudo nano /etc/nginx/sites-available/backend
```

**Pegar esto:**
```nginx
server {
    listen 80;
    server_name _;

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

**Guardar:** `Ctrl+X` → `Y` → `Enter`

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/

# Eliminar default (opcional pero recomendado)
sudo rm /etc/nginx/sites-enabled/default

# Probar configuración
sudo nginx -t

# Debería decir:
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# Reiniciar Nginx
sudo systemctl restart nginx

# Verificar estado
sudo systemctl status nginx

# Debería decir: active (running)
```

#### 3.9 Verificar Backend Funcionando

**Desde la VM:**
```bash
curl http://localhost/api/stats

# Deberías ver JSON:
# {"success":true,"estadisticas":{"clientes_activos":0,...}}
```

**Desde tu PC (navegador):**
```
http://TU_IP_PUBLICA/api/stats

Ejemplo: http://20.185.123.45/api/stats
```

**Si ves JSON con estadísticas → ✅ BACKEND FUNCIONANDO**

### ✅ Verificación Paso 3:
- [ ] Sistema actualizado
- [ ] Python 3.12, git, supervisor, nginx instalados
- [ ] Repositorio clonado
- [ ] Virtual env creado y activado
- [ ] Requirements instalados
- [ ] .env configurado con credenciales reales
- [ ] db_setup.py ejecutado exitosamente
- [ ] update_database.py ejecutado exitosamente
- [ ] Socket Server probado manualmente (OK)
- [ ] Flask Bridge probado manualmente (OK)
- [ ] Supervisor configurado y servicios RUNNING
- [ ] Nginx configurado y activo
- [ ] API accesible desde navegador

---

## 🌐 PASO 4: PRENDER FRONTEND EN NETLIFY (20 minutos)

### ¿Por qué cuarto?
- **Backend ya está funcionando**
- **Tienes IP pública para configurar**
- Frontend se conectará al backend ya operativo

### Acciones:

#### 4.1 Preparar Código Local

**En tu PC (no en la VM):**

```bash
# Ir al directorio del proyecto
cd c:\Users\StefanoIG\PycharmProjects\ExamenDistribuidos

# Ir al frontend
cd Frontend

# Crear .env.production
# Windows PowerShell:
notepad .env.production

# O en VSCode:
code .env.production
```

**Contenido (REEMPLAZAR CON TU IP):**
```env
NEXT_PUBLIC_API_URL=http://20.185.123.45
NEXT_PUBLIC_WS_URL=http://20.185.123.45
```

**Guardar archivo**

```bash
# Probar build local
pnpm install  # Si no has instalado antes
pnpm build

# Deberías ver:
# ✓ Compiled successfully
# ✓ Linting and checking validity of types
# ✓ Collecting page data
# ✓ Generating static pages
# ✓ Finalizing page optimization
```

**Si hay errores:**
- Verificar que todas las dependencias estén instaladas
- Verificar que no haya errores de TypeScript

#### 4.2 Subir a GitHub

```bash
# Volver a la raíz del proyecto
cd ..

# Ver cambios
git status

# Agregar todos los cambios
git add .

# Commit
git commit -m "feat: production deployment with all features"

# Push a GitHub
git push origin main

# Esperar que termine (puede tardar 1-2 minutos)
```

#### 4.3 Deploy en Netlify

**Paso a paso en Netlify:**

```
1. Ir a: https://app.netlify.com
2. Login con GitHub

3. Click: "Add new site" → "Import an existing project"

4. Click: "Deploy with GitHub"

5. Autorizar Netlify si es primera vez

6. Seleccionar repositorio: "ExamenDistribuidos"

7. Configurar Build:
   - Branch to deploy: main
   - Base directory: Frontend
   - Build command: pnpm build
   - Publish directory: Frontend/.next
   
8. Environment variables (IMPORTANTE):
   Click "Add environment variables"
   
   Variable 1:
   - Key: NEXT_PUBLIC_API_URL
   - Value: http://TU_IP_PUBLICA
   
   Variable 2:
   - Key: NEXT_PUBLIC_WS_URL
   - Value: http://TU_IP_PUBLICA
   
   Ejemplo:
   NEXT_PUBLIC_API_URL = http://20.185.123.45
   NEXT_PUBLIC_WS_URL = http://20.185.123.45

9. Click: "Deploy [nombre del repo]"

10. Esperar: 3-5 minutos mientras hace build

11. Cuando termine, te dará una URL:
    https://random-name-123456.netlify.app
    
12. ¡ANOTAR ESTA URL!
```

**Si el deploy falla:**
- Ver logs en Netlify
- Verificar que Build command sea `pnpm build`
- Verificar que Publish directory sea `Frontend/.next`
- Verificar que Base directory sea `Frontend`

#### 4.4 Actualizar CORS en Backend

**SSH a la VM:**
```bash
ssh -i ~/.ssh/vm-backend-key.pem azureuser@TU_IP

cd ~/ExamenDistribuidos

# Editar .env
nano .env
```

**Actualizar línea CORS_ORIGINS (agregar URL de Netlify):**
```dotenv
CORS_ORIGINS=https://random-name-123456.netlify.app,http://localhost:3000
```

**Guardar:** `Ctrl+X` → `Y` → `Enter`

```bash
# Reiniciar Bridge para aplicar cambios
sudo supervisorctl restart bridge

# Verificar que esté corriendo
sudo supervisorctl status

# bridge    RUNNING   pid XXXXX, uptime 0:00:03
```

### ✅ Verificación Paso 4:
- [ ] .env.production creado en Frontend
- [ ] Variables con IP de Azure configuradas
- [ ] Build local exitoso
- [ ] Código pusheado a GitHub
- [ ] Sitio creado en Netlify
- [ ] Build en Netlify exitoso
- [ ] URL de Netlify obtenida
- [ ] CORS actualizado en backend con URL de Netlify
- [ ] Bridge reiniciado

---

## ✅ PASO 5: VERIFICACIÓN Y PRUEBAS (15 minutos)

### ¿Por qué quinto?
- **Todo está prendido**
- Ahora hay que verificar que funcione de punta a punta

### Acciones:

#### 5.1 Test de Login

```
1. Abrir navegador
2. Ir a: https://tu-app.netlify.app
3. Ingresar cédula: 1234567890
4. Click: "Iniciar Sesión"

✅ Deberías ver:
- Dashboard cargado
- Saldo: $1,000.00
- Botones de Depósito y Retiro
- Sección de Transferencias
- Historial vacío o con transacciones
```

#### 5.2 Test de Crear Cuenta

```
1. Click: "Crear nueva cuenta" (botón abajo del login)
2. Cédula: 0111222333 (debe empezar con 0)
3. Nombre: Juan Perez Test
4. Click: "Crear Cuenta"

✅ Deberías ver:
- ✅ ALERTA VERDE GRANDE aparece
- Título: "✅ Cuenta creada exitosamente"
- Mensaje de éxito
- Vuelve automáticamente a login
```

**Si aparece error:**
- Revisar consola del navegador (F12)
- Verificar que URL de API sea correcta en variables Netlify
- Verificar CORS en backend

#### 5.3 Test de Depósito

```
1. Login con: 0111222333
2. Monto: 100
3. Click: "Depositar"

✅ Deberías ver:
- Saldo actualizado a $100.00
- Historial muestra: DEPOSITO $100.00
- Sin errores en consola
```

#### 5.4 Test de Transferencia con Decimales

```
1. Login con: 0111222333 (que tiene $100)
2. Ir a sección "Transferir a Otra Cuenta"
3. Cédula Destino: 1234567890
4. Monto: 50.50
5. Click: "Transferir"

✅ Deberías ver:
- ✅ ALERTA VERDE GRANDE
- Título: "✅ Transferencia Exitosa"
- Descripción: "Se transfirieron $50.50 a la cuenta 1234567890"
- Saldo actualizado a $49.50
- Historial muestra: TRANSFERENCIA_ENVIADA $50.50
- NO aparece error "Decimal is not JSON serializable"
```

#### 5.5 Test de Transferencia con Error

```
1. Login con cualquier cuenta
2. Transferir a cédula: 0999999999 (no existe)
3. Monto: 10
4. Click: "Transferir"

✅ Deberías ver:
- ❌ ALERTA ROJA GRANDE
- Título: "❌ Error en Transferencia"
- Descripción: "Cuenta destino no existe"
- Saldo NO cambia
- Sin errores en consola del navegador
```

#### 5.6 Test de WebSocket Real-Time

```
1. Abrir 2 navegadores (o 2 ventanas incognito)
2. Navegador A: Login con 0111222333
3. Navegador B: Login con 1234567890
4. Navegador A: Transferir $10 a 1234567890
5. Observar Navegador B

✅ Deberías ver en Navegador B:
- Saldo se actualiza AUTOMÁTICAMENTE
- Historial se actualiza AUTOMÁTICAMENTE
- Aparece TRANSFERENCIA_RECIBIDA
- Sin refrescar la página
- Gráfico NO se reinicia (bug corregido)
```

#### 5.7 Verificar Logs Backend

**SSH a la VM:**
```bash
# Ver logs normales
sudo tail -50 /var/log/bridge.out.log

# Deberías ver:
# "TRANSFERENCIA: $50.50 de 0111222333 a 1234567890"
# Sin errores

# Ver logs de errores
sudo tail -50 /var/log/bridge.err.log

# NO debería haber:
# ❌ "Decimal is not JSON serializable"
# ❌ Errores de CORS
# ❌ Errores de conexión MySQL
```

### ✅ Verificación Final Completa:
- [ ] Login funciona
- [ ] Crear cuenta funciona y muestra alerta verde
- [ ] Depósito funciona
- [ ] Retiro funciona
- [ ] Transferencia con decimales funciona (no error Decimal)
- [ ] Transferencia fallida muestra alerta roja
- [ ] WebSocket actualiza en tiempo real
- [ ] Gráfico NO se reinicia con cada update
- [ ] Historial muestra todos los tipos:
  - [ ] DEPOSITO
  - [ ] RETIRO
  - [ ] TRANSFERENCIA_ENVIADA
  - [ ] TRANSFERENCIA_RECIBIDA
- [ ] Alertas visuales grandes aparecen
- [ ] Logs sin errores críticos

---

## 🎉 ¡SISTEMA EN PRODUCCIÓN!

**Si todos los checkboxes están marcados:**

Tu sistema está **100% operativo** con:

✅ **Base de Datos:** Azure MySQL running  
✅ **Backend:** VM Azure con auto-restart  
✅ **Frontend:** Netlify con CDN global  
✅ **Funcionalidades:**
- Login
- Crear cuenta (pública, desde login)
- Depósito/Retiro
- **Transferencias con decimales** (bug Decimal corregido)
- **Alertas visuales grandes** (rojas para errores, verdes para éxito)
- **Gráfico estable** (no se reinicia con cada WS update)
- Historial completo con todos los tipos
- WebSocket real-time

**URLs de tu sistema:**
- Frontend: `https://________________.netlify.app`
- Backend API: `http://________________/api/`
- WebSocket: `ws://________________/socket.io/`

---

## 📞 COMANDOS ÚTILES POST-DEPLOYMENT

**En la VM (SSH):**

```bash
# Ver estado de servicios
sudo supervisorctl status

# Reiniciar servicios
sudo supervisorctl restart all

# Ver logs en tiempo real
sudo tail -f /var/log/bridge.out.log
sudo tail -f /var/log/socket_server.out.log

# Ver errores
sudo tail -f /var/log/bridge.err.log
sudo tail -f /var/log/socket_server.err.log

# Test rápido de API
curl http://localhost/api/stats

# Ver uso de recursos
htop

# Actualizar código desde GitHub
cd ~/ExamenDistribuidos
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart all

# Script de comandos rápidos
cd ~/ExamenDistribuidos
chmod +x comandos-prod.sh
./comandos-prod.sh
```

---

## 📚 DOCUMENTACIÓN COMPLETA

- `GUIA_PRODUCCION_COMPLETA.md` - Guía detallada 30+ páginas
- `RESUMEN_DEPLOYMENT.md` - Resumen ejecutivo
- `DEPLOYMENT_CHECKLIST.md` - Checklist completo
- `CORRECCIONES_BUGS.md` - Bugs corregidos (Decimal, etc)
- `ALERTAS_VISUALES_IMPLEMENTADAS.md` - Sistema de alertas
- `comandos-prod.sh` - Script de comandos útiles
- `verify-deployment.sh` - Script de verificación

---

**¡Felicitaciones! Tu sistema bancario distribuido está en producción. 🚀**

**Costos mensuales estimados:** $20-30 USD  
**Tiempo total de deployment:** ~2 horas  
**Disponibilidad:** 99.9% (con Supervisor auto-restart)
