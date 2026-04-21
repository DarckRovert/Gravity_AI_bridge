<div align="center">
  <img src="https://img.shields.io/badge/GRAVITY_AI-BRIDGE-fff?style=for-the-badge&logo=python&color=1c1c1e" alt="Gravity AI Bridge Logo"/>
  <br><br>
  
  [![Desarrollador](https://img.shields.io/badge/Author-DarckRovert-ff69b4.svg?style=flat-square)](https://github.com/DarckRovert)
  [![Licencia](https://img.shields.io/badge/License-Proprietary-red.svg?style=flat-square)](LICENSE)
  [![Architecture](https://img.shields.io/badge/Architecture-Diamond--Tier-c69c6d.svg?style=flat-square)]()
  [![Release](https://img.shields.io/badge/Release-V10.3_Stable-success.svg?style=flat-square)]()
  [![Twitch Oficial](https://img.shields.io/badge/Twitch-DarckRovert-purple.svg?style=flat-square&logo=twitch)](https://twitch.tv/darckrovert)

  <p align="center">
    <i><strong>Megainteligencia Asíncrona "Local-First" de Grado Corporativo Diamond-Tier.</strong><br>Arquitectura implacable para el puente definitivo entre LLMs, Inteligencia Difusiva Fooocus,<br>Servidores Game-Server Automáticos (WoW) y pipelines CI/CD reactivos de altísima velocidad térmica.</i>
  </p>
</div>

<br>

> [!CAUTION]  
> Este es un mega-ecosistema cerrado de naturaleza **Diamond-Tier Local-First**. No es otro proyecto open-source ni modular de la nube pública; se trata del Core Operacional Privado utilizado en vivo por las infraestructuras macro e ingenierías desarrolladas exlusivamente por y para **[DarckRovert](https://github.com/DarckRovert)**. 

---

## 🌌 El Problema Global y la Filosofía Vectorial del Proyecto

En el desarrollo tradicional, el orquestado de clústeres de IA locales (Ollama, LM Studio), herramientas de generación artística en base Gradio (Fooocus) y sub-máquinas ejecutorias de C++ (Servidores *MangosD* de World of Warcraft) resultaba en asfixia de hardware, puertos huérfanos y colapsos catastróficos por Out of Memory Errors (OOM) en las tarjetas gráficas (VRAM). 

El servidor **Gravity AI Bridge V10.3 Stable** ha sido forjado íntegramente de cero en Python nativo empleando hilos cruzados desde `http.server.ThreadingHTTPServer`. Su filosofía radica en:
- **Cero Dependencias Externas Masivas**: Operamos libres de Flask, FastAPI o bloqueos estáticos, logrando latencia interna de micro-segundos con un payload de memoria insignificante.
- **Conciencia Dinámica del Host**: La IA se auto-diagnostica leyendo la RAM del servidor en la cual habita y modificando activamente sus ventanas contextuales de razonamiento; es *software* que respeta y domestica a tu *hardware*.
- **Sub-Memoria de Tracción Rápida**: Elimina el terror del cuello de botella SSD de Windows desviando los *outputs* de log a bases de datos circulares internas (Ring-Deque Buffers) sin latencia.

---

## 🏛 Desglose Analítico y Profundo de Modulos Inyectados

### 🧠 1. El Multi-Agent Orchestrator Evolutivo (`core/multi_agent.py`)
Tu panel frontal se comunica a través de `/v1/agent/compare`. Contrario al enfoque singular obsoleto (One-Prompt-One-Model), Gravity Bridge detona ruteos concurrentes:
- Dispara solicitudes REST a través del *Provider Manager* midiendo respuestas hacia múltiples APIs al unísono (desde un puerto `11434` en red hasta tu Llama particular).
- Emite un **Voting Consensuado**, donde mediante keywords heurísticas múltiples sub-modelos desmienten la alucinación de las entidades gemelas y seleccionan el Output más lógico.
- Introduce el componente pasivo **Reasoning Stripper**: Los grandes modelos *Open Source* genéricos como *DeepSeek R1* expulsan tokens asíncronos ilegibles llamados `<think>`. Este bloque capta y tritura esos tokens intermedios mediante Regex, inyectándolos con coherencia prístina de vuelto a la IU.

### 🛡️ 2. Optimizer Termal y Biológico de HW (`core/env_optimizer.py` + Profiler)
Un puente de API de peticiones maliciosas o descuidadas puede hacer colapsar (crashing) los Drivers NVIDIA y AMD del Root Device si obligan al límite Contextual Window.
- **Auto-Discovery Físico:** Envíos a consola local de procesos invisibles leyendo el WMI, nvidia-smi y *rocm* diagnosticando el buffer total Cuda.
- Se hace control asíncrono dinámico del hiper-parámetro de Ollama `num_ctx`: bajando los threads a 4 o subiendo tus buffers a *32.000 tokens* en vivo según el estrés termal subyacente. El puente te blinda el OS ante "Over-Context Allocations".

### 🕹️ 3. Infraestructura Host: Game Server Vanilla (`core/game_server_manager.py`)
Acoplar *MangosD* (World of Warcraft V1.12 Server Base) no consiste en correr simples sub-process. 
- **Memoria Ring-Buffer Deque:** Este bridge hace Popen sobre el ejecutable Vanilla e intercepta forzosamente la tubería STDOUT. Usando arreglos tipo FIFO (`collections.deque`), aloja las últimas 500 iteraciones operativas del servidor WoW *enteramente en Random Access Memory (RAM)*. Cuando consultas via `/v1/gameserver/log`, lo que lees rebasa las limitantes crudas I/O previniendo el desgaste (wearout) de tus discos de estado sólido (SSD).
- **Protección Pre-Flight Absoluta:** Antes de ejecutar el Game Server, se inyecta un barrido de puerto 3306 forzado. Si MySQL devuelve error fatal, se cancela el sub-ejecutable y se envía una notificación roja HTTP deteniendo al Bot para evitar corrupción remota de tus *Character-Files*.
- **Auto-Backup (Dump-Safe):** Al detonar el cierre de servidor, `game_server_manager` efectúa automáticamente `mysqldump` a las Databases y genera archivos consolidados en tu directorio interno secreo `/saves`. 

### 🎨 4. Orquestador de Motores Arte y Difumado Fooocus (`core/image_queue.py`)
Los frontends perezosos a menudo tiran fallas `CP1252 Unicode (Expected 153, Got X)` cuando la dependencia del websocket de Gradio pierde conexión. Gravity soluciona este cuello de botella con bypass puro:
- Los Requests son interceptados y limpiados nativamente del error "*x*" remplazándalos con validación estática de dimensiones (`x -> *`)
- **Validación del Output Folder:** Gravity Bridge asimila la petición y ejecuta un sub-trabajo asíncrono local que crea un listado estático del disco HDD de todos los `.png` presentes, dispara a Fooocus y monitorea si la colección de carpetas posee un verdadero Diffing file. Disuelve de forma inquebrantable el reporte falso Positivo, validando verdaderas obras consumadas.
- Todo esto corre por HTTP bidireccional puro *SSE (Server-Sent-Events)* bajo `/v1/queue/stream` en flujos de 5 segundos `Event-Stream`. Cero Polling, flujo libre y vital sin desbordar el Buffer Web.

### 🎬 5. Video Studio CPU-Only (`core/video_pipeline.py`) *(V10.3)*
Generación de videos documentales automatizada sin GPU dedicada. Pipeline de 5 pasos orquestados en background:
- **LLM (Ollama)** genera un guión estructurado JSON con N escenas (título, narración, prompt visual)
- **Fooocus** (CPU) genera 1 imagen cinematic 16:9 por escena (~5 min/imagen en Ryzen 7 8700G)
- **Windows SAPI** (pyttsx3) convierte la narración a audio `.wav`, auto-seleccionando voz en español
- **ffmpeg** ensambla imagen + audio en clip `.mp4` a 24fps con padding 16:9 y codec H.264
- **ffmpeg** concatena clips → video final `.mp4` descargable via `GET /v1/video/download`

Cola SQLite aislada (`_video_queue.sqlite`) + worker daemon. Fallback automático si Fooocus no está corriendo.

### 🗃️ 6. Memoria RAM Longeva & Gestiones Financieras Contables (`RAG` & `Cost Tracker`)
1. **Retrieval-Augmented Generation (RAG):** El sub-directorio de indexaciones de `/rag_index` mastica conocimiento extra-canónico, JSONs inmensos con *chunks* localizados incrustándolos dinámicamente como apéndice a los Prompts multi-agentes antes de chocar con tu procesador. Convierte un modelo base en un experto focal de infraestructura "V10". 
2. **Sistema de Cost Tracker y Limites de Rate:** Afecta a endpoints Cloud tarifados. Contabiliza milimétricamente el "Tokens In / Tokens Out" derivándolo a un valor fiscal y alojándolo en `_cost_log.json`. Al exceder los topes impuestos del threshold, devuelve status HTTP bloqueador previniendo que gastes más de lo que deseas en peticiones API efímeras sin supervisión.

---

## 🔐 Barreras Extensivas de Auditoría y Seguridad V10.3 Stable

En vista de que `Gravity AI Bridge` administra cuentas directas WoW Vanilla por endpoints de registro saltándose Firewalls con SRP-6a y levanta pipes de procesos pesados, sus reglas de Seguridad (`SECURITY.md`) aplastan las interrupciones externas:

1. **Cortafuegos Local Anti-DDoS:** Inyectado directamente a nivel Handler de BaseHTTP: Si una IP lanza un bucle estático mayor a 120 peticiones, las variables dict de la ram bloquearán totalmente el parser ignorando la instrucción entera antes del *Body Data*, aliviando a la CPU. 
2. **Inmortalidad Cache (SQLite PRAGMA):** La clase principal lanza sistemáticamente cláusulas de `"PRAGMA wal_checkpoint(TRUNCATE)"` depurando y asesinando bloqueos fantasma en el Write-Ahead Log (WAL) del SQLite base, previniendo fuga silenciosa de Gigabytes e inestabilidad al arrancar bases sucias dejadas por versiones Beta.
3. **Audit Log y Eliminación de Spam Puros (`security_monitor.py`):** Antes la seguridad se alarmaba por todo cliente que abriese sockets. La V10.1 cuenta con listas blancas dinámicas ignorando a *Discord, Chrome, BatleNet*, enfocándose de manera brutal solo sobre injecciones peligrosas, guardando historiales acorazados `.jsonl` y pre-rotándolos al rozar 5 Megabytes, sellándolos en cajas `.pak`.

---

## 🛠️ Escalabilidad Continua: El FabricaWeb Deploy Pipeline

El ecosistema posee inyectado su pipeline local propio en `core/deploy_manager.py` para React, Vite y Next.js.
Ruteado al Endpoint `/v1/fabricaweb/deploy`, evalúa estáticamente el *package.json* incrustado para perfilar asincrónicamente comandos compilatorios a discos de Netlify / Deploy sin requerir Github Actions u observadores CI/CD pesados. Una infraestructura total y cerrada desde 1 PC.

---

> [!NOTE]  
> Este es el documento final del Manifiesto Arquitectural V10.3. Revisa los apartados indexados para soporte técnico del puente.     
> [**📖 INGRESAR A LA WIKI CORPORATIVA**](./wiki/Home.md)  |  [📜 PAUTAS DE CONTRIBUCIÓN](./CONTRIBUTING.md) 

<br>

<div align="center">
  <sub><i>The complete local deployment & logical footprint of the DarckRovert Core is highly restricted. All architectural assets belong securely to its proprietary author.</i></sub>
</div>
