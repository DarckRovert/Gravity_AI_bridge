@echo off
setlocal enabledelayedexpansion
title DESINSTALADOR GLOBAL - GRAVITY AI BRIDGE V5.1
color 0c
cls

echo.
echo  +------------------------------------------------------+
echo  ^|         DESINSTALACION LIMPIA - GRAVITY AI           ^|
echo  +------------------------------------------------------+
echo.
echo  Iniciando protocolo de neutralizacion...
echo.

set "TARGET_DIR=%~dp0"
if "%TARGET_DIR:~-1%"=="\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"

REM --- [PASO 1/3] Limpiando PATH ---
echo  [1/3] Removiendo comando universal 'gravity' de las variables de entorno (PATH)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = [Environment]::GetEnvironmentVariable('Path', 'User'); $t = [regex]::Escape('%TARGET_DIR%'); $n = $p -ireplace (';?' + $t + '(?=;|$)'), ''; if($n -ne $p) { [Environment]::SetEnvironmentVariable('Path', $n, 'User') }"
if %errorlevel% neq 0 (
    echo    [!] Aviso: No se pudo limpiar el PATH. Quiza necesites permisos administrativos.
) else (
    echo    [OK] PATH Restaurado a la normalidad.
)

REM --- [PASO 2/3] Eliminando rastro en el Escritorio ---
echo  [2/3] Buscando y eliminando icono del Escritorio nativo o OneDrive...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=[Environment]::GetFolderPath('Desktop'); $l=$d+'\Gravity AI Auditor.lnk'; if(Test-Path $l){Remove-Item $l}"
echo    [OK] Icono fulminado.

REM --- [PASO 3/3] Neutralizando configuraciones de IDEs ---
echo  [3/3] Destruyendo configuraciones automaticas integradas...
if exist ".continue\config.yaml" del /Q ".continue\config.yaml"
if exist "aider.conf.yml" del /Q "aider.conf.yml"
if exist "_integrations\cursor.json" del /Q "_integrations\cursor.json"
echo    [OK] Rastros de VS Code, Cursor y Aider suprimidos pertinentemente.

echo.
echo  +------------------------------------------------------+
echo  ^|               NEUTRALIZACION COMPLETA                ^|
echo  +------------------------------------------------------+
echo.
echo    El puente ha sido extraido de tu entorno de Windows.
echo    Tus memorias _history.json y _knowledge.json permanecen
echo    intactas fisicamente para cuando decidas volver.
echo.
pause
exit /b 0
