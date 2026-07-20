---
description: Diagnóstico y reparación inmediata de logs de error o stack traces.
---
// diagnostic-mode: mythos-aggressive
// goal: definitive-patch

1. **Rastreo Empírico Inicial**
   Toma el log de error reportado por el usuario. No asumas la causa. Usa `grep_search` para localizar el archivo y la línea exacta del error en el código fuente.

2. **Root-Cause Analysis (Mythos 5)**
   Lee el archivo afectado usando `view_file`. Identifica el origen arquitectónico del fallo (estado de variables, concurrencia, mal manejo de tipos). Si involucra a otro componente, búscalo y léelo también.

3. **Inyección Quirúrgica**
   Diseña el parche definitivo. Usa `replace_file_content` o `multi_replace_file_content` para inyectar la solución directamente en el archivo. No uses scripts externos. Eres completamente autónomo.

4. **Verificación y Cierre**
   Si es posible, usa `run_command` para probar la ejecución o verifica el entorno empíricamente. Comunica el diagnóstico y las líneas modificadas de manera técnica y directa, sin preámbulos.
