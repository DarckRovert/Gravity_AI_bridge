import { useEffect, useState } from 'react';
import { Activity, Server, Database, Zap, ShieldCheck, Lock, Unlock, Cpu, Globe } from 'lucide-react';
import { showToast } from './Toast';

export const SystemStatus = () => {
  const [status, setStatus] = useState<any>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/v1/status');
      if (res.ok) {
        const data = await res.json().catch(() => null);
        if (data) setStatus(data);
      }
    } catch (e) {
      console.error('Error fetching system status:', e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const iv = setInterval(fetchStatus, 4000);
    return () => clearInterval(iv);
  }, []);

  const handleLockModel = async (provider: string, model: string, currentLocked: boolean) => {
    try {
      const res = await fetch('/v1/model/lock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          model,
          lock: !currentLocked
        })
      });
      if (res.ok) {
        await fetchStatus();
      } else {
        const errData = await res.json().catch(() => ({}));
        showToast('error', errData.error || 'Error al actualizar el bloqueo del modelo');
      }
    } catch (e: any) {
      showToast('error', `Error de red al bloquear modelo: ${e.message}`);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide bg-gradient-to-br from-bg via-bg/95 to-bg-surface/90 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3.5 rounded-2xl bg-surface/80 border border-border-subtle shadow-xl backdrop-blur-md">
              <Cpu className="text-accent-primary animate-pulse" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary bg-gradient-to-r from-text-primary via-text-primary to-accent-primary/80 bg-clip-text">
                Universal AI Model Hub
              </h1>
              <p className="text-text-muted mt-1 font-medium text-sm">
                Inspecciona modelos locales y cloud en tiempo real, monitorea la latencia y bloquea la IA activa del ecosistema.
              </p>
            </div>
          </div>

          {status?.model_locked && (
            <div className="flex items-center gap-2.5 px-4 py-2 rounded-2xl bg-status-warning/10 border border-status-warning/30 text-status-warning text-xs font-bold animate-pulse shadow-md">
              <Lock size={14} />
              <span>SISTEMA FIJADO A: {status?.active_model}</span>
            </div>
          )}
        </div>

        {/* Top Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
           <StatusCard 
             title="Core Version" 
             value={`V${status?.version || '15.1'}`} 
             icon={<Server size={20} />} 
             color="text-accent-primary" 
           />
           <StatusCard 
             title="Estatus de Red" 
             value={status?.bridge_online ? 'ONLINE' : 'OFFLINE'} 
             icon={<ShieldCheck size={20} />} 
             color="text-status-success" 
           />
           <StatusCard 
             title="Proveedor Activo" 
             value={status?.active_provider || 'Automático'} 
             icon={<Globe size={20} />} 
             color="text-accent-secondary" 
           />
           <StatusCard 
             title="Modelo Activo" 
             value={status?.active_model || 'Buscando...'} 
             icon={<Database size={20} />} 
             color="text-text-primary" 
             truncate
           />
        </div>

        {/* Models & Providers Inspection Grid */}
        <div className="space-y-6">
          <h2 className="text-lg font-black tracking-wider text-text-primary uppercase flex items-center gap-2">
            <Activity size={18} className="text-accent-primary" /> 
            Inspección de Servidores e Inteligencia
          </h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {status?.backends?.map((b: any, i: number) => {
              return (
                <div 
                  key={i} 
                  className={`relative overflow-hidden rounded-2xl border transition-all duration-300 flex flex-col justify-between shadow-lg hover:-translate-y-1 hover:shadow-2xl
                    ${b.healthy 
                      ? 'bg-surface/40 backdrop-blur-md border-border-subtle/80 hover:border-accent-primary/40' 
                      : 'bg-surface/10 border-border-subtle/25 opacity-70'}`}
                >
                  {/* Decorative background glow for healthy backends */}
                  {b.healthy && (
                    <div className="absolute -right-20 -top-20 w-44 h-44 rounded-full bg-accent-primary/5 blur-3xl pointer-events-none" />
                  )}

                  {/* Provider Card Top Details */}
                  <div className="p-6 space-y-4 flex-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-xl border ${b.healthy ? 'bg-accent-primary/10 border-accent-primary/20 text-accent-primary' : 'bg-surface border-border-subtle text-text-muted'}`}>
                          {b.category === 'local' ? <Cpu size={18} /> : <Globe size={18} />}
                        </div>
                        <div>
                          <h3 className="font-extrabold text-text-primary text-base flex items-center gap-2">
                            {b.name}
                            <span className="text-[10px] text-text-muted font-bold tracking-wider px-2 py-0.5 rounded-md bg-card border border-border-subtle uppercase">
                              {b.category}
                            </span>
                          </h3>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {b.healthy && (
                          <div className={`text-xs font-black px-2 py-1 rounded-lg border 
                            ${b.latency_ms < 500 ? 'text-status-success bg-status-success/5 border-status-success/20' : 
                              b.latency_ms < 2000 ? 'text-status-warning bg-status-warning/5 border-status-warning/20' : 
                              'text-status-error bg-status-error/5 border-status-error/20'}`}>
                            {b.latency_ms}ms
                          </div>
                        )}
                        <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[9px] font-black uppercase border 
                          ${b.healthy 
                            ? 'bg-status-success/15 text-status-success border-status-success/30 shadow-[0_0_8px_rgba(46,213,115,0.1)]' 
                            : 'bg-status-error/15 text-status-error border-status-error/30'}`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${b.healthy ? 'bg-status-success animate-pulse' : 'bg-status-error'}`} />
                          {b.healthy ? 'ONLINE' : 'OFFLINE'}
                        </span>
                      </div>
                    </div>

                    {/* Available Models List */}
                    {b.healthy ? (
                      <div className="space-y-3">
                        <div className="text-[11px] font-bold text-text-muted uppercase tracking-wider">
                          Modelos Disponibles ({b.models_count}):
                        </div>
                        <div className="flex flex-wrap gap-2 pt-1">
                          {b.models?.map((m: string, idx: number) => {
                            const isCurrentActive = status?.active_model === m && status?.active_provider === b.name;
                            const isLockedModel = status?.model_locked && isCurrentActive;

                            return (
                              <div
                                key={idx}
                                className={`group relative flex items-center gap-2 pl-3.5 pr-2.5 py-1.5 rounded-xl border text-xs font-extrabold transition-all duration-300
                                  ${isLockedModel
                                    ? 'bg-gradient-to-r from-status-warning/20 to-accent-primary/20 border-status-warning text-status-warning shadow-md'
                                    : isCurrentActive
                                      ? 'bg-accent-primary/15 border-accent-primary text-accent-primary shadow-[0_0_10px_rgba(168,85,247,0.15)]'
                                      : 'bg-card/60 hover:bg-card border-border-subtle hover:border-accent-primary/30 text-text-muted hover:text-text-primary cursor-pointer'}`}
                                onClick={() => handleLockModel(b.name, m, isLockedModel)}
                              >
                                <span>{m}</span>
                                {isLockedModel ? (
                                  <Lock size={12} className="text-status-warning shrink-0" />
                                ) : isCurrentActive ? (
                                  <Zap size={12} className="text-accent-primary shrink-0" />
                                ) : (
                                  <Unlock size={12} className="opacity-0 group-hover:opacity-100 text-text-muted shrink-0 transition-opacity" />
                                )}

                                {/* Hover tooltip for locked selection */}
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1 bg-surface border border-border-subtle text-[10px] text-text-primary rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-xl z-20">
                                  {isLockedModel ? 'Haga clic para desbloquear ruteo' : 'Fijar todo el sistema a este modelo'}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ) : (
                      <div className="py-4 text-xs font-semibold text-text-muted italic flex flex-col gap-2">
                        <span>Sin acceso a modelos de este proveedor.</span>
                        {b.name === 'Nvidia NIM' && (
                          <span className="text-[10px] text-accent-primary font-bold not-italic">
                            Configure su clave API en la sección de Configuración para desbloquear.
                          </span>
                        )}
                        {b.name === 'LM Studio' && (
                          <span className="text-[10px] text-accent-secondary font-bold not-italic">
                            Asegúrese de iniciar la aplicación local y verificar el puerto 1234.
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Footer message / info */}
                  {b.healthy && b.models_count > 0 && (
                    <div className="px-6 py-3 bg-surface/50 border-t border-border-subtle/30 flex items-center justify-between text-[10px] text-text-muted font-bold">
                      <span>AUTO-ROTACIÓN HABILITADA</span>
                      <span>{b.category === 'local' ? 'LATENCIA BAJA' : 'MODELOS CLOUD PRESET'}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
};

const StatusCard = ({ title, value, icon, color, truncate }: any) => (
  <div className="glass-panel p-6 rounded-2xl border border-border-subtle/80 bg-surface/40 backdrop-blur-md space-y-4 hover:shadow-xl hover:border-accent-primary/20 transition-all duration-300">
     <div className="flex items-center justify-between">
        <div className="text-text-muted">{icon}</div>
        <div className="w-2 h-2 rounded-full bg-status-success animate-pulse shadow-[0_0_8px_var(--color-status-success)]"></div>
     </div>
     <div>
        <div className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-1">{title}</div>
        <div className={`text-lg font-black ${color} ${truncate ? 'truncate' : ''}`} title={value}>
          {value}
        </div>
     </div>
  </div>
);
