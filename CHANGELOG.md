# CHANGELOG — Gravity AI Bridge

El formato sigue [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
La versión técnica de referencia es siempre la presente en el archivo `.toc` del addon local.

---

## [10.0.0] — 2026-04-17 · Diamond-Tier Edition

### Added — Dashboard
- 17 paneles con cobertura total de todos los módulos core (0 módulos huérfanos)
- Panel **Hardware Monitor**: GPU/VRAM/NPU detection, tabla multi-GPU, badge ROCm/CUDA/iGPU/Vulkan, contexto óptimo calculado
- Panel **Multi-Agent Orchestrator**: comparativa paralela/vote, N modelos simultáneos, result cards con proveedor y elapsed time
- Panel **Cost Center**: coste de sesión, coste diario, barra de límite USD, breakdown por proveedor cloud
- Panel **Engine Watchdog**: estado LOCKED/AUTO-SWITCH, botón Forzar Unlock, info de hardware del motor activo
- Panel **Session Manager**: tabla de sesiones guardadas en `_saves/` con nombre, branch, turnos y timestamp
- Panel **RAG**: estado del índice (doc_count, chunk_count, size_mb, online/offline)
- Panel **MCP Servers**: documentación interactiva para configurar servidores Model Context Protocol en `config.yaml`
- Panel **Tools**: inventario de 6 herramientas con estado (Code Runner, File Edit V2, Web Search, Git Tool, Grep Tool, Native Trigger)

### Added — Backend / API
- `GET /v1/hardware` — perfil completo de hardware desde `hardware_profiler.py`
- `GET /v1/cost` — costes USD desde `cost_tracker.py` con breakdown diario
- `GET /v1/watchdog` — estado del motor activo y lock desde `engine_watchdog.py`
- `GET /v1/sessions` — lista de sesiones JSON desde `_saves/`
- `GET /v1/rag/status` — estado del índice RAG desde `_rag_index/`
- `POST /v1/agent/compare` — orquestación parallel/vote desde `multi_agent.py`
- `POST /v1/watchdog/unlock` — desbloqueo del modelo forzado manualmente

### Added — Producto Comercial
- `gravity_tray.py` — icono de bandeja del sistema con pulso durante arranque, menú contextual
- `gravity_launcher.pyw` — launcher silencioso sin consola con single-instance guard (PID file)
- `installer/gravity_setup.iss` — script Inno Setup 6: autostart Windows, acceso directo escritorio, desinstalador limpio
- `installer/build_installer.bat` — build automatizado completo: PyInstaller → EXE → Inno Setup → Setup.exe
- `make_icon.py` — generador standalone del `assets/gravity_icon.ico` multi-resolución (256/128/64/48/32/16 px)
- `assets/gravity_icon.ico` — icono generado con Pillow, incluido en el repositorio

### Added — Sistema
- `engine_watchdog.start(verbose=True)` añadido a `run_server()` — el Watchdog ahora arranca automáticamente con el Bridge
- `import engine_watchdog` añadido al bloque de imports de `bridge_server.py`

### Fixed
- `exposeWan()` en Dashboard: reemplazado `prompt()` nativo del navegador (bloqueado en algunos contextos) por Modal HTML custom con `backdrop-filter`
- `dashboard.py`: docstring desactualizado "V9.4 PRO" → "V10.0 [Diamond-Tier Edition]"
- `core/ide_integrator.py`: strings de versión "V9.3.1 PRO" → "V10.0" en header y config de Continue.dev
- `installer/build_installer.bat`: `pip install --quiet` reemplazado por salida visible + `--trusted-host` para entornos corporativos. Añadido Paso 0 de auto-generación del `.ico`
- Gráfico de latencia en Dashboard: fill con gradiente CSS, glow en el stroke, punto indicador animado y label de valor actual

### Documentation
- `README.md`: reescrito con hero section, tabla de 17 paneles, instalación dual, tabla de proveedores, arquitectura, seguridad
- `CONTRIBUTING.md`: reescrito con entorno de desarrollo, estándares por tipo de archivo, conveción de commits con ejemplos, tabla de "dónde añadir qué"
- `SECURITY.md`: tabla de versiones soportadas, proceso de divulgación responsable, modelo de seguridad técnico, tabla de vectores de ataque
- `CODE_OF_CONDUCT.md`: reescrito de forma directa y técnica
- `wiki/Manual-Usuario.md`: guía detallada de cada panel (+300 líneas), parámetros específicos, CLI completo, resolución de problemas
- `wiki/FAQ.md`: 25 preguntas por secciones temáticas con instrucciones concretas y tablas
- `wiki/Guia-API.md`: todos los endpoints con ejemplos curl + Python SDK + LangChain + respuestas JSON
- `wiki/Arquitectura.md`: diagrama ASCII, estructura de directorios, flujo técnico, descripción de 20+ módulos, tabla de 17 paneles
- `wiki/Home.md`: índice de la wiki con tabla de documentos y estado del proyecto
- `.github/ISSUE_TEMPLATE/bug_report.md`: tabla de entorno (GPU/proveedor/modelo), checklist previo
- `.github/ISSUE_TEMPLATE/feature_request.md`: enfoque arquitectónico, tipo de cambio, compatibilidad
- `.github/PULL_REQUEST_TEMPLATE.md`: checklist específico del proyecto Bridge

### Dependencies
- Añadidos a `requirements.txt`: `pystray>=0.19`, `Pillow>=10.0`, `pyinstaller>=6.0`, `psutil>=5.9`

---

## [10.0.0-rc1] — 2026-04-17

### Added
- Sistema de Toasts nativo en el Dashboard para alertas no intrusivas
- Whitelist de puertos WoW en `security_monitor.py` (3724, 8085, 7878)
- Módulo `core/reasoning_stripper.py`: extracción de lógica `<think>...</think>` como módulo compartido
- Plantillas de Issues y PRs en `.github/`

### Fixed
- Race condition en `deploy_manager.py`: sincronización con `threading.Lock`
- Audit Log timestamps: zona horaria UTC con sufijo `Z`
- SQLite: eliminadas conexiones duplicadas en `cache_engine.py`
- Rate Limiter: clave de configuración corregida a `rate_limit.requests_per_minute`
- Credenciales MaNGOS: eliminados usuarios/passwords hardcodeados en `game_server_manager.py`
- Dashboard hot-reload: eliminado servidor HTTP secundario redundante

### Removed
- Dependencia de Gradio eliminada de `requirements.txt` (~500 MB de ahorro)
- Copias locales de `ReasoningStripper` en `bridge_server.py` y `ask_deepseek.py`

---

## [9.3.1 PRO] — 2026-04-13

- Versión base previa a la auditoría integral V10.0
- Implementación inicial de la arquitectura SOC (Security Operations Center)
- Soporte para DPAPI en Windows para cifrado de API keys
- Primera integración de `game_server_manager.py` para vMaNGOS

---

*Para el historial completo de versiones anteriores a V9.3.1, consultar el git log.*
