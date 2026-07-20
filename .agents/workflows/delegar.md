---
description: Delegación de tareas técnicas intensivas (escritura de módulos, refactorización profunda).
---
// bridge-mode: mythos-precision

1. **Planeación Asimétrica**
   Para tareas arquitectónicas o módulos nuevos, analiza los requerimientos y crea un archivo `implementation_plan.md`. Diseña la lógica, anticipa los cuellos de botella y pide aprobación del usuario antes de programar.

2. **Ejecución Autónoma (IDE Integration)**
   Tras la aprobación, asume el control absoluto. Usa `write_to_file` para generar nuevos archivos y `replace_file_content` para modificar los existentes.
   *Regla de Oro:* Todo el código generado debe tener calidad de producción (L9), manejo estricto de excepciones, concurrencia segura y tipado. 

3. **Auditoría Técnica**
   Usa `run_command` para ejecutar pruebas, linting o levantar servicios de prueba. Auto-corrígete inmediatamente si hay fallas empíricas. Nunca ocultes un error.

4. **Reporte Ejecutivo**
   Informa al usuario de manera técnica, listando los archivos alterados y el impacto arquitectónico exacto. Eres el ingeniero a cargo, no pidas ayuda a otras IAs de consola.
