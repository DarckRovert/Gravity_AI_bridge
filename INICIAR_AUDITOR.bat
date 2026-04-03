@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

title GRAVITY AI -- AUDITOR SENIOR V3.0
color 0b
cls

REM -- Instalar dependencias criticas silenciosamente ---
python -m pip install rich pyfiglet pyreadline3 --quiet >nul 2>&1

REM -- Ejecutar diagnostico del sistema ---
python health_check.py
set CHECK_RESULT=%errorlevel%

if %CHECK_RESULT% NEQ 0 (
    echo.
    echo  [!] El diagnostico fallo. Revisa la pantalla de arriba.
    echo  [!] El Auditor NO se iniciara hasta que el sistema este listo.
    echo.
    pause
    exit /b 1
)

REM -- Iniciar el Auditor Principal ---
timeout /t 1 /nobreak >nul
cls
python ask_deepseek.py

:END
echo.
echo  [*] El Auditor ha cerrado sesion.
pause
endlocal
