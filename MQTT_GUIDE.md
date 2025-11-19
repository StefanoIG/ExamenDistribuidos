# 🚀 Integración MQTT en Sistema Bancario Distribuido

## 📋 Descripción General

Este sistema ahora integra **MQTT (Message Queuing Telemetry Transport)** para comunicación pub/sub escalable y asíncrona entre componentes distribuidos.

### ✨ Beneficios de MQTT

- **Pub/Sub desacoplado**: Productores y consumidores no necesitan conocerse
- **QoS (Quality of Service)**: 3 niveles de garantía de entrega
- **Retención de mensajes**: Los nuevos suscriptores reciben el último mensaje
- **Ligero**: Protocolo binario optimizado para IoT y sistemas distribuidos
- **Escalable**: Soporta miles de conexiones concurrentes
- **Wildcard subscriptions**: Suscripción a múltiples tópicos con `#` y `+`

---

## 🏗️ Arquitectura MQTT

```
┌─────────────────────────────────────────────────────────────┐
│                    MQTT Broker (Mosquitto)                  │
│                     Port 1883 (MQTT)                        │
│                     Port 9001 (WebSocket)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬─────────────┐
        │            │            │             │
   Publisher    Subscriber    Subscriber   Subscriber
  (Socket Server) (Frontend) (Analytics)  (Monitor)
```

---

## 📡 Tópicos MQTT Disponibles

| Tópico | QoS | Retain | Descripción |
|--------|-----|--------|-------------|
| `banco/transacciones` | 1 | No | Todas las transacciones (depósitos + retiros) |
| `banco/depositos` | 1 | No | Solo depósitos |
| `banco/retiros` | 1 | No | Solo retiros |
| `banco/saldo/{cedula}` | 1 | **Sí** | Actualización de saldo por cédula |
| `banco/estadisticas` | 0 | **Sí** | Estadísticas del servidor (cada 3s) |
| `banco/alertas` | 2 | No | Alertas críticas (saldo bajo, etc) |

### 🔑 Wildcards

- `banco/saldo/#` - Todos los saldos de todas las cédulas
- `banco/+/1350509525` - Cualquier evento de la cédula 1350509525

---

## 📊 Estructura de Mensajes

### 1️⃣ Transacción (`banco/transacciones`)

```json
{
  "cedula": "1350509525",
  "tipo": "DEPOSITO",
  "monto": 150.00,
  "saldo_nuevo": 1150.00,
  "timestamp": "2024-01-15T14:30:00"
}
```

### 2️⃣ Actualización de Saldo (`banco/saldo/{cedula}`)

```json
{
  "cedula": "1350509525",
  "saldo_nuevo": 1150.00,
  "saldo_anterior": 1000.00,
  "timestamp": "2024-01-15T14:30:00"
}
```

**Nota**: Este mensaje tiene `retain=True`, por lo que nuevos suscriptores reciben el último saldo inmediatamente.

### 3️⃣ Estadísticas (`banco/estadisticas`)

```json
{
  "clientes_conectados": 5,
  "total_transacciones": 127,
  "ips_activas": 3,
  "timestamp": "2024-01-15T14:30:00"
}
```

### 4️⃣ Alerta (`banco/alertas`)

```json
{
  "type": "LOW_BALANCE",
  "message": "Saldo bajo: $85.50",
  "cedula": "1350509525",
  "data": {
    "saldo": 85.50
  },
  "timestamp": "2024-01-15T14:30:00"
}
```

---

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias

```bash
pip install paho-mqtt
```

Ya está incluido en `requirements.txt`.

### 2. Variables de Entorno

Agregar a `.env`:

```env
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
```

### 3. Iniciar Broker MQTT (Mosquitto)

#### Opción A: Docker (Recomendado)

```bash
docker-compose up mosquitto
```

#### Opción B: Instalación Local

**Windows (con Chocolatey):**
```powershell
choco install mosquitto
mosquitto -c mosquitto\config\mosquitto.conf
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

**macOS (con Homebrew):**
```bash
brew install mosquitto
brew services start mosquitto
```

---

## 🧪 Pruebas

### 1️⃣ Monitorear Todos los Eventos

```bash
python mqtt_subscriber.py
```

Salida esperada:
```
🏦 Sistema Bancario - Monitor MQTT
============================================================
✅ Conectado a broker MQTT
📡 Suscrito a: banco/transacciones (QoS 1)
📡 Suscrito a: banco/depositos (QoS 1)
📡 Suscrito a: banco/retiros (QoS 1)
📡 Suscrito a: banco/saldo/# (QoS 1)
📡 Suscrito a: banco/estadisticas (QoS 0)
📡 Suscrito a: banco/alertas (QoS 2)
👂 Escuchando eventos MQTT... (Ctrl+C para salir)

