@echo off
setlocal enabledelayedexpansion
REM BUG-10 FIX: Usar paths absolutos con %~dp0 para todos los scripts Python,
REM garantizando que funciona independientemente del directorio de trabajo actual.
cd /d "%~dp0"

title GRAVITY AI -- AUDITOR SENIOR V9.0 PRO
color 0b
cls

REM -- Instalar dependencias criticas silenciosamente ---
python -m pip install rich pyfiglet pyreadline3 --quiet >nul 2>&1

REM -- Ejecutar diagnostico del sistema (path absoluto) ---
python "%~dp0health_check.py"
set CHECK_RESULT=%errorlevel%

if %CHECK_RESULT% NEQ 0 (
    echo.
    echo  [!] El diagnostico fallo. Revisa la pantalla de arriba.
    echo  [!] El Auditor NO se iniciara hasta que el sistema este listo.
    echo.
    pause
    exit /b 1
)

REM -- Breve pausa antes de lanzar el auditor ---
timeout /t 1 /nobreak >nul
cls

REM -- Iniciar el Auditor Principal (path absoluto) ---
python "%~dp0ask_deepseek.py"

:END
echo.
echo  [*] El Auditor ha cerrado sesion.
pause
endlocal
