@echo off
REM -- Instalar dependencias criticas silenciosamente ---
python -m pip install rich pyfiglet pyreadline3 --quiet >nul 2>&1
python "%~dp0ask_deepseek.py" %*
