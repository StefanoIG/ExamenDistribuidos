# 🔌 Integrar MQTT en Frontend Next.js (Opcional)

## ¿Por qué usar MQTT en el Frontend?

MQTT complementa WebSocket para casos específicos:

- ✅ **Múltiples fuentes de datos**: Suscribirse a eventos de diferentes servicios
- ✅ **Retención de mensajes**: Obtener último estado al conectar
- ✅ **QoS garantizado**: Asegurar entrega de mensajes críticos
- ✅ **Desacoplamiento**: Frontend no depende directamente del backend

**Nota**: El sistema ya funciona completamente con WebSocket. MQTT es una mejora opcional para casos avanzados.

---

## 📦 Instalación

```bash
cd Frontend
npm install mqtt
```

---

## 🔧 Configuración

### 1. Agregar variable de entorno

**`Frontend/.env.local`:**
```env
NEXT_PUBLIC_MQTT_BROKER_URL=ws://localhost:9001
```

**Producción (`Frontend/.env.production`):**
```env
NEXT_PUBLIC_MQTT_BROKER_URL=wss://your-mqtt-broker.com:9001
```

### 2. Copiar hook personalizado

```bash
# Renombrar archivo de ejemplo
mv hooks/use-mqtt.ts.example hooks/use-mqtt.ts
```

---

## 🚀 Uso Básico

### Ejemplo 1: Monitor de transacciones en tiempo real

```typescript
import { useMQTT } from '@/hooks/use-mqtt';

export function TransactionMonitor() {
  const { messages, isConnected } = useMQTT({
    topics: ['banco/transacciones']
  });

  return (
    <div>
      <div>Estado: {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}</div>
      
      {messages.map((msg, i) => (
        <div key={i}>
          {msg.payload.tipo}: ${msg.payload.monto}
        </div>
      ))}
    </div>
  );
}
```

### Ejemplo 2: Suscripción dinámica por cédula

```typescript
export function UserBalance({ cedula }: { cedula: string }) {
  const { messages, subscribe, isConnected } = useMQTT();
  const [balance, setBalance] = useState<number | null>(null);

  useEffect(() => {
    if (isConnected) {
      // Suscribirse al saldo específico del usuario
      subscribe(`banco/saldo/${cedula}`);
    }
  }, [isConnected, cedula]);

  useEffect(() => {
    // Actualizar saldo cuando llega mensaje
    const saldoMsg = messages.find(m => m.topic === `banco/saldo/${cedula}`);
    if (saldoMsg) {
      setBalance(saldoMsg.payload.saldo_nuevo);
    }
  }, [messages, cedula]);

  return (
    <div>
      Saldo: ${balance?.toFixed(2) ?? 'Cargando...'}
    </div>
  );
}
```

### Ejemplo 3: Notificaciones de alertas

```typescript
export function AlertNotifier() {
  const { messages } = useMQTT({
    topics: ['banco/alertas'],
    onMessage: (topic, message) => {
      if (message.type === 'LOW_BALANCE') {
        // Mostrar toast notification
        toast.warning(`⚠️ ${message.message}`);
      }
    }
  });

  return null; // Component sin UI, solo escucha eventos
}
```

---

## 🎨 Componente Completo: Monitor MQTT

Copiar el archivo de ejemplo:

```bash
mv components/mqtt-transaction-monitor.tsx.example components/mqtt-transaction-monitor.tsx
```

Usar en tu página:

```typescript
// app/admin/page.tsx
import { MQTTTransactionMonitor } from '@/components/mqtt-transaction-monitor';

export default function AdminPage() {
  return (
    <div className="p-8">
      <h1>Panel de Administración</h1>
      <MQTTTransactionMonitor />
    </div>
  );
}
```

---

## 🔄 Comparación: WebSocket vs MQTT en Frontend

