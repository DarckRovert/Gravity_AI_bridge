# 🔌 Referencia Completa de API — Gravity AI Bridge V10.4

Todos los endpoints del Bridge. Puerto por defecto: `7860`. Base URL: `http://localhost:7860`.

---

## 📡 Sistema y Telemetría

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/health` | Health check básico del bridge |
| GET | `/v1/status` | Estado completo: proveedor activo, backends, latencias |
| GET | `/v1/models` | Lista de modelos disponibles (OpenAI-compatible) |
| GET | `/metrics` | Métricas Prometheus |

---

## 🧠 Chat / Completions (OpenAI-Compatible)

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/v1/chat/completions` | Chat con streaming SSE o respuesta completa |
| POST | `/v1/completions` | Completions (legacy, redirige a chat) |

**Parámetros `POST /v1/chat/completions`:**
```json
{
  "model": "gravity-bridge-auto",
  "messages": [{"role": "user", "content": "Hola"}],
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 2048
}
```

---

## 🤖 Multi-Agent Orchestrator

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/v1/agent/compare` | Compara respuestas de N modelos en paralelo |

**Parámetros:**
```json
{
  "messages": [{"role": "user", "content": "..."}],
  "n_models": 3,
  "mode": "parallel"
}
```
`mode`: `"parallel"` (independientes) | `"vote"` (votación consensuada).

---

## 💾 Session Manager

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/sessions` | Lista sesiones persistentes guardadas en `_saves/` |
| GET | `/v1/sessions/active` | Workers activos (subprocesos spawneados) |
| POST | `/v1/sessions/spawn` | Crea un nuevo worker con rol opcional |
| POST | `/v1/sessions/kill` | Termina un worker activo |

**Spawn Worker:**
```json
{
  "session_id": "dev-1",
  "role": "auditor"
}
```
`role`: `"auditor"` | `"planner"` | `"coder"` | `"researcher"` | `"executor"` | `""` (default).

---

## 🛡️ HITL — Human in the Loop

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/hitl/pending` | Lista solicitudes de aprobación en espera |
| POST | `/v1/hitl/approve` | Aprueba una acción del agente |
| POST | `/v1/hitl/reject` | Rechaza una acción del agente |

**Approve/Reject:**
```json
{"approval_id": "abc123"}
{"approval_id": "abc123", "reason": "Acción no autorizada en producción"}
```

**Tools de Alto Riesgo (requieren aprobación):**
`code_runner`, `shell_exec`, `file_write`, `file_delete`, `deploy`, `git_push`, `git_commit`, `send_email`, `send_request`, `database_write`

---

## 🕷️ Firecrawl / Web Scraper

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/tools/firecrawl/health` | Estado de la API key y modo |
| POST | `/v1/tools/scrape` | Scraping de URL en Markdown |

**Scrape:**
```json
{"url": "https://ejemplo.com/articulo"}
```

**Respuesta:**
```json
{
  "ok": true,
  "url": "https://ejemplo.com/articulo",
  "title": "Título de la página",
  "content": "# Contenido en Markdown...",
  "source": "firecrawl"
}
```
`source`: `"firecrawl"` (API premium) | `"fallback_html"` (sin API key).

---

## 🔌 MCP Servers

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/mcp/status` | Estado de adaptadores MCP y sus tools/resources |
| GET | `/v1/mcp/resource?server=X&uri=Y` | Lee un recurso específico de un servidor MCP |

---

## 📚 RAG (Retrieval-Augmented Generation)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/rag/status` | Estado del índice RAG (documentos, chunks, tamaño) |
| POST | `/v1/rag/toggle` | Activa/desactiva inyección RAG en chat |

**Toggle:**
```json
{"enabled": true}
```

---

## 🎨 Image Queue (Fooocus)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/fooocus/status` | Health check del motor Fooocus (puerto 7861) |
| GET | `/v1/queue` | Estado completo de la cola de imágenes |
| GET | `/v1/queue/stream` | SSE stream del progreso del job activo |
| GET | `/v1/images` | Lista de imágenes generadas |
| POST | `/v1/queue/add` | Añadir trabajo a la cola |
| POST | `/v1/generate` | Generación directa via Fooocus |

---

## 🎨 Image Lab (Pollinations.ai)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/image/health` | Estado de conectividad con Pollinations.ai |
| GET | `/v1/image/lab/history` | Historial de imágenes generadas |
| POST | `/v1/image/generate` | Generación via Pollinations.ai |

