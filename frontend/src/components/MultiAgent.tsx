import { useState, useEffect } from 'react';
import {
  Bot,
  Zap,
  RefreshCw,
  Layers,
  ShieldCheck,
  Sparkles,
  Network,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Clock,
} from 'lucide-react';
import { showToast } from './Toast';

export const MultiAgent = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [responses, setResponses] = useState<any[]>([]);
  const [nModels, setNModels] = useState(3);
  const [mode, setMode] = useState('parallel');

  // ── Estados para Orquestación Paralela V30.3 (OpenCode 2.3) ────────────────
  const [availableAgents, setAvailableAgents] = useState<{ name: string; description: string; provider: string; model: string }[]>([]);
  const [selectedAgents, setSelectedAgents] = useState<string[]>(['backend_specialist', 'qa_tester']);
  const [orchGoal, setOrchGoal] = useState('');
  const [orchId, setOrchId] = useState<string | null>(null);
  const [orchStatus, setOrchStatus] = useState<any>(null);
  const [isDispatching, setIsDispatching] = useState(false);
  const [expandedAgents, setExpandedAgents] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetch('/v1/agents/list')
      .then((res) => res.json())
      .then((data) => {
        if (data.ok && Array.isArray(data.agents)) {
          setAvailableAgents(data.agents);
        }
      })
      .catch((err) => console.error('Error cargando agentes declarativos:', err));
  }, []);

  useEffect(() => {
    if (!orchId) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/v1/agents/status/${orchId}`);
        const data = await res.json();
        if (data.ok) {
          setOrchStatus(data);
          if (data.status === 'done' || data.status === 'failed') {
            clearInterval(interval);
          }
        }
      } catch (e) {
        console.error('Error en polling de orquestación:', e);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [orchId]);

  const handleDispatch = async () => {
    if (!orchGoal.trim() || selectedAgents.length === 0) return;
    setIsDispatching(true);
    try {
      const res = await fetch('/v1/agents/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: orchGoal, agents: selectedAgents }),
      });
      const data = await res.json();
      if (data.ok && data.orchestration_id) {
        setOrchId(data.orchestration_id);
        setOrchStatus(null);
        showToast('success', `Orquestación ${data.orchestration_id} despachada.`);
      } else {
        showToast('error', data.error || 'Error al despachar agentes');
      }
    } catch (err: any) {
      showToast('error', `Fallo al despachar: ${err.message}`);
    } finally {
      setIsDispatching(false);
    }
  };

  const toggleAgentExpand = (name: string) => {
    setExpandedAgents((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const runCompare = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResponses([]);
    try {
      const res = await fetch('/v1/agent/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: query, n_models: nModels, mode: mode })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || 'El orquestador de agentes rechazó la consulta');
      }
      const data = await res.json();
      setResponses(data.results || []);
      showToast('success', 'Inferencia paralela completada exitosamente');
    } catch (e: any) {
      showToast('error', `Fallo de Inferencia: ${e.message}`);
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
              <label className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface border border-border-subtle text-xs font-bold text-text-muted cursor-pointer hover:border-accent-primary transition-all">
                <Bot size={14} className="text-accent-primary" />
                <select 
                  value={nModels} 
                  onChange={(e) => setNModels(+e.target.value)}
                  className="bg-transparent outline-none text-text-primary"
                >
                  <option value={2}>2 Agentes</option>
                  <option value={3}>3 Agentes</option>
                  <option value={5}>5 Agentes</option>
                </select>
              </label>
              <label className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface border border-border-subtle text-xs font-bold text-text-muted cursor-pointer hover:border-accent-secondary transition-all">
                <ShieldCheck size={14} className="text-accent-secondary" />
                <select 
                  value={mode} 
                  onChange={(e) => setMode(e.target.value)}
                  className="bg-transparent outline-none text-text-primary"
                >
                  <option value="parallel">Modo: Paralelo</option>
                  <option value="consensus">Modo: Consenso</option>
                  <option value="debate">Modo: Debate</option>
                </select>
              </label>
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
              <button 
                onClick={() => {
                  navigator.clipboard.writeText(resp.response);
                  showToast('success', 'Respuesta copiada al portapapeles');
                }}
                className="w-full py-2 text-[10px] font-black uppercase tracking-widest text-accent-primary hover:bg-accent-primary/5 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Sparkles size={12} /> Copiar Respuesta
              </button>
            </div>
          )) : !loading && query && (
             <div className="lg:col-span-3 py-20 text-center text-text-muted opacity-30 flex flex-col items-center gap-4">
                <Layers size={48} />
                <p className="text-sm font-bold uppercase tracking-widest">Los resultados del consenso aparecerán aquí</p>
             </div>
          )}
        </div>

        {/* ── Subagentes Declarativos en Paralelo (V30.3 — OpenCode 2.3 Style) ── */}
        <div className="glass-panel p-8 rounded-2xl border border-border-subtle space-y-6 bg-gradient-to-br from-transparent to-accent-secondary/5 mt-12">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-surface border border-border-subtle text-accent-secondary">
                <Network size={22} />
              </div>
              <div>
                <h2 className="text-xl font-extrabold text-text-primary tracking-tight">
                  Orquestación Paralela de Subagentes
                </h2>
                <p className="text-xs text-text-muted font-medium">
                  Arquitectura declarativa (.agents/agents/*.md) con Shared Contract Protocol.
                </p>
              </div>
            </div>
            {orchStatus && (
              <div className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-surface border border-border-subtle text-text-muted">
                ID: <span className="text-accent-primary">{orchStatus.orchestration_id}</span>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-bold text-text-muted uppercase tracking-widest block mb-2">
                Objetivo Global (Shared Contract)
              </label>
              <textarea
                value={orchGoal}
                onChange={(e) => setOrchGoal(e.target.value)}
                placeholder="Ej: Implementar sistema de rate limiting con token bucket en api/ y suites de pruebas en tests/..."
                className="w-full bg-card border border-border-subtle rounded-xl p-4 text-sm text-text-primary outline-none focus:border-accent-secondary transition-all h-24 resize-none shadow-inner"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-text-muted uppercase tracking-widest block mb-2">
                Subagentes Especializados Asignados
              </label>
              <div className="flex flex-wrap gap-2">
                {availableAgents.map((ag) => {
                  const isSelected = selectedAgents.includes(ag.name);
                  return (
                    <button
                      key={ag.name}
                      type="button"
                      onClick={() => {
                        setSelectedAgents((prev) =>
                          isSelected ? prev.filter((x) => x !== ag.name) : [...prev, ag.name]
                        );
                      }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all flex items-center gap-2 ${
                        isSelected
                          ? 'bg-accent-secondary/20 border-accent-secondary text-accent-secondary'
                          : 'bg-surface border-border-subtle text-text-muted hover:border-border-muted'
                      }`}
                    >
                      <Bot size={13} />
                      <span>{ag.name}</span>
                      <span className="text-[10px] opacity-60">({ag.provider || 'auto'})</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleDispatch}
                disabled={isDispatching || !orchGoal.trim() || selectedAgents.length === 0}
                className="px-8 py-3 rounded-xl bg-accent-secondary text-white font-black hover:scale-105 transition-all flex items-center gap-2 disabled:opacity-50 text-xs tracking-wider uppercase shadow-[0_0_20px_rgba(168,85,247,0.4)]"
              >
                {isDispatching ? <RefreshCw className="animate-spin" size={16} /> : <Network size={16} />}
                {isDispatching ? 'Despachando...' : 'Despachar Subagentes en Paralelo'}
              </button>
            </div>
          </div>

          {/* Activity Folding: Tarjetas por Agente */}
          {orchStatus && orchStatus.agents && (
            <div className="space-y-3 pt-4 border-t border-border-subtle">
              <div className="flex items-center justify-between text-xs text-text-muted">
                <span>Progreso de Subagentes:</span>
                <span className={`font-bold uppercase ${
                  orchStatus.status === 'done'
                    ? 'text-status-success'
                    : orchStatus.status === 'failed'
                    ? 'text-status-danger'
                    : 'text-accent-primary animate-pulse'
                }`}>
                  Estado: {orchStatus.status}
                </span>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {Object.entries(orchStatus.agents).map(([agentName, agentData]: [string, any]) => {
                  const isExpanded = !!expandedAgents[agentName];
                  return (
                    <div
                      key={agentName}
                      className="rounded-xl border border-border-subtle bg-card/60 overflow-hidden transition-all"
                    >
                      <div
                        onClick={() => toggleAgentExpand(agentName)}
                        className="flex items-center justify-between p-4 cursor-pointer hover:bg-surface/50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          {isExpanded ? (
                            <ChevronDown size={16} className="text-text-muted" />
                          ) : (
                            <ChevronRight size={16} className="text-text-muted" />
                          )}
                          <span className="text-sm font-black text-text-primary">{agentName}</span>
                          <span className="text-xs text-text-muted">
                            ({agentData.provider || 'auto'} / {agentData.model || 'auto'})
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {agentData.status === 'pending' && (
                            <span className="flex items-center gap-1 text-xs text-text-muted bg-surface px-2.5 py-1 rounded-full border border-border-subtle">
                              <Clock size={12} /> Pendiente
                            </span>
                          )}
                          {agentData.status === 'running' && (
                            <span className="flex items-center gap-1 text-xs text-accent-primary bg-accent-primary/10 px-2.5 py-1 rounded-full border border-accent-primary/30 animate-pulse">
                              <RefreshCw size={12} className="animate-spin" /> Ejecutando
                            </span>
                          )}
                          {agentData.status === 'done' && (
                            <span className="flex items-center gap-1 text-xs text-status-success bg-status-success/10 px-2.5 py-1 rounded-full border border-status-success/30">
                              <CheckCircle2 size={12} /> Completado
                            </span>
                          )}
                          {agentData.status === 'failed' && (
                            <span className="flex items-center gap-1 text-xs text-status-danger bg-status-danger/10 px-2.5 py-1 rounded-full border border-status-danger/30">
                              <XCircle size={12} /> Error
                            </span>
                          )}
                        </div>
                      </div>

                      {isExpanded && (
                        <div className="p-4 border-t border-border-subtle bg-surface/30 text-xs font-mono text-text-muted leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto">
                          {agentData.error ? (
                            <span className="text-status-danger">{agentData.error}</span>
                          ) : (
                            agentData.output_preview || '(Sin salida)'
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
