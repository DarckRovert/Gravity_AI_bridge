import { useEffect, useState } from 'react';
import { Layers, Image as ImageIcon, Trash2, Clock, CheckCircle2, RefreshCw, Eye } from 'lucide-react';

export const ImageQueue = () => {
  const [queue, setQueue] = useState<any[]>([]);

  const fetchQueue = async () => {
    try {
      const res = await fetch('http://localhost:7860/v1/queue');
      if (res.ok) {
        const data = await res.json();
        setQueue(data.queue || []);
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
      await fetch(`http://localhost:7860/v1/queue/cancel?id=${id}`, { method: 'POST' });
      fetchQueue();
    } catch (e) {}
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
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
             <Clock size={14} /> {queue.length} Jobs en cola
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4">
           {queue.length > 0 ? queue.map((job, i) => (
             <div key={i} className="glass-panel p-5 rounded-2xl border border-border-subtle flex items-center justify-between group">
                <div className="flex items-center gap-6">
                   <div className="w-12 h-12 rounded-xl bg-surface border border-border-subtle flex items-center justify-center text-text-muted">
                      {job.status === 'completed' ? <CheckCircle2 className="text-status-success" size={24} /> : <RefreshCw className="animate-spin text-accent-primary" size={24} />}
                   </div>
                   <div>
                      <div className="text-sm font-black text-text-primary uppercase tracking-tighter">Job #{job.id?.substring(0, 8)}</div>
                      <p className="text-[10px] text-text-muted mt-1 font-medium truncate max-w-md">{job.prompt}</p>
                      <div className="flex items-center gap-3 mt-2">
                         <span className="text-[9px] font-black text-accent-primary uppercase tracking-widest">{job.status}</span>
                         <span className="text-[9px] font-bold text-text-muted px-1.5 py-0.5 rounded bg-surface border border-border-subtle">{job.engine || 'Fooocus'}</span>
                      </div>
                   </div>
                </div>
                <div className="flex gap-2">
                   <button 
                     onClick={() => job.status === 'completed' && job.url ? window.open(`http://localhost:7860${job.url}`, '_blank') : alert('Vista previa no disponible o job en proceso')}
                     className="p-2 rounded-lg bg-surface border border-border-subtle text-text-muted hover:text-text-primary transition-all"
                   >
                      <Eye size={16} />
                   </button>
                   <button 
                    onClick={() => cancelJob(job.id)}
                    className="p-2 rounded-lg bg-surface border border-border-subtle text-text-muted hover:text-status-error transition-all"
                   >
                      <Trash2 size={16} />
                   </button>
                </div>
             </div>
           )) : (
             <div className="py-32 text-center text-text-muted flex flex-col items-center gap-4 opacity-30">
                <ImageIcon size={64} />
                <p className="text-sm font-bold uppercase tracking-widest">La cola de renderizado está vacía</p>
             </div>
           )}
        </div>

      </div>
    </div>
  );
};
