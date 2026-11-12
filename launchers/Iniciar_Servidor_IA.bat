@echo off
chcp 65001 >nul
title Servidor IA Local [LM Studio + Open WebUI]
color 0A

echo ================================================================
echo       INICIANDO ECOSISTEMA DE IA LOCAL PARA ACCESO REMOTO
echo ================================================================
echo.

:: 1. Asegurar que el servidor local de LM Studio esta activo
echo [1/3] Verificando servidor de inferencia LM Studio en :1234...
"C:\Users\darck\.lmstudio\bin\lms.exe" server start >nul 2>&1

:: 2. Mostrar el estado del modelo cargado por el usuario
echo.
echo [2/3] Estado actual de tus modelos en LM Studio:
echo ----------------------------------------------------------------
"C:\Users\darck\.lmstudio\bin\lms.exe" status
echo ----------------------------------------------------------------
echo * NOTA: Open WebUI usara automaticamente el modelo que tengas
echo   cargado en LM Studio. Puedes cambiar de modelo en LM Studio
echo   en cualquier momento y se sincronizara dinamicamente.
echo.

:: 3. Limpieza preventiva del puerto 8080 si quedo una instancia previa abierta
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do (
    echo [!] Liberando puerto 8080 ocupado por instancia previa (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 1 >nul
)

:: 4. Variables de entorno de Open WebUI (Sin pantalla de login)
echo [3/3] Iniciando interfaz web Open WebUI en :8080...
set OPENAI_API_BASE_URL=http://127.0.0.1:1234/v1
set OPENAI_API_BASE_URLS=http://127.0.0.1:1234/v1
set OPENAI_API_KEY=lm-studio
set OPENAI_API_KEYS=lm-studio
set ENABLE_OLLAMA_API=False
set WEBUI_AUTH=False
set WEBUI_SECRET_KEY=gravity_mythos_secret_8700g
set WEBUI_HOST=0.0.0.0
set PORT=8080

echo.
echo ================================================================
echo  TODO LISTO! Abre cualquiera de estos enlaces en tu navegador:
echo.
echo  - En esta PC:
echo    http://localhost:8080
echo.
echo  - Desde tu movil o tablet (Misma red Wi-Fi de tu casa):
echo    http://192.168.1.115:8080
echo.
echo  - Desde cualquier lugar del mundo (Via Tailscale):
echo    http://100.81.210.121:8080
echo ================================================================
echo.

"C:\Users\darck\AppData\Local\Programs\Python\Python311\Scripts\open-webui.exe" serve
pause
