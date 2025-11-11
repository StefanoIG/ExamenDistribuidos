# Script para iniciar el Sistema Bancario Distribuido
# Uso: .\start.ps1 -Todos

param(
    [switch]$Servidor = $false,
    [switch]$Bridge = $false,
    [switch]$Frontend = $false,
    [switch]$Todos = $false,
    [switch]$Cliente = $false,
    [switch]$Setup = $false
)

# Configuración
$ROOT_DIR = Get-Location

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  Sistema Bancario Distribuido" -ForegroundColor Cyan
Write-Host "  Iniciador de Servicios" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Si no se especifica nada, mostrar ayuda
if (-not ($Servidor -or $Bridge -or $Frontend -or $Todos -or $Cliente -or $Setup)) {
    Write-Host "Uso:" -ForegroundColor Yellow
    Write-Host "  .\start.ps1 -Todos              # Inicia todos los servicios" -ForegroundColor White
    Write-Host "  .\start.ps1 -Servidor           # Solo servidor socket" -ForegroundColor White
    Write-Host "  .\start.ps1 -Bridge             # Solo bridge Flask" -ForegroundColor White
    Write-Host "  .\start.ps1 -Frontend           # Solo frontend Next.js" -ForegroundColor White
    Write-Host "  .\start.ps1 -Cliente            # Cliente socket interactivo" -ForegroundColor White
    Write-Host "  .\start.ps1 -Setup              # Setup de base de datos" -ForegroundColor White
    Write-Host ""
    exit
}

# Función para ejecutar en nueva ventana
function Start-Service {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDir = $ROOT_DIR
    )
    
    Write-Host "Iniciando: $Title..." -ForegroundColor Green
    
    # Convertir a ruta absoluta
    $AbsoluteDir = if ([System.IO.Path]::IsPathRooted($WorkingDir)) {
        $WorkingDir
    } else {
        Join-Path $ROOT_DIR $WorkingDir
    }
    
    # Crear comando con ruta absoluta
    $FullCommand = "Set-Location '$AbsoluteDir'; $Command"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $FullCommand -WindowStyle Normal
    Start-Sleep -Seconds 1
}

# Setup de Base de Datos
if ($Setup) {
    Write-Host "Configurando Base de Datos..." -ForegroundColor Yellow
    Set-Location $ROOT_DIR
    & python db_setup.py
    Write-Host "Setup completado" -ForegroundColor Green
    exit
}

# Cliente Socket
if ($Cliente) {
    Write-Host "Iniciando Cliente Socket..." -ForegroundColor Yellow
    Set-Location $ROOT_DIR
    & python socket_client.py
    exit
}

# Para -Todos, hacer setup automático primero
if ($Todos) {
    Write-Host "Configurando Base de Datos..." -ForegroundColor Yellow
    Set-Location $ROOT_DIR
    & python db_setup.py
    Write-Host "Base de datos lista" -ForegroundColor Green
    Write-Host ""
    Start-Sleep -Seconds 2
}

# Iniciar servicios individuales
if ($Servidor -or $Todos) {
    Start-Service -Title "Servidor Socket (Puerto 5000)" `
                  -Command "python socket_server.py" `
                  -WorkingDir $ROOT_DIR
}

if ($Bridge -or $Todos) {
    Start-Service -Title "Bridge Flask (Puerto 5001)" `
                  -Command "python socket_bridge.py" `
                  -WorkingDir $ROOT_DIR
}

if ($Frontend -or $Todos) {
    $FrontendDir = Join-Path $ROOT_DIR "Frontend"
    $Cmd = "npm install --legacy-peer-deps; npm run dev"
    
    Start-Service -Title "Frontend Next.js (Puerto 3000)" `
                  -Command $Cmd `
                  -WorkingDir $FrontendDir
}

if ($Todos) {
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host "  TODOS LOS SERVICIOS INICIADOS" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Accesos:" -ForegroundColor Cyan
    Write-Host "  Frontend:       http://localhost:3000" -ForegroundColor White
    Write-Host "  API (Bridge):   http://localhost:5001/api" -ForegroundColor White
    Write-Host "  Socket Server:  localhost:5000" -ForegroundColor White
    Write-Host ""
    Write-Host "Para detener: Cierra las ventanas de terminal" -ForegroundColor Yellow
    Write-Host "===========================================" -ForegroundColor Green
}
