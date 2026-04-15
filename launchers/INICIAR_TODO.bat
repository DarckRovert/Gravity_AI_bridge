@echo off
title Gravity AI Bridge V9.3.1 PRO -- Arranque Completo
cd /d "F:\Gravity_AI_bridge"
color 0B
cls

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI BRIDGE V9.3.1 PRO [Diamond-Tier Edition]             ^|
echo  ^|          Arranque completo del ecosistema                                ^|
echo  +--------------------------------------------------------------------------+
echo.

REM ── 1. Liberar puertos colgados ─────────────────────────────────────────────
echo  [1/4] Liberando puertos previos (7860, 7861, 7862)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :7861 ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :7860 ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :7862 ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
echo  [OK]

REM ── 2. Bridge Server + Dashboard (7860) ─────────────────────────────────────
echo  [2/4] Iniciando Bridge Server (puerto 7860)...
start "Gravity :: Bridge Server" cmd /c "python bridge_server.py"
timeout /t 3 /nobreak > nul
echo  [OK]

REM ── 3. Fooocus en modo CPU (7861) ────────────────────────────────────────────
echo  [3/4] Iniciando Motor Fooocus CPU (puerto 7861)...
if exist "F:\Gravity_AI_bridge\_integrations\Fooocus\python_embeded\python.exe" (
    start "Gravity :: Motor [Fooocus CPU]" /d "F:\Gravity_AI_bridge\_integrations\Fooocus" cmd /c "run_amd.bat"
    echo  [OK] Motor Fooocus iniciando en segundo plano...
) else (
    echo  [!] Fooocus no encontrado en _integrations\Fooocus\
    echo  [!] Generacion de imagenes no disponible.
)

REM ── 4. Fooocus Studio UI Gradio (7862) ───────────────────────────────────────
echo  [4/4] Iniciando Fooocus Studio UI (puerto 7862)...
echo  [INFO] Esperando 15s para que Fooocus Motor inicialice antes de lanzar Studio UI...
timeout /t 15 /nobreak > nul
start "Gravity :: Fooocus Studio UI" cmd /c "python tools\fooocus_studio_ui.py"
echo  [OK]

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|                                                                          ^|
echo  ^|   Dashboard Web:    http://localhost:7860       (Chat, Status, Audit)    ^|
echo  ^|   Fooocus Motor:    http://127.0.0.1:7861      (API de generacion)      ^|
echo  ^|   Vision Studio:    http://127.0.0.1:7862      (UI de generacion)       ^|
echo  ^|                                                                          ^|
echo  ^|   [!] Fooocus CPU tarda ~60-90s en cargar. Imagen: 3-8 min              ^|
echo  ^|   [!] NO cierres la ventana del motor Fooocus mientras trabajas         ^|
echo  ^|                                                                          ^|
echo  +--------------------------------------------------------------------------+
echo.
echo  Abriendo el Dashboard principal en tu navegador...
start http://127.0.0.1:7860/
pause
