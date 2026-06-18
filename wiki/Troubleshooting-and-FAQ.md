# Troubleshooting y FAQ

### 1. El portal de noticias tiene errores de decodificación JSON.
**Solución:** Revisa los logs de `task-*`. Puede ocurrir si un proveedor LLM falla y devuelve un JSON en un bloque markdown inesperado. El sistema ahora tiene un parche en `clean_llm_response()` para extraer y limpiar la salida.

### 2. Fooocus no arranca desde el `INICIAR_TODO.bat`
**Explicación:** Por defecto, Fooocus arranca en "modo manual" para ahorrar RAM (frecuentemente más de 12GB requeridos). Debes activarlo manualmente desde el Mission Control (L0).

### 3. Problemas de Push a Github en el Agente Periodístico
**Solución:** Verifica que el usuario local de Windows tenga las credenciales de Git cacheadas globalmente (`git config --global credential.helper wincred`).
