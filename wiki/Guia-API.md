# Guía de API — Gravity AI Bridge V10.0
**Diamond-Tier Edition** · Base URL: `http://localhost:7860`

El Bridge expone una API HTTP completamente compatible con el estándar OpenAI, más endpoints propios para gestión del sistema. Cualquier cliente que funcione con OpenAI puede conectarse al Bridge sin modificaciones.

---

## Autenticación

Por defecto no se requiere autenticación. Cuando se configura `allowed_keys` en `config.yaml`, todas las peticiones deben incluir:

```http
Authorization: Bearer tu-api-key
```

Las API keys de proveedores cloud (Anthropic, OpenAI, etc.) se configuran en el Dashboard → Configuración, no en este header.

---

## Endpoints Compatibles OpenAI

### `POST /v1/chat/completions`

El endpoint principal. Compatible con cualquier cliente OpenAI (Python SDK, LangChain, Continue.dev, etc.).

**Request (streaming — por defecto):**
```json
{
  "model": "gravity-bridge-auto",
  "messages": [
    {"role": "system", "content": "Eres un asistente técnico."},
    {"role": "user", "content": "¿Cómo funciona un transformer?"}
  ],
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Respuesta en streaming (Server-Sent Events):**
```
data: {"id":"chatcmpl-a1b2c3","object":"chat.completion.chunk","model":"qwen2.5-coder:32b","choices":[{"index":0,"delta":{"content":"Un"},"finish_reason":null}]}

data: {"id":"chatcmpl-a1b2c3","object":"chat.completion.chunk","model":"qwen2.5-coder:32b","choices":[{"index":0,"delta":{"content":" transformer"},"finish_reason":null}]}

data: {"id":"chatcmpl-a1b2c3","object":"chat.completion.chunk","model":"qwen2.5-coder:32b","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**Request (sin streaming):**
```json
{
  "model": "gravity-bridge-auto",
  "messages": [{"role": "user", "content": "¿Qué es ROCm?"}],
  "stream": false
}
```

**Respuesta sin streaming:**
```json
{
  "id": "chatcmpl-a1b2c3",
  "object": "chat.completion",
  "model": "qwen2.5-coder:32b",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "ROCm (Radeon Open Compute) es..."},
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 148,
    "total_tokens": 160
  }
}
```

**Selección de modelo:**
- `"gravity-bridge-auto"` — El Bridge elige el mejor proveedor disponible automáticamente
- `"qwen2.5-coder:32b"` — Nombre exacto de un modelo en Ollama/LM Studio → el Bridge lo busca en todos los proveedores

**Ejemplo con Python SDK de OpenAI:**
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7860/v1",
    api_key="gravity-local"  # Cualquier string si no hay whitelist configurado
)

