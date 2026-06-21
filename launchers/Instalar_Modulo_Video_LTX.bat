@echo off
title Gravity AI Bridge - Instalador de LTX-Video (Motor de Animacion L2)
color 0B
setlocal enabledelayedexpansion
cls

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|          INSTALADOR DEL MOTOR DE ANIMACION LTX-VIDEO (ComfyUI)          ^|
echo  +--------------------------------------------------------------------------+
echo.

set "ROOT=%~dp0.."
set "COMFY_PORTABLE=%ROOT%\_integrations\ComfyUI_windows_portable"
set "COMFY_DIR=%COMFY_PORTABLE%\ComfyUI"

if not exist "%COMFY_DIR%" (
    echo  [!] ERROR: No se encontro la carpeta de ComfyUI.
    echo  Asegurate de haber descargado y descomprimido ComfyUI_windows_portable.7z
    echo  dentro de: %ROOT%\_integrations\
    echo.
    pause
    exit /b 1
)

echo  [1/3] Instalando nodos oficiales de Lightricks (LTX-Video)...
set "CUSTOM_NODES=%COMFY_DIR%\custom_nodes"
cd /d "%CUSTOM_NODES%"

if not exist "ComfyUI-LTXVideo" (
    git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git
) else (
    echo  - El modulo LTX-Video ya esta clonado.
)

echo.
echo  [2/3] Instalando dependencias de Python en el entorno portable de ComfyUI...
cd /d "%COMFY_PORTABLE%"
call python_embeded\python.exe -m pip install -r ComfyUI\custom_nodes\ComfyUI-LTXVideo\requirements.txt

echo.
echo  [3/3] IMPORTANTE: Falta el modelo pesado (Pesos Neuronales).
echo  Debes descargar el archivo "ltx-video-2b-v0.9.5.safetensors" desde HuggingFace
echo  y guardarlo en: %COMFY_DIR%\models\checkpoints\
echo.
echo  [OK] Nodos instalados. Ya puedes cerrar esta ventana.
pause
