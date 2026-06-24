import { useState, useEffect, useRef } from 'react';
import { Camera, Activity, Sliders, RefreshCw, Zap } from 'lucide-react';

const PRESETS = [
    // Humanos / Estilos
    { key: "cyberpunk_commander", label: "Comandante Cyberpunk" },
    { key: "mujer",               label: "Mujer Elegante" },
    { key: "anime",               label: "Personaje Anime" },
    { key: "watercolor",          label: "Acuarela" },
    { key: "claymation",          label: "Claymation" },
    { key: "samurai",             label: "Guerrero Samurai" },
    { key: "pirate_captain",      label: "Capitán Pirata" },
    // Fantasía / Magia
    { key: "zombie",              label: "Zombie Apocalipsis" },
    { key: "dark_mage",           label: "Brujo Oscuro" },
    { key: "dragon",              label: "Dragon Humanoide" },
    { key: "medieval_king",       label: "Rey Medieval" },
    // Sci-Fi / Robots
    { key: "robot_mecha",         label: "Cyborg Mecha" },
    { key: "space_alien",         label: "Alien Espacial" },
    { key: "underwater",          label: "Explorador Submarino" },
    // Animales / Furry
    { key: "bear",                label: "Oso Pardo" },
    { key: "dog",                 label: "Perro Animado" },
    { key: "cat_person",          label: "Persona Gato" },
    { key: "horse",               label: "Centauro" },
    { key: "wolf",                label: "Hombre Lobo" },
    { key: "fox",                 label: "Zorro Kitsune" },
    // Criaturas Extremas
    { key: "amorphous",           label: "Figura Amorfa" },
    { key: "demon",               label: "Demonio Oscuro" },
    { key: "slime",               label: "Criatura Slime" },
    { key: "skeleton",            label: "Esqueleto Viviente" },
];

