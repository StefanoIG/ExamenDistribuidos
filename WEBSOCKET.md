# 🔌 WebSocket - Actualizaciones en Tiempo Real

## Descripción

El sistema utiliza **WebSocket** (Socket.IO) para proporcionar actualizaciones en tiempo real sin necesidad de recargar la página o hacer polling.

## Eventos WebSocket

### 📊 `stats_updated`
**Emisión**: Cada 3 segundos (broadcast automático)  
**Propósito**: Actualizar estadísticas del servidor en el panel de administración

**Datos enviados**:
```json
{
  "success": true,
  "estadisticas": {
    "clientes_activos": 5,
    "operaciones_simultaneas": 2,
    "conexiones_activas": 8
  }
}
```

**Componentes que lo escuchan**:
- `AdminPanel.tsx` - Actualiza contadores en tiempo real

---

### 💰 `balance_updated`
**Emisión**: Cuando se realiza un depósito o retiro  
**Propósito**: Notificar a todos los clientes conectados sobre cambios de saldo

**Datos enviados**:
```json
{
  "cedula": "1350509525",
  "balance": 5250.00
}
```

**Componentes que lo escuchan**:
- `Dashboard.tsx` - Actualiza el saldo y transacciones automáticamente

**Ventaja**: Si tienes la misma cuenta abierta en 2 pestañas, ambas se actualizan instantáneamente cuando haces una operación en una de ellas.

---

### ✅ `connected`
**Emisión**: Cuando un cliente se conecta por WebSocket  
**Propósito**: Confirmar conexión exitosa

---

## Implementación Frontend

### Context Provider (`socket-context.tsx`)

```typescript
const newSocket = io("http://localhost:5001", {
  transports: ["websocket", "polling"],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5
})

// Escuchar balance updates
newSocket.on("balance_updated", (data) => {
  window.dispatchEvent(new CustomEvent("balanceUpdate", { detail: data }))
})

// Escuchar stats updates
newSocket.on("stats_updated", (data) => {
  window.dispatchEvent(new CustomEvent("statsUpdate", { detail: data }))
})
```

### Componentes escuchando eventos

**Dashboard.tsx**:
```typescript
useEffect(() => {
  const handleBalanceUpdate = (event: Event) => {
    const data = (event as CustomEvent).detail
    if (data.cedula === cedula) {
      setUserData(prev => ({ ...prev, balance: data.balance }))
      // Refrescar transacciones
      refreshTransactions()
    }
  }
  
  window.addEventListener("balanceUpdate", handleBalanceUpdate)
  return () => window.removeEventListener("balanceUpdate", handleBalanceUpdate)
}, [cedula])
```

**AdminPanel.tsx**:
```typescript
useEffect(() => {
  const handleStatsUpdate = (event: CustomEvent) => {
    const data = event.detail
    setStats({
      clientes_activos: data.estadisticas.clientes_activos,
      operaciones_simultaneas: data.estadisticas.operaciones_simultaneas,
      conexiones_activas: data.estadisticas.conexiones_activas
    })
  }
  
  window.addEventListener("statsUpdate", handleStatsUpdate)
  return () => window.removeEventListener("statsUpdate", handleStatsUpdate)
}, [])
```

## Implementación Backend

### Servidor WebSocket (`socket_bridge.py`)

```python
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Broadcast de balance
def broadcast_balance_update(cedula, new_balance):
    socketio.emit('balance_updated', {
        'cedula': cedula,
        'balance': new_balance
    }, broadcast=True)

# Thread para broadcast de stats cada 3 segundos
def broadcast_stats():
    while True:
        time.sleep(3)
        comando = "STATS"
        respuesta = SocketBridge.send_command(comando)
        resultado = SocketBridge.parsear_respuesta(respuesta)
        
        if resultado.get('success'):
            socketio.emit('stats_updated', resultado, broadcast=True)
```

### Endpoints que emiten eventos

**`/api/deposito`**:
```python
@app.route('/api/deposito', methods=['POST'])
def deposito():
    # ... lógica de depósito ...
    
    if resultado.get('success'):
        nuevo_saldo = resultado['data']['nuevo_saldo']
        broadcast_balance_update(cedula, nuevo_saldo)  # 🔥 Emite WebSocket
    
    return jsonify(resultado)
```

**`/api/retiro`**:
```python
@app.route('/api/retiro', methods=['POST'])
def retiro():
    # ... lógica de retiro ...
    
    if resultado.get('success'):
        nuevo_saldo = resultado['data']['nuevo_saldo']
        broadcast_balance_update(cedula, nuevo_saldo)  # 🔥 Emite WebSocket
    
    return jsonify(resultado)
```

## Indicadores de Conexión

### Dashboard
Muestra badge "En Línea" o "Desconectado" en el header:
- 🟢 **En Línea**: WebSocket conectado
- 🔴 **Desconectado**: Sin conexión WebSocket

## Ventajas

1. **✅ Tiempo Real**: Los cambios se reflejan inmediatamente sin recargar
2. **✅ Multi-Pestaña**: Si abres la misma cuenta en varias pestañas, todas se sincronizan
3. **✅ Eficiencia**: No hay polling constante, solo se envía cuando hay cambios
4. **✅ Escalabilidad**: Socket.IO maneja reconexiones automáticamente
5. **✅ Broadcast**: Un evento afecta a todos los clientes conectados

## Flujo de Actualización

```
Usuario A (Pestaña 1) hace depósito
    ↓
POST /api/deposito
    ↓
socket_bridge.py actualiza saldo
    ↓
broadcast_balance_update()
    ↓
WebSocket emite 'balance_updated'
    ↓
Todos los clientes conectados reciben el evento
    ↓
Usuario A (Pestaña 1) ✅
Usuario A (Pestaña 2) ✅
Usuario B (Observando) ✅
Admin (Panel) ✅ (stats también se actualizan)
```

## Dependencias

**Backend**:
```
flask-socketio==5.3.5
python-socketio==5.10.0
```

**Frontend**:
```
socket.io-client: "^4.7.2"
```

## Configuración

**Puerto WebSocket**: 5001 (mismo puerto que HTTP)  
**CORS**: Permitido desde cualquier origen (`*`)  
**Transports**: WebSocket y polling (fallback)  
**Reconnection**: Habilitado con 5 intentos

---

**Desarrollado para demostrar comunicación en tiempo real en sistemas distribuidos**
