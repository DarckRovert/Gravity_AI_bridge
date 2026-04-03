# ⚔️ Arsenal de Comandos (Gravity AI V4.0)

Gravity no es un simple chat. Es una terminal interactiva. Abajo se documentan todos los comandos nativos del ecosistema.

## 🕹️ Comandos de Inyección de Contexto

Permiten pasar información instantánea al "Cerebro" de la IA.

| Comando | Sintaxis | Explicación |
| :--- | :--- | :--- |
| **Leer Archivo** | `/leer archivo.py` | Lee cualquier fichero local y lo mete al prompt. Intenta decodificar UTF-8, Latin y UTF-16 automáticamente. |
| **Leer Carpeta** | `/leer-carpeta src/` | Agrupa TODOS los archivos (.py, .ts, .md, etc) ignorando node_modules y .git, y los inyecta en un solo string gigante para auditorías de macro-arquitectura. |
| **Leer Git** | `/leer-git` | Ejecuta un `git diff` internamente y envía todos tus cambios sin comitear para revisión. |
| **Leer URL** | `/leer-url https://...` | Hace un fetch raw del HTML/Texto plano de una web y lo usa de contexto. |

## ⚙️ Control de Proveedores y Motor

| Comando | Sintaxis | Explicación |
| :--- | :--- | :--- |
| **Escanear Red** | `!scan` | Actualiza la lista de proveedores (busca activamente puertos de Ollama, LM Studio, etc). |
| **Dashboard** | `!info` | Muestra el panel maestro con el proveedor actual, modelo cargado y telemetría de contexto restante. |
| **Ver Modelos** | `!modelos` | Muestra la tabla de todos los motores que tu GPU/CPU tienen instalados. |
| **Cambiar Modelo**| `!usar qwen:8b` | Cambia el modelo activo instantáneamente. (Debe coincidir con la lista de `!modelos`). |
| **Forzar Motor** | `!proveedor id` | Si no quieres la auto-selección, fuerza el motor: `ollama`, `lm_studio`, `lemonade`. |

## 🧠 Memoria y Contexto

| Comando | Sintaxis | Explicación |
| :--- | :--- | :--- |
| **Snapshot** | `!guardar refactor1`| Guarda toda la sesión de chat a `_saves/refactor1.json`. |
| **Listar Saves** | `!saves` | Lista tus juegos guardados de contexto. |
| **Cargar Save** | `!cargar refactor1`| Sobreescribe la sesión actual con un snapshot de memoria. |
| **Limpiar** | `!limpiar` | Purga todo el chat efímero actual liberando RAM/VRAM. |
| **Compresor** | `!comprimir` | Si te acercas al límite de tokens (128K), resume la charla en bullets densos por detrás de escena y reemplaza el historial largo. |
| **Reglas Duras** | `!aprende regla` | Inserta permanentemente algo en el System Prompt (ej: `!aprende Siempre usa Typescript con interfaces`). |
| **Reset Reglas** | `!limpiar-reglas`| Borra todas las directrices permanentes. |

## 🎭 Modos de Comportamiento (Perfiles)

| Comando | Sintaxis | Explicación |
| :--- | :--- | :--- |
| **Modo Auditor** | `!modo auditor` | (Default) Experto cuidadoso, extenso, explica en español detalladamente. |
| **Modo Coder** | `!modo coder` | Vomita código. 0 charlas de relleno. 100% bloques lógicos para copy-paste. |
| **Modo Revisor** | `!modo revisor` | Rol destructivo. Busca race-conditions, memory leaks y puertas lógicas rotas. |
| **Modo Creativo** | `!modo creativo` | Deja de lado la rigidez, ideal para arquitecturas y UX brainstorming. |

## 🔌 Ecosistema / Otros

| Comando | Sintaxis | Explicación |
| :--- | :--- | :--- |
| **Integrador** | `!integrar todo` | Crea los scripts `config.yaml` de tus IDEs para empalmarlos con el Bridge Server de la GPU. |
| **Ajustes Avan** | `!ajustes` | Te deja ver tus parámetros matemáticos (Temperature, Top P). |
| **Pipeline CLI** | `cat code | gravity`| Envía tu prompt a través del Pipe nativo de Windows o Bash (sin entrar a la interfaz). |
