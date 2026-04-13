# Arquitectura — Gravity AI Bridge V9.1 PRO [Diamond-Tier Edition]

## Visión General

Gravity AI Bridge es un **enrutador universal de IA** que actúa como capa de abstracción entre el usuario/IDE y múltiples motores de IA (locales y cloud). Expone una API 100% compatible con OpenAI y agrega un módulo de generación de imágenes acelerado por hardware AMD vía ZLUDA.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CAPA DE PRESENTACIÓN                          │
│  CLI (ask_deepseek.py) │ Dashboard SPA (web/) │ IDEs (Cursor/VSCode) │
│                        │ Fooocus Studio UI    │                      │
└──────────────┬─────────────────────────┬───────────────────────────┘
               │ HTTP / stdin / OpenAI   │ Gradio / HTTP
┌──────────────▼─────────────────────┐  ┌──────────────────────────┐
│     BRIDGE SERVER (bridge_server.py)│  │  VISION STUDIO            │
│  • Enrutamiento dinámico latencia   │  │  fooocus_studio_ui.py     │
│  • Rate Limiting IP + API Key       │  │  comfyui_client.py        │
│  • Streaming SSE / JSON             │  └────────────┬─────────────┘
│  • Sirve web/dashboard.html en /    │               │ HTTP JSON
│  • /static/output/ (imágenes)       │  ┌────────────▼─────────────┐
│  • /v1/images (listado galería)     │  │  ComfyUI-ZLUDA (8188)     │
└──────────────┬──────────────────────┘  │  Radeon 780M iGPU         │
               │                         │  JuggernautXL SDXL        │
      ┌─────────▼──────────┐             └──────────────────────────┘
      │  Provider Manager  │
      │  scan_all()        │
      │  get_best()        │
      └──────┬─────────────┘
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
- Sirve imágenes desde `_integrations/ComfyUI-Zluda/output/` en `/static/output/`.
- Endpoints: `/v1/chat/completions`, `/v1/models`, `/v1/status`, `/v1/audit`, `/v1/keys`, `/v1/images`, `/metrics`, `/health`.

### `dashboard.py` — Servidor SPA
- Servidor HTTP minimalista que sirve `web/dashboard.html`.
- Puerto independiente (7862) para uso standalone sin bridge server.

### `web/dashboard.html` — SPA V9.1
- HTML/CSS/JS puro, sin dependencias externas.
- Chat con streaming SSE en tiempo real.
- Tabs: Chat · Status · Vision Studio (iFrame) · Audit Log · Configuración.
- Galería de imágenes con polling automático cada 5s a `/v1/images`.

### `tools/fooocus_studio_ui.py` — Vision Studio
- Interfaz Gradio que replica la UX de Fooocus.
- Puerto 7861 (configurable via `GRADIO_SERVER_PORT`).
- `get_all_images()` + `get_newest_image()`: Detección correcta de imágenes nuevas por set-difference de paths absolutos.
- Timeout de 360 segundos para la primera compilación ZLUDA.

### `tools/comfyui_client.py` — Cliente ComfyUI
- Comunicación HTTP con ComfyUI en `127.0.0.1:8188`.
- Workflow SDXL con KSampler, VAEDecode, SaveImage.
- Checkpoint: `juggernautXL_v8Rundiffusion.safetensors`.

### `provider_manager.py` — Orquestador
- `scan_all()`: Escanea todos los backends en paralelo.
- `get_best()`: Selecciona el proveedor con menor latencia TTFT.
- `stream()` / `complete()`: Interfaz unificada.

### `core/` — Infraestructura (22 módulos)

| Módulo | Responsabilidad |
|--------|----------------|
| `config_manager.py` | Lee/escribe `config.yaml`. Migración desde `_settings.json`. |
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
| `model_selector.py` | Lógica de selección de modelo óptimo. |
| `multi_agent.py` | Coordinación de agentes AI-to-AI. |

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
1. Usuario escribe prompt en Fooocus Studio UI (7861)
2. fooocus_studio_ui.py: snapshot del output dir (set de paths absolutos)
3. comfyui_client.py: POST /prompt → ComfyUI 8188 con workflow SDXL
4. ComfyUI acepta job → devuelve prompt_id
5. Poll cada 2s: get_newest_image() = current_set - snapshot
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
| `8188` | ComfyUI-ZLUDA | Motor de inferencia de imágenes |

---

## Stack de Hardware Soportado

| Hardware | Motor de Texto | Motor de Imágenes |
|----------|---------------|-------------------|
| NVIDIA GPU | Ollama / LM Studio | ComfyUI (CUDA) |
| AMD GPU + HIP SDK | LM Studio / Ollama | ComfyUI-ZLUDA |
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
| ZLUDA sobre DirectML | Mayor estabilidad en AMD sin drivers CUDA nativos |
