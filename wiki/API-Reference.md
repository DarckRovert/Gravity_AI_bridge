# Referencia de API

## `core/provider_manager.py`
Módulo clave para la comunicación con múltiples proveedores de LLM.
- `complete(messages, provider=None, model=None, options=None)`
- Conoce y enruta peticiones hacia LM Studio local, Ollama, Nvidia NIM, Groq, y OpenAI, con manejo de fallback en caso de `401 Unauthorized`.

## `core/autonomy_engine.py`
Núcleo del agente CEO.
- `run_ooda_cycle()`: Ejecuta la lectura del estado (Observe), clasifica alertas (Orient), determina acciones con LLM (Decide), ejecuta tareas de bajo riesgo (Act) y actualiza la base de conocimiento (Learn).

## `gravity_reporter.py`
Ejecución del periodista.
- Argumentos: `--topic "..."`, `--focus "..."`.
- Fallbacks automáticos entre motores.
