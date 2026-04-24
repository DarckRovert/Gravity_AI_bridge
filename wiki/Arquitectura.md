# Arquitectura — Gravity AI Bridge V12.1
**Omniscient-Tier Edition** · Última actualización: 2026-04-24

---

## Visión General

Gravity AI Bridge opera como un **micro-kernel de IA** que hace de proxy universal OpenAI-compatible. No es un reemplazo de los modelos de IA sino un **orquestador** que los gestiona, monitorea y expone como si fueran uno solo.

```
┌────────────────────────────────────────────────────────────────────┐
│                     CLIENTES (cualquier herramienta OpenAI-compat) │
│         Continue.dev / Aider / Cursor / React SPA / curl / Python  │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ HTTP POST /v1/chat/completions
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                    GRAVITY AI BRIDGE V12.1                         │
│                    bridge_server.py (~200 líneas — Orquestador)    │
│                    ThreadingHTTPServer :7860                        │
│                                                                    │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐    │
│  │   api/state.py       │  │   api/routes/                    │    │
│  │   Rate Limiter State │  │   mixin_get.py  (GET endpoints)  │    │
│  │   GeoIP Tracker      │  │   mixin_post.py (POST + LLM)     │    │
│  └──────────────────────┘  └──────────────────────────────────┘    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   provider_manager                           │  │
│  │   scan_all() → get_best() → stream() / complete()           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │             core/session_runner.py (V12.1)                   │  │
│  │   CapacityWake() + SessionSpawner (Multi-session parallel)   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────┬──────────────────────────────────────────┘
                          │
         ┌────────────────┼───────────────────┐
         ▼                ▼                   ▼
   ┌──────────┐     ┌──────────┐        ┌──────────┐
   │  LOCAL   │     │  LOCAL   │        │  CLOUD   │
   │  Ollama  │     │ LM Studio│        │Anthropic │
   │  :11434  │     │  :1234   │        │ OpenAI   │
   └──────────┘     └──────────┘        └──────────┘
```

---

## Principios de Diseño

| Principio | Implementación |
|:---|:---|
| **Local-First** | Los proveedores locales tienen prioridad sobre cloud en la selección automática |
| **Zero-Trust** | Rate limiting, API key whitelist, escaneo de amenazas en background |
| **Micro-Kernel** | `bridge_server.py` solo orquesta. Cada funcionalidad es un módulo independiente con Mixins |
| **Hot-Reload** | El Dashboard HTML se lee desde disco en cada request (sin reiniciar el servidor) |
| **Fault Tolerant** | Si un proveedor falla, el Watchdog hace auto-switch en máximo 30 segundos |

---

## Estructura de Directorios

