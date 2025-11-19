# 🚀 Scripts de Backend - Sistema Bancario

## 📋 Descripción

Scripts automatizados para gestionar el backend del sistema bancario en Linux/Mac.

---

## 🔧 Scripts Disponibles

### 1. `start-backend.sh` - Inicio completo con setup

**Uso:**
```bash
./start-backend.sh
```

**Qué hace:**
1. ✅ Verifica Python 3
2. ✅ Crea entorno virtual (`venv/`) si no existe
3. ✅ Activa el entorno virtual
4. ✅ Actualiza pip
5. ✅ Instala todas las dependencias de `requirements.txt`
6. ✅ Verifica/crea archivo `.env`
7. ✅ Inicializa la base de datos (`db_setup.py`)
8. ✅ Inicia MySQL (Docker si está disponible)
9. ✅ Inicia MQTT Broker (Docker si está disponible)
10. ✅ Inicia Socket Server (puerto 5000)
11. ✅ Inicia Flask Bridge (puerto 5001)

**Salida esperada:**
```
================================
🏦 Sistema Bancario - Backend
================================

📦 Fase 1: Configuración e instalación
...
✅ Setup completado exitosamente

🚀 Fase 2: Iniciando servicios del backend
...
================================
✅ Backend iniciado correctamente
================================

📍 Servicios corriendo:
   • MySQL:         localhost:3306
   • MQTT Broker:   localhost:1883
   • Socket Server: localhost:5000 (PID: 12345)
   • Flask Bridge:  localhost:5001 (PID: 12346)
```

---

### 2. `start-backend.sh --run` - Inicio rápido (sin setup)

**Uso:**
```bash
./start-backend.sh --run
# o
./start-backend.sh -r
```

**Qué hace:**
1. ✅ Activa entorno virtual (debe existir)
2. ✅ Inicia MySQL
3. ✅ Inicia MQTT Broker
4. ✅ Inicia Socket Server
5. ✅ Inicia Flask Bridge

**Cuándo usar:**
- Después de la primera ejecución
- Cuando ya tienes todo instalado
- Para reiniciar servicios rápidamente

---

### 3. `stop-backend.sh` - Detener backend

**Uso:**
```bash
./stop-backend.sh
```

**Qué hace:**
1. ✅ Detiene Socket Server (PID o puerto 5000)
2. ✅ Detiene Flask Bridge (PID o puerto 5001)
3. ✅ Limpia archivos PID

---

## 📦 Requisitos Previos

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### macOS
```bash
# Python viene preinstalado, o instala con Homebrew:
brew install python3
```

### Docker (Opcional pero recomendado)
```bash
# Ubuntu/Debian
sudo apt install docker.io docker-compose

# macOS
brew install docker docker-compose
```

---

## 🎯 Flujo de Trabajo Recomendado

### Primera vez:
```bash
# 1. Clonar repositorio
git clone https://github.com/StefanoIG/ExamenDistribuidos.git
cd ExamenDistribuidos

# 2. Copiar y configurar .env
cp .env.example .env
nano .env  # Editar credenciales de MySQL

# 3. Dar permisos de ejecución
chmod +x start-backend.sh stop-backend.sh

# 4. Iniciar (setup completo)
./start-backend.sh
```

### Usos posteriores:
```bash
# Inicio rápido
./start-backend.sh --run

# Detener
./stop-backend.sh
```

---

## 📊 Monitoreo

### Ver logs en tiempo real:
```bash
# Socket Server
tail -f logs/socket_server.log

# Flask Bridge
tail -f logs/bridge.log
```

### Monitor MQTT:
```bash
source venv/bin/activate
python3 mqtt_subscriber.py
```

### Verificar procesos:
```bash
ps aux | grep python
lsof -i :5000  # Socket Server
lsof -i :5001  # Flask Bridge
```

---

## 🐛 Troubleshooting

### Error: "Python 3 no está instalado"
```bash
# Ubuntu/Debian
sudo apt install python3 python3-venv python3-pip

# macOS
brew install python3
```

### Error: "Docker no disponible"
**Opción 1:** Instalar Docker (recomendado)
```bash
# Ubuntu/Debian
sudo apt install docker.io docker-compose
sudo systemctl start docker
```

**Opción 2:** Usar MySQL/MQTT externos
- Edita `.env` con el host de tu MySQL
- MQTT es opcional

### Error: "Puerto 5000/5001 en uso"
```bash
# Detener procesos previos
./stop-backend.sh

# O manualmente
lsof -ti:5000 | xargs kill -9
lsof -ti:5001 | xargs kill -9
```

### Error: "No se puede conectar a MySQL"
```bash
# Verificar MySQL corriendo
docker ps | grep mysql

# Ver logs de MySQL
docker logs banco_mysql

# Iniciar MySQL manualmente
docker-compose up -d mysql
```

### Error: "ModuleNotFoundError: paho"
```bash
# Reinstalar dependencias
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🔐 Variables de Entorno (.env)

```env
# Base de datos
DB_HOST=localhost
DB_PORT=3306
DB_USER=banco_user
DB_PASSWORD=banco_password
DB_NAME=examen

# Backend
SERVER_PORT=5000
BRIDGE_PORT=5001

# MQTT (opcional)
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
```

---

## 📚 Estructura de Logs

```
logs/
├── socket_server.log   # Socket TCP Server
└── bridge.log          # Flask Bridge + WebSocket
```

---

## 🎨 Ejemplo Completo

```bash
# Terminal 1: Iniciar backend
./start-backend.sh --run

# Terminal 2: Ver logs
tail -f logs/socket_server.log

# Terminal 3: Monitor MQTT (opcional)
source venv/bin/activate
python3 mqtt_subscriber.py

# Cuando termines
./stop-backend.sh
```

---

## ⚡ Comandos Rápidos

```bash
# Inicio completo (primera vez)
./start-backend.sh

# Inicio rápido (después)
./start-backend.sh --run

# Detener todo
./stop-backend.sh

# Ver logs
tail -f logs/socket_server.log
tail -f logs/bridge.log

# Limpiar todo y reiniciar
./stop-backend.sh
rm -rf venv logs/*.log
./start-backend.sh
```

---

## 🏗️ Arquitectura Backend

```
┌─────────────────────────────────────┐
│   Socket Server (Port 5000)         │
│   - TCP Protocol                    │
│   - MySQL Connection                │
│   - MQTT Publisher                  │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Flask Bridge (Port 5001)          │
│   - WebSocket (Socket.IO)           │
│   - REST API                        │
│   - CORS Enabled                    │
└─────────────────────────────────────┘
```

---

**¡Backend listo para desarrollo y producción! 🎉**
