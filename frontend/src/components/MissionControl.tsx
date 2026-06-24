import React, { useEffect, useState } from 'react';
import type { GravityContext } from '../types';
import { Cpu, Server, ShieldCheck, Activity, Zap, Database, RefreshCw, BrainCircuit, DollarSign } from 'lucide-react';
import { showToast } from './Toast';

export const MissionControl: React.FC = () => {
  const [ctx, setCtx] = useState<GravityContext | null>(null);
  const [loading, setLoading] = useState(false);
  
  const fetchCtx = async () => {
    setLoading(true);
    try {
      const res = await fetch('/v1/gravity/context');
      if (res.ok) setCtx(await res.json());
    } catch (e) {}
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchCtx();
    const iv = setInterval(fetchCtx, 10000);
    return () => clearInterval(iv);
  }, []);

  const releaseRam = async () => {
    if (!confirm("¿Deseas detener los motores pesados (Fooocus, Ollama, LM Studio, ComfyUI) para ahorrar RAM?")) return;
    setLoading(true);
    let successCount = 0;
    const enginesToKill = ['Fooocus', 'Ollama', 'LM Studio', 'ComfyUI'];
    
    try {
      for (const engine of enginesToKill) {
        const res = await fetch('/v1/ai/stop', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider: engine })
        });
        if (res.ok) {
          const data = await res.json();
          if (data.success) successCount++;
        }
      }
      
      showToast('success', `Operación completada. Se liberaron ${successCount} motores.`);
      await fetchCtx();
    } catch (e) {
      showToast('error', "Error de conexión con el bridge al intentar liberar RAM");
    } finally {
      setLoading(false);
    }
  };

  const Widget = ({ title, value, sub, icon: Icon, colorClass, delayIndex = 1 }: any) => (
    <div className={`glass-card p-6 flex flex-col group hover:scale-[1.03] transition-all duration-500 cursor-default stagger-${delayIndex}`}>
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-white/5 to-transparent rounded-full blur-2xl -mr-16 -mt-16 pointer-events-none"></div>
      <div className="flex items-center gap-4 mb-5 relative z-10">
        <div className={`p-3 rounded-xl bg-surface border border-border-subtle group-hover:border-${colorClass}/50 transition-all shadow-inner relative overflow-hidden`}>
          <div className={`absolute inset-0 bg-${colorClass}/10 opacity-0 group-hover:opacity-100 transition-opacity`}></div>
          <Icon size={24} className={`text-${colorClass} drop-shadow-[0_0_8px_rgba(currentColor,0.5)]`} />
        </div>
        <div className="text-[11px] font-black text-text-muted uppercase tracking-[0.2em]">{title}</div>
      </div>
      <div className="text-4xl font-black text-white mb-2 tracking-tight drop-shadow-md relative z-10">{value || '--'}</div>
      <div className="text-xs text-text-muted font-medium opacity-80 relative z-10">{sub}</div>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in duration-500">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header Section */}
        <div className="flex items-center justify-between stagger-1">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-primary/10 border border-accent-primary/20 text-accent-primary text-[10px] font-bold tracking-widest uppercase mb-3">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-pulse"></span>
              Live Telemetry
            </div>
            <h1 className="text-4xl font-black text-white tracking-tighter mb-2 drop-shadow-lg">Mission Control</h1>
            <p className="text-text-muted text-sm font-medium">Core systems monitoring powered by Gravity Brain V16.3</p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={fetchCtx}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2.5 glass-panel rounded-xl text-sm font-bold hover:bg-card hover:border-accent-primary transition-all shadow-md disabled:opacity-50"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Sync
            </button>
            <button 
              onClick={releaseRam}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2.5 bg-status-error/10 border border-status-error/30 text-status-error rounded-xl text-sm font-bold hover:bg-status-error hover:text-white transition-all shadow-[0_0_15px_rgba(239,68,68,0.15)]"
            >
              <Zap size={16} /> Free RAM
            </button>
            <button 
              onClick={() => window.dispatchEvent(new CustomEvent('navigate-panel', { detail: 'tools-pro' }))}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-accent-primary to-accent-secondary text-white rounded-xl text-sm font-bold shadow-[0_0_20px_rgba(168,85,247,0.4)] hover:scale-105 hover:shadow-[0_0_30px_rgba(168,85,247,0.6)] transition-all"
            >
              <BrainCircuit size={18} /> Advanced Tools
            </button>
          </div>
        </div>

        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <Widget 
            title="Motor Activo" 
            value={ctx?.active_provider || 'Auto'} 
            sub={`Modelo: ${ctx?.active_model || 'Detectando...'}`} 
            icon={BrainCircuit} colorClass="accent-primary" delayIndex={1}
          />
          <Widget 
            title="Video Studio" 
            value={ctx?.video?.pending_count || '0'} 
            sub="Render queue" 
            icon={Activity} colorClass="accent-tertiary" delayIndex={2}
          />
          <Widget 
            title="Tokens Sesión" 
            value={(ctx?.cost?.session_tokens || 0).toLocaleString()} 
            sub={`Coste: $${Number(ctx?.cost?.session_cost || 0).toFixed(4)}`} 
            icon={Database} colorClass="accent-secondary" delayIndex={3}
          />
          <Widget 
            title="Coste Hoy" 
            value={`$${Number(ctx?.cost?.daily_cost || 0).toFixed(2)}`} 
            sub="Dentro de límite" 
            icon={DollarSign} colorClass="status-warning" delayIndex={4}
          />
          <Widget 
            title="Seguridad" 
            value={ctx?.security_alerts === 0 ? 'Seguro' : ctx?.security_alerts} 
            sub={ctx?.security_alerts === 0 ? 'Sin alertas activas' : 'Atención requerida'} 
            icon={ShieldCheck} colorClass={ctx?.security_alerts === 0 ? "status-success" : "status-error"} delayIndex={5}
          />
          <Widget 
            title="CPU Usage" 
            value={`${ctx?.hardware?.cpu_percent || 0}%`} 
            sub="Carga global" 
            icon={Cpu} colorClass="accent-primary" delayIndex={6}
          />
        </div>

        {/* Services Status Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 stagger-5">
          <div>
            <h2 className="text-xs font-black text-text-muted uppercase tracking-[0.2em] mb-4">Estado de Servicios</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { id: 'bridge', name: 'Bridge Server', staticStatus: 'Puerto 7860', isOk: true },
                { id: 'Pollinations.ai', name: 'Pollinations.ai', isProvider: true, canStop: false },
                { id: 'Fooocus', name: 'Fooocus Motor', isProvider: true, canStop: true },
                { id: 'ComfyUI', name: 'MAI L2 (ComfyUI)', isProvider: true, canStop: true },
                { id: 'LM Studio', name: 'LM Studio', isProvider: true, canStop: true },
                { id: 'Ollama', name: 'Ollama', isProvider: true, canStop: true }
              ].map((srv) => {
                const prov = srv.isProvider ? ctx?.providers?.find((p:any) => p.name.toLowerCase().includes(srv.id.toLowerCase())) : null;
                const isHealthy = srv.staticStatus ? srv.isOk : prov?.healthy;
                const statusText = srv.staticStatus || (isHealthy ? 'En Línea' : (ctx ? 'Offline' : 'Verificando...'));
                
                return (
                  <div key={srv.id} className="glass-card p-4 flex items-center justify-between gap-4 group">
                    <div className="flex items-center gap-4">
                      <div className={`w-2.5 h-2.5 rounded-full ${isHealthy ? 'bg-status-success shadow-[0_0_10px_var(--color-status-success)] animate-blink' : 'bg-status-error/50 shadow-[0_0_10px_var(--color-status-error)]'}`}></div>
                      <div>
                        <div className="text-sm font-bold text-white tracking-wide">{srv.name}</div>
                        <div className="text-[10px] text-text-muted font-medium uppercase tracking-wider">{statusText} {prov?.latency_ms ? `(${prov.latency_ms}ms)` : ''}</div>
                      </div>
                    </div>
                    {srv.canStop && isHealthy && (
                      <button 
                        onClick={() => {
                           if(confirm(`¿Detener ${srv.name}?`)) {
                             fetch('/v1/ai/stop', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({provider: srv.id}) }).then(() => fetchCtx());
                           }
                        }}
                        className="px-3 py-1.5 text-[10px] uppercase font-black tracking-widest text-status-error bg-status-error/10 hover:bg-status-error hover:text-white hover:shadow-[0_0_15px_rgba(239,68,68,0.4)] rounded-lg transition-all opacity-0 group-hover:opacity-100"
                      >
                        Kill
                      </button>
                    )}
                    {srv.canStop && !isHealthy && ctx && (
                      <button 
                        onClick={() => {
                           if(confirm(`¿RUN ${srv.name}?`)) {
                             fetch('/v1/ai/start', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({provider: srv.id}) }).then(() => fetchCtx());
                           }
                        }}
                        className="px-3 py-1.5 text-[10px] uppercase font-black tracking-widest text-status-success bg-status-success/10 hover:bg-status-success hover:text-white hover:shadow-[0_0_15px_rgba(16,185,129,0.4)] rounded-lg transition-all opacity-0 group-hover:opacity-100"
                      >
                        Start
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div>
            <h2 className="text-xs font-black text-text-muted uppercase tracking-[0.2em] mb-4">Control de Recursos</h2>
            <div className="glass-panel p-8 rounded-2xl relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-status-error/10 to-transparent opacity-50 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="flex items-center justify-between gap-6 relative z-10">
                <div className="flex-1">
                  <div className="text-lg font-black text-white flex items-center gap-3 tracking-tight">
                    <div className="p-2 bg-status-error/20 rounded-lg text-status-error"><Zap size={20} /></div> 
                    Liberación de RAM
                  </div>
                  <p className="text-sm text-text-muted mt-3 font-medium leading-relaxed">Detén motores pesados como <strong>Fooocus</strong> o <strong>Ollama</strong> en un solo click para optimizar el rendimiento global.</p>
                </div>
                <button 
                  onClick={releaseRam}
                  className="px-8 py-4 bg-status-error text-white rounded-xl text-sm font-black uppercase tracking-[0.1em] hover:scale-105 active:scale-95 transition-all shadow-[0_0_30px_rgba(239,68,68,0.4)] border border-status-error/50"
                >
                  PURGE
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Activity Log Placeholder */}
        <div className="glass-panel rounded-2xl p-6 relative overflow-hidden stagger-6">
          <div className="absolute top-0 right-0 w-64 h-64 bg-accent-primary/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none"></div>
          <div className="flex items-center gap-3 mb-6 relative z-10">
            <div className="p-2 bg-accent-primary/10 rounded-lg border border-accent-primary/20"><Server className="text-accent-primary" size={20} /></div>
            <h2 className="text-xl font-black text-white tracking-tight">System Events</h2>
          </div>
          <div className="flex flex-col gap-3 relative z-10">
            {[1,2,3].map(i => (
              <div key={i} className="flex items-center gap-4 p-4 rounded-xl glass-card">
                <div className="text-xs text-text-muted font-mono w-24">10:42:{10+i} AM</div>
                <div className="flex-1 text-sm text-text-primary font-medium">Sincronización neural completada con Gravity Brain V16.3 PRO.</div>
                <div className="px-3 py-1 rounded-md bg-status-success/15 border border-status-success/30 text-status-success text-[10px] font-black uppercase tracking-widest shadow-[0_0_10px_rgba(16,185,129,0.1)]">OK</div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
