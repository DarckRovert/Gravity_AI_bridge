import { useEffect, useState } from 'react';
import { Rocket, CheckCircle2, XCircle, RefreshCw, Terminal, Globe, ExternalLink } from 'lucide-react';
import { showToast } from './Toast';

export const DeployManager = () => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [projectPath, setProjectPath] = useState('');

  const fetchStatus = async () => {
    try {
      const res = await fetch('/v1/fabricaweb/status');
      if (res.ok) setStatus(await res.json());
    } catch (e) {}
  };

  useEffect(() => {
    fetchStatus();
    const iv = setInterval(fetchStatus, 5000);
    return () => clearInterval(iv);
  }, []);

  const runDeploy = async () => {
    setLoading(true);
    try {
      const res = await fetch('/v1/fabricaweb/deploy', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_path: projectPath.trim() || undefined })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.error || 'El orquestador de CI/CD rechazó la ejecución');
      showToast('success', data.message || 'Pipeline de Deploy iniciado exitosamente');
      await fetchStatus();
    } catch (e: any) {
      showToast('error', `Error en Deploy: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const hasValidWorkspace = status?.fabricaweb_exists || Boolean(projectPath.trim());

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle">
              <Rocket className="text-accent-primary" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Deploy Manager</h1>
              <p className="text-text-muted mt-1 font-medium">Pipeline de CI/CD para FabricaWeb y micro-servicios integrados.</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-panel p-8 rounded-2xl border border-border-subtle flex flex-col items-center text-center gap-6 bg-gradient-to-br from-accent-primary/5 to-transparent">
              <div className="w-20 h-20 rounded-full bg-accent-primary/10 flex items-center justify-center text-accent-primary shadow-[0_0_40px_rgba(99,102,241,0.2)]">
                <Globe size={40} />
              </div>
              <div>
                <h3 className="text-2xl font-black text-text-primary">{status?.project_name || 'FabricaWeb Engine'}</h3>
                <p className="text-sm text-text-muted mt-2 font-medium">Versión activa: {status?.project_version || '1.0.0-stable'}</p>
              </div>

              {status?.netlify_url && (
                <div className="w-full p-4 rounded-xl bg-status-success/10 border border-status-success/20 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-status-success text-xs font-bold">
                    <CheckCircle2 size={16} />
                    <span>Sitio en Vivo en Producción:</span>
                  </div>
                  <a 
                    href={status.netlify_url} 
                    target="_blank" 
                    rel="noreferrer"
                    className="flex items-center gap-1.5 text-xs font-black text-white bg-accent-primary hover:bg-accent-primary/80 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    <span>Abrir Web</span>
                    <ExternalLink size={12} />
                  </a>
                </div>
              )}

              <div className="flex gap-4 w-full">
                <input 
                  type="text"
                  placeholder={status?.fabricaweb_path || "Ruta al Workspace (Ej: C:/Proyectos/MiWeb)"}
                  value={projectPath}
                  onChange={(e) => setProjectPath(e.target.value)}
                  className="flex-1 px-4 py-3 rounded-xl bg-surface border border-border-subtle text-sm text-text-primary outline-none focus:border-accent-primary transition-all"
                />
                <div className={`px-4 py-3 rounded-xl border flex items-center gap-2 text-xs font-bold whitespace-nowrap
                  ${hasValidWorkspace ? 'bg-status-success/10 text-status-success border-status-success/20' : 'bg-status-error/10 text-status-error border-status-error/20'}`}>
                   {hasValidWorkspace ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                   {hasValidWorkspace ? 'WORKSPACE LISTO' : 'WORKSPACE NO ENCONTRADO'}
                </div>
              </div>
              <button 
                onClick={runDeploy}
                disabled={loading || !hasValidWorkspace}
                className="w-full max-w-sm py-4 rounded-xl bg-accent-primary text-white font-black shadow-lg hover:scale-105 transition-all flex items-center justify-center gap-3 disabled:opacity-50"
              >
                {loading ? <RefreshCw className="animate-spin" size={20} /> : <Rocket size={20} fill="currentColor" />}
                {loading ? 'DESPLEGANDO...' : 'INICIAR DEPLOY A PRODUCCIÓN'}
              </button>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
               <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-4 flex items-center gap-2">
                 <Terminal size={14} /> Log del Pipeline
               </h4>
               <div className="bg-black/50 rounded-xl p-4 font-mono text-[11px] text-accent-secondary h-48 overflow-y-auto scrollbar-hide whitespace-pre-wrap">
                  {Array.isArray(status?.log) && status.log.length > 0 
                    ? status.log.join('\n') 
                    : (status?.last_log || '> Esperando trigger...')}
                  {loading && '\n> [BUILD] Procesando pipeline en segundo plano...'}
               </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
              <h3 className="text-sm font-bold text-text-primary uppercase tracking-widest">Health Check</h3>
              <div className="space-y-4">
                <StatusRow label="Node.js Runtime" ok={Boolean(status?.tools?.node)} />
                <StatusRow label="NPM Package Manager" ok={Boolean(status?.tools?.npm)} />
                <StatusRow label="Netlify CLI" ok={Boolean(status?.tools?.netlify)} />
                <StatusRow label="Workspace" ok={hasValidWorkspace} />
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};

const StatusRow = ({ label, ok }: any) => (
  <div className="flex justify-between items-center text-xs">
    <span className="text-text-muted font-bold">{label}</span>
    <span className={`font-black ${ok ? 'text-status-success' : 'text-status-error'}`}>{ok ? 'OK' : 'FAIL'}</span>
  </div>
);
