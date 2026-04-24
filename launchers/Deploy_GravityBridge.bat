@echo off
title Deploy Gravity Bridge V12.0
cd /d "F:\Gravity_AI_bridge"
echo [GRAVITY AI V12.0] Iniciando Auditoria y Despliegue...
git add .
git commit -m "chore: Sistema estabilizado a V12.0. Clean up, fix React UI bugs, map backend POSTs"
git push origin main
echo [OK] Despliegue completado.
pause