```
F:\Gravity_AI_bridge\
│
├── bridge_server.py          ← Orquestador HTTP (~200 líneas, V12.1.0)
├── frontend/                 ← Frontend React/Vite (Reemplaza dashboard.py)
├── ask_deepseek.py           ← CLI interactivo del auditor
├── gravity_launcher.pyw      ← Launcher silencioso (sin consola)
├── gravity_tray.py           ← Icono de bandeja del sistema
├── make_icon.py              ← Generador del .ico
├── INSTALAR.py               ← Asistente de configuración inicial
├── health_check.py           ← Health check standalone
│
├── api/                      ← Capa de enrutamiento modular (V12.1.0)
│   ├── state.py              ← Estado global: Rate Limiter + GeoIP Tracker
│   └── routes/
│       ├── mixin_get.py      ← 20+ endpoints GET (dashboard, status, métricas)
│       └── mixin_post.py     ← Endpoints POST + lógica LLM (stream/complete)
│
├── core/                     ← Módulos del micro-kernel (29 módulos)
│   ├── provider_manager.py   ← Escaneo y selección de proveedores
│   ├── engine_watchdog.py    ← Auto-switch con lock/unlock
│   ├── hardware_profiler.py  ← GPU/VRAM/NPU detection
│   ├── cost_tracker.py       ← Tracking USD para cloud
│   ├── multi_agent.py        ← Orquestador parallel/vote
│   ├── session_manager.py    ← Sesiones con fork de branches + MemDir (V11.0)
│   ├── session_runner.py     ← Multi-Session spawners y CapacityWake (V11.0)
│   ├── mcp_adapter.py        ← Model Context Protocol client con Reconexión (V11.0)
│   ├── security_monitor.py   ← Zero-Trust scanning en background
│   ├── rate_limiter.py       ← Control de acceso por IP/key
│   ├── audit_log.py          ← Log inmutable de peticiones
│   ├── key_manager.py        ← DPAPI — cifrado de API keys
│   ├── config_manager.py     ← Lectura de config.yaml
│   ├── deploy_manager.py     ← Pipeline npm build + netlify
│   ├── ai_process_manager.py ← Start/stop de motores locales
│   ├── image_queue.py        ← Cola de generación de imágenes
│   ├── game_server_manager.py← Control vMaNGOS WoW
│   ├── model_selector.py     ← Selección por tipo de tarea
│   ├── turbo_kv.py           ← Optimización KV-Cache (ROCm/CUDA)
│   ├── ide_integrator.py     ← Configurador de IDEs
│   ├── reasoning_stripper.py ← Elimina bloques <think>...</think>
│   ├── data_guardian.py      ← Guardián del _knowledge.json
│   ├── metrics.py            ← Prometheus metrics
│   └── logger.py             ← Logger centralizado
│
├── providers/                ← Plugins de proveedores
│   ├── local/                ← ollama, lmstudio, kobold, jan, lemonade
│   └── cloud/                ← anthropic, openai, gemini, groq, mistral
│
├── tools/                    ← Herramientas del agente
│   ├── code_runner.py        ← Ejecución aislada de código
│   ├── file_edit_v2.py       ← Edición con patch diff
│   ├── git_tool.py           ← Operaciones git programáticas
│   ├── grep_tool.py          ← Búsqueda regex en filesystem
│   ├── web_search.py         ← DuckDuckGo sin API key
│   ├── native_trigger.py     ← Notificaciones del SO
│   └── fooocus_client.py     ← Cliente HTTP para Fooocus
│
├── rag/                      ← Retrieval Augmented Generation
│   ├── indexer.py            ← Generación de embeddings y chunks
│   └── retriever.py          ← Búsqueda semántica vectorial
│
├── frontend/
│   ├── src/components/       ← 25 componentes React SPA interactivos (V12.1)
│   └── dist/                 ← Build de producción servido por bridge_server.py
│
├── installer/
│   ├── build_installer.bat   ← Build automatizado (PyInstaller + Inno Setup)
│   └── gravity_setup.iss     ← Script Inno Setup 6
│
├── wiki/                     ← Documentación del proyecto
├── assets/
│   └── gravity_icon.ico      ← Icono multi-resolución (256/128/64/48/32/16)
│
├── _saves/                   ← Sesiones guardadas (JSON)
├── _rag_index/               ← Índice vectorial RAG
├── _audit_log.jsonl          ← Log de peticiones (append-only)
├── _cost_log.json            ← Registro de costes
├── _settings.json            ← Estado persistente (model_locked, etc.)
├── _knowledge.json           ← Personalidad y reglas persistentes
├── _cache.sqlite             ← Cache de respuestas (SQLite WAL)
└── config.yaml               ← Configuración principal
```

---

## Flujo Detallado de una Petición de Chat

```
1. Cliente → POST /v1/chat/completions (con o sin Authorization header)
      │
2. rate_limiter.check_access(ip, api_key)
      │ → 429 si excede límite
      │
3. Inyección de personalidad (data_guardian.load_knowledge)
      │ Si no hay system prompt → inserta reglas de _knowledge.json
      │
4. Resolución de proveedor
      │ Si model == "gravity-bridge-auto" → provider_manager.get_best()
      │ Si model específico → buscar en scan_all() qué proveedor lo tiene
      │ → 503 si ningún proveedor disponible
      │
5. record_request(provider, model)
      │
6. Stream o Complete al proveedor
      │ stream=true  → Server-Sent Events (SSE) token por token
      │ stream=false → Respuesta JSON completa
      │
7. reasoning_stripper.process_chunk(text)
      │ Elimina bloques <think>...</think> del razonamiento interno
      │
8. record_tokens(input, output)
   record_latency(elapsed)
   CostTracker.record(usd)   ← Solo si proveedor cloud
   audit_logger.record(...)  ← Siempre
```

---

## Módulos Core — Referencia Técnica


### gravity_brain.py (V11)
**Responsabilidad:** Cerebro sistémico central. Consolida el estado total (Hardware, Procesos, Video, Imágenes, Seguridad) y lo inyecta como 'System Context' para orquestar acciones complejas desde una interfaz de chat. Permite que el LLM dispare comandos internos de la API.

### provider_manager.py
**Responsabilidad:** Descubrimiento y selección de proveedores.

