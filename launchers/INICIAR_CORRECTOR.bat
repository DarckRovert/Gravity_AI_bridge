@echo off
title Gravity :: Corrector Semantico
color 0A
echo.
echo  +------------------------------------------------------+
echo  ^|   Iniciando Corrector Semantico (176 archivos)       ^|
echo  +------------------------------------------------------+
echo.
cd /d "%~dp0.."
python corrector_semantico.py
echo.
echo Correccion finalizada. Puedes cerrar esta ventana.
pause
