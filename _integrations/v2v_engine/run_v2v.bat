@echo off
set ENGINE_DIR=%~dp0
cd /d "%ENGINE_DIR%"

if not exist "env\Scripts\activate.bat" (
    echo [ERROR] El entorno virtual no existe. Ejecuta setup_v2v_env.bat primero.
    pause
    exit /b
)

echo Activando entorno aislado DirectML...
call env\Scripts\activate.bat

echo Iniciando Servidor V2V (FastAPI + WebSockets) en puerto 7861...
python v2v_server.py
pause
