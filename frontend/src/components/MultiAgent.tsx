import { useState } from 'react';
import { Bot, Zap, RefreshCw, Layers, ShieldCheck, Sparkles } from 'lucide-react';

export const MultiAgent = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [responses, setResponses] = useState<any[]>([]);

  const runCompare = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResponses([]);
    try {
      const res = await fetch('http://localhost:7860/v1/agent/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: query, n_models: 3 })
      });
      if (res.ok) {
        const data = await res.json();
        setResponses(data.results || []);
      }
    } catch (e) {
      alert('Error en consulta multi-agente');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-7xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle">
              <Layers className="text-accent-primary" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Multi-Agent Processor</h1>
              <p className="text-text-muted mt-1 font-medium">Inferencia paralela y consenso entre múltiples proveedores de IA.</p>
            </div>
          </div>
        </div>

        {/* Input area */}
        <div className="glass-panel p-8 rounded-2xl border border-border-subtle space-y-6 bg-gradient-to-br from-transparent to-accent-primary/5">
          <div className="space-y-4">
            <label className="text-xs font-bold text-text-muted uppercase tracking-widest block">Consulta Maestra</label>
            <textarea 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Escribe una tarea compleja para ser resuelta por consenso..."
              className="w-full bg-card border border-border-subtle rounded-xl p-6 text-lg text-text-primary outline-none focus:border-accent-primary transition-all h-40 resize-none shadow-inner"
            />
          </div>

          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="flex gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface border border-border-subtle text-xs font-bold text-text-muted">
                <Bot size={14} /> 3 Agentes Activos
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface border border-border-subtle text-xs font-bold text-text-muted">
                <ShieldCheck size={14} /> Consenso Activado
              </div>
            </div>
            <button 
              onClick={runCompare}
              disabled={loading || !query.trim()}
              className="w-full md:w-auto px-10 py-4 rounded-xl bg-accent-primary text-white font-black shadow-[0_0_20px_rgba(99,102,241,0.4)] hover:scale-105 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <RefreshCw className="animate-spin" size={20} /> : <Zap size={20} fill="currentColor" />}
              {loading ? 'PROCESANDO...' : 'EJECUTAR INFERENCIA PARALELA'}
            </button>
          </div>
        </div>

        {/* Results grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {loading && [1, 2, 3].map(i => (
            <div key={i} className="glass-panel p-6 rounded-2xl border border-border-subtle animate-pulse space-y-4">
              <div className="h-6 w-32 bg-surface rounded"></div>
              <div className="space-y-2">
                <div className="h-4 w-full bg-surface rounded"></div>
                <div className="h-4 w-full bg-surface rounded"></div>
                <div className="h-4 w-2/3 bg-surface rounded"></div>
              </div>
            </div>
          ))}

          {!loading && responses.length > 0 ? responses.map((resp, i) => (
            <div key={i} className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-4 hover:border-accent-primary transition-all group">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-accent-primary/10 flex items-center justify-center text-accent-primary">
                    <Bot size={18} />
                  </div>
                  <div>
                    <div className="text-sm font-black text-text-primary uppercase tracking-tighter">{resp.provider}</div>
                    <div className="text-[10px] text-text-muted font-bold">{resp.model}</div>
                  </div>
                </div>
                <div className="p-1 rounded-full bg-status-success/20 text-status-success">
                  <ShieldCheck size={12} />
                </div>
              </div>
              <div className="p-4 rounded-xl bg-card border border-border-subtle text-sm text-text-muted leading-relaxed max-h-[300px] overflow-y-auto scrollbar-hide italic">
                "{resp.response}"
              </div>
              <button className="w-full py-2 text-[10px] font-black uppercase tracking-widest text-accent-primary hover:bg-accent-primary/5 rounded-lg transition-colors flex items-center justify-center gap-2">
                <Sparkles size={12} /> Seleccionar como respuesta maestra
              </button>
            </div>
          )) : !loading && query && (
             <div className="lg:col-span-3 py-20 text-center text-text-muted opacity-30 flex flex-col items-center gap-4">
                <Layers size={48} />
                <p className="text-sm font-bold uppercase tracking-widest">Los resultados del consenso aparecerán aquí</p>
             </div>
          )}
        </div>

      </div>
    </div>
  );
};
