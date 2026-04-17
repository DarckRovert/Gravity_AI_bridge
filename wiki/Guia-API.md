# 📡 Guía de API (REST) — Gravity AI Bridge V10.0

Gravity AI Bridge expone una API RESTful asíncrona que permite tanto al Dashboard oficial como a aplicaciones de terceros interactuar con el ecosistema. Es **100% compatible** con el protocolo de OpenAI.

**Base URL**: `http://localhost:7860`  
**Auth**: `Authorization: Bearer gravity-local`

---

## 📍 Endpoints Principales

### `POST /v1/chat/completions`
Inferencia de chat con soporte de streaming SSE (Server-Sent Events).

**Ejemplo de Request (JSON):**
```json
{
  "model": "gravity-bridge-auto",
  "messages": [
    {"role": "system", "content": "Eres un auditor técnico."},
    {"role": "user", "content": "Analiza el estado del bridge."}
  ],
  "stream": true,
  "temperature": 0.6
}
```

### `GET /v1/status`
Estado detallado del sistema, backends activos y métricas de latencia.

**Ejemplo de Respuesta:**
```json
{
  "version": "10.0",
  "bridge_online": true,
  "active_provider": "LM Studio",
  "active_model": "deepseek-r1:14b",
  "backends": [
    {
      "name": "LM Studio",
      "category": "local",
      "healthy": true,
      "models": 3,
      "latency_ms": 817
    }
  ]
}
```

---

## 🎮 Game Server Manager

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| **GET** | `/v1/gameserver/status` | Estado de worldserver/realmd (PID, uptime, autorestart). |
| **GET** | `/v1/gameserver/log?server=wow_vanilla&lines=150` | Tail del log en crudo del servidor. |
| **GET** | `/v1/gameserver/players?server=wow_vanilla` | Lista de jugadores online (Nombre, Nivel, Clase, Zona). |
| **POST** | `/v1/gameserver/start` | Inicia el servidor `{"server": "wow_vanilla"}`. |
| **POST** | `/v1/gameserver/command` | Envía comandos GM (SOAP) `{"command": ".announce Hola"}`. |

---

## 🚀 Despliegue y Cola de Imágenes

### Deploy Pipeline
- `GET /v1/deploy/status`: Estado del último despliegue (duración, éxito/error, link Netlify).
- `POST /v1/deploy`: Inicia pipeline `npm install && npm run build`.

### Image Queue
- `GET /v1/queue`: Estado global de la cola persistente.
- `POST /v1/queue/add`: Encola un trabajo de generación de imagen.

---

## 📊 Métricas de Prometheus (`/metrics`)

El bridge exporta métricas en formato estándar Prometheus (text/plain) para su ingesta en Grafana:

```text
# HELP gravity_requests_total Total de peticiones procesadas
# TYPE gravity_requests_total counter
gravity_requests_total{provider="LM Studio",model="gemma-2"} 42

# HELP gravity_tokens_total Total de tokens procesados
# TYPE gravity_tokens_total counter
gravity_tokens_total{direction="input",provider="LM Studio"} 1890
gravity_tokens_total{direction="output",provider="LM Studio"} 5312

# HELP gravity_latency_seconds Latencia de respuesta en segundos
# TYPE gravity_latency_seconds histogram
gravity_latency_seconds_bucket{provider="LM Studio",le="1.0"} 15
```

---

## 🛠️ Integración con SDKs

### Python (OpenAI Library)
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:7860/v1", api_key="gravity-local")
```

### JavaScript / TypeScript
```typescript
import OpenAI from 'openai';
const client = new OpenAI({ baseURL: 'http://localhost:7860/v1', apiKey: 'gravity-local' });
```

---

## 📝 Tabla de Códigos de Error

| Código | Significado | Acción Sugeridada |
| :--- | :--- | :--- |
| `200` | OK | Operación exitosa. |
| `400` | Bad Request | Verifica el esquema del JSON enviado. |
| `429` | Rate Limit | Reduce la frecuencia de peticiones en `config.yaml`. |
| `500` | Internal Error | Revisa `bridge_server.log` para stacktraces. |
| `503` | Service Unavailable | No hay proveedores de IA online (Ollama/LM Studio). |

---
*Referencia Técnica Exhaustiva V10.0.*
