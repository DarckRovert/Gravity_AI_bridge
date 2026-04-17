# Guía de API — Gravity AI Bridge V10.0

Base URL: `http://localhost:7860`

---

## Endpoints GET

### `GET /health`
Verificación de estado mínima. Retorna 200 si el bridge está online.

### `GET /v1/status`
Estado completo del sistema.
```json
{
  "providers": [{"name": "ollama", "healthy": true, "latency_ms": 45, "models": [...]}],
  "active_provider": "ollama",
  "active_model": "qwen2.5-coder:32b",
  "uptime_s": 3600
}
```

### `GET /v1/hardware`
Perfil de hardware. Usado por el panel Hardware Monitor.
```json
{
  "gpu_name": "Radeon RX 6800 XT",
  "gpu_type": "rocm",
  "is_igpu": false,
  "vram_mb": 16384,
  "total_ram_mb": 32768,
  "optimal_ctx": 65536,
  "kv_quant": "q4_0",
  "model_size_b": 32,
  "npu_name": null,
  "all_gpus": [...]
}
```

### `GET /v1/cost`
Costes de sesión y diarios.
```json
{
  "session_cost": 0.0012,
  "daily_cost": 0.0048,
  "daily_limit": 10.0,
  "over_limit": false,
  "session_tokens": {"input": 1200, "output": 800},
  "daily_breakdown": {
    "anthropic": {"calls": 3, "input_tokens": 1200, "output_tokens": 800, "total_cost": 0.0048}
  }
}
```

### `GET /v1/watchdog`
Estado del Engine Watchdog.
```json
{
  "active_provider": "ollama",
  "active_model": "qwen2.5-coder:32b",
  "model_locked": false,
  "hardware": {"gpu_name": "...", "vram_mb": 16384, "gpu_type": "rocm"}
}
```

### `GET /v1/sessions`
Lista sesiones guardadas en `_saves/`.
```json
{
  "count": 3,
  "sessions": [
    {"name": "sesion-debug", "branch": "main", "turns": 24, "saved_at": "2026-04-17 01:00:00"}
  ]
}
```

### `GET /v1/rag/status`
Estado del índice RAG.
```json
{
  "rag_dir": "F:/Gravity_AI_bridge/_rag_index",
  "doc_count": 5,
  "chunk_count": 142,
  "size_mb": 0.38,
  "online": true
}
```

### `GET /v1/security`
Resultado del último escaneo de seguridad.

### `GET /v1/audit`
Últimas 100 entradas del audit log.

### `GET /v1/models`
Lista de modelos disponibles (compatible OpenAI).

### `GET /v1/queue`
Estado de la cola de generación de imágenes.

### `GET /v1/deploy/status`
Estado del último pipeline de deploy.

### `GET /v1/gameserver/status`
Estado de los servidores de juego configurados.

---

## Endpoints POST

### `POST /v1/chat/completions`
**Compatible OpenAI.** Acepta `stream: true` (por defecto) y `stream: false`.
```json
{
  "model": "gravity-bridge-auto",
  "messages": [{"role": "user", "content": "Hola"}],
  "stream": true,
  "temperature": 0.7
}
```

### `POST /v1/agent/compare`
Multi-Agent Orchestrator.
```json
{
  "prompt": "Explica el teorema de Bayes",
  "mode": "parallel",
  "n_models": 3
}
```
Respuesta:
```json
{
  "ok": true,
  "mode": "parallel",
  "results": [
    {"provider": "ollama", "model": "...", "response": "...", "elapsed": "1.2s"},
    ...
  ]
}
```

### `POST /v1/watchdog/unlock`
Desbloquea el modelo forzado manualmente y reactiva el auto-switch.
```json
{}
```
Respuesta: `{"ok": true, "message": "Modelo desbloqueado. Auto-switch reactivo."}`

### `POST /v1/keys`
Guarda API keys cifradas con DPAPI.
```json
{"provider": "anthropic", "key": "sk-ant-..."}
```

### `POST /v1/ai/start`
Inicia un motor de IA local.
```json
{"provider": "LM Studio"}
```

### `POST /v1/ai/stop`
Detiene un motor de IA local.
```json
{"provider": "Ollama"}
```

### `POST /v1/security/scan`
Fuerza un escaneo de seguridad inmediato.

### `POST /v1/deploy`
Inicia el pipeline de deploy.
```json
{"project_path": "C:/Users/.../mi-proyecto"}
```

### `POST /v1/queue/add`
Añade un trabajo a la cola de generación de imágenes.
```json
{
  "prompt": "A cyberpunk city at night",
  "performance": "Speed",
  "width": 1024,
  "height": 1024
}
```

### `POST /v1/gameserver/start`
```json
{"server": "wow_vanilla"}
```

### `POST /v1/gameserver/stop`
```json
{"server": "wow_vanilla"}
```

### `POST /v1/gameserver/command`
Envía comando SOAP al servidor.
```json
{"server": "wow_vanilla", "command": ".server info"}
```

### `POST /v1/gameserver/register`
Registra una cuenta.
```json
{"server": "wow_vanilla", "username": "player1", "password": "Pass123!"}
```

### `POST /v1/gameserver/expose`
Configura el servidor para acceso WAN.
```json
{"server": "wow_vanilla", "public_address": "203.0.113.45"}
```

---

## Autenticación

El bridge acepta cualquier API key en el header `Authorization: Bearer <key>` si no se configura whitelist.
Para configurar API keys de acceso al bridge, editar `config.yaml`:

```yaml
security:
  allowed_keys:
    - "mi-key-personal"
    - "key-de-continue"
```
