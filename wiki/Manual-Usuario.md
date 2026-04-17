# 📖 Manual de Usuario — Gravity AI Bridge V10.0

Este manual exhaustivo cubre la instalación, operación y optimización de Gravity AI Bridge para administradores y desarrolladores.

## 🧭 Índice
1. [Instalación](#instalación)
2. [Launchers y Arranque](#launchers-y-arranque)
3. [Dashboard Web](#dashboard-web)
4. [Uso del CLI](#uso-del-cli)
5. [Generación de Imágenes (Vision)](#generación-de-imágenes-vision)
6. [Sistema RAG](#sistema-rag)
7. [Integración con IDEs](#integración-con-ides)
8. [Atajos y Tips](#atajos-y-tips)

---

## 🛠️ Instalación

### Requisitos previos
- **Python 3.9+** instalado en el PATH.
- **Motor de IA Local:** Se recomienda [LM Studio](https://lmstudio.ai) u [Ollama](https://ollama.ai).
- **GPU AMD (Opcional para Vision):** Requiere instalar `AMD-Software-PRO-Edition-26.Q1-Win11-For-HIP.exe` y **reiniciar Windows**.

### Instalación de Dependencias
```cmd
launchers\INSTALAR.bat
```
El instalador configura el entorno virtual automáticamente y registra el comando `gravity`.

---

## 🚀 Launchers y Arranque

Todos los ejecutables se encuentran en `launchers/`. **Usa `INICIAR_TODO.bat` para el flujo normal diario.**

| Archivo | Función | Puerto |
| :--- | :--- | :--- |
| `INICIAR_TODO.bat` ⭐ | Arranca Bridge Server + Fooocus Studio | 7860 + 7861 |
| `INICIAR_SERVIDOR.bat` | Solo Bridge Server (Chat/Audit/Game) | 7860 |
| `GRAVITY_VISION_PRO.bat` | Solo Vision Studio (Generación Imágenes) | 7861 |
| `INICIAR_AUDITOR.bat` | Inicia el CLI en modo interactivo | — |

---

## 💬 Uso del CLI

### Modos de Ejecución
- **Interactivo:** Escribe `gravity` en tu terminal para entrar al prompt de comandos.
- **Modo Pipe:** `cat error.log | gravity "analiza este log"` para procesar archivos directamente.

### Comandos Esenciales
- `/help`: Lista todos los comandos disponibles.
- `/model`: Abre el menú interactivo para cambiar de motor o modelo.
- `/mode`: Cambia entre `production`, `development` y `Omni-Audit`.
- `/search <query>`: Realiza una búsqueda web rápida mediante Brave Search e inyecta el contexto.
- `/verify <path>`: Audita un archivo en busca de errores de sintaxis o riesgos de seguridad.

---

## 🎨 Generación de Imágenes (Vision)

Para usar la GPU AMD, asegúrate de tener configurado el **HIP SDK**. 
1. Abre el Dashboard en la pestaña **Vision Studio**.
2. **Primera Ejecución:** El sistema compilará los kernels mediante ZLUDA. **Espera 3-5 minutos** hasta que aparezca la primera imagen.
3. **Parámetros:** Puedes ajustar `Performance` (Quality/Speed/Lightning), `Aspect Ratio` y `Styles` directamente desde la interfaz.

---

## 📂 Sistema RAG

Gravity permite indexar tus propios archivos para responder con contexto local.
- **Indexar:** `Gravity> /index F:\mi_proyecto\src`
- **Consultar:** `Gravity> /rag busca la función de login`
- **Inyección Automática:** El sistema detectará términos como "en mi código" o "según mis archivos" y buscará automáticamente en el índice RAG antes de responder.

---

## 💻 Integración con IDEs

### Cursor
En `Settings → AI → OpenAI API`:
- **Base URL:** `http://localhost:7860/v1`
- **API Key:** `gravity-local`
- **Model:** `gravity-bridge-auto`

### VS Code (Continue)
```json
{
  "title": "Gravity AI",
  "provider": "openai",
  "model": "gravity-bridge-auto",
  "apiBase": "http://localhost:7860/v1"
}
```

---

## 💡 Atajos y Tips

| Tip | Función |
| :--- | :--- |
| `!aprende <regla>` | Persiste una instrucción en el `_knowledge.json` permanente. |
| `CTRL+C` | Cancela la generación actual en el CLI sin cerrarlo. |
| `/save <id>` | Guarda la sesión actual para retomarla más tarde con `/load <id>`. |
| `/mcp <path>` | Conecta con un servidor subyacente de Model Context Protocol. |

---
*Manual de Usuario Exhaustivo V10.0.*
