@echo off
echo [V2V Engine] Arrancando Motor V2V en Tiempo Real...
cd /d "%~dp0"
call venv_v2v\Scripts\activate.bat
python v2v_pipeline.py
