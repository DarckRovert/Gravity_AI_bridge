import { useEffect, useState } from 'react';
import { 
  Shield, Eye, AlertTriangle, Terminal, Zap, RefreshCw, Cpu, 
  Trash2, ShieldCheck, Activity, Settings, Info
} from 'lucide-react';
import { showToast } from './Toast';

export const Watchdog = () => {
  const [engineData, setEngineData] = useState<any>(null);
  const [resourceData, setResourceData] = useState<any>(null);
  const [isCleaning, setIsCleaning] = useState(false);
  const [timeoutInput, setTimeoutInput] = useState<string>('');
  const [ramInput, setRamInput] = useState<string>('');

  const fetchData = async (isManual = false) => {
    try {
      const [engRes, resRes] = await Promise.all([
        fetch('/v1/watchdog'),
        fetch('/v1/resource_watchdog')
      ]);
      
      if (engRes.ok) {
        const engJson = await engRes.json().catch(() => null);
        if (engJson) setEngineData(engJson);
      }
      if (resRes.ok) {
        const resJson = await resRes.json().catch(() => null);
        if (resJson) {
          setResourceData(resJson);
          setTimeoutInput((resJson.idle_timeout_seconds / 60).toString());
          setRamInput(resJson.ram_threshold.toString());
        }
      }
      
      if (isManual) {
        showToast('success', 'Telemetría de Sentinel actualizada correctamente');
      }
    } catch (e: any) {
      if (isManual) showToast('error', `Fallo de Telemetría: ${e.message}`);
    }
  };

  const handleClean = async () => {
    setIsCleaning(true);
    try {
      const res = await fetch('/v1/resource_watchdog/clean', { method: 'POST' });
      if (res.ok) {
        const json = await res.json().catch(() => ({ killed: 0 }));
        showToast('success', `Limpieza exitosa. Procesos terminados: ${json.killed}`);
        fetchData();
      } else {
        showToast('error', 'Error ejecutando limpieza de procesos');
      }
    } catch (e) {
      showToast('error', 'Fallo de conexión');
    } finally {
      setIsCleaning(false);
    }
  };

  const handleSaveConfig = async () => {
    try {
      const res = await fetch('/v1/resource_watchdog/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idle_timeout_seconds: parseInt(timeoutInput) * 60,
          ram_threshold: parseFloat(ramInput)
        })
      });
      if (res.ok) {
        showToast('success', 'Configuración de Watchdog actualizada');
        fetchData();
      } else {
        showToast('error', 'Error guardando configuración');
      }
    } catch (e) {
      showToast('error', 'Fallo de conexión');
    }
  };

  useEffect(() => {
    fetchData();
    const iv = setInterval(() => fetchData(false), 5000);
    return () => clearInterval(iv);
  }, []);

  const idlePercent = resourceData 
    ? Math.min(100, Math.round((resourceData.idle_duration / resourceData.idle_timeout_seconds) * 100))
    : 0;

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle shadow-[0_0_20px_rgba(34,197,94,0.1)]">
              <Shield className="text-status-success animate-pulse" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Sentinel Daemon</h1>
              <p className="text-text-muted mt-1 font-medium">Orquestador de auto-recuperación de modelos y optimización dinámica de RAM/VRAM.</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-4 py-2 bg-status-success/10 text-status-success border border-status-success/20 rounded-xl text-xs font-black uppercase tracking-widest">
              <Eye size={14} /> Active Systems
            </div>
            <button 
              onClick={() => fetchData(true)}
              className="p-2.5 rounded-xl bg-surface border border-border-subtle text-text-muted hover:text-text-primary transition-all"
              title="Actualizar telemetría"
            >
              <RefreshCw size={18} />
            </button>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Left Column: Engine Sentinel */}
          <div className="space-y-8">
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
              <div className="flex justify-between items-center border-b border-border-subtle pb-4">
                <h3 className="text-sm font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                  <Activity size={18} className="text-accent-primary" /> Engine Sentinel
                </h3>
                <span className={`text-[10px] font-black uppercase px-2 py-1 rounded-md ${
                  engineData?.status === 'ok' ? 'bg-status-success/10 text-status-success' : 'bg-status-warning/10 text-status-warning'
                }`}>
                  {engineData?.status === 'ok' ? 'Online' : 'Degraded'}
                </span>
              </div>

              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-accent-primary/5 border border-accent-primary/10">
                  <div className="text-xs font-black text-accent-primary uppercase tracking-widest mb-2">Auto-Heal Action</div>
                  <div className="text-md font-bold text-text-primary">RESTART_ON_FREEZE</div>
                  <p className="text-[10px] text-text-muted mt-2">Si un backend de inferencia falla en responder en 45s, se reinicia el socket y se marca temporalmente como Degradado.</p>
                </div>

                {engineData?.active_provider && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-surface border border-border-subtle">
                      <div className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-1">Activo</div>
                      <div className="text-sm font-bold text-text-primary truncate">{engineData.active_provider}</div>
                    </div>
                    <div className="p-4 rounded-xl bg-surface border border-border-subtle">
                      <div className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-1">Modelo Seleccionado</div>
                      <div className="text-sm font-bold text-text-primary truncate">{engineData.active_model}</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Checkpoints */}
              <div className="space-y-4">
                <h4 className="text-xs font-black text-text-muted uppercase tracking-widest">Inference Checkpoints</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <Checkpoint label="Inference Engine Integrity" ok={engineData?.checkpoints?.model_integrity ?? true} />
                  <Checkpoint label="VRAM Garbage Collection" ok={engineData?.checkpoints?.vram_gc ?? true} />
                  <Checkpoint label="API Socket Heartbeat" ok={engineData?.checkpoints?.socket_heartbeat ?? (engineData?.status === 'ok')} />
                  <Checkpoint label="Thread Worker Sync" ok={engineData?.checkpoints?.worker_pool ?? true} />
                </div>
              </div>
            </div>

            {/* Recent Logs & Incidents */}
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
              <h3 className="text-sm font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                <Terminal size={18} className="text-accent-secondary" /> Incidentes Recientes del Sistema
              </h3>
              <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2 scrollbar-hide">
                {engineData?.events?.length > 0 ? (
                  engineData.events.map((ev: any, i: number) => (
                    <div key={i} className="p-4 rounded-xl bg-surface border border-border-subtle flex items-start gap-4">
                      <div className={`mt-1 p-1.5 rounded-lg ${
                        ev.level === 'CRITICAL' ? 'bg-status-error/10 text-status-error' : 'bg-status-warning/10 text-status-warning'
                      }`}>
                        <AlertTriangle size={14} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-center gap-2">
                          <span className="text-xs font-black text-text-primary uppercase tracking-tighter truncate">{ev.title}</span>
                          <span className="text-[9px] font-bold text-text-muted shrink-0">{(ev.timestamp || '').split('T')[1]?.substring(0, 8) || ev.timestamp}</span>
                        </div>
                        <p className="text-[10px] text-text-muted mt-1 leading-relaxed break-all">{ev.description}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-12 text-center text-text-muted opacity-30 flex flex-col items-center gap-2">
                    <Zap size={28} />
                    <span className="text-xs font-bold uppercase tracking-widest">Inferencia Saludable</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Resource Sentinel (Memory Optimizer) */}
          <div className="space-y-8">
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
              <div className="flex justify-between items-center border-b border-border-subtle pb-4">
                <h3 className="text-sm font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                  <Cpu size={18} className="text-status-success" /> Resource Sentinel
                </h3>
                <span className={`text-[10px] font-black uppercase px-2 py-1 rounded-md ${
                  resourceData?.running ? 'bg-status-success/10 text-status-success animate-pulse' : 'bg-status-error/10 text-status-error'
                }`}>
                  {resourceData?.running ? 'Auto-Clean Active' : 'Off'}
                </span>
              </div>

              {/* Memory Telemetry */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-surface border border-border-subtle space-y-2">
                  <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">Uso de RAM</span>
                  <div className="flex items-end justify-between">
                    <span className="text-2xl font-black text-text-primary">{resourceData?.current_ram ?? 0}%</span>
                    <span className="text-[10px] text-text-muted mb-1 font-bold">Umbral: {resourceData?.ram_threshold}%</span>
                  </div>
                  <div className="w-full bg-border-subtle h-2 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-500 ${
                        (resourceData?.current_ram ?? 0) > (resourceData?.ram_threshold ?? 75) ? 'bg-status-error' : 'bg-status-success'
                      }`}
                      style={{ width: `${resourceData?.current_ram ?? 0}%` }}
                    />
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-surface border border-border-subtle space-y-2">
                  <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">Uso de Swap</span>
                  <div className="flex items-end justify-between">
                    <span className="text-2xl font-black text-text-primary">{resourceData?.current_swap ?? 0}%</span>
                    <span className="text-[10px] text-text-muted mb-1 font-bold">Umbral: {resourceData?.swap_threshold}%</span>
                  </div>
                  <div className="w-full bg-border-subtle h-2 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-500 ${
                        (resourceData?.current_swap ?? 0) > (resourceData?.swap_threshold ?? 90) ? 'bg-status-error' : 'bg-status-success'
                      }`}
                      style={{ width: `${resourceData?.current_swap ?? 0}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Idle Time Progress Bar */}
              <div className="p-4 rounded-xl bg-surface border border-border-subtle space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-black text-text-muted uppercase tracking-widest flex items-center gap-1.5">
                    <Info size={12} className="text-accent-secondary" /> Tiempo de Inactividad (Idle)
                  </span>
                  <span className="text-xs font-bold text-text-primary">
                    {resourceData ? Math.floor(resourceData.idle_duration / 60) : 0}m / {resourceData ? Math.floor(resourceData.idle_timeout_seconds / 60) : 0}m
                  </span>
                </div>
                <div className="w-full bg-border-subtle h-3 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-accent-secondary transition-all duration-500 shadow-[0_0_10px_rgba(0,191,255,0.3)]"
                    style={{ width: `${idlePercent}%` }}
                  />
                </div>
                <p className="text-[9px] text-text-muted leading-relaxed font-semibold">
                  Al recibir chats o ejecutar videos, este contador se reinicia. Tras {resourceData ? Math.floor(resourceData.idle_timeout_seconds / 60) : 30}m inactivo con RAM alta, se limpian los procesos.
                </p>
              </div>

              {/* White/Black lists */}
              <div className="grid grid-cols-2 gap-4 text-xs font-bold">
                <div className="space-y-2">
                  <span className="text-[10px] font-black text-status-success uppercase tracking-widest flex items-center gap-1">
                    <ShieldCheck size={12} /> Excluidos (Inmunes)
                  </span>
                  <div className="p-3 bg-surface border border-border-subtle rounded-xl space-y-1 text-text-muted">
                    {resourceData?.protected_keywords?.map((kw: string, i: number) => (
                      <div key={i} className="flex items-center gap-1.5">
                        <div className="w-1 h-1 rounded-full bg-status-success" />
                        <span className="capitalize">{kw}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <span className="text-[10px] font-black text-status-error uppercase tracking-widest flex items-center gap-1">
                    <Trash2 size={12} /> Monitoreados
                  </span>
                  <div className="p-3 bg-surface border border-border-subtle rounded-xl space-y-1 text-text-muted">
                    {resourceData?.target_keywords?.map((kw: string, i: number) => (
                      <div key={i} className="flex items-center gap-1.5">
                        <div className="w-1 h-1 rounded-full bg-status-error" />
                        <span className="capitalize">{kw}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <button
                  onClick={handleClean}
                  disabled={isCleaning}
                  className="flex-1 py-3 rounded-xl bg-status-error/15 border border-status-error/30 text-xs font-black text-status-error hover:bg-status-error/25 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                >
                  <Trash2 size={14} /> {isCleaning ? 'Limpiando...' : 'Forzar Liberación de RAM/VRAM'}
                </button>
              </div>
            </div>

            {/* Configuration Sentinel Panel */}
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
              <h3 className="text-sm font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                <Settings size={18} className="text-text-muted" /> Configuración de Resource Watchdog
              </h3>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-text-muted uppercase tracking-widest">Inactividad (Minutos)</label>
                    <input 
                      type="number" 
                      value={timeoutInput}
                      onChange={(e) => setTimeoutInput(e.target.value)}
                      className="w-full px-4 py-2.5 bg-surface border border-border-subtle rounded-xl text-sm font-bold text-text-primary focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-text-muted uppercase tracking-widest">Límite RAM (%)</label>
                    <input 
                      type="number" 
                      value={ramInput}
                      onChange={(e) => setRamInput(e.target.value)}
                      className="w-full px-4 py-2.5 bg-surface border border-border-subtle rounded-xl text-sm font-bold text-text-primary focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                </div>
                <button
                  onClick={handleSaveConfig}
                  className="w-full py-3 bg-surface border border-border-subtle rounded-xl text-xs font-black text-text-primary hover:bg-border-subtle transition-all flex items-center justify-center gap-2"
                >
                  Guardar Parámetros
                </button>
              </div>
            </div>

            {/* Watchdog Actions History */}
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
              <h3 className="text-sm font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                <Terminal size={18} className="text-accent-secondary" /> Historial de Optimizaciones
              </h3>
              <div className="space-y-4 max-h-[220px] overflow-y-auto pr-2 scrollbar-hide">
                {resourceData?.history?.length > 0 ? (
                  resourceData.history.map((h: any, i: number) => (
                    <div key={i} className="p-3.5 rounded-xl bg-surface border border-border-subtle flex items-start gap-4">
                      <div className={`mt-0.5 p-1 rounded-lg ${
                        h.action === 'Cleanup' ? 'bg-status-success/10 text-status-success' : 'bg-text-muted/10 text-text-muted'
                      }`}>
                        <ShieldCheck size={14} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-center gap-2">
                          <span className="text-[10px] font-black text-text-primary uppercase tracking-widest">{h.action}</span>
                          <span className="text-[9px] font-bold text-text-muted shrink-0">{h.timestamp}</span>
                        </div>
                        <p className="text-[10px] text-text-muted mt-1 leading-relaxed">{h.details}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-8 text-center text-text-muted opacity-30 flex flex-col items-center gap-2">
                    <Zap size={24} />
                    <span className="text-xs font-bold uppercase tracking-widest">Sin intervenciones registradas</span>
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

const Checkpoint = ({ label, ok }: any) => (
  <div className="p-4 rounded-xl bg-surface border border-border-subtle flex items-center justify-between">
    <span className="text-xs font-bold text-text-muted">{label}</span>
    <div className={`w-2 h-2 rounded-full ${ok ? 'bg-status-success shadow-[0_0_10px_rgba(34,197,94,0.5)]' : 'bg-status-error'}`}></div>
  </div>
);
