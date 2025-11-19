# 📊 Resumen de Integración MQTT

## ✅ Lo que se agregó al sistema

### 1. **Archivos Nuevos Creados**

| Archivo | Descripción |
|---------|-------------|
| `mqtt_publisher.py` | Clase para publicar eventos a MQTT |
| `mqtt_subscriber.py` | Monitor en tiempo real de eventos MQTT |
| `mosquitto/config/mosquitto.conf` | Configuración del broker Mosquitto |
| `MQTT_GUIDE.md` | Guía completa de uso de MQTT |
| `QUICKSTART_MQTT.md` | Inicio rápido con MQTT |
| `start-mqtt.ps1` | Script PowerShell para iniciar sistema con MQTT |

### 2. **Archivos Modificados**

| Archivo | Cambios |
|---------|---------|
| `requirements.txt` | ➕ `paho-mqtt==1.6.1` |
| `socket_server.py` | ➕ MQTTPublisher, publicación en transacciones |
| `.env.example` | ➕ Variables MQTT (BROKER_HOST, PORT) |
| `.env.production` | ➕ Variables MQTT para Azure |
| `docker-compose.yml` | ➕ Servicio Mosquitto, env vars MQTT |

---

## 🏗️ Arquitectura Actualizada

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│                  Next.js (Port 3000)                        │
│          WebSocket: ws://localhost:5001                     │
│          MQTT (opcional): ws://localhost:9001               │
└────────────┬────────────────────────────────────────────────┘
             │ WebSocket
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    FLASK BRIDGE                             │
│               Flask + SocketIO (Port 5001)                  │
└────────────┬────────────────────────────────────────────────┘
             │ TCP Socket
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   SOCKET SERVER                             │
│              Python TCP Server (Port 5000)                  │
│                 + MQTT Publisher                            │
└────────┬───────────────────────────────────┬────────────────┘
         │                                   │
         │ SQL                               │ MQTT Publish
         ▼                                   ▼
┌──────────────────┐             ┌────────────────────────────┐
│   MySQL DB       │             │   MQTT Broker (Mosquitto)  │
│   Port 3306      │             │   Port 1883 (MQTT)         │
│                  │             │   Port 9001 (WebSocket)    │
└──────────────────┘             └────────┬───────────────────┘
                                          │ MQTT Subscribe
                                          ▼
                            ┌─────────────────────────────┐
                            │   MQTT Subscribers:         │
                            │   - Monitor (CLI)           │
                            │   - Analytics Service       │
                            │   - Frontend (opcional)     │
                            │   - Audit Logging           │
                            └─────────────────────────────┘
