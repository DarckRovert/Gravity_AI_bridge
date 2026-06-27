import React, { useState, useEffect } from 'react';
import { Radio, MonitorPlay, Mic, MicOff, Volume2, StopCircle, RefreshCw, Wand2, Edit3, Trash2, Code, Layout as LayoutIcon, Eye, X, MessageSquare, BarChart2, Gift, Clock, Music, Target, Globe, Box, Film, Binary, Database } from 'lucide-react';
import { showToast } from './Toast';
import { BRIDGE_BASE } from '../config';

interface OBSStatus {
  connected: boolean;
  current_scene: string;
}

interface OBSScene {
  name: string;
}

interface OBSInput {
  input_name: string;
  volume_db: number;
  muted: boolean;
}

interface OBSOverlay {
  overlay_id: string;
  created_at: number;
  scene_name?: string;
  prompt?: string;
  url?: string;
  width?: number;
  height?: number;
}

const SPARK_TEMPLATES = [
  {
    name: 'Chat Cyberpunk',
    icon: MessageSquare,
    color: 'from-cyan-500/20 to-blue-600/20 border-cyan-500/50 text-cyan-400',
    description: 'Widget de chat oscuro con avatares simulados.',
    prompt: 'Widget de chat cyberpunk con glassmorphism oscuro. Bordes neón cian pulsantes. Incluye script JS que simula recibir mensajes con avatares (imágenes placeholder) y nombres de colores variados cada 2-5 segundos. Auto-scroll fluido y un pequeño destello visual en cada nuevo mensaje. Tipografía monospace consola.'
  },
  {
    name: 'Dashboard HUD',
    icon: BarChart2,
    color: 'from-purple-500/20 to-pink-600/20 border-purple-500/50 text-purple-400',
    description: 'Estadísticas sci-fi animadas.',
    prompt: 'Panel lateral de estadísticas estilo sci-fi. Muestra Viewers, Subs y Bits. Usa JS para actualizar los números dinámicamente simulando tráfico real. Incluye mini gráficos de barras animados con HTML5 Canvas y anillos circulares de progreso. Paleta de colores oscuro con acentos en violeta y verde neón.'
  },
  {
    name: 'Alerta Épica',
    icon: Gift,
    color: 'from-yellow-400/20 to-orange-500/20 border-yellow-400/50 text-yellow-400',
    description: 'Partículas 3D y explosión de confeti.',
    prompt: 'Alerta de donación que se dispara cada 10 segundos (simulado por JS). Inicia con una explosión de partículas doradas 2D usando Canvas, seguido de un texto central 3D con sombras pronunciadas que dice "NUEVA DONACIÓN" y un nombre aleatorio rotando. Efecto de entrada con zoom elástico.'
  },
  {
    name: 'BRB Synthwave',
    icon: Clock,
    color: 'from-fuchsia-500/20 to-purple-600/20 border-fuchsia-500/50 text-fuchsia-400',
    description: 'Cuenta regresiva retro 80s con fondo infinito.',
    prompt: 'Pantalla "Vuelvo Enseguida" estilo retrowave 80s. Fondo animado con un sol de neón y una cuadrícula 3D moviéndose hacia adelante infinitamente (CSS animations). Al centro, un temporizador funcional en JS contando hacia atrás desde 5 minutos. Si llega a 0, muestra "¡ESTAMOS DE VUELTA!".'
  },
  {
    name: 'Now Playing',
    icon: Music,
    color: 'from-emerald-400/20 to-teal-500/20 border-emerald-400/50 text-emerald-400',
    description: 'Vinilo giratorio y ecualizador animado.',
    prompt: 'Widget flotante de música actual. Muestra la rotación de un vinilo con una carátula simulada, barras de ecualizador de audio que saltan aleatoriamente mediante JS, y el texto de la canción desplazándose (marquee). Diseño limpio, translúcido con bordes muy finos blancos, efecto blur de fondo.'
  },
  {
    name: 'Meta Subs Hitos',
    icon: Target,
    color: 'from-rose-400/20 to-red-500/20 border-rose-400/50 text-rose-400',
    description: 'Barra interactiva que lanza confeti.',
    prompt: 'Barra de meta de subs con hitos (25%, 50%, 100%). Script JS incrementa el progreso constantemente. Al alcanzar un hito, la barra cambia de color vibrante y emite confeti CSS/Canvas localmente. El texto muestra "Meta: X/100" actualizándose fluidamente. Estilo moderno, bordes redondeados (pill-shape).'
  },
  {
    name: 'Reloj Sci-Fi',
    icon: Globe,
    color: 'from-green-400/20 to-emerald-600/20 border-green-400/50 text-green-400',
    description: 'Hora real y monitoreo CPU/RAM.',
    prompt: 'Widget HUD que muestra la hora real local (HH:MM:SS) actualizándose cada segundo con JS. Incluye un falso monitor de sistema (CPU/RAM en uso) con barras de progreso fluctuantes aleatoriamente, y un pequeño radar rotativo. Estética de interfaz de nave espacial, colores verde terminal y negro.'
  },
  {
    name: 'Cubo Núcleo Gravity',
    icon: Box,
    color: 'from-blue-500/20 to-indigo-600/20 border-blue-500/50 text-blue-400',
    description: 'Wireframe 3D interactivo.',
    prompt: 'Un cubo wireframe 3D rotando constantemente en el centro de la pantalla, renderizado usando puras matemáticas de proyección de vértices sobre HTML5 Canvas 2D (simulando un motor 3D desde cero). En su centro, un orbe brillante palpitante. Hace fetch a la API local de Gravity para ajustar su velocidad de rotación según la latencia.'
  },
  {
    name: 'Inicio Cinematográfico',
    icon: Film,
    color: 'from-orange-500/20 to-red-600/20 border-orange-500/50 text-orange-400',
    description: 'Humo fractal y temporizador.',
    prompt: 'Pantalla de inicio cinematográfica starting soon con barras cinematográficas negras. El fondo es una simulación compleja de humo o niebla volumétrica generada procedimentalmente usando Perlin Noise o algoritmos de fluidos en Canvas. Cuenta regresiva que al llegar a cero disipa el humo revelando "SISTEMA ONLINE".'
  },
  {
    name: 'Lluvia Matrix Seguridad',
    icon: Binary,
    color: 'from-green-500/20 to-lime-600/20 border-green-500/50 text-green-400',
    description: 'Lluvia digital reactiva.',
    prompt: 'Clásica lluvia digital de caracteres verdes cayendo, construida para máximo rendimiento en Canvas. Se conecta al Security Monitor local y hace que las gotas formen esporádicamente palabras reales como SECURE, FIREWALL o GRAVITY cuando detecta monitoreo activo.'
  }
];

