@echo off
title Gravity AI Bridge V10.0 -- Build Comercial
color 0B
cd /d "F:\Gravity_AI_bridge"

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|        GRAVITY AI BRIDGE V10.0 -- BUILD COMERCIAL                       ^|
echo  ^|        PyInstaller + Inno Setup                                          ^|
echo  +--------------------------------------------------------------------------+
echo.

echo  [0/5] Verificando / Generando icono...
if not exist "assets\gravity_icon.ico" (
    echo  [!] Icono no encontrado. Generando con Pillow...
    pip show Pillow >nul 2>&1
    if %errorlevel% neq 0 (
        pip install Pillow --trusted-host pypi.org --trusted-host files.pythonhosted.org
    )
    python make_icon.py
    if %errorlevel% neq 0 (
        echo  [ERROR] No se pudo generar el icono.
        pause
        exit /b 1
    )
) else (
    echo  [OK] Icono existente encontrado.
)
echo.

REM ── PASO 1: Limpiar artefactos de build anterior ────────────────────────────
echo  [1/5] Limpiando artefactos anteriores...
if exist "dist\GravityBridge.exe"  del /f /q "dist\GravityBridge.exe"
if exist "build\GravityBridge"     rmdir /s /q "build\GravityBridge"
REM NOTA: GravityBridge.spec NO se elimina. Si existe, PyInstaller lo reutiliza.
REM       Esto preserva hidden-imports y add-data configurados.
echo  [OK]
echo.

REM ── Verificar entry point ────────────────────────────────────────────────────
if not exist "gravity_launcher.pyw" (
    echo  [ERROR] No se encontro gravity_launcher.pyw en F:\Gravity_AI_bridge\
    echo  [ERROR] Asegurate de ejecutar este script desde la carpeta correcta.
    pause
    exit /b 1
)

REM ── PASO 2: Verificar PyInstaller ────────────────────────────────────────────
echo  [2/5] Verificando PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] PyInstaller no encontrado. Instalando...
    pip install pyinstaller --trusted-host pypi.org --trusted-host files.pythonhosted.org
    if %errorlevel% neq 0 (
        echo.
        echo  [ERROR] No se pudo instalar PyInstaller.
        echo  [ERROR] Verifica tu conexion a internet y los permisos de pip.
        echo  [ERROR] Intenta manualmente: pip install pyinstaller
        echo.
        pause
        exit /b 1
    )
)
echo  [OK]
echo.

REM ── PASO 3: Compilar con PyInstaller ─────────────────────────────────────────
echo  [3/5] Compilando GravityBridge.exe con PyInstaller...
echo  (Esto puede tardar 3-8 minutos en la primera ejecucion)
echo.

if exist "GravityBridge.spec" (
    echo  [INFO] Usando GravityBridge.spec existente...
    pyinstaller GravityBridge.spec --noconfirm --distpath dist --workpath build --clean
) else (
    echo  [INFO] GravityBridge.spec no encontrado. Generando desde flags...
    pyinstaller gravity_launcher.pyw ^
      --name GravityBridge ^
      --onefile ^
      --noconsole ^
      --icon assets\gravity_icon.ico ^
      --add-data "web;web" ^
      --add-data "core;core" ^
      --add-data "rag;rag" ^
      --add-data "providers;providers" ^
      --add-data "tools;tools" ^
      --add-data "_knowledge.json;." ^
      --add-data "config.yaml;." ^
      --add-data "assets;assets" ^
      --hidden-import pystray ^
      --hidden-import PIL ^
      --hidden-import aiohttp ^
      --hidden-import yaml ^
      --hidden-import rich ^
      --hidden-import anthropic ^
      --hidden-import pymysql ^
      --hidden-import win32api ^
      --hidden-import win32security ^
      --hidden-import prometheus_client ^
      --collect-all pystray ^
      --distpath dist ^
      --workpath build ^
      --clean ^
      --noconfirm
)

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] PyInstaller fallo. Revisa los mensajes anteriores.
    pause
    exit /b 1
)
echo.
echo  [OK] GravityBridge.exe generado en dist\

REM ── PASO 4: Verificar Inno Setup ─────────────────────────────────────────────
echo  [4/5] Buscando Inno Setup Compiler...
set ISCC=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if %ISCC%=="" (
    echo.
    echo  [!] Inno Setup 6 no encontrado en las rutas estandar.
    echo  [!] Descargalo gratis en: https://jrsoftware.org/isdl.php
    echo  [!] El ejecutable GravityBridge.exe esta listo en dist\
    echo  [!] Una vez instalado Inno Setup, ejecuta manualmente:
    echo  [!]   installer\gravity_setup.iss
    echo.
    pause
    exit /b 0
)
echo  [OK] Inno Setup encontrado en %ISCC%
echo.

REM ── PASO 5: Crear instalador .exe ─────────────────────────────────────────────
echo  [5/5] Generando instalador Gravity_AI_Bridge_V10.0_Setup.exe...
%ISCC% "installer\gravity_setup.iss"

if %errorlevel% neq 0 (
    echo  [ERROR] Inno Setup fallo durante la compilacion.
    pause
    exit /b 1
)

echo.
echo  +--------------------------------------------------------------------------+
echo  ^|   BUILD COMPLETADO                                                       ^|
echo  ^|                                                                          ^|
echo  ^|   Ejecutable:   dist\GravityBridge.exe                                  ^|
echo  ^|   Instalador:   dist\Gravity_AI_Bridge_V10.0_Setup.exe                  ^|
echo  ^|                                                                          ^|
echo  ^|   El instalador puede distribuirse a cualquier usuario Windows 10/11.   ^|
echo  ^|   No requiere Python instalado en el equipo destino.                    ^|
echo  +--------------------------------------------------------------------------+
echo.
pause
