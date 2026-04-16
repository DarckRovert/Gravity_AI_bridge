# Arquitectura — Gravity AI Bridge V10.0 [Ecosistema Total]

## Visión General

Gravity AI Bridge es un **enrutador universal de IA** que actúa como capa de abstracción entre el usuario/IDE, múltiples motores de IA (locales y cloud), y el entorno local (gestión de servidores, archivos estáticos, despliegues y seguridad).

```
┌────────────────────────────────────────────────────────────────────────┐
│                          CAPA DE PRESENTACIÓN                          │
│ CLI (ask_deepseek.py) │ Dashboard SPA (web/) │ IDEs (Cursor/VSCode/etc)│
│                        │ Fooocus Studio UI    │                        │
└──────────────┬─────────────────────────┬───────────────────────────────┘
               │ HTTP / stdin / OpenAI   │ Gradio / HTTP / SSE
┌──────────────▼─────────────────────────┴───────────────────────────────┐
│                    BRIDGE SERVER (bridge_server.py)                    │
│ • Enrutamiento latencia TTFT       • Model Context Protocol (MCP)      │
│ • Rate Limiting IP + API Key       • Streaming SSE / JSON              │
│ ┌────────────────┐ ┌──────────────┐ ┌───────────────┐ ┌──────────────┐ │
│ │Security Monitor│ │ Image Queue  │ │Deploy Manager │ │ Game Server  │ │
│ │(puertos/hashes)│ │ (SQLite DB)  │ │ (npm/netlify) │ │ (WoW MaNGOS) │ │
│ └────────────────┘ └─────┬────────┘ └───────────────┘ └──────┬───────┘ │
└──────────────┬───────────│───────────────────────────────────│─────────┘
               │           │                                   │
      ┌────────▼────────┐  │  ┌──────────────────────────┐  ┌──▼──────────┐
      │ Provider Manager│  └──► Fooocus Motor CPU (7861) │  │ mangosd.exe │
      │ get_best()      │     │ JuggernautXL SDXL        │  │ realmd.exe  │
      └──────┬──────────┘     └──────────────────────────┘  └─────────────┘
   ┌─────────┼─────────────────┐
   │         │                 │
┌──▼──┐  ┌──▼──┐         ┌────▼────┐
│Local│  │Cloud│         │  RAG    │
│Ollam│  │OpenA│         │BM25+Vec │
│LMStu│  │Anthr│         └─────────┘
│vLLM │  │Googl│
└─────┘  └─────┘
```

---

## Módulos Principales

### `ask_deepseek.py` — CLI / Auditor Senior
- **AuditorCLI**: Clase principal con 20+ comandos.
- **SettingsManager**: Wrapper de ConfigManager.
- **ReasoningStripper**: Filtra bloques `<think>` del stream.
- **first_run_check()**: Wizard de onboarding (solo primera vez).

### `bridge_server.py` — Servidor HTTP
- `ThreadingHTTPServer` con soporte CORS completo.
- Sirve `web/dashboard.html` en `/` y `/dashboard`.
- Sirve imágenes desde `_integrations/Fooocus/Fooocus/outputs/` en `/static/output/`.
- Endpoints: `/v1/chat/completions`, `/v1/models`, `/v1/status`, `/v1/audit`, `/v1/keys`, `/v1/images`, `/metrics`, `/health`.

### `dashboard.py` — Servidor de Hot-Reload (Opcional)
- Servidor HTTP de utilería (reemplazado en V10 por el interno de Bridge Server).
- Lee `web/dashboard.html` dinámicamente desde disco sin reiniciar el Bridge.

### `web/dashboard.html` — SPA V10.0
- HTML/CSS/JS puro en un solo archivo.
- 9 paneles: Chat, Vision, Queue, Deploy, Game Servers, Status, Security, Audit Log, Config.
- Polling optimizado (sólo escanea los endpoints del panel activo).

### `tools/fooocus_studio_ui.py` — Vision Studio
- Interfaz Gradio que replica la UX de Fooocus.
- Puerto 7862 (configurable via `GRADIO_SERVER_PORT`).
- `get_all_images()` + `get_newest_image()`: Detección correcta de imágenes nuevas por set-difference de paths absolutos.
- Cold-Start detection: timeouts incrementados y polling resiliente a 15 min en modo CPU.

### `tools/fooocus_client.py` — Cliente Fooocus
- Comunicación HTTP con el motor en `127.0.0.1:7861`.
- Workflow SDXL puro en CPU usando sampler `euler` que previene el system crash de DirectML.

### `provider_manager.py` — Orquestador
- `scan_all()`: Escanea todos los backends en paralelo.
- `get_best()`: Selecciona el proveedor con menor latencia TTFT.
- `stream()` / `complete()`: Interfaz unificada.

### `core/` — Infraestructura (26 módulos)

