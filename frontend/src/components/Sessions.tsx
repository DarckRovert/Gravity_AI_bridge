import { useEffect, useState } from 'react';
import { History, Save, Play, Trash2, Clock, Terminal, ChevronRight, Zap } from 'lucide-react';

export const Sessions = () => {
  const [sessions, setSessions] = useState<any[]>([]);
  const [active, setActive] = useState<any[]>([]);

  const fetchData = async () => {
    try {
      const [sRes, aRes] = await Promise.all([
        fetch('/v1/sessions'),
        fetch('/v1/sessions/active')
      ]);
      if (sRes.ok) {
        const data = await sRes.json();
        setSessions(data.sessions || []);
      }
      if (aRes.ok) {
        const data = await aRes.json();
        setActive(data.active_sessions || []);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchData();
    const iv = setInterval(fetchData, 10000);
    return () => clearInterval(iv);
  }, []);

  const spawnSession = async (id: string) => {
     try {
       await fetch('/v1/sessions/spawn', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ session_id: id })
       });
       fetchData();
     } catch (e) { alert('Error al levantar worker'); }
  };

  const deleteSession = async (id: string) => {
    if (!confirm(`¿Eliminar la sesión ${id} permanentemente?`)) return;
    try {
      await fetch('/v1/sessions/kill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: id })
      });
      fetchData();
    } catch (e) {
      alert('Error al matar sesión');
    }
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-7xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle">
              <History className="text-accent-secondary" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Session Manager</h1>
              <p className="text-text-muted mt-1 font-medium">Gestión de persistencia y procesos paralelos de conversación.</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
               <div className="p-6 border-b border-border-subtle bg-surface/30 flex justify-between items-center">
                  <h3 className="font-bold text-text-primary flex items-center gap-2"><Save size={18} className="text-accent-secondary" /> Historial de Guardados</h3>
               </div>
               <div className="divide-y divide-border-subtle/30">
                  {sessions.length > 0 ? sessions.map((s, i) => (
                    <div key={i} className="p-5 flex items-center justify-between hover:bg-accent-secondary/5 transition-all group">
                       <div className="flex items-center gap-4">
                          <div className="p-2 rounded-lg bg-surface border border-border-subtle text-text-muted">
                             <Clock size={16} />
                          </div>
                          <div>
                             <div className="text-sm font-black text-text-primary uppercase tracking-tighter">{s.name}</div>
                             <div className="text-[10px] font-bold text-text-muted flex items-center gap-3">
                                <span>{s.saved_at}</span>
                                <span className="flex items-center gap-1"><ChevronRight size={10} /> Branch: {s.branch}</span>
                                <span className="flex items-center gap-1"><Zap size={10} className="text-accent-secondary" /> {s.turns} Turnos</span>
                             </div>
                          </div>
                       </div>
                       <div className="flex gap-2">
                          <button 
                            onClick={() => spawnSession(s.name)}
                            className="p-2 rounded-lg bg-accent-secondary text-white shadow-lg hover:scale-110 transition-all opacity-0 group-hover:opacity-100"
                          >
                             <Play size={16} fill="currentColor" />
                          </button>
                          <button 
                            onClick={() => deleteSession(s.name)}
                            className="p-2 rounded-lg bg-surface border border-border-subtle text-text-muted hover:text-status-error transition-all"
                          >
                             <Trash2 size={16} />
                          </button>
                       </div>
                    </div>
                  )) : (
                    <div className="p-20 text-center text-text-muted text-xs font-bold uppercase tracking-widest opacity-30">No hay sesiones guardadas</div>
                  )}
               </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
              <h3 className="text-xs font-black text-text-primary uppercase tracking-widest mb-6 flex items-center gap-2">
                 <Terminal size={16} className="text-status-success" /> Procesos Activos (Workers)
              </h3>
              <div className="space-y-3">
                {active.map((s, i) => (
                  <div key={i} className="p-4 rounded-xl bg-status-success/5 border border-status-success/20 flex items-center justify-between">
                     <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-status-success animate-pulse"></div>
                        <div className="text-xs font-bold text-text-primary">{s.id}</div>
                     </div>
                     <div className="text-[10px] font-black text-text-muted">PID: {s.pid}</div>
                  </div>
                ))}
                {active.length === 0 && (
                  <div className="py-12 text-center text-[10px] font-bold text-text-muted uppercase tracking-widest opacity-50">
                    No hay workers activos
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
