@echo off
chcp 65001 >nul
title GRAVITY AI - Reportero Autonomo
color 0A
cd /d "%~dp0.."
set "PYTHONPATH=%~dp0.."
echo ======================================================================
echo   INICIANDO GRAVITY AI - REPORTERO WEB
echo ======================================================================
echo.
echo Presiona CTRL + C en cualquier momento o simplemente CIERRA ESTA VENTANA
echo para pausar el agente y liberar los recursos de tu PC.
echo.
python news_daemon.py
pause
