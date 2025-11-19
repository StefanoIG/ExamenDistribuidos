# Plan de Deployment: VM Frontend

## Arquitectura Final
```
[VM 1: MySQL DB]  ←→  [VM 2: Backend]  ←→  [VM 3: Frontend]
20.163.61.202:3306    135.234.27.161        [Nueva IP]:80
```

## Pasos para crear VM 3

### 1. Crear VM en Azure
- **Nombre:** vm-frontend
- **OS:** Ubuntu 22.04 LTS
- **Tamaño:** Standard_B1s (1 vCPU, 1GB RAM)
- **Puertos:** 22 (SSH), 80 (HTTP), 443 (HTTPS)
- **Grupo de recursos:** Mismo que las otras VMs

### 2. Instalar dependencias en VM Frontend
```bash
# Conectar vía Consola Serie de Azure

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Instalar pnpm
sudo npm install -g pnpm

# Instalar Nginx
sudo apt install -y nginx

# Instalar Git
sudo apt install -y git

# Verificar instalaciones
node --version  # Debe ser v20.x
pnpm --version
nginx -v
```

### 3. Clonar repositorio y hacer build
```bash
# Clonar repo
cd ~
git clone https://github.com/StefanoIG/ExamenDistribuidos.git
cd ExamenDistribuidos/Frontend

# Crear .env.production
cat > .env.production << 'EOF'
NEXT_PUBLIC_API_URL=http://135.234.27.161/api
NEXT_PUBLIC_WS_URL=http://135.234.27.161
EOF

# Instalar dependencias
pnpm install

# Hacer build de producción
pnpm build
```

### 4. Configurar Nginx para servir Next.js
```bash
# Crear configuración de Nginx
sudo nano /etc/nginx/sites-available/frontend
```

**Contenido del archivo:**
```nginx
server {
    listen 80;
    server_name _;  # Cambia por la IP pública de la VM 3

    root /home/azureuser/ExamenDistribuidos/Frontend/.next;
    
    # Logs
    access_log /var/log/nginx/frontend_access.log;
    error_log /var/log/nginx/frontend_error.log;

    # Servir archivos estáticos de Next.js
    location /_next/static {
        alias /home/azureuser/ExamenDistribuidos/Frontend/.next/static;
        expires 365d;
        access_log off;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/frontend /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Configurar Next.js como servicio systemd
```bash
# Crear servicio
sudo nano /etc/systemd/system/nextjs.service
```

**Contenido:**
```ini
[Unit]
Description=Next.js Frontend
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/ExamenDistribuidos/Frontend
Environment="NODE_ENV=production"
ExecStart=/usr/bin/pnpm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y arrancar servicio
sudo systemctl daemon-reload
sudo systemctl enable nextjs
sudo systemctl start nextjs
sudo systemctl status nextjs
```

### 6. Actualizar CORS en VM Backend
**En VM 2 (Backend), editar .env:**
```bash
# Conectar a VM Backend
# Editar .env
nano ~/ExamenDistribuidos/.env
```

Cambiar línea CORS_ORIGINS:
```dotenv
CORS_ORIGINS=http://[IP_VM_FRONTEND],http://localhost:3000
```

```bash
# Reiniciar servicios backend
sudo supervisorctl restart all
```

### 7. Verificar funcionamiento
```bash
# En VM Frontend
curl http://localhost:3000  # Debe devolver HTML de Next.js
curl http://localhost  # Debe pasar por Nginx y devolver lo mismo

# Desde tu navegador
http://[IP_PUBLICA_VM_FRONTEND]
```

## Ventajas de esta arquitectura

✅ **Separación de responsabilidades clara**
- VM 1: Solo base de datos
- VM 2: Solo lógica de negocio
- VM 3: Solo presentación

✅ **Sin problemas de Mixed Content**
- Todo es HTTP en el mismo nivel
- No hay conflictos HTTPS → HTTP

✅ **Demuestra arquitectura distribuida**
- 3 máquinas independientes comunicándose
- Escalabilidad horizontal visible

✅ **Fácil de mantener**
- Cada VM tiene un propósito único
- Deployments independientes

## Costos aproximados Azure
- VM Frontend B1s: ~$7-10 USD/mes
- Total 3 VMs: ~$30-35 USD/mes

## Alternativa más barata
Si quieres ahorrar, puedes:
1. Servir el frontend desde VM 2 (Backend)
2. Hacer build del Frontend y ponerlo en `/var/www/html`
3. Nginx sirve frontend estático y hace proxy a backend
