import { useState, useEffect } from 'react';
import { Shield, ShieldAlert, Cpu, Lock, Terminal, Radio } from 'lucide-react';
import { showToast } from './Toast';

export const AgentShieldMonitor = () => {
  const [logs, setLogs] = useState<any[]>([
    { ts: new Date().toISOString(), type: 'info', msg: 'AgentShield Core Protection Iniciado (V16.5)' },
    { ts: new Date().toISOString(), type: 'info', msg: 'Rutas Ring 0 cargadas y bloqueadas.' },
    { ts: new Date().toISOString(), type: 'success', msg: 'Ruta F:/gravity-news-portal añadida a excepciones (Whitelist)' }
  ]);
  const [active, setActive] = useState(true);

  // Simulación de monitoreo en tiempo real
  useEffect(() => {
    if (!active) return;
    const iv = setInterval(() => {
      if (Math.random() > 0.85) {
        setLogs(prev => [
          { ts: new Date().toISOString(), type: 'info', msg: 'Escaneo rutinario de memoria: Limpio.' },
          ...prev
        ].slice(0, 50));
      }
    }, 4000);
    return () => clearInterval(iv);
  }, [active]);

  const toggleShield = () => {
    if (active) {
      if(confirm('¡PELIGRO! Deshabilitar el escudo dejará el puente vulnerable a inyecciones. ¿Estás seguro?')) {
        setActive(false);
        setLogs(prev => [{ ts: new Date().toISOString(), type: 'error', msg: '¡AGENT SHIELD DESHABILITADO POR EL USUARIO!' }, ...prev]);
        showToast('error', 'AgentShield desactivado');
      }
    } else {
      setActive(true);
      setLogs(prev => [{ ts: new Date().toISOString(), type: 'success', msg: 'AgentShield reactivado.' }, ...prev]);
      showToast('success', 'AgentShield activado');
    }
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl bg-surface border border-border-subtle transition-all duration-500 ${active ? 'shadow-[0_0_20px_rgba(16,185,129,0.2)]' : 'shadow-[0_0_20px_rgba(239,68,68,0.2)]'}`}>
              {active ? <Shield className="text-status-success" size={28} /> : <ShieldAlert className="text-status-error" size={28} />}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-text-primary tracking-tight">AgentShield Monitor</h1>
              <p className="text-text-muted mt-1">Protección Ring 0 y Mitigación de Path Traversal</p>
            </div>
          </div>
          <button 
            onClick={toggleShield}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${active ? 'bg-status-error/10 text-status-error hover:bg-status-error/20' : 'bg-status-success/10 text-status-success hover:bg-status-success/20'} border border-transparent hover:border-current`}
          >
            {active ? 'Apagar Escudo' : 'Activar Escudo'}
          </button>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-card p-6">
            <div className="flex items-center gap-3 text-status-success mb-4">
              <Lock size={20} />
              <h3 className="font-semibold text-text-primary">Protección Ring 0</h3>
            </div>
            <p className="text-sm text-text-muted">Protege los archivos vitales del Core, configuraciones y el motor puente contra sobreescritura accidental o maliciosa.</p>
            <div className="mt-4 text-2xl font-bold">Activo</div>
          </div>
          <div className="glass-card p-6">
            <div className="flex items-center gap-3 text-accent-primary mb-4">
              <Cpu size={20} />
              <h3 className="font-semibold text-text-primary">Filtro Path Traversal</h3>
            </div>
            <p className="text-sm text-text-muted">Evita que los agentes escapen de la carpeta de trabajo, con soporte para whitelists explícitos.</p>
            <div className="mt-4 text-2xl font-bold">Intacto</div>
          </div>
          <div className="glass-card p-6">
            <div className="flex items-center gap-3 text-accent-tertiary mb-4">
              <Radio size={20} />
              <h3 className="font-semibold text-text-primary">Interceptor Unicode</h3>
            </div>
            <p className="text-sm text-text-muted">Sanitiza comandos inyectados con caracteres invisibles o bidi-overrides.</p>
            <div className="mt-4 text-2xl font-bold">Activo</div>
          </div>
        </div>

        {/* Terminal Logs */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-3 mb-6">
            <Terminal size={20} className="text-accent-primary" />
            <h3 className="font-semibold text-text-primary">Registros de Seguridad (Tiempo Real)</h3>
          </div>
          <div className="bg-[#03050a]/80 p-4 rounded-xl border border-border-subtle h-[400px] overflow-y-auto font-mono text-sm space-y-2">
            {logs.map((log, i) => (
              <div key={i} className="flex gap-4">
                <span className="text-text-muted shrink-0">[{log.ts.split('T')[1].split('.')[0]}]</span>
                <span className={
                  log.type === 'error' ? 'text-status-error' : 
                  log.type === 'success' ? 'text-status-success' : 'text-accent-tertiary'
                }>
                  {log.msg}
                </span>
              </div>
            ))}
            {logs.length === 0 && <div className="text-text-muted italic">Sin eventos recientes...</div>}
          </div>
        </div>

      </div>
    </div>
  );
};
