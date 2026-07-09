@echo off
chcp 65001 >nul
title GRAVITY AI - Reportero Perú
color 0C
cd /d "%~dp0.."
set "PYTHONPATH=%~dp0.."
echo ======================================================================
echo   INICIANDO GRAVITY AI - REPORTERO PERÚ (SKIN ESPECIALIZADO)
echo ======================================================================
echo.
echo Presiona CTRL + C en cualquier momento o simplemente CIERRA ESTA VENTANA
echo para pausar el agente y liberar los recursos de tu PC.
echo.
python news_daemon_peru.py
pause
