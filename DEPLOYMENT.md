# 🚀 Guía de Despliegue - Sistema Bancario Distribuido

## Arquitectura de Producción

```
┌─────────────────────┐
│   Netlify (CDN)     │  ← Frontend Next.js
│   https://...       │
└──────────┬──────────┘
           │
           ↓ HTTPS/WSS
┌─────────────────────┐
│   Azure VM          │  ← Backend Python
│   Socket Server     │  - Puerto 5000 (Socket TCP)
│   Bridge Flask      │  - Puerto 5001 (HTTP + WebSocket)
└──────────┬──────────┘
           │
           ↓ MySQL
┌─────────────────────┐
│ Azure Database      │  ← Base de Datos
│ for MySQL           │  - Puerto 3306
└─────────────────────┘
```

---

## 📋 Prerequisitos

### 1. Azure Database for MySQL
- Crear instancia de MySQL en Azure Portal
- Configurar firewall para permitir conexiones desde VM
- Anotar: `host`, `user`, `password`, `database`

### 2. Azure Virtual Machine
- **Sistema Operativo**: Ubuntu 20.04 LTS o superior
- **Tamaño**: Standard B2s (2 vCPUs, 4 GB RAM) mínimo
- **Puertos abiertos**: 5000, 5001, 22 (SSH)
- **IP Pública**: Estática recomendada

### 3. Netlify Account
- Cuenta gratuita o de pago
- Repositorio Git conectado

---

## 🗄️ Paso 1: Configurar Azure Database for MySQL

### Crear la base de datos:
```sql
CREATE DATABASE examen CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Configurar usuario:
```sql
CREATE USER 'banco_user'@'%' IDENTIFIED BY 'TU_PASSWORD_SEGURO';
GRANT ALL PRIVILEGES ON examen.* TO 'banco_user'@'%';
FLUSH PRIVILEGES;
```

### Configurar firewall:
1. Ve a Azure Portal → Tu servidor MySQL → "Connection security"
2. Agregar regla de firewall para la IP de tu VM
3. Habilitar "Allow access to Azure services" (opcional)

### Probar conexión desde local:
```bash
mysql -h your-server.mysql.database.azure.com -u banco_user@your-server -p
```

---

## 🖥️ Paso 2: Configurar Azure VM

### SSH a la VM:
```bash
ssh azureuser@YOUR_VM_IP
```

### Instalar dependencias:
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.12 y pip
sudo apt install -y python3.12 python3-pip python3.12-venv git

# Instalar supervisor para gestión de procesos
sudo apt install -y supervisor

# Instalar certbot para SSL (opcional pero recomendado)
sudo apt install -y certbot
```

### Clonar el repositorio:
```bash
cd /home/azureuser
git clone https://github.com/TU_USUARIO/ExamenDistribuidos.git
cd ExamenDistribuidos
```

### Configurar entorno virtual:
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configurar variables de entorno:
```bash
# Copiar archivo de ejemplo
cp .env.production .env

# Editar con tus credenciales
nano .env
```

Configurar `.env`:
```bash
DB_HOST=your-server.mysql.database.azure.com
DB_PORT=3306
DB_USER=banco_user@your-server
DB_PASSWORD=TU_PASSWORD_SEGURO
DB_NAME=examen

SERVER_PORT=5000
BRIDGE_PORT=5001

CORS_ORIGINS=https://your-app.netlify.app
SOCKET_HOST=0.0.0.0
```

### Inicializar la base de datos:
```bash
python db_setup.py
```

### Configurar Supervisor para auto-inicio:

**Crear `/etc/supervisor/conf.d/socket_server.conf`:**
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

**Crear `/etc/supervisor/conf.d/bridge.conf`:**
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

**Iniciar servicios:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start socket_server
sudo supervisorctl start bridge

