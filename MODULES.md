# 📦 Documentación de Módulos (Architecture V7.0 Omni-Tier)

La capa V7.0 Omni-Tier migra a una estructura Desacoplada Modular pura y segura. Ahora el núcleo incorpora multi-proveedores locales e infraestructura basada en Nube interactuando vía DPAPI, más capacidades `zero-overhead`.

## Núcleo Desacoplado 

### 1. `provider_manager.py` & `providers/` (El Orquestador Neuronal)
Reemplaza el antiguo _scanner_ centralizando todo el ecosistema.
**Responsabilidad:** Importa automáticamente cada clase hija bajo de `ProviderPlugin` en `providers/local/` o `providers/cloud/`. Gestiona enrutamiento inteligente (Latencia/Caché), y delega el I/O.
**Superpoder:** Autoselección de modelos y fallo en cascada *Local fallback -> Cloud*.

### 2. `bridge_server.py` (Universal SSE Proxy)
Servidor minimalista en CPython que inyecta en pipelines `localhost` para integraciones IDE.
**Responsabilidad:** Recibir JSON estilo OpenAI puro de un IDE y triangularlo transparentemente al orquestador.
**Superpoder:** Es capaz de ingerir *streams puros* irregulares o asíncronos y empaquetarlos obligadamente bajo formato *OpenAI Chunk SSE*, garantizando que Cursor/Aider/Continue.dev funcionarán fluidamente consumiendo a *Mistral*, *Grok*, o *LLama3* sin importar el host.

### 3. `key_manager.py` (Seguridad Activa)
Motor integrado DPAPI en Microsoft Windows (con fallback de XOR).  
**Responsabilidad:** Evita el almacenamiento en texto plano en repositorios de cualquier API key. Las claves residen cifradas para AWS, OpenAI, Anthropic, GCP y otras.

### 4. `tools/` y `rag/` (Ejecución Cognitiva y Acceso Lógico)
La "Habilidad" otorgada al motor.
- `rag/`: Utiliza una simpleza cruda para inyectar vectores de indexación usando `TF-IDF` y/o embeddings Chroma encapsulados sobre SQLite para no desbordar latencias de arranque.
- `tools/`: Capa perimetral de scripts Python. Le da agencia autónoma (Tool Execution) para analizar Git, leer y modificar variables crudas interactivamente, ejecutar Bash, y buscar en DuckDuckGo/Brave.

### 5. `ask_deepseek.py` (Frontend AuditorCLI)
**Responsabilidades:**
- **UI & Control:** Despliega paneles interactivos desde la terminal. Engranaje directo con los comandos (`/model`, `/cost`, `/rag`, `/search`). 
- **Pipe & Hooks:** Absorbe *stdout* local y responde mediante la inyección del contexto en un buffer.

### 6. `cost_tracker.py` 
Calcula y estima los token/ms por dólar, actualizando cuotas consumidas diariamente en los proveedores Cloud a fin de evitar sorpresas y facturaciones cruzadas.

## Componentes de Almacenamiento Cifrado (State)
- `_settings.json`: La verdad universal del entorno.
- `_keystore.bin`: Certificados de clave asimétrica para Cloud APIs.
- `_knowledge.json`: Reglas duras de la red y el sistema.
- `_saves/`: El multi-verso donde se guardan sesiones enteras archivadas y listas para bifurcar (Forks).
