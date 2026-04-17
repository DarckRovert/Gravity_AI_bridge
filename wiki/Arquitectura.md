# Arquitectura — Gravity AI Bridge V10.0

## Visión General

Gravity AI Bridge es un **micro-kernel de IA** que actúa como proxy universal OpenAI-compatible.
No reemplaza los motores de IA: los orquesta.

```
Cliente (Continue.dev / Aider / Cursor / SPA Web)
          │
          ▼  HTTP POST /v1/chat/completions
   ┌──────────────────────────┐
   │   bridge_server.py       │  ← ThreadingHTTPServer (puerto 7860)
   │   GravityBridgeHandler   │
   └──────────┬───────────────┘
              │
     ┌────────▼────────┐
     │ provider_manager │  ← scan_all() + get_best() + stream()
     └────────┬─────────┘
              │
    ┌─────────┴──────────┐
    │  Proveedor Activo  │  ← LM Studio / Ollama / KoboldCPP / Jan / Cloud
    └────────────────────┘
```

## Módulos Core

### bridge_server.py
HTTP handler principal. Gestiona **29 endpoints** (GET + POST) y delega a módulos core.
Inicia los módulos background en `run_server()`: security_monitor, image_queue, engine_watchdog, ai_process_manager.

### provider_manager.py
Escanea puertos locales y conecta proveedores activos. Implementa la lógica de selección del mejor proveedor por latencia y disponibilidad. Ejecutado en segundo plano cada 30 segundos.

### engine_watchdog.py
Hilo demonio que monitorea el motor activo y realiza auto-switch si falla.
Soporta modo LOCKED (selección manual desde CLI o Dashboard).
Endpoints: `GET /v1/watchdog`, `POST /v1/watchdog/unlock`.

### hardware_profiler.py
Detección de GPU (ROCm/CUDA/Vulkan/CPU), VRAM, RAM del sistema, NPU (Ryzen AI).
Calcula el `num_ctx` óptimo según VRAM y cuantización del modelo.
Endpoint: `GET /v1/hardware`.

### cost_tracker.py
Registra costes USD en `_cost_log.json` solo para proveedores cloud.
Soporta límite diario configurable con alerta cuando se supera.
Endpoint: `GET /v1/cost`.

### multi_agent.py
Orquestador paralelo: envía el mismo prompt a N modelos simultáneamente.
Modos: `parallel` (comparativa libre) y `vote` (consenso por scoring).
Endpoint: `POST /v1/agent/compare`.

### session_manager.py
Gestión de sesiones conversacionales con persistencia JSON en `_saves/`.
Soporta fork de branches para exploración de variantes de conversación.
Endpoints: `GET /v1/sessions`.

### mcp_adapter.py
Implementa el cliente MCP (JSON-RPC sobre stdio). Conecta con servidores MCP externos
como `@modelcontextprotocol/server-filesystem` o `@modelcontextprotocol/server-github`.

### security_monitor.py
Escaneo Zero-Trust en background. Monitorea intentos de acceso, rate limiting abusivo,
y genera alertas en el panel Security del Dashboard.

### deploy_manager.py
Pipeline `npm run build` → `netlify deploy --prod`. Estado accesible en `GET /v1/deploy/status`.

### ai_process_manager.py
Auto-descubrimiento y gestión lifecycle de motores locales (LM Studio, Ollama, Fooocus, Jan).
Endpoints: `POST /v1/ai/start`, `POST /v1/ai/stop`.

### rag/ (Retrieval Augmented Generation)
Motor de búsqueda semántica sobre documentos locales. Usa embeddings locales.
Índice almacenado en `_rag_index/`. Endpoint de estado: `GET /v1/rag/status`.

## Flujo de una Request de Chat

```
1. POST /v1/chat/completions
2. rate_limiter.check_access(ip, api_key)
3. Inyección de personalidad desde _knowledge.json (si no hay system prompt)
4. provider_manager.get_best() → selecciona proveedor
5. record_request() + record_tokens(input)
6. stream() o complete() al proveedor seleccionado
7. ReasoningStripper filtra el reasoning interne (<think>...</think>)
8. record_latency() + CostTracker.record() + audit_logger.record()
```

## Seguridad

- **Rate Limiting** — configurable por IP y API key
- **Zero-Trust Monitor** — escaneo de amenazas en background
- **DPAPI (Windows)** — API keys cifradas localmente (key_manager.py)
- **Audit Log** — `_audit_log.jsonl` con cada request trazada

## Dashboard — 17 Paneles

| Panel | Módulo Backend | Endpoint |
|:---|:---|:---|
| Chat Auditor | provider_manager | POST /v1/chat/completions |
| Vision Studio | fooocus_client | GET /v1/fooocus/status |
| Image Queue | image_queue | GET /v1/queue |
| Deploy | deploy_manager | GET /v1/deploy/status |
| Game Servers | game_server_manager | GET /v1/gameserver/status |
| Multi-Agent | multi_agent | POST /v1/agent/compare |
| Hardware | hardware_profiler | GET /v1/hardware |
| Cost Center | cost_tracker | GET /v1/cost |
| Watchdog | engine_watchdog | GET /v1/watchdog |
| Sessions | session_manager | GET /v1/sessions |
| RAG | rag/retriever | GET /v1/rag/status |
| MCP Servers | mcp_adapter | Configuración local |
| Tools | tools/* | Uso desde CLI |
| System Status | metrics | GET /v1/status |
| Security | security_monitor | GET /v1/security |
| Audit Log | audit_logger | GET /v1/audit |
| Configuración | key_manager + config | POST /v1/keys |
