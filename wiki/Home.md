# 🪐 Gravity AI Bridge | Wiki Corporativa V12.1 Omniscient-Tier

Bienvenido al Centro de Conocimiento del Bridge — hub principal para orquestar infraestructuras pesadas con LLMs, multimedia, Game Servers y agentes IA con control total.

---

## 📚 Índice de Documentación

| # | Documento | Descripción |
|---|---|---|
| 1 | [⚙️ Arquitectura](./Arquitectura.md) | Módulos, flujos y diseño del sistema |
| 2 | [🔌 Referencia de API](./API-Reference.md) | Todos los endpoints REST con ejemplos |
| 3 | [📖 Guía de API Detallada](./Guia-API.md) | Ejemplos `curl` y JSON completos |
| 4 | [📑 Manual de Usuario](./Manual-Usuario.md) | Instructivo paso a paso del Dashboard |
| 5 | [❓ FAQ](./FAQ.md) | Preguntas frecuentes y troubleshooting |
| 6 | [🏠 Game Server Guide](./Game-Server-Guide.md) | Gestión de servidores WoW MangosD |
| 7 | [🚀 Deploy Externo VPS](./Deploy_Externo_VPS.md) | Configuración de despliegue en VPS |
| 8 | [🔒 Seguridad](../SECURITY.md) | Política de seguridad y vulnerabilidades |

---

## 🚀 Novedades V12.1 Omniscient-Tier

### Arquitectura Frontend SPA (React/Vite)
- **Eliminación de HTML Estático:** Sustitución completa del dashboard monolítico antiguo por un framework moderno React/Vite.
- **Interconectividad Total:** Los 25 componentes operativos ahora interactúan directamente con el backend Python a través del Bridge REST API.
- **Reproductor de Video Embebido:** Previsualización de videos renderizados directamente en el frontend usando `/v1/video/stream`.

### Control de Hardware y Seguridad
- **Hook Activo:** Las interfaces de aniquilación de sesiones (`/v1/sessions/kill`), seguridad y monitoreo de procesos, reaccionan con 0% de maquetas desconectadas.
- **Saneamiento UI:** Endpoints como `seed`, `enhance` de *Vision Studio*, y los selectores reales de modo y n_agents en *MultiAgent* fueron completamente integrados.
- **`core/hitl_manager.py`** — Human-in-the-Loop: intercepta tools de alto riesgo (code_runner, shell_exec, file_write, deploy, git_push, etc.) y requiere aprobación humana desde el Dashboard antes de ejecutarlas. Cola thread-safe con timeout de 120s.
- **`core/firecrawl_scraper.py`** — Scraping web en Markdown limpio: usa Firecrawl API si hay API key configurada, fallback HTTP nativo (`urllib`) si no. Sin dependencias externas.

### Nuevos Endpoints
- `GET /v1/hitl/pending` — Lista solicitudes de aprobación pendientes
- `POST /v1/hitl/approve` — Aprueba una acción del agente
- `POST /v1/hitl/reject` — Rechaza una acción del agente
- `POST /v1/tools/scrape` — Scraping de URL
- `GET /v1/tools/firecrawl/health` — Estado de la configuración Firecrawl

### Dashboard V11.0
- **Nuevo Panel HITL Approval**: Aprobación/rechazo en tiempo real con polling cada 8s. Badge rojo en el sidebar cuando hay solicitudes pendientes.
- **Nuevo Panel Firecrawl**: Scraper interactivo con viewer de resultado Markdown.
- **Sessions — Role Selector**: Selector de rol al hacer Spawn (auditor/planner/coder/researcher/executor).
- **Rediseño CSS completo**: Nueva paleta Diamond `#07090e/#6366f1`, animaciones premium, tipografía Inter 900.
- **Fix Bug switchTab**: Eliminada colisión de override doble en JavaScript.

---

## 🏛 Ecosistema de Paneles (Dashboard)

| Panel | Ruta Nav | Función Principal |
|---|---|---|
| 💬 Chat Auditor | `/chat` | LLM streaming con plantillas y modo auditor |
| 🏠 Mission Control | `/home` | KPIs en vivo de todo el sistema |
| 🎨 Vision Studio | `/vision` | Fooocus UI embebido (iframe) |
| 🖼️ Image Queue | `/queue` | Cola de generación Fooocus con SSE |
| 🎬 Video Studio | `/video` | Pipeline CPU-only LLM→TTS→ffmpeg |
| 🎨 Image Lab | `/imagelab` | Generación Pollinations.ai con historial |
| 🚀 Deploy | `/deploy` | FabricaWeb CI/CD pipeline |
| ⚔️ Game Servers | `/gameserver` | Control MangosD WoW |
| 🤖 Multi-Agent | `/multiagent` | Comparación/voting multi-modelo |
| 🖥️ Hardware | `/hardware` | GPU/VRAM/CPU/NPU en tiempo real |
| 💰 Cost Center | `/cost` | Costos por proveedor y límites |
| ⚡ Watchdog | `/watchdog` | Lock/unlock de modelo activo |
| 💾 Sessions | `/sessions` | Sesiones persistentes + workers activos |
| 📚 RAG | `/rag` | Índice RAG y toggle de inyección en chat |
| 🔌 MCP Servers | `/mcp` | Adaptadores MCP: tools y resources |
| 🛠️ Tools | `/tools` | Code Runner, Web Search, Git, Grep |
| ⚡ Tools Pro | `/tools-pro` | Terminal reactiva avanzada |
| 🕷️ Firecrawl | `/firecrawl` | Scraping web en Markdown |
| 🛡️ HITL Approval | `/hitl` | Aprobación humana de tools de riesgo |
| 📡 System Status | `/status` | Estado completo de backends |
| 🔒 Security | `/security` | Monitor de procesos y puertos |
| 📋 Audit Log | `/audit` | Historial de peticiones |
| ⚙️ Configuración | `/config` | API keys y configuración general |

---

## 🌐 Infraestructura Base

```
Puerto por defecto: 7860 (configurable en config.yaml)
Protocolo: HTTP/1.1 puro (ThreadingHTTPServer)
Compatibilidad: OpenAI API v1 (drop-in replacement)
```

**Backends compatibles:**
- Ollama (local)
- LM Studio (local)
- Kobold.cpp (local)
- Jan (local)
- OpenAI (cloud)
- Anthropic Claude (cloud)
- Cualquier backend OpenAI-compatible

---

## 🔗 Links del Ecosistema DarckRovert

- **GitHub**: [github.com/DarckRovert](https://github.com/DarckRovert)
- **Twitch**: [twitch.tv/darckrovert](https://twitch.tv/darckrovert)
- **Issues**: [github.com/DarckRovert/Gravity_AI_bridge/issues](https://github.com/DarckRovert/Gravity_AI_bridge/issues)
- **Releases**: [github.com/DarckRovert/Gravity_AI_bridge/releases](https://github.com/DarckRovert/Gravity_AI_bridge/releases)

---

<div align="center">
  <sub><i>© 2026 DarckRovert · Gravity AI Bridge V12.1 Omniscient-Tier</i></sub>
</div>
