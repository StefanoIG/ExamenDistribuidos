# Script de inicio completo - Sistema Bancario con MQTT
# Uso: .\start-mqtt.ps1

param(
    [switch]$ConMQTT,
    [switch]$SoloMQTT,
    [switch]$Monitor
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "🏦 Sistema Bancario Distribuido" -ForegroundColor Green
Write-Host "   Con soporte MQTT" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Matar procesos previos
Write-Host "🧹 Limpiando procesos previos..." -ForegroundColor Yellow
taskkill /F /IM python.exe 2>$null
taskkill /F /IM node.exe 2>$null
Start-Sleep -Seconds 2

if ($SoloMQTT) {
    Write-Host "📡 Iniciando solo broker MQTT..." -ForegroundColor Green
    docker-compose up mosquitto
    exit
}

if ($Monitor) {
    Write-Host "👂 Iniciando monitor MQTT..." -ForegroundColor Green
    Write-Host "Presiona Ctrl+C para salir" -ForegroundColor Yellow
    Write-Host ""
    python mqtt_subscriber.py
    exit
}

# Iniciar MQTT Broker con Docker
if ($ConMQTT) {
    Write-Host "📡 Iniciando MQTT Broker (Mosquitto)..." -ForegroundColor Green
    Write-Host "   Si no tienes Docker, el sistema funcionara sin MQTT" -ForegroundColor Yellow
    try {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "docker-compose up mosquitto"
        Start-Sleep -Seconds 5
        Write-Host "✅ MQTT Broker iniciado" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  No se pudo iniciar MQTT (Docker no disponible)" -ForegroundColor Yellow
        Write-Host "   El sistema funcionara sin MQTT" -ForegroundColor Yellow
    }
}

# Activar entorno virtual Python
Write-Host "🐍 Activando entorno virtual..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Iniciar Base de Datos
Write-Host "🗄️  Iniciando MySQL..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "docker-compose up mysql"
Start-Sleep -Seconds 5

# Iniciar Socket Server
Write-Host "🔌 Iniciando Socket Server (Puerto 5000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python socket_server.py"
Start-Sleep -Seconds 3

# Iniciar Flask Bridge
Write-Host "🌉 Iniciando Flask Bridge (Puerto 5001)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python socket_bridge.py"
Start-Sleep -Seconds 3

# Iniciar Frontend
Write-Host "⚛️  Iniciando Frontend (Puerto 3000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\Frontend'; npm run dev"
Start-Sleep -Seconds 3

# Iniciar Monitor MQTT
if ($ConMQTT) {
    Write-Host "👂 Iniciando Monitor MQTT..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python mqtt_subscriber.py"
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✅ Sistema iniciado correctamente" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Servicios disponibles:" -ForegroundColor Cyan
Write-Host "   - Socket Server:   localhost:5000" -ForegroundColor White
Write-Host "   - Flask Bridge:    localhost:5001" -ForegroundColor White
Write-Host "   - Frontend:        http://localhost:3000" -ForegroundColor White
if ($ConMQTT) {
    Write-Host "   - MQTT Broker:     localhost:1883" -ForegroundColor White
    Write-Host "   - MQTT WebSocket:  localhost:9001" -ForegroundColor White
    Write-Host "   - Monitor MQTT:    Ventana separada" -ForegroundColor White
}
Write-Host ""
Write-Host "📚 Comandos utiles:" -ForegroundColor Yellow
Write-Host "   .\start-mqtt.ps1 -ConMQTT     # Iniciar con MQTT" -ForegroundColor Gray
Write-Host "   .\start-mqtt.ps1 -SoloMQTT     # Solo broker MQTT" -ForegroundColor Gray
Write-Host "   .\start-mqtt.ps1 -Monitor      # Solo monitor MQTT" -ForegroundColor Gray
Write-Host ""
Write-Host "🛑 Para detener: Cerrar todas las ventanas de PowerShell" -ForegroundColor Red
Write-Host ""