@echo off
echo =========================================================
echo  Gravity AI Bridge - Generador de Ejecutable (PyInstaller)
echo =========================================================
echo.

echo 1. Instalando PyInstaller...
pip install pyinstaller

echo.
echo 2. Compilando bridge_server.py y gravity_launcher.pyw...
echo.

:: Limpiamos builds anteriores
rmdir /S /Q build
rmdir /S /Q dist

:: Construir gravity_launcher (GUI invisible) que incluye a bridge_server internamente
pyinstaller --noconfirm --windowed --log-level=WARN ^
    --name "Gravity AI Launcher" ^
    --icon "assets/gravity_icon.ico" ^
    --add-data "config.yaml;." ^
    --add-data "frontend/dist;frontend/dist" ^
    --add-data "assets;assets" ^
    --add-data "core;core" ^
    --hidden-import "uvicorn" ^
    --hidden-import "fastapi" ^
    --hidden-import "psutil" ^
    --hidden-import "pillow" ^
    --hidden-import "pystray" ^
    --hidden-import "bridge_server" ^
    gravity_launcher.pyw

echo.
echo =========================================================
echo  Compilacion finalizada. Los ejecutables estan en /dist
echo =========================================================
pause
