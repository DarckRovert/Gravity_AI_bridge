@echo off
setlocal enabledelayedexpansion
title INSTALADOR GLOBAL - GRAVITY AI BRIDGE V4.2
color 0b
cls

echo.
echo  +------------------------------------------------------+
echo  ^|       GRAVITY AI BRIDGE V4.2 - MODO GOD-TIER         ^|
echo  +------------------------------------------------------+
echo.
echo  Iniciando asistente de instalacion automatizado...
echo.

set "TARGET_DIR=%~dp0"
if "%TARGET_DIR:~-1%"=="\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"

REM --- [PASO 1/8] Python ---
echo  [1/8] Verificando motor de Python 3.10+...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    [X] ERROR FATAL: Python no esta instalado. Descarga e instala python.org
    pause
    exit /b 1
) else (
    echo    [OK] Python detectado satisfactoriamente.
)

REM --- [PASO 2/8] Pip ---
echo  [2/8] Actualizando gestor de paquetes...
python -m pip install --upgrade pip --quiet >nul 2>&1
echo    [OK] Pip actualizado.

REM --- [PASO 3/8] Dependencias ---
echo  [3/8] Instalando dependencias core (rich, pyfiglet, etc)...
python -m pip install rich pyfiglet pyreadline3 urllib3 --quiet >nul 2>&1
if %errorlevel% neq 0 (
    echo    [!] Aviso: Pip devolvio advertencias o fallos, intentando continuar...
) else (
    echo    [OK] Bibliotecas principales listas.
)

REM --- [PASO 4/8] Escaneo de IA ---
echo  [4/8] Escaneando hardware neuronal (Ollama, LM Studio)...
python "%TARGET_DIR%\provider_scanner.py"
if %errorlevel% neq 0 (
    echo    [!] Fallo escaneando hardware.
)

REM --- [PASO 5/8] Auto-Configurando Settings ---
echo  [5/8] Asignando la mejor Inteligencia Artificial como Core por defecto...
python "%TARGET_DIR%\auto_config.py"
if %errorlevel% neq 0 (
    echo    [!] Falla vinculando configuraciones de red, se usaran defaults.
)

REM --- [PASO 6/8] Configurando Integraciones (IDE) ---
echo  [6/8] Auto-generando perfiles para Continue.dev, Aider y Cursor...
python "%TARGET_DIR%\run_integrator.py" "todo"
if %errorlevel% neq 0 (
    echo    [!] Imposible autoconfigurar las extensiones IDE en esta pasada.
)

REM --- [PASO 7/8] PATH Global ---
echo  [7/8] Instalando comando universal 'gravity' en variables de entorno...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = [Environment]::GetEnvironmentVariable('Path', 'User'); if ($p -match [regex]::Escape('%TARGET_DIR%')) { exit 0 } else { exit 1 }"
if %errorlevel%==0 (
    echo    [OK] Comando universal 'gravity' ya estaba registrado.
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'User') + ';%TARGET_DIR%', 'User')"
    if %errorlevel%==0 (
        echo    [OK] Inyectado comando global. Puedes escribir 'gravity' en cualquier CMD.
    ) else (
        echo    [!] Aviso: No se pudo inyectar el PATH. Posible falta de persmisos.
    )
)

REM --- [PASO 7/8] Icono del Escritorio ---
echo  [7/8] Configurando iconografia del Escritorio...
cscript //nologo "%TARGET_DIR%\create_icon.vbs" "%TARGET_DIR%" >nul 2>&1
if exist "%TARGET_DIR%\create_icon.vbs" del "%TARGET_DIR%\create_icon.vbs"
echo    [OK] Acceso directo magnetizado en el Escritorio.

REM --- [PASO 8/8] Test Inferencia Frontal ---
echo  [8/8] Ejecutando test de inferencia local con proxy de consola...
echo        Pregunta: "Resume tu proposito en 10 palabras"
echo.

set "BEST=deepseek-r1:8b"
if exist "%TARGET_DIR%\_install_best_model.txt" (
    set /p BEST=<"%TARGET_DIR%\_install_best_model.txt"
    del "%TARGET_DIR%\_install_best_model.txt"
)

python "%TARGET_DIR%\ask_deepseek.py" "Resume tu proposito en menos de 10 palabras analitico, directo. Soy un desarrollador."
if %errorlevel% neq 0 (
    echo    [!] La inferencia o conexion de primer arranque dio error.
) else (
    echo.
    echo    [OK] Cerebro conectado exitosamente empleando "%BEST%".
)

echo.
echo  +------------------------------------------------------+
echo  ^|         SISTEMA GRAVITY INSTALADO CON EXITO          ^|
echo  +------------------------------------------------------+
echo.
echo  Gravity AI Bridge V4.2 se ha fusionado con tu entorno de desarrollo.
echo.
echo  MODOS DE USO:
echo    1. Consola Nativa: Escribe en cualquier CMD: gravity "tu pregunta"
echo    2. Visual Studio Code: Simplemente usa Continue.dev / Aider / Cursor.
echo       Su trafico ahora mismo sera interceptado por tu modelo local: %BEST%
echo.
echo  Opcional: Lanza INICIAR_SERVIDOR.bat para dejar el bridge vivo en 2do plano.
echo.
pause
exit /b 0
