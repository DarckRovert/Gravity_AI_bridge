# Arquitectura — Gravity AI Bridge V9.0 PRO [Diamond-Tier Edition]

## Visión General

Gravity AI Bridge es un **enrutador universal de IA** que actúa como capa de abstracción entre el usuario/IDE y múltiples motores de IA (locales y cloud). Expone una API 100% compatible con OpenAI, permitiendo usar cualquier cliente existente sin modificaciones.

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE PRESENTACIÓN                        │
│  CLI (ask_deepseek.py) │ Dashboard SPA │ IDEs (Cursor/VS Code)  │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP / stdin / OpenAI API
┌────────────────▼────────────────────────────────────────────────┐
│                    BRIDGE SERVER (bridge_server.py)              │
│  • Enrutamiento dinámico por latencia/disponibilidad             │
│  • Rate Limiting (IP + API Key)                                  │
│  • Streaming SSE / JSON non-stream                               │
│  • ReasoningStripper (filtro de tags <think>)                    │
└────────────────┬────────────────────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │  Provider Manager│
        │  (provider_manager.py)                                   │
        │  scan_all() → get_best() → stream()/complete()           │
        └────────┬─────────┘
    ┌────────────┼─────────────────────────────────┐
    │            │                                 │
┌───▼───┐   ┌───▼───┐                      ┌──────▼─────┐
│ Local │   │ Cloud │                      │    RAG     │
│Ollama │   │OpenAI │                      │ Retriever  │
│LMStud │   │Anthr. │                      │ BM25+Vec.  │
│ vLLM  │   │Google │                      └────────────┘
│Kobold │   │ Groq  │
└───────┘   └───────┘
```

## Módulos Principales

### `ask_deepseek.py` — CLI / Auditor Senior
- **AuditorCLI**: Clase principal del CLI con 20+ comandos.
- **SettingsManager**: Wrapper de ConfigManager para compatibilidad.
- **ReasoningStripper**: Filtra bloques `<think>` del streaming.
- **first_run_check()**: Wizard de onboarding (solo primera ejecución).

### `bridge_server.py` — Servidor HTTP
- `ThreadingHTTPServer` con soporte CORS completo.
- Sirve la SPA del dashboard en `/` y `/dashboard`.
- Endpoints: `/v1/chat/completions`, `/v1/models`, `/v1/status`, `/v1/audit`, `/v1/keys`, `/metrics`, `/health`.

### `dashboard.py` — SPA Web
- HTML/CSS/JS puro, sin dependencias externas.
- Chat con streaming SSE en tiempo real.
- Tabs: Chat · Estado · Audit Log · Configuración.

### `provider_manager.py` — Orquestador
- `scan_all()`: Escanea todos los backends en paralelo (RTO).
- `get_best()`: Selecciona el proveedor con menor latencia TTFT.
- `stream()` / `complete()`: Unifica la interfaz de todos los proveedores.

### `core/` — Infraestructura

| Módulo | Responsabilidad |
|--------|----------------|
| `config_manager.py` | Lee/escribe `config.yaml`. Migración desde `_settings.json`. |
| `audit_log.py` | Audit log JSONL append-only. `AuditLogger.record()` y `get_recent()`. |
| `logger.py` | Logger estructurado JSON. Sanitización de API Keys. |
| `metrics.py` | Contadores Prometheus. `record_request/tokens/latency/error()`. |
| `rate_limiter.py` | Rate limiting por IP y API Key con ventana deslizante. |
| `mcp_adapter.py` | Adaptador MCP stdio (JSON-RPC 2.0). |
| `verification_agent.py` | Auditoría adversarial de código. Detecta patrones de riesgo. |

### `providers/` — Sistema de Plugins

```
providers/
├── base.py          ← BaseProvider, ProviderResult
├── registry.py      ← Registro y descubrimiento de plugins
├── local/           ← Ollama, LM Studio, vLLM, KoboldCPP, etc.
└── cloud/           ← OpenAI, Anthropic, Google, Groq, Cohere
```

Cada proveedor hereda de `BaseProvider` e implementa:
- `scan() → ProviderResult`: Detecta disponibilidad y modelos.
- `stream(messages, model, options) → Iterator[str]`: Streaming token a token.
- `complete(messages, model, options) → str`: Respuesta completa.

### `rag/` — Motor RAG Híbrido

- **Indexación**: Fragmenta documentos en chunks, genera embeddings (CPU/GPU/NPU).
- **Recuperación**: BM25 (palabra clave) + similitud vectorial (semántica).
- **Inyección**: El contexto relevante se prepende al prompt del usuario.

### `tools/` — Herramientas del Agente

| Herramienta | Función |
|-------------|---------|
| `FileEditV2` | Edición quirúrgica por bloques exactos (Claw Edition). |
| `CodeRunner` | Ejecuta bloques de código (Python, JS, PowerShell, Bash). |
| `WebSearch` | DuckDuckGo scraping + Brave Search API. |
| `GitTool` | status, log, diff, branch, stash. |
| `FileOpsTool` | backup, diff, apply_patch. |

## Flujo de una Petición

```
1. Usuario escribe mensaje en CLI o POST /v1/chat/completions
2. Rate Limiter verifica IP/Key (→ 429 si excede)
3. Provider Manager selecciona el mejor backend disponible
4. Cache Engine: ¿hit? → respuesta inmediata
5. stream() / complete() → chunks de texto
6. ReasoningStripper filtra <think> tags
7. Respuesta mostrada/enviada al cliente
8. Audit Logger registra: tokens, latencia, coste
9. Prometheus metrics actualizadas
10. Cache Engine almacena para futuras peticiones
```

## Configuración (`config.yaml`)

```yaml
profile: production  # production | development

server:
  host: 0.0.0.0
  port: 7860
  log_level: INFO

model:
  default_provider: "ollama"
  default_model: "deepseek-r1:14b"
  ctx_size: 32768
  temperature: 0.6
  stream: true

cache:
  enabled: true
  ttl_hours: 24

rate_limit:
  enabled: true
  requests_per_minute: 60
```

## Decisiones de Diseño

| Decisión | Razón |
|----------|-------|
| HTTP puro (sin Flask) | Cero dependencias extra, portabilidad máxima |
| JSONL para audit log | Append-only garantizado, lectura incremental |
| DPAPI para keys | Cifrado nativo de Windows sin dependencias |
| Rich para CLI | Terminal premium sin implementación custom |
| BM25 + vectorial | Mejor recall que solo semántico en código |
| ThreadingHTTPServer | Concurrencia sin async, compatible con Python 3.10+ |