Funciones clave:
- `scan_all()` → devuelve lista de `ProviderResult` con health status, latencia y modelos disponibles
- `get_best()` → retorna `(provider_name, model_name)` del proveedor más rápido y saludable
- `stream(messages, model, provider)` → genera chunks de texto en streaming
- `complete(messages, model, provider)` → retorna texto completo (sin streaming)

Ejecuta `scan_all()` cada 30 segundos en background para mantener el estado actualizado.

---

### engine_watchdog.py
**Responsabilidad:** Resiliencia del motor activo.

- **Modo AUTO-SWITCH**: evalúa proveedores periódicamente y cambia al mejor si el actual falla o degrada
- **Modo LOCKED**: respeta la selección manual del usuario, no cambia de motor
- El estado `model_locked` se persiste en `_settings.json`
- Endpoints: `GET /v1/watchdog`, `POST /v1/watchdog/unlock`

---

### hardware_profiler.py
**Responsabilidad:** Detección de hardware para optimización de inferencia.

Detecta automáticamente:
- **AMD ROCm**: busca GFX version y VRAM real via `/usr/bin/rocm-smi` o subprocess
- **NVIDIA CUDA**: interroga `nvidia-smi` y PyTorch si está disponible
- **iGPU**: detecta AMD Vega/RDNA iGPU y Intel Arc integradas
- **NPU Ryzen AI**: detecta el NPU de procesadores AMD modernos
- **Cálculo de `optimal_ctx`**: `(vram_mb * 1024 * 1024) / (2 * model_size_b * 1e9 / kv_layers)`

---

### cost_tracker.py
**Responsabilidad:** Registro de gastos en USD para proveedores cloud.

- Los costes se estiman según precio por 1M tokens de cada proveedor (configurable)
- Se acumulan en `_cost_log.json` con granularidad por proveedor y modelo
- Soporta límite diario configurable — alerta cuando se supera
- El `session_cost` se reinicia cuando se reinicia el Bridge; el `daily_cost` cuando pasa medianoche

---

### multi_agent.py
**Responsabilidad:** Orquestación paralela de múltiples modelos.

- **Modo `parallel`**: usa `threading.Thread` para enviar el mismo mensaje a N proveedores simultáneamente
- **Modo `vote`**: los N modelos responden, luego un modelo "juez" puntúa y selecciona la mejor
- Cada resultado incluye proveedor, modelo, respuesta, elapsed y vote_score si aplica

---

### session_manager.py
**Responsabilidad:** Persistencia de conversaciones con soporte de branches y MemDir (V11.0).

- Las sesiones se guardan como JSON en `_saves/<nombre>.json`
- Cada sesión contiene: nombre, branch, timestamp, historial completo de mensajes
- El fork crea una copia independiente de la sesión en una rama nueva
- **MemDir (V11.0)**: Inyección dinámica de contexto (archivos `.gravity_mem` y `MEMORY.md`) directo al System Prompt simulando una "memoria de directorio" sin coste extra de RAG vectorial.

---

### session_runner.py (V11.0)
**Responsabilidad:** Orquestación Multi-sesión paralela.

- Define `CapacityWake` para señalización de subprocesos y control de carga.
- Exporta `SessionSpawner` para levantar un agente de CLI aislado (`ask_deepseek.py --session`) sin colisionar el bridge principal.

---

### mcp_adapter.py
**Responsabilidad:** Cliente del Model Context Protocol.

- Implementa JSON-RPC 2.0 sobre stdin/stdout con el proceso del servidor MCP
- Métodos: `connect()`, `call_tool(name, args)`, `list_tools()`, `disconnect()`
- Cada servidor MCP configurado en `config.yaml` se conecta como subproceso independiente

---

### turbo_kv.py
**Responsabilidad:** Optimización del KV-Cache para máxima eficiencia de VRAM.

Estrategia de cuantización por VRAM disponible:
| VRAM | Cuantización KV | Reducción | Calidad |
|:---|:---|:---|:---|
| < 10 GB | q4_0 | 4x | Ligera pérdida en contextos extremos |
| ≥ 10 GB | q8_0 | 2x | Near-lossless |
| TurboQuant (futuro) | ~3 bits | 6x | Google DeepMind (pendiente soporte en Ollama) |

Aplica via variables de entorno `OLLAMA_KV_CACHE_TYPE` y `OLLAMA_FLASH_ATTENTION=1`.

---

## Dashboard — 25 Componentes React V12.1

