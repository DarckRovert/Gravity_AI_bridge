import { useEffect, useState } from 'react';
import { Activity, Cpu, Database, Gauge, Server, Thermometer, Trash2, RefreshCw, Zap, HardDrive } from 'lucide-react';
import { showToast } from './Toast';

export const HardwareMonitor = () => {
  const [stats, setStats] = useState<any>(null);
  const [processes, setProcesses] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    try {
      const [statsRes, procRes] = await Promise.all([
        fetch('/v1/hardware/stats'),
        fetch('/v1/processes')
      ]);
      if (statsRes.ok) setStats(await statsRes.json());
      if (procRes.ok) {
        const pData = await procRes.json();
        setProcesses(pData.processes || []);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchData();
    const iv = setInterval(fetchData, 5000);
    return () => clearInterval(iv);
  }, []);

  const killProcess = async (pid: number, name: string) => {
    if (!confirm(`¿Deseas finalizar el proceso ${name} (PID: ${pid})?`)) return;
    setLoading(true);
    try {
      const res = await fetch(`/v1/security/kill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pid })
      });
      if (res.ok) {
        showToast('success', `Proceso ${name} (PID: ${pid}) finalizado.`);
        await fetchData();
      } else {
        const err = await res.json();
        showToast('error', `Error al finalizar proceso: ${err.error}`);
      }
    } catch (e) {
      showToast('error', "Error de conexión con el backend");
    } finally {
      setLoading(false);
    }
  };

  const ProgressItem = ({ value, label, icon: Icon, colorClass, colorHex }: any) => (
    <div className="glass-panel p-6 rounded-2xl border border-border-subtle flex-1 min-w-[280px] group hover:border-accent-primary/30 transition-all">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-surface border border-border-subtle text-${colorClass} shadow-sm group-hover:scale-110 transition-transform`}>
            <Icon size={20} />
          </div>
          <span className="text-xs font-black uppercase tracking-widest text-text-muted">{label}</span>
        </div>
        <span className={`text-lg font-black text-${colorClass}`}>{value}%</span>
      </div>
      <div className="w-full bg-surface h-2.5 rounded-full overflow-hidden border border-border-subtle">
        <div 
          className={`h-full transition-all duration-1000 shadow-[0_0_10px_${colorHex}44]`}
          style={{ width: `${value}%`, backgroundColor: colorHex }} 
        />
      </div>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in duration-500">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle shadow-[0_0_20px_rgba(168,85,247,0.1)]">
              <Activity className="text-accent-primary" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Hardware Telemetry</h1>
              <p className="text-text-muted mt-1 font-medium">Monitoreo de recursos físicos y optimización de carga en tiempo real.</p>
            </div>
          </div>
          <button 
            onClick={() => { setLoading(true); fetchData().finally(() => setLoading(false)); }}
            className="p-2.5 hover:bg-white/5 rounded-xl text-text-muted transition-all border border-transparent hover:border-border-subtle"
          >
             <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Main Stats */}
        <div className="flex flex-wrap gap-6">
          <ProgressItem value={stats?.cpu_percent || 0} label="CPU Usage" icon={Cpu} colorClass="accent-primary" colorHex="#818cf8" />
          <ProgressItem value={stats?.ram_percent || 0} label="RAM Memory" icon={Database} colorClass="accent-secondary" colorHex="#a855f7" />
          <ProgressItem value={stats?.gpu_percent || 0} label="GPU Load" icon={Gauge} colorClass="accent-tertiary" colorHex="#ec4899" />
        </div>

        {/* Detailed Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Process List */}
          <div className="lg:col-span-2 glass-panel rounded-2xl border border-border-subtle overflow-hidden">
            <div className="p-4 border-b border-border-subtle bg-surface/30 flex items-center justify-between">
               <h3 className="text-xs font-black uppercase tracking-widest text-text-muted flex items-center gap-2">
                 <Server size={14} /> Procesos de Alto Impacto (TOP 12)
               </h3>
               <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-status-success animate-pulse"></span>
                  <span className="text-[10px] text-text-muted font-bold uppercase">Live Sync</span>
               </div>
            </div>
            <div className="overflow-x-auto">
               <table className="w-full text-left text-xs">
                 <thead className="bg-surface/50 text-text-muted border-b border-border-subtle">
                   <tr>
                     <th className="px-6 py-4 uppercase font-bold tracking-tighter">Proceso</th>
                     <th className="px-6 py-4 uppercase font-bold tracking-tighter">RAM</th>
                     <th className="px-6 py-4 uppercase font-bold tracking-tighter">CPU</th>
                     <th className="px-6 py-4 text-right">Acción</th>
                   </tr>
                 </thead>
                 <tbody className="divide-y divide-border-subtle/30">
                    {processes.slice(0, 12).map((p) => (
                      <tr key={p.pid} className="hover:bg-white/5 transition-colors group">
                        <td className="px-6 py-4">
                           <div className="font-bold text-text-primary flex items-center gap-2">
                              {p.name}
                              <span className="text-[9px] text-text-muted font-mono bg-black/20 px-1.5 py-0.5 rounded">PID {p.pid}</span>
                           </div>
                        </td>
                        <td className="px-6 py-4 font-mono text-accent-secondary font-black">{p.ram} MB</td>
                        <td className="px-6 py-4">
                           <div className="flex items-center gap-2">
                              <div className="w-12 bg-surface h-1 rounded-full overflow-hidden">
                                 <div className="h-full bg-text-muted opacity-50" style={{ width: `${p.cpu}%` }}></div>
                              </div>
                              <span className="font-mono text-text-muted w-8">{p.cpu}%</span>
                           </div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button 
                            onClick={() => killProcess(p.pid, p.name)}
                            className="p-2 rounded-lg bg-status-error/20 text-status-error hover:bg-status-error hover:text-white transition-all shadow-sm border border-status-error/30"
                            title="Matar proceso"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {processes.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-6 py-12 text-center text-text-muted font-medium italic">
                           No se detectaron procesos relevantes o cargando...
                        </td>
                      </tr>
                    )}
                 </tbody>
               </table>
            </div>
          </div>

          {/* Sidebar Info */}
          <div className="space-y-6">
             <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
                <h3 className="text-xs font-black uppercase tracking-widest text-text-muted mb-6 flex items-center gap-2">
                  <Thermometer size={14} /> Sensores Térmicos
                </h3>
                <div className="space-y-6">
                  <TempItem label="CPU Package" value={stats?.cpu_temp || '42°C'} color="status-success" />
                  <TempItem label="GPU Core" value={stats?.gpu_temp || '68°C'} color="status-warning" />
                  <TempItem label="Storage Hub" value="35°C" color="status-success" />
                </div>
             </div>
             
             <div className="glass-panel p-6 rounded-2xl border border-border-subtle bg-gradient-to-br from-accent-primary/10 to-transparent">
                <div className="flex items-center gap-3 mb-3">
                   <Zap size={18} className="text-accent-primary" />
                   <h3 className="text-xs font-black uppercase tracking-widest text-accent-primary">Gravity Recommendation</h3>
                </div>
                <p className="text-[11px] text-text-muted leading-relaxed font-medium">
                  {stats?.ram_percent > 85 
                    ? "Carga de RAM crítica. Se recomienda cerrar motores IA inactivos (como Fooocus) para evitar swap de disco y degradación de latencia." 
                    : "Rendimiento del sistema óptimo. Los niveles de telemetría indican suficiente margen para ejecutar modelos de inferencia pesados."}
                </p>
             </div>

             <div className="glass-panel p-6 rounded-2xl border border-border-subtle flex items-center gap-4">
                <div className="p-3 rounded-xl bg-surface border border-border-subtle">
                   <HardDrive size={20} className="text-text-muted" />
                </div>
                <div>
                   <div className="text-[10px] font-black text-text-muted uppercase tracking-widest">Almacenamiento ({(stats?.disk_total_gb / 1024).toFixed(1)} TB)</div>
                   <div className="text-lg font-black text-text-primary">{stats?.disk_free_gb >= 1024 ? (stats.disk_free_gb / 1024).toFixed(1) + ' TB' : (stats?.disk_free_gb || 0).toFixed(1) + ' GB'} <span className="text-xs text-text-muted font-medium">LIBRES</span></div>
                </div>
             </div>
          </div>

        </div>

      </div>
    </div>
  );
};



const TempItem = ({ label, value }: any) => {
  const isHigh = parseInt(value) > 75;
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center text-xs">
        <span className="text-text-muted font-bold">{label}</span>
        <span className={`font-black ${isHigh ? 'text-status-error' : 'text-text-primary'}`}>{value}</span>
      </div>
      <div className="w-full h-1 bg-surface rounded-full overflow-hidden">
        <div 
          className={`h-full ${isHigh ? 'bg-status-error' : 'bg-status-success'} opacity-50`} 
          style={{ width: `${Math.min(parseInt(value) * 1.2, 100)}%` }}
        />
      </div>
    </div>
  );
};
