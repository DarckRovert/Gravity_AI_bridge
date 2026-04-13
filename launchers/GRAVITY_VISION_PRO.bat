@echo off
title Gravity AI — Vision Studio V9.1 PRO
cd /d "F:\Gravity_AI_bridge"
color 0B
cls

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI — Vision Studio V9.1 PRO [Diamond-Tier]              ^|
echo  ^|          ComfyUI ZLUDA + Fooocus Studio UI                               ^|
echo  +--------------------------------------------------------------------------+
echo.

REM ── Matar procesos previos en puerto 7861 si quedaron colgados ──────────────
echo  [1/4] Liberando puerto 7861 (limpieza preventiva)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :7861 ^| findstr LISTENING') do (
    echo        Matando PID %%p que ocupaba 7861...
    taskkill /F /PID %%p >nul 2>&1
)
echo  [OK]

REM ── Verificar que ComfyUI existe ────────────────────────────────────────────
echo  [2/4] Verificando motor ComfyUI-ZLUDA...
if not exist "F:\Gravity_AI_bridge\_integrations\ComfyUI-Zluda\comfyui-user.bat" (
    echo.
    echo  [ERROR] No se encontro comfyui-user.bat en:
    echo          F:\Gravity_AI_bridge\_integrations\ComfyUI-Zluda\
    echo  Asegurate de que ComfyUI-Zluda este instalado.
    pause
    exit /b 1
)

REM ── Verificar si ComfyUI ya corre (puerto 8188) ─────────────────────────────
netstat -ano | findstr :8188 | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo  [OK] ComfyUI ya esta corriendo en 8188. Saltando arranque.
) else (
    echo  [3/4] Iniciando Motor ComfyUI-ZLUDA en puerto 8188...
    start "Gravity Motor [ComfyUI-ZLUDA]" /d "F:\Gravity_AI_bridge\_integrations\ComfyUI-Zluda" cmd /c "comfyui-user.bat"
    echo  [!] Esperando 15s para que cargue el motor...
    timeout /t 15 /nobreak > nul
)

REM ── Lanzar Fooocus Studio UI ────────────────────────────────────────────────
echo  [4/4] Iniciando Fooocus Studio UI en puerto 7861...
start "Gravity Studio [Fooocus UI]" cmd /c "python tools\fooocus_studio_ui.py"

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|  Studio UI:  http://127.0.0.1:7861                                       ^|
echo  ^|  ComfyUI:    http://127.0.0.1:8188                                       ^|
echo  ^|  Bridge:     http://127.0.0.1:7860  (solo si INICIAR_SERVIDOR esta abierto)^|
echo  +--------------------------------------------------------------------------+
echo.
echo  [!] NO cierres las ventanas del Motor ni del Studio mientras trabajas.
echo  [!] La primera generacion tarda 3-5 min mientras ZLUDA compila los kernels.
echo.
timeout /t 5 /nobreak > nul
exit
