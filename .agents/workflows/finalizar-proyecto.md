---
description: Auditoría total, Generación de Documentación, Wiki y Despliegue en DarckRovert.
---
// workflow-id: ultra-professional-release
// git-user: DarckRovert

1. **Generación de Suite Legal y Organizativa (Local AI)**
   Delegar al bridge la creación de la base del repositorio:
   - README.md (Nivel empresarial con badges).
   - LICENSE (MIT con año actual).
   - CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md.
   - .gitignore y .github/ISSUE_TEMPLATE/.

2. **Generación de Wiki Técnica (Local AI)**
   Solicitar al modelo local la creación de una carpeta `/wiki` con archivos .md detallados:
   - Home.md (Índice).
   - Architecture-Deep-Dive.md (Diagramas y lógica).
   - API-Reference.md (Si aplica).
   - Troubleshooting-and-FAQ.md.
   
   Comando:
   ```bash
   cat "F:\Gravity_AI_bridge\project_analysis.txt" | python F:\Gravity_AI_bridge\ask_deepseek.py "Genera una Wiki técnica profesional completa en Español. Estructura el contenido en archivos .md dentro de /wiki. Sé extremadamente detallado."
   ```

3. **Auditoría y Verificación de Rutas**
   Confirmar que todos los archivos (Suite + Wiki) existen en la raíz y en /wiki. Validar que los enlaces internos funcionen.

4. **Despliegue Git**
   Ejecutar secuencia de comandos:
   ```bash
   git add .
   git commit -m "Official Release: Full Documentation Suite and Technical Wiki included"
   git push origin main
   ```

5. **Reporte Final**
   Entregar al usuario en Español el resumen del despliegue y el enlace al repositorio: https://github.com/DarckRovert/Gravity_AI_bridge
