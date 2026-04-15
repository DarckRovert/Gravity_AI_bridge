@echo off
title Gravity AI -- Vision Studio V9.3 PRO
cd /d "F:\Gravity_AI_bridge"
color 0B
cls

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI -- Vision Studio V9.3.1 PRO [Diamond-Tier]           ^|
echo  ^|          Motor: Fooocus 2.5.5 CPU-Mode (Estable sin crash)               ^|
echo  +--------------------------------------------------------------------------+
echo.

REM ── Matar procesos previos en puerto 7861 si quedaron colgados ─────────
echo  [1/3] Liberando puerto 7861...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :7861 ^| findstr LISTENING') do (
    echo        Matando PID %%p en 7861...
    taskkill /F /PID %%p >nul 2>&1
)
echo  [OK]

REM ── Verificar que Fooocus existe ─────────────────────────────────────────────
echo  [2/3] Verificando motor Fooocus CPU...
if not exist "F:\Gravity_AI_bridge\_integrations\Fooocus\python_embeded\python.exe" (
    echo.
    echo  [ERROR] No se encontro Fooocus internamente en:
    echo          F:\Gravity_AI_bridge\_integrations\Fooocus\
    pause
    exit /b 1
)
echo  [OK] Fooocus encontrado.

REM ── Lanzar Fooocus ───────────────────────────────────────────────
echo  [3/3] Iniciando Ecosistema Vision...
start "Gravity Motor [Fooocus CPU]" /d "F:\Gravity_AI_bridge\_integrations\Fooocus" cmd /c "run_amd.bat"
timeout /t 5 /nobreak > nul

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|  Fooocus Motor:  http://127.0.0.1:7861  (abrir en ~60-90 segundos)       ^|
echo  ^|  Vision Studio:  http://127.0.0.1:7862  (Interfaz unificada)             ^|
echo  ^|  Bridge API:     http://127.0.0.1:7860  (solo si Bridge corriendo)       ^|
echo  ^|                                                                           ^|
echo  ^|  [!] Generacion en modo CPU puro: 3-8 min por imagen (sin crash)          ^|
echo  ^|  [!] NO cierres la ventana del motor Fooocus                             ^|
echo  +--------------------------------------------------------------------------+
echo.
timeout /t 5 /nobreak > nul
exit
