import React, { useState, useEffect } from 'react';
import { Ghost, Play, Square, Crosshair, AlertTriangle, Monitor, MousePointer2 } from 'lucide-react';

interface InfiltratorStatus {
  running: boolean;
  current_url: string | null;
  status_msg: string;
  last_screenshot: string | null;
}

export const Infiltrator: React.FC = () => {
  const [targetUrl, setTargetUrl] = useState('https://www.freelancer.com/login');
  const [status, setStatus] = useState<InfiltratorStatus>({
    running: false,
    current_url: null,
    status_msg: 'Apagado',
    last_screenshot: null
  });

  const fetchStatus = async () => {
    try {
      const res = await fetch('/v1/infiltrator/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    try {
      await fetch('/v1/infiltrator/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: targetUrl })
      });
      fetchStatus();
    } catch (e) {
      console.error(e);
    }
  };

  const handleStop = async () => {
    try {
      await fetch('/v1/infiltrator/stop', { method: 'POST' });
      fetchStatus();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="h-full flex flex-col bg-bg/50 overflow-hidden">
      {/* Header */}
      <div className="flex-none p-6 pb-2 border-b border-border-subtle bg-surface/50 backdrop-blur-md z-10">
        <div className="flex items-center gap-3 mb-1">
          <div className="p-2 bg-status-error/10 rounded-lg text-status-error">
            <Ghost size={24} />
          </div>
          <h1 className="text-2xl font-bold text-text-primary">Infiltrador (AGI Financiero)</h1>
        </div>
        <p className="text-text-muted text-sm ml-12">Motor de Navegación Autónoma y Evasión Anti-Bot (Playwright Stealth)</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 scrollbar-hide flex flex-col lg:flex-row gap-6">
        
        {/* Controles Izquierdos */}
        <div className="w-full lg:w-1/3 flex flex-col gap-4">
          <div className="glass-card bg-card/80 border border-border-subtle rounded-xl p-6 shadow-lg">
            
            <div className="flex items-center gap-2 mb-4 text-status-warning">
              <AlertTriangle size={20} />
              <h2 className="text-lg font-bold">Panel de Control</h2>
            </div>
            
            <div className="mb-4">
              <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">Target URL (Punto de Inyección)</label>
              <div className="flex items-center bg-bg border border-border-subtle rounded-lg px-3 py-2 focus-within:border-accent-primary transition-colors">
                <Crosshair size={16} className="text-text-muted mr-2" />
                <input
                  type="text"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  disabled={status.running}
                  className="bg-transparent border-none text-text-primary text-sm w-full focus:outline-none"
                  placeholder="https://..."
                />
              </div>
            </div>

            <div className="flex flex-col gap-2">
              {!status.running ? (
                <button
                  onClick={handleStart}
                  className="w-full flex items-center justify-center gap-2 py-3 bg-status-error text-white font-bold rounded-lg hover:bg-status-error/90 transition-all shadow-lg shadow-status-error/20"
                >
                  <Play size={18} /> Lanzar Infiltración Stealth
                </button>
              ) : (
                <button
                  onClick={handleStop}
                  className="w-full flex items-center justify-center gap-2 py-3 bg-surface border border-status-error/50 text-status-error font-bold rounded-lg hover:bg-status-error/10 transition-all"
                >
                  <Square size={18} /> Detener Motor
                </button>
              )}
            </div>
          </div>

          <div className="glass-card bg-card/80 border border-border-subtle rounded-xl p-6 shadow-lg flex-1">
            <h2 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-4 flex items-center gap-2">
              <Monitor size={16} /> Estado del Motor
            </h2>
            
            <div className="space-y-4">
              <div>
                <div className="text-xs text-text-muted mb-1">Estado General</div>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${status.running ? 'bg-status-success animate-pulse' : 'bg-status-error'}`}></div>
                  <span className={`text-sm font-bold ${status.running ? 'text-status-success' : 'text-status-error'}`}>
                    {status.running ? 'INFILTRACIÓN ACTIVA' : 'APAGADO'}
                  </span>
                </div>
              </div>
              
              <div>
                <div className="text-xs text-text-muted mb-1">Status Log</div>
                <div className="text-sm text-text-primary bg-bg p-3 rounded-lg border border-border-subtle break-words">
                  {status.status_msg}
                </div>
              </div>
              
              <div>
                <div className="text-xs text-text-muted mb-1">URL Actual</div>
                <div className="text-sm text-accent-primary truncate bg-bg p-2 rounded-lg border border-border-subtle">
                  {status.current_url || 'N/A'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Monitoreo Derecho (Live View) */}
        <div className="w-full lg:w-2/3 flex flex-col">
          <div className="glass-card bg-card/80 border border-border-subtle rounded-xl shadow-lg flex-1 flex flex-col overflow-hidden relative">
            <div className="p-4 border-b border-border-subtle bg-surface/50 flex justify-between items-center z-10">
              <h2 className="text-sm font-bold text-text-muted uppercase tracking-wider flex items-center gap-2">
                <MousePointer2 size={16} /> Vista de Telemetría (Live View)
              </h2>
              {status.running && <div className="text-xs text-status-success font-medium flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-status-success animate-ping"></div> Live</div>}
            </div>
            
            <div className="flex-1 bg-black relative flex items-center justify-center">
              {status.last_screenshot ? (
                <img 
                  src={status.last_screenshot} 
                  alt="Live Telemetry" 
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="text-text-muted flex flex-col items-center gap-3">
                  <Monitor size={48} className="opacity-20" />
                  <p className="text-sm">Sin telemetría de video. Lanza la infiltración para ver.</p>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
