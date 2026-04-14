@echo off
title GRAVITY AI -- FABRICA WEB V9.3.1 PRO (NEXT.JS)
color 0d
cls

REM ── Estandarización de directorio local ──────────────────────────────────────
cd /d "%~dp0.."

echo.
echo  +------------------------------------------------------------------------------+
echo  ^|         GRAVITY AI - FABRICA WEB V9.3.1 PRO [Diamond-Tier Edition]           ^|
echo  ^|                      Frontend Node.js / Next.js Server                       ^|
echo  +------------------------------------------------------------------------------+
echo.

REM ── Verificación de persistencia ─────────────────────────────────────────────
if not exist "F:\Gravity_AI_bridge\_integrations\FabricaWeb\package.json" (
    echo  [ERROR] FabricaWeb no fue encontrada en el anillo de integraciones.
    echo  Revisa la carpeta _integrations\FabricaWeb.
    pause
    exit /b 1
)

REM ── Liberación Obligatoria del Puerto 3000 ───────────────────────────────────
echo  [1/2] Escaneando puerto 3000 (React/Next.js)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo  [!] Destruyendo proceso zombi en puerto 3000 (PID: %%p)...
    taskkill /F /PID %%p >nul 2>&1
)

REM ── Inicialización Segura ───────────────────────────────────────────────────
echo  [2/2] Iniciando Node.js local (npm run dev)...
cd "_integrations\FabricaWeb"
start "Fabrica Web UI" "http://localhost:3000"
npm run dev

pause
