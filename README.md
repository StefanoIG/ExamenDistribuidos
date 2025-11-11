# 🏦 Sistema Bancario Distribuido

Sistema bancario con arquitectura distribuida usando **Socket TCP/IP**, **Multi-threading**, **Control de concurrencia**, **Bases de datos MySQL** y **Frontend React/Next.js**.

## 📋 Tabla de Contenidos

- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Ejecución](#-ejecución)
- [Arquitectura](#-arquitectura)
- [Comandos Disponibles](#-comandos-disponibles)
- [Características Pro](#-características-pro)

---

## 🛠 Requisitos

### Backend
- **Python 3.8+**
- **MySQL 8.0+** o **MariaDB 10.5+**
- Librerías Python: ver `requirements.txt`

### Frontend
- **Node.js 18+**
- **pnpm** o **npm**

---

## 📦 Instalación

### 1. Backend - Instalación de dependencias Python

```bash
cd c:\Users\StefanoIG\PycharmProjects\ExamenDistribuidos

# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Frontend - Instalación de dependencias Node.js

```bash
cd Frontend

# Con pnpm (recomendado)
pnpm install

# O con npm
npm install
```

---

## ⚙️ Configuración

### 1. Base de datos MySQL

Asegúrate de que MySQL esté corriendo:

```bash
# En Windows (si está instalado como servicio)
# Debería estar corriendo automáticamente

# O inicia manualmente:
mysql -u root
```

### 2. Variables de Entorno

Crea/actualiza el archivo `.env` en la raíz del proyecto:

```env
# Base de Datos MySQL
DB_HOST=localhost
DB_PORT=3306
DB_NAME=examen
DB_USER=socketuser
DB_PASSWORD=12345

# Servidor de Sockets
SERVER_HOST=0.0.0.0
SERVER_PORT=5000

# Bridge Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5001

# Logging
LOG_LEVEL=INFO
```

### 3. Crear Base de Datos

```bash
# Ejecutar script de setup
python db_setup.py

# Ingresa la contraseña de MySQL cuando se solicite
```

Este script:
- ✅ Crea la base de datos `examen`
- ✅ Crea las tablas `clientes` y `transacciones`
- ✅ Inserta datos de ejemplo
- ✅ Muestra los datos creados

---

## 🚀 Ejecución

### Opción 1: Terminal separadas (Recomendado para desarrollo)

#### Terminal 1 - Servidor Socket

```bash
cd c:\Users\StefanoIG\PycharmProjects\ExamenDistribuidos

python socket_server.py

# Esperado:
# 🚀 Servidor escuchando en 0.0.0.0:5000
# 📊 Esperando conexiones de clientes...
```

#### Terminal 2 - Bridge Flask (API REST)

```bash
cd c:\Users\StefanoIG\PycharmProjects\ExamenDistribuidos

python socket_bridge.py

# Esperado:
# 🚀 Iniciando bridge en port 5001
# 🔗 Conectando a socket server en localhost:5000
```

#### Terminal 3 - Frontend Next.js

```bash
cd Frontend

# Con pnpm
pnpm dev

# O con npm
npm run dev

# Esperado:
# ▲ Next.js 14.0.0
# - Local: http://localhost:3000
```

Abre http://localhost:3000 en tu navegador.

### Opción 2: Cliente Socket (Línea de comandos)

Para probar el servidor sin frontend:

```bash
# Modo interactivo
python socket_client.py

# Modo pruebas automáticas
python socket_client.py --test
```

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTE WEB                          │
│                   (React/Next.js)                           │
│                  http://localhost:3000                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/JSON
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               BRIDGE FLASK (API REST)                       │
│                  http://localhost:5001                      │
│        Traduce peticiones HTTP → Comandos Socket            │
└────────────────────────┬────────────────────────────────────┘
                         │ Socket TCP/IP
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            SERVIDOR SOCKET (Multi-threading)                │
│                 localhost:5000                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  • Escucha múltiples clientes                       │  │
│  │  • Un hilo por cliente                              │  │
│  │  • Locks por cédula (sincronización)                │  │
│  │  • Logging detallado                                │  │
│  │  • Estadísticas en tiempo real                      │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ MySQL Driver
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   BASE DE DATOS MySQL                       │
│                    Nombre: examen                           │
│                                                             │
│  ┌──────────────────────┐   ┌──────────────────────┐       │
│  │  Tabla: clientes     │   │ Tabla: transacciones │       │
│  │  ├─ cedula (PK)      │   │ ├─ id (PK)           │       │
│  │  ├─ nombres          │   │ ├─ cedula (FK)       │       │
│  │  ├─ apellidos        │   │ ├─ tipo              │       │
│  │  ├─ saldo            │   │ ├─ monto             │       │
│  │  └─ fecha_registro   │   │ ├─ saldo_final       │       │
│  │                      │   │ └─ fecha             │       │
│  └──────────────────────┘   └──────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 💬 Comandos Disponibles

### 1. CONSULTA

Obtiene información de un cliente

```
CONSULTA 1315151515
```

**Respuesta exitosa:**
```
OK|Juan|Pérez García|1500.00
```

### 2. AUMENTAR

Realiza un depósito (suma saldo)

```
AUMENTAR 1315151515 500
```

**Respuesta exitosa:**
```
OK|Depósito exitoso|2000.00
```

### 3. DISMINUIR

Realiza un retiro (resta saldo)

```
DISMINUIR 1315151515 200
```

**Respuesta exitosa:**
```
OK|Retiro exitoso|1800.00
```

**Si saldo insuficiente:**
```
ERROR|Saldo insuficiente|1800.00
```

### 4. CREAR

Crea un nuevo cliente

```
CREAR 1234567890 Carlos López 1000.00
```

**Respuesta exitosa:**
```
OK|Cliente creado exitosamente|1000.00
```

### 5. HISTORIAL

Obtiene las últimas 10 transacciones

```
HISTORIAL 1315151515
```

**Respuesta exitosa:**
```
OK|DEPOSITO|500.00|2000.00|2025-11-10 14:32:45|RETIRO|200.00|1800.00|2025-11-10 14:33:12|...
```

### 6. STATS

Obtiene estadísticas del servidor

```
STATS
```

**Respuesta exitosa:**
```
OK|Clientes conectados: 5|Transacciones: 42|IPs activas: 3
```

### 7. SALIR

Cierra la conexión

```
SALIR
```

---

## 🧠 Características Pro

### ✅ Threading Avanzado
- **Múltiples clientes concurrentes** - Cada cliente en su propio hilo
- **Event loop no bloqueante** - El servidor sigue aceptando conexiones mientras procesa

### 🔒 Sincronización de Datos
- **Locks por cédula** - Evita race conditions cuando dos clientes modifican el mismo saldo
- **Thread-safe operations** - Operaciones atómicas en la base de datos

### 📝 Logging Profesional
- **Logs a archivo** (`server.log`, `bridge.log`)
- **Timestamp detallado** - `[2025-11-10 14:32:10]`
- **Niveles de severidad** - INFO, WARNING, ERROR
- **Emojis para claridad** - ✅ ❌ 📥 📤 🔒 🔓

### 💾 Historial de Transacciones
- **Tabla dedicada** - `transacciones` con FK a `clientes`
- **Auditoría completa** - Cada operación registrada con timestamp
- **Índices optimizados** - Queries rápidas incluso con millones de registros

### 🌐 Microservicio Puente
- **API REST con Flask** - Interfaz HTTP estándar
- **CORS habilitado** - Accesible desde cualquier origen
- **JSON responses** - Integración moderna con frontend

### 📊 Pool de Conexiones
- **ThreadedConnectionPool** - Reutiliza conexiones MySQL
- **Autocommit controlado** - Transacciones explícitas
- **Connection timeout** - Libera recursos automáticamente

### 🎨 Frontend Moderno
- **Next.js 14** con App Router
- **React Hooks** - Estado reactivo
- **UI Components profesionales** - Shadcn/ui
- **TypeScript** - Type-safe frontend

---

## 📊 Ejemplo de flujo completo

### 1. Usuario inicia sesión con cédula

```
Frontend: Usuario ingresa "1315151515"
  ↓
  POST /api/consulta
    ↓
    Bridge Flask traduce a: CONSULTA 1315151515
      ↓
      Socket Server busca en BD
        ↓
        MySQL retorna: {nombres: "Juan", apellidos: "Pérez", saldo: 1500}
      ↓
    Bridge devuelve JSON
  ↓
Frontend muestra: "Bienvenido Juan Pérez - Saldo: $1500.00"
```

### 2. Usuario realiza un depósito

```
Frontend: Usuario ingresa monto $500
  ↓
  POST /api/deposito {cedula: "1315151515", monto: 500}
    ↓
    Bridge Flask → AUMENTAR 1315151515 500
      ↓
      Socket Server obtiene LOCK para cédula
        ↓
        Consulta saldo actual: $1500
        Suma: $1500 + $500 = $2000
        Actualiza en BD
        Registra transacción (tipo: DEPOSITO, monto: 500, saldo_final: 2000)
        Libera LOCK
      ↓
      Respuesta: OK|Depósito exitoso|2000.00
  ↓
Frontend muestra: "Depósito exitoso - Nuevo saldo: $2000.00"
```

---

## 🔧 Solución de problemas

### Error: "Connection refused"

**Causa:** El servidor socket no está corriendo

**Solución:**
```bash
python socket_server.py
```

### Error: "No module named 'mysql'"

**Causa:** Dependencias no instaladas

**Solución:**
```bash
pip install -r requirements.txt
```

### Error: "Database 'examen' does not exist"

**Causa:** Base de datos no creada

**Solución:**
```bash
python db_setup.py
```

### Error: "Port 5000 already in use"

**Causa:** Otro proceso ocupa el puerto

**Solución:**
```bash
# En PowerShell
lsof -i :5000  # Ver qué usa el puerto
kill -9 <PID>  # Terminar el proceso

# O cambiar el puerto en .env
```

---

## 📈 Mejoras futuras

- [ ] Autenticación JWT
- [ ] Validación de entrada más robusta
- [ ] Rate limiting por cliente
- [ ] Notificaciones en tiempo real (WebSocket)
- [ ] Reportes de transacciones (PDF)
- [ ] Dashboard de administrador
- [ ] Encriptación de contraseñas
- [ ] Backup automático de BD

---

## 👨‍💼 Estructura de commits (Git)

```
✨ feat: Agregar servidor socket con multi-threading
🐛 fix: Corregir race condition en actualización de saldo
📝 docs: Agregar documentación de arquitectura
🔧 chore: Actualizar dependencias
🧪 test: Agregar pruebas unitarias
```

---

## 📜 Licencia

Proyecto educativo para examen de Sistemas Distribuidos 2025

---

## ✉️ Contacto

Para preguntas o problemas, contacta a: **Stefano IG**

**Última actualización:** Noviembre 10, 2025
