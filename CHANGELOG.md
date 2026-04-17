# CHANGELOG — Gravity AI Bridge

## [10.0.0] — 2026-04-17 [Diamond-Tier Edition]

### Added
- Dashboard 17 paneles: Sessions, RAG, MCP Servers, Tools (completando cobertura de todos los módulos core)
- Panel Hardware Monitor: GPU/VRAM/NPU detection, tabla de todas las GPUs, badge ROCm/CUDA/iGPU
- Panel Multi-Agent Orchestrator: comparativa paralela/vote, N modelos, result cards con elapsed
- Panel Cost Center: dial de sesión, barra de límite diario, breakdown por proveedor
- Panel Engine Watchdog: estado LOCKED/AUTO, botón Forzar Unlock, info de hardware del motor
- Panel Session Manager: lista de sesiones guardadas desde `_saves/` con branch y turnos
- Panel RAG: estado del índice (docs, chunks, tamaño, online/offline)
- Panel MCP Servers: documentación interactiva para configurar servidores MCP
- Panel Tools: inventario de 6 herramientas integradas (Code Runner, Git, Web Search, Grep, File Edit, Native Trigger)
- Endpoints: `GET /v1/hardware`, `GET /v1/cost`, `GET /v1/watchdog`, `GET /v1/sessions`, `GET /v1/rag/status`
- Endpoints: `POST /v1/agent/compare`, `POST /v1/watchdog/unlock`
- `gravity_tray.py`: icono de bandeja del sistema con pulso durante arranque
- `gravity_launcher.pyw`: launcher silencioso sin consola con single-instance guard
- `installer/gravity_setup.iss`: asistente Inno Setup 6 con autostart, desktop icon, uninstaller
- `installer/build_installer.bat`: build automatizado PyInstaller → exe → Inno Setup → Setup.exe
- Wiki completa: Arquitectura, Guia-API, Manual-Usuario, FAQ, Game-Server-Guide
- `engine_watchdog.start()` añadido a `run_server()` (fix: watchdog ahora arranca con el bridge)

### Fixed
- `exposeWan()`: reemplazado `prompt()` nativo del navegador por modal HTML con backdrop-filter
- `dashboard.py`: docstring actualizado de V9.4 PRO a V10.0
- `ide_integrator.py`: versión actualizada de V9.3.1 PRO a V10.0 en config y header
- `build_installer.bat`: pip más robusto con `--trusted-host` y output de error visible
- Gráfico de latencia: fill con gradiente, glow stroke, punto indicador y label de valor

### Dependencies
- Añadidos: `pystray`, `Pillow`, `pyinstaller`, `psutil`

---

# Registro de Cambios — Gravity AI Bridge

Todos los cambios notables en este proyecto serán documentados en este archivo. El formato se basa en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) y este proyecto adhiere a la versión técnica presente en el archivo `.toc` local.

## [10.0.0 Stable] — 2026-04-17 [Diamond-Tier Edition]

### 🚀 Añadido
- **Sistema de Toasts nativo:** Interfaz visual mejorada en el Dashboard para alertas no intrusivas.
- **Whitelist de Puertos WoW:** Soporte explícito en `security_monitor.py` para puertos 3724 (realmd), 8085 (worldserver) y 7878 (SOAP).
- **Módulo `ReasoningStripper`:** Extracción de lógica de limpieza de pensamientos de IA a un módulo compartido en `core/`.
- **Plantillas de Issues:** Estructuras estandarizadas para reportes de bugs y sugerencias de funciones.

### 🛠️ Corregido
- **Race Condition en Deploy:** Sincronización mediante `threading.Lock` al iniciar el pipeline de despliegue.
- **Audit Log Timestamps:** Corrección de zona horaria a UTC con sufijo 'Z' para compatibilidad universal.
- **SQLite Optimization:** Eliminación de conexiones duplicadas y bloqueos en `cache_engine.py`.
- **Rate Limiter Configuration:** Corregida clave de configuración de `security.rate_limit_ip` a `rate_limit.requests_per_minute`.
- **Credenciales MaNGOS:** Eliminación de usuarios/passwords hardcodeados en `game_server_manager.py`, ahora utiliza el motor de configuración.
- **Dashboard Hot-Reload:** Eliminado servidor HTTP secundario redundante; ahora el Dashboard se sirve y actualiza desde el núcleo principal.

### 🧹 Eliminado
- **Gradio Dependency:** Eliminada la dependencia de Gradio en `requirements.txt` (ahorro de ~500MB).
- **Redundancia de código:** Eliminadas copias locales de `ReasoningStripper` en `bridge_server.py` y `ask_deepseek.py`.

---

## [9.3.1 PRO] — 2026-04-13
- Versión base previa a la auditoría integral V10.0.
- Implementación inicial de la arquitectura SOC.
- Soporte para DPAPI en Windows.

---
*Anteriormente el proyecto se manejaba mediante versionado incremental rápido.*
