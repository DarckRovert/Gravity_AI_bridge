import { useEffect, useState } from 'react';
import { Shield, Clock, Search, RotateCcw, AlertTriangle, CheckCircle, Info } from 'lucide-react';

export const AuditLog = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      const res = await fetch('http://localhost:7860/v1/audit');
      if (res.ok) {
        const data = await res.json();
        setLogs(data.data || []);
      }
    } catch (e) {} finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const iv = setInterval(fetchLogs, 15000);
    return () => clearInterval(iv);
  }, []);

  const rotateLogs = async () => {
    if (!confirm('¿Seguro que deseas rotar (archivar) los logs actuales?')) return;
    try {
      await fetch('http://localhost:7860/v1/audit/rotate', { method: 'POST' });
      fetchLogs();
    } catch (e) {
      alert('Error al rotar logs');
    }
  };

  const getIcon = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'ERROR': return <AlertTriangle className="text-status-error" size={14} />;
      case 'WARNING': return <AlertTriangle className="text-accent-secondary" size={14} />;
      case 'SUCCESS': return <CheckCircle className="text-status-success" size={14} />;
      default: return <Info className="text-accent-primary" size={14} />;
    }
  };

  const filteredLogs = logs.filter(l => 
    JSON.stringify(l).toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-7xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle">
              <Shield className="text-accent-primary" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">System Audit Log</h1>
              <p className="text-text-muted mt-1 font-medium">Registro inmutable de acciones, acceso a APIs y telemetría de seguridad.</p>
            </div>
          </div>
          <button 
            onClick={rotateLogs}
            className="flex items-center gap-2 px-4 py-2 bg-surface border border-border-subtle rounded-xl text-sm font-bold hover:bg-card transition-all"
          >
            <RotateCcw size={16} /> Rotar Logs
          </button>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-border-subtle flex items-center gap-3 bg-surface/30">
          <Search size={18} className="text-text-muted" />
          <input 
            type="text" 
            placeholder="Filtrar registros por IP, comando, usuario o evento..."
            className="bg-transparent border-none outline-none flex-1 text-sm text-text-primary"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>

        <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface/50 border-b border-border-subtle">
                  <th className="p-4 text-[10px] font-black uppercase tracking-widest text-text-muted">Timestamp</th>
                  <th className="p-4 text-[10px] font-black uppercase tracking-widest text-text-muted">Nivel</th>
                  <th className="p-4 text-[10px] font-black uppercase tracking-widest text-text-muted">Acción</th>
                  <th className="p-4 text-[10px] font-black uppercase tracking-widest text-text-muted">Origen (IP/User)</th>
                  <th className="p-4 text-[10px] font-black uppercase tracking-widest text-text-muted">Detalles</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle/30 font-mono text-[11px]">
                {loading ? (
                  <tr><td colSpan={5} className="p-12 text-center text-text-muted">Cargando registros de auditoría...</td></tr>
                ) : filteredLogs.map((l, i) => (
                  <tr key={i} className="hover:bg-accent-primary/5 transition-colors">
                    <td className="p-4 text-text-muted whitespace-nowrap">{l.timestamp || l.saved_at}</td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        {getIcon(l.level)}
                        <span className="font-bold">{l.level || 'INFO'}</span>
                      </div>
                    </td>
                    <td className="p-4 font-bold text-text-primary">{l.action || l.event || 'API_REQUEST'}</td>
                    <td className="p-4 text-accent-secondary">{l.ip || l.user || 'system'}</td>
                    <td className="p-4 text-text-muted truncate max-w-xs">{JSON.stringify(l.data || l.details || l)}</td>
                  </tr>
                ))}
                {!loading && filteredLogs.length === 0 && (
                  <tr><td colSpan={5} className="p-12 text-center text-text-muted">No se encontraron registros que coincidan con el filtro.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="flex justify-between items-center text-[10px] font-bold text-text-muted uppercase tracking-widest px-2">
          <span>Mostrando {filteredLogs.length} de {logs.length} registros recientes</span>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1"><Clock size={12} /> Auto-refresh cada 15s</span>
          </div>
        </div>

      </div>
    </div>
  );
};
