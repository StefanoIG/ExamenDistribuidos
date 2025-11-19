# 🚀 Despliegue a Producción (Linux)

## 📋 Pre-requisitos

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3 python3-pip python3-venv git nodejs npm docker.io docker-compose

# Agregar usuario al grupo docker (para no usar sudo)
sudo usermod -aG docker $USER
newgrp docker
```

---

## 📦 Clonar Repositorio

```bash
# Clonar proyecto
git clone https://github.com/StefanoIG/ExamenDistribuidos.git
cd ExamenDistribuidos

# Dar permisos a scripts
chmod +x *.sh
```

---

## ⚙️ Configuración

### 1. Variables de Entorno

```bash
# Crear archivo .env
cat > .env << 'EOF'
# Base de Datos
DB_HOST=mysql
DB_PORT=3306
DB_USER=banco_user
DB_PASSWORD=CAMBIAR_PASSWORD_SEGURO
DB_NAME=examen
DB_ROOT_PASSWORD=CAMBIAR_ROOT_PASSWORD

# MQTT
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
MQTT_USERNAME=banco_mqtt
MQTT_PASSWORD=CAMBIAR_MQTT_PASSWORD

# Socket Server
SOCKET_HOST=0.0.0.0
SOCKET_PORT=5000

# Flask Bridge
FLASK_HOST=0.0.0.0
FLASK_PORT=5001

# Frontend
NEXT_PUBLIC_API_URL=http://TU_IP_PUBLICA:5001/api
NEXT_PUBLIC_WS_URL=ws://TU_IP_PUBLICA:5001
EOF

# Cambiar permisos (solo propietario puede leer)
chmod 600 .env
```

### 2. Configurar Seguridad MQTT

```bash
# Editar mosquitto.conf para producción
nano mosquitto/config/mosquitto.conf
```

Cambiar a:
```conf
listener 1883 0.0.0.0
listener 9001 0.0.0.0
protocol websockets

# SEGURIDAD PARA PRODUCCIÓN
allow_anonymous false
password_file /mosquitto/config/passwd

# Logs
log_dest file /mosquitto/log/mosquitto.log
log_type all

# Persistencia
persistence true
persistence_location /mosquitto/data/
```

Crear archivo de passwords:
```bash
# Crear directorio si no existe
mkdir -p mosquitto/config

# Crear usuario MQTT
docker run -it --rm -v $(pwd)/mosquitto/config:/mosquitto/config eclipse-mosquitto:2.0 mosquitto_passwd -c /mosquitto/config/passwd banco_mqtt
# Te pedirá ingresar password (usa el mismo de .env)
```

---

## 🔧 Setup Inicial

```bash
# Ejecutar setup completo (primera vez)
./start-backend.sh

# Esto hará:
# - Crear entorno virtual Python
# - Instalar dependencias
# - Inicializar base de datos
# - Instalar dependencias Frontend
```

---

## 🚀 Iniciar en Producción

### Opción 1: Con systemd (Recomendado)

Crear servicio systemd para inicio automático:

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/banco-sistema.service
```

Contenido:
```ini
[Unit]
Description=Sistema Bancario Distribuido
After=network.target docker.service
Requires=docker.service

[Service]
Type=forking
User=TU_USUARIO
WorkingDirectory=/ruta/completa/a/ExamenDistribuidos
ExecStart=/ruta/completa/a/ExamenDistribuidos/start-mqtt.sh --con-mqtt
ExecStop=/ruta/completa/a/ExamenDistribuidos/stop-mqtt.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activar servicio:
```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar inicio automático
sudo systemctl enable banco-sistema

# Iniciar servicio
sudo systemctl start banco-sistema

# Ver estado
sudo systemctl status banco-sistema
```

### Opción 2: Manual

```bash
# Iniciar con MQTT
./start-mqtt.sh --con-mqtt

