# Troubleshooting y Preguntas Frecuentes

## Problema: Fooocus no arranca o se cuelga
**Síntoma:** El log arroja _Fooocus offline_ e intenta hacer fallback a Pollinations infinitamente hasta que te bannean con HTTP 402.
**Solución:** Si intentabas renderizar un Motor Matemático (V17), asegúrate de que su ID de estilo (ej. `turing_patterns`) esté debidamente registrado en `CINEMA_STYLES` dentro de `script_builder.py` y en la lista de intercepción GLSL en `pipeline.py`.

## Problema: El sistema dice "OAUTH_ERROR detectado"
**Causa:** Tu cuenta de Google en modo "En pruebas" ha revocado los tokens tras 7 días.
**Qué hace el sistema:** Gravity continuará renderizando en local pero abortará el envío a la nube de forma segura.
**Solución Real:** Generar un nuevo token en tu consola y sustituir `youtube_oauth.json`.

## Problema: FFmpeg no se reconoce
**Solución:** Gravity integra un binario FFMPEG en la ruta `_integrations\ffmpeg\ffmpeg.exe`. Si tu script usa subprocess globalmente para el comando `ffmpeg` en lugar de la constante `FFMPEG_EXE`, fallará si tu PC no lo tiene en el PATH de Windows.
