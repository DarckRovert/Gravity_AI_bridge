@echo off
setlocal EnableDelayedExpansion
title Gravity AI Bridge — Deploy V9.1 PRO
cd /d "F:\Gravity_AI_bridge"
color 0B
cls

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI BRIDGE V9.1 PRO — Sincronizacion GitHub              ^|
echo  ^|          Repositorio: github.com/DarckRovert/Gravity_AI_bridge           ^|
echo  +--------------------------------------------------------------------------+
echo.

REM ── 1. Verificar Git ────────────────────────────────────────────────────────
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Git no encontrado en el PATH del sistema.
    echo  Instala Git desde https://git-scm.com
    pause
    exit /b 1
)

REM ── 2. Verificar repositorio ────────────────────────────────────────────────
if not exist "F:\Gravity_AI_bridge\.git" (
    echo  [ERROR] Este directorio no es un repositorio Git.
    pause
    exit /b 1
)

REM ── 3. Asegurar remote correcto ─────────────────────────────────────────────
git remote set-url origin "https://github.com/DarckRovert/Gravity_AI_bridge.git" >nul 2>&1

REM ── 4. Obtener fecha del sistema ────────────────────────────────────────────
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /format:list 2^>nul') do set _dt=%%I
set FECHA=%_dt:~0,4%-%_dt:~4,2%-%_dt:~6,2%
set HORA=%_dt:~8,2%:%_dt:~10,2%

REM ── 5. Verificar si hay cambios ─────────────────────────────────────────────
echo  Verificando cambios pendientes...
set CHANGES=0
for /f "tokens=*" %%i in ('git status --porcelain') do set CHANGES=1

if %CHANGES% EQU 0 (
    echo.
    echo  [OK] No hay cambios nuevos. El repositorio esta sincronizado.
    echo  Ultimo commit:
    git log -1 --format="  %%h — %%s (%%ad)" --date=format:"%%Y-%%m-%%d %%H:%%M"
    echo.
    timeout /t 5 /nobreak >nul
    exit /b 0
)

REM ── 6. Mostrar resumen de cambios ───────────────────────────────────────────
echo.
echo  Archivos con cambios:
git status --short
echo.

REM ── 7. Confirmar con el usuario ─────────────────────────────────────────────
set /p CONFIRM="  Proceder con el commit y push? [S/N]: "
if /i not "%CONFIRM%"=="S" (
    echo  [CANCELADO] Deploy abortado por el usuario.
    pause
    exit /b 0
)

REM ── 8. Commit y Push ────────────────────────────────────────────────────────
set MSG=feat: Gravity AI Bridge V9.1 PRO sync %FECHA% %HORA%
echo.
echo  Commiteando: "%MSG%"

git add .
git commit -m "%MSG%"
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Fallo al crear el commit. Revisa el estado de Git.
    pause
    exit /b 1
)

git branch -M main
echo  Subiendo a GitHub...
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo  +--------------------------------------------------------------------------+
    echo  ^|  [OK] Deploy exitoso a github.com/DarckRovert/Gravity_AI_bridge          ^|
    echo  ^|  Commit: %MSG%  ^|
    echo  +--------------------------------------------------------------------------+
) else (
    echo.
    echo  [ERROR] Push fallido. Posibles causas:
    echo    1. Sin conexion a internet.
    echo    2. Token de GitHub expirado (configura con: git credential-manager).
    echo    3. Conflictos remotos (haz git pull primero).
)

echo.
pause
exit /b 0