| Característica | WebSocket (Actual) | MQTT (Opcional) |
|----------------|-------------------|-----------------|
| **Estado inicial** | ✅ Sí (API call) | ✅ Sí (retained messages) |
| **Actualizaciones** | ✅ Real-time | ✅ Real-time |
| **Complejidad** | 🟢 Simple | 🟡 Media |
| **Multi-servicio** | ❌ Solo backend | ✅ Cualquier publisher |
| **Wildcards** | ❌ No | ✅ `banco/#` |
| **QoS** | ❌ Best effort | ✅ 0, 1, 2 |

**Recomendación**: Mantener WebSocket para la aplicación principal. Usar MQTT solo para:
- Dashboard administrativo en tiempo real
- Monitoreo de múltiples cuentas simultáneamente
- Integración con otros servicios (analytics, logs)

---

## 🧪 Probar Integración

### 1. Iniciar broker MQTT
```bash
docker-compose up mosquitto
```

### 2. Iniciar frontend
```bash
cd Frontend
npm run dev
```

### 3. Abrir consola del navegador

Deberías ver:
```
✅ Conectado a MQTT broker: ws://localhost:9001
📡 Suscrito a: banco/transacciones
```

### 4. Hacer una transacción

Desde otra terminal:
```bash
docker exec -it banco_mosquitto mosquitto_pub -t "banco/transacciones" -m '{"cedula":"123","tipo":"DEPOSITO","monto":100,"saldo_nuevo":1100,"timestamp":"2024-01-01T12:00:00"}'
```

Verás el mensaje aparecer en el componente!

---

## 🔐 Seguridad

### Desarrollo (localhost)
```typescript
const { messages } = useMQTT({
  brokerUrl: 'ws://localhost:9001' // Sin autenticación
});
```

### Producción (con SSL y auth)
```typescript
const { messages } = useMQTT({
  brokerUrl: 'wss://your-broker.com:9001',
  username: process.env.NEXT_PUBLIC_MQTT_USERNAME,
  password: process.env.NEXT_PUBLIC_MQTT_PASSWORD
});
```

**Nota**: Nunca expongas credenciales MQTT en el frontend para producción. Usa tokens JWT o autenticación por IP.

---

## 📊 Casos de Uso Recomendados

### ✅ Cuándo usar MQTT en Frontend:

1. **Dashboard administrativo**: Múltiples gráficas en tiempo real
2. **Monitor de sistema**: Ver todas las transacciones de todos los usuarios
3. **Alertas críticas**: Notificaciones push de eventos importantes
4. **Multi-cuenta**: Usuario supervisor viendo múltiples cuentas

### ❌ Cuándo NO usar MQTT en Frontend:

1. **Operaciones de usuario simple**: WebSocket es suficiente
2. **Login/Transacciones**: Usar WebSocket (ya implementado)
3. **Datos sensibles**: No enviar información privada vía MQTT público

---

## 🐛 Troubleshooting

### No se conecta al broker

**Solución**: Verificar que Mosquitto WebSocket está en puerto 9001:
```bash
docker exec -it banco_mosquitto cat /mosquitto/config/mosquitto.conf | grep 9001
```

Debe mostrar:
```
listener 9001
protocol websockets
```

### CORS error en navegador

**Solución**: Mosquitto no tiene CORS. Usar proxy nginx o configurar CORS en Mosquitto config:
```conf
# mosquitto.conf
http_dir /var/www/html
```

### Mensajes no llegan

**Solución**: Verificar tópicos con CLI:
```bash
docker exec -it banco_mosquitto mosquitto_sub -t "banco/#" -v
```

---

## 🎯 Próximos Pasos

- [ ] Implementar `use-mqtt.ts` hook
- [ ] Crear componente `MQTTTransactionMonitor`
- [ ] Agregar notificaciones con `sonner` toast
- [ ] Configurar SSL para producción
- [ ] Implementar autenticación MQTT

---

**Frontend MQTT es completamente opcional. El sistema funciona perfectamente solo con WebSocket.** 

Use MQTT solo si necesita características avanzadas como multi-servicio pub/sub o retención de mensajes.
