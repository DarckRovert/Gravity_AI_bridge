# Gravity AI Bridge V10.0 — Wiki
**Diamond-Tier Edition** · [github.com/DarckRovert/Gravity_AI_bridge](https://github.com/DarckRovert/Gravity_AI_bridge) · [twitch.tv/darckrovert](https://twitch.tv/darckrovert)

Bienvenido a la base de conocimientos oficial. Esta wiki cubre desde la instalación inicial hasta los detalles técnicos más profundos del sistema.

---

## Índice de Documentación

### Para empezar
| Documento | Contenido |
|:---|:---|
| [Manual de Usuario](Manual-Usuario.md) | Instalación, guía de todos los paneles del Dashboard, CLI completo, resolución de problemas |
| [FAQ](FAQ.md) | Preguntas frecuentes organizadas por tema: instalación, modelos, red, seguridad, mantenimiento |

### Referencia Técnica
| Documento | Contenido |
|:---|:---|
| [Arquitectura](Arquitectura.md) | Diseño del micro-kernel, diagrama de flujo de peticiones, módulos core con descripción técnica, sistema de seguridad |
| [Guía de API](Guia-API.md) | Todos los endpoints REST con ejemplos `curl` y Python, respuestas JSON completas, integración con LangChain / Continue.dev / Aider |

### Guías Especializadas
| Documento | Contenido |
|:---|:---|
| [Game Server Guide](Game-Server-Guide.md) | Configuración completa de vMaNGOS WoW, SOAP, jugadores online, logs |
| [Deploy Externo VPS](Deploy_Externo_VPS.md) | Migrar el servidor WoW a un VPS/Cloud con Gravity como orquestador 24/7 |

---

## Estado del Proyecto

| Categoría | Estado |
|:---|:---|
| Version | **V10.0.0 [Diamond-Tier Edition]** |
| Dashboard Paneles | **17** (cobertura completa de todos los módulos core) |
| Módulos con UI | **17 / 17** (0 módulos huérfanos) |
| Proveedores Locales | LM Studio · Ollama · KoboldCPP · Jan AI · Lemonade |
| Proveedores Cloud | Anthropic · OpenAI · Google Gemini · Groq · Mistral |
| Producto Instalable | ✅ `installer/build_installer.bat` → Setup.exe |
| Icono Multi-resolución | ✅ `make_icon.py` → `assets/gravity_icon.ico` |

---

## Arquitectura en una Línea

```
CLIENTE → POST /v1/chat/completions → bridge_server.py → provider_manager → Ollama/LMStudio/Claude
```

---

## Estructura de Archivos Clave

```
bridge_server.py      ← Servidor HTTP (puerto 7860)
core/                 ← 20+ módulos del micro-kernel
providers/            ← Plugins de proveedores (local + cloud)
tools/                ← 6 herramientas del agente
rag/                  ← Motor RAG (búsqueda semántica local)
web/dashboard.html    ← SPA Dashboard (17 paneles)
installer/            ← Build comercial (PyInstaller + Inno Setup)
wiki/                 ← Esta documentación
```

---

## Inicio Rápido (3 comandos)

```bash
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge && pip install -r requirements.txt
python bridge_server.py
# → Dashboard: http://localhost:7860
```

---

## Links

- **Repositorio:** [github.com/DarckRovert/Gravity_AI_bridge](https://github.com/DarckRovert/Gravity_AI_bridge)
- **Issues & Bugs:** [github.com/DarckRovert/Gravity_AI_bridge/issues](https://github.com/DarckRovert/Gravity_AI_bridge/issues)
- **Twitch:** [twitch.tv/darckrovert](https://twitch.tv/darckrovert)
- **Licencia:** MIT © 2026 DarckRovert

---

*Mantenido por DarckRovert & Antigravity AI.*
