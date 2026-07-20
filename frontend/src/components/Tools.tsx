import { useEffect, useState } from 'react';
import { Hammer, Code, Search, FileText, Zap, ExternalLink, Box, Database } from 'lucide-react';
import { showToast } from './Toast';

export const Tools = () => {
  const [tools, setTools] = useState<any[]>([]);

  useEffect(() => {
    // Simular lista de herramientas desde comandos del sistema
    setTools([
      { id: 'grep', name: 'Web Search', desc: 'Búsqueda en tiempo real via Tavily/Google.', icon: <Search size={20} />, status: 'ready', link: 'tools-pro' },
      { id: 'run', name: 'Code Executor', desc: 'Entorno de ejecución Python/JS seguro.', icon: <Code size={20} />, status: 'ready', link: 'tools-pro' },
      { id: 'grep', name: 'File Surgical Editor', desc: 'Edición precisa de código con AST.', icon: <FileText size={20} />, status: 'ready', link: 'tools-pro' },
      { id: 'rag', name: 'RAG Retriever', desc: 'Inyección semántica de documentos.', icon: <Database size={20} />, status: 'ready', link: 'rag' },
      { id: 'git', name: 'Git Manager', desc: 'Control de versiones y pull requests.', icon: <Box size={20} />, status: 'ready', link: 'tools-pro' },
    ]);
  }, []);

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-surface border border-border-subtle">
            <Hammer className="text-accent-secondary" size={28} />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">System Tools</h1>
            <p className="text-text-muted mt-1 font-medium">Caja de herramientas nativas para la manipulación del entorno y datos.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tools.map((t, i) => (
            <div key={i} className="glass-panel p-6 rounded-2xl border border-border-subtle group hover:border-accent-secondary/50 transition-all flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex justify-between items-start">
                   <div className="p-3 rounded-xl bg-accent-secondary/10 text-accent-secondary border border-accent-secondary/20">
                      {t.icon}
                   </div>
                   <div className="px-2 py-0.5 rounded-full bg-status-success/10 text-status-success text-[9px] font-black uppercase tracking-widest border border-status-success/20">
                      {t.status}
                   </div>
                </div>
                <div>
                   <h3 className="text-lg font-black text-text-primary">{t.name}</h3>
                   <p className="text-xs text-text-muted mt-1 font-medium leading-relaxed">{t.desc}</p>
                </div>
              </div>
              <button 
                onClick={() => {
                   // En un entorno SPA real usaríamos un router o setActivePanel. 
                   // Como setActivePanel está en el padre, emitimos un evento custom que el padre escuche o simplemente alertamos por ahora si no podemos inyectar.
                   // Pero basándonos en la estructura, el sidebar ya maneja la navegación. 
                   // Haremos que el botón redirija visualmente a la sección correspondiente.
                   window.dispatchEvent(new CustomEvent('navigate-panel', { detail: t.link }));
                }}
                className="mt-6 w-full py-2 bg-surface border border-border-subtle rounded-lg text-[10px] font-black text-text-muted group-hover:bg-accent-secondary group-hover:text-white group-hover:border-accent-secondary transition-all flex items-center justify-center gap-2"
              >
                 ABRIR HERRAMIENTA <ExternalLink size={12} />
              </button>
            </div>
          ))}
        </div>

        <div className="glass-panel p-8 rounded-2xl border border-border-subtle bg-gradient-to-r from-accent-primary/5 to-accent-secondary/5 flex items-center justify-between">
           <div className="flex items-center gap-6">
              <div className="w-16 h-16 rounded-2xl bg-black/40 flex items-center justify-center text-accent-primary shadow-xl">
                 <Zap size={32} fill="currentColor" />
              </div>
              <div>
                 <h4 className="text-xl font-black text-text-primary">Custom Tool Registry</h4>
                 <p className="text-sm text-text-muted mt-1">Registra nuevos plugins cumpliendo con el protocolo BaseTool para expandir Gravity.</p>
              </div>
           </div>
           <button 
             onClick={() => showToast('info', "Módulo de Registro de Plugins en desarrollo (V30.0 MYTHOS)")}
             className="px-8 py-3 bg-accent-primary text-white font-black rounded-xl shadow-lg hover:scale-105 transition-all"
           >
              REGISTRAR PLUGIN
           </button>
        </div>

      </div>
    </div>
  );
};
