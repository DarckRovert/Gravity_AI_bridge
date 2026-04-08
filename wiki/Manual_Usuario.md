# Manual de Usuario — Gravity AI Bridge V8.5

## Instalación y Arranque

1. Asegúrate de tener Python 3.10+ instalado.
2. Ejecuta `INSTALAR.bat` para configurar las dependencias.
3. Inicia el puente con `INICIAR_AUDITOR.bat` para entrar en la CLI.

## Interacción con el Auditor

### Flujo de Trabajo Recomendado
1. **Consulta**: Haz una pregunta técnica directa.
2. **Planificación**: Usa `/plan <tarea>` para que el sistema proponga cambios detallados.
3. **Ejecución**: El sistema propondrá ediciones quirúrgicas (`file_edit`). Aprueba si el Verificador no reporta riesgos críticos.

## Comandos Útiles en la CLI

- `/model`: Abre un selector interactivo de modelos.
- `/clear`: Reinicia la sesión si el contexto se vuelve pesado.
- `/index <ruta>`: Añade código local al índice RAG para que la IA lo conozca.
- `/mcp <server>`: Carga herramientas externas si usas servidores compatibles con MCP.

## Personalidad de la IA
La IA actuará de forma fría, técnica y sin rodeos. No esperes agradecimientos ni disculpas; está optimizada para la eficiencia pura.
