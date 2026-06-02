# 🔌 API Reference — Gravity AI Bridge V15.2 PRO

Referencia completa de todos los endpoints REST del ecosistema. Compatible con el protocolo OpenAI API v1.

**Base URL**: `http://localhost:7860`

---

## 🧠 Chat & LLM

### `POST /v1/chat/completions`
Chat con streaming SSE. Drop-in replacement de OpenAI.

**Request:**
```json
{
  "model": "llama3.2:latest",
  "messages": [{"role": "user", "content": "Hola"}],
  "stream": true,
  "temperature": 0.7
}
```

**Response** (stream): `text/event-stream` con chunks `data: {"choices":[{"delta":{"content":"..."}}]}`

---

### `POST /v1/agent/compare`
Comparación multi-modelo paralela.

**Request:**
```json
{
  "prompt": "Explica qué es un transformer",
  "models": ["llama3.2:latest", "mistral:latest"],
  "mode": "parallel"
}
```

`mode`: `parallel` | `voting` | `debate`

---

## 🎬 Video Studio

### `POST /v1/video/create`
Encolar un nuevo job de video.

**Request:**
```json
{
  "topic": "Historia del Imperio Inca",
  "style": "biomechanic_v13",
  "job_type": "music",
  "audio_track_path": "C:/ruta/audio.mp3",
  "fps": 24,
  "resolution": "1280x720",
  "n_scenes": 7
}
```

**`job_type`**: `standard` | `music`  
**`style`**: `biomechanic_v13` | `julia_v13` | `quantum_v13` | `mandelbulb_v13`

**Response:**
```json
{"job_id": 52, "status": "queued", "message": "Job #52 encolado."}
```

---

### `GET /v1/video/status?job_id=52`
Estado del job de video.

**Response:**
```json
{
  "job_id": 52,
  "status": "rendering",
  "progress": 65,
  "scene": 4,
  "total_scenes": 7,
  "eta_seconds": 120
}
```

`status`: `queued` | `rendering` | `done` | `error`

---

### `GET /v1/video/stream?job_id=52`
Stream del MP4 finalizado al reproductor web.

**Response**: `video/mp4` (stream parcial con rango de bytes)

---

### `POST /v1/video/cancel`
Cancela un job en cola o en proceso.

**Request:** `{"job_id": 52}`

---

### `POST /v1/video/delete`
Elimina un job y sus archivos de salida.

**Request:** `{"job_id": 52}`

---

## 👥 Sesiones Multi-Agente

### `POST /v1/sessions/spawn`
Crea un sub-agente en un subproceso aislado.

**Request:**
```json
{
  "role": "coder",
  "context": "Analiza el archivo pipeline.py"
}
```

`role`: `auditor` | `planner` | `coder` | `researcher` | `executor`

**Response:** `{"session_id": "sess_abc123", "pid": 14523}`

---

### `POST /v1/sessions/kill`
Termina un sub-agente activo.

**Request:** `{"session_id": "sess_abc123"}`

---

### `GET /v1/sessions/active`
Lista todos los sub-agentes corriendo.

**Response:**
```json
{
  "sessions": [
    {"session_id": "sess_abc123", "role": "coder", "pid": 14523, "uptime_s": 42}
  ]
}
```

---

## 🛡️ HITL — Human in the Loop

### `GET /v1/hitl/pending`
Lista aprobaciones pendientes.

**Response:**
```json
{
  "pending": [
    {
      "approval_id": "hitl_001",
      "tool": "shell_exec",
      "args": {"cmd": "rm -rf /tmp/test"},
      "requested_at": "2026-06-02T08:00:00Z"
    }
  ]
}
```

---

### `POST /v1/hitl/approve`
Aprueba una acción del agente.

**Request:** `{"approval_id": "hitl_001"}`

---

### `POST /v1/hitl/reject`
Rechaza una acción del agente.

**Request:** `{"approval_id": "hitl_001", "reason": "Comando demasiado destructivo"}`

---

## 🖼️ Image Queue (Fooocus)

### `POST /v1/queue/add`
Añade una imagen a la cola de Fooocus.

