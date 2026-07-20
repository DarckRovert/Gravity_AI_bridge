---
description: Auditoría de seguridad, bugs o deuda técnica de un archivo específico.
---
// audit-mode: zero-trust-security

1. **Inmersión Profunda**
   Usa `view_file` para extraer y leer el contenido íntegro del archivo indicado por el usuario. 

2. **Auditoría Mythos 5**
   Analiza el archivo de forma nativa con tu propio razonamiento de Ingeniero Principal buscando: 
   - Fugas de memoria (Memory Leaks) o bloqueos mutuos (Deadlocks / Race conditions).
   - Deuda técnica y falta de robustez en el manejo de excepciones.
   - Vulnerabilidades lógicas o de inyección.

3. **Despliegue de Soluciones**
   No uses scripts puente de consola. Genera tú mismo los parches.
   Presenta los hallazgos críticos de forma quirúrgica al usuario. Si el usuario acepta, usa tus herramientas de edición de archivos (`replace_file_content`) para refactorizar el código de inmediato.
