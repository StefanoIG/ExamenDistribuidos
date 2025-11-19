# Script de inicio para Backend Windows - Sistema Bancario
# Uso: 
#   .\start-backend.ps1           # Setup completo + inicio
#   .\start-backend.ps1 -RunOnly  # Solo inicio (sin setup)

param(
    [switch]$RunOnly
)

$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "🏦 Sistema Bancario - Backend" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if ($RunOnly) {
    Write-Host "⚡ Modo rápido: Solo inicio (sin setup)" -ForegroundColor Yellow
    Write-Host ""
}

# ========================================
# FASE 1: SETUP (solo si no es -RunOnly)
# ========================================

if (-not $RunOnly) {
    Write-Host "📦 Fase 1: Configuración e instalación" -ForegroundColor Blue
    Write-Host ""

    # 1. Verificar Python
    Write-Host "🐍 Verificando Python..." -ForegroundColor Yellow
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✅ $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python no está instalado" -ForegroundColor Red
        Write-Host "   Descarga desde: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
    Write-Host ""

    # 2. Crear entorno virtual si no existe
    if (-not (Test-Path "venv")) {
        Write-Host "📦 Creando entorno virtual..." -ForegroundColor Yellow
        python -m venv venv
        Write-Host "✅ Entorno virtual creado" -ForegroundColor Green
    } else {
        Write-Host "✅ Entorno virtual ya existe" -ForegroundColor Green
    }
    Write-Host ""

    # 3. Activar entorno virtual
    Write-Host "🔄 Activando entorno virtual..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "✅ Entorno virtual activado" -ForegroundColor Green
    Write-Host ""

    # 4. Actualizar pip
    Write-Host "📥 Actualizando pip..." -ForegroundColor Yellow
    python -m pip install --upgrade pip -q
    Write-Host "✅ pip actualizado" -ForegroundColor Green
    Write-Host ""

    # 5. Instalar dependencias
    Write-Host "📚 Instalando dependencias desde requirements.txt..." -ForegroundColor Yellow
    pip install -r requirements.txt -q
    Write-Host "✅ Dependencias instaladas" -ForegroundColor Green
    Write-Host ""

    # 6. Verificar archivo .env
    Write-Host "⚙️  Verificando configuración (.env)..." -ForegroundColor Yellow
    if (-not (Test-Path ".env")) {
        Write-Host "⚠️  Archivo .env no encontrado, creando desde .env.example..." -ForegroundColor Yellow
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Host "✅ Archivo .env creado" -ForegroundColor Green
            Write-Host "⚠️  IMPORTANTE: Edita .env con tus credenciales de base de datos" -ForegroundColor Red
        } else {
            Write-Host "❌ No existe .env.example" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✅ Archivo .env existe" -ForegroundColor Green
    }
    Write-Host ""

    # 7. Verificar Docker
    Write-Host "🐳 Verificando Docker..." -ForegroundColor Yellow
    try {
        docker --version | Out-Null
        Write-Host "✅ Docker instalado" -ForegroundColor Green
        
        try {
            docker-compose --version | Out-Null
            Write-Host "✅ Docker Compose disponible" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Docker Compose no encontrado" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Docker no instalado (MySQL y MQTT deben estar corriendo externamente)" -ForegroundColor Yellow
    }
    Write-Host ""

    # 8. Inicializar base de datos
    Write-Host "🗄️  Inicializando base de datos..." -ForegroundColor Yellow
    try {
        python db_setup.py
        Write-Host "✅ Base de datos inicializada" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error inicializando base de datos" -ForegroundColor Red
        Write-Host "   Verifica que MySQL esté corriendo y las credenciales en .env sean correctas" -ForegroundColor Yellow
        exit 1
    }
    Write-Host ""

    Write-Host "✅ Setup completado exitosamente" -ForegroundColor Green
    Write-Host ""

} else {
    # Modo -RunOnly: solo activar venv
    & ".\venv\Scripts\Activate.ps1"
}

# ========================================
# FASE 2: INICIAR SERVICIOS
# ========================================

Write-Host "🚀 Fase 2: Iniciando servicios del backend" -ForegroundColor Blue
Write-Host ""

# Función para verificar si un puerto está en uso
function Test-Port {
    param($Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
    return $connection
}

# Función para matar proceso en un puerto
function Stop-PortProcess {
    param($Port)
    $process = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($process) {
        Write-Host "⚠️  Puerto $Port en uso (PID: $process), deteniendo..." -ForegroundColor Yellow
        Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

# Limpiar puertos si están ocupados
Write-Host "🧹 Limpiando puertos previos..." -ForegroundColor Yellow
Stop-PortProcess -Port 5000  # Socket Server
Stop-PortProcess -Port 5001  # Flask Bridge
Write-Host "✅ Puertos liberados" -ForegroundColor Green
Write-Host ""

# Leer variables del .env
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

$DB_PORT = $env:DB_PORT ?? 3306
$MQTT_PORT = $env:MQTT_BROKER_PORT ?? 1883
$SERVER_PORT = $env:SERVER_PORT ?? 5000
$BRIDGE_PORT = $env:BRIDGE_PORT ?? 5001

# 1. Verificar/Iniciar MySQL
Write-Host "🗄️  Verificando MySQL..." -ForegroundColor Yellow
if (Test-Port -Port $DB_PORT) {
    Write-Host "✅ MySQL corriendo en puerto $DB_PORT" -ForegroundColor Green
} else {
    Write-Host "⚠️  MySQL no detectado en puerto $DB_PORT" -ForegroundColor Yellow
    Write-Host "   Intentando iniciar con Docker..." -ForegroundColor Yellow
    
    try {
        docker-compose up -d mysql 2>$null
        Write-Host "   Esperando a que MySQL esté listo..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    } catch {
        Write-Host "❌ Error iniciando MySQL. Inicia MySQL manualmente" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# 2. Verificar/Iniciar MQTT Broker
Write-Host "📡 Verificando MQTT Broker..." -ForegroundColor Yellow
if (Test-Port -Port $MQTT_PORT) {
    Write-Host "✅ MQTT Broker corriendo en puerto $MQTT_PORT" -ForegroundColor Green
} else {
    Write-Host "⚠️  MQTT Broker no detectado en puerto $MQTT_PORT" -ForegroundColor Yellow
    Write-Host "   Intentando iniciar Mosquitto con Docker..." -ForegroundColor Yellow
    
    try {
        docker-compose up -d mosquitto 2>$null
        Write-Host "   Esperando a que MQTT esté listo..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    } catch {
        Write-Host "⚠️  Docker no disponible. MQTT opcional, continuando..." -ForegroundColor Yellow
    }
}
Write-Host ""

# Crear directorio de logs si no existe
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# 3. Iniciar Socket Server en nueva ventana
Write-Host "🔌 Iniciando Socket Server (puerto $SERVER_PORT)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python socket_server.py | Tee-Object -FilePath logs\socket_server.log"
Start-Sleep -Seconds 2

if (Test-Port -Port $SERVER_PORT) {
    Write-Host "✅ Socket Server iniciado" -ForegroundColor Green
} else {
    Write-Host "❌ Error iniciando Socket Server" -ForegroundColor Red
    Write-Host "   Ver logs\socket_server.log para detalles" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 4. Iniciar Flask Bridge en nueva ventana
Write-Host "🌉 Iniciando Flask Bridge (puerto $BRIDGE_PORT)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python socket_bridge.py | Tee-Object -FilePath logs\bridge.log"
Start-Sleep -Seconds 2

if (Test-Port -Port $BRIDGE_PORT) {
    Write-Host "✅ Flask Bridge iniciado" -ForegroundColor Green
} else {
    Write-Host "❌ Error iniciando Flask Bridge" -ForegroundColor Red
    Write-Host "   Ver logs\bridge.log para detalles" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# ========================================
# RESUMEN
# ========================================

Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ Backend iniciado correctamente" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Servicios corriendo:" -ForegroundColor Blue
Write-Host "   • MySQL:         localhost:$DB_PORT" -ForegroundColor White
Write-Host "   • MQTT Broker:   localhost:$MQTT_PORT" -ForegroundColor White
Write-Host "   • Socket Server: localhost:$SERVER_PORT" -ForegroundColor White
Write-Host "   • Flask Bridge:  localhost:$BRIDGE_PORT" -ForegroundColor White
Write-Host ""
Write-Host "📊 Logs:" -ForegroundColor Blue
Write-Host "   • Socket Server: logs\socket_server.log" -ForegroundColor Cyan
Write-Host "   • Flask Bridge:  logs\bridge.log" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 Comandos útiles:" -ForegroundColor Yellow
Write-Host "   • Ver logs Socket:  Get-Content logs\socket_server.log -Wait" -ForegroundColor Gray
Write-Host "   • Ver logs Bridge:  Get-Content logs\bridge.log -Wait" -ForegroundColor Gray
Write-Host "   • Monitor MQTT:     python mqtt_subscriber.py" -ForegroundColor Gray
Write-Host "   • Detener backend:  taskkill /F /IM python.exe" -ForegroundColor Gray
Write-Host ""
Write-Host "🛑 Para detener: Cierra las ventanas de PowerShell o ejecuta:" -ForegroundColor Red
Write-Host "   taskkill /F /IM python.exe" -ForegroundColor Red
Write-Host ""
