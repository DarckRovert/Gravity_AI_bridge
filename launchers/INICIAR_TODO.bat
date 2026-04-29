@echo off
title Gravity AI Bridge V12.1 PRO -- Arranque Completo
cd /d "F:\Gravity_AI_bridge"
color 0B
cls

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI BRIDGE V12.1 PRO [Ecosistema Total]                 ^|
echo  ^|          Arranque completo del ecosistema                                ^|
echo  +--------------------------------------------------------------------------+
echo.

REM ── Definir rutas absolutas ───────────────────────────────────────────────────
set "ROOT=F:\Gravity_AI_bridge"
set "FOOOCUS_DIR=%ROOT%\_integrations\Fooocus"
set "PYTHON_EMB=%FOOOCUS_DIR%\python_embeded\python.exe"
set "FOOOCUS_SCRIPT=%FOOOCUS_DIR%\Fooocus\entry_with_update.py"

REM ── 1. Matar procesos Python previos en los puertos del ecosistema ────────────
echo  [1/4] Liberando puertos previos (7860, 7861, 7862)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":7861 " ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":7860 " ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":7862 " ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo  [OK] Puertos liberados.

REM ── 2. Bridge Server + Dashboard (7860) ──────────────────────────────────────
echo.
echo  [2/4] Iniciando Bridge Server (puerto 7860)...
start "Gravity :: Bridge Server" cmd /k "cd /d "%ROOT%" && python bridge_server.py"
echo  [INFO] Esperando 4s para que el Bridge levante...
timeout /t 4 /nobreak >nul
echo  [OK] Bridge Server iniciado.

REM ── 3. Motor Fooocus CPU (7861) ───────────────────────────────────────────────
echo.
echo  [3/4] Verificando Motor Fooocus CPU...
if not exist "%PYTHON_EMB%" (
    echo  [!] ERROR: Python embebido de Fooocus no encontrado en:
    echo  [!]   %PYTHON_EMB%
    echo  [!] Generacion de imagenes via Fooocus no disponible.
    echo  [!] El sistema usara Pollinations como fallback automatico.
    goto :skip_fooocus
)
if not exist "%FOOOCUS_SCRIPT%" (
    echo  [!] ERROR: entry_with_update.py no encontrado en:
    echo  [!]   %FOOOCUS_SCRIPT%
    echo  [!] Generacion de imagenes via Fooocus no disponible.
    goto :skip_fooocus
)

echo  [3/4] Iniciando Motor Fooocus CPU (puerto 7861)...
start "Gravity :: Motor [Fooocus CPU]" cmd /k "cd /d "%FOOOCUS_DIR%" && "%PYTHON_EMB%" -s Fooocus\entry_with_update.py --always-cpu --all-in-fp32 --disable-async-cuda-allocation --port 7861 --disable-in-browser --disable-analytics"
echo  [OK] Motor Fooocus iniciando en segundo plano (tarda 60-90s)...
goto :after_fooocus

:skip_fooocus
echo  [SKIP] Fooocus omitido.

:after_fooocus

REM ── 4. Fooocus Studio UI Gradio (7862) ───────────────────────────────────────
echo.
echo  [4/4] Iniciando Fooocus Studio UI (puerto 7862)...
echo  [INFO] Esperando 20s para que el Motor Fooocus inicialice...
timeout /t 20 /nobreak >nul
start "Gravity :: Fooocus Studio UI" cmd /k "cd /d "%ROOT%" && python tools\fooocus_studio_ui.py"
echo  [OK] Studio UI iniciado.

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|                                                                          ^|
echo  ^|   Dashboard Web:    http://localhost:7860       (Chat, Status, Audit)    ^|
echo  ^|   Fooocus Motor:    http://127.0.0.1:7861      (API de generacion)      ^|
echo  ^|   Vision Studio:    http://127.0.0.1:7862      (UI de generacion)       ^|
echo  ^|                                                                          ^|
echo  ^|   [!] Fooocus CPU tarda ~60-90s en cargar. Imagen: 3-8 min              ^|
echo  ^|   [!] NO cierres la ventana del motor Fooocus mientras trabajas         ^|
echo  ^|   [!] Cada componente corre en su propia ventana CMD (cmd /k)           ^|
echo  ^|                                                                          ^|
echo  +--------------------------------------------------------------------------+
echo.
echo  Abriendo el Dashboard principal en tu navegador...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:7860/
echo.
echo  [LISTO] Ecosistema Gravity AI iniciado. Esta ventana puede cerrarse.
pause
