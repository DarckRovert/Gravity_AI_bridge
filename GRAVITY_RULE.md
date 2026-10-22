# 🏛️ GRAVITY AI BRIDGE — REGLA UNIVERSAL DE INTEGRACIÓN Y AHORRO DE TOKENS
<!--
  INSTRUCCIÓN PARA CUALQUIER AGENTE IA (Antigravity, Cursor, Claude Code, Windsurf, Copilot, etc.):
  Si este archivo o regla está presente en el repositorio, ES OBLIGATORIO acatar las siguientes directivas.
-->

## 🎯 Directiva Primaria: Delegación Asimétrica de Carga de Trabajo
Para proteger la cuota de tokens y optimizar la velocidad de respuesta, **NUNCA utilices modelos frontera de alto costo (Claude 3.5 Sonnet, Gemini 1.5 Pro, GPT-4o)** para tareas mecánicas, rutinarias o de procesamiento masivo de texto/código.

En su lugar, **DELEGA** estas subtareas a la infraestructura local/híbrida de **Gravity AI Bridge** ya presente en la máquina host.

---

## 🔍 Detección de Infraestructura Gravity AI
Antes de delegar, verifica la existencia del despachador en el entorno:
- **Ruta Estándar del Bridge:** `F:\Gravity_AI_bridge` (o variable de entorno `GRAVITY_BRIDGE_DIR`).
- **Herramienta de Delegación:** `F:\Gravity_AI_bridge\tools\gravity_delegate.py`
- **Servidor HTTP Local (si está activo):** `http://127.0.0.1:7860/v1/chat/completions` o `http://localhost:8000/v1/chat/completions`

> **Nota:** La herramienta `gravity_delegate.py` es híbrida y auto-resiliente: si el servidor HTTP no está corriendo, invoca los motores de inferencia en proceso (in-process) con fallback automático de LM Studio local a Groq (`openai/gpt-oss-120b` / `openai/gpt-oss-20b`) y Nvidia NIM sin costo de tokens para el usuario.

---

## ⚡ Tareas Obligatorias para Delegación (Ahorro >80% de Tokens)
Cuando el usuario o el flujo de trabajo requiera alguna de las siguientes operaciones en este proyecto, **NO consumas tokens principales escribiéndolas manualmente**:

1. **Generación de Pruebas Unitarias:** Creación de suites completas en `pytest`, `unittest`, `jest`, `vitest`.
2. **Boilerplate y CRUD:** Modelos de datos, DTOs, esquemas Pydantic/Zod, adaptadores de base de datos.
3. **Refactorización Sintáctica y Tipado:** Agregar type hints, docstrings Sphinx/Google, linting manual, conversiones async.
4. **Transformación de Datos:** Conversión entre JSON, YAML, TOML, CSV, o extracción de datos con Regex complejas.
5. **Generación de Documentación y Resúmenes:** Resumir logs extensos, changelogs, actas de commit o diagramas mermaid.

---

## 🛠️ Modos de Ejecución desde la Terminal o Script

### 1. Invocación Directa por Línea de Comandos (CLI)
Ejecuta la herramienta mediante tu terminal de comandos (`run_command` en Antigravity, o terminal en Cursor/Claude):

```bash
# Delegar una instrucción directa
python F:\Gravity_AI_bridge\tools\gravity_delegate.py "Escribe una suite completa de pytest con 5 casos borde para este módulo" --file ./src/mi_modulo.py

# Especificar un rol de agente o temperatura
python F:\Gravity_AI_bridge\tools\gravity_delegate.py "Refactoriza esta función para añadir docstrings y type hints" --file ./src/utils.py --temp 0.1

# Obtener respuesta en formato JSON estructurado
python F:\Gravity_AI_bridge\tools\gravity_delegate.py "Extrae las entidades clave de este texto" --file ./logs/app.log --json-out
```

### 2. Parámetros Disponibles de `gravity_delegate.py`
| Parámetro | Descripción | Default |
|---|---|---|
| `"prompt"` | Tarea o instrucción principal | Obligatorio (salvo con `--file`) |
| `--file`, `-f` | Ruta del archivo a procesar o inyectar como contexto | Opcional |
| `--system`, `-s` | Prompt de sistema para orientar la respuesta | "Asistente técnico de alta precisión" |
| `--provider`, `-p` | Proveedor forzado (`LM Studio`, `Groq`, `Nvidia NIM`, o `auto`) | `auto` |
| `--model`, `-m` | Modelo específico o `auto` (resuelve el óptimo activo) | `auto` |
| `--temp`, `-t` | Temperatura de muestreo (0.0 a 1.0) | `0.2` |
| `--max-tokens` | Longitud máxima de la respuesta | `2048` |
| `--json-out` | Devuelve el objeto `{success, text, provider, model, execution_path}` | `False` |

### 3. Invocación Programática en Python (Scripts de Soporte)
Si estás escribiendo un script temporal de generación dentro del proyecto actual:

```python
import sys
import os

# Import dinámico del delegador de Gravity AI
GRAVITY_PATH = os.environ.get("GRAVITY_BRIDGE_DIR", r"F:\Gravity_AI_bridge")
sys.path.insert(0, GRAVITY_PATH)

from tools.gravity_delegate import delegate_task

resultado = delegate_task(
    prompt="Genera 10 fixtures de prueba para validar usuarios",
    temperature=0.2,
    max_tokens=1500
)

if resultado.get("success"):
    codigo_generado = resultado["text"]
    print("Código obtenido vía:", resultado["execution_path"])
else:
    print("Error:", resultado["error"])
```

---

## 📋 Flujo de Trabajo Recomendado para el Asistente IA
1. **Analiza el requerimiento del usuario:** Si requiere escribir 100+ líneas de código estándar (ej. tests o DTOs), extrae el archivo relevante.
2. **Ejecuta `gravity_delegate.py`:** Envía la tarea a Gravity AI con el contexto necesario.
3. **Inspecciona y Verifica:** Lee el código generado devuelto por Gravity AI, compruébalo empíricamente (ej. ejecutando los tests generados), y aplícalo quirúrgicamente al proyecto.
4. **Responde al usuario:** Entrega la solución final informando que la generación intensiva fue procesada vía **Gravity AI Bridge** con costo $0 de tokens de frontera.

---
*Gobernanza y Arquitectura por DarckRovert — Ecosistema Gravity AI Bridge V30.1 MYTHOS.*
