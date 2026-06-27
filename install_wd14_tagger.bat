@echo off
echo ========================================================
echo GRAVITY AI: Instalador de WD14 Tagger para ComfyUI L2
echo ========================================================

set COMFY_PATH=%~dp0_integrations\ComfyUI_windows_portable
set CUSTOM_NODES=%COMFY_PATH%\ComfyUI\custom_nodes
set PYTHON_BIN=%COMFY_PATH%\python_embeded\python.exe

if not exist "%COMFY_PATH%" (
    echo [ERROR] No se encuentra la instalacion portable de ComfyUI en %COMFY_PATH%
    pause
    exit /b
)

echo [1/3] Entrando a custom_nodes...
cd /d "%CUSTOM_NODES%"

echo [2/3] Clonando ComfyUI-WD14-Tagger...
if exist "ComfyUI-WD14-Tagger" (
    echo Ya existe la carpeta ComfyUI-WD14-Tagger. Actualizando...
    cd ComfyUI-WD14-Tagger
    git pull
) else (
    git clone https://github.com/pythongosssss/ComfyUI-WD14-Tagger.git
    cd ComfyUI-WD14-Tagger
)

echo [3/3] Instalando dependencias en el entorno embebido de ComfyUI...
"%PYTHON_BIN%" -m pip install -r requirements.txt

echo.
echo ========================================================
echo Instalacion completada. El modelo se descargara
echo automaticamente la primera vez que se ejecute el nodo.
echo ========================================================
pause
