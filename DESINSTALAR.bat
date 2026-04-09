@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title DESINSTALADOR — GRAVITY AI BRIDGE V9.0 PRO
color 0c
cls

echo.
echo  +------------------------------------------------------------------------------+
echo  ^|      GRAVITY AI BRIDGE V9.0 PRO [Diamond-Tier Edition] - Desinstalador       ^|
echo  +------------------------------------------------------------------------------+
echo.
echo  Iniciando protocolo de neutralizacion...
echo.

REM Capturar directorio sin barra final (necesario para el regex de PowerShell)
set "TARGET_DIR=%~dp0"
if "%TARGET_DIR:~-1%"=="\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"

REM ── [PASO 1/4] Limpiar PATH del usuario ──────────────────────────────────────
echo  [1/4] Removiendo 'gravity' del PATH del usuario...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$t = [regex]::Escape('%TARGET_DIR%'); $p = [Environment]::GetEnvironmentVariable('Path','User'); $n = ($p -split ';' | Where-Object { $_ -ne '%TARGET_DIR%' }) -join ';'; if($n -ne $p){ [Environment]::SetEnvironmentVariable('Path',$n,'User'); Write-Host '   [OK] PATH restaurado.' } else { Write-Host '   [OK] No estaba en PATH.' }"

REM ── [PASO 2/4] Eliminar acceso directo del Escritorio ────────────────────────
echo  [2/4] Eliminando icono del Escritorio...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$desk = [Environment]::GetFolderPath('Desktop'); $lnk = Join-Path $desk 'Gravity AI Auditor.lnk'; if(Test-Path $lnk){ Remove-Item $lnk -Force; Write-Host '   [OK] Icono eliminado.' } else { Write-Host '   [OK] No existia el icono.' }"

REM ── [PASO 3/4] Eliminar rastros en IDEs ──────────────────────────────────────
echo  [3/4] Limpiando configuraciones de IDEs...
if exist "%~dp0.continue\config.yaml"    del /Q "%~dp0.continue\config.yaml"
if exist "%~dp0aider.conf.yml"           del /Q "%~dp0aider.conf.yml"
if exist "%~dp0_integrations\cursor.json" del /Q "%~dp0_integrations\cursor.json"
echo    [OK] Configuraciones de Cursor, Aider y VS Code eliminadas.

REM ── [PASO 4/4] Limpiar estado de primera ejecucion ───────────────────────────
echo  [4/4] Resetear estado de primera ejecucion...
if exist "%~dp0_first_run_done" del /Q "%~dp0_first_run_done"
echo    [OK] El wizard de bienvenida se mostrara en la proxima ejecucion.

echo.
echo  +------------------------------------------------------------------------------+
echo  ^|                   DESINSTALACION COMPLETA                    ^|
echo  +------------------------------------------------------------------------------+
echo.
echo    El puente ha sido extraido de tu entorno de Windows.
echo.
echo    Se han CONSERVADO (no eliminados):
echo      - _knowledge.json    (base de conocimiento persistente)
echo      - _audit_log.jsonl   (audit log inmutable)
echo      - _saves\            (sesiones guardadas con /save)
echo      - Todos los archivos del proyecto en %TARGET_DIR%
echo.
echo    Para reinstalar: ejecuta INSTALAR.bat
echo    Para eliminar el proyecto completo: borra la carpeta manualmente.
echo.
pause
exit /b 0
