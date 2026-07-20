@echo off
title Gravity News Portal - Servidor Web
color 0E

echo ==============================================================
echo   INICIANDO PORTAL FRONTAL DE NOTICIAS (GRAVITY NEWS)
echo ==============================================================
echo.
echo Iniciando servidor web de React/Vite...
echo Por favor, no cierres esta ventana mientras leas las noticias.
echo.

cd /d "%~dp0..\..\gravity-news-portal"
npm run dev
