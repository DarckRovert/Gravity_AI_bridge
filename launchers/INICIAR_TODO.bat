@echo off
title Gravity AI Bridge V9.1 PRO — Arranque Completo
cd /d "F:\Gravity_AI_bridge"
color 0B
cls

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI BRIDGE V9.1 PRO [Diamond-Tier Edition]               ^|
echo  ^|          Arranque completo del ecosistema                                ^|
echo  +--------------------------------------------------------------------------+
echo.

REM ── 1. Liberar puertos colgados ─────────────────────────────────────────────
echo  [1/4] Liberando puertos previos...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :7861 ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :7860 ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
echo  [OK]

REM ── 2. ComfyUI ZLUDA (si no corre ya) ───────────────────────────────────────
echo  [2/4] Verificando motor ComfyUI-ZLUDA (puerto 8188)...
netstat -ano | findstr :8188 | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo  [OK] ComfyUI ya esta corriendo, no se reinicia.
) else (
    if exist "F:\Gravity_AI_bridge\_integrations\ComfyUI-Zluda\comfyui-user.bat" (
        start "Gravity :: Motor [ComfyUI]" /d "F:\Gravity_AI_bridge\_integrations\ComfyUI-Zluda" cmd /c "comfyui-user.bat"
        echo  [OK] Motor iniciando en segundo plano...
        timeout /t 15 /nobreak > nul
    ) else (
        echo  [!] ComfyUI no encontrado. Generacion de imagenes no disponible.
    )
)

REM ── 3. Bridge Server + Dashboard (7860) ─────────────────────────────────────
echo  [3/4] Iniciando Bridge Server y Dashboard (puerto 7860)...
start "Gravity :: Bridge Server" cmd /c "python bridge_server.py"
timeout /t 3 /nobreak > nul
echo  [OK]

REM ── 4. Fooocus Studio UI (7861) ─────────────────────────────────────────────
echo  [4/4] Iniciando Fooocus Studio UI (puerto 7861)...
start "Gravity :: Studio" cmd /c "python tools\fooocus_studio_ui.py"
echo  [OK]

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|                                                                          ^|
echo  ^|   Dashboard Web:    http://localhost:7860       (Chat, Status, Audit)    ^|
echo  ^|   Fooocus Studio:   http://127.0.0.1:7861      (Generacion de imagenes) ^|
echo  ^|   ComfyUI:          http://127.0.0.1:8188      (Motor interno)          ^|
echo  ^|                                                                          ^|
echo  ^|   [!] Primera imagen tarda 3-5 min (ZLUDA compila kernels)             ^|
echo  ^|   [!] NO cierres las ventanas del motor mientras trabajas              ^|
echo  ^|                                                                          ^|
echo  +--------------------------------------------------------------------------+
echo.
pause
