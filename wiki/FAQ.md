# FAQ — Gravity AI Bridge V8.5

**1. ¿Por qué el Bridge no me saluda ni se disculpa?**
A partir de la V8.5, el Bridge adopta la personalidad de Claude Code. Está diseñado para ser puramente técnico y directo para maximizar la productividad y reducir el ruido en la terminal.

**2. ¿Cómo funciona el modo planificación?**
Al usar `/plan`, el sistema prioriza la investigación del codebase (RAG + Grep) y propone un documento de diseño antes de escribir una sola línea de código. Esto imita el comportamiento de los ingenieros senior.

**3. ¿Qué es el VerificationAgent?**
Es una capa de seguridad que intercepta cada edición propuesta. Comprueba que el código compile/tenga sentido sintáctico y busca patrones de riesgo como inyecciones de comandos shell.

**4. ¿Puedo usar mis propios servidores MCP?**
Sí. El comando `/mcp <ruta_al_servidor>` permite conectar cualquier servidor que hable el protocolo Model Context Protocol vía stdio/JSON-RPC.

**5. ¿Qué pasa si Ripgrep no está instalado?**
El sistema detectará la ausencia de `rg` y activará automáticamente un `python_fallback` para realizar las búsquedas, aunque con un rendimiento menor en codebases masivos.
