@echo off
title Gravity AI Bridge - Fooocus Studio UI
cd /d "%~dp0.."
echo [Gravity] Lanzando Fooocus Studio UI (Gradio)...
echo [INFO] Asegurate de que ComfyUI (ZLUDA) este corriendo en segundo plano.
python tools\fooocus_studio_ui.py
pause