| # | Panel | Módulo Backend | Endpoints |
|:---|:---|:---|:---|
| 1 | 💬 Chat Auditor | provider_manager | POST /v1/chat/completions |
| 2 | 🏠 Mission Control | metrics + all | GET /v1/status, GET /v1/hardware |
| 3 | 🎨 Vision Studio | fooocus_client | GET /v1/fooocus/status, POST /v1/generate |
| 4 | 🖼️ Image Queue | image_queue | GET /v1/queue, POST /v1/queue/add |
| 5 | 🎥 Video Studio | video_pipeline | GET /v1/video/status, POST /v1/video/create |
| 6 | 🎨 Image Lab | image_lab | POST /v1/generate (modo lab) |
| 7 | 🎦 Largometraje | video_pipeline | POST /v1/video/create (100 escenas) |
| 8 | 🚀 Deploy | deploy_manager | GET /v1/deploy/status, POST /v1/deploy |
| 9 | ⚔️ Game Servers | game_server_manager | GET /v1/gameserver/status + 6 POST |
| 10 | 🤖 Multi-Agent | multi_agent | POST /v1/agent/compare |
| 11 | 🖥️ Hardware | hardware_profiler | GET /v1/hardware |
| 12 | 💰 Cost Center | cost_tracker | GET /v1/cost |
| 13 | ⚡ Watchdog | engine_watchdog | GET /v1/watchdog, POST /v1/watchdog/unlock |
| 14 | 💾 Sessions | session_manager + session_runner | GET /v1/sessions, POST /v1/sessions/spawn |
| 15 | 📚 RAG | rag/retriever | GET /v1/rag/status, POST /v1/rag/toggle |
| 16 | 🔌 MCP Servers | mcp_adapter | GET /v1/mcp/status, GET /v1/mcp/resource |
| 17 | 🛠️ Tools | tools/* | POST /v1/tools/run, /search, /git, /grep |
| 18 | ⚡ Tools Pro | tools/* | POST /v1/tools/run, /search, /git, /grep |
| 19 | 🕷️ Firecrawl | firecrawl_scraper | POST /v1/tools/scrape, GET /v1/tools/firecrawl/health |
| 20 | 🛡️ HITL Approval | hitl_manager | GET /v1/hitl/pending, POST /v1/hitl/approve, /reject |
| 21 | 📡 System Status | metrics + provider_manager | GET /v1/status, GET /metrics |
| 22 | 📄 Audit Log | audit_logger | GET /v1/audit, POST /v1/audit/rotate |
| 23 | ⚙️ Configuración | key_manager + ide_integrator | POST /v1/keys, GET /v1/security |

---

## Sistema de Seguridad

### Rate Limiting
- Por IP: máximo de requests por ventana de tiempo (configurable en `config.yaml`)
- Por API key: si se configura whitelist, solo las keys autorizadas pasan
- Respuesta: `429 Too Many Requests` con razón

### DPAPI (Windows Data Protection API)
- Las API keys de proveedores cloud se cifran con la identidad del usuario de Windows
- Solo el mismo usuario en el mismo equipo puede descifrar las keys
- Las keys nunca se almacenan en texto plano en ningún archivo

### Audit Log
- Cada petición queda registrada en `_audit_log.jsonl` (formato append-only)
- Incluye: timestamp, ip, proveedor, modelo, tokens, coste, latencia
- No se puede modificar retrospectivamente (diseño intencional)

### Zero-Trust Monitor
- Hilo background que escanea patrones de acceso anómalos
- Detecta: rate limiting abusivo, intentos de inyección de prompts, accesos a endpoints no autorizados
- Las alertas se muestran en el panel Security del Dashboard

---

## Empaquetado Comercial

### Proceso de Build
```
make_icon.py          → genera assets/gravity_icon.ico (multi-res: 256..16px)
      ↓
PyInstaller           → empaqueta Python + todas las dependencias → GravityBridge.exe
      ↓
Inno Setup 6          → crea Gravity_AI_Bridge_V11.0_Setup.exe
      ↓
gravity_launcher.pyw  → EXE sin consola que arranca bridge_server + gravity_tray
```

### Componentes del Instalador
| Archivo generado | Descripción |
|:---|:---|
| `dist/GravityBridge.exe` | Ejecutable standalone (no requiere Python) |
| `dist/Gravity_AI_Bridge_V12.1_Setup.exe` | Instalador completo para distribución |

### Características del Instalador
- Instala en `C:\Program Files\Gravity AI Bridge\`
- Crea acceso directo en el Escritorio (opcional)
- Crea entrada en el Menú de Inicio
- Autostart con Windows (opcional)
- Desinstalador completo incluido
- Requiere Windows 10 1809+ x64
