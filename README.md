# Gravity AI Bridge V10.0 [Diamond-Tier Edition]

[![License: MIT](https://img.shields.io/badge/License-MIT-7c3aed.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-10.0-4f46e5.svg)](CHANGELOG.md)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4.svg)]()
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)]()

> Orquestador de IA local de alto rendimiento. Enruta llamadas OpenAI-compatible hacia los mejores modelos disponibles en tu hardware, con Dashboard web, monitoreo en tiempo real y empaquetado comercial.

---

## Características

- **Enrutamiento Inteligente** — auto-switch entre LM Studio, Ollama, Kobold, Jan, Lemonade y proveedores cloud
- **Dashboard Web (17 paneles)** — UI glassmorphism completa, no se requiere ningún cliente externo
- **Hardware Monitor** — detección de GPU/VRAM/NPU con recomendación de contexto óptimo
- **Multi-Agent Orchestrator** — comparativa paralela entre múltiples modelos (modo Paralelo o Vote)
- **Cost Center** — tracking en tiempo real de costes USD para proveedores cloud
- **Engine Watchdog** — auto-switch con lock/unlock de modelo manual
- **RAG integrado** — búsqueda semántica en documentos locales sin enviar datos a la nube
- **Session Manager** — sesiones persistentes con fork de branches
- **MCP Protocol** — integración con servidores Model Context Protocol externos
- **Tools** — code runner, git, web search, grep, file edit, native trigger
- **Game Server Manager** — arranque/parada de vMaNGOS con gestión de cuentas y WAN
- **Deploy Manager** — pipeline npm build + netlify deploy
- **Security Monitor** — escaneo Zero-Trust en background
- **Audit Log** — trazabilidad completa de todas las peticiones
- **Empaquetado Comercial** — instalador Inno Setup + icono de bandeja del sistema

---

## Instalación Rápida (Desarrollador)

```bash
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
pip install -r requirements.txt
python INSTALAR.py          # Configuración interactiva
python bridge_server.py     # Inicia el servidor
# Dashboard: http://localhost:7860
```

---

## Build Comercial (Instalador .exe)

```bash
# Requiere Inno Setup 6: https://jrsoftware.org/isdl.php
installer\build_installer.bat
# Genera: dist\Gravity_AI_Bridge_V10.0_Setup.exe
```

---

## Arquitectura

```
bridge_server.py          ← HTTP handler principal (17 GET + 12 POST endpoints)
core/
  provider_manager.py     ← Escaneo y selección de proveedores
  engine_watchdog.py      ← Auto-switch con lock/unlock
  hardware_profiler.py    ← GPU/VRAM/NPU detection
  cost_tracker.py         ← Tracking USD
  multi_agent.py          ← Orquestador paralelo/vote
  session_manager.py      ← Sesiones con fork
  mcp_adapter.py          ← Model Context Protocol
  security_monitor.py     ← Zero-Trust scanning
  deploy_manager.py       ← Pipeline build/deploy
  ai_process_manager.py   ← Start/stop motores IA
  rag/                    ← Retrieval Augmented Generation
providers/
  local/                  ← Ollama, LM Studio, Kobold, Jan, Lemonade
  cloud/                  ← Anthropic, OpenAI, Gemini, Groq
tools/                    ← code_runner, git_tool, web_search, grep_tool
web/dashboard.html        ← SPA servida en http://localhost:7860
```

---

## Documentación

- [Arquitectura del Sistema](wiki/Arquitectura.md)
- [Guía de API](wiki/Guia-API.md)
- [Manual de Usuario](wiki/Manual-Usuario.md)
- [FAQ](wiki/FAQ.md)
- [Game Server Guide](wiki/Game-Server-Guide.md)

---

## Proveedores Soportados

| Proveedor | Tipo | Detección |
|:---|:---|:---|
| LM Studio | local | Automática (puerto 1234) |
| Ollama | local | Automática (puerto 11434) |
| KoboldCPP | local | Automática (puerto 5001) |
| Jan AI | local | Automática (puerto 1337) |
| Lemonade | local | Automática (puerto 8000) |
| Anthropic Claude | cloud | API Key via config |
| OpenAI | cloud | API Key via config |
| Google Gemini | cloud | API Key via config |
| Groq | cloud | API Key via config |

---

## Integración con IDEs

```bash
python core/ide_integrator.py todo     # Configura Continue.dev + Aider + Cursor
```

O desde el Dashboard → Configuración → IDE Setup.

---

## Licencia

MIT © 2026 DarckRovert — [github.com/DarckRovert](https://github.com/DarckRovert)

Twitch: [twitch.tv/darckrovert](https://twitch.tv/darckrovert)
