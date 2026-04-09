@echo off
cd /d "%~dp0"
title GRAVITY BRIDGE SERVER V9.0 PRO [Diamond-Tier Edition]
color 0b
cls

echo.
echo  +------------------------------------------------------------------------------+
echo  ^|          GRAVITY AI - BRIDGE SERVER V9.0 PRO [Diamond-Tier Edition]          ^|
echo  ^|                  Enrutador Local + Cloud OpenAI-Compatible                   ^|
echo  +------------------------------------------------------------------------------+
echo.
echo  Dashboard Web:  http://localhost:7860/
echo  API Endpoint:   http://localhost:7860/v1/chat/completions
echo  Metricas:       http://localhost:7860/metrics
echo  Estado:         http://localhost:7860/v1/status
echo.
echo  [Iniciando el servidor. Ctrl+C para detener]
echo.

python "%~dp0bridge_server.py"

echo.
echo  [Servidor detenido]
pause
