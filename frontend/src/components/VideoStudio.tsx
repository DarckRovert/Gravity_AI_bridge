import { useEffect, useState } from 'react';
import { Video, Film, PlayCircle, Clock, CheckCircle2, AlertCircle, Plus, RefreshCw, X, Share2, Camera, MonitorPlay, Download, Play } from 'lucide-react';

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
  const [creating, setCreating] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<any>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:7860/v1/video/status');
      if (res.ok) setStatus(await res.json());
    } catch (e) {}
  };

  useEffect(() => {
    fetchStatus();
    const iv = setInterval(fetchStatus, 5000);
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
          narration_lang: lang,
          transitions,
          resolution,
          subtitles,
          title,
          bgm_type: bgmType
        })
      });
      setTopic('');
      setTitle('');
      fetchStatus();
    } catch (e) {
      alert('Error al encolar video');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-7xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle">
              <Video className="text-accent-primary" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Video Studio</h1>
              <p className="text-text-muted mt-1 font-medium">Pipeline de generación de video cinematográfico con IA y FFMPEG.</p>
            </div>
          </div>
          <div className={`px-4 py-2 rounded-xl border flex items-center gap-2 text-sm font-bold
            ${status?.ffmpeg_ok ? 'bg-status-success/10 border-status-success/30 text-status-success' : 'bg-status-error/10 border-status-error/30 text-status-error'}`}>
            {status?.ffmpeg_ok ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            FFMPEG Engine: {status?.ffmpeg_ok ? 'READY' : 'MISSING'}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Creator Panel */}
          <div className="lg:col-span-1 space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
              <h2 className="text-lg font-bold text-text-primary flex items-center gap-2"><Plus size={18} className="text-accent-primary"/> Nueva Producción</h2>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2">Título del Video</label>
                    <input 
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="Ej: El Misterio del Universo..."
                      className="w-full bg-card border border-border-subtle rounded-xl p-4 text-sm text-text-primary outline-none focus:border-accent-primary transition-all"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2">Música de Fondo</label>
                    <select 
                      value={bgmType}
                      onChange={(e) => setBgmType(e.target.value)}
                      className="w-full bg-card border border-border-subtle rounded-xl p-4 text-sm text-text-primary outline-none focus:border-accent-primary"
                    >
                      <option value="ninguna">Sin Música</option>
                      <option value="epico">Épica / Cinemática</option>
                      <option value="documental">Documental / Chill</option>
                      <option value="synthwave">Retro / Synthwave</option>
                      <option value="jazz">Jazz / Lounge</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2">Tema / Guion</label>
                  <textarea 
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="Ej: Escribe aquí la historia que quieres contar..."
                    className="w-full bg-card border border-border-subtle rounded-xl p-4 text-sm text-text-primary outline-none focus:border-accent-primary transition-all h-32 resize-none"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2">Estilo Visual</label>
                    <select 
                      value={style}
                      onChange={(e) => setStyle(e.target.value)}
                      className="w-full bg-card border border-border-subtle rounded-xl p-3 text-sm text-text-primary outline-none focus:border-accent-primary"
                    >
                      {status?.styles ? Object.entries(status.styles).map(([k, v]: any) => (
                        <option key={k} value={k}>{v}</option>
                      )) : <option value="documental">Documental</option>}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2">Idioma (Narrador)</label>
                    <select 
                      value={lang}
                      onChange={(e) => setLang(e.target.value)}
                      className="w-full bg-card border border-border-subtle rounded-xl p-3 text-sm text-text-primary outline-none focus:border-accent-primary"
                    >
                      <option value="es">Español</option>
                      <option value="en">English</option>
                      <option value="pt">Português</option>
                      <option value="fr">Français</option>
                      <option value="de">Deutsch</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2">Escenas ({scenes})</label>
                    <input 
                      type="range" min="3" max="15" 
                      value={scenes}
                      onChange={(e) => setScenes(+e.target.value)}
                      className="w-full accent-accent-primary"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2">Velocidad Voz ({voiceSpeed} WPM)</label>
                    <input 
                      type="range" min="100" max="250" step="10"
                      value={voiceSpeed}
                      onChange={(e) => setVoiceSpeed(+e.target.value)}
                      className="w-full accent-accent-primary"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2">Resolución</label>
                  <select 
                    value={resolution}
                    onChange={(e) => setResolution(e.target.value)}
                    className="w-full bg-card border border-border-subtle rounded-xl p-2 text-sm text-text-primary outline-none focus:border-accent-primary"
                  >
                    <option value="1216x832">16:9 (1216x832)</option>
                    <option value="832x1216">9:16 (832x1216)</option>
                    <option value="1024x1024">1:1 (1024x1024)</option>
                  </select>
                </div>

                <div className="flex items-center justify-between gap-4 p-4 rounded-xl bg-card border border-border-subtle">
                  <label className="flex items-center gap-2 cursor-pointer text-sm font-bold text-text-primary">
                    <input type="checkbox" checked={subtitles} onChange={(e) => setSubtitles(e.target.checked)} className="accent-accent-primary w-4 h-4" />
                    Subtítulos
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer text-sm font-bold text-text-primary">
                    <input type="checkbox" checked={transitions} onChange={(e) => setTransitions(e.target.checked)} className="accent-accent-primary w-4 h-4" />
                    Fade FFMPEG
                  </label>
                </div>
              </div>

              <button 
                onClick={createVideo}
                disabled={creating || !topic.trim()}
                className="w-full py-4 rounded-xl bg-accent-primary text-white font-extrabold shadow-lg hover:scale-[1.02] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {creating ? <RefreshCw className="animate-spin" size={20} /> : <Film size={20} />}
                {creating ? 'ENCOLANDO...' : 'INICIAR PROCESO'}
              </button>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
              <h3 className="text-xs font-bold text-text-primary uppercase tracking-widest mb-4">Métricas del Pipeline</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-text-muted">Jobs Completados</span>
                  <span className="font-bold text-text-primary">{status?.history?.length || 0}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-text-muted">Espacio en Disco</span>
                  <span className="font-bold text-text-primary">42.8 GB libres</span>
                </div>
              </div>
            </div>
          </div>

          {/* Queue & History Panel */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Current Job */}
            {status?.current_job ? (
              <div className="glass-panel p-8 rounded-2xl border-accent-primary/40 bg-accent-primary/5 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <Film size={80} />
                </div>
                <div className="relative z-10 space-y-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="text-[10px] font-bold text-accent-primary uppercase tracking-widest mb-1 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-accent-primary animate-ping"></span> EN PROCESO — ID #{status.current_job.id}
                      </div>
                      <h3 className="text-2xl font-black text-text-primary">{status.current_job.topic}</h3>
                    </div>
                    <div className="text-4xl font-black text-accent-primary">{status.current_job.progress}%</div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-bold text-text-muted uppercase">
                      <span>{status.current_job.current_step}</span>
                      <span>Restante: ~2m</span>
                    </div>
                    <div className="w-full bg-surface h-3 rounded-full overflow-hidden border border-border-subtle">
                      <div className="h-full bg-accent-primary transition-all duration-1000 shadow-[0_0_15px_rgba(99,102,241,0.5)]" style={{ width: `${status.current_job.progress}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="glass-panel p-8 rounded-2xl border-dashed border-border-subtle text-center text-text-muted flex flex-col items-center gap-3">
                <Clock size={40} className="opacity-20" />
                <p className="font-medium">No hay producciones activas en este momento.</p>
              </div>
            )}

            {/* History Table */}
            <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
              <div className="p-6 border-b border-border-subtle bg-surface/30">
                <h3 className="font-bold text-text-primary flex items-center gap-2"><PlayCircle size={18} className="text-accent-secondary" /> Historial de Exportación</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="bg-surface/50 text-[10px] uppercase font-bold text-text-muted">
                      <th className="px-6 py-4">ID</th>
                      <th className="px-6 py-4">Tema / Producción</th>
                      <th className="px-6 py-4">Estado</th>
                      <th className="px-6 py-4">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-subtle">
                    {(status?.history || []).map((job: any) => (
                      <tr key={job.id} className="hover:bg-card transition-colors group">
                        <td className="px-6 py-4 font-mono text-xs text-text-muted">#{job.id}</td>
                        <td className="px-6 py-4">
                          <div className="font-bold text-text-primary">{job.title || job.topic}</div>
                          <div className="text-[10px] text-text-muted mt-0.5">{job.style} • {job.scenes} escenas</div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase
                            ${(job.status?.toLowerCase() === 'completed' || job.status?.toLowerCase() === 'done') ? 'bg-status-success/10 text-status-success' : job.status?.toLowerCase() === 'deleted' ? 'bg-surface border border-border-subtle text-text-muted' : 'bg-status-error/10 text-status-error'}`}>
                            {job.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <button 
                            onClick={() => (job.status?.toLowerCase() === 'completed' || job.status?.toLowerCase() === 'done') && setSelectedVideo(job)}
                            className={`p-2 rounded-lg bg-surface border border-border-subtle transition-all
                              ${(job.status?.toLowerCase() === 'completed' || job.status?.toLowerCase() === 'done') ? 'text-accent-primary hover:bg-accent-primary hover:text-white cursor-pointer' : 'text-text-muted opacity-50 cursor-not-allowed'}`}
                            title={job.status?.toLowerCase() === 'deleted' ? "Archivo eliminado" : "Reproducir y Compartir"}
                          >
                            <Play size={16} fill="currentColor" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

          </div>

        </div>

      </div>

      {/* Video Player Modal */}
      {selectedVideo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-surface border border-border-subtle rounded-2xl overflow-hidden max-w-4xl w-full shadow-2xl">
            <div className="p-4 border-b border-border-subtle flex justify-between items-center bg-card">
              <h3 className="font-bold text-text-primary">Reproductor Cinematic: #{selectedVideo.id}</h3>
              <button onClick={() => setSelectedVideo(null)} className="p-2 rounded-lg bg-surface hover:text-status-error transition-colors">
                <X size={20}/>
              </button>
            </div>
            <div className="p-6 bg-black flex justify-center">
              <video 
                controls 
                autoPlay 
                src={`http://localhost:7860/v1/video/stream?path=${selectedVideo.output_path?.split(/[/\\]/).pop() || ''}`} 
                className="max-h-[60vh] rounded-lg shadow-[0_0_40px_rgba(0,0,0,0.8)]"
              />
            </div>
            <div className="p-6 bg-card border-t border-border-subtle">
              <h4 className="text-xs font-black text-text-muted uppercase tracking-widest mb-4">Exportar & Monetizar</h4>
              <div className="flex flex-wrap gap-4">
                <button onClick={() => window.open("https://business.facebook.com/creatorstudio/home", "_blank")} className="flex-1 min-w-[140px] py-3 bg-blue-600/10 text-blue-500 border border-blue-500/30 font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-blue-600 hover:text-white transition-all shadow-lg">
                  <Share2 size={18}/> Facebook
                </button>
                <button onClick={() => window.open("https://www.instagram.com/", "_blank")} className="flex-1 min-w-[140px] py-3 bg-pink-600/10 text-pink-500 border border-pink-500/30 font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-pink-600 hover:text-white transition-all shadow-lg">
                  <Camera size={18}/> Reels
                </button>
                <button onClick={() => window.open("https://studio.youtube.com/", "_blank")} className="flex-1 min-w-[140px] py-3 bg-red-600/10 text-red-500 border border-red-500/30 font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-red-600 hover:text-white transition-all shadow-lg">
                  <MonitorPlay size={18}/> Shorts
                </button>
                <a 
                  href={`http://localhost:7860/v1/video/download?file=${selectedVideo.output_path?.split(/[/\\]/).pop() || ''}`} 
                  download
                  target="_blank" rel="noreferrer"
                  className="flex-1 min-w-[140px] py-3 bg-surface border border-border-subtle font-bold text-text-primary rounded-xl flex items-center justify-center gap-2 hover:bg-accent-primary hover:border-accent-primary hover:text-white transition-all shadow-lg"
                >
                  <Download size={18}/> MP4 Master
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
