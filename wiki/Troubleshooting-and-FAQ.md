# Troubleshooting y FAQ

### 1. El portal de noticias tiene errores de decodificación JSON.
**Solución:** Revisa los logs de `task-*`. Puede ocurrir si un proveedor LLM falla y devuelve un JSON en un bloque markdown inesperado. El sistema ahora tiene un parche en `clean_llm_response()` para extraer y limpiar la salida.

### 2. Fooocus no arranca desde el `INICIAR_TODO.bat`
**Explicación:** Por defecto, Fooocus arranca en "modo manual" para ahorrar RAM (frecuentemente más de 12GB requeridos). Debes activarlo manualmente desde el Mission Control (L0).

### 3. Problemas de Push a Github en el Agente Periodístico
**Solución:** Verifica que el usuario local de Windows tenga las credenciales de Git cacheadas globalmente (`git config --global credential.helper wincred`).

### 4. Fallos al decodificar contenido de Web Search
**Explicación:** Si la búsqueda web retorna errores de Gzip o decodificación, revisa que no estés enviando headers de codificación (Accept-Encoding) incompatibles con `urllib`. La V30.0 MYTHOS ya maneja esto limpiando cabeceras innecesarias.

### 5. Dependencias de Audio y Faster-Whisper
**Explicación:** En V30.4 MYTHOS, se erradicaron las llamadas en caliente a `pip install` en tiempo de ejecución. Si `faster-whisper` no está instalado en el entorno Python activo, `youtube_analyzer.py` degrada limpiamente informando que Whisper no está disponible en lugar de bloquear el proceso del servidor.

### 6. Colisión de Puertos en V2V Studio (LivePortrait)
**Solución:** A partir de V30.4 MYTHOS, el motor V2V opera en el puerto dedicado `7863`, desacoplado totalmente de Fooocus UI (`7862`), erradicando colisiones de socket al renderizar animaciones faciales en tiempo real.

### 7. Ingestión RAG en Python 3.13 (`cgi.FieldStorage` deprecado)
**Explicación:** El endpoint `/v1/rag/ingest` utiliza el parser nativo de la biblioteca estándar `email.parser.BytesParser(policy=default)`, garantizando compatibilidad total con Python 3.13 sin requerir módulos obsoletos.
