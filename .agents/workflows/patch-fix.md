---
description: Diagnóstico y reparación inmediata de logs de error o stack traces.
---
// diagnostic-mode: aggressive
// goal: definitive-patch

1. **Analyze Crash Log**
   Procesar el error reportado. Identificar el punto de falla en la arquitectura.

2. **Local AI Diagnosis**
   Enviar el log de error al modelo local para obtener una solución basada en el contexto del proyecto:
   ```bash
   python F:\Gravity_AI_bridge\ask_deepseek.py "Analyze this stack trace: <ERROR_LOG>. Provide the definitive code patch to fix it immediately. No explanations, just the patch."
   ```

3. **Execute Patch**
   Presentar el parche al usuario y, tras confirmación, aplicarlo directamente sobre el archivo afectado.
