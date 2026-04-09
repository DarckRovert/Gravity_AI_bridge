@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

REM ── Gravity AI Bridge V9.0 PRO [Diamond-Tier Edition] - Comando Global ──────────────────────────────
REM Uso:  gravity "pregunta"          → respuesta directa
REM       gravity                     → modo interactivo
REM       gravity --help              → ayuda rápida
REM       gravity --install           → lanzar instalador TUI
REM       gravity --server            → iniciar bridge server
REM       gravity --status            → estado del sistema
REM ────────────────────────────────────────────────────────────────────────────

if "%~1"=="--help" (
    echo.
    echo  GRAVITY AI BRIDGE V9.0 PRO [Diamond-Tier Edition] - Ayuda Rapida
    echo  ─────────────────────────────────────────
    echo  gravity                  Modo interactivo
    echo  gravity "pregunta"       Respuesta directa
    echo  gravity --install        Instalador TUI premium
    echo  gravity --server         Iniciar bridge server
    echo  gravity --dashboard      Abrir dashboard ^(http://localhost:7860^)
    echo  gravity --status         Estado de los motores de IA
    echo  gravity --version        Version actual
    echo.
    exit /b 0
)

if "%~1"=="--version" (
    echo Gravity AI Bridge V9.0 PRO [Diamond-Tier Edition]
    echo https://github.com/DarckRovert/Gravity_AI_bridge
    exit /b 0
)

if "%~1"=="--install" (
    python "%~dp0INSTALAR.py"
    exit /b 0
)

if "%~1"=="--server" (
    start "" "%~dp0INICIAR_SERVIDOR.bat"
    exit /b 0
)

if "%~1"=="--dashboard" (
    start "" "http://localhost:7860"
    exit /b 0
)

if "%~1"=="--status" (
    python "%~dp0health_check.py"
    exit /b 0
)

REM ── Verificar Python ─────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Python no encontrado. Descarga: https://www.python.org/downloads/
    exit /b 1
)

REM ── Bootstrap Rich silencioso ─────────────────────────────────────────────────
python -m pip install rich pyfiglet pyreadline3 -q --no-warn-script-location >nul 2>&1

REM ── Lanzar Auditor ───────────────────────────────────────────────────────────
python "%~dp0ask_deepseek.py" %*
