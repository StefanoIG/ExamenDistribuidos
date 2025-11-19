# ✅ Checklist de Despliegue

## Pre-Despliegue

### Azure Database for MySQL
- [ ] Crear servidor MySQL en Azure Portal
- [ ] Configurar firewall (permitir IP de VM)
- [ ] Crear base de datos `examen`
- [ ] Crear usuario `banco_user` con permisos
- [ ] Anotar: Host, User, Password
- [ ] Probar conexión desde local

### Azure Virtual Machine
- [ ] Crear VM Ubuntu 20.04+ (Standard B2s mínimo)
- [ ] Configurar IP pública estática (recomendado)
- [ ] Configurar Network Security Group:
  - [ ] Puerto 22 (SSH)
  - [ ] Puerto 5000 (Socket Server)
  - [ ] Puerto 5001 (Bridge Flask)
  - [ ] Puerto 443 (HTTPS) si usarás SSL
- [ ] Conectar vía SSH

### Repositorio Git
- [ ] Código pusheado a GitHub/GitLab
- [ ] Branch `main` actualizada
- [ ] Secrets/credenciales NO commiteadas

---

## Despliegue Backend (Azure VM)

### Instalación Inicial
```bash
# 1. Conectar a VM
ssh azureuser@YOUR_VM_IP

# 2. Ejecutar script de setup
chmod +x setup-azure-vm.sh
./setup-azure-vm.sh
```

### Configuración Manual
- [ ] Editar `.env` con credenciales reales
  ```bash
  nano .env
  ```
- [ ] Verificar DB_HOST apunta a Azure MySQL
- [ ] Verificar CORS_ORIGINS tiene URL de Netlify
- [ ] Inicializar BD: `python db_setup.py`

### Verificación
- [ ] Servicios corriendo: `sudo supervisorctl status`
- [ ] Ver logs: `sudo tail -f /var/log/bridge.out.log`
- [ ] Test health: `curl http://localhost:5001/health`
- [ ] Puertos abiertos: `sudo netstat -tulpn | grep python`

---

## Despliegue Frontend (Netlify)

### Preparación Local
```bash
cd Frontend

# 1. Crear .env.local con URLs de producción
cp .env.local.example .env.local
nano .env.local

# 2. Build de prueba
npm run build

# 3. Test local
npm start
```

### Deploy en Netlify

#### Opción A: GitHub (Automático - Recomendado)
- [ ] Push código a GitHub
- [ ] Conectar repo en Netlify
- [ ] Configurar:
  - Base directory: `Frontend`
  - Build command: `npm run build`
  - Publish directory: `.next`
- [ ] Agregar variables de entorno:
  - `NEXT_PUBLIC_API_URL` = `https://YOUR_VM_IP:5001`
  - `NEXT_PUBLIC_WS_URL` = `wss://YOUR_VM_IP:5001`
- [ ] Deploy

#### Opción B: CLI Manual
```bash
npm install -g netlify-cli
netlify login
netlify deploy --prod
```

### Verificación
- [ ] Sitio accesible: `https://your-app.netlify.app`
- [ ] Consola sin errores (F12)
- [ ] WebSocket conectado: ver `✅ WebSocket conectado`
- [ ] Login funciona
- [ ] Transacciones funcionan
- [ ] Multi-tab sync funciona

---

## Post-Despliegue

### Pruebas de Integración
- [ ] Login desde frontend Netlify
- [ ] Consultar saldo
- [ ] Hacer depósito
- [ ] Hacer retiro
- [ ] Ver historial
- [ ] Panel admin (si aplica)
- [ ] Abrir 2 pestañas y verificar sync
- [ ] Verificar modal de historial se actualiza

### Monitoreo
- [ ] Logs backend: `sudo tail -f /var/log/bridge.out.log`
- [ ] Logs frontend: Netlify dashboard → Functions → Logs
- [ ] Conexiones BD: Verificar en Azure Portal
- [ ] Uso de recursos VM: `htop`

### Seguridad (Opcional pero Recomendado)
- [ ] Configurar HTTPS con Let's Encrypt
- [ ] Configurar Nginx como reverse proxy
- [ ] Cambiar contraseñas default
- [ ] Configurar firewall más restrictivo
- [ ] Habilitar backups automáticos de BD

---

## Comandos Útiles

### Backend (VM)
```bash
# Ver estado
sudo supervisorctl status

# Reiniciar servicios
sudo supervisorctl restart socket_server bridge

# Ver logs en tiempo real
sudo tail -f /var/log/bridge.out.log
sudo tail -f /var/log/socket_server.out.log

# Actualizar código
cd ~/ExamenDistribuidos
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart socket_server bridge
```

### Frontend (Netlify)
```bash
# Redesplegar
git push origin main  # Si está conectado a GitHub

# O manual
netlify deploy --prod
```

### Base de Datos
```bash
# Conectar a BD
mysql -h your-server.mysql.database.azure.com -u banco_user@your-server -p

# Ver transacciones recientes
SELECT * FROM transacciones ORDER BY fecha DESC LIMIT 10;

# Ver clientes
SELECT * FROM clientes;
```

---

## Troubleshooting

### ❌ Backend no responde
```bash
sudo supervisorctl status
sudo supervisorctl restart socket_server bridge
sudo tail -f /var/log/bridge.err.log
```

### ❌ Error de BD
- Verificar firewall de Azure MySQL
- Verificar credenciales en `.env`
- Test: `mysql -h HOST -u USER -p`

### ❌ WebSocket no conecta
- Verificar CORS_ORIGINS en backend `.env`
- Verificar puerto 5001 abierto en Azure
- Verificar URL correcta en Netlify env vars
- Ver consola del navegador (F12)

### ❌ Frontend no carga
- Revisar build logs en Netlify
- Verificar variables de entorno
- Limpiar caché: `netlify deploy --prod --clear-cache`

---

## Costos Estimados Mensuales

| Servicio | Plan | Costo |
|----------|------|-------|
| Azure Database for MySQL | Basic (1 vCore) | $25-40 |
| Azure VM | Standard B2s | $30-50 |
| Netlify | Free Tier | $0 |
| **Total** | | **~$55-90** |

---

## URLs de Producción

Anotar aquí tus URLs después del despliegue:

- **Frontend**: `https://_____.netlify.app`
- **Backend API**: `https://_____:5001`
- **Health Check**: `https://_____:5001/health`
- **Azure MySQL**: `_____.mysql.database.azure.com`

---

## Contacto y Soporte

Para problemas o preguntas:
- Ver logs detallados
- Revisar [DEPLOYMENT.md](DEPLOYMENT.md)
- Verificar variables de entorno
- Comprobar puertos y firewall
