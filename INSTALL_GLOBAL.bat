@echo off
setlocal enabledelayedexpansion

title INSTALADOR GLOBAL - GRAVITY AI BRIDGE
color 0a
cls

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║       GRAVITY AI BRIDGE — INSTALADOR GLOBAL          ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  [*] Iniciando instalacion del comando 'gravity'...
echo.

set "TARGET_DIR=%~dp0"
:: Quitar la barra invertida final si existe
if "%TARGET_DIR:~-1%"=="\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"

echo  [+] Directorio detectado: %TARGET_DIR%
echo.

REM ── Verificar si ya esta en el PATH ──────────────────────────────────────
echo %PATH% | findstr /i /c:"%TARGET_DIR%" >nul
if %errorlevel%==0 (
    echo  [OK] El directorio ya se encuentra en tu PATH. No es necesario reinstalar.
) else (
    echo  [*] Añadiendo al PATH del usuario de forma segura...
    :: Usamos PowerShell para evitar el limite de 1024 caracteres de SETX y evitar duplicados
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'User') + ';%TARGET_DIR%', 'User')"
    
    if %errorlevel%==0 (
        echo  [OK] Directorio añadido con exito.
        echo  [TIP] Deberas reiniciar tu terminal para usar el comando 'gravity'.
    ) else (
        echo  [ERROR] No se pudo actualizar el PATH. Prueba ejecutando como Administrador.
        pause
        exit /b 1
    )
)

REM ── Verificar Dependencias ────────────────────────────────────────────────
echo.
echo  [*] Verificando dependencias criticas...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] ADVERTENCIA: Python no detectado. Instala Python 3.x para usar el Auditor.
) else (
    echo  [OK] Python detectado.
    pip install rich --quiet
    echo  [OK] Libreria 'rich' lista.
)

REM ── Verificar Ollama ──────────────────────────────────────────────────────
curl.exe -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] ADVERTENCIA: Ollama no parece estar corriendo.
) else (
    echo  [OK] Ollama detectado y en linea.
)

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║       INSTALACION COMPLETADA CON EXITO               ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Ahora puedes usar el comando 'gravity' desde cualquier terminal.
echo  Prueba con: gravity "Hola, dime quien eres"
echo.
pause
exit /b 0
