@echo off
title Instalador de Motor Nativo Gravity AI
echo ==============================================================
echo Instalador de Motor de Inferencia Nativo (llama-cpp-python)
echo Gravity AI Bridge V16.0 PRO
echo ==============================================================
echo.
echo Selecciona el hardware de tu equipo para la aceleracion:
echo.
echo [1] AMD Radeon / APU Ryzen (Usa aceleracion Vulkan) - Recomendado para Ryzen 8700G
echo [2] NVIDIA RTX/GTX (Usa aceleracion CUDA)
echo [3] Solo Procesador / CPU basico (Mas lento)
echo.
set /p choice="Elige una opcion (1, 2 o 3): "

if "%choice%"=="1" goto amd
if "%choice%"=="2" goto nvidia
if "%choice%"=="3" goto cpu

:amd
echo.
echo [+] Instalando version pre-compilada con soporte VULKAN para graficas AMD...
pip install llama-cpp-python huggingface-hub --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/vulkan --upgrade --force-reinstall --no-cache-dir
goto fin

:nvidia
echo.
echo [+] Instalando version pre-compilada con soporte CUDA para graficas NVIDIA...
pip install llama-cpp-python huggingface-hub --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 --upgrade --force-reinstall --no-cache-dir
goto fin

:cpu
echo.
echo [+] Instalando version basica de CPU...
pip install llama-cpp-python huggingface-hub --upgrade
goto fin

:fin

if %errorlevel% neq 0 (
    echo.
    echo [!] Hubo un error en la instalacion acelerada. Asegurate de tener instaladas las herramientas de compilacion de C++.
    echo [!] Haciendo fallback a instalacion generica de CPU por seguridad...
    set CMAKE_ARGS=
    set FORCE_CMAKE=
    pip install llama-cpp-python huggingface-hub --upgrade
)

echo.
echo [V] Instalacion completada.
pause
