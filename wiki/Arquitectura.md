# Arquitectura de Gravity AI Bridge V8.5

Gravity AI Bridge es un orquestador híbrido diseñado para unir modelos LLM (locales y cloud) con el entorno de desarrollo local mediante una arquitectura de "Agente Auditor".

## Componentes Principales

1. **CLI Frontend (`ask_deepseek.py`)**: Interfaz de línea de comandos enriquecida que gestiona la sesión, el historial y la ruteo dinámico de modelos.
2. **System Prompt (Claw Persona)**: Implementa los principios de minimalismo y veracidad extraídos de Claude Code.
3. **Tool Executor (`tool_executor.py`)**: Motor que parsea y ejecuta comandos automáticos detectados en la respuesta del modelo.
4. **Verification Agent (`core/verification_agent.py`)**: Capa de seguridad adversarial que audita cambios antes de su aplicación.
5. **RAG Engine (`rag/`)**: Sistema de recuperación aumentada por generación para inyectar contexto de archivos locales.
6. **MCP Adapter (`core/mcp_adapter.py`)**: Interfaz para el Model Context Protocol, permitiendo la extensión mediante servidores externos.

## Flujo de Trabajo (Planification Mode)

Cuando se usa `/plan`, el sistema entra en una fase de reflexión previa:
1. **Investigación**: Búsqueda RAG y Grep del contexto relevante.
2. **Síntesis**: Generación de un plan de implementación.
3. **Ejecución**: Aplicación quirúrgica de cambios mediante `file_edit`.
4. **Verificación**: Auditoría del `VerificationAgent`.
