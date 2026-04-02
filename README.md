# Gravity AI Bridge 🌉🤖

Este proyecto es un conector ligero (bridge) diseñado para que tu asistente de IA principal (como Antigravity/Gemini) pueda consultar, auditar y delegar tareas de manera transparente a modelos locales respaldados por **Ollama** (específicamente `deepseek-r1:8b`).

## ¿Por qué existe este puente?
- **Auditoría Local:** Permite a la IA en la nube utilizar tu GPU local para generar los "borradores rápidos" de código o texto, delegando el peso cognitivo pesado y ahorrando costos/créditos.
- **Relevo Técnico (Fallback):** Funciona como la capa de abstracción para que cuando no tengas créditos en la nube, la interfaz de chat pueda continuar la conversación localmente sin perder contexto.

## Requisitos
- [Ollama](https://ollama.com/) instalado y corriendo en `localhost:11434`.
- El modelo `deepseek-r1:8b` nativo descargado en Ollama (`ollama run deepseek-r1:8b`).
- Python 3.x

## Uso del Script Auditor

El script principal `ask_deepseek.py` puede usarse directamente desde la consola o ser llamado por otras IAs.

```bash
python ask_deepseek.py "Pídele a la IA local que escriba una función de ordenamiento en Python"
```

## Configuración del Relevo (Fallback) en tu Interfaz
Si te quedas sin créditos, puedes configurar la mayoría de editores (Cursor, Roo, Cline, Antigravity) para hablar directo con este ecosistema:
1. Busca la opción **API Provider** o **Model Selection** en las opciones del chat.
2. Escoge **OpenAI Compatible** o **Local API**.
3. Base URL: `http://localhost:11434/v1`
4. API Key: `ollama` (o cualquiera)
5. Model ID: `deepseek-r1:8b`
