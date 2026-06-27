import { useEffect, useState } from 'react';
import { Shield, Eye, AlertTriangle, CheckCircle2, Terminal, Zap, RefreshCw, Cpu } from 'lucide-react';
import { showToast } from './Toast';

export const Watchdog = () => {
  const [data, setData] = useState<any>(null);

  const fetchWatchdog = async (isManual = false) => {
    try {
      const res = await fetch('/v1/watchdog');
      if (!res.ok) {
        if (isManual) throw new Error('El orquestador del Watchdog rechazó la conexión');
        return;
      }
      const json = await res.json().catch(() => null);
      if (json) {
        setData(json);
        if (isManual) showToast('success', 'Diagnóstico de Watchdog actualizado exitosamente');
      } else if (isManual) {
        throw new Error('Respuesta corrupta del sistema');
      }
    } catch (e: any) {
      if (isManual) showToast('error', `Fallo de Telemetría: ${e.message}`);
    }
  };

  useEffect(() => {
    fetchWatchdog();
    const iv = setInterval(() => fetchWatchdog(false), 5000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle shadow-[0_0_20px_rgba(34,197,94,0.1)]">
              <Eye className="text-status-success" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Engine Watchdog</h1>
              <p className="text-text-muted mt-1 font-medium">Auto-recuperación de procesos y monitor de salud del motor de inferencia.</p>
            </div>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-status-success/10 text-status-success border border-status-success/20 rounded-xl text-xs font-black uppercase tracking-widest">
             <Shield size={14} /> Sentinel Active
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
           
           <div className="lg:col-span-2 space-y-6">
              <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
                 <h3 className="text-sm font-black text-text-primary uppercase tracking-widest flex items-center gap-2 mb-6">
                    <Terminal size={18} className="text-accent-primary" /> Incidentes Recientes
                 </h3>
                 <div className="space-y-4">
                    {data?.events?.length > 0 ? data.events.map((ev: any, i: number) => (
                      <div key={i} className="p-4 rounded-xl bg-surface border border-border-subtle flex items-start gap-4">
                         <div className={`mt-1 p-1.5 rounded-lg ${ev.level === 'CRITICAL' ? 'bg-status-error/10 text-status-error' : 'bg-status-success/10 text-status-success'}`}>
                            {ev.level === 'CRITICAL' ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
                         </div>
                         <div className="flex-1">
                            <div className="flex justify-between">
                               <span className="text-xs font-black text-text-primary uppercase tracking-tighter">{ev.title}</span>
                               <span className="text-[10px] font-bold text-text-muted">{ev.timestamp}</span>
                            </div>
                            <p className="text-[11px] text-text-muted mt-1 leading-relaxed">{ev.description}</p>
                         </div>
                      </div>
                    )) : (
                      <div className="py-12 text-center text-text-muted opacity-30 flex flex-col items-center gap-2">
                         <Zap size={32} />
                         <span className="text-xs font-bold uppercase tracking-widest">No se registran fallos en los motores</span>
                      </div>
                    )}
                 </div>
              </div>

              <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
                 <h3 className="text-sm font-black text-text-primary uppercase tracking-widest flex items-center gap-2 mb-6">
                    <Cpu size={18} className="text-accent-secondary" /> Puntos de Control (Checkpoints)
                 </h3>
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Checkpoint label="Model Load Integrity" ok={data?.checkpoints?.model_integrity ?? true} />
                    <Checkpoint label="VRAM Garbage Collection" ok={data?.checkpoints?.vram_gc ?? true} />
                    <Checkpoint label="Socket Heartbeat" ok={data?.checkpoints?.socket_heartbeat ?? (data?.status === 'ok')} />
                    <Checkpoint label="Worker Pool Sync" ok={data?.checkpoints?.worker_pool ?? true} />
                 </div>
              </div>
           </div>

           <div className="space-y-6">
              <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
                 <h3 className="text-sm font-black text-text-primary uppercase tracking-widest">Auto-Heal Strategy</h3>
                 <div className="space-y-4">
                    <div className="p-4 rounded-xl bg-accent-primary/5 border border-accent-primary/10">
                       <div className="text-xs font-black text-accent-primary uppercase tracking-widest mb-2">MODO ACTUAL</div>
                       <div className="text-lg font-black text-text-primary">RESTART_ON_FREEZE</div>
                       <p className="text-[10px] text-text-muted mt-2">Si un provider no responde en 45s, se reinicia el socket y se marca como "Degradado".</p>
                    </div>
                    {data?.active_provider && (
                      <div className="p-4 rounded-xl bg-surface border border-border-subtle">
                        <div className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-1">Proveedor Activo</div>
                        <div className="text-sm font-black text-text-primary">{data.active_provider}</div>
                        <div className="text-[10px] font-bold text-accent-secondary mt-1 truncate">{data.active_model}</div>
                      </div>
                    )}
                    <button 
                      onClick={() => fetchWatchdog(true)}
                      className="w-full py-3 rounded-xl bg-surface border border-border-subtle text-xs font-black text-text-muted hover:text-text-primary transition-all flex items-center justify-center gap-2"
                    >
                       <RefreshCw size={14} /> Forzar Re-escaneo
                    </button>
                 </div>
              </div>
           </div>

        </div>

      </div>
    </div>
  );
};

const Checkpoint = ({ label, ok }: any) => (
  <div className="p-4 rounded-xl bg-surface border border-border-subtle flex items-center justify-between">
     <span className="text-xs font-bold text-text-muted">{label}</span>
     <div className={`w-2 h-2 rounded-full ${ok ? 'bg-status-success shadow-[0_0_10px_rgba(34,197,94,0.5)]' : 'bg-status-error'}`}></div>
  </div>
);