**Request:**
```json
{
  "prompt": "A cosmic nebula, hyperrealistic, 8k",
  "style": "Cinematic",
  "aspect_ratio": "16:9"
}
```

---

### `GET /v1/queue/stream`
SSE stream de progreso de la cola de imágenes.

**Response**: `text/event-stream`
```
data: {"status": "generating", "progress": 45, "preview_url": "/preview/img_001.jpg"}
```

---

## 📚 RAG

### `POST /v1/rag/toggle`
Activa o desactiva la inyección de contexto RAG.

**Request:** `{"enabled": true}`

---

### `POST /v1/rag/reindex`
Fuerza la re-indexación de documentos en `_rag_index/`.

---

## 🕷️ Web Scraping

### `POST /v1/tools/scrape`
Raspa una URL y devuelve Markdown limpio.

**Request:** `{"url": "https://example.com/article"}`

**Response:**
```json
{
  "content": "# Título\n\nContenido en markdown...",
  "source": "firecrawl",
  "chars": 3420
}
```

`source`: `firecrawl` | `urllib_fallback`

---

### `GET /v1/tools/firecrawl/health`
Estado del scraper.

**Response:** `{"api_key_set": true, "mode": "firecrawl", "status": "ok"}`

---

## ⚡ Watchdog & Hardware

### `GET /v1/hardware/stats`
Métricas de hardware en tiempo real.

**Response:**
```json
{
  "cpu_percent": 42.3,
  "ram_used_gb": 6.1,
  "ram_total_gb": 16.0,
  "vram_used_mb": 512,
  "vram_total_mb": 2048,
  "gpu_name": "Intel UHD Graphics 620",
  "temperature_c": 68
}
```

---

### `POST /v1/watchdog/lock`
Fija el modelo activo (evita cambio automático por watchdog).

**Request:** `{"model": "llama3.2:latest"}`

---

### `POST /v1/watchdog/unlock`
Desbloquea el modelo para que el watchdog seleccione automáticamente.

---

## 📋 Audit & Security

### `POST /v1/audit/rotate`
Fuerza la rotación del audit log activo.

**Response:** `{"archived_to": "_audit_log.bak.1748880000.jsonl", "new_log": "_audit_log.jsonl"}`

---

### `POST /v1/security/scan`
Ejecuta un escaneo completo de procesos, puertos e integridad.

**Response:** `{"score": 87, "threats": [], "open_ports": [7860, 11434]}`

---

### `POST /v1/security/kill`
Termina un proceso por PID.

**Request:** `{"pid": 9999}`

---

## 🔑 Configuration

### `POST /v1/keys`
Guarda una API key cifrada con DPAPI.

**Request:**
```json
{
  "provider": "openai",
  "key": "sk-..."
}
```

La key se cifra y almacena en `_keystore.bin`. Nunca se persiste en texto plano.

---

### `GET /v1/config`
Obtiene la configuración activa (sin exponer keys).

**Response:**
```json
{
  "base_url": "http://localhost:11434",
  "model": "llama3.2:latest",
  "daily_budget_usd": 5.0,
  "rag_enabled": true,
  "port": 7860
}
```

---

## ⚔️ Game Server

### `POST /v1/gameserver/start`
Arranca el servidor MangosD (pre-flight MySQL automático).

### `POST /v1/gameserver/stop`
Detiene MangosD y ejecuta `mysqldump` de backup.

### `GET /v1/gameserver/log`
Retorna las últimas 500 líneas del ring-buffer del servidor.

### `GET /v1/gameserver/players`
Lista de personajes conectados en tiempo real.

---

## 📡 System Status

### `GET /v1/status`
Estado de todos los backends registrados.

**Response:**
```json
{
  "backends": [
    {"name": "Ollama", "url": "http://localhost:11434", "latency_ms": 12, "status": "ok"},
    {"name": "Fooocus", "url": "http://localhost:7865", "latency_ms": null, "status": "offline"}
  ],
  "active_model": "llama3.2:latest",
  "queue_size": 2,
  "uptime_s": 3600
}
```
