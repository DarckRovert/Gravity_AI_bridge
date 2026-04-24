import { useEffect, useState } from 'react';
import { Activity, Server, Database, Zap, ShieldCheck } from 'lucide-react';

export const SystemStatus = () => {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('http://localhost:7860/v1/status');
        if (res.ok) setStatus(await res.json());
      } catch (e) {}
    };
    fetchStatus();
    const iv = setInterval(fetchStatus, 5000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-surface border border-border-subtle">
            <Activity className="text-accent-primary" size={28} />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">System Architecture</h1>
            <p className="text-text-muted mt-1 font-medium">Estado omnisciente del ruteador central y salud de los backends integrados.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
           <StatusCard title="Core Version" value={`V${status?.version || '12.0'}`} icon={<Server size={20} />} color="text-accent-primary" />
           <StatusCard title="Uptime" value="99.9%" icon={<Zap size={20} />} color="text-accent-secondary" />
           <StatusCard title="Backend" value={status?.bridge_online ? 'Online' : 'Offline'} icon={<ShieldCheck size={20} />} color="text-status-success" />
           <StatusCard title="Model Active" value={status?.active_provider || 'Automatic'} icon={<Database size={20} />} color="text-text-primary" />
        </div>

        <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
           <table className="w-full text-left">
             <thead className="bg-surface/50 border-b border-border-subtle">
               <tr className="text-[10px] font-black uppercase tracking-widest text-text-muted">
                 <th className="p-4">Backend Engine</th>
                 <th className="p-4">Categoría</th>
                 <th className="p-4">Salud</th>
                 <th className="p-4">Latencia</th>
                 <th className="p-4">Modelos</th>
               </tr>
             </thead>
             <tbody className="divide-y divide-border-subtle/30">
               {status?.backends?.map((b: any, i: number) => (
                 <tr key={i} className="hover:bg-accent-primary/5 transition-colors">
                    <td className="p-4 font-black text-text-primary text-sm">{b.name}</td>
                    <td className="p-4 text-xs text-text-muted font-bold uppercase">{b.category}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase border ${b.healthy ? 'bg-status-success/10 text-status-success border-status-success/20' : 'bg-status-error/10 text-status-error border-status-error/20'}`}>
                        {b.healthy ? 'HEALTHY' : 'UNHEALTHY'}
                      </span>
                    </td>
                    <td className="p-4 text-xs font-bold text-accent-secondary">{b.latency_ms}ms</td>
                    <td className="p-4 text-xs font-bold text-text-muted">{b.models}</td>
                 </tr>
               ))}
             </tbody>
           </table>
        </div>

      </div>
    </div>
  );
};

const StatusCard = ({ title, value, icon, color }: any) => (
  <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-4">
     <div className="flex items-center justify-between">
        <div className="text-text-muted">{icon}</div>
        <div className="w-2 h-2 rounded-full bg-status-success animate-pulse"></div>
     </div>
     <div>
        <div className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-1">{title}</div>
        <div className={`text-xl font-black ${color}`}>{value}</div>
     </div>
  </div>
);
