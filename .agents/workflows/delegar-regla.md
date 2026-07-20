---
description: Sincronización de convenciones y reglas permanentes a tu sistema base.
---
// sync-mode: permanent
// target: GEMINI.md

1. **Rule Formulation**
   Analiza la nueva convención o regla que el usuario quiere imponer. Tradúcela a una directiva técnica, concisa y procesable que un LLM (como tú) pueda seguir estrictamente sin ambigüedades.

2. **Delegate Learning (Native Injection)**
   No uses scripts de consola de terceros. Usa `view_file` para leer el archivo de reglas globales del usuario en `c:\Users\darck\.gemini\GEMINI.md`.
   Usa `replace_file_content` para inyectar la nueva regla al final del archivo, manteniendo la numeración correlativa. Si la regla es específica del proyecto Gravity AI, inyéctala en `F:\Gravity_AI_bridge\.agents\workflows\` como un nuevo workflow en su lugar.

3. **Verify Sync**
   Lee `GEMINI.md` nuevamente con `view_file` para confirmar que la regla quedó escrita exactamente como se especificó. Comunica al usuario en Español que la regla ha sido interiorizada a nivel de sistema base.
