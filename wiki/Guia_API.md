# Guía de API — Gravity AI Bridge V10.0 [Ecosistema Total]

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
  "version": "9.1",
  "bridge_online": true,
  "active_provider": "LM Studio",
  "active_model": "google/gemma-4-e2b",
  "backends": [
    {
      "name": "LM Studio",
      "category": "local",
      "healthy": true,
      "models": 3,
      "latency_ms": 817
    },
    {
      "name": "Ollama",
      "category": "local",
      "healthy": false,
      "models": 0,
      "latency_ms": 1814
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
      "timestamp": "2026-04-13T04:54:06.000Z",
      "session_id": "chatcmpl-abc123",
      "provider": "LM Studio",
      "model": "google/gemma-4-e2b",
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

### `GET /v1/images`

Lista de imágenes generadas por Fooocus disponibles en la galería.

**Response:**
```json
{
  "images": [
    "/static/output/Gravity_Gen_00001_.png",
    "/static/output/Gravity_Gen_00002_.png"
  ]
}
```

---

### `GET /static/output/<filename>`

Sirve una imagen generada directamente desde el directorio de outputs de Fooocus.

**Ejemplo:**
```
GET http://localhost:7860/static/output/Gravity_Gen_00001_.png
```

---

### `POST /v1/keys`

Guardar una API Key cifrada (DPAPI).

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

### Endpoints de Security Monitor

- `GET /v1/security`: Retorna el estado actual del demonio de seguridad (archivos monitoreados, puertos bloqueados, procesos sospechosos).
- `POST /v1/security/scan`: Fuerza un escaneo inmediato de procesos, puertos e integridad SHA-256.

---

### Endpoints de Image Queue

- `GET /v1/queue`: Muestra el estado global de la cola, últimos 50 trabajos y estadísticas de procesados/errores.
- `POST /v1/queue/add`: Encola un trabajo de generación. (Mismos parámetros que `/v1/generate`). Retorna el ID del trabajo.

---

### Endpoints de Deploy Manager

- `GET /v1/deploy/status`: Estado del último despliegue (duración, éxito/error, link de Netlify).
- `POST /v1/deploy`: Inicia un pipeline asíncrono de build (`npm install && npm run build`) y posterior volcado a Netlify.

---

### Endpoints de Game Server Manager

- `GET /v1/gameserver/status`: Estado detallado de todos los servidores registrados en `config.yaml` (PID, uptime, autorestart).
- `GET /v1/gameserver/log?server=wow_vanilla&lines=100`: Obtiene las N últimas líneas (tail) del log en crudo del servidor.
- `GET /v1/gameserver/players?server=wow_vanilla`: Consulta la base de datos MySQL asociada y retorna lista de jugadores online.
- `POST /v1/gameserver/start`: Arranca el servidor (body: `{"server": "wow_vanilla"}`). Lanza scripts de base de datos y exes.
- `POST /v1/gameserver/stop`: Detiene o mata (kill) los procesos asociados de forma segura.
- `POST /v1/gameserver/restart`: Wrapper automatizado stop -> start.
- `POST /v1/gameserver/command`: Inyecta comandos de consola (Game Master) al proceso activo.

---

### `GET /health`

Health check simple para balanceadores de carga.

**Response:**
```json
{
  "status": "ok",
  "backends": [
    {"name": "LM Studio", "healthy": true, "models": 3}
  ]
}
```

---

### `GET /metrics`

Métricas en formato Prometheus (text/plain).

```
# HELP gravity_requests_total Total de peticiones procesadas
# TYPE gravity_requests_total counter
gravity_requests_total{provider="LM Studio",model="google/gemma-4-e2b"} 42

# HELP gravity_tokens_total Total de tokens procesados
# TYPE gravity_tokens_total counter
gravity_tokens_total{direction="input",provider="LM Studio"} 1890
gravity_tokens_total{direction="output",provider="LM Studio"} 5312

# HELP gravity_latency_seconds Latencia de respuesta en segundos
# TYPE gravity_latency_seconds histogram
gravity_latency_seconds_bucket{provider="LM Studio",le="1.0"} 15
gravity_latency_seconds_bucket{provider="LM Studio",le="5.0"} 38
```

---

### `GET /` o `GET /dashboard`

Dashboard SPA interactivo (HTML). Sirve `web/dashboard.html`.

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
