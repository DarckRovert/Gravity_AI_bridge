# Política de Seguridad y Blindaje

Este repositorio implementa salvaguardas avanzadas para el control de IA autónoma, conocidas como **AgentShield V16.6 Diamond-Tier**, desarrolladas tras auditorías profundas cruzadas con vulnerabilidades conocidas (incluyendo el framework ECC y reportes de Anthropic/Check Point).

## Versiones Soportadas
Actualmente solo se brinda soporte de seguridad a la rama principal (Gravity V16.6 PRO).

## Arquitectura de Seguridad
- **AgentShield Ring 0:** Previene RCE y Directory Traversal en el motor autónomo. El LLM tiene bloqueada la escritura y lectura en archivos de configuración (`.env`, `_settings.json`, `_knowledge.json`) y carpetas del núcleo (`core/`, `.agents/`).
- **Validación Estricta de Hooks:** (Mitigación CVE-2025-59536) Los scripts de eventos se validan criptográficamente desde una fuente segura fuera del proyecto (`%LOCALAPPDATA%\Gravity\hooks_trust.json`).
- **AST Python Sandbox:** Ejecución segura de scripts delegados (Periodista/Scrapers) anulando dependencias peligrosas (`socket`, `os`, `sys`, `subprocess`) a nivel léxico.
- **Sanitización Unicode Estricta:** Neutralización agresiva de inyecciones de Prompt (zero-width characters, Bidi overrides) antes de ingresar al contexto.
- **HITL Manager Ultraeficiente:** Hilos bloqueados a nivel OS para la intercepción de herramientas de red y terminal, previniendo abusos de autonomía.

## Reporte de Vulnerabilidades
Si encuentras una manera en la que el Motor de Autonomía de Gravity pueda eludir sus bloqueos (HITL, AgentShield, Sandbox o presupuesto), repórtalo directamente mediante un Issue privado o contactando al administrador. NO crees un Issue público si el problema expone claves de API en texto plano o permite RCE remoto sin autenticación.