response = client.chat.completions.create(
    model="gravity-bridge-auto",
    messages=[{"role": "user", "content": "Explica async/await en Python"}],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

**Ejemplo con curl:**
```bash
curl http://localhost:7860/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gravity-bridge-auto",
    "messages": [{"role": "user", "content": "Hola"}],
    "stream": false
  }'
```

---

### `GET /v1/models`

Lista de modelos disponibles en todos los proveedores activos. Compatible con el selector de modelos de Continue.dev y otros clientes.

**Respuesta:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "gravity-bridge-auto",
      "object": "model",
      "owned_by": "gravity-ai",
      "provider": "auto"
    },
    {
      "id": "qwen2.5-coder:32b",
      "object": "model",
      "owned_by": "ollama",
      "provider": "ollama"
    },
    {
      "id": "claude-3-5-sonnet-20241022",
      "object": "model",
      "owned_by": "anthropic",
      "provider": "anthropic"
    }
  ]
}
```

---

## Endpoints de Sistema

### `GET /health`

Health check mínimo. Retorna 200 si el servidor está online.

```bash
curl http://localhost:7860/health
# → HTTP 200 OK
```

---

### `GET /v1/status`

Estado completo: proveedores, modelo activo, uptime.

```bash
curl http://localhost:7860/v1/status
```

```json
{
  "providers": [
    {
      "name": "ollama",
      "healthy": true,
      "latency_ms": 42,
      "models": [
        {"name": "qwen2.5-coder:32b"},
        {"name": "deepseek-r1:14b"}
      ]
    },
    {
      "name": "lmstudio",
      "healthy": false,
      "latency_ms": null,
      "error": "Connection refused"
    }
  ],
  "active_provider": "ollama",
  "active_model": "qwen2.5-coder:32b",
  "model_locked": false,
  "uptime_s": 7234,
  "total_requests": 142
}
```

---

### `GET /v1/hardware`

Perfil de hardware para inferencia de IA.

```json
{
  "gpu_name": "AMD Radeon RX 6800 XT",
  "gpu_type": "rocm",
  "is_igpu": false,
  "gfx_version": "gfx1031",
  "vram_mb": 16384,
  "total_ram_mb": 32768,
  "optimal_ctx": 65536,
  "kv_quant": "q8_0",
  "model_size_b": 32,
  "npu_name": null,
  "all_gpus": [
    {
      "name": "AMD Radeon RX 6800 XT",
      "is_igpu": false,
      "vram_mb": 16384,
      "vendor": "amd",
      "gpu_type": "rocm",
      "gfx_version": "gfx1031"
    },
    {
      "name": "AMD Radeon Graphics",
      "is_igpu": true,
      "vram_mb": 0,
      "vendor": "amd",
      "gpu_type": "rocm",
      "gfx_version": "gfx90c"
    }
  ]
}
```

---

### `GET /v1/cost`

Costes de la sesión actual y del día.

```json
{
  "session_cost": 0.0024,
  "daily_cost": 0.0087,
  "daily_limit": 10.0,
  "over_limit": false,
  "session_tokens": {
    "input": 3200,
    "output": 1800
  },
  "daily_breakdown": {
    "anthropic": {
      "calls": 4,
      "input_tokens": 3200,
      "output_tokens": 1800,
      "total_cost": 0.0087
    }
  }
}
```

> **Nota:** Si solo usas proveedores locales, todos los valores son `0` o `{}`. Esto es correcto — los modelos locales son gratuitos.

---

### `GET /v1/watchdog`

Estado del Engine Watchdog y lock de modelo.

```json
{
  "active_provider": "ollama",
  "active_model": "qwen2.5-coder:32b",
  "model_locked": false,
  "last_switch": "2026-04-17T01:30:00",
  "hardware": {
    "gpu_name": "AMD Radeon RX 6800 XT",
    "vram_mb": 16384,
    "gpu_type": "rocm"
  }
}
```

---

### `GET /v1/sessions`

Lista de sesiones guardadas en `_saves/`.

```json
{
  "count": 3,
  "sessions": [
    {
      "name": "debug-bridge-server",
      "branch": "main",
      "turns": 32,
      "saved_at": "2026-04-17 01:00:00"
    },
    {
      "name": "wow-server-audit",
      "branch": "rocm-fix",
      "turns": 14,
      "saved_at": "2026-04-16 23:30:00"
    }
  ]
}
```

---

### `GET /v1/rag/status`

Estado del índice RAG.

```json
{
  "rag_dir": "F:/Gravity_AI_bridge/_rag_index",
  "doc_count": 8,
  "chunk_count": 247,
  "size_mb": 1.24,
  "online": true
}
```

---

### `GET /v1/audit`

Últimas N entradas del audit log.

```json
{
  "entries": [
    {
      "id": "chatcmpl-a1b2c3",
      "provider": "ollama",
      "model": "qwen2.5-coder:32b",
      "input_tokens": 312,
      "output_tokens": 148,
      "cost_usd": 0.0,
      "latency_ms": 2341,
      "timestamp": "2026-04-17T01:44:00"
    }
  ],
  "total": 142
}
```

---

### `GET /v1/security`

Resultado del último escaneo de seguridad Zero-Trust.

---

### `GET /v1/queue`

Estado de la cola de generación de imágenes.

---

### `GET /v1/deploy/status`

Estado del último pipeline de deploy a Netlify.

---

### `GET /v1/gameserver/status`

Estado de los servidores de juego configurados.

```json
{
  "wow_vanilla": {
    "display_name": "WoW Vanilla (MaNGOS)",
    "status": "online",
    "worldserver": true,
    "realmd": true,
    "players_online": 3,
    "uptime": "2h 14m"
  }
}
```

---

## Endpoints POST de Acción

### `POST /v1/agent/compare`

Multi-Agent Orchestrator — envía un prompt a múltiples modelos en paralelo.

```bash
curl -X POST http://localhost:7860/v1/agent/compare \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "¿Cuál es la diferencia entre ROCm y CUDA?",
    "mode": "parallel",
    "n_models": 3
  }'
```

**Parámetros:**
| Campo | Tipo | Por defecto | Opciones |
|:---|:---|:---|:---|
| `prompt` | string | requerido | — |
| `mode` | string | `"parallel"` | `"parallel"`, `"vote"` |
| `n_models` | int | `3` | 2, 3, 4 |
| `messages` | array | — | Alternativa a `prompt` si quieres historial |

**Respuesta:**
```json
{
  "ok": true,
  "mode": "parallel",
  "results": [
    {
      "provider": "ollama",
      "model": "qwen2.5-coder:32b",
      "response": "ROCm es el stack de compute de AMD...",
      "elapsed": "2.3s"
    },
    {
      "provider": "ollama",
      "model": "deepseek-r1:14b",
      "response": "La principal diferencia está en...",
      "elapsed": "3.1s"
    }
  ]
}
```

En modo `vote`, el resultado ganador incluye `"vote_score"` con la puntuación.

---

### `POST /v1/watchdog/unlock`

Desbloquea el modelo fijado manualmente y reactiva el auto-switch.

```bash
curl -X POST http://localhost:7860/v1/watchdog/unlock \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Respuesta:**
```json
{"ok": true, "message": "Modelo desbloqueado. Auto-switch reactivo."}
```

