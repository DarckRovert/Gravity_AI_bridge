# FAQ — Preguntas Frecuentes — Gravity AI Bridge V9.1 PRO

## 🚀 Inicio y Configuración

### ¿Cómo arranco todo el sistema?
Abre el archivo:
```
launchers\INICIAR_TODO.bat
```
Arranca automáticamente el Bridge Server (7860), Fooocus Motor API (7861) y Vision Studio UI (7862).

### ¿Tengo que abrir varios launchers?
No. `INICIAR_TODO.bat` lo hace todo. Solo usa launchers individuales si quieres arrancar componentes específicos por separado.

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
El bridge enrutará automáticamente a OpenAI, Anthropic, Groq u otros según disponibilidad. Tu sistema actualmente usa **LM Studio** como motor local.

### El comando `gravity` no funciona desde otra terminal. ¿Por qué?
El instalador registra el PATH en la sesión actual. Cierra y vuelve a abrir la terminal. Si persiste:
```cmd
launchers\INSTALAR.bat
```

---

## 🎨 Generación de Imágenes

### La imagen no aparece después de pulsar Generate
Tres causas posibles:
1. **Fooocus no está corriendo** — Abre `launchers\GRAVITY_VISION_PRO.bat` o `INICIAR_TODO.bat`
2. **Descarga del modelo Base** — La primera imagen puede tardar 3-5 minutos. No presiones Generate de nuevo.
3. **amdhip64.dll no encontrado** — Necesitas instalar el AMD HIP SDK (ver abajo)

### Error: `amdhip64.dll no encontrado`
Instala el driver HIP de AMD:
1. Descarga `AMD-Software-PRO-Edition-26.Q1-Win11-For-HIP.exe` de [amd.com/en/support](https://www.amd.com/en/support)
2. Instala como Administrador
3. **Reinicia Windows** (obligatorio)
4. Vuelve a ejecutar `launchers\GRAVITY_VISION_PRO.bat`

### Error: `OSError: Cannot find empty port in range: 7861-7861`
El puerto 7861 está ocupado por un proceso anterior. El nuevo `GRAVITY_VISION_PRO.bat` lo libera automáticamente al arrancar. Si el error persiste, ejecuta en CMD:
```cmd
for /f "tokens=5" %p in ('netstat -ano ^| findstr :7861 ^| findstr LISTENING') do taskkill /F /PID %p
```

### ¿Cuánto tiempo tarda en generar una imagen?
- **Primera imagen de la sesión**: 3-5 minutos (arranque de motor)
- **Imágenes siguientes**: 30-90 segundos dependiendo de resolución y steps
- **Resolución 1024x1024, 30 steps**: ~45-60 segundos en Radeon 780M

### Las pestañas Styles, Models y Advanced están vacías
Son paneles informativos de solo lectura. Los valores reales están fijados y se inyectan automáticamente a la API de Fooocus CPU.

### ¿Dónde se guardan las imágenes generadas?
```
F:\Gravity_AI_bridge\_integrations\Fooocus\Fooocus\outputs\
```
Prefijo de archivo: `Gravity_Gen_XXXXX_.png`

---

## 💻 CLI y Comandos

### ¿Cómo cambio el modelo que usa el auditor?
```
Gravity> /model
```
Muestra un picker interactivo con todos los modelos disponibles.

### ¿Qué diferencia hay entre `/model` y `/mode`?
- `/model`: Cambia el **motor y modelo de IA** activo (LM Studio, Ollama, etc.).
- `/mode`: Cambia el **perfil de comportamiento** (production, development, Omni-Audit).

### ¿Cómo evito que el CLI cierre con Ctrl+C?
`Ctrl+C` dentro del CLI no cierra la sesión. Usa `/exit` para salir correctamente.

### ¿Cómo persisto una regla permanente?
```
Gravity> !aprende Siempre usa type hints explícitos en Python. Prohibido 'Any'.
✓ Regla persistida en _knowledge.json (5 total)
```

---

## 🌐 Bridge Server y Dashboard

### ¿Qué hace exactamente el bridge server?
Actúa como proxy compatible con OpenAI. Cualquier IDE puede conectarse a `http://localhost:7860/v1` y el bridge decide automáticamente qué motor usar.

### ¿Por qué mi IDE no conecta con el bridge?
1. Verifica que el bridge esté corriendo: `http://localhost:7860/health`
2. La Base URL debe ser `http://localhost:7860/v1` (con `/v1` al final)
3. El API Key puede ser cualquier valor (`gravity-local` recomendado)

### ¿Cómo inicio el bridge sin ventana visible?
Doble clic en `launchers\MODO_FANTASMA.vbs`. Los logs van a `bridge.log`.

### El Dashboard muestra "BRIDGE OFFLINE"
El Bridge Server no está corriendo. Ejecuta `launchers\INICIAR_SERVIDOR.bat` o `launchers\INICIAR_TODO.bat`.

---

## 🔑 Seguridad y API Keys

### ¿Dónde se almacenan las API Keys?
En Windows se cifran con **DPAPI** (criptografía nativa vinculada a tu sesión). Nadie puede descifrarlas sin acceso a tu sesión de Windows.

### ¿Es seguro exponer el bridge en mi red local?
Con la configuración por defecto (escucha en `0.0.0.0`), otros dispositivos de tu red pueden conectarse. Para restringirlo:
```yaml
# config.yaml
server:
  host: 127.0.0.1
```

---

## 🔬 RAG y Documentos

### ¿Qué tipo de archivos puedo indexar?
Por defecto: `.py`, `.js`, `.ts`, `.md`, `.txt`, `.json`, `.yaml`.
Con `pypdf` instalado: también `.pdf`.

### ¿El RAG actualiza automáticamente cuando modifico archivos?
No, es manual. Vuelve a ejecutar `/index <ruta>` para reindexar.

---

## ⚡ Rendimiento

### ¿Por qué a veces la respuesta es instantánea?
El **Cache Engine** (SQLite WAL) devuelve respuestas idénticas en <5ms.

### El modelo tarda mucho. ¿Qué puedo hacer?
1. Usa un modelo más pequeño: `/model`
2. Reduce el contexto: `/clear`
3. Activa modo `production`: `/mode`

---

## 🐛 Errores Comunes

| Error | Causa | Solución |
|-------|-------|---------|
| `ERROR: Sin proveedor disponible` | Ningún motor activo | Abre LM Studio o configura API Key cloud |
| `ModuleNotFoundError: No module named 'rich'` | Dependencias incompletas | Ejecuta `launchers\INSTALAR.bat` |
| `ConnectionRefusedError` IDE | Bridge no corre | Ejecuta `launchers\INICIAR_SERVIDOR.bat` |
| `amdhip64.dll no encontrado` | AMD HIP SDK no instalado | Instala AMD PRO Edition 26.Q1 for HIP |
| `OSError: Cannot find empty port 7861` | Puerto ocupado | Ejecuta `INICIAR_TODO.bat` (libera puertos automáticamente) |

---

*Gravity AI Bridge — [github.com/DarckRovert/Gravity_AI_bridge](https://github.com/DarckRovert/Gravity_AI_bridge)*
*Stream en vivo: [twitch.tv/darckrovert](https://twitch.tv/darckrovert)*
