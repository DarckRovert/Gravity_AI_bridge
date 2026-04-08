# FAQ — Preguntas Frecuentes

## 🚀 Inicio y Configuración

### ¿Cómo sé si el bridge está funcionando?
```cmd
gravity --status
```
O visita `http://localhost:7860/health` desde el browser. Si ves `"status": "ok"`, el bridge está activo.

### No tengo ningún motor de IA local. ¿Puedo usar Gravity?
Sí. Configura una API Key de un proveedor cloud:
```
gravity
Gravity> /keys set openai
```
El bridge enrutará automáticamente a OpenAI, Anthropic, Groq u otros según disponibilidad.

### ¿Cómo instalo Ollama?
```cmd
winget install Ollama.Ollama
ollama pull deepseek-r1:14b    # Modelo recomendado 14B
ollama serve                    # Iniciar el servidor (si no está corriendo)
```

### El comando `gravity` no funciona desde otra terminal. ¿Por qué?
El instalador registra el PATH en la sesión actual. Cierra y vuelve a abrir la terminal para que el PATH actualizado surta efecto. Si persiste, ejecuta manualmente:
```cmd
INSTALAR.bat
```

---

## 💻 CLI y Comandos

### ¿Cómo cambio el modelo que usa el auditor?
```
Gravity> /model
```
Muestra un picker interactivo con todos los modelos disponibles en los backends online.

### ¿Qué diferencia hay entre `/model` y `/mode`?
- `/model`: Cambia el **motor y modelo de IA** activo (Ollama, OpenAI, etc.).
- `/mode`: Cambia el **perfil de comportamiento** (production, development, Omni-Audit).

### ¿Cómo evito que el CLI cierre con Ctrl+C?
`Ctrl+C` dentro del CLI no cierra la sesión — muestra un hint. Usa `/exit` para cerrar correctamente (purga los bloques de razonamiento antes de salir).

### ¿Cómo persisto una regla permanente?
```
Gravity> !aprende Siempre usa type hints explícitos en Python. Prohibido 'Any'.
✓ Regla persistida en _knowledge.json (5 total)
```
La regla se añade al system prompt en cada sesión futura.

---

## 🌐 Bridge Server y Dashboard

### ¿Qué hace exactamente el bridge server?
Actúa como proxy compatible con OpenAI. Cualquier IDE o aplicación que soporte OpenAI API puede conectarse a `http://localhost:7860/v1` y el bridge decide automáticamente qué motor local o cloud usar.

### ¿Por qué mi IDE no conecta con el bridge?
1. Verifica que el bridge esté corriendo: `http://localhost:7860/health`.
2. La Base URL debe ser `http://localhost:7860/v1` (con `/v1` al final).
3. El API Key puede ser cualquier valor (`gravity-local` es el recomendado).
4. Verifica que el modelo sea `gravity-bridge-auto` o un modelo disponible de `/v1/models`.

### ¿Cómo inicio el bridge sin ventana visible?
Doble clic en `MODO_FANTASMA.vbs`. El bridge corre en segundo plano y los logs van a `bridge.log`.

---

## 🔑 Seguridad y API Keys

### ¿Dónde se almacenan las API Keys?
En Windows se cifran con **DPAPI** (criptografía nativa del sistema, vinculada a tu sesión de usuario). Nadie puede descifrarlas sin acceso a tu sesión de Windows.

### ¿Puedo ver mis API Keys almacenadas?
Solo en formato enmascarado:
```
Gravity> /keys list
┌─────────┬───────────────┐
│openai   │ sk-pr...xyz   │
└─────────┴───────────────┘
```

### ¿Es seguro exponer el bridge en mi red local?
Con la configuración por defecto (escucha en `0.0.0.0`), otros dispositivos de tu red pueden conectarse. Si no deseas esto, cambia en `config.yaml`:
```yaml
server:
  host: 127.0.0.1
```

---

## 🔬 RAG y Documentos

### ¿Qué tipo de archivos puedo indexar?
Por defecto: `.py`, `.js`, `.ts`, `.md`, `.txt`, `.json`, `.yaml`.  
Con `pypdf` instalado: también `.pdf`.

### ¿Cuánto tarda la indexación?
Depende del hardware y el tamaño. Una carpeta de 200 archivos `.py` tarda ~30 segundos en CPU. Con GPU es significativamente más rápido.

### ¿El RAG actualiza automáticamente cuando modifico archivos?
No, actualmente es manual. Vuelve a ejecutar `/index <ruta>` para reindexar.

---

## ⚡ Rendimiento

### ¿Por qué a veces la respuesta es instantánea?
El **Cache Engine** (SQLite WAL) devuelve respuestas idénticas en <5ms. El hash tiene en cuenta el contenido de todos los mensajes del historial y el modelo activo. Los bloques `<think>` se excluyen del hash para mayor precisión.

### El modelo tarda mucho. ¿Qué puedo hacer?
1. Usa un modelo más pequeño: `/model` → selecciona un 7B en lugar de 32B.
2. Reduce el contexto: `/clear` para limpiar el historial.
3. Activa el modo `production` en lugar de `Omni-Audit`: `/mode`.
4. Revisa el `optimal_ctx` en `health_check.py` para tu hardware.

---

## 🐛 Errores Comunes

### `ERROR: Sin proveedor disponible`
- Verifica que Ollama esté corriendo: `ollama serve`.
- O configura una API Key cloud: `/keys set openai`.

### `ModuleNotFoundError: No module named 'rich'`
```cmd
pip install rich pyfiglet
```
O ejecuta `INSTALAR.bat` que lo hace automáticamente.

### `ConnectionRefusedError` al conectar el IDE
El bridge server no está corriendo. Ejecuta `INICIAR_SERVIDOR.bat` o `gravity --server`.

### El historial creció demasiado y el modelo es lento
El Sliding Window recorta automáticamente al superar 128k tokens. Si quieres un reset manual:
```
Gravity> /clear
```

---

*Gravity AI Bridge — [github.com/DarckRovert/Gravity_AI_bridge](https://github.com/DarckRovert/Gravity_AI_bridge)*
