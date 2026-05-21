@echo off
title Gravity AI Bridge V15.0 PRO -- Arranque Completo
setlocal enabledelayedexpansion
color 0B
cls

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI BRIDGE V15.0 PRO [Ecosistema Total]                 ^|
echo  ^|          Motor de Animacion (MAI) L0/L1/L2 habilitado                   ^|
echo  +--------------------------------------------------------------------------+
echo.

REM ── Rutas relativas al script (nunca hardcodeadas) ─────────────────────────────
set "ROOT=%~dp0.."
set "FOOOCUS_DIR=%ROOT%\_integrations\Fooocus"
set "PYTHON_EMB=%FOOOCUS_DIR%\python_embeded\python.exe"
set "FOOOCUS_SCRIPT=%FOOOCUS_DIR%\Fooocus\entry_with_update.py"
set "STUDIO_UI=%ROOT%\tools\fooocus_studio_ui.py"

REM ── Validar entorno base ────────────────────────────────────────────────────────
if not exist "%ROOT%\bridge_server.py" (
    echo  [!] ERROR: bridge_server.py no encontrado en: %ROOT%
    echo  [!] Verifica que este script este en la carpeta 'launchers' del proyecto.
    pause
    exit /b 1
)

REM ── 1. Liberar puertos previos (7860, 7861, 7862, 7863) ────────────────────
echo  [1/4] Liberando puertos previos (7860, 7861, 7862, 7863)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":7860 " ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":7861 " ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":7862 " ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":7863 " ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo  [OK] Puertos liberados.

REM ── 2. Bridge Server + Dashboard (7860) ───────────────────────────────────────
echo.
echo  [2/4] Iniciando Bridge Server (puerto 7860)...
start "Gravity :: Bridge Server" cmd /k "cd /d "%ROOT%" && python bridge_server.py"

REM Polling real del puerto 7860
echo  [INFO] Esperando a que el Bridge levante en :7860 (max 45s)...
set "_BRIDGE_OK=0"
for /L %%i in (1,1,45) do (
    if "!_BRIDGE_OK!"=="0" (
        netstat -ano | findstr ":7860 " | findstr "LISTENING" >nul 2>&1
        if not errorlevel 1 (
            set "_BRIDGE_OK=1"
            echo  [OK] Bridge Server listo en %%is.
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)
if "!_BRIDGE_OK!"=="0" (
    echo  [!] ADVERTENCIA: Bridge no respondio en 45s. Verifica Python y dependencias.
    echo  [!] Continuando de todas formas (puede tardar mas en hardware lento).
)

REM ── 3. Motor Fooocus CPU (7861) ────────────────────────────────────────────────
echo.
echo  [3/4] Verificando Motor Fooocus CPU...
if not exist "%PYTHON_EMB%" (
    echo  [SKIP] Python embebido de Fooocus no encontrado: %PYTHON_EMB%
    echo  [INFO] Generacion de imagenes via Pollinations (fallback automatico activo).
    goto :after_fooocus
)
if not exist "%FOOOCUS_SCRIPT%" (
    echo  [SKIP] entry_with_update.py no encontrado: %FOOOCUS_SCRIPT%
    echo  [INFO] Generacion via Pollinations activa.
    goto :after_fooocus
)

echo  [3/4] Iniciando Motor Fooocus CPU (puerto 7861)...
start "Gravity :: Motor [Fooocus CPU]" cmd /k "cd /d "%FOOOCUS_DIR%" && "%PYTHON_EMB%" -s Fooocus\entry_with_update.py --always-cpu --all-in-fp32 --disable-async-cuda-allocation --port 7861 --disable-in-browser --disable-analytics"
echo  [OK] Motor Fooocus iniciando en segundo plano...

REM Polling real de Fooocus (BUG: antes usaba timeout ciego de 20s)
echo  [INFO] Esperando a que Fooocus este listo en :7861 (max 120s)...
set "_FOOOCUS_OK=0"
for /L %%i in (1,1,120) do (
    if "!_FOOOCUS_OK!"=="0" (
        netstat -ano | findstr ":7861 " | findstr "LISTENING" >nul 2>&1
        if not errorlevel 1 (
            set "_FOOOCUS_OK=1"
            echo  [OK] Motor Fooocus listo en %%is.
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)
if "!_FOOOCUS_OK!"=="0" (
    echo  [!] ADVERTENCIA: Fooocus no respondio en 120s. Studio UI puede no funcionar.
)

REM ── 4. Fooocus Studio UI (7862) ────────────────────────────────────────────────
:after_fooocus
echo.
echo  [4/4] Iniciando Fooocus Studio UI (puerto 7862)...
if not exist "%STUDIO_UI%" (
    echo  [SKIP] tools\fooocus_studio_ui.py no encontrado. Studio UI omitido.
    goto :launch_done
)
start "Gravity :: Fooocus Studio UI" cmd /k "cd /d "%ROOT%" && python tools\fooocus_studio_ui.py"
echo  [OK] Studio UI iniciado.

:launch_done
echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI BRIDGE V15.0 PRO — Ecosistema Completo               ^|
echo  +--------------------------------------------------------------------------+
echo  ^|   Dashboard Web:    http://localhost:7860  (Chat, V2V, Video Studio)    ^|
echo  ^|   Fooocus Motor:    http://127.0.0.1:7861  (API generacion imagenes)    ^|
echo  ^|   Fooocus Studio:   http://127.0.0.1:7862  (UI de generacion)           ^|
echo  ^|   V2V WebSocket:    ws://127.0.0.1:7863    (Motor en vivo)              ^|
echo  ^|   MAI L2 ComfyUI:   http://localhost:8188  (si activo)                  ^|
echo  ^|                                                                          ^|
echo  ^|   [!] V2V Engine: inicia desde el panel V2V Live Studio                 ^|
echo  ^|   [!] Fooocus CPU tarda ~60-120s en cargar. Imagen: 3-8 min             ^|
echo  ^|   [!] NO cierres ventanas de motores mientras trabajas                  ^|
echo  ^|                                                                          ^|
echo  +--------------------------------------------------------------------------+
echo.
echo  Abriendo el Dashboard principal en tu navegador...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:7860/
echo.
echo  [LISTO] Ecosistema Gravity AI V15.0 PRO iniciado. Esta ventana puede cerrarse.
pause
