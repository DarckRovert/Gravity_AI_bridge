# Troubleshooting y FAQ

### 1. El portal de noticias tiene errores de decodificación JSON.
**Solución:** Revisa los logs de `task-*`. Puede ocurrir si un proveedor LLM falla y devuelve un JSON en un bloque markdown inesperado. El sistema ahora tiene un parche en `clean_llm_response()` para extraer y limpiar la salida.

### 2. Fooocus no arranca desde el `INICIAR_TODO.bat`
**Explicación:** Por defecto, Fooocus arranca en "modo manual" para ahorrar RAM (frecuentemente más de 12GB requeridos). Debes activarlo manualmente desde el Mission Control (L0).

### 3. Problemas de Push a Github en el Agente Periodístico
**Solución:** Verifica que el usuario local de Windows tenga las credenciales de Git cacheadas globalmente (`git config --global credential.helper wincred`).

### 4. Fallos al decodificar contenido de Web Search
**Explicación:** Si la búsqueda web retorna errores de Gzip o decodificación, revisa que no estés enviando headers de codificación (Accept-Encoding) incompatibles con `urllib`. La V16.0 PRO ya maneja esto limpiando cabeceras innecesarias.

### 5. Falla silenciosa al instalar faster-whisper
**Solución:** En V16.0 PRO, la instalación de dependencias como Whisper es de tipo "bloqueante" (`blocking`). Si notas errores de "módulo no encontrado" en la consola, verifica que el subprocess tenga permisos para instalar pip localmente sin detener la ejecución.