export const OBSStudio: React.FC = () => {
  const [status, setStatus] = useState<OBSStatus>({ connected: false, current_scene: '' });
  const [scenes, setScenes] = useState<OBSScene[]>([]);
  const [inputs, setInputs] = useState<OBSInput[]>([]);
  const [streamRecord, setStreamRecord] = useState({ streaming: false, recording: false });
  const [overlays, setOverlays] = useState<OBSOverlay[]>([]);
  const [loading, setLoading] = useState(true);

  // Spark form state
  const [sparkPrompt, setSparkPrompt] = useState('');
  const [sparkWidth, setSparkWidth] = useState(800);
  const [sparkHeight, setSparkHeight] = useState(600);
  const [sparkX, setSparkX] = useState(0);
  const [sparkY, setSparkY] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [useSparkCache, setUseSparkCache] = useState(true);
  
  // Edit overlay state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editPrompt, setEditPrompt] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  // Live preview state
  const [selectedOverlay, setSelectedOverlay] = useState<OBSOverlay | null>(null);

  const fetchData = async () => {
    try {
      const [statusRes, scenesRes, inputsRes, streamRes, overlaysRes] = await Promise.all([
        fetch('/v1/obs/status').catch(() => null),
        fetch('/v1/obs/scenes').catch(() => null),
        fetch('/v1/obs/inputs').catch(() => null),
        fetch('/v1/obs/stream/status').catch(() => null),
        fetch('/v1/obs/overlays').catch(() => null)
      ]);

      if (statusRes?.ok) {
        const data = await statusRes.json();
        setStatus(data);
      }
      if (scenesRes?.ok) {
        const data = await scenesRes.json();
        setScenes(data.scenes || []);
      }
      if (inputsRes?.ok) {
        const data = await inputsRes.json();
        setInputs(data.inputs || []);
      }
      if (streamRes?.ok) {
        const data = await streamRes.json();
        setStreamRecord({ streaming: data.streaming, recording: data.recording });
      }
      if (overlaysRes?.ok) {
        const data = await overlaysRes.json();
        setOverlays(data.overlays || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Polling every 5s
    return () => clearInterval(interval);
  }, []);

  const handleSwitchScene = async (sceneName: string) => {
    try {
      const res = await fetch('/v1/obs/scene/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scene_name: sceneName })
      });
      if (res.ok) {
        setStatus(prev => ({ ...prev, current_scene: sceneName }));
      } else {
        showToast('error', 'Error al cambiar escena');
      }
    } catch (e) {
      showToast('error', 'Error de conexión');
    }
  };

  const handleToggleMute = async (inputName: string) => {
    try {
      const res = await fetch('/v1/obs/audio/mute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_name: inputName })
      });
      if (!res.ok) throw new Error('El servidor rechazó silenciar el canal');
      const data = await res.json();
      setInputs(inputs.map(i => i.input_name === inputName ? { ...i, muted: data.muted } : i));
    } catch (e: any) {
      showToast('error', `Error al mutear: ${e.message}`);
    }
  };

  const handleToggleStream = async () => {
    try {
      const res = await fetch('/v1/obs/stream/toggle', { method: 'POST' });
      if (!res.ok) throw new Error('El servidor OBS rechazó la acción de Stream');
      const data = await res.json();
      setStreamRecord(prev => ({ ...prev, streaming: data.streaming }));
      showToast('success', data.streaming ? 'Stream Iniciado' : 'Stream Detenido');
    } catch (e: any) {
      showToast('error', `Error crítico en Stream: ${e.message}`);
    }
  };

  const handleToggleRecord = async () => {
    try {
      const res = await fetch('/v1/obs/record/toggle', { method: 'POST' });
      if (!res.ok) throw new Error('El servidor OBS rechazó la acción de Grabación');
      const data = await res.json();
      setStreamRecord(prev => ({ ...prev, recording: data.recording }));
      showToast('success', data.recording ? 'Grabación Iniciada' : 'Grabación Detenida');
    } catch (e: any) {
      showToast('error', `Error crítico en Grabación: ${e.message}`);
    }
  };

  const handleGenerateOverlay = async () => {
    if (!sparkPrompt.trim() || !status.current_scene) {
      showToast('error', 'Prompt y escena activa requeridos');
      return;
    }
    setIsGenerating(true);
    try {
      const res = await fetch('/v1/obs/spark/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: sparkPrompt,
          scene_name: status.current_scene,
          width: sparkWidth,
          height: sparkHeight,
          x: sparkX,
          y: sparkY,
          use_cache: useSparkCache
        })
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        showToast('success', `Overlay generado: ${data.overlay_id}`);
        setSparkPrompt('');
        
        // Auto-select for live preview
        const newOverlay: OBSOverlay = {
          overlay_id: data.overlay_id,
          created_at: Date.now() / 1000,
          scene_name: data.scene_name,
          prompt: data.prompt,
          url: data.preview_url,
          width: sparkWidth,
          height: sparkHeight
        };
        setSelectedOverlay(newOverlay);
        
        fetchData();
      } else {
        showToast('error', data.error || 'Error generando overlay');
      }
    } catch (e) {
      showToast('error', 'Error conectando con el Bridge');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleEditOverlay = async (id: string) => {
    if (!editPrompt.trim()) return;
    setIsEditing(true);
    try {
      const res = await fetch('/v1/obs/spark/edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          overlay_id: id,
          prompt: editPrompt
        })
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        showToast('success', 'Overlay editado con éxito');
        setEditingId(null);
        setEditPrompt('');
      } else {
        showToast('error', data.error || 'Error editando overlay');
      }
    } catch (e) {
      showToast('error', 'Error de conexión');
    } finally {
      setIsEditing(false);
    }
  };

  const handleRemoveOverlay = async (id: string) => {
    try {
      const res = await fetch('/v1/obs/spark/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ overlay_id: id })
      });
      if (!res.ok) throw new Error('Error purgando overlay del sistema');
      showToast('success', 'Overlay purgado permanentemente de OBS');
      setOverlays(overlays.filter(o => o.overlay_id !== id));
      if (selectedOverlay?.overlay_id === id) {
        setSelectedOverlay(null);
      }
    } catch (e: any) {
      showToast('error', `Fallo al eliminar: ${e.message}`);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full"><RefreshCw className="animate-spin text-accent-primary" /></div>;
  }

  return (
    <div className="h-full flex flex-col p-6 overflow-y-auto space-y-6">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-text-primary flex items-center gap-3">
            <Radio className="text-accent-primary" size={28} />
            OBS Studio Control
          </h1>
          <p className="text-sm text-text-muted mt-1">Gestión remota de producción en vivo</p>
        </div>
        <div className={`px-4 py-1.5 rounded-full text-xs font-bold flex items-center gap-2 ${status.connected ? 'bg-status-success/20 text-status-success border border-status-success/30' : 'bg-status-error/20 text-status-error border border-status-error/30'}`}>
          <div className={`w-2 h-2 rounded-full ${status.connected ? 'bg-status-success animate-pulse' : 'bg-status-error'}`}></div>
          {status.connected ? 'CONECTADO' : 'DESCONECTADO'}
        </div>
      </div>

      {!status.connected ? (
        <div className="glass-card p-6 border border-status-warning/30 rounded-xl bg-status-warning/5">
          <h2 className="text-status-warning font-bold flex items-center gap-2"><Radio size={18} /> OBS no está conectado</h2>
          <p className="text-sm text-text-muted mt-2">
            Habilita el WebSocket en OBS (Herramientas &gt; Ajustes del servidor WebSocket) en el puerto 4455 con la contraseña configurada en <code className="bg-bg px-1 rounded">config.yaml</code>. El sistema reintentará conectar automáticamente.
          </p>
        </div>
      ) : (
        <div className={`grid grid-cols-1 ${selectedOverlay ? 'xl:grid-cols-3' : 'lg:grid-cols-2'} gap-6 transition-all duration-300`}>
          
          {/* Controls Panel */}
          <div className="space-y-6">
            <div className="glass-card p-5 border border-border-subtle rounded-xl">
              <h2 className="text-sm font-bold uppercase text-text-muted mb-4 flex items-center gap-2"><LayoutIcon size={16}/> Emisión y Grabación</h2>
              <div className="flex gap-4">
                <button 
                  onClick={handleToggleStream}
                  className={`flex-1 py-3 px-4 rounded-lg font-bold flex items-center justify-center gap-2 transition-all ${streamRecord.streaming ? 'bg-status-error text-white hover:bg-red-600' : 'bg-bg border border-border-subtle text-text-primary hover:border-accent-primary'}`}
                >
                  <Radio size={18} />
                  {streamRecord.streaming ? 'Detener Stream' : 'Iniciar Stream'}
                </button>
                <button 
                  onClick={handleToggleRecord}
                  className={`flex-1 py-3 px-4 rounded-lg font-bold flex items-center justify-center gap-2 transition-all ${streamRecord.recording ? 'bg-status-warning text-black hover:bg-yellow-500' : 'bg-bg border border-border-subtle text-text-primary hover:border-accent-primary'}`}
                >
                  <StopCircle size={18} />
                  {streamRecord.recording ? 'Detener Grabación' : 'Iniciar Grabación'}
                </button>
              </div>
            </div>

            <div className="glass-card p-5 border border-border-subtle rounded-xl">
              <h2 className="text-sm font-bold uppercase text-text-muted mb-4 flex items-center gap-2"><MonitorPlay size={16}/> Escenas</h2>
              <div className="flex flex-wrap gap-2">
                {scenes.map(s => (
                  <button
                    key={s.name}
                    onClick={() => handleSwitchScene(s.name)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${status.current_scene === s.name ? 'bg-accent-primary text-black' : 'bg-bg border border-border-subtle text-text-muted hover:text-text-primary'}`}
                  >
                    {s.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="glass-card p-5 border border-border-subtle rounded-xl">
              <h2 className="text-sm font-bold uppercase text-text-muted mb-4 flex items-center gap-2"><Volume2 size={16}/> Mezclador de Audio</h2>
              <div className="space-y-3">
                {inputs.map(i => (
                  <div key={i.input_name} className="flex items-center justify-between p-3 bg-bg border border-border-subtle rounded-lg">
                    <span className="font-medium text-sm text-text-primary">{i.input_name}</span>
                    <button 
                      onClick={() => handleToggleMute(i.input_name)}
                      className={`p-2 rounded-md transition-colors ${i.muted ? 'bg-status-error/20 text-status-error' : 'bg-status-success/20 text-status-success'}`}
                    >
                      {i.muted ? <MicOff size={16} /> : <Mic size={16} />}
                    </button>
                  </div>
                ))}
                {inputs.length === 0 && <span className="text-xs text-text-muted">No se detectaron fuentes de audio activas.</span>}
              </div>
            </div>
          </div>

          {/* Spark Panel */}
          <div className="space-y-6 flex flex-col">
            <div className="glass-card p-5 border border-accent-primary/50 shadow-[0_0_15px_rgba(var(--color-accent-primary),0.1)] rounded-xl flex-1 flex flex-col">
              <h2 className="text-lg font-black tracking-tight text-accent-primary mb-1 flex items-center gap-2"><Wand2 size={20}/> Gravity Spark Engine</h2>
              <p className="text-xs text-text-muted mb-6">Generador de overlays dinámicos (Browser Sources) con Inteligencia Artificial. Escribe lo que necesitas, el LLM lo programará en HTML/JS y se inyectará automáticamente en OBS.</p>
              
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-xs font-bold text-text-muted mb-1">PROMPT DEL OVERLAY</label>
                  <textarea 
                    value={sparkPrompt}
                    onChange={e => setSparkPrompt(e.target.value)}
                    placeholder="Ej. Un widget de chat cyberpunk con fondo oscuro transparente y borde neon azul..."
                    className="w-full bg-bg border border-border-subtle rounded-lg p-3 text-sm focus:border-accent-primary focus:outline-none min-h-[100px] resize-none mb-2"
                  />
                </div>

                <div className="mb-6">
                  <label className="block text-xs font-bold text-text-muted mb-3 flex items-center justify-between">
                    <span>PLANTILLAS RÁPIDAS CREATIVAS</span>
                    <span className="text-[10px] font-bold bg-accent-primary/10 text-accent-primary px-2.5 py-0.5 rounded-full border border-accent-primary/20">¡Inspiración!</span>
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
                    {SPARK_TEMPLATES.map((t, i) => {
                      const Icon = t.icon;
                      return (
                        <button
                          key={i}
                          onClick={() => setSparkPrompt(t.prompt)}
                          className="text-left group relative p-3.5 rounded-xl bg-bg border border-border-subtle hover:border-accent-primary transition-all duration-300 hover:shadow-[0_0_20px_rgba(var(--color-accent-primary),0.15)] hover:-translate-y-1 overflow-hidden"
                        >
                          <div className={`absolute -top-10 -right-10 w-24 h-24 bg-gradient-to-br ${t.color.split(' ')[0]} ${t.color.split(' ')[1]} opacity-20 rounded-full blur-2xl transition-opacity duration-500 group-hover:opacity-60`}></div>
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-3 border ${t.color} bg-gradient-to-br bg-opacity-10 backdrop-blur-sm relative z-10`}>
                            <Icon size={16} className="drop-shadow-md" />
                          </div>
                          <h3 className="text-xs font-bold text-text-primary mb-1.5 group-hover:text-accent-primary transition-colors relative z-10">{t.name}</h3>
                          <p className="text-[10px] text-text-muted leading-relaxed line-clamp-2 relative z-10">{t.description}</p>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
                  <div>
                    <label className="block text-[10px] font-bold text-text-muted mb-1">ANCHO (px)</label>
                    <input type="number" value={sparkWidth} onChange={e => setSparkWidth(Number(e.target.value))} className="w-full bg-bg border border-border-subtle rounded-lg p-2 text-xs focus:border-accent-primary focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-text-muted mb-1">ALTO (px)</label>
                    <input type="number" value={sparkHeight} onChange={e => setSparkHeight(Number(e.target.value))} className="w-full bg-bg border border-border-subtle rounded-lg p-2 text-xs focus:border-accent-primary focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-text-muted mb-1">POSICIÓN X</label>
                    <input type="number" value={sparkX} onChange={e => setSparkX(Number(e.target.value))} className="w-full bg-bg border border-border-subtle rounded-lg p-2 text-xs focus:border-accent-primary focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-text-muted mb-1">POSICIÓN Y</label>
                    <input type="number" value={sparkY} onChange={e => setSparkY(Number(e.target.value))} className="w-full bg-bg border border-border-subtle rounded-lg p-2 text-xs focus:border-accent-primary focus:outline-none" />
                  </div>
                </div>

                <div className="flex items-center justify-between p-3 bg-bg border border-border-subtle rounded-lg mb-4">
                  <div className="flex items-center gap-2.5">
                    <Database size={16} className={useSparkCache ? "text-accent-primary" : "text-text-muted"} />
                    <div>
                      <span className="text-xs font-bold text-text-primary block">Caché de Plantillas Instantáneas</span>
                      <span className="text-[10px] text-text-muted block">Desactiva para forzar a la IA a crear variaciones únicas en cada clic</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setUseSparkCache(!useSparkCache)}
                    className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${useSparkCache ? "bg-accent-primary" : "bg-card"}`}
                  >
                    <span className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-black shadow ring-0 transition duration-200 ease-in-out ${useSparkCache ? "translate-x-4" : "translate-x-0"}`} />
                  </button>
                </div>

                <button 
                  onClick={handleGenerateOverlay}
                  disabled={isGenerating}
                  className="w-full py-3 rounded-lg bg-accent-primary text-black font-black flex items-center justify-center gap-2 hover:bg-accent-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isGenerating ? <RefreshCw className="animate-spin" size={18} /> : <Wand2 size={18} />}
                  {isGenerating ? 'Generando código HTML/JS...' : 'Generar e Inyectar en OBS'}
                </button>
              </div>

              <h3 className="text-xs font-bold uppercase text-text-muted mb-3 flex items-center gap-2"><Code size={14}/> Overlays Activos</h3>
              <div className="space-y-2.5 flex-1 overflow-y-auto pr-1 max-h-[300px]">
                {overlays.length === 0 ? (
                  <div className="text-center p-6 border border-dashed border-border-subtle rounded-lg text-text-muted text-xs">
                    No hay overlays generados en esta sesión.
                  </div>
                ) : overlays.map(ov => (
                  <div 
                    key={ov.overlay_id} 
                    onClick={() => setSelectedOverlay(ov)}
                    className={`bg-bg border rounded-lg p-3 cursor-pointer transition-all ${selectedOverlay?.overlay_id === ov.overlay_id ? 'border-accent-primary shadow-[0_0_10px_rgba(var(--color-accent-primary),0.05)]' : 'border-border-subtle hover:border-text-muted'}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <MonitorPlay size={14} className="text-accent-secondary" />
                        <span className="font-bold text-xs truncate max-w-[120px]">{ov.overlay_id}</span>
                        {ov.scene_name && <span className="text-[9px] bg-card px-2 py-0.5 rounded text-text-muted">{ov.scene_name}</span>}
                      </div>
                      <div className="flex items-center gap-1.5" onClick={e => e.stopPropagation()}>
                        <button onClick={() => { setEditingId(editingId === ov.overlay_id ? null : ov.overlay_id); setEditPrompt(ov.prompt || ''); }} className="p-1.5 hover:bg-card rounded text-text-muted hover:text-accent-primary transition-colors" title="Editar con IA">
                          <Edit3 size={14} />
                        </button>
                        <button onClick={() => handleRemoveOverlay(ov.overlay_id)} className="p-1.5 hover:bg-card rounded text-text-muted hover:text-status-error transition-colors" title="Eliminar de OBS">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    {editingId === ov.overlay_id && (
                      <div className="mt-3 flex gap-2" onClick={e => e.stopPropagation()}>
                        <input 
                          type="text" 
                          value={editPrompt}
                          onChange={e => setEditPrompt(e.target.value)}
                          placeholder="Ej. Cambia el color a rojo"
                          className="flex-1 bg-card border border-border-subtle rounded px-2.5 py-1.5 text-xs focus:border-accent-primary focus:outline-none"
                        />
                        <button 
                          onClick={() => handleEditOverlay(ov.overlay_id)}
                          disabled={isEditing}
                          className="px-3 bg-accent-secondary text-black text-xs font-bold rounded hover:bg-accent-primary transition-colors disabled:opacity-50"
                        >
                          {isEditing ? '...' : 'Aplicar'}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Live Preview Panel */}
          {selectedOverlay && (
            <div className="space-y-6 flex flex-col xl:col-span-1">
              <div className="glass-card p-5 border border-accent-secondary/40 shadow-[0_0_15px_rgba(var(--color-accent-secondary),0.05)] rounded-xl flex-1 flex flex-col min-h-[450px]">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-lg font-black tracking-tight text-accent-secondary flex items-center gap-2">
                    <Eye size={20} /> Vista Previa en Vivo
                  </h2>
                  <button 
                    onClick={() => setSelectedOverlay(null)}
                    className="p-1.5 hover:bg-card rounded-md text-text-muted hover:text-text-primary transition-colors"
                  >
                    <X size={16} />
                  </button>
                </div>
                <p className="text-[11px] text-text-muted mb-4">
                  Renderizando overlay <code className="bg-bg px-1 rounded">{selectedOverlay.overlay_id}</code> tal como lo ve OBS.
                </p>
                
                {/* Visual IFrame Container */}
                <div className="flex-1 bg-black/40 border border-border-subtle rounded-lg overflow-hidden relative min-h-[300px] flex items-center justify-center">
                  <iframe 
                    src={`/obs-overlay/${selectedOverlay.overlay_id}`}
                    title={`Preview ${selectedOverlay.overlay_id}`}
                    className="w-full h-full border-none bg-transparent"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '100%',
                      aspectRatio: `${selectedOverlay.width || 800} / ${selectedOverlay.height || 600}`,
                    }}
                  />
                </div>
                
                <div className="mt-4 p-3 bg-bg/50 border border-border-subtle rounded-lg space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-text-muted font-medium">Dimensiones:</span>
                    <span className="font-semibold text-text-primary">{selectedOverlay.width || 800}x{selectedOverlay.height || 600}px</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted font-medium">URL de OBS:</span>
                    <span className="font-semibold text-accent-primary select-all truncate max-w-[200px]" title={`${BRIDGE_BASE}/obs-overlay/${selectedOverlay.overlay_id}`}>
                      /obs-overlay/{selectedOverlay.overlay_id}
                    </span>
                  </div>
                  {selectedOverlay.prompt && (
                    <div className="pt-2 border-t border-border-subtle">
                      <span className="text-text-muted font-medium block mb-1">Concepto IA:</span>
                      <p className="italic text-text-muted line-clamp-3">{selectedOverlay.prompt}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
};
