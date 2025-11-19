# 🚀 Quick Start - Sistema Bancario con MQTT

## Iniciar Todo el Sistema con MQTT

### 1️⃣ Iniciar con Docker Compose (Incluye MQTT Broker)

```bash
docker-compose up -d
```

Esto inicia:
- ✅ MySQL Database (puerto 3306)
- ✅ **MQTT Broker Mosquitto (puertos 1883, 9001)**
- ✅ Socket Server con MQTT Publisher (puerto 5000)
- ✅ Flask Bridge (puerto 5001)

### 2️⃣ Monitorear Eventos MQTT en Tiempo Real

En una nueva terminal:

```bash
# Instalar dependencia si aún no está
pip install paho-mqtt

# Iniciar monitor
python mqtt_subscriber.py
```

Verás eventos como:
```
💰 DEPÓSITO: $150.00 - Cédula: 1350509525 - Nuevo saldo: $1150.00
💸 RETIRO: $50.00 - Cédula: 1350509525 - Nuevo saldo: $1100.00
🚨 ALERTA [LOW_BALANCE]: Saldo bajo: $85.50 (Cédula: 1350509525)
📊 STATS: Conectados: 5 | Transacciones: 127 | IPs activas: 3
```

### 3️⃣ Iniciar Frontend

```bash
cd Frontend
npm install
npm run dev
```

Abre: http://localhost:3000

---

## 📡 Tópicos MQTT Disponibles

| Tópico | Descripción |
|--------|-------------|
| `banco/transacciones` | Todas las transacciones |
| `banco/depositos` | Solo depósitos |
| `banco/retiros` | Solo retiros |
| `banco/saldo/{cedula}` | Saldo por cédula (retained) |
| `banco/estadisticas` | Stats del servidor |
| `banco/alertas` | Alertas (saldo bajo, etc) |

---

## 🧪 Probar MQTT con CLI

### Suscribirse a un tópico:

```bash
# Dentro del contenedor
docker exec -it banco_mosquitto mosquitto_sub -t "banco/transacciones" -v

# Todos los tópicos
docker exec -it banco_mosquitto mosquitto_sub -t "banco/#" -v
```

### Publicar mensaje de prueba:

```bash
docker exec -it banco_mosquitto mosquitto_pub -t "banco/alertas" -m '{"type":"TEST","message":"Hola MQTT"}'
```

---

## 🛑 Detener Todo

```bash
docker-compose down
```

Mantener datos (no eliminar volúmenes):
```bash
docker-compose down --volumes
```

---

## 📚 Documentación Completa

- [MQTT_GUIDE.md](./MQTT_GUIDE.md) - Guía completa de MQTT
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Despliegue en producción

---

## 🔧 Troubleshooting

### MQTT no se conecta

```bash
# Verificar que Mosquitto está corriendo
docker ps | grep mosquitto

# Ver logs
docker logs banco_mosquitto
```

### No llegan mensajes MQTT

```bash
# Probar conectividad
telnet localhost 1883

# Ver logs del publisher (socket_server)
docker logs banco_socket_server
```

---

**¡Sistema con MQTT listo! 🎉**
