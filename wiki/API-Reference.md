# Referencia de API & Módulos V30.4 MYTHOS

## Nuevos Endpoints V30.4 MYTHOS

### `GET /v1/memory/graph`
Retorna la topología completa del Knowledge Graph en memoria construido por NetworkX a partir de `strategic_decisions` y `system_patterns` de `gravity_brain.db`.
- **Respuesta (200 OK)**:
  ```json
  {
    "nodes_count": 55,
    "edges_count": 90,
    "most_central_nodes": [{"node": "system", "score": 0.1804}, ...],
    "nodes": [{"id": "dec_1", "label": "Ciclo OODA...", "type": "decision", "score": 0.0121, "hits": 1}],
    "edges": [{"source": "dec_1", "target": "system", "relation": "belongs_to", "weight": 1}]
  }
  ```

### `POST /v1/sessions/delete`
Elimina de forma segura y permanente una sesión guardada del disco (`_saves/<session_id>.json`).
- **Payload**: `{"session_id": "session_12345"}`
- **Respuesta (200 OK)**: `{"ok": true, "session_id": "session_12345", "deleted": true}`

### `POST /v1/multi_agent/ask` (Debate & Consenso)
Orquesta votaciones y debates multi-modelo entre agentes concurrentes.
- **Payload**: `{"prompt": str, "models": list[str], "mode": "parallel" | "consensus" | "debate"}`
- **Respuesta (200 OK)**: `{"ok": true, "mode": "debate", "response": str, "debates": list}`

### `POST /v1/tools/scrape` (Firecrawl + RAG Indexer)
Extrae contenido de URLs y lo indexa vectorialmente de forma automática en la memoria RAG.
- **Payload**: `{"url": "https://...", "index_to_rag": true}`
- **Respuesta (200 OK)**: `{"ok": true, "markdown": str, "rag_indexed": true, "chunks": int}`

### `GET /v1/deploy/status` & `POST /v1/deploy/package`
Inspecciona herramientas del sistema (usando `shutil.which` resistente a codificaciones de consola de Windows) y permite compilar y desplegar carpetas de proyectos arbitrarias.

---

## `core/subagent_loader.py` (V30.3 Declarative Subagents)
Carga y valida dinámicamente definiciones declarativas de subagentes desde `.agents/agents/*.md`.
- `load_agent(filepath, force=False)`: Carga y cachea la estructura `AgentDefinition`. Normaliza UTF-8 BOM y CRLF. Re-parsea solo ante cambios en `mtime`.
- `discover_agents(agents_dir=AGENTS_DIR)`: Escanea el directorio `.agents/agents/` y devuelve un diccionario de agentes válidos indexados por su nombre.
- `get_agent(name)`: Devuelve la definición del agente especificado o `None`.

## `core/parallel_orchestrator.py` (V30.3 Shared Contract Protocol)
Despachador asíncrono no bloqueante para fan-out de tareas a subagentes en paralelo.
- `dispatch(goal, agent_names, task_per_agent=None, max_workers=6, on_complete=None)`: Retorna inmediatamente un `OrchestrationHandle` mientras ejecuta en segundo plano vía hilos daemon.
- `get_orchestration(orch_id)`: Consulta el estado en memoria de la orquestación.
- `list_orchestrations()`: Lista todas las orquestaciones activas y recientes (sujetas a limpieza automática TTL 3600s).

## Endpoints REST de Subagentes (`api/routes/`)
- `POST /v1/agents/dispatch`:
  - **Payload**: `{"goal": str, "agents": list[str], "task_per_agent": dict[str, str] (opcional)}`
  - **Respuesta (202 Accepted)**: `{"ok": true, "orchestration_id": str, "message": str}`
- `GET /v1/agents/list`:
  - **Respuesta (200 OK)**: `{"ok": true, "agents": [{"name": str, "description": str, "mode": str, "model": str, "provider": str}]}`
- `GET /v1/agents/status/<orch_id>`:
  - **Respuesta (200 OK / 404)**: `{"ok": true, "orchestration_id": str, "status": str, "agents": {...}}`

## `tools/gravity_delegate.py` (CLI & Python Bridge)
Herramienta universal de delegación y ahorro de tokens con fallback multinivel (LM Studio → Groq → Nvidia NIM).
- Parámetros CLI de inferencia simple: `python tools/gravity_delegate.py "<prompt>" --provider auto --model auto --json-out`
- Parámetros CLI paralelos V30.3: `python tools/gravity_delegate.py "<prompt>" --agents backend_specialist qa_tester --parallel`

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
