@echo off
chcp 65001 >nul
title Gravity AI Bridge V16.0 PRO -- Arranque Completo
setlocal enabledelayedexpansion
color 0B
cls

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI BRIDGE V16.0 PRO [Ecosistema Total]                 ^|
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

REM ── 1. Liberar puertos secundarios previos (7861, 7862, 7863) ──────────────
echo  [1/4] Omitiendo liberación de puertos para no cerrar al agente local...
REM for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":7861 " ^| findstr LISTENING') do ( taskkill /F /PID %%p >nul 2>&1 )
REM for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":7862 " ^| findstr LISTENING') do ( taskkill /F /PID %%p >nul 2>&1 )
REM for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":7863 " ^| findstr LISTENING') do ( taskkill /F /PID %%p >nul 2>&1 )
REM set _PORT_RETRIES=0
REM :wait_ports_free
REM set _PORTS_BUSY=0
REM netstat -ano | findstr ":7861 " | findstr LISTENING >nul 2>&1 && set _PORTS_BUSY=1
REM netstat -ano | findstr ":7862 " | findstr LISTENING >nul 2>&1 && set _PORTS_BUSY=1
REM netstat -ano | findstr ":7863 " | findstr LISTENING >nul 2>&1 && set _PORTS_BUSY=1
REM if "!_PORTS_BUSY!"=="1" (
REM     set /a _PORT_RETRIES+=1
REM     if !_PORT_RETRIES! lss 10 (
REM         timeout /t 1 /nobreak >nul
REM         goto wait_ports_free
REM     ) else (
REM         echo  [!] Advertencia: No se pudieron liberar todos los puertos secundarios.
REM     )
REM )
REM ── 2. Bridge Server (GravityAI) ──────────────────────────────────────────
echo.
echo  [2/4] Verificando nucleo de Gravity...
set _BRIDGE_OK=0
netstat -ano | findstr ":7860 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    set _BRIDGE_OK=1
    echo  [OK] GravityAI esta corriendo en segundo plano, Puerto 7860 activo.
) else (
    echo  [!] Gravity no esta respondiendo en el puerto 7860.
    echo  [+] Iniciando puente de Gravity AI automaticamente...
    start "Gravity AI Bridge Server" cmd /k "cd /d "%ROOT%" && python bridge_server.py"
    set _BRIDGE_OK=1
)

REM ── 3. Motor Fooocus CPU (7861) ───────────────────────────────────────────
echo.
echo  [3/4] Verificando Motor Fooocus CPU...
if not exist "%PYTHON_EMB%" (
    echo  [SKIP] Python embebido de Fooocus no encontrado: %PYTHON_EMB%
    echo  [INFO] Generacion de imagenes via Pollinations ^(fallback automatico activo^).
    goto :after_fooocus
)
if not exist "%FOOOCUS_SCRIPT%" (
    echo  [SKIP] entry_with_update.py no encontrado: %FOOOCUS_SCRIPT%
    echo  [INFO] Generacion via Pollinations activa.
    goto :after_fooocus
)

echo  [3/4] Motor Fooocus configurado en modo Manual.
echo  [INFO] Para ahorrar memoria RAM, inicia Fooocus desde el Dashboard (Mission Control) cuando lo necesites.


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

echo.
echo  [5/5] Despertando al Agente Periodistico Autonomo...
start "Gravity :: Agente Periodistico" cmd /k "cd /d "%ROOT%" && python news_daemon.py"
echo  [OK] Agente Periodistico iniciado en background.

:launch_done
echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI BRIDGE V16.0 PRO — Ecosistema Completo               ^|
echo  +--------------------------------------------------------------------------+
echo  ^|   Dashboard Web:    http://localhost:7860  (Chat, V2V, Video Studio)    ^|
echo  ^|   Fooocus Motor:    http://127.0.0.1:7861  (API generacion imagenes)    ^|
echo  ^|   Fooocus Studio:   http://127.0.0.1:7862  (UI de generacion)           ^|
echo  ^|   V2V WebSocket:    ws://127.0.0.1:7863    (Motor en vivo)              ^|
echo  ^|   Periodista:       Autonomo y en ejecucion silenciosa                  ^|
echo  ^|   MAI L2 ComfyUI:   http://localhost:8188  (si activo)                  ^|
echo  ^|                                                                          ^|
echo  ^|   [!] V2V Engine: inicia desde el panel V2V Live Studio                 ^|
echo  ^|   [!] Fooocus CPU tarda ~60-120s en cargar. Imagen: 3-8 min             ^|
echo  ^|   [!] NO cierres ventanas de motores mientras trabajas                  ^|
echo  ^|                                                                          ^|
echo  +--------------------------------------------------------------------------+
echo.
if "!_BRIDGE_OK!"=="1" (
    echo  Esperando a que el Dashboard responda...
    :wait_dashboard
    netstat -ano | findstr ":7860 " | findstr "LISTENING" >nul 2>&1
    if errorlevel 1 (
        timeout /t 1 /nobreak >nul
        goto wait_dashboard
    )
    echo  Abriendo el Dashboard principal en tu navegador...
    start http://127.0.0.1:7860/
) else (
    echo  [!] Dashboard no se abrira porque el servicio GravityAI esta detenido.
)
echo.
echo  [LISTO] Ecosistema Gravity AI V16.0 PRO iniciado. Esta ventana puede cerrarse.
pause
