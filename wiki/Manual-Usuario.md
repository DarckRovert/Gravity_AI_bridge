# Manual de Usuario — Gravity AI Bridge V10.0

## Inicio Rápido

### Opción A: Instalador (Usuario Final)
1. Ejecuta `Gravity_AI_Bridge_V10.0_Setup.exe`
2. Sigue el asistente (Siguiente → Siguiente → Instalar)
3. El Bridge arranca automáticamente en la bandeja del sistema
4. Doble clic en el icono para abrir el Dashboard

### Opción B: Modo Desarrollador
```bash
python bridge_server.py
```
Abre `http://localhost:7860` en el navegador.

---

## Dashboard — Navegación por Paneles

### 💬 Chat Auditor
Interfaz de chat directa con el modelo activo. Soporta streaming en tiempo real.
- Usa `Ctrl+Enter` para enviar
- El modelo activo se muestra en la esquina inferior del sidebar
- Historial de la conversación visible en el panel

### 🎨 Vision Studio
Generación de imágenes via Fooocus (requiere Fooocus iniciado).
- Ingresa el prompt descriptivo
- Selecciona el estilo y calidad
- Las imágenes generadas se guardan en `_integrations/Fooocus/outputs/`

### 🖼️ Image Queue
Cola de trabajos de generación de imágenes con estado en tiempo real.

### 🚀 Deploy
Pipeline automatizado de despliegue a Netlify.
1. Configura la ruta del proyecto
2. Click "Deploy"
3. El log en tiempo real muestra el proceso `npm build → netlify deploy`

### ⚔️ Game Servers
Control completo del servidor WoW vMaNGOS:
- Iniciar / Detener / Reiniciar
- Enviar comandos de administrador
- Registrar cuentas de jugadores
- Configurar IP pública para acceso WAN

### 🤖 Multi-Agent Orchestrator
Comparativa paralela de múltiples modelos:
1. Selecciona modo: Paralelo (comparativa libre) o Vote (consenso)
2. Selecciona cuántos modelos usar (2-4)
3. Escribe el prompt
4. Click "Ejecutar"
5. Las respuestas aparecen en cards individuales con tiempo de respuesta

### 🖥️ Hardware Monitor
Muestra en tiempo real:
- GPU primaria con tipo de backend (ROCm/CUDA/iGPU)
- VRAM disponible
- RAM del sistema
- Contexto óptimo calculado para tu hardware
- Tabla de todas las GPUs detectadas

### 💰 Cost Center
Solo activo para proveedores cloud (Anthropic, OpenAI, etc.):
- Coste de sesión actual
- Coste del día
- Barra de progreso hacia el límite diario
- Desglose por proveedor

### ⚡ Engine Watchdog
- Estado del modelo: AUTO-SWITCH o LOCKED
- Proveedor y modelo activo
- Hardware que el watchdog usó para seleccionar
- Botón "Forzar Unlock" cuando está en modo manual

### 💾 Sessions
Muestra las sesiones guardadas desde el CLI:
- Nombre de la sesión
- Branch activo
- Número de turnos
- Fecha de guardado

Comandos de sesión desde el CLI:
```
/guardar mi-sesion     → Guarda la sesión actual
/cargar mi-sesion      → Restaura una sesión
/fork rama-nueva       → Crea un branch de la conversación
```

### 📚 RAG
Estado del motor de búsqueda semántica:
- Documentos indexados
- Chunks totales
- Tamaño del índice
- Estado (Online / Sin Índice)

Indexar desde el CLI:
```
/rag indexar C:\mis-documentos\manual.pdf
/rag: ¿Cuál es la sección sobre instalación?
```

### 🔌 MCP Servers
Documentación interactiva para configurar servidores MCP en `config.yaml`.

### 🛠️ Tools
Inventario de herramientas integradas con estado (ACTIVO/INACTIVO):
- Code Runner, Web Search, Git Tool, Grep Tool, File Edit V2, Native Trigger

### 📡 System Status
Métricas en tiempo real:
- Proveedores activos y latencias
- Requests por proveedor
- Gráfico de latencia histórica

### 🛡️ Security
Resultado del último escaneo Zero-Trust con detalle de amenazas.

### 📋 Audit Log
Historial completo de todas las peticiones con proveedor, modelo, tokens y coste.

### ⚙️ Configuración
- Guardar API keys de proveedores cloud (cifradas con DPAPI)
- Configurar IDE (Continue.dev, Aider, Cursor)
- Configurar ruta del proyecto para deploy

---

## CLI — Comandos Disponibles

| Comando | Descripción |
|:---|:---|
| `/guardar <nombre>` | Guarda la sesión actual |
| `/cargar <nombre>` | Carga una sesión guardada |
| `/fork <rama>` | Crea un branch de conversación |
| `/rag indexar <ruta>` | Indexa un documento |
| `/rag: <pregunta>` | Consulta el índice RAG |
| `/buscar <query>` | Web search DuckDuckGo |
| `/run <código>` | Ejecuta código Python |
| `!aprende <regla>` | Añade regla al _knowledge.json |

---

## Configuración del Modelo (config.yaml)

```yaml
server:
  port: 7860

security:
  allowed_keys: []     # Vacío = sin restricción de key
  daily_limit_usd: 10  # Límite de gasto diario en cloud

ai_engines:            # Auto-descubiertos por ai_process_manager
  LM Studio: "C:/Users/.../LM Studio.exe"
  Ollama: "C:/Users/.../ollama app.exe"
```

---

## Integración con IDEs

### Continue.dev (VS Code)
```bash
python core/ide_integrator.py continue
```
Crea `.continue/config.yaml` apuntando al bridge en `http://localhost:7860/v1`.

### Aider
```bash
python core/ide_integrator.py aider
```
Crea `aider.conf.yml` en la raíz del proyecto.

### Cursor
```bash
python core/ide_integrator.py cursor
```
Crea `_integrations/cursor.json` con la configuración del modelo.

---

## Solución de Problemas

| Problema | Solución |
|:---|:---|
| Dashboard no carga | Verifica que `bridge_server.py` esté corriendo y el puerto 7860 no esté ocupado |
| "No provider available" | Inicia al menos un motor local (LM Studio, Ollama, etc.) |
| Costes no aparecen | Normal — solo se registran para proveedores cloud con API key |
| Watchdog en LOCKED | Click "Forzar Unlock" en el panel Watchdog |
| Build de instalador falla | Instala manualmente: `pip install pyinstaller` |
