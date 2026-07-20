---
description: Auditoría total, Generación de Documentación, Wiki y Despliegue en DarckRovert.
---
// workflow-id: ultra-professional-release
// mode: mythos-deployment

1. **Suite Legal y Organizativa**
   Usa tus propias herramientas de análisis (`list_dir`, `view_file`) para escanear la raíz del repositorio.
   Si no existen, usa `write_to_file` para crear archivos de nivel empresarial directamente:
   - `README.md` (Completo, con arquitectura técnica y Mermaid charts).
   - `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`.

2. **Generación Nativa de Wiki Técnica**
   Usa `write_to_file` para diseñar y escribir archivos `.md` profundos dentro del directorio `/wiki` del proyecto:
   - `Home.md` (Índice y visión general).
   - `Architecture-Deep-Dive.md`.
   - `Troubleshooting-and-FAQ.md`.

3. **Auditoría de Enlaces**
   Verifica que todos los archivos creados tengan coherencia cruzada y enlaces relativos funcionales.

4. **Despliegue Maestro Git**
   Usa `run_command` en PowerShell para ejecutar el script de despliegue oficial.
   ```bash
   F:\Gravity_AI_bridge\launchers\Deploy_GravityBridge.bat
   ```
   Si el script no está disponible, realiza el despliegue manual usando comandos git nativos en la terminal.

5. **Cierre Profesional**
   Entrega un reporte de despliegue definitivo en Español.