```

---

## 📡 Tópicos MQTT Publicados

### Desde `socket_server.py`:

| Evento | Tópico | QoS | Retain | Cuándo |
|--------|--------|-----|--------|--------|
| **Depósito** | `banco/transacciones`<br>`banco/depositos`<br>`banco/saldo/{cedula}` | 1<br>1<br>1 | No<br>No<br>**Sí** | Después de cada depósito exitoso |
| **Retiro** | `banco/transacciones`<br>`banco/retiros`<br>`banco/saldo/{cedula}` | 1<br>1<br>1 | No<br>No<br>**Sí** | Después de cada retiro exitoso |
| **Alerta Saldo Bajo** | `banco/alertas` | 2 | No | Cuando saldo < $100 después de retiro |
| **Estadísticas** | `banco/estadisticas` | 0 | **Sí** | Cada vez que se consultan stats |

---

## 🔄 Flujo de Datos

### Ejemplo: Usuario hace un depósito de $150

1. **Frontend** → WebSocket → **Flask Bridge**
2. **Flask Bridge** → TCP Socket → **Socket Server**
3. **Socket Server**:
   - ✅ Actualiza BD MySQL
   - ✅ Publica a MQTT:
     - `banco/transacciones` → `{"cedula":"123","tipo":"DEPOSITO","monto":150,"saldo_nuevo":1150}`
     - `banco/depositos` → (mismo mensaje)
     - `banco/saldo/123` → `{"cedula":"123","saldo_nuevo":1150,"saldo_anterior":1000}` **(RETAINED)**
4. **MQTT Broker** → Distribuye a todos los suscriptores:
   - 👂 Monitor CLI muestra: `💰 DEPÓSITO: $150.00 - Cédula: 123 - Nuevo saldo: $1150.00`
   - 📊 Servicio de analytics registra transacción
   - 📧 Servicio de notificaciones envía email (futuro)

---

## 🚀 Comandos de Inicio

### Opción 1: Sistema completo SIN MQTT
```powershell
.\start.ps1 -Todos
```

### Opción 2: Sistema completo CON MQTT
```powershell
.\start-mqtt.ps1 -ConMQTT
```

### Opción 3: Solo MQTT Broker
```powershell
.\start-mqtt.ps1 -SoloMQTT
```

### Opción 4: Solo Monitor MQTT
```powershell
.\start-mqtt.ps1 -Monitor
```

---

## 🧪 Verificación

### 1. Verificar Broker MQTT está corriendo
```powershell
docker ps | Select-String mosquitto
```

Salida esperada:
```
banco_mosquitto   Up 2 minutes   0.0.0.0:1883->1883/tcp, 0.0.0.0:9001->9001/tcp
```

### 2. Probar publicación desde CLI
```powershell
docker exec -it banco_mosquitto mosquitto_pub -t "banco/alertas" -m '{"type":"TEST","message":"Hola MQTT"}'
```

### 3. Ver mensajes en tiempo real
```powershell
python mqtt_subscriber.py
```

### 4. Hacer una transacción en el frontend
- Abre http://localhost:3000
- Login con cédula `1350509525`
- Haz un depósito de $50
- Observa el monitor MQTT mostrar el evento en tiempo real

---

## 📊 Beneficios de MQTT vs Solo WebSocket

| Característica | WebSocket Solo | WebSocket + MQTT |
|----------------|----------------|------------------|
| **Escalabilidad** | Limitada (punto a punto) | ✅ Alta (pub/sub) |
| **Desacoplamiento** | ❌ Cliente-servidor acoplados | ✅ Productores y consumidores independientes |
| **Retención** | ❌ Sin memoria | ✅ Últimos mensajes retenidos |
| **QoS** | ❌ No garantizado | ✅ 3 niveles de garantía |
| **Wildcard Subs** | ❌ No | ✅ `banco/#` para todos los tópicos |
| **Múltiples servicios** | ❌ Difícil | ✅ Fácil (analytics, logs, notificaciones) |

---

## 🔮 Casos de Uso Avanzados

### 1. **Dashboard Administrativo en Tiempo Real**
Suscribirse a `banco/estadisticas` para mostrar métricas sin polling.

### 2. **Auditoría y Compliance**
Servicio separado suscrito a `banco/transacciones` que guarda logs inmutables.

### 3. **Notificaciones Push**
Servicio que escucha `banco/alertas` y envía emails/SMS cuando saldo < $100.

### 4. **Analytics en Tiempo Real**
Apache Kafka consume de MQTT y procesa streams de transacciones.

### 5. **Multi-Datacenter Sync**
Bridge MQTT entre diferentes regiones para replicación.

---

## 🔐 Seguridad en Producción

### Actualmente (Desarrollo):
- ✅ `allow_anonymous true`
- ⚠️ Sin autenticación
- ⚠️ Sin SSL/TLS

### Para Producción:
1. **Habilitar autenticación**:
   ```conf
   allow_anonymous false
   password_file /mosquitto/config/passwd
   ```

2. **Crear usuarios**:
   ```bash
   mosquitto_passwd -c /mosquitto/config/passwd publisher
   mosquitto_passwd /mosquitto/config/passwd subscriber
   ```

3. **SSL/TLS**:
   ```conf
   listener 8883
   cafile /mosquitto/config/ca.crt
   certfile /mosquitto/config/server.crt
   keyfile /mosquitto/config/server.key
   ```

4. **ACL (Control de Acceso)**:
   ```conf
   acl_file /mosquitto/config/acl.conf
   ```

   `acl.conf`:
   ```
   user publisher
   topic write banco/#

   user subscriber
   topic read banco/#
   ```

---

## 📚 Próximos Pasos

- [ ] Integrar MQTT en frontend con `mqtt.js`
- [ ] Servicio de notificaciones por email
- [ ] Dashboard administrativo real-time
- [ ] Apache Kafka para analytics
- [ ] Bridge MQTT a Azure IoT Hub
- [ ] Autenticación y SSL en producción

---

**✅ MQTT integrado exitosamente en el sistema bancario distribuido!** 🎉
