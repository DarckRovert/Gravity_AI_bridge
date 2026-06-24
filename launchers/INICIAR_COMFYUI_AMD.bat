@echo off
chcp 65001 >nul
title Gravity AI Bridge -- MAI L2 (ComfyUI AMD DirectML)
setlocal enabledelayedexpansion
color 0D

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          GRAVITY AI BRIDGE V16.0 PRO                                     ^|
echo  ^|          Motor L2 - ComfyUI Optimizado para AMD Radeon (DirectML)        ^|
echo  +--------------------------------------------------------------------------+
echo.

set "ROOT=%~dp0.."
set "VENV_DIR=%ROOT%\_integrations\comfy_amd_venv"
set "COMFY_DIR=%ROOT%\_integrations\ComfyUI_windows_portable\ComfyUI"

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [!] ERROR: Entorno virtual AMD no encontrado en %VENV_DIR%
    pause
    exit /b 1
)

if not exist "%COMFY_DIR%\main.py" (
    echo [!] ERROR: ComfyUI no encontrado en %COMFY_DIR%
    pause
    exit /b 1
)

echo [INFO] Iniciando ComfyUI con entorno virtual dedicado para AMD...
echo [INFO] Argumentos: --directml --highvram --disable-cuda-malloc
echo.

cd /d "%COMFY_DIR%"
"%VENV_DIR%\Scripts\python.exe" main.py --directml --highvram --disable-cuda-malloc

pause
