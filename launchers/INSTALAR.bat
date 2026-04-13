@echo off
setlocal enabledelayedexpansion
title GRAVITY AI BRIDGE - Instalador
color 0b
cls

echo.
echo  +------------------------------------------------------------------------------+
echo  ^|        GRAVITY AI BRIDGE V9.0 PRO [Diamond-Tier Edition] - Instalador        ^|
echo  ^|                   github.com/DarckRovert/Gravity_AI_bridge                   ^|
echo  +------------------------------------------------------------------------------+
echo.

REM ── Verificar Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python no encontrado en tu sistema.
    echo.
    echo  Instala Python 3.10 o superior desde:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANTE: Durante la instalacion, marca la opcion:
    echo  "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Python detectado: %PYVER%

REM Verificar version minima 3.10
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)
if %PY_MAJOR% LSS 3 (
    echo  [ERROR] Python 3.10+ requerido. Tienes %PYVER%
    pause & exit /b 1
)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 (
    echo  [ERROR] Python 3.10+ requerido. Tienes %PYVER%
    pause & exit /b 1
)

echo  Version OK.
echo.

REM ── Bootstrap minimo: instalar Rich antes de lanzar el instalador TUI ─────────
echo  Preparando instalador visual (primera vez puede tardar ~30s)...
python -m pip install rich pyfiglet --quiet --no-warn-script-location >nul 2>&1
if %errorlevel% neq 0 (
    echo  [AVISO] No se pudo instalar automaticamente. Intentando igualmente...
)

echo  Lanzando instalador...
echo.

REM ── Lanzar INSTALAR.py pasando todos los argumentos ──────────────────────────
python "%~dp0..\INSTALAR.py" %*

if %errorlevel% neq 0 (
    echo.
    echo  El instalador termino con errores. Revisa los mensajes anteriores.
    pause
    exit /b 1
)

endlocal