export function V2VStudio() {
    const wsRef = useRef<WebSocket | null>(null);

    // Estado local — fuente de verdad independiente del polling
    const [isActive, setIsActive] = useState(false);
    const [fps, setFps] = useState(0);
    const [bgReady, setBgReady] = useState(false);

    // Controles de configuración
    const [preset, setPreset] = useState("cyberpunk_commander");
    const [customPrompt, setCustomPrompt] = useState("");
    const [negativePrompt, setNegativePrompt] = useState(
        "low quality, blurry, watermark, text, deformed, extra limbs"
    );
    const [strength, setStrength] = useState(0.85);

    // Estado del proceso externo
    const [status, setStatus] = useState<any>(null);
    const [wsConnected, setWsConnected] = useState(false);

    // ── Polling del proceso externo (cada 5s) ──────────────────────────────
    useEffect(() => {
        const fetchStatus = () => {
            fetch('/v1/v2v/status')
                .then(r => r.json())
                .then(data => setStatus(data))
                .catch(() => {});
        };
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const [reconnectTrigger, setReconnectTrigger] = useState(0);

    // ── WebSocket connection ───────────────────────────────────────────────
    useEffect(() => {
        if (status?.online && !wsRef.current) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const socket = new WebSocket(`${protocol}//${window.location.hostname}:7863`);
            socket.onopen = () => {
                setWsConnected(true);
                socket.send(JSON.stringify({ command: "get_status" }));
            };
            socket.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === "status") {
                        // Sólo actualizar métricas — NO actualizar isActive desde el servidor
                        // para evitar el race condition del toggle
                        setFps(msg.data.fps ?? 0);
                        setBgReady(msg.data.bg_ready ?? false);
                    }
                } catch {}
            };
            socket.onclose = () => {
                setWsConnected(false);
                wsRef.current = null;
                // Intentar reconectar tras un delay
                setTimeout(() => {
                    setReconnectTrigger(prev => prev + 1);
                }, 3000);
            };
            wsRef.current = socket;
        } else if (!status?.online && wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
            setWsConnected(false);
        }
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
        };
    }, [status?.online, reconnectTrigger]);

    // ── Polling de métricas en vivo (cada 1s) ────────────────────────────
    useEffect(() => {
        const interval = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ command: "get_status" }));
            }
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    // ── Acciones ──────────────────────────────────────────────────────────
    const sendWs = (payload: object) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(payload));
        }
    };

    const toggleActive = () => {
        const next = !isActive;
        setIsActive(next); // actualización optimista en React
        sendWs({ command: "toggle_active", active: next });
    };

    const generateBase = () => {
        sendWs({ command: "generate_base" });
    };

    const applyStyle = () => {
        sendWs({
            command: "set_prompt",
            preset,
            prompt: customPrompt.trim(),   // string vacío si no hay prompt
            negative_prompt: negativePrompt,
            strength,
        });
        setBgReady(false);
    };

    const refreshBg = () => {
        sendWs({ command: "refresh_bg" });
        setBgReady(false);
    };

    const startEngine = async () => {
        try {
            await fetch('/v1/v2v/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: 'V2V Engine' })
            });
        } catch {}
    };

    const stopEngine = async () => {
        try {
            await fetch('/v1/v2v/stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: 'V2V Engine' })
            });
        } catch {}
    };

    return (
        <div className="p-6 space-y-6 max-h-full overflow-y-auto">

            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        <Camera className="h-6 w-6 text-[#c69c6d]" />
                        V2V Studio — Be Anything
                    </h2>
                    <p className="text-sm text-zinc-400">
                        Motor de transformación corporal total · DirectML (Radeon 780M)
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    {status?.process_running ? (
                        <button
                            id="v2v-stop-engine"
                            onClick={stopEngine}
                            className="px-3 py-1 rounded-full text-xs font-bold bg-red-500/20 text-red-400 hover:bg-red-500/40 transition-colors"
                        >
                            DETENER MOTOR
                        </button>
                    ) : (
                        <button
                            id="v2v-start-engine"
                            onClick={startEngine}
                            className="px-3 py-1 rounded-full text-xs font-bold bg-[#c69c6d]/20 text-[#c69c6d] hover:bg-[#c69c6d]/40 transition-colors"
                        >
                            INICIAR MOTOR
                        </button>
                    )}
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        wsConnected ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                    }`}>
                        {wsConnected ? "WS ONLINE" : "WS OFFLINE"}
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Panel principal */}
                <div className="lg:col-span-2 bg-[#1c1c1e] border border-zinc-800 rounded-xl p-5 shadow-lg space-y-5">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <Activity className="h-5 w-5 text-blue-400" />
                        Control de Transformación
                    </h3>

                    {/* Toggle AI */}
                    <div className="flex items-center justify-between p-4 bg-black/40 rounded-lg border border-zinc-800">
                        <div className="space-y-1">
                            <h3 className="font-medium text-white">Transformación AI</h3>
                            <p className="text-sm text-zinc-400">
                                Activa para ver el avatar en la cámara virtual.
                            </p>
                        </div>
                        <div className="flex items-center gap-4">
                            <span className="font-mono text-xl text-[#c69c6d]">
                                {fps.toFixed(1)} FPS
                            </span>
                            <button
                                id="v2v-toggle-active"
                                onClick={toggleActive}
                                disabled={!wsConnected}
                                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-40
                                    ${isActive ? 'bg-[#c69c6d]' : 'bg-zinc-700'}`}
                            >
                                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                                    ${isActive ? 'translate-x-6' : 'translate-x-1'}`}
                                />
                            </button>
                        </div>
                    </div>

                    <div className="flex justify-end">
                        <button
                            id="v2v-generate-base"
                            onClick={generateBase}
                            disabled={!wsConnected || !isActive}
                            className="px-4 py-2 bg-gradient-to-r from-[#c69c6d] to-[#e6b981] text-black font-bold rounded-md hover:opacity-90 transition-opacity disabled:opacity-40"
                        >
                            <Camera className="h-4 w-4 inline mr-2" />
                            Generar Avatar Base (SD-Turbo)
                        </button>
                    </div>

                    {/* Preset selector */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-zinc-300">
                            ¿Qué quieres ser?
                        </label>
                        <select
                            id="v2v-preset-select"
                            className="w-full bg-[#111] border border-zinc-800 text-white p-2.5 rounded-md
                                       focus:border-[#c69c6d] focus:ring-1 focus:ring-[#c69c6d] outline-none transition-all"
                            value={preset}
                            onChange={e => setPreset(e.target.value)}
                        >
                            {PRESETS.map(p => (
                                <option key={p.key} value={p.key}>{p.label}</option>
                            ))}
                        </select>
                    </div>

                    {/* Prompt personalizado */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-zinc-300">
                            Prompt Personalizado (opcional)
                        </label>
                        <textarea
                            id="v2v-custom-prompt"
                            value={customPrompt}
                            onChange={e => setCustomPrompt(e.target.value)}
                            className="w-full bg-[#111] border border-zinc-800 text-white p-2.5 rounded-md
                                       focus:border-[#c69c6d] outline-none text-sm h-16 resize-none"
                            placeholder="Ej: with blue glowing eyes, wearing a crown, on fire..."
                        />
                        <p className="text-xs text-zinc-500">
                            Se combina con el preset seleccionado. Deja vacío para usar sólo el preset.
                        </p>
                    </div>

                    {/* Negative prompt */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-zinc-300">Negative Prompt</label>
                        <textarea
                            id="v2v-negative-prompt"
                            value={negativePrompt}
                            onChange={e => setNegativePrompt(e.target.value)}
                            className="w-full bg-[#111] border border-zinc-800 text-white p-2.5 rounded-md
                                       focus:border-red-900 outline-none text-sm h-12 resize-none"
                        />
                    </div>

                    {/* Strength */}
                    <div className="space-y-2">
                        <div className="flex justify-between items-center">
                            <label className="text-sm font-medium text-zinc-300">
                                Intensidad de Transformación
                            </label>
                            <span className="text-xs text-[#c69c6d] font-mono">
                                {strength.toFixed(2)}
                            </span>
                        </div>
                        <input
                            id="v2v-strength-slider"
                            type="range" min="0.70" max="0.99" step="0.01"
                            value={strength}
                            onChange={e => setStrength(parseFloat(e.target.value))}
                            className="w-full accent-[#c69c6d]"
                        />
                        <div className="flex justify-between text-xs text-zinc-500">
                            <span>0.70 — Conserva tu cuerpo</span>
                            <span>0.99 — Transformación total</span>
                        </div>
                    </div>

                    {/* Acciones */}
                    <div className="flex gap-3">
                        <button
                            id="v2v-apply-style"
                            onClick={applyStyle}
                            disabled={!wsConnected}
                            className="flex-1 flex items-center justify-center gap-2 bg-[#c69c6d] hover:bg-[#b8895c]
                                       text-black font-bold py-2.5 rounded-md transition-colors disabled:opacity-40"
                        >
                            <Zap className="h-4 w-4" />
                            Aplicar Transformación
                        </button>
                        <button
                            id="v2v-refresh-bg"
                            onClick={refreshBg}
                            disabled={!wsConnected}
                            title="Regenerar fondo"
                            className="px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 rounded-md transition-colors
                                       disabled:opacity-40 text-white"
                        >
                            <RefreshCw className="h-4 w-4" />
                        </button>
                    </div>

                    {/* Status bar */}
                    <div className={`p-2 rounded-md text-xs font-mono text-center
                        ${bgReady ? 'bg-green-500/10 text-green-400' : 'bg-orange-500/10 text-orange-400'}`}
                    >
                        {bgReady ? '✓ Avatar listo · Transformación activa' : '⟳ Generando escena...'}
                    </div>
                </div>

                {/* Panel lateral Hardware */}
                <div className="bg-[#1c1c1e] border border-zinc-800 rounded-xl p-5 shadow-lg">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
                        <Sliders className="h-5 w-5 text-purple-400" />
                        Hardware
                    </h3>
                    <div className="space-y-4">
                        <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-md">
                            <p className="text-xs text-green-400 font-semibold mb-1">MOTOR V4.0 — BE ANYTHING</p>
                            <p className="text-xs text-zinc-300 leading-relaxed">
                                VTuber Engine: SD-Turbo genera el avatar una vez,
                                LivePortrait ONNX lo anima en tiempo real con tu rostro y gestos.
                            </p>
                        </div>

                        <div className="space-y-3 pt-2">
                            {[
                                ["Motor",         "SD-Turbo + LivePortrait"],
                                ["GPU Provider",  "DirectML (AMD)"],
                                ["GPU",           "Radeon 780M (UMA)"],
                                ["Resolución",    "512 × 512"],
                                ["Animación",     "ONNX Real-time 30+ FPS"],
                                ["Arquitectura",  "Generate Once · Drive Live"],
                            ].map(([k, v]) => (
                                <div key={k} className="flex justify-between text-sm">
                                    <span className="text-zinc-400">{k}</span>
                                    <span className="text-white font-medium">{v}</span>
                                </div>
                            ))}
                        </div>

                        <div className="pt-4 border-t border-zinc-800 space-y-2">
                            <p className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Guía de Intensidad</p>
                            <p className="text-xs text-zinc-500">
                                <span className="text-white">0.70–0.80</span> — Conserva tu silueta. Cambio sutil.<br />
                                <span className="text-white">0.85–0.90</span> — Transformación clara. Recomendado.<br />
                                <span className="text-white">0.95–0.99</span> — Total. Casi irreconocible.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
