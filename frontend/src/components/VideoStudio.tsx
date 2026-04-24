import { useEffect, useState } from 'react';
import { Video, Film, PlayCircle, Clock, CheckCircle2, AlertCircle, Plus, Wand2, RefreshCw } from 'lucide-react';

export const VideoStudio = () => {
  const [status, setStatus] = useState<any>(null);
  const [topic, setTopic] = useState('');
  const [creating, setCreating] = useState(false);

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
        body: JSON.stringify({ topic, n_scenes: 6, style: 'cinematic' })
      });
      setTopic('');
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
                <div>
                  <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2">Tema / Guion</label>
                  <textarea 
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="Ej: Historia de la computación cuántica..."
                    className="w-full bg-card border border-border-subtle rounded-xl p-4 text-sm text-text-primary outline-none focus:border-accent-primary transition-all h-32 resize-none"
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2">Estilo Visual</label>
                  <select className="w-full bg-card border border-border-subtle rounded-xl p-3 text-sm text-text-primary outline-none focus:border-accent-primary">
                    <option>Cinematic Documentary</option>
                    <option>Epic Sci-Fi</option>
                    <option>Abstract Art</option>
                  </select>
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
                          <div className="font-bold text-text-primary">{job.topic}</div>
                          <div className="text-[10px] text-text-muted mt-0.5">{job.style} • {job.scenes} escenas</div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase
                            ${job.status === 'completed' ? 'bg-status-success/10 text-status-success' : 'bg-status-error/10 text-status-error'}`}>
                            {job.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <button className="p-2 rounded-lg bg-surface border border-border-subtle text-text-muted hover:text-text-primary transition-all">
                            <Wand2 size={16} />
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
    </div>
  );
};
