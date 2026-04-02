---
description: Delegar una tarea técnica al Auditor Senior (DeepSeek local)
---

Este flujo de trabajo permite a **Antigravity** (o cualquier IA compatible) procesar peticiones complejas consumiendo el mínimo de tokens en la nube.

// turbo
1. **Verificar Estado del Sistema**
   Ejecuta: `python health_check.py`
   - Si falla, informa al usuario sobre la falta de conexión con Ollama.
   - Si es exitoso, continúa al paso 2.

2. **Formular la Petición al Auditor Local**
   Usa el comando `run_command` enviando la consulta directa. El Auditor detectará que es una llamada de Agente (con argumentos) y **responderá en Inglés técnico** para mayor fidelidad lógica.
   ```bash
   python ask_deepseek.py "[Petición detallada del usuario]"
   ```

3. **Recibir y Refinar la Respuesta**
   - Captura el `output` del comando anterior.
   - Analiza la respuesta técnica en inglés (gratuita).
   - Traduce y presenta el resultado final al usuario en español, añadiendo cualquier refinamiento adicional necesario en la capa de la nube.

4. **Confirmar Persistencia (Opcional)**
   Si el usuario indica que la respuesta es una "regla" que debemos recordar siempre, ejecuta:
   ```bash
   python ask_deepseek.py "!aprende [Regla]"
   ```