---

### `POST /v1/keys`

Guarda una API key de proveedor cloud, cifrada con DPAPI.

```bash
curl -X POST http://localhost:7860/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"provider": "anthropic", "key": "sk-ant-..."}'
```

```json
{"ok": true, "provider": "anthropic"}
```

---

### `POST /v1/ai/start` / `POST /v1/ai/stop`

Inicia o detiene un motor de IA local.

```json
{"provider": "LM Studio"}
```

```json
{"success": true, "message": "LM Studio iniciado."}
```

---

### `POST /v1/security/scan`

Fuerza un escaneo de seguridad Zero-Trust inmediato.

```bash
curl -X POST http://localhost:7860/v1/security/scan \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### `POST /v1/deploy`

Inicia el pipeline `npm run build` → `netlify deploy --prod`.

```json
{"project_path": "C:/Users/darck/proyectos/mi-web"}
```

```json
{"started": true, "project": "mi-web"}
```

---

### `POST /v1/queue/add`

Añade un trabajo de generación de imagen a la cola de Fooocus.

```json
{
  "prompt": "A majestic dragon flying over a medieval castle, fantasy art, detailed",
  "performance": "Quality",
  "width": 1024,
  "height": 1024
}
```

```json
{"ok": true, "job_id": "job_a1b2c3d4"}
```

---

### `POST /v1/generate`

Generación de imagen directa (sin cola) via Fooocus API.

```json
{
  "prompt": "Cyberpunk cityscape at night, rain, neon lights",
  "negative_prompt": "blurry, low quality",
  "width": 1024,
  "height": 1024,
  "performance": "Speed",
  "style_selections": ["Fooocus V2", "Futuristic"],
  "num_images": 1
}
```

---

### Endpoints de Game Server

```bash
# Iniciar servidor
curl -X POST http://localhost:7860/v1/gameserver/start \
  -d '{"server": "wow_vanilla"}'

# Detener servidor
curl -X POST http://localhost:7860/v1/gameserver/stop \
  -d '{"server": "wow_vanilla"}'

# Reiniciar
curl -X POST http://localhost:7860/v1/gameserver/restart \
  -d '{"server": "wow_vanilla"}'

# Enviar comando de administrador (via SOAP)
curl -X POST http://localhost:7860/v1/gameserver/command \
  -d '{"server": "wow_vanilla", "command": ".server info"}'

# Registrar cuenta de jugador
curl -X POST http://localhost:7860/v1/gameserver/register \
  -d '{"server": "wow_vanilla", "username": "jugador1", "password": "Pass123!"}'

# Exponer a internet (actualiza configs MaNGOS)
curl -X POST http://localhost:7860/v1/gameserver/expose \
  -d '{"server": "wow_vanilla", "public_address": "203.0.113.45"}'
```

---

## Códigos de Estado HTTP

| Código | Significado |
|:---|:---|
| `200` | OK — petición procesada correctamente |
| `400` | Bad Request — parámetros inválidos o faltantes |
| `404` | Not Found — endpoint no existe |
| `429` | Too Many Requests — rate limit excedido |
| `503` | Service Unavailable — ningún proveedor de IA disponible |
| `500` | Internal Server Error — error inesperado en el Bridge |

Todos los errores retornan JSON:
```json
{"error": "descripción del error"}
```

---

## Integración con Herramientas Externas

### LangChain (Python)
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    openai_api_base="http://localhost:7860/v1",
    openai_api_key="gravity-local",
    model_name="gravity-bridge-auto"
)

result = llm.invoke("Explica cómo funciona el attention mechanism")
print(result.content)
```

### Continue.dev (config.yaml)
```yaml
name: Gravity Local V10.0
version: 10.0.0
schema: v1
models:
  - name: "Gravity Bridge"
    provider: openai
    model: gravity-bridge-auto
    apiBase: "http://localhost:7860/v1"
    apiKey: "gravity-local"
```

### Aider
```bash
aider --openai-api-base http://localhost:7860/v1 --model openai/gravity-bridge-auto
```

### Open WebUI (alternativa al Dashboard)
```
OPENAI_API_BASE_URL=http://localhost:7860/v1
OPENAI_API_KEY=gravity-local
```
