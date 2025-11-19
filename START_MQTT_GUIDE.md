# 🚀 Scripts de Inicio con MQTT

## 📋 Scripts Disponibles

### Windows (PowerShell)
- `start-mqtt.ps1` - Inicio completo con soporte MQTT
- `start.ps1` - Inicio sin MQTT (básico)

### Linux/Mac (Bash)
- `start-mqtt.sh` - Inicio completo con soporte MQTT  
- `stop-mqtt.sh` - Detener todos los servicios
- `start-backend.sh` - Inicio sin MQTT (básico)
- `stop-backend.sh` - Detener servicios backend

---

## 🪟 Windows - PowerShell

### Inicio Completo (con MQTT)
```powershell
# Iniciar todo el sistema con MQTT
.\start-mqtt.ps1 -ConMQTT

# Iniciar sin MQTT (solo core)
.\start-mqtt.ps1
```

### Modos Especiales
```powershell
# Solo MQTT Broker (para desarrollo)
.\start-mqtt.ps1 -SoloMQTT

# Solo Monitor MQTT (para observar eventos)
.\start-mqtt.ps1 -Monitor
```

### Detener
```powershell
# Matar todos los procesos
taskkill /F /IM python.exe 2>$null
taskkill /F /IM node.exe 2>$null

# Detener contenedores Docker
docker-compose down
```

---

## 🐧 Linux/Mac - Bash

### Permisos (Primera vez)
```bash
# Dar permisos de ejecución
chmod +x start-mqtt.sh
chmod +x stop-mqtt.sh
chmod +x start-backend.sh
chmod +x stop-backend.sh
```

### Inicio Completo (con MQTT)
```bash
# Iniciar todo el sistema con MQTT
./start-mqtt.sh --con-mqtt

# Iniciar sin MQTT (solo core)
./start-mqtt.sh
```

### Modos Especiales
```bash
# Solo MQTT Broker (para desarrollo)
./start-mqtt.sh --solo-mqtt

# Solo Monitor MQTT (para observar eventos)
./start-mqtt.sh --monitor
```

### Detener
```bash
# Detener todos los servicios
./stop-mqtt.sh

# O manualmente
pkill -f "python.*socket_server.py"
pkill -f "python.*socket_bridge.py"
pkill -f "node.*next-server"
docker-compose down
```

---

## 📊 Servicios Iniciados

| Servicio | Puerto | Proceso | Log |
|----------|--------|---------|-----|
| Socket Server | 5000 | Python | logs/socket_server.log |
| Flask Bridge | 5001 | Python | logs/bridge.log |
| Frontend | 3000 | Node.js | logs/frontend.log |
| MySQL | 3306 | Docker | docker logs banco_mysql |
| MQTT Broker | 1883, 9001 | Docker | docker logs banco_mosquitto |
| Monitor MQTT | - | Python | logs/mqtt_monitor.log |

---

## 🔍 Verificar Estado

### Windows
```powershell
# Ver procesos Python
Get-Process python

# Ver procesos Node
Get-Process node

# Ver contenedores Docker
docker ps

# Ver puertos en uso
netstat -ano | findstr "5000 5001 3000 1883"
```

### Linux/Mac
```bash
# Ver procesos Python
ps aux | grep python

# Ver procesos Node
ps aux | grep node

# Ver contenedores Docker
docker ps

# Ver puertos en uso
lsof -i :5000,5001,3000,1883
```

---

## 📄 Ver Logs en Tiempo Real

### Windows
```powershell
# Socket Server
Get-Content logs\socket_server.log -Wait -Tail 50

# Flask Bridge
Get-Content logs\bridge.log -Wait -Tail 50

# Frontend
Get-Content logs\frontend.log -Wait -Tail 50

# MQTT Monitor
Get-Content logs\mqtt_monitor.log -Wait -Tail 50
```

### Linux/Mac
```bash
# Socket Server
tail -f logs/socket_server.log

# Flask Bridge
tail -f logs/bridge.log

# Frontend
tail -f logs/frontend.log

# MQTT Monitor
tail -f logs/mqtt_monitor.log

# Ver todos los logs a la vez
tail -f logs/*.log
```

---

## 🐛 Troubleshooting

### Error: "Missing closing '}' in statement block"
**Causa:** Archivo PowerShell corrupto o truncado

**Solución:**
```powershell
# Re-descargar el archivo o corregir manualmente
# El archivo debe terminar con todas las llaves cerradas
```

