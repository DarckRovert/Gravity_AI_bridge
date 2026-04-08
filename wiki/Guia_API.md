# Guía de API y Comandos V8.5

## Comandos de la CLI

- `/plan <tarea>`: Inicia un flujo de planificación profundo antes de realizar cambios.
- `/grep <patrón>`: Realiza una búsqueda rápida de texto usando Ripgrep o Fallback Python.
- `/rag <query>`: Busca contexto relevante en los documentos indexados.
- `/mcp <servidor>`: Conecta con un servidor MCP (Model Context Protocol).
- `/clear`: Limpia el contexto actual para iniciar una tarea desde cero.

## Herramientas para el Modelo (Tool Syntax)

El modelo puede invocar herramientas automáticamente usando la sintaxis:
`{{ tool: nombre | arg: valor }}`

### Herramientas Disponibles:
1. **`grep_search`**: Búsqueda de patrones avanzada.
   - Args: `pattern`, `path`, `glob`, `case_insensitive`.
2. **`file_edit`**: Edición quirúrgica de archivos.
   - Args: `target_file`, `old_string`, `new_string`.
3. **`web_search`**: Búsqueda en internet en vivo.
4. **`git_tool`**: Operaciones de control de versiones.
