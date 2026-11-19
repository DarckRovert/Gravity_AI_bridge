@echo off
echo [V2V Engine] Arrancando Servidor WebSocket V2V en Puerto 7863...
cd /d "%~dp0"
if exist venv_v2v\Scripts\activate.bat (
    call venv_v2v\Scripts\activate.bat
)
python v2v_server.py
