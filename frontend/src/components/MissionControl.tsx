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
      const res = await fetch('http://localhost:7860/v1/gravity/context');
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
    if (!confirm("¿Deseas detener Fooocus para ahorrar RAM?")) return;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:7860/v1/ai/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: 'Fooocus' })
      });
      const data = await res.json();
      if (res.ok) {
        showToast('success', data.message || "RAM liberada correctamente.");
      } else {
        showToast('error', data.error || "Error al liberar RAM");
      }
      fetchCtx();
    } catch (e) {
      showToast('error', "Error de conexión con el bridge");
    } finally {
      setLoading(false);
    }
  };

  const Widget = ({ title, value, sub, icon: Icon, colorClass }: any) => (
    <div className="glass-card p-6 flex flex-col group hover:scale-[1.02] transition-all cursor-default">
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-2 rounded-lg bg-surface border border-border-subtle group-hover:border-${colorClass} transition-colors shadow-sm`}>
          <Icon size={20} className={`text-${colorClass}`} />
        </div>
        <div className="text-sm font-bold text-text-muted uppercase tracking-wider">{title}</div>
      </div>
      <div className="text-3xl font-extrabold text-text-primary mb-1">{value || '--'}</div>
      <div className="text-xs text-text-muted font-medium">{sub}</div>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in duration-500">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header Section */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-text-primary tracking-tight mb-2">Mission Control</h1>
            <p className="text-text-muted text-sm font-medium">Vista general del sistema en tiempo real gobernada por el Gravity Brain.</p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={fetchCtx}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-surface border border-border-subtle rounded-xl text-sm font-bold hover:bg-card hover:border-accent-primary transition-all shadow-md disabled:opacity-50"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Refrescar
            </button>
            <button 
              onClick={releaseRam}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-status-error/10 border border-status-error/20 text-status-error rounded-xl text-sm font-bold hover:bg-status-error hover:text-white transition-all shadow-md"
            >
              <Zap size={16} /> Liberar RAM
            </button>
            <button 
              onClick={() => window.dispatchEvent(new CustomEvent('navigate-panel', { detail: 'tools-pro' }))}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-accent-primary to-accent-secondary text-white rounded-xl text-sm font-bold shadow-[0_0_15px_rgba(168,85,247,0.3)] hover:scale-105 transition-all"
            >
              <BrainCircuit size={16} /> Advanced Tools
            </button>
          </div>
        </div>

        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <Widget 
            title="Motor Activo" 
            value={ctx?.active_provider || 'Auto-Routing'} 
            sub={`Modelo: ${ctx?.active_model || 'Detectando...'}`} 
            icon={BrainCircuit} colorClass="accent-primary" 
          />
          <Widget 
            title="Video Studio" 
            value={ctx?.video?.pending_count || '0'} 
            sub="Jobs de render en cola" 
            icon={Activity} colorClass="accent-tertiary" 
          />
          <Widget 
            title="Tokens Sesión" 
            value={(ctx?.cost?.session_tokens || 0).toLocaleString()} 
            sub={`Coste: $${Number(ctx?.cost?.session_cost || 0).toFixed(4)}`} 
            icon={Database} colorClass="accent-secondary" 
          />
          <Widget 
            title="Coste Hoy" 
            value={`$${Number(ctx?.cost?.daily_cost || 0).toFixed(2)}`} 
            sub="Límite no superado" 
            icon={DollarSign} colorClass="status-warning" 
          />
          <Widget 
            title="Seguridad" 
            value={ctx?.security_alerts === 0 ? 'Seguro' : ctx?.security_alerts} 
            sub={ctx?.security_alerts === 0 ? 'Sin alertas activas' : 'Atención requerida'} 
            icon={ShieldCheck} colorClass={ctx?.security_alerts === 0 ? "status-success" : "status-error"} 
          />
          <Widget 
            title="CPU Usage" 
            value={`${ctx?.hardware?.cpu_percent || 0}%`} 
            sub="Carga de procesamiento global" 
            icon={Cpu} colorClass="accent-primary" 
          />
        </div>

        {/* Services Status Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h2 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-4">Estado de Servicios</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { id: 'bridge', name: 'Bridge Server', staticStatus: 'Puerto 7860', isOk: true },
                { id: 'Pollinations.ai', name: 'Pollinations.ai', isProvider: true },
                { id: 'Fooocus', name: 'Fooocus Motor', isProvider: true, canStop: true },
                { id: 'LM Studio', name: 'LM Studio', isProvider: true, canStop: true },
                { id: 'Ollama', name: 'Ollama', isProvider: true, canStop: true }
              ].map((srv) => {
                const prov = srv.isProvider ? ctx?.providers?.find((p:any) => p.name.toLowerCase().includes(srv.id.toLowerCase())) : null;
                const isHealthy = srv.staticStatus ? srv.isOk : prov?.healthy;
                const statusText = srv.staticStatus || (isHealthy ? 'En Línea' : (ctx ? 'Offline' : 'Verificando...'));
                
                return (
                  <div key={srv.id} className="glass-card p-4 flex items-center justify-between gap-4 group">
                    <div className="flex items-center gap-4">
                      <div className={`w-3 h-3 rounded-full ${isHealthy ? 'bg-status-success shadow-[0_0_8px_var(--color-status-success)] animate-blink' : 'bg-status-error/50'}`}></div>
                      <div>
                        <div className="text-sm font-bold text-text-primary">{srv.name}</div>
                        <div className="text-[10px] text-text-muted uppercase">{statusText} {prov?.latency_ms ? `(${prov.latency_ms}ms)` : ''}</div>
                      </div>
                    </div>
                    {srv.canStop && isHealthy && (
                      <button 
                        onClick={() => {
                           if(confirm(`¿Detener ${srv.name}?`)) {
                             fetch('http://localhost:7860/v1/ai/stop', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({provider: srv.id}) }).then(() => fetchCtx());
                           }
                        }}
                        className="px-2 py-1 text-[10px] uppercase font-black tracking-widest text-status-error bg-status-error/10 hover:bg-status-error hover:text-white rounded transition-all opacity-0 group-hover:opacity-100"
                      >
                        Kill
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div>
            <h2 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-4">Gestión de Motores IA</h2>
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle bg-gradient-to-br from-status-error/5 to-transparent">
              <div className="flex items-center justify-between gap-6">
                <div className="flex-1">
                  <div className="text-sm font-bold text-text-primary flex items-center gap-2">
                    <Zap size={16} className="text-status-error" /> Liberación de RAM
                  </div>
                  <p className="text-xs text-text-muted mt-2">Detén motores pesados como <strong>Fooocus</strong> o <strong>Ollama</strong> cuando no los uses para optimizar el rendimiento global.</p>
                </div>
                <button 
                  onClick={releaseRam}
                  className="px-6 py-3 bg-status-error text-white rounded-xl text-sm font-black uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-[0_0_20px_rgba(239,68,68,0.3)]"
                >
                  Liberar Ahora
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Activity Log Placeholder */}
        <div className="glass-panel rounded-2xl p-6 border border-border-subtle">
          <div className="flex items-center gap-3 mb-6">
            <Server className="text-accent-primary" size={20} />
            <h2 className="text-lg font-bold text-text-primary">Actividad de Infraestructura</h2>
          </div>
          <div className="flex flex-col gap-3">
            {[1,2,3].map(i => (
              <div key={i} className="flex items-center gap-4 p-3 rounded-xl bg-card border border-border-subtle">
                <div className="text-xs text-text-muted font-mono w-20">10:42:{10+i} AM</div>
                <div className="flex-1 text-sm text-text-primary">Servicio base sincronizado con Gravity Brain V12.</div>
                <div className="px-2 py-1 rounded bg-status-success/10 text-status-success text-[10px] font-bold">INFO</div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
