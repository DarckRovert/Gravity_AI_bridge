# 🪐 Gravity AI Bridge | Wiki Corporativa V15.1 PRO Omniscient-Tier

Bienvenido al Centro de Conocimiento del Bridge — hub principal para orquestar infraestructuras pesadas con LLMs, multimedia, Game Servers, OBS Studio y agentes IA con control total.

---

## 📚 Índice de Documentación

| # | Documento | Descripción |
|---|---|---|
| 1 | [⚙️ Arquitectura](./Arquitectura.md) | Módulos, flujos y diseño del sistema |
| 2 | [🔌 Referencia de API](./API-Reference.md) | Todos los endpoints REST con ejemplos |
| 3 | [📖 Guía de API Detallada](./Guia-API.md) | Ejemplos `curl` y JSON completos |
| 4 | [📑 Manual de Usuario](./Manual-Usuario.md) | Instructivo paso a paso del Dashboard |
| 5 | [❓ FAQ](./FAQ.md) | Preguntas frecuentes y troubleshooting |
| 6 | [⚔️ Game Server Guide](./Game-Server-Guide.md) | Gestión de servidores WoW MangosD |
| 7 | [🚀 Deploy Externo VPS](./Deploy_Externo_VPS.md) | Configuración de despliegue en VPS |
| 8 | [🧠 Plan Evolución Agéntica](./Plan-Evolucion-Agentic.md) | Roadmap y diseño del Agentic Core V15.1/V16.0 |
| 9 | [💰 Manual de Monetización](./Monetizacion-Manual.md) | Operación de la Content Factory y monetización pasiva |
| 10 | [🔒 Seguridad](../SECURITY.md) | Política de seguridad y vulnerabilidades |


---

## 🚀 Novedades V15.2 PRO — Motor Cinematic V2.0 PBR

### Video Studio: Motor GLSL PBR Híbrido God-Tier
El subsistema de Video Studio ha sido elevado a un nivel de producción Hollywood mediante un motor gráfico híbrido de doble capa:

| Capa | Tecnología | Rol |
|---|---|---|
| Render 3D SDF | `moderngl` (OpenGL 3.3 Core) | Shaders PBR con reflejos IBL |
| Composición | `COMPOSITE_FS` / `POST_PROCESS_FS` | Post-procesado Hollywood |
| Shorts 9:16 | `Remotion` + React (Node.js) | Subtítulos karaoke interactivos |
| Fallback AI | FBM Procedural (Numpy) | Nebulosa cósmica sin GPU |

**Post-procesado activo en cada frame:**
- `bass > 0.85` → Cyber Glitch (desgarro de scanlines + inversion subliminal)
- `bass` → Aberración Cromática Radial (separación RGB anamórfica)
- `high` → Film Grain analógico procedural escalante
- Siempre → ACES Tone-Mapping + Viñeta Cinemática Profunda

**Generador AI Ultra-Resiliente:**
- Cascading Pollinations: `flux-realism` (90s) → `flux` (150s) → `turbo` (210s)
- Fallback: Nebulosa Fractal FBM en Numpy (6 octavas, filtro gaussiano, estrellas procedurales)

**Interfaz de Shorts Cyberpunk:**
- Fuentes `Montserrat`/`Inter` garantizadas en Chromium headless via `@import` directo en CSS
- Karaoke interactivo con glow `#00f0ff`, `cubic-bezier` de rebote orgánico
- VHS Scanlines animados CSS (barrido temporal) + Letterbox cinemático

---

## 🚀 Novedades V15.1 PRO Omniscient-Tier

### Real-Time VTuber Engine V4.0 (Aletheia V2V)
- **LivePortrait ONNX Integrado**: Se descartó la transformación ineficiente "frame-by-frame" con SD-Turbo. El sistema ahora utiliza `FasterLivePortrait` puro a 30-60 FPS procesando exclusivamente por DirectML en GPU AMD/NVIDIA.
- **Doble Fase V4.0 (Generar una vez, conducir en tiempo real)**:
  1. *Fase Generativa (Init)*: SD-Turbo se invoca una sola vez al cambiar de preset para generar un `reference_avatar` estático pero perfecto (evitando el flickering).
  2. *Fase Animación (Live)*: LivePortrait intercepta la webcam para trasladar parpadeos, rotación de cabeza y tracking labial al avatar maestro de manera hiperfluida.

### OBS Studio Control & Gravity Spark
- **OBS WebSocket v5 Integrado**: Auto-conexión activa y control total de escenas, fuentes, mute/volumen, streaming y grabación desde la API REST.
- **Gravity Spark (Motor de Overlays AI)**: Genera código HTML/JS autocontenido en tiempo real usando tu LLM local, inyectándolo directamente como `Browser Source` en OBS. Permite modificar overlays al vuelo mediante chat ("hazlo azul", "borde neón").

### Fábrica de Monetización Pasiva & Social Assets (V15.1)
- **Language Cloner**: Reutiliza renders visuales (0 gasto de GPU) traduciendo guiones (LLM) y clonando el audio a Inglés, Portugués y Francés. Multiplica el CPM orgánico de AdSense.
- **Affiliate Manager**: Banco de base de datos con programas CPA categorizados por nicho. Inyecta enlaces y CTAs optimizados en las descripciones de YouTube.
- **Social Distribution (TikTok & Instagram)**: Integración directa con TikTok Content API v2 e Instagram Graph API v19 para auto-publicar Shorts de 58s.
- **Revenue Tracker**: Tracking pasivo que estima y proyecta ganancias basándose en vistas, histórico y nicho de producción.

### Módulos Core Robustecidos
- **Turbo KV-Cache**: Conectado directamente al `engine_watchdog.py`. Detecta si el proveedor es Ollama y aplica dinámicamente `OLLAMA_KV_CACHE_TYPE=q4_0` y `OLLAMA_FLASH_ATTENTION=1`, reduciendo drásticamente el consumo de VRAM y RAM.
- **`core/hitl_manager.py`** — Human-in-the-Loop: intercepta tools de alto riesgo (code_runner, shell_exec, file_write, deploy, git_push, etc.) y requiere aprobación humana desde el Dashboard antes de ejecutarlas. Cola thread-safe con timeout de 120s.
- **`core/firecrawl_scraper.py`** — Scraping web en Markdown limpio: usa Firecrawl API si hay API key configurada, fallback HTTP nativo (`urllib`) si no. Sin dependencias externas.

---

## 🏛 Ecosistema de Paneles (Dashboard)

| Panel | Ruta Nav | Función Principal |
|---|---|---|
| 💬 Chat Auditor | `/chat` | LLM streaming con plantillas y modo auditor |
| 🏠 Mission Control | `/home` | KPIs en vivo de todo el sistema |
| 🎨 Vision Studio | `/vision` | Fooocus UI embebido (iframe) |
| 🖼️ Image Queue | `/queue` | Cola de generación Fooocus con SSE |
| 🎬 Video Studio | `/video` | Pipeline CPU-only LLM→TTS→ffmpeg |
| 👤 Aletheia V2V Studio | `/v2v` | VTuber animado en vivo con FasterLivePortrait a 30-60 FPS |
| 📹 OBS Studio Controller | `/obs` | Control total de escenas y fuentes con OBS WebSocket v5 |
| 🖼️ Image Lab | `/imagelab` | Generación Pollinations.ai con historial |
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
| 💸 Monetization Hub | `/monetization` | Centro de ingresos pasivos, SEO, CPA y automatización de nichos |
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
  <sub><i>© 2026 DarckRovert · Gravity AI Bridge V15.1 PRO Omniscient-Tier</i></sub>
</div>
