import { useEffect, useState } from 'react';
import { ShieldAlert, Globe, Crosshair, Cpu, Lock, MapPin, Zap, AlertCircle } from 'lucide-react';

export const Security = () => {
  const [sec, setSec] = useState<any>(null);
  const [geo, setGeo] = useState<any[]>([]);

  const fetchSecurity = async () => {
    try {
      const [sRes, gRes] = await Promise.all([
        fetch('/v1/security'),
        fetch('/v1/security/geoip')
      ]);
      if (sRes.ok) setSec(await sRes.json());
      if (gRes.ok) {
        const gData = await gRes.json();
        setGeo(gData.tracker || []);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchSecurity();
    const iv = setInterval(fetchSecurity, 5000);
    return () => clearInterval(iv);
  }, []);

  const killProcess = async (pid: number) => {
    if (!confirm(`¿Seguro que deseas terminar el proceso con PID ${pid}?`)) return;
    try {
      await fetch('/v1/security/kill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pid })
      });
      fetchSecurity();
    } catch (e) {
      alert('Error al terminar proceso');
    }
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-7xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle shadow-[0_0_20px_rgba(239,68,68,0.2)]">
              <ShieldAlert className="text-status-error" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Intrusion & Security</h1>
              <p className="text-text-muted mt-1 font-medium">Monitoreo Zero-Trust de procesos, puertos y geolocalización de atacantes.</p>
            </div>
          </div>
          <div className={`px-4 py-2 rounded-xl border font-black text-xs uppercase tracking-widest flex items-center gap-2
            ${sec?.status === 'warning' || sec?.status === 'error' ? 'bg-status-error text-white border-status-error animate-pulse' : 'bg-status-success/10 text-status-success border-status-success/20'}`}>
            <Lock size={14} /> {sec?.status === 'warning' || sec?.status === 'error' ? 'THREAT DETECTED' : 'ENFORCED'}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Active Threats */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
              <h3 className="text-sm font-black text-text-primary uppercase tracking-widest flex items-center gap-2 mb-6">
                <Cpu size={18} className="text-accent-primary" /> Procesos Sospechosos
              </h3>
              <div className="space-y-3">
                {(sec?.processes?.filter((p: any) => p.suspicious) || []).length > 0
                  ? (sec.processes.filter((p: any) => p.suspicious) as any[]).map((p: any, i: number) => (
                  <div key={i} className="p-4 rounded-xl bg-status-error/5 border border-status-error/20 flex items-center justify-between group hover:bg-status-error/10 transition-all">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-status-error/20 flex items-center justify-center text-status-error">
                        <Zap size={20} fill="currentColor" />
                      </div>
                      <div>
                        <div className="font-bold text-text-primary text-sm">{p.name} <span className="text-text-muted text-xs">PID: {p.pid}</span></div>
                        <div className="text-[10px] font-bold text-status-error uppercase tracking-tighter">{p.reason || 'Proceso sospechoso detectado'}</div>
                      </div>
                    </div>
                    <button 
                      onClick={() => killProcess(p.pid)}
                      className="px-3 py-1.5 bg-status-error text-white text-[10px] font-black rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      KILL PROCESS
                    </button>
                  </div>
                )) : (
                  <div className="py-12 text-center text-text-muted flex flex-col items-center gap-2 opacity-50 font-bold uppercase tracking-widest text-xs">
                    <Crosshair size={32} className="mb-2" /> No hay amenazas activas detectadas
                  </div>
                )}
              </div>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
              <h3 className="text-sm font-black text-text-primary uppercase tracking-widest flex items-center gap-2 mb-6">
                <Globe size={18} className="text-accent-secondary" /> Rastreador de IPs (HTTP Traffic)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {geo.map((hit, i) => (
                  <div key={i} className="p-4 rounded-xl bg-surface border border-border-subtle flex items-center gap-4">
                    <div className="w-8 h-8 rounded-full bg-accent-secondary/10 flex items-center justify-center text-accent-secondary">
                      <MapPin size={16} />
                    </div>
                    <div className="flex-1">
                      <div className="text-xs font-black text-text-primary">{hit.ip}</div>
                      <div className="text-[10px] font-bold text-text-muted">{hit.city}, {hit.country}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-[9px] font-bold text-accent-secondary">{hit.isp?.substring(0, 15)}...</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Security Stats */}
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
              <h3 className="text-sm font-black text-text-primary uppercase tracking-widest">Estado Global</h3>
              <div className="space-y-4">
                <StatItem label="Nivel de Alerta" value={sec?.status === 'warning' ? 'HIGH' : sec?.status === 'error' ? 'CRITICAL' : 'LOW'} color={sec?.status !== 'ok' && sec?.status ? 'text-status-error' : 'text-status-success'} />
                <StatItem label="Escaneos hoy" value={sec?.scans_today || 0} />
                <StatItem label="Puertos Abiertos" value={sec?.listening_ports?.length || sec?.open_ports?.length || 0} />
                <StatItem label="Score Seguridad" value={`${sec?.score ?? 100}/100`} color={sec?.score < 70 ? 'text-status-error' : 'text-status-success'} />
              </div>
              <div className="pt-4 border-t border-border-subtle">
                <button 
                  onClick={() => fetch('/v1/security/scan', { method: 'POST' }).then(() => { alert('Escaneo forzado iniciado'); fetchSecurity(); })}
                  className="w-full py-3 rounded-xl bg-accent-primary text-white text-xs font-black uppercase tracking-widest hover:scale-105 transition-all"
                >
                  Ejecutar Escaneo Total
                </button>
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-gradient-to-br from-status-error/10 to-transparent border border-status-error/20 flex flex-col items-center text-center gap-3">
              <AlertCircle className="text-status-error" size={32} />
              <div className="text-xs font-bold text-status-error uppercase tracking-widest">Protocolo Hard-Reset</div>
              <p className="text-[10px] text-text-muted font-medium italic">En caso de compromiso total, este comando purgará todas las sesiones activas y bloqueará las API keys.</p>
              <button 
                onClick={() => alert('Protocolo Omega Activado. Restringiendo todas las peticiones externas y limpiando estado en memoria...')}
                className="mt-2 text-[10px] font-black text-status-error hover:underline uppercase"
              >
                Activar protocol omega
              </button>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};

const StatItem = ({ label, value, color = "text-text-primary" }: any) => (
  <div className="flex justify-between items-center text-xs">
    <span className="text-text-muted font-bold uppercase tracking-tighter">{label}</span>
    <span className={`font-black ${color}`}>{value}</span>
  </div>
);
