# 🧠 Plan de Evolución Agéntica — Gravity AI Bridge V30.0 MYTHOS Roadmap

Estado: **V30.0 MYTHOS Activo** | Próximo hito: **V31.0 Swarm Autonomy**

---

## ✅ Hitos Completados

### V30.0 MYTHOS — Monolito de Excelencia & Resiliencia L9 (Julio 2026)
- [x] **LLM Frontier & Pydantic Validation:** Inyección de `complete_structured` en el gestor de proveedores con validación de esquemas Pydantic y 3 intentos de auto-corrección.
- [x] **Pre-LLM Guardrails:** Intercepción determinista en microsegundos de comandos de parada (`alto`, `stop`), reinicio (`reset`) y escalado a humano (`handoff`).
- [x] **Universal LLM Endpoint Auditor:** Demonio proactivo en segundo plano que prueba la disponibilidad real (`max_tokens: 1`) de los modelos configurados en la nube y alerta sobre modelos descontinuados (HTTP 404/410).
- [x] **Server-Sent Events (SSE) Bus:** Enrutamiento in-process `/v1/events/stream` desacoplado para notificaciones en vivo en el Dashboard React.
- [x] **Thermal Watchdog & Throttling:** Monitoreo térmico con `psutil` que suspende procesos pesados (`ollama`, `ffmpeg`, `comfyui`) si la CPU/APU alcanza los 85°C y los reanuda al enfriar.
- [x] **Home Assistant IoT Integration:** Consulta nativa del estado de sensores y alarmas mediante la API REST de Home Assistant.
- [x] **Limpieza Total de Deuda Técnica:** Purga de 20+ archivos duplicados `(1)` y erradicación de todas las rutas absolutas hardcodeadas en favor de resoluciones relativas dinámicas (`os.path.dirname`).

### V16.4 PRO — OODA Loop & Executive Packaging (Junio 2026)
- [x] Consolidación del Bucle OODA con *Scraping de Bounties* integrado (Orient & Decide).
- [x] *Resource Watchdog* para purgar procesos de IA inactivos de la VRAM bajo carga (>65%).
- [x] Scripts de compilación unificados para PyInstaller (Launcher + Bridge Server encapsulado).
- [x] Empaquetado Ejecutivo InnoSetup con Frontend React embebido.

### V16.3 PRO — Intelligent Resource Guard (Junio 2026)
- [x] Memory Guard nativo con `psutil` para monitoreo de RAM física y VRAM.
- [x] Desalojo LRU proactivo de IAs locales bajo presión de memoria.
- [x] Enrutamiento de tareas multicapa para Visión (LLaVA) y Embeddings (Nomic) con penalización estricta de cruce.

### V16.0 PRO — Motor Cinematic God-Tier (Junio 2026)
- [x] Motor GLSL PBR V13 con IBL, Lens Flares, Mandelbulb Raymarching
- [x] Post-procesado Hollywood: Cyber Glitch, ACES TM, Film Grain, Vignette
- [x] Generador AI ultra-resiliente con cascading Pollinations + FBM Procedural
- [x] Interfaz Remotion/React Cyberpunk (Karaoke neón, VHS Scanlines)
- [x] Pipeline multi-parte FFmpeg+Whisper completamente estabilizado

### V16.0 PRO — Omniscient-Tier (Mayo 2026)
- [x] Arquitectura modular `/core/video/` (5 submódulos desacoplados)
- [x] VTuber Engine V4.0 FasterLivePortrait ONNX (30-60 FPS)
- [x] Multi-Agent Orchestrator con voting, debate y routing por rol
- [x] HITL Human-in-the-Loop con cola thread-safe y timeout 120s
- [x] Monetización Factory (Language Cloner, Affiliate Manager, Social Distribution)
- [x] OBS Studio Control + Gravity Spark (Overlays AI en vivo)
- [x] RAG indexado local + toggle en caliente
- [x] Turbo KV-Cache (OLLAMA_KV_CACHE_TYPE=q4_0 automático)

