<div align="center">
  <img src="https://img.shields.io/badge/GRAVITY_AI-BRIDGE-fff?style=for-the-badge&logo=python&color=20232a" alt="Gravity AI Bridge Logo"/>
  <br><br>
  
  [![Desarrollador](https://img.shields.io/badge/Author-DarckRovert-ff69b4.svg?style=flat-square)](https://github.com/DarckRovert)
  [![Licencia](https://img.shields.io/badge/License-Proprietary-red.svg?style=flat-square)](LICENSE)
  [![Architecture](https://img.shields.io/badge/Architecture-Diamond--Tier-c69c6d.svg?style=flat-square)]()
  [![Release](https://img.shields.io/badge/Release-V10.1_Stable-success.svg?style=flat-square)]()
  [![Twitch Oficial](https://img.shields.io/badge/Twitch-DarckRovert-purple.svg?style=flat-square&logo=twitch)](https://twitch.tv/darckrovert)

  <p align="center">
    <i><strong>Orquestador asíncrono "Local-First" para redes masivas Diamond-Tier.</strong><br>Bypass latencia cero para LLMs, RAG-Indexers, Servidores WoW Vanilla y Pipelines Reactivos CI/CD.</i>
  </p>
</div>

<br>

> [!WARNING]  
> Este es un proyecto de ecosistema cerrado y propietario. No está destinado a servidores públicos de código abierto ni a su bifurcación (forking) fuera de las redes físicas autorizadas explícitamente por [DarckRovert Ecosystem](https://github.com/DarckRovert). 

---

## 🌌 Visión y Alcance (V10.1)

El **Gravity AI Bridge** dejó de ser un simple túnel asíncrono para convertirse en un Demonio Host (Headless o Threaded HTTP). Su meta es abstraer en una sola capa de API las complejas variables de hardware físico y las APIs agnósticas (Ollama, LM Studio, Fooocus). Garantiza la automatización de clusters físicos desde una intranet sin exposición foránea al Cloud ni asfixia termal de los sub-sistemas huésped.

### ⚡ Highlights Tecnológicos

- **Concurrencia Pura en Python:** Construido en el módulo inamovible nativo `http.server`, lo que lo provee de un footprint (huella VRAM/RAM) prácticamente microscópico y una nula dependencia de frameworks terciarios como Flask o Node.JS.
- **Rompimiento de Interfaces Duras:** Ejecución "REST bypass" contra clientes inestables (Ej. Gradio 0.5) usando inyección por colas (Image Queue validation).
- **Protección Autónoma de Memoria (Watchdog):** Modulación de VRAM contextuales en caliente en base a la NPU/CUDA presente operando en la placa madre (`hardware_profiler`).

---

## 🏗 Estructura de Módulos (Core Suite)

El puente domina y encierra los siguientes dominios orquestales (Puedes profundizar exhaustivamente en nuestro [Wiki Corporativo](./wiki/Architecture-Deep-Dive.md)):

| Módulo Interno | Dominio Operacional | Función Principal V10.1 |
| --- | --- | --- |
| 🧠 **Multi-Agent Orchestrator** | `core/multi_agent.py` | Lanza tareas hacia N-número de modelos LLM al unísono, usando modo `Compare` y modo `Vote` (decisión consensuada de IA). Integra depuración para desvestir bloques de pensamiento `<think>`. |
| 🛡️ **VRAM Env Optimizer** | `core/env_optimizer.py` | Audita la RAM compartida del OS al vuelo y escala artificialmente los `num_ctx` bloqueados de Ollama salvándote de Crashes (Out-Of-Memory) fatales. |
| 🗃️ **RAG Indexing Memory** | `_rag_index/` | Memoria a largo alcance. Indexador de vectores JSON que alimenta un puente conectivo RAG entre tus LLMs para interacciones y contextos hiper-extensos de archivos subidos. |
| 🕹️ **Game Server Manager** | `core/game_server_manager.py` | Inicia/Detiene *MangosD.exe* local (WoW Server). Traga automáticamente su Output (STDOUT) en memoria Ring-Buffer y lanza dumps autónomos en `MySQL` al apagarse. |
| 🎨 **Orquestador Difusivo** | `core/image_queue.py` | Pipeline de Arte. Envía prompts al entorno Fooocus por subprocesos. Auto-valida archivos pasivamente en los discos duros y emite telemetría Server-Sent Events (SSE) `v1/queue`. |
| 💸 **Cost & Session Tracker** | `core/cost_tracker.py` | En caso de que uses un LLM tarifado, audita el logueo de token-gasto a nivel decimal para forzar paradas a servidores antes de liquidar tarjetas. |
| 🚀 **FabricaWeb Deployer** | `core/deploy_manager.py` | Escanea repos React/Vite aislados en `_integrations`, traga el *package.json* y forjea despliegues automatizados (Auto CI/CD pipe push). |

---

## 🔒 Postura de Seguridad e Infiltración

El proyecto se despliega por naturaleza y exclusividad en `/localhost` o VLAN seguras. Para mitigar fallas en sus API y la vulneración del límite de hardware, se ejecutan las siguientes cortafuegos incorporados.

> [!CAUTION]
> Cualquier intervención hacia el caché SQlite estacional desprotegido podría bloquear sub-procesos en vivo. El puente cuenta con auto-truncamiento de colas `(PRAGMA wal_checkpoint)` cada que nace.

* **Rate Limiter Absoluto (120 req/60s):** Todo atacante local que infeste las peticiones web rebotará con código *429 Too Many Requests*, previniendo la latencia LLM de fondo.
* **Escudo Pasivo:** Su `security_monitor` incorporado no se asusta por procesos de rutina (ej. Discord, Steam) garantizando que tus Logs de Seguridad (JSONL) en la carpeta Root no superen la masa estática del límite de *5MB físicos*.

---

<div align="center">
  <br>
  <b>Para depuración a nivel código fuente de API, por favor apunte a nuestro HUB:</b><br><br>
  
  [📚 IR AL WIKI CORPORATIVO EXACTO](./wiki/Home.md)  |  [📜 PAUTAS DE CONTRIBUCIÓN](./CONTRIBUTING.md)
  
  <br>
  <sub><i>Gravity bridge design, rights, and orchestration are sole propriety of DarckRovert Core Protocol.</i></sub>
</div>
