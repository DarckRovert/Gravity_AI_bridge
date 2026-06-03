# Arquitectura del Sistema (Deep-Dive)

Gravity está dividido en capas interconectadas:

## 1. El Puente de IA (`ask_deepseek.py` / `model_client.py`)
Responsable de extraer anclajes visuales, escribir guiones dinámicos (`script_builder.py`) e invocar los promts para generadores de imagen de fallback. Utiliza un esquema de Rate-Limit nativo (Exponential Backoff) para evitar bloqueos por APIs externas.

## 2. El Pipeline de Video (`pipeline.py`)
El corazón del ecosistema. Determina dinámicamente si el `job` es tradicional o puramente matemático:

### Ruta Tradicional (AI-First)
1. Invoca Fooocus o Pollinations para generar fondos consistentes.
2. Descarga TTS y Subtítulos (Whisper).
3. Corta y anima con FFMPEG.

### Ruta Demoscene V17 (Matemática Pura)
Diseñada exclusivamente para Music Videos (`job_type = "music"`):
1. Omite completamente la IA 2D.
2. Analiza las frecuencias del espectro con `audio_analyzer.py` (Graves, Medios, Agudos).
3. Inyecta la matriz multi-banda directamente en un fragment shader de GLSL (`glsl_renderer_v13.py`).
4. Compila el video y exporta la versión *Máster Horizontal* y luego la _recorta inteligentemente_ a un Short *Vertical 9:16*.

## 3. Escudo OAuth2 (Persistencia)
Ubicado en `youtube_uploader.py`. Valida la salud de los `refresh_tokens`. Si detecta `invalid_grant`, frena las peticiones HTTP **sin matar el hilo de renderizado local**, garantizando que el usuario obtenga sus archivos MP4 físicos.
