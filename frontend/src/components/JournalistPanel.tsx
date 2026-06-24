import { useState, useEffect, useRef } from 'react';
import { Play, Square, Terminal, Activity, Rss, Clock, ExternalLink, Hash, Globe, WifiOff, FileText, LayoutList } from 'lucide-react';
import { BRIDGE_BASE } from '../config';

interface JournalistStatus {
  online: boolean;
  pid: number | null;
  message: string;
}

interface NewsItem {
  id: string;
  title: string;
  excerpt: string;
  category: string;
  date: string;
  image: string;
  featured?: boolean;
}

export const JournalistPanel = () => {
  const [status, setStatus] = useState<JournalistStatus | null>(null);
  const [logs, setLogs] = useState<string>('');
  const [news, setNews] = useState<NewsItem[]>([]);
  const [processing, setProcessing] = useState(false);
  const [isOffline, setIsOffline] = useState(false);
  
  const logsEndRef = useRef<HTMLDivElement>(null);

  const handleStartPortal = async () => {
    try {
      const res = await fetch(`${BRIDGE_BASE}/v1/journalist/portal/start`, { method: "POST" });
      if (res.ok) {
        setTimeout(() => {
          window.open("http://localhost:5173", "_blank");
        }, 2000);
      } else {
        window.open("http://localhost:5173", "_blank"); // Fallback
      }
    } catch (e) {
      window.open("http://localhost:5173", "_blank"); // Fallback
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch('/v1/journalist/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
        setIsOffline(false);
      } else {
        setIsOffline(true);
      }
    } catch (e) {
      setIsOffline(true);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch('/v1/journalist/log');
      if (res.ok) {
        const data = await res.json();
        if (data.ok) {
          setLogs(data.logs);
        }
      }
    } catch (e) {
      // Offline ya manejado por status
    }
  };

  const fetchNews = async () => {
    try {
      const res = await fetch('/v1/journalist/news');
      if (res.ok) {
        const data = await res.json();
        if (data.ok) {
          setNews(data.news || []);
        }
      }
    } catch (e) {
      // Offline manejado por status
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchLogs();
    fetchNews();
    
    // Polling cada 3 segundos
    const ivStatus = setInterval(fetchStatus, 3000);
    const ivLogs = setInterval(fetchLogs, 3000);
    const ivNews = setInterval(fetchNews, 10000);
    
    return () => {
      clearInterval(ivStatus);
      clearInterval(ivLogs);
      clearInterval(ivNews);
    };
  }, []);

  // Auto-scroll logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const handleStart = async () => {
    setProcessing(true);
    try {
      await fetch('/v1/journalist/start', { method: 'POST' });
      await fetchStatus();
    } finally {
      setProcessing(false);
    }
  };

  const handleStop = async () => {
    setProcessing(true);
    try {
      await fetch('/v1/journalist/stop', { method: 'POST' });
      await fetchStatus();
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-4 md:p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-700 relative">
      {/* Background FX */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-600/10 blur-[120px] rounded-full pointer-events-none"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[40%] h-[50%] bg-purple-600/10 blur-[120px] rounded-full pointer-events-none"></div>

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        
        {/* Header & Connectivity Alert */}
        {isOffline && (
          <div className="bg-status-error/10 border border-status-error/30 text-status-error p-4 rounded-2xl flex items-center gap-3 animate-pulse shadow-[0_0_20px_rgba(239,68,68,0.15)]">
            <WifiOff size={24} />
            <div>
              <h4 className="font-bold text-sm tracking-widest uppercase">Pérdida de Conexión</h4>
              <p className="text-xs opacity-90">El servidor no responde. <b>¿Reiniciaste INICIAR_TODO.bat?</b> Hazlo para que los botones funcionen.</p>
            </div>
          </div>
        )}

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 bg-surface/40 border border-border-subtle p-6 rounded-3xl backdrop-blur-xl shadow-2xl">
          <div className="flex items-center gap-5">
            <div className="relative">
              <div className="absolute inset-0 bg-blue-500 blur-xl opacity-20 rounded-full"></div>
              <div className="p-4 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 relative">
                <Globe className="text-blue-400" size={32} />
              </div>
            </div>
            <div>
              <h1 className="text-4xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                Periodista Autónomo
              </h1>
              <p className="text-text-muted mt-1 font-medium text-sm flex items-center gap-2">
                Agente OSINT de Inteligencia Global <span className="w-1 h-1 bg-text-muted rounded-full"></span> V16.3 PRO
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            {/* Metricas Rapidas */}
            <div className="flex items-center gap-4 px-6 py-3 rounded-2xl bg-black/40 border border-border-subtle">
               <div className="text-center">
                 <div className="text-2xl font-black text-text-primary">{news.length}</div>
                 <div className="text-[10px] text-text-muted uppercase tracking-widest font-bold">Publicaciones</div>
               </div>
               <div className="w-px h-8 bg-border-subtle"></div>
               <div className="text-center">
                 <div className="text-lg font-mono text-blue-400">{status?.pid || '---'}</div>
                 <div className="text-[10px] text-text-muted uppercase tracking-widest font-bold">PID</div>
               </div>
            </div>

            {/* Estado Vivo */}
            <div className={`px-6 py-4 rounded-2xl border font-black text-xs uppercase tracking-widest flex items-center gap-3 shadow-lg transition-all duration-500
              ${status?.online 
                ? 'bg-status-success/15 text-status-success border-status-success/40 shadow-[0_0_30px_rgba(34,197,94,0.15)]' 
                : 'bg-status-error/15 text-status-error border-status-error/40'}`}>
              <div className="relative flex h-3 w-3">
                {status?.online && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-success opacity-75"></span>}
                <span className={`relative inline-flex rounded-full h-3 w-3 ${status?.online ? 'bg-status-success' : 'bg-status-error'}`}></span>
              </div>
              {status?.online ? 'OPERACIONES ACTIVAS' : 'SISTEMA INACTIVO'}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Mando de Operaciones */}
          <div className="lg:col-span-4 space-y-6">
            
            <div className="bg-surface/50 backdrop-blur-xl p-6 rounded-3xl border border-border-subtle shadow-xl relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 opacity-50 group-hover:opacity-100 transition-opacity"></div>
              
              <h3 className="text-xs font-black text-text-muted mb-6 flex items-center gap-2 uppercase tracking-widest">
                <Terminal size={14} className="text-blue-400" />
                Mando de Control
              </h3>
              
              <div className="space-y-4 relative z-10">
                <button
                  onClick={handleStart}
                  disabled={processing || status?.online || isOffline}
                  className="w-full relative overflow-hidden group/btn disabled:opacity-50 disabled:cursor-not-allowed rounded-2xl"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 opacity-20 group-hover/btn:opacity-100 transition-all duration-300"></div>
                  <div className="relative px-4 py-4 border border-blue-500/50 bg-blue-500/10 flex items-center justify-center gap-3 text-sm font-black uppercase tracking-widest text-blue-400 group-hover/btn:text-white transition-colors">
                    <Play size={18} className={processing ? 'animate-spin' : ''} />
                    {processing ? 'INICIANDO...' : 'INICIAR CICLO OSINT'}
                  </div>
                </button>
                
                <button
                  onClick={handleStop}
                  disabled={processing || !status?.online || isOffline}
                  className="w-full flex items-center justify-center gap-3 px-4 py-4 rounded-2xl bg-black/40 border border-status-error/30 text-status-error hover:bg-status-error/20 transition-all text-sm font-black uppercase tracking-widest disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Square size={18} />
                  ABORTAR PROTOCOLO
                </button>

                <div className="pt-6 mt-6 border-t border-border-subtle grid grid-cols-2 gap-4">
                  <div className="bg-black/40 p-4 rounded-2xl border border-border-subtle/50">
                    <Rss className="text-purple-400 mb-2" size={18} />
                    <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Fuentes</div>
                    <div className="text-xs font-mono text-text-primary mt-1">Google News</div>
                  </div>
                  <div className="bg-black/40 p-4 rounded-2xl border border-border-subtle/50">
                    <Clock className="text-blue-400 mb-2" size={18} />
                    <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Frecuencia</div>
                    <div className="text-xs font-mono text-text-primary mt-1">~15-45 mins</div>
                  </div>
                </div>

                <div className="flex justify-between items-center bg-gray-900/50 p-4 rounded-xl border border-gray-700/50 hover:border-gray-600 transition-colors cursor-pointer" onClick={handleStartPortal}>
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-500/20 rounded-lg">
                      <LayoutList className="text-blue-400" size={20} />
                    </div>
                    <div>
                      <div className="font-bold text-gray-200">Ver Portal Frontal</div>
                      <div className="text-xs text-purple-400 font-mono tracking-widest uppercase">Netlify (En Vivo)</div>
                    </div>
                  </div>
                  <ExternalLink className="text-blue-400 hover:text-blue-300" size={18} />
                </div>
              </div>
            </div>

          </div>

          {/* Consola & Feed */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            
            {/* Registro del Sistema */}
            <div className="bg-surface/50 backdrop-blur-xl p-1 rounded-3xl border border-border-subtle shadow-xl flex flex-col h-[350px]">
              <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle bg-black/20 rounded-t-[22px]">
                <div className="flex items-center gap-3">
                  <Terminal size={16} className="text-blue-400" />
                  <span className="text-[11px] font-black text-text-muted uppercase tracking-widest">Transmisiones Crudas (gravity.log)</span>
                </div>
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-status-error/80 shadow-[0_0_10px_rgba(239,68,68,0.5)]"></div>
                  <div className="w-3 h-3 rounded-full bg-status-warning/80 shadow-[0_0_10px_rgba(234,179,8,0.5)]"></div>
                  <div className="w-3 h-3 rounded-full bg-status-success/80 shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
                </div>
              </div>
              
              <div className="flex-1 bg-[#0a0a0c] p-6 overflow-y-auto font-mono text-[12px] leading-relaxed rounded-b-[22px] scrollbar-hide">
                {logs ? (
                  <pre className="whitespace-pre-wrap">
                    {logs.split('\n').map((line, i) => {
                      let colorClass = 'text-text-muted/70';
                      if (line.includes('INFO')) colorClass = 'text-blue-300';
                      if (line.includes('ERROR') || line.includes('CRITICAL')) colorClass = 'text-status-error font-bold';
                      if (line.includes('WARNING')) colorClass = 'text-status-warning';
                      if (line.includes('Anomalía RSS') || line.includes('Iniciando inmersión')) colorClass = 'text-purple-400 font-bold';
                      if (line.includes('✓')) colorClass = 'text-status-success font-bold text-[13px]';
                      
                      return (
                        <div key={i} className={`hover:bg-white/5 px-2 py-1 rounded transition-colors ${colorClass}`}>
                          {line}
                        </div>
                      );
                    })}
                    <div ref={logsEndRef} />
                  </pre>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-text-muted/50 gap-3">
                    <Activity size={24} className="animate-pulse" />
                    <span className="text-xs uppercase tracking-widest font-bold">Sincronizando Registros...</span>
                  </div>
                )}
              </div>
            </div>

            {/* Catálogo en Vivo */}
            <div className="bg-surface/50 backdrop-blur-xl p-6 rounded-3xl border border-border-subtle shadow-xl">
              <h3 className="text-xs font-black text-text-primary mb-6 flex items-center justify-between uppercase tracking-widest">
                <div className="flex items-center gap-2">
                  <FileText size={16} className="text-purple-400" />
                  Últimos Reportes Generados
                </div>
                <div className="text-[10px] text-text-muted font-mono">{news.length} Artículos</div>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {news.length > 0 ? news.slice(0, 3).map((item) => (
                  <div key={item.id} className="group cursor-pointer bg-black/40 rounded-2xl overflow-hidden border border-border-subtle hover:border-purple-500/50 hover:shadow-[0_0_30px_rgba(168,85,247,0.15)] transition-all duration-300">
                    <div className="h-32 overflow-hidden relative">
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent z-10"></div>
                      <img src={item.image} alt={item.title} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
                      <div className="absolute bottom-3 left-3 z-20 text-[9px] font-black uppercase tracking-widest bg-purple-500/20 text-purple-300 px-2 py-1 rounded border border-purple-500/30 backdrop-blur-md">
                        {item.category}
                      </div>
                    </div>
                    <div className="p-4">
                      <h4 className="font-bold text-sm text-text-primary line-clamp-2 leading-tight group-hover:text-purple-400 transition-colors">{item.title}</h4>
                      <p className="text-[11px] text-text-muted mt-2 line-clamp-2 leading-relaxed">{item.excerpt}</p>
                      <div className="mt-4 flex items-center gap-2 text-[10px] font-mono text-text-muted">
                        <Clock size={10} />
                        {new Date(item.date).toLocaleDateString()} {new Date(item.date).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                )) : (
                  <div className="col-span-3 py-12 flex flex-col items-center justify-center text-text-muted/50 border-2 border-dashed border-border-subtle rounded-2xl">
                    <Hash size={32} className="mb-3 opacity-50" />
                    <p className="text-sm font-bold">No hay artículos publicados todavía</p>
                    <p className="text-xs">Inicia el ciclo OSINT para comenzar</p>
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
