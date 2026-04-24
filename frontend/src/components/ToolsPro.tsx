import { useState } from 'react';
import type { ReactNode } from 'react';
import { Zap, Code, Search, GitBranch, Terminal, Send, CheckCircle, AlertCircle, Cpu, Trash2, RefreshCw } from 'lucide-react';
import { showToast } from './Toast';

type ToolMode = 'grep' | 'git' | 'search' | 'run' | 'process';

export const ToolsPro = () => {
  const [mode, setMode] = useState<ToolMode>('grep');
  const [input, setInput] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processes, setProcesses] = useState<any[]>([]);

  const TOOL_CONFIGS: Record<ToolMode, { label: string; icon: ReactNode; endpoint: string; method: string; body: (i: string) => object; placeholder: string }> = {
    grep: {
      label: 'Grep Regex', icon: <Search size={18} />,
      endpoint: '/v1/tools/grep', method: 'POST',
      body: (i) => ({ pattern: i, path: 'F:\\Gravity_AI_bridge', recursive: true }),
      placeholder: 'Patrón regex: ej. def _serve_.*\\(.*\\)'
    },
    git: {
      label: 'Git Manager', icon: <GitBranch size={18} />,
      endpoint: '/v1/tools/git', method: 'POST',
      body: (i) => ({ cmd: i }),
      placeholder: 'Comando Git: ej. status, log, diff, branch'
    },
    search: {
      label: 'Web Search', icon: <Code size={18} />,
      endpoint: '/v1/tools/search', method: 'POST',
      body: (i) => ({ query: i, max_results: 5 }),
      placeholder: 'Consulta de búsqueda web...'
    },
    run: {
      label: 'Code Runner', icon: <Terminal size={18} />,
      endpoint: '/v1/tools/run', method: 'POST',
      body: (i) => ({ code: i, lang: 'python' }),
      placeholder: 'Código Python a ejecutar de forma segura...'
    },
    process: {
      label: 'Process Manager', icon: <Cpu size={18} />,
      endpoint: '/v1/processes', method: 'GET',
      body: () => ({}),
      placeholder: 'Haz clic en EJECUTAR para listar procesos activos.'
    }
  };

  const execute = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const cfg = TOOL_CONFIGS[mode];
      const options: any = {
        method: cfg.method,
        headers: { 'Content-Type': 'application/json' },
      };
      if (cfg.method === 'POST') {
        options.body = JSON.stringify(cfg.body(input));
      }

      const res = await fetch(`http://localhost:7860${cfg.endpoint}`, options);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error del servidor');
      
      if (mode === 'process') {
        setProcesses(data.processes || []);
        setResult('Lista de procesos actualizada.');
      } else {
        setResult(typeof data.output === 'string' ? data.output : (data.matches ? data.raw : JSON.stringify(data, null, 2)));
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const killProcess = async (pid: number, name: string) => {
    if (!confirm(`¿Estás seguro de matar el proceso ${name} (PID: ${pid})?`)) return;
    try {
      const res = await fetch(`http://localhost:7860/v1/security/kill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pid })
      });
      const data = await res.json();
      if (res.ok) {
        showToast('success', data.message || `Proceso ${name} terminado.`);
        execute(); // Refresh list
      } else {
        showToast('error', `Error: ${data.error}`);
      }
    } catch (e: any) {
      showToast('error', `Error de conexión: ${e.message}`);
    }
  };

  const cfg = TOOL_CONFIGS[mode];

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-5xl mx-auto space-y-8">
        
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-surface border border-border-subtle shadow-[0_0_20px_rgba(168,85,247,0.1)]">
            <Zap className="text-accent-secondary" size={28} />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Tools Pro</h1>
            <p className="text-text-muted mt-1 font-medium">Suite de herramientas avanzadas: Grep, Git, Web Search, Code Runner y Process Manager.</p>
          </div>
        </div>

        {/* Tool Selector */}
        <div className="flex gap-2 p-1 bg-surface border border-border-subtle rounded-xl w-fit overflow-x-auto">
          {(Object.entries(TOOL_CONFIGS) as [ToolMode, typeof cfg][]).map(([key, c]) => (
            <button
              key={key}
              onClick={() => { setMode(key); setResult(null); setError(null); if(key==='process') setInput(''); }}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all whitespace-nowrap
                ${mode === key ? 'bg-accent-secondary text-white shadow-lg' : 'text-text-muted hover:text-text-primary'}`}
            >
              {c.icon} {c.label}
            </button>
          ))}
        </div>

        {/* Input Area */}
        <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
          <div className="p-3 border-b border-border-subtle bg-surface/30 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="text-accent-secondary">{cfg.icon}</div>
              <span className="text-xs font-black uppercase tracking-widest text-text-muted">{cfg.label}</span>
            </div>
            {mode === 'process' && (
               <button onClick={execute} className="p-1.5 hover:bg-white/10 rounded-lg text-accent-secondary transition-all">
                  <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
               </button>
            )}
          </div>
          <div className="p-6 space-y-4">
            {mode === 'run' ? (
              <textarea
                rows={8}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={cfg.placeholder}
                className="w-full bg-black/40 border border-border-subtle rounded-xl p-4 font-mono text-xs text-accent-secondary outline-none focus:border-accent-secondary resize-none"
              />
            ) : mode === 'process' ? (
              <div className="bg-accent-primary/5 p-4 rounded-xl border border-accent-primary/20 text-xs text-text-muted leading-relaxed">
                <p className="font-bold text-text-primary mb-1">Modo Gestión de Procesos</p>
                Visualiza los procesos pesados del sistema (Motores IA, Python, Node) y libera RAM cerrando los que no necesites, como <strong>Fooocus</strong> o <strong>Ollama</strong>.
              </div>
            ) : (
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && execute()}
                placeholder={cfg.placeholder}
                className="w-full bg-surface border border-border-subtle rounded-xl px-4 py-3 text-sm text-text-primary outline-none focus:border-accent-secondary"
              />
            )}
            <button
              onClick={execute}
              disabled={loading || (mode !== 'process' && !input.trim())}
              className="w-full py-3 rounded-xl bg-accent-secondary text-white font-black flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-95 transition-all shadow-lg disabled:opacity-50"
            >
              {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : (mode === 'process' ? <RefreshCw size={16} /> : <Send size={16} />)}
              {loading ? 'EJECUTANDO...' : (mode === 'process' ? 'ACTUALIZAR PROCESOS' : 'EJECUTAR HERRAMIENTA')}
            </button>
          </div>
        </div>

        {/* Process Table Mode */}
        {mode === 'process' && processes.length > 0 && (
          <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden animate-in fade-in zoom-in-95 duration-300">
            <div className="p-3 border-b border-border-subtle bg-surface/30 flex items-center gap-2 text-xs font-black uppercase tracking-widest text-accent-primary">
              <Cpu size={14} /> PROCESOS DETECTADOS
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface/50 border-b border-border-subtle">
                  <tr className="text-text-muted font-black uppercase tracking-tighter">
                    <th className="p-4">PID</th>
                    <th className="p-4">Nombre</th>
                    <th className="p-4">CPU %</th>
                    <th className="p-4">RAM MB</th>
                    <th className="p-4 text-right">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle/30">
                  {processes.map((p) => (
                    <tr key={p.pid} className="hover:bg-white/5 transition-colors group">
                      <td className="p-4 font-mono text-text-muted">{p.pid}</td>
                      <td className="p-4 font-bold text-text-primary">{p.name}</td>
                      <td className="p-4">
                        <span className={`font-bold ${p.cpu > 5 ? 'text-status-warning' : 'text-text-muted'}`}>{p.cpu}%</span>
                      </td>
                      <td className="p-4 font-bold text-accent-secondary">{p.ram} MB</td>
                      <td className="p-4 text-right">
                        <button 
                          onClick={() => killProcess(p.pid, p.name)}
                          className="p-2 rounded-lg bg-status-error/10 text-status-error opacity-0 group-hover:opacity-100 hover:bg-status-error hover:text-white transition-all shadow-sm"
                          title="Matar proceso"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Result Area (Non-Process Mode) */}
        {mode !== 'process' && (result || error) && (
          <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
            <div className={`p-3 border-b border-border-subtle bg-surface/30 flex items-center gap-2 text-xs font-black uppercase tracking-widest
              ${error ? 'text-status-error' : 'text-status-success'}`}>
              {error ? <AlertCircle size={14} /> : <CheckCircle size={14} />}
              {error ? 'ERROR' : 'RESULTADO'}
            </div>
            <pre className={`p-6 text-[11px] font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto scrollbar-hide
              ${error ? 'text-status-error' : 'text-text-primary'}`}>
              {error || result}
            </pre>
          </div>
        )}

      </div>
    </div>
  );
};
