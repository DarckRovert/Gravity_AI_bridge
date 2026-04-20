# 🪐 Gravity AI Bridge | Control Maestro & Ecosistema de Automatización V10.2

Bienvenido a la Central de Conocimiento del Bridge, tu hub principal para orquestar infraestructuras pesadas con herramientas LLMs subyacentes sin fricciones externas.

## Catálogo de Módulos Operativos
A continuación verás el índice para navegar los pilares funcionales que conforman el proyecto:

1. [⚙️ Arquitectura Deep Dive](./Arquitectura.md)
   Estudia el asincronismo y el anclaje físico de todos los módulos: Multi-Agente (Orquestador Vote/Compare), Gestor Difusor de Fooocus, Optimizador dinámico de VRAM, Tracker Financiero y Manejador Pasivo en vivo de MangosD (WoW).
2. [🔌 Referencia Oficial de API](./API-Reference.md)
   Domina la capa de abstracción. Todos los métodos HTTP (Deploy Pipeline Reactivo, Server Endpoints, Live Deque Logs, RAG System Memory y Seguridad).
3. [🛡️ Matrices y Estándares de Seguridad](../SECURITY.md)
   Nuestras leyes de Rate Limiting y barreras de control de VRAM. Indispensable lectura.
4. [📖 Guía Completa de API](./Guia-API.md)
   Referencia detallada de todos los endpoints con ejemplos `curl` y JSON.
5. [📑 Manual de Usuario](./Manual-Usuario.md)
   Instructivo base e interactivo apuntando al Dashboard.
6. [❓ FAQ](./FAQ.md)
   Preguntas frecuentes, solución de problemas y guía de Video Studio.

## Novedades V10.2
- **🎬 Video Studio**: Generación automática de videos documentales sin GPU dedicada. Pipeline: LLM → Fooocus (CPU) → SAPI TTS → ffmpeg.
- **RAG en Chat**: Contexto vectorial inyectado automáticamente en cada petición cuando `rag_enabled: true`.
- **Admin API**: Nuevos endpoints `POST /v1/audit/rotate` y `POST /v1/rag/toggle`.
- **62 tests pasados** con cobertura completa de todos los módulos core.

## Visión e Infraestructura (Tier-Diamond)
Somos un eslabón directo hacia entornos cerrados y eficientes. Rechazamos los intermediarios lentos. Este sistema te otorgará latencia casi nula al comunicarse con clústeres propios de inferencia y despliegue local automatizado. Redactado, administrado y protegido bajo la óptica de **[DarckRovert Ecosystem](https://github.com/DarckRovert)**.
