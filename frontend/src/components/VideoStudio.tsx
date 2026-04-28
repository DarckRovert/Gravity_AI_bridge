import { useEffect, useState, useRef } from 'react';
import { Film, PlayCircle, Clock, CheckCircle2, AlertCircle, RefreshCw, X, Share2, Camera, MonitorPlay, Download, Trash2, Settings, Clapperboard, AudioLines, Sparkles, Layers, SlidersHorizontal } from 'lucide-react';

export const VideoStudio = () => {
  const [status, setStatus] = useState<any>(null);
  const [title, setTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [scenes, setScenes] = useState(6);
  const [voiceSpeed, setVoiceSpeed] = useState(150);
  const [style, setStyle] = useState('documental');
  const [lang, setLang] = useState('es');
  const [transitions, setTransitions] = useState(true);
  const [resolution, setResolution] = useState('1216x832');
  const [subtitles, setSubtitles] = useState(true);
  const [bgmType, setBgmType] = useState('ninguna');
  const [voiceId, setVoiceId] = useState('');
  const [quality, setQuality] = useState('hd');
  const [useLore, setUseLore] = useState(true);
  const [fps, setFps] = useState(24);
  const [sceneDuration, setSceneDuration] = useState(8);
  const [bgmVolume, setBgmVolume] = useState(0.1);
  const [codec, setCodec] = useState('libx264');
  const [kenBurns, setKenBurns] = useState(true);
  const [introCard, setIntroCard] = useState(false);
  const [colorGrade, setColorGrade] = useState('auto');
  
  const applyPreset = (preset: string) => {
    if (preset === 'documentary') {
      setStyle('documental');
      setScenes(8);
      setFps(24);
      setBgmVolume(0.15);
      setQuality('hd');
      setDurationMode('auto');
      setResolution('1216x832');
      setTransitions(true);
      setKenBurns(true);
      setIntroCard(false);
      setColorGrade('auto');
    } else if (preset === 'epic_trailer') {
      setStyle('cinematic');
      setScenes(10);
      setFps(30);
      setBgmVolume(0.3);
      setQuality('4k');
      setDurationMode('manual');
      setSceneDuration(4);
      setResolution('1216x832');
      setTransitions(false);
      setKenBurns(false);
      setIntroCard(true);
      setColorGrade('auto');
    } else if (preset === 'tiktok_short') {
      setStyle('anime');
      setScenes(5);
      setFps(30);
      setBgmVolume(0.2);
      setQuality('hd');
      setDurationMode('manual');
      setSceneDuration(3);
      setResolution('832x1216');
      setTransitions(true);
      setKenBurns(true);
      setIntroCard(false);
      setColorGrade('auto');
    } else if (preset === 'publicidad') {
      setStyle('publicitario');
      setScenes(6);
      setFps(60);
      setBgmVolume(0.25);
      setQuality('4k');
      setDurationMode('manual');
      setSceneDuration(3);
      setResolution('832x1216');
      setTransitions(true);
      setKenBurns(true);
      setIntroCard(true);
      setColorGrade('auto');
      setBgmType('publicitario');
      setVoiceSpeed(180);
    }
  };
  
  const [durationMode, setDurationMode] = useState('manual');
  const [creating, setCreating] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('creator'); // 'creator', 'queue', 'history'
  const [voices, setVoices] = useState<any[]>([]);
  
  const formRef = useRef<HTMLDivElement>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:7860/v1/video/status');
      if (res.ok) setStatus(await res.json());
    } catch (e) {}
  };

  const fetchVoices = async () => {
    try {
      const res = await fetch('http://localhost:7860/v1/video/voices');
      if (res.ok) {
        const data = await res.json();
        setVoices(data.voices || []);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchStatus();
    fetchVoices();
    const iv = setInterval(fetchStatus, 3000); // Polling más rápido para mejor UX
    return () => clearInterval(iv);
  }, []);

  const createVideo = async () => {
    if (!topic.trim()) return;
    setCreating(true);
    try {
      await fetch('http://localhost:7860/v1/video/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          topic, 
          n_scenes: scenes, 
          style,
          voice_speed: voiceSpeed,
          voice_id: voiceId,
          narration_lang: lang,
          transitions,
          resolution,
          subtitles,
          title,
          bgm_type: bgmType,
          quality,
          use_lore: useLore,
          fps,
          scene_duration: sceneDuration,
          duration_mode: durationMode,
          bgm_volume: bgmVolume,
          codec,
          ken_burns: kenBurns,
          intro_card: introCard,
          color_grade: colorGrade,
        })
      });
      setTopic('');
      setTitle('');
      setActiveTab('queue'); // Cambiar a la pestaña de cola al crear
      fetchStatus();
    } catch (e) {
      alert('Error al encolar video');
    } finally {
      setCreating(false);
    }
  };

  const deleteJob = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`⚠️ ALERTA DE SISTEMA\n\n¿Estás seguro de que deseas eliminar de raíz la producción #${id}?\n\nEsta acción purgará la base de datos y borrará permanentemente todos los archivos físicos (clips, audios, video final) del disco.`)) return;
    try {
      await fetch('http://localhost:7860/v1/video/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: id })
      });
      if (selectedVideo?.id === id) setSelectedVideo(null);
      fetchStatus();
    } catch (e) {
      alert('Error crítico al borrar la producción');
    }
  };

  const cancelJob = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`¿Deseas cancelar el procesamiento del job #${id}?`)) return;
    try {
      await fetch('http://localhost:7860/v1/video/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      fetchStatus();
    } catch (e) {
      alert('Error al cancelar el job');
    }
  };

  return (
    <div className="h-full flex flex-col bg-background text-text-primary overflow-hidden">
      {/* Header Studio Profesional */}
      <div className="px-8 py-5 border-b border-border-subtle bg-surface/50 backdrop-blur-md flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-accent-primary/20 to-accent-primary/5 border border-accent-primary/20 shadow-[0_0_15px_rgba(99,102,241,0.15)]">
            <Clapperboard className="text-accent-primary" size={26} />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight flex items-center gap-2">
              GRAVITY <span className="text-text-muted font-normal">|</span> STUDIO <span className="px-1.5 py-0.5 rounded bg-accent-primary/20 text-accent-primary text-[10px] uppercase font-bold tracking-widest border border-accent-primary/30">Pro Edition</span>
            </h1>
            <p className="text-xs text-text-muted font-medium mt-0.5">Pipeline Cinemático Autárquico V12.1</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          {/* Status Indicators */}
          <div className="flex items-center gap-4 text-xs font-bold bg-surface border border-border-subtle px-4 py-2 rounded-xl">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-success opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-status-success"></span>
              </span>
              <span className="text-text-muted">CORE</span>
            </div>
            <div className="w-px h-3 bg-border-subtle"></div>
            <div className={`flex items-center gap-2 ${status?.ffmpeg_ok ? 'text-status-success' : 'text-status-error'}`}>
              <CheckCircle2 size={14} /> FFMPEG RENDER
            </div>
          </div>
          
          {/* Tab Navigation */}
          <div className="flex p-1 bg-surface border border-border-subtle rounded-xl">
            <button onClick={() => setActiveTab('creator')} className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'creator' ? 'bg-accent-primary text-white shadow-md' : 'text-text-muted hover:text-text-primary hover:bg-surface-hover'}`}>
              <Settings size={14} /> DIRECTOR'S CUT
            </button>
            <button onClick={() => setActiveTab('queue')} className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'queue' ? 'bg-accent-primary text-white shadow-md' : 'text-text-muted hover:text-text-primary hover:bg-surface-hover'}`}>
              <Layers size={14} /> RENDER QUEUE {status?.pending_jobs?.length > 0 && <span className="bg-white/20 px-1.5 rounded-full text-[10px]">{status.pending_jobs.length}</span>}
            </button>
            <button onClick={() => setActiveTab('history')} className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'history' ? 'bg-accent-primary text-white shadow-md' : 'text-text-muted hover:text-text-primary hover:bg-surface-hover'}`}>
              <Film size={14} /> MASTER ARCHIVE
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8 scrollbar-hide bg-gradient-to-b from-background to-surface/30">
        <div className="max-w-7xl mx-auto">
          
          {/* =======================================================================
              TAB 1: CREATOR PANEL (DIRECTOR'S CUT)
              ======================================================================= */}
          {activeTab === 'creator' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              
              {/* Formulario Principal */}
              <div className="lg:col-span-8 space-y-6" ref={formRef}>
                <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
                    <div className="p-4 border-b border-border-subtle bg-surface/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                      <h2 className="text-sm font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                        <Sparkles size={16} className="text-accent-primary"/> 
                        Pizarra de Pre-Producción
                      </h2>
                      <div className="flex gap-2">
                        <button onClick={() => applyPreset('documentary')} className="px-3 py-1.5 bg-background border border-border-subtle rounded-lg text-[10px] font-bold text-text-muted hover:text-white hover:border-accent-primary hover:bg-accent-primary/10 transition-colors">
                          DOCU HISTÓRICO
                        </button>
                        <button onClick={() => applyPreset('epic_trailer')} className="px-3 py-1.5 bg-background border border-border-subtle rounded-lg text-[10px] font-bold text-text-muted hover:text-white hover:border-accent-secondary hover:bg-accent-secondary/10 transition-colors">
                          EPIC TRAILER
                        </button>
                        <button onClick={() => applyPreset('tiktok_short')} className="px-3 py-1.5 bg-background border border-border-subtle rounded-lg text-[10px] font-bold text-text-muted hover:text-white hover:border-pink-500 hover:bg-pink-500/10 transition-colors">
                          SHORT VIRAL
                        </button>
                        <button onClick={() => applyPreset('publicidad')} className="px-3 py-1.5 bg-background border border-border-subtle rounded-lg text-[10px] font-bold text-text-muted hover:text-white hover:border-emerald-500 hover:bg-emerald-500/10 transition-colors shadow-[0_0_10px_rgba(16,185,129,0.1)]">
                          PUBLICIDAD / AD
                        </button>
                      </div>
                    </div>
                  
                  <div className="p-6 space-y-8">
                    {/* Título & Guion */}
                    <div className="space-y-4">
                      <div>
                        <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2 flex items-center gap-2"><Film size={12}/> Título del Máster</label>
                        <input 
                          type="text" value={title} onChange={(e) => setTitle(e.target.value)}
                          placeholder="Ej: Odisea Espacial - Episodio 1"
                          className="w-full bg-surface border border-border-subtle rounded-xl p-4 text-base font-medium text-text-primary outline-none focus:border-accent-primary transition-all shadow-inner"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2 flex items-center gap-2"><AudioLines size={12}/> Tratamiento de Guion (Topic)</label>
                        <textarea 
                          value={topic} onChange={(e) => setTopic(e.target.value)}
                          placeholder="Escribe la premisa o el guion detallado. El LLM extraerá el Visual Anchor y expandirá las escenas automáticamente..."
                          className="w-full bg-surface border border-border-subtle rounded-xl p-4 text-sm text-text-primary outline-none focus:border-accent-primary transition-all h-32 resize-none shadow-inner leading-relaxed"
                        />
                      </div>
                    </div>

                    <div className="w-full h-px bg-gradient-to-r from-transparent via-border-subtle to-transparent"></div>

                    {/* Especificaciones Técnicas Básicas */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="space-y-2">
                        <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block">Estilo Cinemático</label>
                        <select value={style} onChange={(e) => setStyle(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-lg p-2.5 text-xs font-bold text-text-primary outline-none focus:border-accent-primary cursor-pointer hover:bg-surface-hover">
                          {status?.styles ? Object.entries(status.styles).map(([k, v]: any) => (
                            <option key={k} value={k}>{v}</option>
                          )) : <option value="documental">Documental</option>}
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block">Relación Aspecto</label>
                        <select value={resolution} onChange={(e) => setResolution(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-lg p-2.5 text-xs font-bold text-text-primary outline-none focus:border-accent-primary cursor-pointer hover:bg-surface-hover">
                          <option value="1216x832">16:9 Landscape</option>
                          <option value="832x1216">9:16 Portrait</option>
                          <option value="1024x1024">1:1 Square</option>
                          <option value="1920x1080">1920x1080 (HD)</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block">Modo Duración</label>
                        <select value={durationMode} onChange={(e) => setDurationMode(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-lg p-2.5 text-xs font-bold text-text-primary outline-none focus:border-accent-primary cursor-pointer hover:bg-surface-hover">
                          <option value="manual">Manual (Fijo)</option>
                          <option value="auto">Automático (TTS)</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block">Cant. Escenas</label>
                        <input type="number" min="1" max="100" value={scenes} onChange={(e) => setScenes(+e.target.value)} className="w-full bg-surface border border-border-subtle rounded-lg p-2.5 text-xs font-bold text-text-primary outline-none focus:border-accent-primary text-center" />
                      </div>
                      <div className="space-y-2">
                        <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block">Duración Esc. (s)</label>
                        <input type="number" min="1" max="120" value={sceneDuration} onChange={(e) => setSceneDuration(+e.target.value)} disabled={durationMode === 'auto'} className="w-full bg-surface border border-border-subtle rounded-lg p-2.5 text-xs font-bold text-text-primary outline-none focus:border-accent-primary text-center disabled:opacity-50 disabled:cursor-not-allowed" />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Panel de Rendimiento y Motor */}
                <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
                  <div className="p-4 border-b border-border-subtle bg-surface/50">
                    <h2 className="text-sm font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                      <Settings size={16} className="text-accent-primary"/> 
                      Configuración de Motor (Render & Audio)
                    </h2>
                  </div>
                  <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                    
                    {/* Audio Engine */}
                    <div className="space-y-5">
                      <h3 className="text-xs font-bold text-text-muted uppercase border-b border-border-subtle pb-2">Audio Engineering</h3>
                      
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1.5">
                          <label className="text-[10px] text-text-muted uppercase font-bold">Voz Principal</label>
                          <select value={voiceId} onChange={(e) => setVoiceId(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-md p-2 text-xs outline-none">
                            <option value="">Auto (Sistema)</option>
                            {voices.map((v) => (
                              <option key={v.id} value={v.id}>{v.name} ({v.lang})</option>
                            ))}
                          </select>
                           <button
                             id="btn-preview-voice"
                             onClick={async () => {
                               if (!voiceId) return;
                               try {
                                 const r = await fetch('http://localhost:7860/v1/video/preview_voice', {
                                   method: 'POST',
                                   headers: { 'Content-Type': 'application/json' },
                                   body: JSON.stringify({ voice_id: voiceId, text: 'Hola, esta es una prueba de la voz seleccionada en Gravity Studio. Sistema operativo al máximo nivel.' })
                                 });
                                 if (r.ok) {
                                   const blob = await r.blob();
                                   const url = URL.createObjectURL(blob);
                                   const audio = new Audio(url);
                                   audio.play();
                                 }
                               } catch (e) { console.error('preview_voice:', e); }
                             }}
                             disabled={!voiceId}
                             className="mt-1.5 w-full px-3 py-1.5 bg-surface/50 border border-border-subtle rounded-md text-[10px] font-bold uppercase tracking-wider text-text-muted hover:text-accent-primary hover:border-accent-primary/60 transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
                           >
                             ▶ Preview de Voz
                           </button>
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-[10px] text-text-muted uppercase font-bold">Idioma TTS</label>
                          <select value={lang} onChange={(e) => setLang(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-md p-2 text-xs outline-none">
                            <option value="es">Español</option>
                            <option value="en">Inglés</option>
                            <option value="pt">Portugués</option>
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1.5">
                          <label className="text-[10px] text-text-muted uppercase font-bold">BGM (Fondo)</label>
                          <select value={bgmType} onChange={(e) => setBgmType(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-md p-2 text-xs outline-none">
                            
                             <option value="ninguna">Sin Música</option>
                             <option value="epico">Cine Épico</option>
                             <option value="heroico">Heroico / Épico Orquestal</option>
                             <option value="documental">Documental / Ambiental</option>
                             <option value="ambient">Ambiental Suave</option>
                             <option value="tension">Tensión / Thriller</option>
                             <option value="synthwave">Retro / Synth 80s</option>
                             <option value="lofi_beats">Lo-Fi Beats</option>
                             <option value="jazz">Jazz Lounge</option>
                             <option value="corporativo">Corporativo / Limpio</option>
                             <option value="publicitario">Upbeat / Publicitario</option>
                           
</select>
                        </div>
                        <div className="space-y-1.5">
                          <div className="flex justify-between">
                            <label className="text-[10px] text-text-muted uppercase font-bold">Vol. BGM</label>
                            <span className="text-[10px] font-mono text-accent-primary">{(bgmVolume * 100).toFixed(0)}%</span>
                          </div>
                          <input type="range" min="0" max="1" step="0.05" value={bgmVolume} onChange={(e) => setBgmVolume(+e.target.value)} className="w-full accent-accent-primary mt-1" />
                        </div>
                      </div>

                      <div className="space-y-1.5">
                        <div className="flex justify-between">
                          <label className="text-[10px] text-text-muted uppercase font-bold">Velocidad TTS</label>
                          <span className="text-[10px] font-mono text-accent-primary">{voiceSpeed} WPM</span>
                        </div>
                        <input type="range" min="100" max="250" step="5" value={voiceSpeed} onChange={(e) => setVoiceSpeed(+e.target.value)} className="w-full accent-accent-primary mt-1" />
                      </div>
                    </div>

                    {/* Render Engine */}
                    <div className="space-y-5">
                      <h3 className="text-xs font-bold text-text-muted uppercase border-b border-border-subtle pb-2">Render Pipeline</h3>
                      
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1.5">
                          <label className="text-[10px] text-text-muted uppercase font-bold">Framerate (FPS)</label>
                          <select value={fps} onChange={(e) => setFps(+e.target.value)} className="w-full bg-surface border border-border-subtle rounded-md p-2 text-xs outline-none">
                            <option value="24">24 (Cine Estándar)</option>
                            <option value="30">30 (Digital/TV)</option>
                            <option value="60">60 (HFR Fluido)</option>
                          </select>
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-[10px] text-text-muted uppercase font-bold">Video Codec</label>
                          <select value={codec} onChange={(e) => setCodec(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-md p-2 text-xs outline-none">
                            <option value="libx264">H.264 (Universal)</option>
                            <option value="libx265">H.265 (Eficiente)</option>
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1.5">
                          <label className="text-[10px] text-text-muted uppercase font-bold">Calidad Imagen</label>
                          <select value={quality} onChange={(e) => setQuality(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-md p-2 text-xs outline-none">
                            <option value="standard">Standard (Rápido)</option>
                            <option value="hd">HD (Balanceado)</option>
                            <option value="4k">Cinemático (Lento)</option>
                          </select>
                        </div>
                        <div className="flex flex-col justify-center space-y-2 pt-4">
                          <label className="flex items-center gap-2 cursor-pointer text-xs font-medium hover:text-accent-primary transition-colors">
                            <input type="checkbox" checked={subtitles} onChange={(e) => setSubtitles(e.target.checked)} className="accent-accent-primary w-4 h-4" />
                            Quemar Subtítulos
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer text-xs font-medium hover:text-accent-primary transition-colors">
                            <input type="checkbox" checked={transitions} onChange={(e) => setTransitions(e.target.checked)} className="accent-accent-primary w-4 h-4" />
                            Transiciones Fade
                          </label>
                        </div>
                      </div>

                      <div className="pt-2">
                        <label className="flex items-center gap-2 cursor-pointer text-xs font-medium bg-surface/50 border border-border-subtle p-2 rounded-lg hover:border-accent-primary/50 transition-colors w-full">
                          <input type="checkbox" checked={useLore} onChange={(e) => setUseLore(e.target.checked)} className="accent-accent-primary w-4 h-4" />
                          <div className="flex-1">
                            <span className="block font-bold">Persistir Lore al Conocimiento</span>
                            <span className="block text-[9px] text-text-muted">Guarda el guion y estilo en la base de RAG de Gravity</span>
                          </div>
                        </label>
                      </div>

                      {/* Efectos Cinematográficos */}
                      <div className="pt-2 space-y-2">
                        <h4 className="text-[9px] font-bold text-text-muted uppercase tracking-widest">Efectos Cinematográficos</h4>
                        <div className="grid grid-cols-1 gap-2">
                          <label className="flex items-center gap-2 cursor-pointer text-xs font-medium bg-surface/50 border border-border-subtle p-2 rounded-lg hover:border-accent-primary/50 transition-colors">
                            <input type="checkbox" checked={kenBurns} onChange={(e) => setKenBurns(e.target.checked)} className="accent-accent-primary w-4 h-4" />
                            <div className="flex-1">
                              <span className="block font-bold">Ken Burns (Zoom + Pan)</span>
                              <span className="block text-[9px] text-text-muted">Animación de cámara sobre imágenes estáticas</span>
                            </div>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer text-xs font-medium bg-surface/50 border border-border-subtle p-2 rounded-lg hover:border-accent-primary/50 transition-colors">
                            <input type="checkbox" checked={introCard} onChange={(e) => setIntroCard(e.target.checked)} className="accent-accent-primary w-4 h-4" />
                            <div className="flex-1">
                              <span className="block font-bold">Tarjeta de Intro</span>
                              <span className="block text-[9px] text-text-muted">Slide inicial con título animado (3.5s)</span>
                            </div>
                          </label>
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-[10px] text-text-muted uppercase font-bold">Color Grade</label>
                          <select value={colorGrade} onChange={(e) => setColorGrade(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-md p-2 text-xs outline-none">
                            <option value="auto">Auto (por estilo cinemático)</option>
                            <option value="none">Sin grading</option>
                          </select>
                        </div>
                      </div>

                    </div>

                  </div>
                </div>
              </div>

              {/* Panel de Ejecución (Sidebar) */}
              <div className="lg:col-span-4 space-y-6">
                <div className="glass-panel p-6 rounded-2xl border-accent-primary/30 bg-gradient-to-b from-surface to-background shadow-[0_0_30px_rgba(0,0,0,0.5)] flex flex-col h-full justify-between">
                  <div>
                    <h3 className="text-sm font-black text-text-primary uppercase tracking-widest mb-6 flex items-center gap-2">
                      <SlidersHorizontal size={16} className="text-accent-primary"/> 
                      Consola de Masterización
                    </h3>

                    <div className="space-y-4 mb-8">
                      <div className="flex justify-between items-center text-xs border-b border-border-subtle pb-2">
                        <span className="text-text-muted">Tiempo de Render CPU / Escena</span>
                        <span className="font-mono font-bold">~4.5 min</span>
                      </div>
                      <div className="flex justify-between items-center text-xs border-b border-border-subtle pb-2">
                        <span className="text-text-muted">Tiempo Total Estimado</span>
                        <span className="font-mono font-bold text-accent-primary">~{Math.round(scenes * 4.5)} min</span>
                      </div>
                      <div className="flex justify-between items-center text-xs border-b border-border-subtle pb-2">
                        <span className="text-text-muted">Resolución de Salida</span>
                        <span className="font-mono font-bold text-white">{resolution.split('x').join(' x ')}</span>
                      </div>
                      <div className="flex justify-between items-center text-xs border-b border-border-subtle pb-2">
                        <span className="text-text-muted">Duración Estimada Master</span>
                        <span className="font-mono font-bold text-white">{durationMode === 'auto' ? `~${scenes * 10}s (Adaptativa)` : `${scenes * sceneDuration}s (Fijo)`}</span>
                      </div>
                    </div>
                  </div>

                  <button 
                    onClick={createVideo}
                    disabled={creating || !topic.trim()}
                    className="w-full py-5 rounded-xl bg-gradient-to-r from-accent-primary to-accent-secondary text-white font-black text-sm tracking-widest shadow-[0_0_20px_rgba(99,102,241,0.4)] hover:shadow-[0_0_30px_rgba(99,102,241,0.6)] hover:scale-[1.02] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:grayscale disabled:hover:scale-100"
                  >
                    {creating ? <RefreshCw className="animate-spin" size={20} /> : <MonitorPlay size={20} />}
                    {creating ? 'INICIALIZANDO RENDER...' : 'RENDERIZAR MASTER'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* =======================================================================
              TAB 2: QUEUE & ACTIVE RENDER
              ======================================================================= */}
          {activeTab === 'queue' && (
            <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              
              {status?.current_job ? (
                <div className="glass-panel p-8 rounded-2xl border-accent-primary/50 bg-gradient-to-br from-background to-accent-primary/10 shadow-[0_0_40px_rgba(99,102,241,0.15)] relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                    <MonitorPlay size={160} />
                  </div>
                  <div className="absolute top-4 right-4 z-20">
                    <button onClick={(e) => cancelJob(status.current_job.id, e)} className="p-2 rounded-lg bg-black/40 hover:bg-status-error text-white transition-colors border border-white/10 flex items-center gap-2 text-xs font-bold">
                      <X size={14} /> CANCELAR RENDER
                    </button>
                  </div>
                  <div className="relative z-10 space-y-8">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="text-[10px] font-bold text-accent-primary uppercase tracking-widest mb-2 flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-accent-primary animate-ping"></span> 
                          RENDER ENGINE ACTIVO — JOB #{status.current_job.id}
                        </div>
                        <h3 className="text-3xl font-black text-text-primary leading-tight max-w-2xl">{status.current_job.topic}</h3>
                      </div>
                      <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-accent-primary to-white drop-shadow-lg">
                        {status.current_job.progress}%
                      </div>
                    </div>

                    <div className="space-y-3 bg-black/40 p-5 rounded-xl border border-white/5 backdrop-blur-sm">
                      <div className="flex justify-between text-xs font-bold text-text-muted uppercase tracking-widest">
                        <span className="text-accent-primary flex items-center gap-2"><RefreshCw size={12} className="animate-spin"/> {status.current_job.current_step}</span>
                        <span className="font-mono text-white/50">Cálculo en vivo...</span>
                      </div>
                      <div className="w-full bg-background h-4 rounded-full overflow-hidden border border-border-subtle/50">
                        <div className="h-full bg-gradient-to-r from-accent-primary to-accent-secondary transition-all duration-1000 shadow-[0_0_15px_rgba(99,102,241,0.8)] relative" style={{ width: `${status.current_job.progress}%` }}>
                          <div className="absolute inset-0 bg-white/20 w-full animate-[shimmer_2s_infinite]"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="glass-panel p-16 rounded-2xl border-dashed border-border-subtle text-center flex flex-col items-center justify-center gap-4 bg-surface/20">
                  <Clock size={48} className="text-text-muted opacity-30" />
                  <h3 className="text-lg font-bold text-text-primary">Motores de Render Inactivos</h3>
                  <p className="text-sm text-text-muted max-w-md">No hay ninguna producción en curso. Dirígete al Director's Cut para encolar un nuevo proyecto.</p>
                  <button onClick={() => setActiveTab('creator')} className="mt-4 px-6 py-2 rounded-lg bg-surface border border-border-subtle text-sm font-bold text-accent-primary hover:bg-accent-primary hover:text-white transition-colors">
                    Crear Producción
                  </button>
                </div>
              )}

              {/* Pending Queue List */}
              {status?.pending_jobs && status.pending_jobs.length > 0 && (
                <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
                  <div className="p-4 border-b border-border-subtle bg-surface/50">
                    <h3 className="text-xs font-black text-text-primary uppercase tracking-widest">Cola de Render ({status.pending_jobs.length})</h3>
                  </div>
                  <div className="divide-y divide-border-subtle">
                    {status.pending_jobs.map((job: any, i: number) => (
                      <div key={job.id} className="p-4 flex items-center justify-between hover:bg-surface/30 transition-colors">
                        <div className="flex items-center gap-4">
                          <div className="text-2xl font-black text-border-subtle">{(i+1).toString().padStart(2, '0')}</div>
                          <div>
                            <div className="font-bold text-text-primary text-sm">{job.title || job.topic}</div>
                            <div className="text-[10px] text-text-muted mt-0.5 font-mono">ID: #{job.id} | {job.style} | {job.n_scenes} escenas</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] uppercase font-bold text-text-muted bg-surface px-2 py-1 rounded border border-border-subtle">Waiting</span>
                          <button onClick={(e) => cancelJob(job.id, e)} className="p-1.5 rounded hover:bg-status-error/20 text-status-error transition-colors" title="Cancelar Job">
                            <X size={14} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Statistics Dashboard */}
              {status?.aggregate && (
                <div className="glass-panel rounded-2xl border border-border-subtle p-6 grid grid-cols-2 md:grid-cols-4 gap-4 bg-surface/10 mt-8">
                  <div className="flex flex-col items-center p-3 rounded-xl bg-surface/30 border border-border-subtle/50">
                    <span className="text-[10px] uppercase font-bold text-text-muted mb-1">Total Producciones</span>
                    <span className="text-2xl font-black text-text-primary">{status.aggregate.total}</span>
                  </div>
                  <div className="flex flex-col items-center p-3 rounded-xl bg-surface/30 border border-border-subtle/50">
                    <span className="text-[10px] uppercase font-bold text-text-muted mb-1">Completados</span>
                    <span className="text-2xl font-black text-status-success">{status.aggregate.completed}</span>
                  </div>
                  <div className="flex flex-col items-center p-3 rounded-xl bg-surface/30 border border-border-subtle/50">
                    <span className="text-[10px] uppercase font-bold text-text-muted mb-1">Cancelados/Borrados</span>
                    <span className="text-2xl font-black text-status-warning">{status.aggregate.cancelled + status.aggregate.deleted}</span>
                  </div>
                  <div className="flex flex-col items-center p-3 rounded-xl bg-surface/30 border border-border-subtle/50">
                    <span className="text-[10px] uppercase font-bold text-text-muted mb-1">Errores</span>
                    <span className="text-2xl font-black text-status-error">{status.aggregate.failed}</span>
                  </div>
                </div>
              )}

            </div>
          )}

          {/* =======================================================================
              TAB 3: MASTER ARCHIVE (HISTORY)
              ======================================================================= */}
          {activeTab === 'history' && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {(status?.history || []).map((job: any) => {
                  const isReady = job.status?.toLowerCase() === 'completed' || job.status?.toLowerCase() === 'done';
                  const isDeleted = job.status?.toLowerCase() === 'deleted';
                  const isError = job.status?.toLowerCase() === 'failed';
                  
                  return (
                    <div key={job.id} className="glass-panel rounded-2xl border border-border-subtle overflow-hidden flex flex-col group hover:border-accent-primary/30 transition-all hover:shadow-[0_8px_30px_rgba(0,0,0,0.4)]">
                      
                      {/* Video Thumbnail Area (Mock) */}
                      <div 
                        className={`aspect-video bg-black relative flex items-center justify-center cursor-pointer transition-all overflow-hidden ${!isReady ? 'opacity-50 pointer-events-none' : 'group-hover:bg-zinc-900'}`}
                        onClick={() => isReady && setSelectedVideo(job)}
                      >
                        {isReady ? (
                          <>
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent z-10 pointer-events-none"></div>
                            {job.thumbnail_path && (
                              <img src={`http://localhost:7860/v1/video/thumbnail?job_id=${job.id}`} alt="thumb" className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity" />
                            )}
                            <PlayCircle size={48} className="text-white/50 group-hover:text-accent-primary group-hover:scale-110 transition-all duration-300 z-20 relative" strokeWidth={1} />
                            <div className="absolute bottom-2 right-2 z-20 px-1.5 py-0.5 bg-black/70 backdrop-blur text-[9px] text-white rounded font-mono font-bold">
                              {job.resolution || '16:9'}
                            </div>
                          </>
                        ) : isDeleted ? (
                          <div className="text-center">
                            <Trash2 size={32} className="mx-auto text-text-muted/50 mb-2" />
                            <span className="text-[10px] font-bold uppercase text-text-muted">Purgado</span>
                          </div>
                        ) : isError ? (
                          <div className="text-center">
                            <AlertCircle size={32} className="mx-auto text-status-error/50 mb-2" />
                            <span className="text-[10px] font-bold uppercase text-status-error">Error Crítico</span>
                          </div>
                        ) : (
                          <div className="text-center">
                            <Clock size={32} className="mx-auto text-text-muted/50 mb-2" />
                            <span className="text-[10px] font-bold uppercase text-text-muted">{job.status}</span>
                          </div>
                        )}
                      </div>

                      {/* Info & Actions */}
                      <div className="p-4 flex-1 flex flex-col justify-between bg-surface/30">
                        <div>
                          <h3 className="font-bold text-sm text-text-primary line-clamp-2 leading-tight" title={job.title || job.topic}>{job.title || job.topic}</h3>
                          <div className="mt-2 flex flex-wrap gap-1">
                            <span className="px-1.5 py-0.5 rounded-sm bg-background border border-border-subtle text-[9px] text-text-muted uppercase font-bold">{job.style}</span>
                            <span className="px-1.5 py-0.5 rounded-sm bg-background border border-border-subtle text-[9px] text-text-muted uppercase font-bold">{job.codec || 'h264'}</span>
                          </div>
                        </div>
                        
                        <div className="mt-4 pt-3 border-t border-border-subtle/50 flex justify-between items-center">
                          <span className="text-[10px] text-text-muted font-mono">ID: #{job.id}</span>
                          <div className="flex gap-1">
                            {isReady && (
                              <a 
                                href={`http://localhost:7860/v1/video/download?file=${job.output_path?.split(/[/\\]/).pop() || ''}`} 
                                download
                                className="p-1.5 rounded bg-surface hover:bg-accent-primary hover:text-white text-text-muted transition-colors"
                                title="Descargar MP4"
                              >
                                <Download size={14} />
                              </a>
                            )}
                            <button 
                              onClick={(e) => deleteJob(job.id, e)}
                              className="p-1.5 rounded bg-surface hover:bg-status-error hover:text-white text-text-muted transition-colors"
                              title="Purgar del sistema"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </div>
                      </div>

                    </div>
                  );
                })}
                {status?.history?.length === 0 && (
                  <div className="col-span-full py-20 text-center text-text-muted">
                    No hay registros en el archivo maestro.
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </div>

      {/* =======================================================================
          MODAL: VIDEO PLAYER (CINEMA VIEW)
          ======================================================================= */}
      {selectedVideo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/95 backdrop-blur-lg animate-in fade-in duration-300">
          <div className="max-w-6xl w-full flex flex-col gap-4">
            
            <div className="flex justify-between items-center px-2">
              <div className="text-white">
                <h3 className="font-black text-xl">{selectedVideo.title || selectedVideo.topic}</h3>
                <p className="text-xs text-white/50 font-mono mt-1">
                  MASTER ID: #{selectedVideo.id} | {selectedVideo.fps} FPS | {selectedVideo.codec} | {selectedVideo.resolution}
                </p>
              </div>
              <button onClick={() => setSelectedVideo(null)} className="p-3 rounded-full bg-white/10 hover:bg-white/20 hover:text-status-error transition-colors text-white">
                <X size={24}/>
              </button>
            </div>
            
            <div className="rounded-2xl overflow-hidden bg-black shadow-[0_0_100px_rgba(0,0,0,1)] border border-white/10 relative group flex items-center justify-center min-h-[50vh]">
              <video 
                controls 
                autoPlay 
                src={`http://localhost:7860/v1/video/stream?path=${selectedVideo.output_path?.split(/[/\\]/).pop() || ''}`} 
                className="w-full max-h-[75vh] object-contain"
              />
            </div>
            
            <div className="flex justify-between items-center px-2 mt-2">
              <a 
                href={`http://localhost:7860/v1/video/download?file=${selectedVideo.output_path?.split(/[/\\]/).pop() || ''}`} 
                download
                target="_blank" rel="noreferrer"
                className="px-6 py-3 bg-white text-black font-black rounded-xl hover:bg-accent-primary hover:text-white transition-all flex items-center gap-2 text-sm"
              >
                <Download size={18}/> OBTENER MÁSTER MP4
              </a>

              <div className="flex gap-3">
                <button onClick={() => window.open("https://business.facebook.com/creatorstudio/home", "_blank")} className="p-3 rounded-xl bg-[#1877F2]/20 text-[#1877F2] hover:bg-[#1877F2] hover:text-white transition-all border border-[#1877F2]/30" title="Compartir a Facebook">
                  <Share2 size={18}/>
                </button>
                <button onClick={() => window.open("https://www.instagram.com/", "_blank")} className="p-3 rounded-xl bg-[#E1306C]/20 text-[#E1306C] hover:bg-[#E1306C] hover:text-white transition-all border border-[#E1306C]/30" title="Subir a Reels">
                  <Camera size={18}/>
                </button>
                <button onClick={() => window.open("https://studio.youtube.com/", "_blank")} className="p-3 rounded-xl bg-[#FF0000]/20 text-[#FF0000] hover:bg-[#FF0000] hover:text-white transition-all border border-[#FF0000]/30" title="Subir a YouTube">
                  <MonitorPlay size={18}/>
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};
