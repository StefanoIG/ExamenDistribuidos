# ⚡ Guía de Despliegue Rápido

## 🚀 Opción 1: Inicio Automático (Recomendado)

### En PowerShell (Windows)

```powershell
# Permitir ejecución de scripts (si es la primera vez)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Navegar a la carpeta del proyecto
cd c:\Users\StefanoIG\PycharmProjects\ExamenDistribuidos

# Ejecutar script de inicio
.\start.ps1 -Todos
```

### En Bash/Linux/Mac

```bash
chmod +x start.sh
./start.sh
```

---

## 🔧 Opción 2: Inicio Manual por Componentes

### Terminal 1: Servidor Socket

```bash
cd c:\Users\StefanoIG\PycharmProjects\ExamenDistribuidos
python socket_server.py
```

**Esperado:**
```
[2025-11-10 14:32:10] INFO - 🚀 Servidor escuchando en 0.0.0.0:5000
[2025-11-10 14:32:10] INFO - 📊 Esperando conexiones de clientes...
```

### Terminal 2: Bridge Flask

```bash
cd c:\Users\StefanoIG\PycharmProjects\ExamenDistribuidos
python socket_bridge.py
```

**Esperado:**
```
[2025-11-10 14:32:12] INFO - 🚀 Iniciando bridge en port 5001
[2025-11-10 14:32:12] INFO - 🔗 Conectando a socket server en localhost:5000
```

### Terminal 3: Frontend Next.js

```bash
cd c:\Users\StefanoIG\PycharmProjects\ExamenDistribuidos\Frontend
pnpm dev
```

**Esperado:**
```
▲ Next.js 14.0.0
- Local: http://localhost:3000
```

---

## 📱 Acceso a la Aplicación

| Componente | URL | Acceso |
|-----------|-----|--------|
| **Frontend** | http://localhost:3000 | 🌐 Navegador |
| **API Bridge** | http://localhost:5001/api | 🔌 HTTP POST |
| **Socket Server** | localhost:5000 | 🔗 TCP/IP |

---

## 🧪 Pruebas Rápidas

### 1. Test Servidor Socket (Cliente de prueba)

```bash
python socket_client.py --test
```

Ejecuta un conjunto de pruebas automáticas contra el servidor.

### 2. Test Interactivo

```bash
python socket_client.py
```

Modo shell interactivo para enviar comandos manualmente:

```
📥 Ingresa comando: CONSULTA 1315151515
✅ Operación exitosa
   Nombres: Juan
   Apellidos: Pérez García
   Saldo: $1500.00

📥 Ingresa comando: AUMENTAR 1315151515 500
✅ Operación exitosa
   Depósito exitoso
   Nuevo saldo: $2000.00
```

### 3. Test API Bridge con curl

```bash
# Consultar cliente
curl -X POST http://localhost:5001/api/consulta \
  -H "Content-Type: application/json" \
  -d '{"cedula":"1315151515"}'

# Hacer depósito
curl -X POST http://localhost:5001/api/deposito \
  -H "Content-Type: application/json" \
  -d '{"cedula":"1315151515","monto":500}'

# Ver historial
curl -X GET http://localhost:5001/api/historial/1315151515

# Ver estadísticas
curl -X GET http://localhost:5001/api/stats
```

---

## 🗄️ Setup Base de Datos (Primera vez)

```bash
python db_setup.py
```

Ingresa contraseña de MySQL cuando se solicite. El script:

✅ Crea la base de datos `examen`
✅ Crea tablas `clientes` y `transacciones`
✅ Inserta datos de ejemplo
✅ Muestra resumen de datos creados

---

## 📊 Monitoreo

### Ver Logs del Servidor

```bash
# En tiempo real
tail -f server.log

# Últimas 50 líneas
tail -50 server.log

# Buscar errores
grep ERROR server.log
```

### Ver Logs del Bridge

```bash
tail -f bridge.log
```

### Ver Logs de Setup

```bash
tail -f setup.log
```

---

## ⚠️ Solución de Problemas Comunes

### Error: "Address already in use"

**Problema:** El puerto ya está ocupado

**Solución:**
```bash
# Encontrar proceso que usa el puerto (Windows)
netstat -ano | findstr :5000

# Terminar proceso
taskkill /PID <PID> /F

# Cambiar puerto en .env
```

### Error: "Connection refused"

**Problema:** El servidor socket no está corriendo

**Solución:**
```bash
# Terminal 1: Iniciar servidor
python socket_server.py

# Luego: Terminal 2 para bridge
python socket_bridge.py
```

