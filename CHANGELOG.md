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
