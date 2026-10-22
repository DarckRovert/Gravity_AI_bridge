---
name: gravity_delegator
description: Delegación de subtareas técnicas, rutinarias o de procesamiento de texto a los motores de inferencia locales y cloud de Gravity AI (Groq, Nvidia NIM, LM Studio, Ollama) para ahorro masivo de tokens.
---

# Gravity Delegator — Guía de Delegación Agéntica

Este skill permite al asistente delegar tareas específicas a los modelos locales y cloud configurados dentro de Gravity AI Bridge, ahorrando tokens en modelos de alto nivel (Claude / Gemini).

## Cuándo delegar
Usa la delegación para tareas de procesamiento, extracción y generación rutinaria:
- Generación de expresiones regulares (Regex).
- Normalización, transformación o validación de JSON/YAML.
- Generación de código boilerplate o estructuras repetitivas.
- Resúmenes técnicos de logs, excepciones o textos extensos.
- Redacción de pruebas unitarias básicas (mocks, fixtures).
- Traducciones técnicas rápidas.

## Cómo ejecutar la delegación
Ejecuta el script CLI `tools/gravity_delegate.py` mediante la herramienta `run_command`:

```bash
# Inferencia rápida (auto-ruteada o fallback)
python tools/gravity_delegate.py "Escribe una regex para validar slugs en formato kebab-case"

# Inferencia explícita en Groq (ultrarrápida y sin costo de tokens principales)
python tools/gravity_delegate.py "Genera 5 casos de prueba unitarios en pytest para validar emails" --provider "Groq" --model "openai/gpt-oss-20b"

# Inferencia en modelo de alta capacidad (120B)
python tools/gravity_delegate.py "Resume este log de error y extrae la causa raíz" --file "path/to/log.txt" --provider "Groq" --model "openai/gpt-oss-120b"

# Salida estructurada JSON (para parsing programático)
python tools/gravity_delegate.py "Extrae las entidades de este texto" --json-out
```

## Proveedores y Modelos Disponibles Auditados (2026)
- **Groq:**
  - `openai/gpt-oss-20b` (Ultrarrápido, ideal para tareas pequeñas, regex, validación).
  - `openai/gpt-oss-120b` (Gran capacidad de razonamiento y código).
- **Nvidia NIM:**
  - `meta/llama-3.2-11b-vision-instruct` (Visión, multimodal y texto).
  - `meta/llama-3.2-90b-vision-instruct` (Flagship open-weights).
  - `google/diffusiongemma-26b-a4b-it` (Inferencia especializada).
  - `nvidia/nemotron-3-ultra-550b-a55b` (Modelo colosal).
- **LM Studio / Ollama (Local):**
  - Conexión directa a `http://localhost:1234` o `http://localhost:11434` cuando estén abiertos.
  - Con fallback automático a Groq si el motor local está inactivo.
