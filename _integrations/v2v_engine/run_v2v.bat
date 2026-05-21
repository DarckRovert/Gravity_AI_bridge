@echo off
title Gravity AI - V2V Engine (AMD DirectML)
cd /d "%~dp0"

echo ---------------------------------------------------
echo Inicializando Entorno Virtual Aislado para DirectML
echo ---------------------------------------------------

call env\Scripts\activate.bat

echo Ejecutando Pipeline V2V...
python v2v_pipeline.py

pause