### Error: Docker Compose version obsolete
**Causa:** Warning de `version: '3.8'` en docker-compose.yml

**Solución:** Ya corregido - el campo `version` fue removido

### Error: Puerto en uso
**Windows:**
```powershell
# Encontrar proceso usando el puerto
netstat -ano | findstr "5000"

# Matar proceso por PID
taskkill /F /PID <PID>
```

**Linux/Mac:**
```bash
# Encontrar proceso usando el puerto
lsof -i :5000

# Matar proceso por PID
kill -9 <PID>
```

### Error: Permiso denegado (Linux/Mac)
```bash
# Dar permisos de ejecución
chmod +x start-mqtt.sh
chmod +x stop-mqtt.sh
```

### Error: MQTT Connection Refused
**Causa:** Mosquitto no está corriendo

**Windows:**
```powershell
# Iniciar solo MQTT
.\start-mqtt.ps1 -SoloMQTT
```

**Linux/Mac:**
```bash
# Iniciar solo MQTT
./start-mqtt.sh --solo-mqtt
```

---

## 🎯 Flujo de Trabajo Recomendado

### Desarrollo Local
```bash
# 1. Primera vez - Setup completo
./start-backend.sh          # Linux/Mac
.\start.ps1 -Todos          # Windows

# 2. Desarrollo diario - Inicio rápido
./start-backend.sh --run    # Linux/Mac
.\start-backend.ps1 -RunOnly # Windows

# 3. Probar MQTT
./start-mqtt.sh --con-mqtt  # Linux/Mac
.\start-mqtt.ps1 -ConMQTT   # Windows
```

### Producción (Linux Server)
```bash
# 1. Setup inicial (una vez)
./start-backend.sh

# 2. Iniciar en producción con MQTT
./start-mqtt.sh --con-mqtt

# 3. Monitorear logs
tail -f logs/*.log

# 4. Detener para mantenimiento
./stop-mqtt.sh
```

---

## 🚀 Inicio Rápido

### Desarrollo (Sin MQTT)
```bash
# Windows
.\start.ps1 -Todos

# Linux/Mac
./start-backend.sh --run
```

### Producción (Con MQTT)
```bash
# Windows
.\start-mqtt.ps1 -ConMQTT

# Linux/Mac
./start-mqtt.sh --con-mqtt
```

### Solo Testing MQTT
```bash
# Windows
.\start-mqtt.ps1 -Monitor

# Linux/Mac
./start-mqtt.sh --monitor
```

---

## 📚 Documentación Relacionada

- `ERRORES_CORREGIDOS.md` - Errores resueltos recientemente
- `MQTT_README.md` - Documentación MQTT completa
- `BACKEND_SCRIPTS.md` - Scripts de backend sin MQTT
- `DEPLOYMENT.md` - Guía de despliegue a producción

---

## ⚙️ Variables de Entorno

Crea un archivo `.env` en la raíz con:

```env
# Base de Datos
DB_HOST=localhost
DB_PORT=3306
DB_USER=banco_user
DB_PASSWORD=banco_password
DB_NAME=examen
DB_ROOT_PASSWORD=rootpassword

# MQTT (opcional)
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Socket Server
SOCKET_HOST=localhost
SOCKET_PORT=5000

# Flask Bridge
FLASK_HOST=localhost
FLASK_PORT=5001
```

---

## 🎉 Resultado Esperado

Después de ejecutar `start-mqtt.sh --con-mqtt` o `start-mqtt.ps1 -ConMQTT`:

```
================================
✅ Sistema iniciado correctamente
================================

📍 Servicios disponibles:
   - Socket Server:  localhost:5000 (PID: 12345)
   - Flask Bridge:   localhost:5001 (PID: 12346)
   - Frontend:       http://localhost:3000 (PID: 12347)
   - MQTT Broker:    localhost:1883
   - MQTT WebSocket: localhost:9001
   - Monitor MQTT:   (PID: 12348)

📚 Comandos útiles:
   ./start-mqtt.sh --con-mqtt      # Iniciar con MQTT
   ./start-mqtt.sh --solo-mqtt     # Solo broker MQTT
   ./start-mqtt.sh --monitor       # Solo monitor MQTT
   ./stop-mqtt.sh                  # Detener todos los servicios

🛑 Para detener: ./stop-mqtt.sh
```

Luego abre **http://localhost:3000** y prueba con cédula `1350509525`.

---

**✅ Sistema completamente funcional en Windows y Linux!** 🎉
