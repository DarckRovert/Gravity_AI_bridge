# 🏛️ GRAVITY AI BRIDGE — REGLA UNIVERSAL DE INTEGRACIÓN Y AHORRO DE TOKENS

## 🎯 Directiva Primaria: Delegación Asimétrica de Carga de Trabajo
Para proteger la cuota de tokens y optimizar la velocidad de respuesta, **NUNCA utilices modelos frontera de alto costo (Claude 3.5 Sonnet, Gemini 1.5 Pro, GPT-4o)** para tareas mecánicas, rutinarias o de procesamiento masivo de texto/código.

En su lugar, **DELEGA** estas subtareas a la infraestructura local/híbrida de **Gravity AI Bridge** (`tools/gravity_delegate.py`).

## ⚡ Tareas Obligatorias para Delegación
1. **Generación de Pruebas Unitarias:** Creación de suites completas en `pytest`, `unittest`, `jest`, `vitest`.
2. **Boilerplate y CRUD:** Modelos de datos, DTOs, esquemas Pydantic/Zod, adaptadores de base de datos.
3. **Refactorización Sintáctica y Tipado:** Agregar type hints, docstrings Sphinx/Google, linting manual, conversiones async.
4. **Transformación de Datos:** Conversión entre JSON, YAML, TOML, CSV, o extracción de datos con Regex complejas.
5. **Generación de Documentación y Resúmenes:** Resumir logs extensos, changelogs, actas de commit o diagramas mermaid.

## 🛠️ Ejecución:
```bash
python F:\Gravity_AI_bridge\tools\gravity_delegate.py "Escribe una suite completa de pytest con 5 casos borde para este módulo" --file ./src/mi_modulo.py
```
Fallback automático: LM Studio Local -> Groq (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`) -> Nvidia NIM.
