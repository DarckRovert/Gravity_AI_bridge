# Arquitectura Profunda (L0, L1, L2)

## Estructura de Capas

1. **L0: Cerebro y Coordinación (Gravity Bridge Server)**
   - Puerto `7860`.
   - Carga el entorno de Gradio (`bridge_server.py`) y el motor cognitivo (`gravity_brain.py`).
   - El Motor de Autonomía (`autonomy_engine.py`) opera aquí en un ciclo OODA de 6 horas, tomando decisiones sobre gasto, contenido y seguridad.

2. **L1: Motor de Renderizado Estático (Fooocus Studio)**
   - Puertos `7861` y `7862`.
   - Controla la API para la generación asíncrona de miniaturas y recursos gráficos.

3. **L2: Motor de Renderizado Dinámico (ComfyUI / LTX)**
   - Puerto `8188`.
   - Utilizado para animaciones pesadas y pipelines de contenido de video en lote.

## Reportero Autónomo
Un proceso demonio continuo (`news_daemon.py`) que:
1. Ejecuta `workflows/reporter.json` via `run_workflow("reporter")`.
2. Busca temáticas usando herramientas de WebSearch.
3. Inyecta respuestas LLM en `news.json` en un repositorio independiente (`gravity-news-portal`).
4. Realiza sincronizaciones automáticas a través de `git commit` y `git push` a Netlify. Cuenta con control de idempotencia para evitar fallos si no hay cambios nuevos, garantizando un ciclo de ejecución continuo.

## Mecanismo de Estabilidad Estructural (Anti-Alucinaciones)

Para garantizar la estabilidad del portal frente a alucinaciones de modelos locales de menor tamaño (ej. caídas de formato JSON provocando "Transmisiones Clandestinas"), la arquitectura implementa dos capas de seguridad:
1. **Chain-of-Thought Forzado (`<thought>`):** Todos los manifiestos de redactores exigen que el LLM planifique sus deconstrucciones dentro de un bloque XML `<thought>` antes de escupir el JSON final. Esto purga la longitud de razonamiento e impide que rompa el string JSON.
2. **Parser Multinivel (`ContentNormalizerNode`):** El motor no falla si el LLM incluye texto extra. Implementa un parser con 4 capas de fallback:
   - `json.loads` estricto.
   - Extracción con Regex de bloques de código ` ```json `.
   - Extracción de llaves extremas `{...}` (ignorando el bloque `<thought>` superior).
   - Ensamblaje manual y reparación sintáctica del JSON si ocurre un truncamiento por límite de tokens.
