---
description: Sincronización de convenciones y reglas permanentes al _knowledge.json local.
---
// sync-mode: permanent
// target: _knowledge.json

1. **Rule Formulation**
   Convertir la convención definida por el usuario en una directiva técnica precisa en Inglés.

2. **Delegate Learning**
   Ejecutar el comando de aprendizaje en el modelo local de forma silenciosa:
   ```bash
   python F:\Gravity_AI_bridge\ask_deepseek.py "!aprende <TECHNICAL_RULE_IN_ENGLISH>"
   ```

3. **Verify Sync**
   Confirmar que el comando devolvió un estado de éxito. Informar al usuario en Español que el "Cerebro Local" ha sido actualizado y ahora comparte esa convención.
