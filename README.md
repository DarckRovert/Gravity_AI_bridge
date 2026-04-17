<div align="center">

# ⚡ Gravity AI Bridge

### V10.0 · Diamond-Tier Edition

**Orquestador de IA local-first. Un punto de entrada. Todos tus modelos.**

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-10.0-4f46e5.svg)](CHANGELOG.md)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4.svg)]()
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)]()
[![Providers](https://img.shields.io/badge/Providers-10-22c55e.svg)]()
[![Panels](https://img.shields.io/badge/Dashboard_Panels-17-f59e0b.svg)]()

[📖 Manual de Usuario](wiki/Manual-Usuario.md) · [🔌 API Reference](wiki/Guia-API.md) · [🏗️ Arquitectura](wiki/Arquitectura.md) · [🐛 Reportar Bug](https://github.com/DarckRovert/Gravity_AI_bridge/issues)

</div>

---

## ¿Qué es Gravity AI Bridge?

Gravity AI Bridge es un **servidor proxy OpenAI-compatible** que actúa como punto de entrada único para cualquier modelo de IA — local o en la nube — con un Dashboard web de 17 paneles que no requiere configuración adicional.

Apunta tu IDE, terminal o aplicación a `http://localhost:7860/v1` y Gravity selecciona automáticamente el mejor modelo disponible, monitorea el hardware, registra costes y te avisa si algo falla.

```
Continue.dev ──┐
  Aider ────── ┤──► http://localhost:7860/v1 ──► Ollama / LM Studio / Claude / GPT-4o
  Cursor ────── ┤                              ↑ Auto-Switch por latencia
  Tu app ────── ┘                              └ Hardware Monitor + Cost Tracker
```

---

## Dashboard — 17 Paneles en el Navegador

| Panel | Función |
|:---|:---|
| 💬 **Chat Auditor** | Chat directo con streaming en tiempo real al modelo activo |
| 🎨 **Vision Studio** | Generación de imágenes via Fooocus (local, sin API externa) |
| 🖼️ **Image Queue** | Cola de trabajos de generación con estado en tiempo real |
| 🚀 **Deploy** | Pipeline `npm build` → `netlify deploy --prod` en un clic |
| ⚔️ **Game Servers** | Control completo de vMaNGOS WoW: start/stop/SOAP/jugadores/WAN |
| 🤖 **Multi-Agent** | Envía el mismo prompt a N modelos en paralelo y compara respuestas |
| 🖥️ **Hardware Monitor** | GPU/VRAM/NPU detection, contexto óptimo calculado por hardware |
| 💰 **Cost Center** | Tracking USD en tiempo real solo para proveedores cloud |
| ⚡ **Engine Watchdog** | Auto-switch con estado LOCKED/AUTO y botón de unlock manual |
| 💾 **Sessions** | Sesiones conversacionales persistentes con soporte de branches |
| 📚 **RAG** | Estado del índice de documentos local (sin enviar datos a internet) |
| 🔌 **MCP Servers** | Guía interactiva para conectar servidores Model Context Protocol |
| 🛠️ **Tools** | Inventario de herramientas: code runner, git, web search, grep, y más |
| 📡 **System Status** | Estado de proveedores, latencias y gráfico histórico |
| 🛡️ **Security** | Escaneo Zero-Trust con historial de amenazas detectadas |
| 📋 **Audit Log** | Historial completo de peticiones: proveedor, tokens, coste, latencia |
| ⚙️ **Configuración** | API keys cifradas con DPAPI, IDE setup, proyecto de deploy |

---

## Instalación

### Opción A — Instalador (usuarios sin Python)

```
1. Descarga Gravity_AI_Bridge_V10.0_Setup.exe
2. Ejecuta como Administrador → Siguiente → Siguiente → Instalar
3. Icono en la bandeja del sistema → click → Dashboard en el navegador
```

### Opción B — Modo desarrollador

```bash
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
pip install -r requirements.txt
python INSTALAR.py          # Asistente de configuración inicial
python bridge_server.py     # Inicia en http://localhost:7860
```

### Build del instalador .exe

```bash
# Requiere Inno Setup 6 → https://jrsoftware.org/isdl.php
installer\build_installer.bat
# → dist\Gravity_AI_Bridge_V10.0_Setup.exe
```

> El icono `.ico` se genera automáticamente si no existe. No se requiere configuración previa.

### Requisitos mínimos

| | Mínimo | Recomendado |
|:---|:---|:---|
| **OS** | Windows 10 (1809) x64 | Windows 11 |
| **Python** | 3.11 | 3.12 |
| **RAM** | 8 GB | 32 GB |
| **GPU** | Opcional (CPU funciona) | 8+ GB VRAM |

---

## Proveedores Soportados

### Locales — detección automática por puerto, cero configuración

| Motor | Puerto | Obtener |
|:---|:---|:---|
| **Ollama** | 11434 | [ollama.com](https://ollama.com) |
| **LM Studio** | 1234 | [lmstudio.ai](https://lmstudio.ai) |
| **KoboldCPP** | 5001 | [github.com/LostRuins/koboldcpp](https://github.com/LostRuins/koboldcpp) |
| **Jan AI** | 1337 | [jan.ai](https://jan.ai) |
| **Lemonade** | 8000 | AMD ROCm Edge |

### Cloud — con API key configurada en el Dashboard

| Proveedor | Modelos destacados |
|:---|:---|
| **Anthropic** | Claude 3.5 Sonnet, Claude 3.7 Opus |
| **OpenAI** | GPT-4o, o1, o3 |
| **Google** | Gemini 2.0 Flash, Gemini 1.5 Pro |
| **Groq** | LLaMA 3.3 70B (ultra-rápido) |
| **Mistral AI** | Mistral Large, Mistral Nemo |

---

## Integración con IDEs en 1 comando

```bash
python core/ide_integrator.py todo
# Configura Continue.dev + Aider + Cursor simultáneamente
# apuntando todos a http://localhost:7860/v1
```

Con cualquier cliente OpenAI-compatible (LangChain, Open WebUI, etc.):
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:7860/v1", api_key="gravity-local")
```

---

## Arquitectura

```
bridge_server.py              ← ThreadingHTTPServer :7860 (29 endpoints)
│
├── core/
│   ├── provider_manager.py   ← scan_all() + get_best() + stream()
│   ├── engine_watchdog.py    ← auto-switch daemon (cada 30s)
│   ├── hardware_profiler.py  ← GPU/VRAM/NPU → num_ctx óptimo
│   ├── cost_tracker.py       ← registro USD por proveedor cloud
│   ├── multi_agent.py        ← parallel/vote orchestrator
│   ├── session_manager.py    ← persistencia JSON + fork branches
│   ├── mcp_adapter.py        ← JSON-RPC client para MCP servers
│   ├── security_monitor.py   ← Zero-Trust background scanner
│   ├── key_manager.py        ← DPAPI — cifrado de API keys
│   ├── deploy_manager.py     ← npm build + netlify deploy
│   ├── game_server_manager.py← vMaNGOS lifecycle + SOAP
│   ├── ai_process_manager.py ← start/stop motores locales
│   └── rag/                  ← embeddings locales + búsqueda semántica
│
├── providers/
│   ├── local/                ← ollama, lmstudio, kobold, jan, lemonade
│   └── cloud/                ← anthropic, openai, gemini, groq, mistral
│
├── tools/                    ← code_runner, git, web_search, grep, file_edit
├── web/dashboard.html        ← SPA 17 paneles (~1800 líneas, glassmorphism)
└── installer/                ← PyInstaller + Inno Setup → Setup.exe
```

---

## Características de Seguridad

- **DPAPI** — API keys cifradas con la identidad del usuario Windows. Sin texto plano en disco
- **Rate Limiting** — Por IP y por key. Configurable por ventana de tiempo
- **Audit Log** — `_audit_log.jsonl` append-only. Cada petición trazada permanentemente
- **Zero-Trust Scanner** — Hilo background que detecta patrones anómalos de acceso
- **Local-First** — Los proveedores locales tienen prioridad sobre cloud en el auto-switch

---

## Documentación Completa

| Documento | Descripción |
|:---|:---|
| [Manual de Usuario](wiki/Manual-Usuario.md) | Guía detallada de cada panel, CLI completo, resolución de problemas |
| [Guía de API](wiki/Guia-API.md) | Todos los endpoints con ejemplos curl/Python/LangChain |
| [Arquitectura](wiki/Arquitectura.md) | Diseño del micro-kernel, flujo técnico, 20+ módulos |
| [FAQ](wiki/FAQ.md) | Preguntas frecuentes por tema: instalación, modelos, red, seguridad |
| [Game Server Guide](wiki/Game-Server-Guide.md) | Configuración completa de vMaNGOS WoW |
| [Deploy Externo VPS](wiki/Deploy_Externo_VPS.md) | Migración a servidor cloud 24/7 |

---

## Contribuir

Lee [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir un PR.  
Para vulnerabilidades de seguridad, sigue el protocolo en [SECURITY.md](SECURITY.md) — **no abras un Issue público**.

---

<div align="center">

**Strictly Non-Commercial**: This software is owned by DarckRovert. Commercial use for profit is prohibited. <br>
**Estrictamente No-Comercial**: Este software es propiedad de DarckRovert. El uso comercial con fines de lucro está prohibido.

<br>
© 2026 [DarckRovert](https://github.com/DarckRovert) · [twitch.tv/darckrovert](https://twitch.tv/darckrovert)

</div>
