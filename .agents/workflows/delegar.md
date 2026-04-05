---
description: Delegación de tareas técnicas intensivas (escritura de módulos, refactorización profunda).
---
// turbo-all
// bridge-mode: high-precision
// language-target: English (Local) / Spanish (User)

1. **Verify Ecosystem**
   Ejecutar validación de recursos locales para asegurar disponibilidad de VRAM:
   ```bash
   python F:\Gravity_AI_bridge\ask_deepseek.py "!info"
   ```

2. **Translate & Pipe (AI-to-AI)**
   Traducir el requerimiento del usuario a Inglés Técnico. Generar el prompt y enviarlo mediante pipe para evitar truncamiento:
   ```bash
   cat "F:\Gravity_AI_bridge\temp_task.txt" | python F:\Gravity_AI_bridge\ask_deepseek.py "Execute the following technical task. Provide full code blocks only. No placeholders. [PROMPT_IN_ENGLISH]"
   ```

3. **Incorporate & Report**
   Analizar la salida del modelo local. Si el código es válido, presentarlo al usuario en Español con una breve explicación técnica de los cambios realizados.