### Error: "Database 'examen' does not exist"

**Problema:** Base de datos no configurada

**Solución:**
```bash
python db_setup.py
```

### Error: "No module named 'mysql'"

**Problema:** Dependencias no instaladas

**Solución:**
```bash
pip install -r requirements.txt
```

### Error: "ModuleNotFoundError: No module named 'flask'"

**Problema:** Dependencias de Flask no instaladas

**Solución:**
```bash
pip install flask flask-cors
```

---

## 🎯 Flujo de Prueba Recomendado

### 1️⃣ Iniciar todos los servicios
```bash
.\start.ps1 -Todos
```

### 2️⃣ Verificar servidor socket
```bash
python socket_client.py --test
```

### 3️⃣ Abrir frontend en navegador
```
http://localhost:3000
```

### 4️⃣ Pruebas en la UI
- Ingresar cédula: `1315151515`
- Ver saldo
- Hacer depósito
- Ver historial
- Hacer retiro
- Crear nuevo cliente

### 5️⃣ Monitorear logs
```bash
# En otra terminal
tail -f server.log
```

---

## 📝 Checklist de Verificación

### ✅ Servidor Socket
- [ ] Escucha en puerto 5000
- [ ] Acepta múltiples conexiones
- [ ] Procesa comandos correctamente
- [ ] Genera logs en `server.log`
- [ ] Sincroniza con locks
- [ ] Cierra conexiones correctamente

### ✅ Bridge Flask
- [ ] Escucha en puerto 5001
- [ ] Conecta al servidor socket
- [ ] Traduce HTTP → Socket
- [ ] Retorna JSON válido
- [ ] CORS habilitado
- [ ] Genera logs en `bridge.log`

### ✅ Frontend Next.js
- [ ] Se inicia en puerto 3000
- [ ] Accesible en http://localhost:3000
- [ ] Conexión con API funciona
- [ ] UI se carga correctamente
- [ ] Operaciones funcionan

### ✅ Base de Datos
- [ ] MySQL está corriendo
- [ ] Base de datos `examen` existe
- [ ] Tablas `clientes` y `transacciones` existen
- [ ] Datos de ejemplo insertados
- [ ] Consultas funcionan correctamente

---

## 🔥 Modo de Producción (Avanzado)

### Usar Gunicorn para Flask

```bash
pip install gunicorn

gunicorn --workers 4 --bind 0.0.0.0:5001 socket_bridge:app
```

### Usar Supervisor para procesos persistentes

```bash
pip install supervisor

# Configurar en /etc/supervisor/conf.d/sistema_bancario.conf
[program:socket_server]
command=python socket_server.py
directory=/ruta/al/proyecto
autostart=true
autorestart=true

[program:socket_bridge]
command=gunicorn --workers 4 socket_bridge:app
directory=/ruta/al/proyecto
autostart=true
autorestart=true
```

---

## 💾 Backup de Base de Datos

```bash
# Backup
mysqldump -u socketuser -p examen > backup_examen.sql

# Restore
mysql -u socketuser -p examen < backup_examen.sql
```

---

## 🎓 Puntos Clave para Demostrar

Cuando demuestres el sistema, resalta:

1. **Threading**
   - Múltiples clientes conectados simultáneamente
   - Cada uno en su propio hilo
   - Logs mostrando [Thread-X-Y]

2. **Concurrencia**
   - Ejecutar `socket_client.py` en 2 terminales
   - Ambas haciendo transacciones simultáneamente
   - Logs mostrando locks siendo adquiridos/liberados
   - Saldo siempre consistente

3. **Persistencia**
   - Transacciones almacenadas en BD
   - Historial disponible
   - Datos persisten después de reiniciar

4. **Logging**
   - `server.log` con detalles de cada operación
   - Timestamps precisos
   - Niveles de severidad (INFO, WARNING, ERROR)

5. **API REST**
   - Frontend comunica vía HTTP/JSON
   - Bridge traduce a comandos socket
   - Respuestas estructuradas

---

## 📞 Comandos Rápidos

```bash
# Iniciar todo de una vez
.\start.ps1 -Todos

# Solo pruebas
python socket_client.py --test

# Setup BD
python db_setup.py

# Logs en tiempo real
Get-Content -Path server.log -Wait -Tail 50

# Ver puertos activos
netstat -ano

# Detener proceso en puerto
taskkill /F /IM python.exe
```

---

**¡Listo para presentar!** 🚀
