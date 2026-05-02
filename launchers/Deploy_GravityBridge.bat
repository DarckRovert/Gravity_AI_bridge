@echo off
title Gravity AI Bridge V12.1 PRO -- Deploy a GitHub
color 0B
setlocal enabledelayedexpansion

REM ── Ruta relativa desde launchers/ hacia la raiz del proyecto ─────────────
set "ROOT=%~dp0.."
cd /d "%ROOT%"

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|        GRAVITY AI BRIDGE V12.1 PRO -- DEPLOY A GITHUB                   ^|
echo  +--------------------------------------------------------------------------+
echo.

REM ── Verificar que estamos en el repo correcto ─────────────────────────────────
if not exist ".git" (
    echo  [ERROR] No se encontro repositorio Git en: %ROOT%
    echo  [ERROR] Asegurate de que este script este en la carpeta 'launchers'.
    pause
    exit /b 1
)

REM ── Mensaje de commit dinamico con fecha y hora ───────────────────────────────
for /f "tokens=1-3 delims=/" %%a in ("%DATE%") do (
    set "FECHA=%%c-%%b-%%a"
)
for /f "tokens=1-2 delims=:" %%a in ("%TIME%") do (
    set "HORA=%%a:%%b"
)
set "COMMIT_MSG=chore: Gravity AI Bridge V12.1 PRO [MAI Engine] — estabilizado %FECHA% %HORA%"

echo  [INFO] Raiz del proyecto: %ROOT%
echo  [INFO] Commit: %COMMIT_MSG%
echo.

REM ── Verificar estado git ──────────────────────────────────────────────────────
git status --short
echo.
set /p CONFIRM="Confirmar deploy a GitHub? (S/N): "
if /i not "%CONFIRM%"=="S" (
    echo  [CANCELADO] Deploy abortado por el usuario.
    pause
    exit /b 0
)

REM ── Staging, commit y push ────────────────────────────────────────────────────
echo  [1/3] git add ...
git add .
if %errorlevel% neq 0 ( echo  [ERROR] git add fallo. & pause & exit /b 1 )

echo  [2/3] git commit ...
git commit -m "%COMMIT_MSG%"
if %errorlevel% neq 0 (
    echo  [INFO] Sin cambios que commitear (working tree limpio).
)

echo  [3/3] git push origin main ...
git push origin main
if %errorlevel% neq 0 (
    echo  [ERROR] git push fallo. Verifica credenciales y conectividad.
    pause
    exit /b 1
)

echo.
echo  [OK] Deploy completado exitosamente.
echo  [OK] Ver en: https://github.com/DarckRovert/Gravity_AI_bridge
echo.
pause