| Módulo | Responsabilidad |
|--------|----------------|
| `config_manager.py` | Lee/escribe `config.yaml`. |
| `security_monitor.py` | (V10) Monitoreo de procesos, puertos permitidos e integridad SHA-256. |
| `image_queue.py` | (V10) Cola SQLite de generación de imágenes sin bloqueo. |
| `game_server_manager.py` | (V10) Gestión de servidores de juego (WoW MaNGOS). |
| `deploy_manager.py` | (V10) CI/CD local npm → Netlify. |
| `audit_log.py` | Audit log JSONL append-only. |
| `logger.py` | Logger estructurado JSON. Sanitización de keys. |
| `metrics.py` | Contadores Prometheus. |
| `rate_limiter.py` | Rate limiting por IP y API Key con ventana deslizante. |
| `mcp_adapter.py` | Adaptador MCP stdio (JSON-RPC 2.0). |
| `verification_agent.py` | Auditoría adversarial de código. |
| `cache_engine.py` | Cache SQLite WAL con TTL configurable. |
| `key_manager.py` | Cifrado/descifrado DPAPI de API Keys. |
| `session_manager.py` | Guardar/cargar/exportar sesiones de chat. |
| `hardware_profiler.py` | Detección CPU/GPU/NPU/RAM. |
| `model_selector.py` | Selección del modelo óptimo por capacidad/hardware. |

### `providers/` — Sistema de Plugins

```
providers/
├── base.py          ← BaseProvider, ProviderResult
├── registry.py      ← Registro y descubrimiento de plugins
├── local/           ← Ollama, LM Studio, vLLM, KoboldCPP, etc.
└── cloud/           ← OpenAI, Anthropic, Google, Groq, Cohere
```

Cada proveedor implementa:
- `scan() → ProviderResult`: Detecta disponibilidad y modelos.
- `stream(messages, model, options) → Iterator[str]`: Streaming token a token.
- `complete(messages, model, options) → str`: Respuesta completa.

---

## Flujo de una Petición de Chat

```
1. Usuario escribe en CLI o POST /v1/chat/completions
2. Rate Limiter verifica IP/Key (→ 429 si excede)
3. Cache Engine: ¿hit? → respuesta inmediata
4. Provider Manager → get_best() → backend óptimo
5. stream() / complete() → chunks de texto
6. ReasoningStripper filtra <think> tags
7. Respuesta enviada al cliente
8. Audit Logger registra: tokens, latencia, coste
9. Prometheus metrics actualizadas
10. Cache Engine almacena para futuras peticiones
```

## Flujo de Generación de Imagen

```
1. Usuario escribe prompt en Vision Studio UI (7862)
2. fooocus_studio_ui.py: snapshot del output dir (set de paths absolutos)
3. fooocus_client.py: POST generation → Fooocus Motor en puerto 7861
4. Fooocus acepta job → devuelve job_id
5. Poll cada 4s: verifica API query-job y fallback a get_newest_image()
6. Cuando aparece imagen nueva → se muestra en Gradio
7. Bridge Server sirve imagen vía /static/output/
8. Dashboard Web actualiza galería vía /v1/images
```

---

## Configuración (`config.yaml`)

```yaml
profile: production

server:
  host: 0.0.0.0
  port: 7860
  log_level: INFO

model:
  default_provider: "lm_studio"
  default_model: "auto"
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

---

## Puertos del Sistema

| Puerto | Proceso | Descripción |
|--------|---------|-------------|
| `7860` | `bridge_server.py` | API OpenAI-compatible + Dashboard Web |
| `7861` | `fooocus_studio_ui.py` | Fooocus Studio UI (Gradio) |
| `7862` | `dashboard.py` | Dashboard standalone (sin bridge) |
| `7861` | Fooocus Motor CPU | Motor de inferencia de imágenes |

---

## Stack de Hardware Soportado

| Hardware | Motor de Texto | Motor de Imágenes |
|----------|---------------|-------------------|
| CPU / AMD GPU | LM Studio / Ollama | Fooocus CPU --all-in-fp32 |
| CPU solamente | Ollama (CPU) | No disponible |
| Cloud | OpenAI / Anthropic / Gemini | No aplica |

---

## Decisiones de Diseño

| Decisión | Razón |
|----------|-------|
| HTTP puro (sin Flask) | Cero dependencias extra, portabilidad máxima |
| JSONL para audit log | Append-only garantizado, lectura incremental |
| DPAPI para keys | Cifrado nativo de Windows sin dependencias |
| Set-difference para polling de imágenes | Evita falsos positivos con archivos pre-existentes |
| BM25 + vectorial | Mejor recall que solo semántico en código |
| ThreadingHTTPServer | Concurrencia sin async, compatible con Python 3.10+ |
| Gradio para Vision UI | Interfaz interactiva sin frontend custom |
| Fooocus CPU-mode | DirectML/ZLUDA causaban crashes de hardware nativo por incompatibilidad de Kernels de Pytorch-AMD. CPU Mode (euler) garantiza 100% fail-safe execution. |