💰 DEPÓSITO: $150.00 - Cédula: 1350509525 - Nuevo saldo: $1150.00
💸 RETIRO: $50.00 - Cédula: 1350509525 - Nuevo saldo: $1100.00
🚨 ALERTA [LOW_BALANCE]: Saldo bajo: $85.50 (Cédula: 1350509525)
```

### 2️⃣ Suscribirse a un Solo Tópico (CLI)

```bash
# Windows
docker exec -it banco_mosquitto mosquitto_sub -h localhost -t "banco/transacciones" -v

# Linux/macOS
mosquitto_sub -h localhost -t "banco/transacciones" -v
```

### 3️⃣ Publicar Mensaje de Prueba (CLI)

```bash
# Windows
docker exec -it banco_mosquitto mosquitto_pub -h localhost -t "banco/alertas" -m '{"type":"TEST","message":"Prueba"}'

# Linux/macOS
mosquitto_pub -h localhost -t "banco/alertas" -m '{"type":"TEST","message":"Prueba"}'
```

---

## 🔧 Integración con Frontend (Next.js)

### Opción 1: MQTT sobre WebSocket

Instalar cliente MQTT para navegador:

```bash
cd Frontend
npm install mqtt
```

Crear hook personalizado `hooks/use-mqtt.ts`:

```typescript
import { useEffect, useState } from 'react';
import mqtt, { MqttClient } from 'mqtt';

export function useMQTT(topics: string[]) {
  const [client, setClient] = useState<MqttClient | null>(null);
  const [messages, setMessages] = useState<any[]>([]);

  useEffect(() => {
    // Conectar a broker vía WebSocket
    const mqttClient = mqtt.connect('ws://localhost:9001');

    mqttClient.on('connect', () => {
      console.log('✅ Conectado a MQTT Broker');
      topics.forEach(topic => {
        mqttClient.subscribe(topic);
      });
    });

    mqttClient.on('message', (topic, payload) => {
      const message = JSON.parse(payload.toString());
      setMessages(prev => [...prev, { topic, message }]);
    });

    setClient(mqttClient);

    return () => {
      mqttClient.end();
    };
  }, []);

  return { client, messages };
}
```

Usar en componente:

```typescript
function TransactionMonitor() {
  const { messages } = useMQTT(['banco/transacciones']);

  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i}>
          {msg.message.tipo}: ${msg.message.monto}
        </div>
      ))}
    </div>
  );
}
```

---

## 📈 Casos de Uso Avanzados

### 1️⃣ Dashboard en Tiempo Real

Suscribirse a `banco/estadisticas` para mostrar métricas en vivo.

### 2️⃣ Notificaciones Push

Suscribirse a `banco/alertas` para alertas de saldo bajo.

### 3️⃣ Auditoría y Analytics

Suscribirse a `banco/transacciones` para análisis en tiempo real.

### 4️⃣ Sincronización Multi-Tab

Usar `banco/saldo/{cedula}` con `retain=true` para sincronizar saldo entre pestañas.

---

## 🔐 Seguridad en Producción

### 1. Habilitar Autenticación

Editar `mosquitto/config/mosquitto.conf`:

```conf
allow_anonymous false
password_file /mosquitto/config/passwd
```

Crear usuario:

```bash
docker exec -it banco_mosquitto mosquitto_passwd -c /mosquitto/config/passwd banco_user
```

### 2. SSL/TLS

```conf
listener 8883
protocol mqtt
cafile /mosquitto/config/ca.crt
certfile /mosquitto/config/server.crt
keyfile /mosquitto/config/server.key
```

### 3. ACL (Control de Acceso)

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

## 🐛 Troubleshooting

### Problema: "Connection refused"

**Solución**: Verificar que Mosquitto esté corriendo:
```bash
docker ps | grep mosquitto
```

### Problema: "No messages received"

**Solución**: Verificar suscripción con CLI:
```bash
docker exec -it banco_mosquitto mosquitto_sub -h localhost -t "banco/#" -v
```

### Problema: "Messages lost"

**Solución**: Aumentar QoS a 1 o 2 en publisher y subscriber.

---

## 📚 Recursos

- [MQTT.org](https://mqtt.org/) - Especificación oficial
- [Eclipse Mosquitto](https://mosquitto.org/) - Broker MQTT
- [Paho Python](https://eclipse.dev/paho/index.php?page=clients/python/index.php) - Cliente Python
- [MQTT.js](https://github.com/mqttjs/MQTT.js) - Cliente JavaScript/TypeScript

---

## 🎯 Próximos Pasos

1. ✅ Integración básica de MQTT completada
2. 🔲 Frontend con MQTT.js (opcional)
3. 🔲 Autenticación y SSL en producción
4. 🔲 Analytics con Apache Kafka (alternativa a MQTT)
5. 🔲 Microservicio de notificaciones (email/SMS)

---

**¡MQTT integrado exitosamente! 🎉**
