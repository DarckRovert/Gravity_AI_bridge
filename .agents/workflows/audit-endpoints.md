---
description: Auditoría empírica de todos los endpoints de LLM configurados en Gravity AI. Verifica cuáles modelos están vivos, muertos o descontinuados (HTTP 410/404) y purga automáticamente los inoperativos.
---
// diagnostic-mode: mythos-aggressive
// goal: empirical-endpoint-validation

1. **Extracción del Mapa de Providers**
   Lee `F:\Gravity_AI_bridge\providers\cloud\openai_compat_providers.py` usando `view_file`. Construye mentalmente el mapa completo de `{provider: [modelos]}` que está actualmente en el código. No asumas que ya lo sabes; léelo.

2. **Ejecución del Script de Auditoría Empírica**
   Escribe un script Python temporal en el directorio `scratch/` del artefacto de conversación. El script debe:
   - Importar `KeyManager` desde `F:\Gravity_AI_bridge\core\key_manager.py`.
   - Para cada proveedor con API key configurada, hacer un `POST /chat/completions` con `max_tokens: 1` a cada uno de sus modelos.
   - Clasificar cada modelo como `VIVO (200)`, `MUERTO (4xx/5xx)` o `SKIP (sin key)`.
   - Guardar los resultados en un JSON en `scratch/audit_results.json`.
   Ejecuta el script con `run_command`.

3. **Root-Cause del Modelo Muerto**
   Si algún modelo devuelve 410 Gone o 404 Not Found, es que fue descontinuado por el proveedor. Usa `grep_search` para localizar el nombre exacto del modelo en `openai_compat_providers.py` y confirma que coincide con el modelo fallido.

4. **Purga Quirúrgica**
   Usa `replace_file_content` para eliminar del array `_available_models` de la clase correspondiente cada modelo inoperativo confirmado. No modifiques nada más. No añadas comentarios innecesarios.

5. **Verificación Final**
   Compila el archivo modificado con `python -m py_compile` para confirmar integridad sintáctica. Reporta el resultado final en forma de tabla: modelos eliminados vs modelos que sobrevivieron.
