# Guía de API — Gravity AI Bridge V9.0 PRO [Diamond-Tier Edition]

> La API es 100% compatible con el protocolo OpenAI. Cualquier cliente que soporte OpenAI funciona sin modificaciones.

**Base URL**: `http://localhost:7860`

---

## Autenticación

```http
Authorization: Bearer gravity-local
```

Cualquier valor es válido para uso local. Para rate limiting por key, configura en `config.yaml`.

---

## Endpoints

### `POST /v1/chat/completions`

Chat completions con soporte de streaming SSE.

**Request:**
```json
{
  "model": "gravity-bridge-auto",
  "messages": [
    {"role": "system", "content": "Eres un asistente técnico."},
    {"role": "user", "content": "Explica qué es RAG."}
  ],
  "stream": true,
  "temperature": 0.6,
  "max_tokens": 2048
}
```

**Response (stream=false):**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "model": "deepseek-r1:14b",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "RAG es..."},
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 128,
    "total_tokens": 173
  }
}
```

**Response (stream=true):** Server-Sent Events
```
data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":"RAG"},"index":0}]}
data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":" es"},"index":0}]}
data: [DONE]
```

**Modelos disponibles:**
- `gravity-bridge-auto` — Selección automática por latencia (recomendado)
- Cualquier modelo disponible en los backends configurados

---

### `GET /v1/models`

Lista todos los modelos disponibles de todos los backends online.

**Response:**
```json
{
  "object": "list",
  "data": [
    {"id": "gravity-bridge-auto", "object": "model", "owned_by": "Gravity AI"},
    {"id": "deepseek-r1:14b", "object": "model", "owned_by": "ollama"},
    {"id": "gpt-4o", "object": "model", "owned_by": "openai"}
  ]
}
```

---

### `GET /v1/status`

Estado del sistema con todos los backends y métricas.

**Response:**
```json
{
  "version": "8.0",
  "bridge_online": true,
  "active_provider": "ollama",
  "active_model": "deepseek-r1:14b",
  "backends": [
    {
      "name": "ollama",
      "category": "local",
      "healthy": true,
      "models": 5,
      "latency_ms": 124
    },
    {
      "name": "openai",
      "category": "cloud",
      "healthy": false,
      "models": 0,
      "latency_ms": 0
    }
  ]
}
```

---

### `GET /v1/audit`

Últimas 100 entradas del Audit Log.

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "timestamp": "2026-04-08T21:00:00.000Z",
      "session_id": "chatcmpl-abc123",
      "provider": "ollama",
      "model": "deepseek-r1:14b",
      "input_tokens": 45,
      "output_tokens": 128,
      "total_tokens": 173,
      "latency_ms": 1842.5,
      "cost_usd": 0.0
    }
  ]
}
```

---

### `POST /v1/keys`

Guardar una API Key cifrada (desde el Dashboard web).

**Request:**
```json
{
  "provider": "openai",
  "key": "sk-..."
}
```

**Response:**
```json
{"ok": true, "provider": "openai"}
```

---

### `GET /health`

Health check simple para balanceadores de carga.

**Response:**
```json
{
  "status": "ok",
  "backends": [
    {"name": "ollama", "healthy": true, "models": 5}
  ]
}
```

---

### `GET /metrics`

Métricas en formato Prometheus (text/plain).

```
# HELP gravity_requests_total Total de peticiones procesadas
# TYPE gravity_requests_total counter
gravity_requests_total{provider="ollama",model="deepseek-r1:14b"} 42

# HELP gravity_tokens_total Total de tokens procesados
# TYPE gravity_tokens_total counter
gravity_tokens_total{direction="input",provider="ollama"} 1890
gravity_tokens_total{direction="output",provider="ollama"} 5312

# HELP gravity_latency_seconds Latencia de respuesta en segundos
# TYPE gravity_latency_seconds histogram
gravity_latency_seconds_bucket{provider="ollama",le="1.0"} 15
gravity_latency_seconds_bucket{provider="ollama",le="5.0"} 38
```

---

### `GET /` o `GET /dashboard`

Dashboard SPA interactivo (HTML).

---

## Integración con Clientes

### Python (openai SDK)
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7860/v1",
    api_key="gravity-local"
)

response = client.chat.completions.create(
    model="gravity-bridge-auto",
    messages=[{"role": "user", "content": "Hola"}]
)
print(response.choices[0].message.content)
```

### JavaScript / TypeScript
```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:7860/v1',
  apiKey: 'gravity-local',
});

const response = await client.chat.completions.create({
  model: 'gravity-bridge-auto',
  messages: [{ role: 'user', content: 'Hola' }],
});
```

### cURL
```bash
curl -X POST http://localhost:7860/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer gravity-local" \
  -d '{"model":"gravity-bridge-auto","messages":[{"role":"user","content":"Hola"}],"stream":false}'
```

### Configuración Cursor / VS Code Continue
```json
{
  "baseUrl": "http://localhost:7860/v1",
  "apiKey": "gravity-local",
  "model": "gravity-bridge-auto"
}
```

---

## Códigos de Error

| Código | Significado |
|--------|------------|
| `200` | OK |
| `400` | Request malformado |
| `404` | Endpoint inexistente |
| `429` | Rate limit excedido |
| `500` | Error interno del bridge |
| `503` | Sin proveedores disponibles |
