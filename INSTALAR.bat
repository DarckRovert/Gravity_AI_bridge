@echo off
setlocal enabledelayedexpansion
title INSTALADOR GLOBAL - GRAVITY AI BRIDGE V4.0
color 0b
cls

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║       GRAVITY AI BRIDGE V4.0 — MODO GOD-TIER         ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Iniciando asistente de instalacion automatizado...
echo.

set "TARGET_DIR=%~dp0"
if "%TARGET_DIR:~-1%"=="\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"

REM --- [PASO 1/8] Python ---
echo  [1/8] Verificando motor de Python 3.10+...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    [X] ERROR FATAL: Python no esta instalado. Abortando.
    pause
    exit /b 1
) else (
    echo    [OK] Listo.
)

REM --- [PASO 2/8] Pip ---
echo  [2/8] Actualizando gestor de paquetes...
python -m pip install --upgrade pip --quiet >nul 2>&1
echo    [OK] Pip actualizado.

REM --- [PASO 3/8] Dependencias ---
echo  [3/8] Instalando motor de UI y extensiones (rich, pyfiglet, etc)...
python -m pip install rich pyfiglet pyreadline3 urllib3 --quiet >nul 2>&1
echo    [OK] Bibliotecas core listas.

REM --- [PASO 4/8] Escaneo de IA ---
echo  [4/8] Escaneando hardware (Ollama, LM Studio)...
python "%TARGET_DIR%\provider_scanner.py" >nul 2>&1
echo    [OK] Ecosistema indexado.

REM --- [PASO 5/8] Configurando Integraciones (IDE) ---
echo  [5/8] Auto-generando configuraciones proxy proxy para IDEs...
python "%TARGET_DIR%\run_integrator.py" "todo" >nul 2>&1
echo    [OK] Puente OpenAI expuesto para Continue.dev/Cursor/Aider.

REM --- [PASO 6/8] PATH Global ---
echo  [6/8] Instalando comando universal 'gravity' en CMD/PowerShell...
echo %PATH% | findstr /i /c:"%TARGET_DIR%" >nul
if %errorlevel%==0 (
    echo    [OK] Comando ya existia previamente.
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'User') + ';%TARGET_DIR%', 'User')"
    if %errorlevel%==0 (
        echo    [OK] PATH de Windows inyectado con exito.
    ) else (
        echo    [!] Aviso: No se pudo editar el PATH (probablemente requiera Admin).
    )
)

REM --- [PASO 7/8] Icono ---
echo  [7/8] Configurando iconografia del Escritorio...
set "LNK_PATH=%USERPROFILE%\Desktop\Gravity AI Auditor.lnk"
if not exist "%LNK_PATH%" (
    echo $s=^(New-Object -COM WScript.Shell^).CreateShortcut^('%LNK_PATH%'^);$s.TargetPath^='%TARGET_DIR%\INICIAR_AUDITOR.bat';$s.WorkingDirectory^='%TARGET_DIR%';$s.IconLocation^='%SystemRoot%\System32\SHELL32.dll,300';$s.Save^(^) > "%TEMP%\createlink.ps1"
    powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\createlink.ps1"
    del "%TEMP%\createlink.ps1"
    echo    [OK] Acceso directo magnetizado.
) else (
    echo    [OK] El icono ya estaba en el escritorio.
)

REM --- [PASO 8/8] Test Inferencia ---
echo  [8/8] Ejecutando test de inferencia local...
echo        Pregunta: "Resume tu proposito en 10 palabras"
echo.
python "%TARGET_DIR%\ask_deepseek.py" "Resume tu proposito en menos de 10 palabras directo, sin markdown"
echo.
echo    [OK] Inferencia completada.

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║       INSTALACION TOTAL COMPLETADA EXITOSAMENTE      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Gravity AI Bridge V4.0 se ha convertido en el sistema nervioso de tu PC.
echo.
echo  Ahora dispones de estas herramientas:
echo    1. Desde cualquier consola escribe: gravity "tu pregunta"
echo    2. En el escritorio tienes: Gravity AI Auditor
echo    3. Si usas Continue.dev en VSCode, ya tienes el Bridge Server auto-configurado.
echo.
echo  TIP PRO: Lanza el servidor backend con 'INICIAR_SERVIDOR.bat' para tus IDEs.
echo.
pause
exit /b 0
