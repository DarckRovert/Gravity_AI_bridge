import { useEffect, useState } from 'react';
import { Layers, Image as ImageIcon, Trash2, Clock, CheckCircle2, RefreshCw, Eye } from 'lucide-react';
import { showToast } from './Toast';
import { BRIDGE_BASE } from '../config';

export const ImageQueue = () => {
  const [queue, setQueue] = useState<any[]>([]);

  const fetchQueue = async () => {
    try {
      const res = await fetch('/v1/queue');
      if (res.ok) {
        const data = await res.json();
        let allJobs: any[] = [];
        
        if (data.current_job) {
          allJobs.push({ ...data.current_job, id: String(data.current_job.id) });
        }
        if (data.pending_jobs) {
          allJobs = allJobs.concat(data.pending_jobs.map((j: any) => ({ ...j, id: String(j.id) })));
        }
        if (data.history) {
          allJobs = allJobs.concat(data.history.map((j: any) => {
            let url = null;
            if (j.status === 'done' && j.result_json) {
              try {
                const resJson = JSON.parse(j.result_json);
                if (resJson.success && resJson.images && resJson.images.length > 0) {
                  const pathStr = resJson.images[0].replace(/\\/g, '/');
                  const parts = pathStr.split('/outputs/');
                  if (parts.length > 1) {
                    url = '/static/output/' + parts[1];
                  }
                }
              } catch(e) {}
            }
            return { 
              ...j, 
              id: String(j.id), 
              status: j.status === 'done' ? 'completed' : j.status,
              engine: j.performance || 'Fooocus',
              url 
            };
          }));
        }
        setQueue(allJobs);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchQueue();
    const iv = setInterval(fetchQueue, 3000);
    return () => clearInterval(iv);
  }, []);

  const cancelJob = async (id: string) => {
    try {
      await fetch(`/v1/queue/cancel?id=${id}`, { method: 'POST' });
      fetchQueue();
    } catch (e) {}
  };

  const deleteJob = async (id: string) => {
    try {
      await fetch(`/v1/queue/delete?id=${id}`, { method: 'POST' });
      fetchQueue();
    } catch (e) {}
  };

  const clearHistory = async () => {
    try {
      await fetch('/v1/queue/clear_history', { method: 'POST' });
      fetchQueue();
    } catch (e) {}
  };

  const activeJobs = queue.filter(
    (job) => job.status !== 'completed' && job.status !== 'failed' && job.status !== 'cancelled'
  );

  const historyJobs = queue.filter(
    (job) => job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled'
  );

  const renderJobCard = (job: any, i: number, isHistory: boolean) => (
    <div key={i} className="glass-panel p-5 rounded-2xl border border-border-subtle flex items-center justify-between group">
       <div className="flex items-center gap-6">
          <div className="w-12 h-12 rounded-xl bg-surface border border-border-subtle flex items-center justify-center text-text-muted">
             {job.status === 'completed' ? <CheckCircle2 className="text-status-success" size={24} /> : 
              job.status === 'failed' ? <Trash2 className="text-status-error" size={24} /> : 
              job.status === 'cancelled' ? <Trash2 className="text-text-muted" size={24} /> : 
              <RefreshCw className="animate-spin text-accent-primary" size={24} />}
          </div>
          <div>
             <div className="text-sm font-black text-text-primary uppercase tracking-tighter">Job #{String(job.id).substring(0, 8)}</div>
             <p className="text-[10px] text-text-muted mt-1 font-medium truncate max-w-md">{job.prompt}</p>
             <div className="flex items-center gap-3 mt-2">
                <span className="text-[9px] font-black text-accent-primary uppercase tracking-widest">{job.status}</span>
                <span className="text-[9px] font-bold text-text-muted px-1.5 py-0.5 rounded bg-surface border border-border-subtle">{job.engine || 'Fooocus'}</span>
             </div>
          </div>
       </div>
       <div className="flex gap-2">
          <button 
            onClick={() => job.status === 'completed' && job.url ? window.open(`${BRIDGE_BASE}${job.url}`, '_blank') : showToast('info', 'Vista previa no disponible o job en proceso')}
            className="p-2 rounded-lg bg-surface border border-border-subtle text-text-muted hover:text-text-primary transition-all"
          >
             <Eye size={16} />
          </button>
          <button 
           onClick={() => isHistory ? deleteJob(job.id) : cancelJob(job.id)}
           className="p-2 rounded-lg bg-surface border border-border-subtle text-text-muted hover:text-status-error transition-all"
           title={isHistory ? "Eliminar del historial" : "Cancelar tarea"}
          >
             <Trash2 size={16} />
          </button>
       </div>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle">
              <Layers className="text-accent-primary" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Image Queue</h1>
              <p className="text-text-muted mt-1 font-medium">Cola de renderizado asíncrono para Fooocus y motores locales.</p>
            </div>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-accent-primary/10 text-accent-primary border border-accent-primary/20 rounded-xl text-xs font-black uppercase tracking-widest">
             <Clock size={14} /> {activeJobs.length} {activeJobs.length === 1 ? 'Job' : 'Jobs'} en cola
          </div>
        </div>

        {/* Sección 1: Tareas Activas */}
        <div className="space-y-4">
           <h2 className="text-xs font-black text-text-primary uppercase tracking-widest opacity-80 flex items-center gap-2">
              <RefreshCw size={14} className="text-accent-primary animate-pulse" />
              Tareas Activas
           </h2>
           <div className="grid grid-cols-1 gap-4">
              {activeJobs.length > 0 ? activeJobs.map((job, i) => renderJobCard(job, i, false)) : (
                <div className="py-20 glass-panel rounded-2xl border border-border-subtle text-center text-text-muted flex flex-col items-center justify-center gap-3 opacity-40">
                   <ImageIcon size={48} />
                   <p className="text-xs font-bold uppercase tracking-widest">La cola de renderizado está vacía</p>
                </div>
              )}
           </div>
        </div>

        {/* Sección 2: Historial de Renderizado */}
        {historyJobs.length > 0 && (
           <div className="space-y-4 pt-6 border-t border-border-subtle/40">
              <div className="flex items-center justify-between">
                 <h2 className="text-xs font-black text-text-muted uppercase tracking-widest flex items-center gap-2">
                    <Layers size={14} />
                    Historial de Renderizado
                 </h2>
                 <button 
                   onClick={clearHistory}
                   className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface border border-border-subtle text-xs text-status-error hover:bg-status-error/10 transition-all font-bold"
                 >
                    <Trash2 size={12} /> Limpiar Historial
                 </button>
              </div>
              <div className="grid grid-cols-1 gap-4">
                 {historyJobs.map((job, i) => renderJobCard(job, i, true))}
              </div>
           </div>
        )}

      </div>
    </div>
  );
};