# Ver logs en tiempo real
tail -f logs/*.log
```

---

## 🔥 Configurar Firewall

```bash
# Permitir puertos necesarios
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP (Nginx)
sudo ufw allow 443/tcp     # HTTPS (Nginx)
sudo ufw allow 5000/tcp    # Socket Server
sudo ufw allow 5001/tcp    # Flask Bridge
sudo ufw allow 3000/tcp    # Frontend
sudo ufw allow 1883/tcp    # MQTT
sudo ufw allow 9001/tcp    # MQTT WebSocket

# Activar firewall
sudo ufw enable
```

---

## 🌐 Configurar Nginx (Reverse Proxy)

### Instalar Nginx

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Configurar Virtual Host

```bash
sudo nano /etc/nginx/sites-available/banco-sistema
```

Contenido:
```nginx
upstream socket_server {
    server localhost:5000;
}

upstream flask_api {
    server localhost:5001;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API Flask
    location /api/ {
        proxy_pass http://flask_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /socket.io/ {
        proxy_pass http://flask_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # MQTT WebSocket
    location /mqtt {
        proxy_pass http://localhost:9001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Activar sitio:
```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/banco-sistema /etc/nginx/sites-enabled/

# Probar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

### Configurar SSL (HTTPS)

```bash
# Obtener certificado Let's Encrypt
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Renovación automática (ya viene configurado)
sudo certbot renew --dry-run
```

---

## 📊 Monitoreo

### Ver Logs

```bash
# Todos los logs
tail -f logs/*.log

# Solo errores
grep -i error logs/*.log

# Logs de Docker
docker logs banco_mysql
docker logs banco_mosquitto
```

### Ver Procesos

```bash
# Procesos Python
ps aux | grep python

# Procesos Node
ps aux | grep node

# Contenedores Docker
docker ps

# Uso de recursos
htop
```

### Verificar Puertos

```bash
# Puertos en uso
sudo lsof -i :5000,5001,3000,1883,9001

# Conexiones activas
sudo netstat -tulpn | grep LISTEN
```

---

## 🔄 Actualización

```bash
# Detener servicios
./stop-mqtt.sh

# Actualizar código
git pull origin main

# Actualizar dependencias Python
source venv/bin/activate
pip install -r requirements.txt

# Actualizar dependencias Frontend
cd Frontend
npm install
cd ..

# Reiniciar
./start-mqtt.sh --con-mqtt
```

---

## 🛡️ Seguridad

### 1. Actualizar Passwords

```bash
# Editar .env con passwords fuertes
nano .env

# Actualizar password MQTT
docker exec -it banco_mosquitto mosquitto_passwd -b /mosquitto/config/passwd banco_mqtt NUEVO_PASSWORD
```

### 2. Limitar Acceso SSH

```bash
# Editar configuración SSH
sudo nano /etc/ssh/sshd_config

# Cambiar:
PermitRootLogin no
PasswordAuthentication no  # Solo usar SSH keys

# Reiniciar SSH
sudo systemctl restart sshd
```

### 3. Fail2Ban (Protección contra brute force)

```bash
# Instalar
sudo apt install -y fail2ban

# Configurar
sudo nano /etc/fail2ban/jail.local
```

Contenido:
```ini
[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

```bash
# Iniciar
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

---

## 📈 Performance

### Optimizar Base de Datos

```bash
# Editar configuración MySQL
docker exec -it banco_mysql mysql -uroot -p

# Ejecutar:
# ALTER DATABASE examen CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
# OPTIMIZE TABLE usuarios, transacciones;
```

### Optimizar Frontend

```bash
cd Frontend

# Build para producción
npm run build

# Usar PM2 para mejor performance
npm install -g pm2
pm2 start npm --name "frontend" -- start
pm2 save
pm2 startup
```

---

## 🔧 Troubleshooting Producción

### Error: Conexión rechazada

```bash
# Verificar que servicios estén corriendo
./start-mqtt.sh --con-mqtt

# Verificar firewall
sudo ufw status

# Verificar puertos
sudo lsof -i :5000,5001,3000
```

### Error: Out of Memory

```bash
# Ver uso de memoria
free -h

# Agregar swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Hacer permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Error: Disco lleno

```bash
# Ver uso de disco
df -h

# Limpiar logs viejos
find logs/ -name "*.log" -mtime +30 -delete

# Limpiar Docker
docker system prune -af
```

---

## 📋 Checklist Pre-Producción

- [ ] Passwords fuertes en `.env`
- [ ] MQTT con autenticación habilitada
- [ ] Firewall configurado (UFW)
- [ ] Nginx con SSL/HTTPS (Let's Encrypt)
- [ ] Servicio systemd configurado
- [ ] Logs rotación configurada
- [ ] Backups automáticos de base de datos
- [ ] Monitoreo configurado (opcional: Grafana + Prometheus)
- [ ] DNS configurado apuntando al servidor
- [ ] Fail2Ban instalado y configurado
- [ ] SSH con keys, sin passwords

---

## 🎯 Comandos Rápidos

```bash
# Estado del sistema
sudo systemctl status banco-sistema

# Reiniciar sistema
sudo systemctl restart banco-sistema

# Ver logs del servicio
sudo journalctl -u banco-sistema -f

# Ver logs de aplicación
tail -f logs/*.log

# Detener sistema
./stop-mqtt.sh

# Iniciar sistema manualmente
./start-mqtt.sh --con-mqtt

# Backup de base de datos
docker exec banco_mysql mysqldump -uroot -p examen > backup_$(date +%Y%m%d).sql
```

---

**✅ Sistema listo para producción!** 🚀

Para soporte: [GitHub Issues](https://github.com/StefanoIG/ExamenDistribuidos/issues)