---

## 🔭 V30.0 Autonomous Studio — Hitos Planificados

### 🎯 Prioridad Alta

#### Beat-Sync Engine V2 (sincronización musical precisa)
- Detección automática de **beat drops** via librosa `onset_detect`
- Mapeo de cortes de escena a los beats del BPM del track (no solo a la energía del bass)
- Transiciones de shader sincronizadas a milisegundos con el onset
- Efecto "freeze frame + explosion" en el primer drop

#### Particle System Volumétrico
- Sistema de partículas procedural en GLSL (líneas de fuerza gravitacional)
- Partículas que fluyen siguiendo el gradiente de la geometría SDF
- Sincronización de densidad con `mid` y `high` frequencies
- Emisor de partículas posicionado en los puntos de mayor luminancia del overlay

#### Upscaler IA Integrado
- Post-render automático con `Real-ESRGAN` o `ESRGAN` local
- Upscale 720p → 4K para la versión "Master" del videoclip
- Compresión x265 para distribución YouTube de alta calidad

### 🎯 Prioridad Media

#### Auto-Distribution Pipeline
- Upload automático a YouTube con título, descripción SEO y tags generados por LLM
- Auto-publicación de Shorts en TikTok e Instagram Reels tras el render
- Scheduler de publicación (horario pico de audiencia por nicho)

#### Generación de Clips Highlight
- Análisis post-render de los frames más energéticos (pico de bass + luma alta)
- Recorte automático de 15s para Instagram Stories y YouTube Shorts verticales
- Thumbnail AI-generated para YouTube usando el frame más impactante

#### Memory Engine (Lore Persistente)
- Base de conocimiento por artista/banda con estilos visuales preferidos
- Contexto persistente entre sesiones de render
- Personalidad visual coherente a lo largo de un álbum completo

### 🎯 Prioridad Baja / Experimental

#### Multi-GPU Pipeline
- Distribución del render entre GPU discreta + GPU integrada simultáneamente
- Shader compute en GPU, composición en CPU, encode en GPU (hardware H.265)
- Objetivo: render en tiempo real (1:1 con duración del audio)

#### Neural Style Transfer Adaptativo
- Estilo visual extraído de un video de referencia del usuario
- Aplicado frame a frame mediante ONNX local (sin GPU cloud)
- Compatible con el motor GLSL como capa de post-procesado adicional

#### Autonomous Music Video Director AI
- El LLM analiza la lírica completa y genera un "storyboard emocional"
- Asigna automáticamente escenas GLSL, paletas y transiciones a cada estrofa
- Zero configuración manual — el director AI toma todas las decisiones

---

## 📐 Principios de Diseño para V30.0

1. **Local-First siempre**: Ninguna función crítica dependerá de APIs cloud. Toda IA de síntesis corre localmente.
2. **Zero-Config para el usuario**: El sistema infiere estilos, duraciones y transiciones sin intervención manual.
3. **Presupuesto GPU conservador**: Máximo 16ms/frame en GPU integrada. Sin bucles de raymarching > 100 iteraciones sin LOD.
4. **Modularidad extrema**: Cada nueva feature es un módulo intercambiable. Zero acoplamiento con el core.
5. **Observabilidad total**: Cada paso del pipeline emite logs estructurados al Dashboard en tiempo real.

---

## 🔗 Dependencias Técnicas para V30.0

| Feature | Dependencia | Estado |
|---|---|---|
| Beat-Sync V2 | `librosa>=0.10` | Pendiente de integrar |
| Particle System | GLSL puro (sin deps) | En diseño |
| Upscaler IA | `basicsr` + `realesrgan` | Pendiente |
| Auto-YouTube Upload | `google-api-python-client` | Parcial (OAuth listo) |
| Neural Style Transfer | ONNX Runtime + modelo NST | Investigación |
| Multi-GPU | `moderngl` múltiples contextos | Experimental |
