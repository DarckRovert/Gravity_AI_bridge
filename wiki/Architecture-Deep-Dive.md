# Architecture Deep Dive (V16.14 PRO Cognitive-Tier)

Gravity AI Bridge opera mediante una arquitectura altamente modular y resistente a fallos diseñada específicamente para entornos de recursos compartidos (como el Ryzen 7 8700G).

## 1. El Workflow Engine (`core/workflow_engine.py`)
El corazón del ecosistema. Ejecuta grafos dirigidos acíclicos (DAGs) definidos en JSON.
- **Auto-cargado de Nodos:** Dinámicamente escanea `core/nodes/` e inyecta las clases heredadas de `GravityNode`.
- **Z.ai Cloud Fallback:** Integración nativa de alta disponibilidad. Si el hardware local colapsa (OOM), el motor desvía la petición matemática o de inferencia a los clusters remotos de Z.ai de forma transparente.
- **AgentShield Ring 0:** Todo comando de sistema disparado por el Workflow pasa por un interceptor Regex que bloquea manipulaciones de rutas absolutas o borrados en el disco primario.
- **Persistencia Zombie:** Si el servidor se apaga abruptamente, la cola SQLite (`_video_queue.sqlite`) mantiene los trabajos "running" para poder ser reseteados.
- **Inyección Dinámica de Variables:** Utiliza sintaxis Jinja-like (`{{nodo.variable}}`) para encadenar las salidas de un modelo IA como entrada del siguiente nodo en tiempo de ejecución.

## 2. Optimizaciones de Hardware (AMD APU)
Para proteger la RAM unificada compartida entre CPU y GPU, Gravity implementa:

```mermaid
graph LR
    RAM[("Unified RAM 32GB")] -.->|Llama 3 Loading| LLM["NativeLlamaProvider"]
    RAM -.->|H.264 Encoder| AMF["h264_amf Hardware Encoder"]
    
    LLM -->|force_unload| Drop[Purga de Memoria]
    Drop -->|Libera espacio| AMF
```

- **Kill-Switch de LLMs (`NativeLlamaProvider.force_unload()`)**: Inyectado directamente en `video_job_node.py`. Justo antes de que FFmpeg o ComfyUI asalten la VRAM, este interruptor oblitera el modelo de lenguaje de la memoria, garantizando que el pipeline visual tenga todo el espacio necesario.
- **Aceleración H.264 AMF**: Se purgó `libx264` del ecosistema. Todos los motores, desde `video_slicer` hasta el renderizado GLSL, inyectan `-c:v h264_amf` nativamente, logrando velocidades de codificación de 4x en hardware AMD Radeon sin estresar la CPU.

## 3. High Frequency Radar
Demonio independiente (`core/high_frequency_radar.py`) que:
- Escanea RSS globales (ej: Google News) cada 60 segundos.
- Busca keywords de emergencia (*"colapso"*, *"guerra"*, *"alerta"*).
- Interrumpe pacíficamente el flujo e inyecta la crisis directamente en el motor principal invocando `run_workflow('reporter')` de forma no bloqueante.

## 4. J.A.R.V.I.S Cognitive Architecture (V16.14 PRO)
El ecosistema periférico se coordina mediante un bus asíncrono y capacidades de ejecución de comandos por voz:

```mermaid
graph TD
    Mic[Micrófono USB] -->|Audio| Voice[Voice Daemon V2]
    Voice -->|Transcribe 'crea video'| Bus((Sensory Bus ws:9999))
    Dashboard[React UI Dashboard] <-->|WS 9999 LAN| Bus
    Bus -->|voice_input| CogLoop[Cognitive Loop Thread]
    
    subgraph Gravity Engine
        CogLoop -->|Inyecta Reglas + Prompt| LLM((Provider Manager))
        LLM -->|Genera Comando '/video crear'| Extractor[Regex Command Extractor]
        Extractor -->|Ejecuta a nivel kernel| Bridge[execute_system_command]
    end
    
    Bridge -->|Resultado OK| CogLoop
    CogLoop -->|voice_output| Bus
    Bus -->|JSON| Voice
    Voice -->|Edge-TTS| Speaker[Altavoces]
```

- **Sensory Bus**: Hub asíncrono puro (Port 9999, Host 0.0.0.0) tolerante a caídas de red que permite conexión LAN desde múltiples dispositivos. Si un módulo muere, se desconecta sin tirar el servidor central. Se suprimen silenciosamente las peticiones HTTP fantasma (port scanners) para evitar tracebacks masivos.
- **Voice Daemon V2**: Opera un bucle seguro con SpeechRecognition (True VAD). Emplea bloqueos lógicos (`is_speaking = False` en un bloque `finally`) y archivos temporales únicos UUID para evitar la corrupción de disco por hilos concurrentes.
- **Cognitive Loop (En el Bridge)**: Posee **Memoria a Corto Plazo** (20 turnos de historial) y **Capacidades Ejecutivas**. Si detecta una orden, el LLM emite un Comando Slash (`/`) que el Bucle extrae ignorando charla de relleno, disparando la acción física en el servidor.
