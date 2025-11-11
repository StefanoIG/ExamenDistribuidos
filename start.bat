@echo off
REM Script para iniciar todos los servicios del Sistema Bancario Distribuido
REM Para Windows PowerShell

echo.
echo ==========================================
echo    Sistema Bancario Distribuido
echo    Iniciador de Servicios
echo ==========================================
echo.

REM Obtener la ruta del directorio actual
set ROOT_DIR=%~dp0

echo [1/3] Iniciando Servidor Socket (Puerto 5000)...
cd /d "%ROOT_DIR%"
start /B python socket_server.py

timeout /t 2 /nobreak

echo [2/3] Iniciando Bridge Flask (Puerto 5001)...
start /B python socket_bridge.py

timeout /t 2 /nobreak

echo [3/3] Iniciando Frontend Next.js (Puerto 3000)...
cd /d "%ROOT_DIR%Frontend"
start /B pnpm dev

echo.
echo ==========================================
echo    ✅ TODOS LOS SERVICIOS INICIADOS
echo ==========================================
echo.
echo Accesos:
echo   • Frontend:       http://localhost:3000
echo   • API (Bridge):   http://localhost:5001/api
echo   • Socket Server:  localhost:5000
echo.
echo Para detener: Cierra las ventanas de terminal o presiona Ctrl+C
echo ==========================================
echo.

pause
