import { useEffect, useState } from 'react';
import { Cpu, Server, Box, RefreshCw, CheckCircle2, XCircle } from 'lucide-react';

export const MCPServers = () => {
  const [servers, setServers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMCP = async () => {
    try {
      const res = await fetch('/v1/mcp/status');
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        setServers(data.mcp_servers || []);
      }
    } catch (e) {} finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMCP();
    const iv = setInterval(fetchMCP, 10000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-surface border border-border-subtle">
            <Box className="text-accent-primary" size={28} />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">MCP Connectors</h1>
            <p className="text-text-muted mt-1 font-medium">Model Context Protocol: Integración con herramientas y recursos externos.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {servers.map((s, i) => (
            <div key={i} className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3">
                   <div className="p-2 rounded-lg bg-surface border border-border-subtle text-accent-primary">
                      <Server size={20} />
                   </div>
                   <div>
                      <h3 className="font-black text-text-primary uppercase tracking-tighter">{s.name}</h3>
                      <div className={`text-[10px] font-bold flex items-center gap-1 ${s.connected ? 'text-status-success' : 'text-status-error'}`}>
                         {s.connected ? <CheckCircle2 size={10} /> : <XCircle size={10} />}
                         {s.connected ? 'CONNECTED' : 'DISCONNECTED'}
                      </div>
                   </div>
                </div>
                <button onClick={fetchMCP} className="p-2 rounded-lg hover:bg-surface transition-all text-text-muted">
                   <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                 <div className="p-4 rounded-xl bg-surface border border-border-subtle">
                    <div className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-1">Herramientas</div>
                    <div className="text-xl font-black text-text-primary">{s.tools?.length || 0}</div>
                 </div>
                 <div className="p-4 rounded-xl bg-surface border border-border-subtle">
                    <div className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-1">Recursos</div>
                    <div className="text-xl font-black text-text-primary">{s.resources?.length || 0}</div>
                 </div>
              </div>

              <div className="space-y-2">
                 <div className="text-[10px] font-black text-text-muted uppercase tracking-widest">Capabilities</div>
                 <div className="flex flex-wrap gap-2">
                    {s.tools?.slice(0, 5).map((t: any, j: number) => (
                      <span key={j} className="px-2 py-1 rounded-md bg-accent-primary/10 text-accent-primary text-[9px] font-bold border border-accent-primary/20">
                         {t.name || t}
                      </span>
                    ))}
                    {(s.tools?.length > 5) && <span className="text-[9px] font-bold text-text-muted">+{s.tools.length - 5} más</span>}
                 </div>
              </div>
            </div>
          ))}
          {servers.length === 0 && !loading && (
             <div className="md:col-span-2 py-20 text-center text-text-muted opacity-30 flex flex-col items-center gap-4">
                <Cpu size={48} />
                <p className="text-sm font-bold uppercase tracking-widest">No se encontraron adaptadores MCP activos</p>
             </div>
          )}
        </div>

      </div>
    </div>
  );
};
