---
description: Auditoría de seguridad, bugs o deuda técnica de un archivo específico.
---
// audit-mode: strict
// zero-trust-security: enabled

1. **Source Injection**
   Leer el contenido íntegro del archivo especificado por el usuario. No omitir ninguna línea.

2. **Execute Direct Pipe Audit**
   Generar un prompt de auditoría en Inglés y enviarlo junto con el archivo al modelo local:
   ```bash
   cat "<FILE_PATH>" | python F:\Gravity_AI_bridge\ask_deepseek.py "Perform a deep technical audit of this file. Identify: 1. Logic bugs. 2. Memory leaks. 3. Security vulnerabilities. Present a structured report in English."
   ```

3. **Present Findings**
   Traducir los hallazgos críticos al Español. Ofrecer al usuario la opción de aplicar los parches sugeridos de forma automática.