# Verificar estado
sudo supervisorctl status
```

### Configurar Firewall de Azure:
1. Azure Portal → Tu VM → Networking → Inbound port rules
2. Agregar reglas:
   - Puerto 5000 (TCP) - Socket Server
   - Puerto 5001 (TCP) - Bridge Flask
   - Puerto 443 (HTTPS) - Si usas SSL

---

## 🌐 Paso 3: Desplegar Frontend en Netlify

### Opción A: Desde GitHub (Recomendado)

1. **Push tu código a GitHub:**
```bash
cd Frontend
git add .
git commit -m "Production ready"
git push origin main
```

2. **Conectar en Netlify:**
   - Ve a [Netlify](https://app.netlify.com)
   - "Add new site" → "Import an existing project"
   - Conectar tu repositorio GitHub
   - Seleccionar branch `main`
   - Build settings:
     - **Base directory**: `Frontend`
     - **Build command**: `npm run build`
     - **Publish directory**: `.next`

3. **Configurar Variables de Entorno en Netlify:**
   - Site settings → Environment variables
   - Agregar:
     ```
     NEXT_PUBLIC_API_URL = https://YOUR_VM_IP:5001
     NEXT_PUBLIC_WS_URL = wss://YOUR_VM_IP:5001
     ```

4. **Deploy:**
   - Netlify desplegará automáticamente

### Opción B: Deploy manual con Netlify CLI

```bash
cd Frontend

# Instalar Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Build
npm run build

# Deploy
netlify deploy --prod
```

---

## 🔒 Paso 4: Configurar HTTPS/SSL (Recomendado)

### Para la VM (usando Certbot):

**Si tienes dominio:**
```bash
sudo certbot certonly --standalone -d your-domain.com
```

**Configurar Nginx como reverse proxy:**
```bash
sudo apt install nginx

# Crear configuración
sudo nano /etc/nginx/sites-available/banco
```

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/banco /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 📊 Paso 5: Verificación

### Verificar servicios en VM:
```bash
# Ver logs
sudo tail -f /var/log/socket_server.out.log
sudo tail -f /var/log/bridge.out.log

# Verificar puertos
sudo netstat -tulpn | grep python

# Test manual
curl http://localhost:5001/health
```

### Verificar desde frontend:
1. Abrir https://your-app.netlify.app
2. Abrir consola del navegador (F12)
3. Buscar: `✅ WebSocket conectado`
4. Hacer login y transacción de prueba

---

## 🔄 Actualización y Mantenimiento

### Actualizar backend:
```bash
ssh azureuser@YOUR_VM_IP
cd /home/azureuser/ExamenDistribuidos
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart socket_server bridge
```

### Actualizar frontend:
- Push a GitHub → Netlify despliega automáticamente
- O manual: `netlify deploy --prod`

### Monitoreo:
```bash
# Ver estado de servicios
sudo supervisorctl status

# Ver logs en tiempo real
sudo tail -f /var/log/bridge.out.log

# Ver uso de recursos
htop
```

---

## 🐛 Troubleshooting

### Backend no responde:
```bash
sudo supervisorctl status
sudo supervisorctl restart socket_server bridge
```

### Error de conexión a BD:
```bash
# Probar conexión
mysql -h your-server.mysql.database.azure.com -u banco_user@your-server -p

# Verificar firewall de Azure
# Verificar credenciales en .env
```

### WebSocket no conecta:
- Verificar CORS_ORIGINS en `.env`
- Verificar puertos abiertos en Azure
- Verificar URL en variables de entorno de Netlify

### Frontend no carga:
- Revisar build logs en Netlify
- Verificar variables de entorno
- Limpiar caché: `npm run build` limpio

---

## 📝 Checklist de Despliegue

- [ ] Azure Database for MySQL creada y configurada
- [ ] VM creada con puertos 5000, 5001 abiertos
- [ ] Python 3.12 y dependencias instaladas en VM
- [ ] Repositorio clonado y `.env` configurado
- [ ] Base de datos inicializada (`db_setup.py`)
- [ ] Supervisor configurado y servicios corriendo
- [ ] Frontend desplegado en Netlify
- [ ] Variables de entorno configuradas en Netlify
- [ ] HTTPS configurado (opcional pero recomendado)
- [ ] Pruebas de login y transacciones exitosas
- [ ] WebSocket conectado correctamente

---

## 💡 Costos Estimados (Azure)

- **Azure Database for MySQL** (Basic, 1 vCore): ~$25-40/mes
- **Azure VM** (Standard B2s): ~$30-50/mes
- **Netlify** (Free tier): $0
- **Total estimado**: ~$55-90/mes

---

## 🔗 URLs de Producción

Una vez desplegado, tendrás:
- **Frontend**: `https://your-app.netlify.app`
- **API**: `https://your-vm-ip:5001/api`
- **WebSocket**: `wss://your-vm-ip:5001`
- **Health Check**: `https://your-vm-ip:5001/health`
