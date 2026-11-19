# Arquitectura Profunda (L0, L1, L2, L3) — V30.4 MYTHOS

## Estructura de Capas

1. **L0: Cerebro y Coordinación (Gravity Bridge Server)**
   - Puerto `7860`.
   - Carga el servidor asíncrono (`bridge_server.py`) y el motor cognitivo (`gravity_brain.py`).
   - El Motor de Autonomía (`autonomy_engine.py`) opera aquí en un ciclo OODA de 6 horas, tomando decisiones sobre gasto, contenido y seguridad.
   - Orquestador de Subagentes Declarativos V30.3 (OpenCode 2.3) con Shared Contract Protocol.

2. **L1: Motor de Renderizado Estático (Fooocus Studio)**
   - Puertos `7861` y `7862`.
   - Controla la API para la generación asíncrona de miniaturas y recursos gráficos.

3. **L2: Motor de Renderizado Dinámico (ComfyUI / LTX)**
   - Puerto `8188`.
   - Utilizado para animaciones pesadas y pipelines de contenido de video en lote.

4. **L3: Motor de Animación Facial y Video-to-Video (LivePortrait / V2V Studio)**
   - Puerto `7863` (desacoplado de Fooocus para evitar colisiones).
   - Motor `V2VPipeline` ejecutado en hilos independientes para animación facial en tiempo real a partir de imágenes guía y videos de conducción.

## Strategic Memory & Knowledge Graph
Gravity V30.4 integra un motor de grafo de conocimiento bidireccional en memoria gestionado con **NetworkX**:
- Ingesta dinámica de decisiones (`strategic_decisions`) y patrones (`system_patterns`).
- Cálculo de métricas de centralidad PageRank en tiempo real para determinar los nodos neurálgicos (`system`, `success`, `autonomy`, etc.).
- Visualización interactiva en frontend mediante SVG reactivo radial en `MemoryStudio.tsx`.

## Reportero Autónomo
Un proceso demonio continuo (`news_daemon.py`) que:
1. Ejecuta `workflows/reporter.json` via `run_workflow("reporter")`.
2. Busca temáticas usando herramientas de WebSearch.
3. Inyecta respuestas LLM en `news.json` en un repositorio independiente (`gravity-news-portal`).
4. Realiza sincronizaciones automáticas a través de `git commit` y `git push` a Netlify. Cuenta con control de idempotencia para evitar fallos si no hay cambios nuevos, garantizando un ciclo de ejecución continuo.
