@echo off
:: =============================================================
:: Gravity AI Bridge V9.3.1 PRO - Fooocus CPU Launcher
:: Hardware: Ryzen 7 8700G (CPU mode - estable y sin crash)
:: Motor: Fooocus 2.5.5 con --always-cpu + --all-in-fp32
:: Puerto: 7861
:: Args validos verificados en ldm_patched/modules/args_parser.py
:: =============================================================
cd /d "%~dp0"

echo.
echo  [Gravity] Iniciando Fooocus V2.5.5 en modo CPU...
echo  [Gravity] Puerto: 7861 - Startup en: 60-90 segundos
echo  [Gravity] Generacion por imagen: 3-8 min (CPU/fp32, sin crash)
echo.

.\python_embeded\python.exe -s Fooocus\entry_with_update.py ^
    --always-cpu ^
    --all-in-fp32 ^
    --disable-async-cuda-allocation ^
    --port 7861 ^
    --disable-in-browser ^
    --disable-analytics

pause
