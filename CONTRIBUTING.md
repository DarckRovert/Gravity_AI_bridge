# Contribuir al Ecosistema DarckRovert

Gracias por interesarte en la estabilidad del Gravity AI Bridge. Si deseas ayudar al desarrollo de la capa asíncrona de LLMs de este proyecto, te solicitamos obedecer estrictamente este protocolo, fundado en la metodología corporativa de DarckRovert.

## Estilo y Mentalidad
1. **Idioma Local-Primero:** Cada variable, comentario de clase (`""" """`), y discusión en Pull Request (PR) o Issue DEBE estar en Español, con tecnicismos respetados (por ejemplo, Threads, Queues, etc). 
2. **Nada De Dependencias Externas Masivas:** Este puente se pavimentó bajo la base nativa `http.server`. Evita subir librerías web como Flask, FastAPI o Django, el Bridge vive del peso nulo y sub-hilos de Python.
3. **Cero Placeholders:** Envíos de código sugerido en reportes no deben ser abstracciones (`// ... resto del codigo`). Presenta algoritmos listos para inyección en el Core.
4. **Respeto VRAM:** Ningún PR puede intentar forzar bloqueos perezosos sobre la VRAM; el LLM debe obedecer siempre la directriz de `core/env_optimizer.py`.

## Cómo Reportar o Proponer un Desarrollo
Tu reporte debe tener:
- Confirmación de Testeo Físico y visual de la métrica (Ollama, Fooocus Output).
- Versionamiento explícito (ej: Evaluado bajo la V10.1 en entornos Windows 10/11).
- Lectura de tu STDOUT buffer (capturado del log real-time `/v1/audit`).

El equipo base se adjudica la completa autorización de silenciar PRs que no encajen en el Roadmap de los transmisiones directas de [Twitch.tv/darckrovert](https://twitch.tv/darckrovert).
