# Changelog - Gravity AI Bridge

Todas las actualizaciones notables a este proyecto serán documentadas en este archivo.

## [8.5.0] - 2026-04-08
### Added
- Integración de arquitectura inspirada en **Claude Code (Claw)**.
- Nueva herramienta `grep_tool` basada en Ripgrep (con fallback Python).
- Nueva herramienta de edición quirúrgica `file_edit_v2` (bloques exactos).
- Módulo `VerificationAgent` para auditoría adversarial de cambios.
- Adaptador inicial para **Model Context Protocol (MCP)**.
- Modo Planificación mediante comando `/plan`.
- Personalidad minimalista y veraz de Anthropic en el prompt del sistema.

## [8.0.0] - 2026-04-07
### Añadido
- **FASE 2**: Sistema de logging estructurado JSON con sanitización de secretos.
- **FASE 2**: Auditoría inmutable en `_audit_log.jsonl` (Append-only).
- **FASE 3**: Nuevo `ConfigManager` con soporte nativo para `config.yaml`.
- **FASE 3**: Migración automática desde el antiguo `_settings.json` al nuevo formato.
- **FASE 4**: Módulo de Métricas integrado con Prometheus (`/metrics`).
- **FASE 4**: Rate Limiting por IP y API Key.
- **FASE 5**: Suite de pruebas unitarias (`pytest`) y pipeline de CI en GitHub Actions.
- **FASE 6**: Dashboard Web Premium rediseñado con Glassmorphism y animaciones CSS.

### Cambiado
- El servidor ahora escala mediante la reducción de latencia en la detección de modelos.
- Interfaz CLI (`ask_deepseek.py`) actualizada a V8.0 PRO.

### Corregido
- Reparado el error de sintaxis en `Console_Safe` de `bridge_server.py`.
- Solucionada la inconsistencia en los mensajes RAG del CLI (soporte bilingüe).

## [7.1.0] - 2026-04-06
- Integración NPU Ryzen AI (XDNA).
- Mejoras en el rendimiento de concurrencia.
