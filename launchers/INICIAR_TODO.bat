@echo off
chcp 65001 >nul
title Gravity AI Bridge V16.7 PRO -- Arranque Completo
setlocal enabledelayedexpansion
color 0B
cls

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI BRIDGE V16.7 PRO [Vision-Tier]                      ^|
echo  ^|          J.A.R.V.I.S Sensory Net ^& Motor MAI L0/1/2 habilitados         ^|
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

REM ── Configurar PYTHONPATH para que los módulos 'core' se encuentren ───────
set "PYTHONPATH=%ROOT%"


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
REM ── 1.5. Iniciar FastFlowLM (NPU Server) si está instalado ───────────────
echo.
echo  [NPU] Verificando FastFlowLM (Motor NPU Hawk Point)...
set _FLM_ACTIVE=0
where flm >nul 2>&1
if errorlevel 1 (
    echo  [SKIP] FastFlowLM no instalado o no esta en el PATH.
    goto :after_flm
)

REM Si llegamos aqui, FLM esta instalado. Verificamos RAM.
set _FREE_MB=0
for /f %%a in ('python -c "import psutil; print(int(psutil.virtual_memory().available / (1024*1024)))" 2^>nul') do set _FREE_MB=%%a

if !_FREE_MB! lss 6000 (
    echo  [WARN] RAM libre insuficiente ^(!_FREE_MB! MB^) para la compilacion NPU.
    echo  [WARN] FLM requiere al menos 6GB libres. Cierra LM Studio o apps pesadas y reintenta.
    echo  [INFO] FastFlowLM NO iniciado para evitar colapso del sistema.
    goto :after_flm
)

echo  [OK] RAM libre: !_FREE_MB! MB. Iniciando servidor NPU en puerto 52625...
start "Gravity :: FastFlowLM Server (NPU)" cmd /k "flm serve llama3.2:1b --ctx-len 4096 --port 52625"

REM Esperar hasta 30s a que el puerto 52625 responda
set _FLM_RETRIES=0
:wait_flm
netstat -ano | findstr ":52625 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    set _FLM_ACTIVE=1
    echo  [OK] FastFlowLM activo en puerto 52625. La NPU esta en uso.
    goto :after_flm
)

set /a _FLM_RETRIES+=1
if !_FLM_RETRIES! lss 30 (
    ping 127.0.0.1 -n 2 > nul
    goto wait_flm
)

echo  [WARN] FastFlowLM no respondio en 30s ^(normal la 1era vez, puede tardar 5-10 min cargando^).
echo  [INFO] El modelo NPU sigue cargando en segundo plano. El sistema lo usara cuando este listo.

:after_flm

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
    start "Gravity AI Bridge Server" cmd /k cd /d "%ROOT%" ^&^& python bridge_server.py
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


REM ── 4. Fooocus Studio UI (7862) — INICIO MANUAL para ahorrar RAM ───────────────────────────
:after_fooocus
echo.
echo  [4/4] Fooocus Studio UI configurado en modo MANUAL (ahorra RAM).
echo  [INFO] Inicialo desde el Dashboard Web cuando necesites generar imagenes.
REM NOTA: Para activar el arranque automatico descomenta la linea siguiente:
REM start "Gravity :: Fooocus Studio UI" cmd /k cd /d "%ROOT%" ^&^& python tools\fooocus_studio_ui.py

echo.
echo  [INFO] Los modulos autonomos (Periodista, Radar, J.A.R.V.I.S) 
echo  [INFO] han sido configurados para inicio MANUAL via Dashboard Web.
echo  [INFO] Esto ahorra recursos y evita multiples consolas.

:launch_done
echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI BRIDGE V16.7 PRO — Vision-Tier Ecosistema           ^|
echo  +--------------------------------------------------------------------------+
echo  ^|   Dashboard Web:    http://localhost:7860  (Chat, V2V, Video Studio)    ^|
echo  ^|   Fooocus Motor:    http://127.0.0.1:7861  (API generacion imagenes)    ^|
echo  ^|   Fooocus Studio:   http://127.0.0.1:7862  (UI de generacion)           ^|
echo  ^|   V2V WebSocket:    ws://127.0.0.1:7863    (Motor en vivo)              ^|
echo  ^|   Periodista:       [MANUAL] Iniciar desde el Dashboard Web             ^|
echo  ^|   Radar HF:         [MANUAL] Iniciar desde el Dashboard Web             ^|
echo  ^|   J.A.R.V.I.S:      [MANUAL] Iniciar desde el Dashboard Web             ^|
echo  ^|   FastFlowLM NPU:   http://localhost:52625 (Opcional, Backend de IA)    ^|
echo  ^|                                                                         ^|
echo  ^|   [!] V2V Engine y Modulos Autonomos inician desde el Dashboard Web     ^|
echo  ^|   [!] Fooocus CPU tarda ~60-120s en cargar. Imagen: 3-8 min             ^|
echo  ^|   [!] Todo corre en segundo plano de manera limpia sin tantas consolas  ^|
echo  ^|                                                                         ^|
echo  +--------------------------------------------------------------------------+
echo.
if "!_BRIDGE_OK!"=="1" (
    echo  Esperando a que el Dashboard responda...
    goto wait_dashboard
) else (
    echo  [!] Dashboard no se abrira porque el servicio GravityAI esta detenido.
    goto launch_done_final
)

:wait_dashboard
netstat -ano | findstr ":7860 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    ping 127.0.0.1 -n 2 > nul
    goto wait_dashboard
)
echo  Abriendo el Dashboard principal en tu navegador...
start http://127.0.0.1:7860/

:launch_done_final
echo.
echo  [LISTO] Ecosistema Gravity AI V16.7 PRO (J.A.R.V.I.S) iniciado. Esta ventana puede cerrarse.
pause
