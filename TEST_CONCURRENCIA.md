# 🧪 Pruebas de Concurrencia del Sistema Bancario

## Descripción

El archivo `test_concurrency.py` contiene pruebas exhaustivas que demuestran cómo el sistema bancario maneja correctamente **operaciones simultáneas** sin conflictos de datos gracias al sistema de **locks por cédula**.

## ¿Qué demuestra?

### 🔒 Sistema de Locks
- Cada cliente tiene su propio lock (`threading.Lock`)
- Las operaciones sobre la misma cuenta son **atómicas** (no se interrumpen)
- Múltiples threads pueden operar en **diferentes cuentas simultáneamente**
- No hay **race conditions** ni **data corruption**

### 📊 Pruebas Incluidas

#### Test 1: Depósitos Simultáneos a la Misma Cuenta
- 5 threads depositando simultáneamente en la misma cuenta
- Cada thread hace 3 depósitos de $50
- **Resultado esperado**: $750 depositados sin pérdidas

#### Test 2: Operaciones Mixtas (Depósitos + Retiros)
- 3 threads depositando
- 3 threads retirando
- Todos operando en la misma cuenta
- **Resultado esperado**: El saldo final refleja correctamente todas las operaciones

#### Test 3: Múltiples Cuentas Simultáneas
- 4 cuentas diferentes
- Cada cuenta tiene 2 threads (uno depositando, otro retirando)
- **Resultado esperado**: Cada cuenta mantiene su integridad independientemente

## 🚀 Cómo Ejecutar

### Opción 1: Desde el Panel de Administración (Recomendado)
1. Inicia sesión con la cédula de administrador: `1350509525`
2. En el **Panel de Administración**, haz clic en el botón:
   ```
   🔹 Demostración de Concurrencia
   ```
3. Se abrirá una nueva consola con las pruebas ejecutándose

### Opción 2: Manualmente desde Terminal
```bash
# Asegúrate de que el servidor esté corriendo
python test_concurrency.py
```

## 📈 Salida Esperada

La prueba mostrará:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║         PRUEBA DE CONCURRENCIA - SISTEMA BANCARIO DISTRIBUIDO            ║
╚═══════════════════════════════════════════════════════════════════════════╝

🔍 Verificando conexión con el servidor...
✅ Conexión exitosa

================================================================================
🧪 TEST 1: DEPÓSITOS SIMULTÁNEOS A LA MISMA CUENTA
================================================================================

📊 Consultando saldo inicial...
   OK|Ana|Torres|1500.00

🚀 Iniciando 5 threads simultáneos...

💰 [23:45:12.345] Thread-1 - DEPOSITO $50.00 en cédula 1315151515 (12.3ms)
💰 [23:45:12.347] Thread-2 - DEPOSITO $50.00 en cédula 1315151515 (14.1ms)
💰 [23:45:12.349] Thread-3 - DEPOSITO $50.00 en cédula 1315151515 (11.8ms)
...
```

### Métricas Mostradas
- ⏱️ **Tiempo de respuesta** de cada operación (en milisegundos)
- 📊 **Timestamp** exacto de cada operación
- 💰 **Tipo de operación** (depósito o retiro)
- ✅ **Estadísticas finales**:
  - Total de operaciones
  - Tiempo promedio/mínimo/máximo
  - Éxito/errores

## 🔍 ¿Qué Observar?

### 1. **Orden de Ejecución**
Las operaciones se ejecutan en orden aleatorio debido a la concurrencia, pero **todas se completan correctamente**.

### 2. **Timestamps Superpuestos**
Verás timestamps muy cercanos (diferencia de milisegundos), demostrando que múltiples threads están trabajando **simultáneamente**.

### 3. **Integridad de Datos**
Al final, el saldo de cada cuenta es **matemáticamente correcto**:
- Saldo Final = Saldo Inicial + Total Depósitos - Total Retiros

### 4. **Sin Race Conditions**
Nunca verás:
- ❌ Saldos negativos inesperados
- ❌ Operaciones perdidas
- ❌ Balances incorrectos

## 🛠️ Implementación Técnica

### Locks por Cédula
```python
# En socket_server.py
self.client_locks = {}  # Un lock por cada cédula

def get_client_lock(self, cedula):
    if cedula not in self.client_locks:
        self.client_locks[cedula] = threading.Lock()
    return self.client_locks[cedula]

# Uso en operaciones
with self.get_client_lock(cedula):
    # Operación atómica (leer saldo -> modificar -> guardar)
    # Ningún otro thread puede acceder a esta cédula
    # hasta que se libere el lock
```

### Ventajas de Este Enfoque
- ✅ **Alta concurrencia**: Múltiples cuentas pueden operar simultáneamente
- ✅ **Seguridad**: Cada cuenta está protegida individualmente
- ✅ **Rendimiento**: No bloquea toda la base de datos, solo la cuenta específica
- ✅ **Escalabilidad**: Puede manejar miles de clientes concurrentes

## 📊 Estadísticas del Panel de Administración

Mientras ejecutas las pruebas, el **Panel de Administración** mostrará en tiempo real:

- **Clientes Conectados**: Número de conexiones activas
- **Ops. Simultáneas**: Cuántas operaciones se están procesando al mismo tiempo
- **Conexiones Activas**: Threads activos del servidor

Estos números se actualizan cada 5 segundos y reflejan el **estado real** del servidor.

## 🎯 Casos de Uso

Este script es útil para:
1. **Demostrar** el correcto funcionamiento del sistema de locks
2. **Validar** que no hay race conditions
3. **Medir** el rendimiento bajo carga concurrente
4. **Probar** la robustez del sistema antes de producción

## ⚠️ Requisitos

- ✅ El servidor socket debe estar corriendo (`socket_server.py`)
- ✅ La base de datos MySQL debe estar activa
- ✅ Python 3.8+

## 📝 Notas

- Las pruebas usan cuentas reales de la base de datos
- Los cambios en los saldos son **persistentes**
- Se recomienda ejecutar `db_setup.py` para resetear los datos si es necesario
- El script tiene colores para facilitar la lectura (funciona mejor en terminales que soportan ANSI)

---

**Desarrollado como parte del examen de Sistemas Distribuidos**  
*Demostrando concurrencia, sincronización y consistencia de datos*
