/* ==========================================================================
   GRAVITY AI BRIDGE V15.1 PRO - Interactive Scripts
   Particle Canvas, Command Line Simulator, Multi-Agent Arena, Watchdog, HITL
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {

    // ==========================================
    // 1. GRAVITY PARTICLES BACKGROUND CANVAS
    // ==========================================
    const canvas = document.getElementById('gravity-bg');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let particles = [];
        const particleCount = 75;
        let mouse = { x: null, y: null, active: false };

        // Resize handler
        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        // Particle Class
        class Particle {
            constructor() {
                this.reset();
            }

            reset() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = Math.random() * 2.5 + 0.5;
                this.baseXSpeed = Math.random() * 0.4 - 0.2;
                this.baseYSpeed = Math.random() * 0.4 - 0.2;
                this.vx = this.baseXSpeed;
                this.vy = this.baseYSpeed;
                this.color = `rgba(139, 92, 246, ${Math.random() * 0.3 + 0.15})`; // violet accent
            }

            update() {
                // Gravity attraction center
                let targetX = mouse.active ? mouse.x : canvas.width / 2;
                let targetY = mouse.active ? mouse.y : canvas.height / 2;
                
                let dx = targetX - this.x;
                let dy = targetY - this.y;
                let distance = Math.sqrt(dx * dx + dy * dy);

                // Attraction force logic
                if (distance < 300) {
                    let force = (300 - distance) / 3000;
                    this.vx += (dx / distance) * force * 0.5;
                    this.vy += (dy / distance) * force * 0.5;
                } else {
                    // Return slowly to base speed
                    this.vx += (this.baseXSpeed - this.vx) * 0.02;
                    this.vy += (this.baseYSpeed - this.vy) * 0.02;
                }

                // Speed capping
                const maxSpeed = 1.5;
                let speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
                if (speed > maxSpeed) {
                    this.vx = (this.vx / speed) * maxSpeed;
                    this.vy = (this.vy / speed) * maxSpeed;
                }

                this.x += this.vx;
                this.y += this.vy;

                // Bounce at edges
                if (this.x < 0 || this.x > canvas.width) { this.vx *= -1; this.x = Math.max(0, Math.min(this.x, canvas.width)); }
                if (this.y < 0 || this.y > canvas.height) { this.vy *= -1; this.y = Math.max(0, Math.min(this.y, canvas.height)); }
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.fill();
            }
        }

        // Initialize particles
        for (let i = 0; i < particleCount; i++) {
            particles.push(new Particle());
        }

        // Track Mouse
        window.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
            mouse.active = true;
        });

        window.addEventListener('mouseleave', () => {
            mouse.active = false;
        });

        // Animation Loop
        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw a subtle nebula in the center or at mouse position
            let glowX = mouse.active ? mouse.x : canvas.width / 2;
            let glowY = mouse.active ? mouse.y : canvas.height / 2;
            let grad = ctx.createRadialGradient(glowX, glowY, 50, glowX, glowY, 320);
            grad.addColorStop(0, 'rgba(168, 85, 247, 0.07)'); // purple glow
            grad.addColorStop(0.5, 'rgba(6, 182, 212, 0.03)'); // cyan glow
            grad.addColorStop(1, 'transparent');
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw interactive quantum constellation lines between close particles
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    let dx = particles[i].x - particles[j].x;
                    let dy = particles[i].y - particles[j].y;
                    let dist = Math.sqrt(dx * dx + dy * dy);
                    
                    if (dist < 115) {
                        // Fade alpha based on distance
                        let alpha = ((115 - dist) / 115) * 0.12;
                        
                        // Amplify glow if connection is near cursor (gravitational excitation)
                        if (mouse.active) {
                            let midX = (particles[i].x + particles[j].x) / 2;
                            let midY = (particles[i].y + particles[j].y) / 2;
                            let mdx = mouse.x - midX;
                            let mdy = mouse.y - midY;
                            let mdist = Math.sqrt(mdx * mdx + mdy * mdy);
                            if (mdist < 180) {
                                alpha += ((180 - mdist) / 180) * 0.22;
                            }
                        }
                        
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        
                        // Cyberpunk linear gradient for connection lines
                        let lineGrad = ctx.createLinearGradient(particles[i].x, particles[i].y, particles[j].x, particles[j].y);
                        lineGrad.addColorStop(0, `rgba(168, 85, 247, ${alpha * 0.8})`);
                        lineGrad.addColorStop(1, `rgba(6, 182, 212, ${alpha})`);
                        
                        ctx.strokeStyle = lineGrad;
                        ctx.lineWidth = 0.75;
                        ctx.stroke();
                    }
                }
            }

            // Update & Draw particles
            particles.forEach(p => {
                p.update();
                p.draw();
            });

            requestAnimationFrame(animate);
        };
        animate();
    }


    // ==========================================
    // 2. INTERACTIVE TERMINAL "GRAVITY CLI"
    // ==========================================
    const termInput = document.getElementById('terminal-input');
    const termScreen = document.getElementById('terminal-screen');
    const termInputRow = termInput?.parentElement;

    if (termInput && termScreen) {
        // Stream text writer
        const writeToTerminal = (lines, speed = 15, callback = null) => {
            let lineIdx = 0;

            const printLine = () => {
                if (lineIdx >= lines.length) {
                    // Bring input row back down
                    if (termInputRow) {
                        termScreen.appendChild(termInputRow);
                        termInput.focus();
                    }
                    termScreen.scrollTop = termScreen.scrollHeight;
                    if (callback) callback();
                    return;
                }

                const lineData = lines[lineIdx];
                const lineDiv = document.createElement('div');
                lineDiv.className = `terminal-line ${lineData.type || ''}`;
                termScreen.insertBefore(lineDiv, termInputRow);

                let charIdx = 0;
                const text = lineData.text;

                const printChar = () => {
                    if (charIdx >= text.length) {
                        lineIdx++;
                        termScreen.scrollTop = termScreen.scrollHeight;
                        setTimeout(printLine, 100);
                        return;
                    }
                    
                    // Simple HTML entity escape to avoid rendering HTML inside streaming text
                    const char = text[charIdx];
                    if (char === '<') lineDiv.innerHTML += '&lt;';
                    else if (char === '>') lineDiv.innerHTML += '&gt;';
                    else lineDiv.innerHTML += char;
                    
                    charIdx++;
                    termScreen.scrollTop = termScreen.scrollHeight;
                    setTimeout(printChar, speed);
                };
                printChar();
            };

            // Temporarily detach input to avoid multiple writes during streaming
            if (termInputRow) {
                termInputRow.remove();
            }
            printLine();
        };

        // Commands execution map
        const runCommand = (cmdText) => {
            const cleanCmd = cmdText.trim().toLowerCase();
            
            // Print user command prompt first
            const userPromptDiv = document.createElement('div');
            userPromptDiv.className = 'terminal-line';
            userPromptDiv.innerHTML = `<span class="terminal-prompt">gravity:~$</span> ${cmdText}`;
            termScreen.insertBefore(userPromptDiv, termInputRow);

            if (cleanCmd === '') {
                termScreen.scrollTop = termScreen.scrollHeight;
                return;
            }

            if (cleanCmd === 'help') {
                writeToTerminal([
                    { text: 'Available commands on this demo:', type: 'system-msg' },
                    { text: '  gravity status  - Check real-time engine, CPU, VRAM, and models latency' },
                    { text: '  gravity spawn   - Instantiates a multi-session asynchronous worker (coder)' },
                    { text: '  gravity vote    - Simulates parallel multi-agent voting debate' },
                    { text: '  gravity spark   - Dynamically inject overlays HTML into OBS Studio' },
                    { text: '  gravity deploy  - Simulates the packaging and deployment pipeline to Netlify' },
                    { text: '  clear           - Clears the console logs' }
                ]);
            } else if (cleanCmd === 'clear') {
                // Clear all except background messages
                const lines = termScreen.querySelectorAll('.terminal-line');
                lines.forEach(l => l.remove());
                termScreen.appendChild(termInputRow);
                termInput.value = '';
                termInput.focus();
            } else if (cleanCmd === 'gravity status') {
                writeToTerminal([
                    { text: '[SYSTEM STATUS] Running Diagnostic on LocalHost...', type: 'system-msg' },
                    { text: '  Host CPU: AMD Ryzen 7 8700G (iGPU 8GB VRAM allocated) - OK', type: 'success-msg' },
                    { text: '  Ollama Provider: localhost:11434 - CONNECTED', type: 'success-msg' },
                    { text: '  LM Studio Provider: localhost:1234 - CONNECTED', type: 'success-msg' },
                    { text: '  RAG Vector Index: 147 documents - READY', type: 'success-msg' },
                    { text: '  Active Models: [deepseek-r1:8b (ollama), llama-3.1-8b (lm_studio)]', type: 'highlight' },
                    { text: '  Watchdog state: UNLOCKED | VRAM: 35.2% | Temperature: 58C', type: 'success-msg' },
                    { text: '  Latency Bridge (Internal SSE Pipe): 1.4ms (Microseconds standard)', type: 'success-msg' }
                ]);
            } else if (cleanCmd === 'gravity spawn' || cleanCmd.startsWith('gravity spawn')) {
                writeToTerminal([
                    { text: '[SPAWNER] Spawning isolated agent session...', type: 'system-msg' },
                    { text: '  Spawning worker type: Coder (CapacityWake invoked)...', type: 'system-msg' },
                    { text: '  Worker allocated PID: 18452 (Isolated subprocess spawned)', type: 'highlight' },
                    { text: '  State: SSE stream connection established at /v1/sessions/spawn/18452', type: 'success-msg' },
                    { text: '  Logs: [Worker-18452] Listening for code-generation jobs.', type: 'success-msg' },
                    { text: '[OK] Worker active. Subprocess ready. System load: STABLE.', type: 'success-msg' }
                ]);
            } else if (cleanCmd.startsWith('gravity vote')) {
                writeToTerminal([
                    { text: '[MULTIPLE-AGENT] Initializing parallel voting consensus debate...', type: 'system-msg' },
                    { text: '  Prompt: "diseñar cola paralela"', type: 'system-msg' },
                    { text: '  Consensus Agents: DeepSeek-R1 (Reasoner), Llama-3.1 (Coder), Mistral (Auditor)', type: 'highlight' },
                    { text: '  [Agent-1 DeepSeek-R1] Generating reasoning path...', type: 'system-msg' },
                    { text: '  [Reasoning Stripper] Filtering <think> tokens in hot pipeline...', type: 'warning-msg' },
                    { text: '  [Agent-2 Coder] Evaluating algorithmic efficiency... (No loops found)', type: 'system-msg' },
                    { text: '  [Agent-3 Auditor] Security Audit: Thread-safe lock parameters validated.', type: 'success-msg' },
                    { text: '  Debate Consensus: 100% agreement. Emitting finalized response.', type: 'success-msg' }
                ]);
            } else if (cleanCmd.startsWith('gravity spark')) {
                writeToTerminal([
                    { text: '[SPARK ENGINE] Connecting OBS WebSocket v5 on port 4455...', type: 'system-msg' },
                    { text: '  OBS State: Connected. Current Scene: "Live Stream Coding".', type: 'success-msg' },
                    { text: '  Generating overlay code in Hot Spark pipeline...', type: 'system-msg' },
                    { text: '  CSS Variables injected: --neon-glow: #8b5cf6 (Neon Violet)', type: 'highlight' },
                    { text: '  Injecting HTML structure directly into OBS Browser Source: "gravity-overlay"...', type: 'system-msg' },
                    { text: '[SPARK SUCCESS] OBS overlay updated instantly without reload.', type: 'success-msg' }
                ]);
            } else if (cleanCmd === 'gravity deploy') {
                writeToTerminal([
                    { text: '[DEPLOY PIPELINE] Initializing packaging daemon...', type: 'system-msg' },
                    { text: '  Scanning: f:\\Gravity_AI_bridge\\frontend\\dist... Found 26 modules.', type: 'system-msg' },
                    { text: '  Verifying bundle integrity... hash matched [V15.1-78a4c1]', type: 'success-msg' },
                    { text: '  Invoking Netlify API deployment bridge...', type: 'system-msg' },
                    { text: '  [Netlify] Uploading static assets stream... 100%', type: 'success-msg' },
                    { text: '  [Netlify] Assigning dynamic subdomain... gravity-bridge.netlify.app', type: 'highlight' },
                    { text: '  [Netlify] SSL/DNS propagation checks - OK', type: 'success-msg' },
                    { text: '[SUCCESS] Landing page uploaded. Live URL: https://gravity-bridge.netlify.app', type: 'success-msg' }
                ]);
            } else {
                writeToTerminal([
                    { text: `gravity: command not found: "${cmdText}"`, type: 'error-msg' },
                    { text: 'Type "help" to view all available commands in this interactive demo.', type: 'system-msg' }
                ]);
            }

            termInput.value = '';
        };

        // Input enter key listener
        termInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                runCommand(termInput.value);
            }
        });

        // Quick suggestions button clicks
        const suggestBtns = document.querySelectorAll('.cmd-btn');
        suggestBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const cmd = btn.getAttribute('data-command');
                termInput.value = cmd;
                runCommand(cmd);
            });
        });
    }


    // ==========================================
    // 3. MULTI-AGENT DEBATE ARENA SIMULATION
    // ==========================================
    const debatePromptSelect = document.getElementById('debate-prompt');
    const startDebateBtn = document.getElementById('start-debate-btn');
    const arenaStream = document.getElementById('arena-stream');
    const stripperToggle = document.getElementById('stripper-toggle');
    const arenaTabs = document.querySelectorAll('.arena-tab');

    // Sample debate scripts
    const debatesScripts = [
        // Prompt 0: Rust Binary Search
        {
            reasoner: `<think>
1. Necesito optimizar la búsqueda binaria para Rust.
2. La búsqueda binaria estándar en porciones (&[T]) usa índices usize.
3. Para hacerlo asíncrono, normalmente no se bloquea la CPU. Pero la búsqueda binaria en memoria es O(log n), muy rápida. Si la porción es masiva (gigantesca, paginada en memoria mapeada), podríamos usar lecturas asíncronas de disco.
4. Asumiré que el usuario quiere optimización a nivel de registro CPU utilizando operaciones sin ramificaciones (branchless binary search) y soporte asíncrono si los datos provienen de un stream indexado de archivos.
5. Plan de acción:
   a. Crear una búsqueda binaria asíncrona usando Tokio File.
   b. Usar branchless indexes para optimizar predicciones de saltos del procesador.
</think>
\`\`\`rust
pub async fn binary_search_async(file: &mut tokio::fs::File, target: u32) -> io::Result<Option<u64>> {
    let len = file.metadata().await?.len();
    let mut low = 0;
    let mut high = len / 4; // Asumiendo enteros de 32 bits
    // Lógica branchless asíncrona...
}
\`\`\``,
            coder: `Aquí tienes la implementación optimizada en Rust. He implementado una búsqueda binaria sin ramificaciones (branchless) para minimizar fallos en la predicción del pipeline de la CPU, envuelta en un flujo Tokio asíncrono para lecturas masivas no bloqueantes:

\`\`\`rust
use tokio::fs::File;
use tokio::io::{self, AsyncSeekExt, AsyncReadExt, SeekFrom};

pub async fn binary_search_async_branchless(
    file: &mut File, 
    size: u64, 
    target: i32
) -> io::Result<Option<u64>> {
    let mut base = 0u64;
    let mut len = size;
    
    while len > 1 {
        let half = len / 2;
        let mid = base + half;
        file.seek(SeekFrom::Start(mid * 4)).await?;
        let mut buf = [0u8; 4];
        file.read_exact(&mut buf).await?;
        let val = i32::from_le_bytes(buf);
        
        // Operación lógica condicional para evitar ramificaciones (branchless)
        base = if val < target { base + half } else { base };
        len -= half;
    }
    
    // Verificación final del índice
    file.seek(SeekFrom::Start(base * 4)).await?;
    let mut buf = [0u8; 4];
    file.read_exact(&mut buf).await?;
    if i32::from_le_bytes(buf) == target {
        Ok(Some(base))
    } else {
        Ok(None)
    }
}
\`\`\``,
            auditor: `**Auditoría de Seguridad & Rendimiento:**
1. **Acceso Concurrente:** Si el archivo se comparte entre múltiples hilos, usar un descriptor mutable único causará colisiones de posición de cursor (Seek). Se recomienda usar la API de posición indexada de Windows/Linux nativa (pread) o clonar el descriptor por sesión.
2. **Seguridad Aritmética:** No hay peligro de desbordamiento en enteros usize ya que Rust realiza comprobaciones de rango, pero el casteo de \`mid * 4\` debe protegerse con \`checked_mul\` en hosts de 32 bits.
3. **Optimización:** La técnica branchless disminuye las latencias de CPU en un 38% sobre arrays enormes. Excelente.`,
            consensus: `### Solución Consensuada Final:
Búsqueda binaria asíncrona no bloqueante optimizada para CPU (branchless) y segura para entornos multihilo.
* **Optimización de CPU:** Código estructurado sin condicionales anidados dentro del bucle crítico.
* **Seguridad de Hilos:** Se reemplaza el cursor mutable secuencial por lecturas concurrentes indexadas usando Tokio \`read_at\` (en Linux/Unix se mapea a pread) evitando colisiones de hilos.

\`\`\`rust
use std::os::unix::fs::FileExt; // Para pread concurrente sin Seek mutable

// Lógica concurrente segura sin colisión de cursor
pub fn search_thread_safe(file: &std::fs::File, size: u64, target: i32) -> Result<Option<u64>, std::io::Error> {
    let mut base = 0u64;
    let mut len = size;
    while len > 1 {
        let half = len / 2;
        let mid = base + half;
        let mut buf = [0u8; 4];
        file.read_exact_at(&mut buf, mid * 4)?;
        let val = i32::from_le_bytes(buf);
        base = if val < target { base + half } else { base };
        len -= half;
    }
    Ok(Some(base))
}
\`\`\``
        },
        // Prompt 1: Rate Limiter
        {
            reasoner: `<think>
1. Diseñar un Rate Limiter thread-safe en lenguajes concurrentes (e.g., C++ o Go). Usaré Go por claridad.
2. El algoritmo más común es Token Bucket.
3. Para que sea thread-safe, necesito mutexes o primitivas atómicas del paquete sync/atomic.
4. Con sync/atomic, evitamos los bloqueos pesados de un Mutex mutex, logrando latencias ínfimas.
5. Flujo del Token Bucket asíncrono con marcas de tiempo atómicas.
</think>
\`\`\`go
type RateLimiter struct {
    rate       int64
    limit      int64
    tokens     int64
    lastUpdate int64
}
// Algoritmo de actualización atómico...
\`\`\``,
            coder: `Aquí tienes la implementación ultra-eficiente en Go de un Limitador de Tasa (Rate Limiter) basado en Token Bucket. He utilizado exclusión mutua de CPU de bajo nivel con el paquete \`sync/atomic\` en lugar de canales o mutexes tradicionales, eliminando cambios de contexto de hilos (thread context switching) de manera absoluta:

\`\`\`go
package main

import (
	"sync/atomic"
	"time"
)

type AtomicRateLimiter struct {
	rate       int64 // Tokens a regenerar por segundo
	capacity   int64 // Capacidad máxima del cubo
	tokens     int64 // Tokens activos disponibles
	lastUpdate int64 // Marca de tiempo de Unix en nanosegundos
}

func NewLimiter(rate, capacity int64) *AtomicRateLimiter {
	return &AtomicRateLimiter{
		rate:       rate,
		capacity:   capacity,
		tokens:     capacity,
		lastUpdate: time.Now().UnixNano(),
	}
}

func (rl *AtomicRateLimiter) Allow() bool {
	now := time.Now().UnixNano()
	
	// Carga atómica de variables
	last := atomic.LoadInt64(&rl.lastUpdate)
	elapsed := now - last
	
	// Regeneración matemática
	generatedTokens := (elapsed * rl.rate) / int64(time.Second)
	
	for {
		currentTokens := atomic.LoadInt64(&rl.tokens)
		newTokens := currentTokens + generatedTokens
		if newTokens > rl.capacity {
			newTokens = rl.capacity
		}
		
		if newTokens < 1 {
			return false // Cubo vacío, petición limitada
		}
		
		// Intenta decrementar un token y actualizar la marca temporal atómicamente (CAS Loop)
		if atomic.CompareAndSwapInt64(&rl.tokens, currentTokens, newTokens-1) {
			atomic.StoreInt64(&rl.lastUpdate, now)
			return true
		}
		// Si CompareAndSwap falla por competencia concurrente, el bucle reintenta de inmediato
	}
}
\`\`\``,
            auditor: `**Auditoría de Seguridad Concurrente:**
1. **Bucle CAS (Compare And Swap):** Bajo una contención masiva extrema (millones de peticiones simultáneas), el bucle CAS de Go puede consumir ciclos de CPU de forma excesiva. Se recomienda inyectar un breve yield (\`runtime.Gosched()\`) tras 3 fallos consecutivos en el CAS Loop.
2. **Seguridad contra Desbordamientos:** La multiplicación \`elapsed * rl.rate\` podría desbordar el entero de 64 bits si transcurren meses de inactividad del servidor. Es obligatorio asegurar un límite al tiempo transcurrido en el cálculo.`,
            consensus: `### Solución Consensuada Final:
Limitador de Tasa Token Bucket Thread-Safe sin Mutexes con mitigación de estrés de CPU y protección contra desbordamientos.

* **Mitigación de Estrés de CPU:** Se añade \`runtime.Gosched()\` en el bucle CAS para evitar bloqueos por giros improductivos (spinlock starvation).
* **Protección de Desbordamiento:** Se limita el intervalo máximo de tiempo evaluado para evitar desbordes en hilos de larga duración.

\`\`\`go
func (rl *AtomicRateLimiter) Allow() bool {
    now := time.Now().UnixNano()
    last := atomic.LoadInt64(&rl.lastUpdate)
    elapsed := now - last
    
    // Evitar desbordamiento de enteros limitando el cálculo de tiempo
    maxElapsed := (rl.capacity * int64(time.Second)) / rl.rate
    if elapsed > maxElapsed {
        elapsed = maxElapsed
    }
    generated := (elapsed * rl.rate) / int64(time.Second)
    // ... CAS loop con runtime.Gosched()
}
\`\`\``
        },
        // Prompt 2: Semaphores vs Mutexes
        {
            reasoner: `<think>
1. Explicar la diferencia entre semáforos y mutexes en sistemas de tiempo real (RTOS).
2. Puntos clave:
   - Mutex tiene el concepto de pertenencia (ownership). Solo el hilo que bloqueó el mutex puede desbloquearlo.
   - Semáforo es un contador, se usa para señalización entre hilos. Un hilo puede disparar el semáforo y otro consumirlo.
   - Mutex tiene protección contra inversión de prioridad (Priority Inheritance). Semáforos no.
3. Formatear la respuesta técnica y clara.
</think>
Un Mutex y un Semáforo se comportan de manera similar en la superficie, pero sus reglas a nivel de Kernel en RTOS son fundamentalmente distintas.`,
            coder: `Aquí tienes la comparación técnica estructurada para ingenieros de sistemas.

### 1. Mutex (Mutual Exclusion)
* **Concepto de Propiedad (Ownership):** Un mutex es un mecanismo de bloqueo con "dueño". Solo el hilo exacto que adquirió el mutex (\`lock\`) puede liberarlo (\`unlock\`).
* **Inversión de Prioridades:** Los mutexes modernos implementan protocolos como **Priority Inheritance** (Herencia de Prioridades). Si un hilo de alta prioridad está bloqueado por un mutex en manos de un hilo de baja prioridad, el kernel eleva temporalmente la prioridad del hilo de baja prioridad para evitar bloqueos por hilos de prioridad intermedia.
* **Uso estándar:** Protección estricta de secciones críticas de memoria.

### 2. Semáforo (Contador de Señales)
* **Sin dueños:** Un semáforo es simplemente un contador atómico de señales. Cualquier hilo del sistema puede incrementar el semáforo (\`Signal / V\`) y cualquier otro hilo diferente puede decrementarlo (\`Wait / P\`).
* **Inversión de Prioridades:** **NO** admiten herencia de prioridades, lo que los hace peligrosos para proteger secciones críticas en sistemas embebidos de tiempo real estricto.
* **Uso estándar:** Sincronización de tareas y señalización de eventos (ej. productor-consumidor).`,
            auditor: `**Anotación de Auditoría de Sistemas:**
El análisis es impecable. Un error clásico en sistemas embebidos es usar semáforos binarios como si fueran mutexes, resultando en caídas catastróficas por inversión de prioridad que son indetectables en depuración estándar. Excelente aclaración del concepto de herencia de prioridad.`,
            consensus: `### Resumen Técnico Consensuado:
* **Usa Mutex** exclusivamente para proteger áreas de datos compartidos en memoria (Secciones Críticas) donde la propiedad del recurso deba garantizarse y se requiera protección de herencia de prioridades para evitar bloqueos del planificador del Kernel.
* **Usa Semáforos** para tareas de coordinación, señalización asíncrona de eventos y control de flujos de producción/consumición entre múltiples hilos autónomos.`
        }
    ];

    let activeAgentTab = 'reasoner';
    let debateActive = false;

    // Arena tabs switching
    arenaTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            arenaTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeAgentTab = tab.getAttribute('data-agent');
            
            // Re-render state if a debate has already run
            if (debateActive) {
                renderActiveTabContent();
            }
        });
    });

    const renderActiveTabContent = () => {
        const promptIdx = parseInt(debatePromptSelect.value);
        const script = debatesScripts[promptIdx];
        const stripEnabled = stripperToggle.checked;
        
        let textToShow = '';
        if (activeAgentTab === 'reasoner') {
            textToShow = script.reasoner;
        } else if (activeAgentTab === 'coder') {
            textToShow = script.coder;
        } else if (activeAgentTab === 'auditor') {
            textToShow = script.auditor;
        } else if (activeAgentTab === 'consensus') {
            textToShow = script.consensus;
        }

        // Apply Reasoning Stripper to Consensus / General if active
        if (stripEnabled && activeAgentTab === 'consensus') {
            // Simulated consensus code is already clean, but we enforce formatting
            arenaStream.innerHTML = `<div class="terminal-line success-msg">[Reasoning Stripper: OK. 0 think tokens emitted]</div>` + 
                                    `<pre class="code-pre"><code>${escapeHTML(textToShow)}</code></pre>`;
        } else if (activeAgentTab === 'reasoner') {
            if (stripEnabled) {
                // Strips the <think>...</think> block from DeepSeek using regex simulator
                const stripped = textToShow.replace(/<think>[\s\S]*?<\/think>\n?/g, '');
                arenaStream.innerHTML = `<div class="terminal-line warning-msg">[Reasoning Stripper: 1 think block hidden]</div>` +
                                        `<pre class="code-pre"><code>${escapeHTML(stripped)}</code></pre>`;
            } else {
                // Shows with think block styled
                const parts = textToShow.split('</think>');
                if (parts.length > 1) {
                    const thinkContent = parts[0].replace('<think>', '');
                    arenaStream.innerHTML = `<div class="think-block">&lt;thinking_tokens&gt;\n${escapeHTML(thinkContent)}&lt;/thinking_tokens&gt;</div>` +
                                            `<pre class="code-pre"><code>${escapeHTML(parts[1])}</code></pre>`;
                } else {
                    arenaStream.innerHTML = `<pre class="code-pre"><code>${escapeHTML(textToShow)}</code></pre>`;
                }
            }
        } else {
            arenaStream.innerHTML = `<pre class="code-pre"><code>${escapeHTML(textToShow)}</code></pre>`;
        }
    };

    const escapeHTML = (str) => {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    // Run simulated debate stream
    if (startDebateBtn && arenaStream) {
        startDebateBtn.addEventListener('click', () => {
            arenaStream.innerHTML = '';
            debateActive = true;
            
            const promptIdx = parseInt(debatePromptSelect.value);
            const script = debatesScripts[promptIdx];
            const stripEnabled = stripperToggle.checked;
            
            // Pestaña inicial por defecto
            arenaTabs.forEach(t => t.classList.remove('active'));
            document.getElementById('tab-reasoner').classList.add('active');
            activeAgentTab = 'reasoner';

            const lines = [
                { text: '[MULTIPLE-AGENT] Launching concurrent LLM debate instances...', type: 'system-msg' },
                { text: '  Node 1: deepseek-r1:8b (Active Provider: Ollama local)', type: 'highlight' },
                { text: '  Node 2: llama-3.1-8b (Active Provider: LM Studio local)', type: 'highlight' },
                { text: '  Node 3: mistral-7b (Active Provider: Ollama local - Role: Auditor)', type: 'highlight' },
                { text: '[STREAM] DeepSeek-R1 beginning reasoning pipeline...', type: 'system-msg' }
            ];

            let lineIdx = 0;
            const printPreLogs = () => {
                if (lineIdx >= lines.length) {
                    // Start streaming actual text
                    setTimeout(streamReasonerText, 300);
                    return;
                }
                const div = document.createElement('div');
                div.className = `terminal-line ${lines[lineIdx].type}`;
                div.textContent = lines[lineIdx].text;
                arenaStream.appendChild(div);
                lineIdx++;
                arenaStream.scrollTop = arenaStream.scrollHeight;
                setTimeout(printPreLogs, 200);
            };
            printPreLogs();

            // Stream DeepSeek output letter by letter
            const streamReasonerText = () => {
                const thinkDiv = document.createElement('div');
                arenaStream.appendChild(thinkDiv);
                
                const responseText = script.reasoner;
                let charIdx = 0;
                let isThinking = responseText.includes('<think>');
                
                if (isThinking && stripEnabled) {
                    // Instantly hide the think block and log warning
                    const warnDiv = document.createElement('div');
                    warnDiv.className = 'terminal-line warning-msg';
                    warnDiv.textContent = '[Reasoning Stripper] Intercepted DeepSeek-R1 thinking tokens. Blocking stream to UI...';
                    arenaStream.appendChild(warnDiv);
                    
                    const textWithoutThink = responseText.replace(/<think>[\s\S]*?<\/think>\n?/g, '');
                    
                    const codeDiv = document.createElement('pre');
                    codeDiv.className = 'code-pre';
                    const codeInner = document.createElement('code');
                    codeDiv.appendChild(codeInner);
                    arenaStream.appendChild(codeDiv);

                    let cIdx = 0;
                    const printClean = () => {
                        if (cIdx >= textWithoutThink.length) {
                            concludeDebateLogs();
                            return;
                        }
                        codeInner.textContent += textWithoutThink[cIdx];
                        cIdx++;
                        arenaStream.scrollTop = arenaStream.scrollHeight;
                        setTimeout(printClean, 5);
                    };
                    printClean();
                    return;
                }

                // Normal streaming (either no think block, or stripper disabled)
                let currentContainer = arenaStream;
                let inThinkTag = false;
                
                const printNormal = () => {
                    if (charIdx >= responseText.length) {
                        concludeDebateLogs();
                        return;
                    }

                    const char = responseText[charIdx];
                    
                    // Simple simulated tag parsing
                    if (responseText.substring(charIdx, charIdx + 7) === '<think>') {
                        inThinkTag = true;
                        const thinkBlock = document.createElement('div');
                        thinkBlock.className = 'think-block';
                        thinkBlock.innerHTML = '<strong>&lt;thinking_tokens&gt;</strong><br>';
                        arenaStream.appendChild(thinkBlock);
                        currentContainer = thinkBlock;
                        charIdx += 7;
                        printNormal();
                        return;
                    }
                    
                    if (responseText.substring(charIdx, charIdx + 8) === '</think>') {
                        inThinkTag = false;
                        currentContainer = arenaStream;
                        charIdx += 8;
                        const spacing = document.createElement('div');
                        spacing.className = 'empty';
                        arenaStream.appendChild(spacing);
                        printNormal();
                        return;
                    }

                    if (!inThinkTag && currentContainer === arenaStream) {
                        // Create code pre once
                        let pre = arenaStream.querySelector('.main-stream-code');
                        if (!pre) {
                            pre = document.createElement('pre');
                            pre.className = 'code-pre main-stream-code';
                            pre.innerHTML = '<code></code>';
                            arenaStream.appendChild(pre);
                        }
                        pre.querySelector('code').textContent += char;
                    } else {
                        currentContainer.innerHTML += char;
                    }

                    charIdx++;
                    arenaStream.scrollTop = arenaStream.scrollHeight;
                    setTimeout(printNormal, inThinkTag ? 2 : 5);
                };
                printNormal();
            };

            const concludeDebateLogs = () => {
                const logs = [
                    { text: '\n[STREAM] Llama-3.1-8B (Coder) peer-review process: OK.', type: 'success-msg' },
                    { text: '[STREAM] Mistral-7B (Auditor) compilation audit: SECURE.', type: 'success-msg' },
                    { text: '[ARENA SUCCESS] Multi-agent consensus debate completed. Switch tabs above to view individual logs.', type: 'highlight' }
                ];
                
                let idx = 0;
                const printPostLogs = () => {
                    if (idx >= logs.length) {
                        return;
                    }
                    const div = document.createElement('div');
                    div.className = `terminal-line ${logs[idx].type}`;
                    div.textContent = logs[idx].text;
                    arenaStream.appendChild(div);
                    idx++;
                    arenaStream.scrollTop = arenaStream.scrollHeight;
                    setTimeout(printPostLogs, 300);
                };
                printPostLogs();
            };
        });
    }


    // ==========================================
    // 4. HARDWARE & WATCHDOG SIMULATION
    // ==========================================
    const vramVal = document.getElementById('vram-val');
    const vramBar = document.getElementById('vram-bar');
    const ramVal = document.getElementById('ram-val');
    const ramBar = document.getElementById('ram-bar');
    const tempVal = document.getElementById('temp-val');
    const tempBar = document.getElementById('temp-bar');
    
    const watchdogLogScreen = document.getElementById('watchdog-log-screen');
    const heavyModelBtn = document.getElementById('heavy-model-btn');
    const optimizeKvBtn = document.getElementById('optimize-kv-btn');
    const resetHardwareBtn = document.getElementById('reset-hardware-btn');
    const hardwareAlert = document.getElementById('hardware-alert');
    const hardwareAlertText = document.getElementById('hardware-alert-text');

    const addWatchdogLog = (msg) => {
        if (watchdogLogScreen) {
            const line = document.createElement('div');
            line.className = 'log-line';
            line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
            watchdogLogScreen.appendChild(line);
            watchdogLogScreen.scrollTop = watchdogLogScreen.scrollHeight;
        }
    };

    if (heavyModelBtn) {
        heavyModelBtn.addEventListener('click', () => {
            // Simular sobrecarga
            vramVal.textContent = '11.3 GB / 12 GB';
            vramBar.style.width = '94%';
            vramBar.className = 'progress-bar red';
            
            ramVal.textContent = '28.4 GB / 32 GB';
            ramBar.style.width = '88%';
            ramBar.className = 'progress-bar orange';

            tempVal.textContent = '84°C';
            tempBar.style.width = '84%';
            tempBar.className = 'progress-bar red';

            addWatchdogLog('WARNING: VRAM consumption exceeded critical threshold (94.1% > 85.0%).');
            addWatchdogLog('WATCHDOG ACTION: Allocating lock state: LOCKED.');
            addWatchdogLog('WATCHDOG ACTION: Ollama API requests enqueued to prevent OOM crash.');

            hardwareAlert.className = 'alert-box alarm';
            hardwareAlertText.innerHTML = '<strong>ALERTA CRÍTICA:</strong> VRAM saturada. Watchdog bloqueando peticiones. Activa <strong>Turbo KV</strong>.';
            
            heavyModelBtn.disabled = true;
            optimizeKvBtn.disabled = false;
        });

        optimizeKvBtn.addEventListener('click', () => {
            // Simular optimización Turbo KV
            vramVal.textContent = '4.8 GB / 12 GB';
            vramBar.style.width = '40%';
            vramBar.className = 'progress-bar purple';

            ramVal.textContent = '18.1 GB / 32 GB';
            ramBar.style.width = '56%';
            ramBar.className = 'progress-bar blue';

            tempVal.textContent = '62°C';
            tempBar.style.width = '62%';
            tempBar.className = 'progress-bar orange';

            addWatchdogLog('USER INPUT: Turbo KV command received.');
            addWatchdogLog('ENGINE: Injecting environment OLLAMA_KV_CACHE_TYPE=q4_0.');
            addWatchdogLog('ENGINE: Injecting environment OLLAMA_FLASH_ATTENTION=1.');
            addWatchdogLog('OLLAMA: Compressing context cache keys 4x... Done.');
            addWatchdogLog('WATCHDOG SUCCESS: GPU memory cleared by 6.5 GB. Lock status: UNLOCKED.');

            hardwareAlert.className = 'alert-box';
            hardwareAlertText.innerHTML = '<strong>SISTEMA OPTIMIZADO:</strong> Turbo KV activo. Cache comprimido 4x. Inferencia local veloz.';
            
            optimizeKvBtn.disabled = true;
        });

        resetHardwareBtn.addEventListener('click', () => {
            // Restablecer valores estándar
            vramVal.textContent = '4.2 GB / 12 GB';
            vramBar.style.width = '35%';
            vramBar.className = 'progress-bar purple';

            ramVal.textContent = '14.1 GB / 32 GB';
            ramBar.style.width = '44%';
            ramBar.className = 'progress-bar blue';

            tempVal.textContent = '58°C';
            tempBar.style.width = '58%';
            tempBar.className = 'progress-bar orange';

            if (watchdogLogScreen) {
                watchdogLogScreen.innerHTML = '';
            }
            addWatchdogLog('SYSTEM: Hardware state telemetry restored to baseline.');

            hardwareAlert.className = 'alert-box';
            hardwareAlertText.innerHTML = 'El sistema opera en rangos normales de temperatura y memoria.';

            heavyModelBtn.disabled = false;
            optimizeKvBtn.disabled = true;
        });
    }


    // ==========================================
    // 5. HITL SECURITY APPROVAL SIMULATOR
    // ==========================================
    const hitlCmd = document.getElementById('hitl-command');
    const hitlRationale = document.getElementById('hitl-rationale');
    const hitlTimer = document.getElementById('hitl-timer');
    const hitlRejectBtn = document.getElementById('hitl-reject-btn');
    const hitlApproveBtn = document.getElementById('hitl-approve-btn');
    const hitlResultLog = document.getElementById('hitl-result-log');

    const hitlGitBtn = document.getElementById('btn-hitl-git');
    const hitlDeleteBtn = document.getElementById('btn-hitl-delete');
    const hitlWriteBtn = document.getElementById('btn-hitl-write');

    let hitlCountdownVal = 120;
    let hitlInterval = null;

    const startHitlTimer = () => {
        if (hitlInterval) clearInterval(hitlInterval);
        hitlCountdownVal = 120;
        hitlTimer.textContent = `${hitlCountdownVal}s`;
        
        hitlInterval = setInterval(() => {
            hitlCountdownVal--;
            hitlTimer.textContent = `${hitlCountdownVal}s`;
            
            if (hitlCountdownVal <= 0) {
                clearInterval(hitlInterval);
                hitlResultLog.className = 'hitl-result-status error-msg';
                hitlResultLog.textContent = '[AUTO-RECHAZADO] Solicitud caducada tras 120s de inactividad humana.';
            }
        }, 1000);
    };
    startHitlTimer();

    const hitlToolsData = {
        git: {
            cmd: 'git push origin main --force',
            rationale: 'He corregido el bug en la lógica de las cookies de sesión local. Necesito forzar el empuje a la rama principal de producción en GitHub para aplicar los cambios de inmediato.',
            success: '[APROBADO] Ejecutando shell_exec ("git push origin main --force")... Upload success. Hash match [78ae4c].',
            fail: '[RECHAZADO] Comando denegado por el usuario. Bloqueando git socket. Worker liberado.'
        },
        delete: {
            cmd: 'rm -f _cache.sqlite',
            rationale: 'El monitor de auditoría ha detectado logs corruptos de la base de datos sqlite. Propongo borrar el archivo de caché completo para recrear el esquema relacional limpio.',
            success: '[APROBADO] Ejecutando file_delete ("_cache.sqlite")... File unlinked. Recreating clean database schema... Done.',
            fail: '[RECHAZADO] Eliminación cancelada. El archivo _cache.sqlite conserva sus descriptores intactos.'
        },
        write: {
            cmd: 'cat <<EOF > bridge_server.py\n# Core overwrite payload\n...',
            rationale: 'He optimizado los manejadores de ruta HTTP en bridge_server.py para soportar hilos ilimitados. Deseo sobrescribir por completo el archivo operacional principal.',
            success: '[APROBADO] Ejecutando file_write ("bridge_server.py")... Bytes written [15,587]. Reloading local server... OK.',
            fail: '[RECHAZADO] Escritura prohibida en bridge_server.py. Integridad del archivo del sistema preservada.'
        }
    };

    let activeHitlTool = 'git';

    const switchHitlTool = (toolKey) => {
        activeHitlTool = toolKey;
        const data = hitlToolsData[toolKey];
        
        hitlCmd.textContent = data.cmd;
        hitlRationale.textContent = data.rationale;
        
        hitlResultLog.className = 'hitl-result-status';
        hitlResultLog.textContent = 'Esperando interacción del programador...';
        
        startHitlTimer();
    };

    if (hitlRejectBtn) {
        hitlRejectBtn.addEventListener('click', () => {
            clearInterval(hitlInterval);
            hitlResultLog.className = 'hitl-result-status error-msg';
            hitlResultLog.textContent = hitlToolsData[activeHitlTool].fail;
        });

        hitlApproveBtn.addEventListener('click', () => {
            clearInterval(hitlInterval);
            hitlResultLog.className = 'hitl-result-status success-msg';
            hitlResultLog.textContent = hitlToolsData[activeHitlTool].success;
        });

        hitlGitBtn.addEventListener('click', () => {
            document.querySelectorAll('.tool-sel-btn').forEach(b => b.classList.remove('active'));
            hitlGitBtn.classList.add('active');
            switchHitlTool('git');
        });

        hitlDeleteBtn.addEventListener('click', () => {
            document.querySelectorAll('.tool-sel-btn').forEach(b => b.classList.remove('active'));
            hitlDeleteBtn.classList.add('active');
            switchHitlTool('delete');
        });

        hitlWriteBtn.addEventListener('click', () => {
            document.querySelectorAll('.tool-sel-btn').forEach(b => b.classList.remove('active'));
            hitlWriteBtn.classList.add('active');
            switchHitlTool('write');
        });
    }


    // ==========================================
    // 6. AUTONOMOUS MONETIZATION CALCULATOR
    // ==========================================
    const rangeVideos = document.getElementById('range-videos');
    const rangeLanguages = document.getElementById('range-languages');
    const rangeChannels = document.getElementById('range-channels');

    const valVideos = document.getElementById('val-videos');
    const valLanguages = document.getElementById('val-languages');
    const valChannels = document.getElementById('val-channels');

    const mPubVideos = document.getElementById('m-pub-videos');
    const mSocialAssets = document.getElementById('m-social-assets');
    const mViews = document.getElementById('m-views');
    const mRevenue = document.getElementById('m-revenue');

    const channelNames = [
        "TikTok",
        "TikTok + YouTube Shorts",
        "TikTok + YouTube + Instagram Reels",
        "TikTok + YouTube + Instagram + Twitter"
    ];

    const calculateMonetizationProjections = () => {
        const v = parseInt(rangeVideos.value);
        const l = parseInt(rangeLanguages.value);
        const c = parseInt(rangeChannels.value);

        // Videos published / year = videos/day * 365 * languages
        const totalVideosYear = v * 365 * l;
        
        // Social assets = videos published * 2 (Threads, Linkedin, Insta carousels)
        const socialAssets = totalVideosYear * 2;
        
        // Estimated views = totalVideosYear * channels * average views per video (conservatively 2,000 views)
        const estViews = totalVideosYear * c * 2000;
        
        // Revenue CPA = Views * (1.2% CTR) * (Average Conversion payout of $2.50 USD) / 1000 views = views * 0.00003
        // Simplified: views * $0.002 CPM/CPA conversion rate
        const estRevenue = estViews * 0.002;

        // Animate counter values
        animateCounter(mPubVideos, totalVideosYear);
        animateCounter(mSocialAssets, socialAssets);
        
        // Format view counter
        if (estViews >= 1000000) {
            mViews.textContent = `${(estViews / 1000000).toFixed(1)}M`;
        } else {
            mViews.textContent = estViews.toLocaleString();
        }

        // Format revenue
        mRevenue.textContent = `$${Math.round(estRevenue).toLocaleString()} USD`;
    };

    const animateCounter = (element, targetValue) => {
        let currentValue = parseInt(element.textContent.replace(/,/g, '')) || 0;
        const duration = 300; // ms
        const steps = 15;
        const increment = Math.ceil((targetValue - currentValue) / steps);
        let step = 0;

        const timer = setInterval(() => {
            currentValue += increment;
            step++;
            
            if (step >= steps || currentValue === targetValue) {
                clearInterval(timer);
                element.textContent = targetValue.toLocaleString();
            } else {
                element.textContent = currentValue.toLocaleString();
            }
        }, duration / steps);
    };

    if (rangeVideos) {
        // Event listeners for range inputs
        rangeVideos.addEventListener('input', () => {
            valVideos.textContent = rangeVideos.value;
            calculateMonetizationProjections();
        });

        rangeLanguages.addEventListener('input', () => {
            valLanguages.textContent = rangeLanguages.value;
            calculateMonetizationProjections();
        });

        rangeChannels.addEventListener('input', () => {
            valChannels.textContent = `${rangeChannels.value} (${channelNames[rangeChannels.value - 1]})`;
            calculateMonetizationProjections();
        });

        // Init calculations
        calculateMonetizationProjections();
    }


    // ==========================================
    // 7. UTILS & COPY CODE
    // ==========================================
    const copyYamlBtn = document.getElementById('copy-yaml-btn');
    if (copyYamlBtn) {
        copyYamlBtn.addEventListener('click', () => {
            const yamlText = `server:
  port: 7860
  host: "127.0.0.1"

agent_routing:
  auditor:
    provider: ollama
    model: "deepseek-r1:8b"
  planner:
    provider: lm_studio
    model: "llama-3.1-8b"

watchdog:
  vram_threshold_pct: 85.0
  turbo_kv_enabled: true`;

            navigator.clipboard.writeText(yamlText).then(() => {
                copyYamlBtn.textContent = '¡Copiado!';
                copyYamlBtn.style.borderColor = 'var(--accent-green)';
                copyYamlBtn.style.color = 'var(--accent-green)';
                
                setTimeout(() => {
                    copyYamlBtn.textContent = 'Copiar';
                    copyYamlBtn.style.borderColor = 'rgba(255, 255, 255, 0.15)';
                    copyYamlBtn.style.color = 'var(--text-secondary)';
                }, 2000);
            });
        });
    }

    // ==========================================
    // 8. MOBILE HAMBURGER NAVIGATION DRAWER
    // ==========================================
    const hamburgerToggle = document.getElementById('hamburger-toggle');
    const mobileNav = document.getElementById('mobile-nav');
    const mobileLinks = document.querySelectorAll('.mobile-nav-link');

    if (hamburgerToggle && mobileNav) {
        const toggleMenu = () => {
            const isOpened = hamburgerToggle.classList.contains('active');
            if (isOpened) {
                hamburgerToggle.classList.remove('active');
                mobileNav.classList.remove('active');
                hamburgerToggle.setAttribute('aria-expanded', 'false');
                mobileNav.setAttribute('aria-hidden', 'true');
            } else {
                hamburgerToggle.classList.add('active');
                mobileNav.classList.add('active');
                hamburgerToggle.setAttribute('aria-expanded', 'true');
                mobileNav.setAttribute('aria-hidden', 'false');
            }
        };

        hamburgerToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleMenu();
        });

        // Close menu when clicking a link
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                hamburgerToggle.classList.remove('active');
                mobileNav.classList.remove('active');
                hamburgerToggle.setAttribute('aria-expanded', 'false');
                mobileNav.setAttribute('aria-hidden', 'true');
            });
        });

        // Close menu when clicking outside of the drawer
        document.addEventListener('click', (e) => {
            const isMenuOpen = mobileNav.classList.contains('active');
            if (isMenuOpen && !mobileNav.contains(e.target) && e.target !== hamburgerToggle) {
                hamburgerToggle.classList.remove('active');
                mobileNav.classList.remove('active');
                hamburgerToggle.setAttribute('aria-expanded', 'false');
                mobileNav.setAttribute('aria-hidden', 'true');
            }
        });
    }

    // ==========================================
    // 9. CYBERPUNK SCROLL PROGRESS INDICATOR & BACK TO TOP
    // ==========================================
    const scrollTopBtn = document.getElementById('scroll-top-btn');
    const progressCircle = document.querySelector('.progress-ring-circle');

    if (scrollTopBtn && progressCircle) {
        const radius = progressCircle.r.baseVal.value;
        const circumference = radius * 2 * Math.PI;

        // Init circle dasharray and offset
        progressCircle.style.strokeDasharray = `${circumference} ${circumference}`;
        progressCircle.style.strokeDashoffset = circumference;

        const updateScrollProgress = () => {
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            
            // Toggle visibility of button
            if (scrollTop > 300) {
                scrollTopBtn.classList.add('visible');
            } else {
                scrollTopBtn.classList.remove('visible');
            }

            // Calculate percentage
            if (docHeight > 0) {
                const scrollPercent = scrollTop / docHeight;
                const offset = circumference - (scrollPercent * circumference);
                progressCircle.style.strokeDashoffset = offset;
            }
        };

        // Click handler to smooth scroll back to top
        scrollTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });

        window.addEventListener('scroll', updateScrollProgress);
        // Run initial check in case page starts scrolled
        updateScrollProgress();
    }

    // ==========================================
    // 10. PREMIUM 3D TILT EFFECT FOR FEATURE CARDS
    // ==========================================
    const cards = document.querySelectorAll('.feature-card, .use-case-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left; // x position within the element
            const y = e.clientY - rect.top;  // y position within the element
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Calculate tilt angle (max 7.5 degrees to avoid extreme warping)
            const rotateX = ((centerY - y) / centerY) * 7.5;
            const rotateY = ((x - centerX) / centerX) * 7.5;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
        });
        
        card.addEventListener('mouseleave', () => {
            // Smoothly reset transformations on cursor exit
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)`;
        });
    });

});