**Generate:**
```json
{
  "prompt": "A futuristic city at night",
  "model": "flux",
  "width": 1024,
  "height": 1024,
  "enhance": true,
  "seed": 42
}
```

---

## 🎬 Video Studio (CPU-Only)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/video/status` | Estado completo de la cola de video |
| GET | `/v1/video/voices` | Lista de voces SAPI disponibles |
| GET | `/v1/video/download?file=nombre.mp4` | Descarga un video generado |
| POST | `/v1/video/create` | Encola un trabajo de video |
| POST | `/v1/video/cancel` | Cancela un trabajo pendiente |

**Create:**
```json
{
  "topic": "Historia de la Inteligencia Artificial",
  "n_scenes": 6,
  "voice_id": "Microsoft Helena Desktop",
  "voice_speed": 150,
  "style": "documental",
  "narration_lang": "es",
  "transitions": true,
  "subtitles": true,
  "resolution": "1024x1024"
}
```

---

## ⚔️ Game Server (World of Warcraft MangosD)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/gameserver/status` | Estado de todos los servidores configurados |
| GET | `/v1/gameserver/log?server=wow_vanilla&lines=100` | Log en vivo (Ring-Buffer RAM) |
| GET | `/v1/gameserver/players?server=wow_vanilla` | Lista de jugadores conectados |
| POST | `/v1/gameserver/start` | Inicia un servidor |
| POST | `/v1/gameserver/stop` | Detiene un servidor |
| POST | `/v1/gameserver/restart` | Reinicia un servidor |
| POST | `/v1/gameserver/command` | Envía comando de consola |
| POST | `/v1/gameserver/register` | Crea cuenta de jugador (SRP-6a) |
| POST | `/v1/gameserver/expose` | Expone el servidor a WAN |
| POST | `/v1/gameserver/backup` | Backup manual de la base de datos |
| GET | `/registro` | Formulario web de creación de cuenta |

---

## 🚀 Deploy / FabricaWeb

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/deploy/status` | Estado del último pipeline de deploy |
| GET | `/v1/fabricaweb/status` | Estado del proyecto FabricaWeb activo |
| POST | `/v1/deploy` | Inicia deploy de un proyecto web |
| POST | `/v1/fabricaweb/deploy` | Deploy específico de FabricaWeb → Netlify |

---

## 🖥️ Hardware & Sistema

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/hardware` | Perfil completo: GPUs, VRAM, NPU, CPU, RAM |
| GET | `/v1/cost` | Costos de sesión, diarios, breakdown por proveedor |
| GET | `/v1/watchdog` | Estado del Engine Watchdog y lock de modelo |
| POST | `/v1/watchdog/unlock` | Desbloquea el modelo para auto-switch |
| GET | `/v1/audit` | Historial de peticiones (últimas 100) |
| POST | `/v1/audit/rotate` | Fuerza rotación del audit log |

---

## 🔐 Seguridad

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/security` | Estado del Security Monitor |
| GET | `/v1/security/geoip` | Tracker de IPs externas con geolocalización |
| POST | `/v1/security/scan` | Fuerza un escaneo de seguridad inmediato |
| POST | `/v1/security/kill` | Termina un proceso sospechoso por PID |

---

## 🛠️ Tools

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/v1/tools/run` | Ejecuta código Python/Bash |
| POST | `/v1/tools/search` | Búsqueda web DuckDuckGo |
| POST | `/v1/tools/git` | Operaciones Git (status/log/diff/branch) |
| POST | `/v1/tools/grep` | Búsqueda de patrones en archivos |
| POST | `/v1/tools/scrape` | Scraping de URL (Firecrawl/fallback) |

---

## ⚙️ Configuración

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/v1/keys` | Guarda una API key (cifrada con DPAPI) |
| POST | `/v1/ai/start` | Inicia un motor de IA (provider) |
| POST | `/v1/ai/stop` | Detiene un motor de IA |

---

## 🗂️ Archivos Estáticos

| Ruta | Descripción |
|---|---|
| `GET /static/output/<subcarpeta>/<archivo>` | Imágenes de Fooocus |
| `GET /static/imagelab/<archivo>` | Imágenes de Image Lab |

---

<div align="center">
  <sub><i>© 2026 DarckRovert · Gravity AI Bridge V10.4 · Referencia API Completa</i></sub>
</div>
