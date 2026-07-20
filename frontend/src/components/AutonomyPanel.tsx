import React, { useEffect, useState, useCallback } from 'react';
import {
  Brain, Zap, ShieldCheck, TrendingUp, CheckCircle,
  XCircle, Clock, RefreshCw, Activity, Eye, Code2, Target, Lock,
  BarChart3, ChevronRight, Cpu, Power, PowerOff, Radio
} from 'lucide-react';
import { showToast } from './Toast';

// ── Tipos ────────────────────────────────────────────────────────────────────

interface AutonomyState {
  running: boolean;
  last_cycle_utc: string | null;
  next_cycle_utc: string | null;
  cycles_done: number;
  last_decision: {
    ts: string;
    level: string;
    plan: string;
    n_actions: number;
  } | null;
  last_status_level: string;
  actions_taken: number;
  actions_pending_hitl: number;
  daily_spend_usd: number;
  budget_remaining_usd: number;
}

interface ReflectionState {
  running: boolean;
  last_run_utc: string | null;
  next_run_utc: string | null;
  issues_found: number;
  cycles_done: number;
  patches_pending: number;
}

interface Decision {
  id: number;
  ts: string;
  category: string;
  title: string;
  description: string;
  outcome: string;
  impact_score: number;
  action_taken: string;
}

interface Patch {
  id: string;
  module: string;
  ts: string;
  issue: string;
  patch_file: string;
  status: string;
}

interface Summary {
  total_decisions: number;
  success_rate_pct: number | null;
  avg_impact: number;
  by_category: Record<string, number>;
}

// ── Constantes de nivel ───────────────────────────────────────────────────────

const LEVEL_CONFIG: Record<string, { color: string; bg: string; border: string; label: string }> = {
  'CRÍTICO':     { color: 'text-status-error',   bg: 'bg-status-error/10',   border: 'border-status-error/30',   label: 'CRÍTICO' },
  'ALERTA':      { color: 'text-status-warning',  bg: 'bg-status-warning/10', border: 'border-status-warning/30', label: 'ALERTA' },
  'OPORTUNIDAD': { color: 'text-accent-secondary', bg: 'bg-accent-secondary/10', border: 'border-accent-secondary/30', label: 'OPORTUNIDAD' },
  'NORMAL':      { color: 'text-status-success',  bg: 'bg-status-success/10', border: 'border-status-success/20', label: 'NORMAL' },
};

const OUTCOME_CONFIG: Record<string, { color: string; icon: React.ReactNode }> = {
  success: { color: 'text-status-success', icon: <CheckCircle size={12} /> },
  failure: { color: 'text-status-error',   icon: <XCircle size={12} /> },
  neutral: { color: 'text-text-muted',     icon: <Activity size={12} /> },
  pending: { color: 'text-status-warning', icon: <Clock size={12} /> },
};

const CAT_COLORS: Record<string, string> = {
  content:    'text-blue-400',
  monetize:   'text-green-400',
  system:     'text-purple-400',
  security:   'text-red-400',
  evolution:  'text-yellow-400',
  opportunity:'text-cyan-400',
};

// ── Componente principal ──────────────────────────────────────────────────────

export const AutonomyPanel = () => {
  const [autonomyState, setAutonomyState]   = useState<AutonomyState | null>(null);
  const [reflectionState, setReflectionState] = useState<ReflectionState | null>(null);
  const [decisions, setDecisions]           = useState<Decision[]>([]);
  const [patches, setPatches]               = useState<Patch[]>([]);
  const [summary, setSummary]               = useState<Summary | null>(null);
  const [rules, setRules]                   = useState<string[]>([]);
  const [loading, setLoading]               = useState(true);
  const [processing, setProcessing]         = useState<string | null>(null);
  const [activeTab, setActiveTab]           = useState<'overview' | 'decisions' | 'patches' | 'rules'>('overview');
  const [triggeringOODA, setTriggeringOODA] = useState(false);
  const [triggeringReflection, setTriggeringReflection] = useState(false);
  const [radarOnline, setRadarOnline]       = useState(false);
  const [radarProcessing, setRadarProcessing] = useState(false);
  const [npuStatus, setNpuStatus]           = useState<{online: boolean; models: string[]; error: string | null}>({online: false, models: [], error: null});
  const [npuProcessing, setNpuProcessing]   = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [statusRes, decisionsRes, patchesRes, rulesRes] = await Promise.allSettled([
        fetch('/v1/autonomy/status'),
        fetch('/v1/autonomy/decisions'),
        fetch('/v1/reflection/patches'),
        fetch('/v1/autonomy/rules'),
      ]);

      if (statusRes.status === 'fulfilled' && statusRes.value.ok) {
        const d = await statusRes.value.json().catch(() => null);
        if (d) {
          setAutonomyState(d.autonomy_engine);
          setReflectionState(d.self_reflection);
        }
      }
      if (decisionsRes.status === 'fulfilled' && decisionsRes.value.ok) {
        const d = await decisionsRes.value.json().catch(() => null);
        if (d) {
          setDecisions(d.decisions || []);
          setSummary(d.summary || null);
        }
      }
      if (patchesRes.status === 'fulfilled' && patchesRes.value.ok) {
        const d = await patchesRes.value.json().catch(() => null);
        if (d) setPatches(d.patches || []);
      }
      if (rulesRes.status === 'fulfilled' && rulesRes.value.ok) {
        const d = await rulesRes.value.json().catch(() => null);
        if (d) setRules(d.invariant_rules || []);
      }
      
      const radarRes = await fetch('/v1/radar/status').catch(() => null);
      if (radarRes && radarRes.ok) {
        const rd = await radarRes.json().catch(() => null);
        if (rd) setRadarOnline(rd.online);
      }

      const npuRes = await fetch('/v1/npu/status').catch(() => null);
      if (npuRes && npuRes.ok) {
        const nd = await npuRes.json().catch(() => null);
        if (nd) setNpuStatus(nd);
      }
      
    } catch (_) {}
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    fetchAll();
    const iv = setInterval(fetchAll, 10000);
    return () => clearInterval(iv);
  }, [fetchAll]);

  const triggerOODA = async () => {
    setTriggeringOODA(true);
    try {
      const res = await fetch('/v1/autonomy/trigger', { method: 'POST' });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || 'El orquestador rechazó la operación OODA');
      }
      showToast('success', 'Ciclo OODA forzado exitosamente');
      setTimeout(fetchAll, 3000);
    } catch (e: any) {
      showToast('error', `Error OODA: ${e.message}`);
    }
    finally { setTimeout(() => setTriggeringOODA(false), 2000); }
  };

  const triggerReflection = async () => {
    setTriggeringReflection(true);
    try {
      const res = await fetch('/v1/reflection/trigger', { method: 'POST' });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || 'El orquestador rechazó la operación de Reflexión');
      }
      showToast('success', 'Auto-Reflexión iniciada exitosamente');
      setTimeout(fetchAll, 5000);
    } catch (e: any) {
      showToast('error', `Error Reflexión: ${e.message}`);
    }
    finally { setTimeout(() => setTriggeringReflection(false), 3000); }
  };

  const handleStartRadar = async () => {
    setRadarProcessing(true);
    try { await fetch('/v1/radar/start', { method: 'POST' }); }
    finally { setTimeout(() => { setRadarProcessing(false); fetchAll(); }, 2000); }
  };

  const handleStopRadar = async () => {
    setRadarProcessing(true);
    try { await fetch('/v1/radar/stop', { method: 'POST' }); }
    finally { setTimeout(() => { setRadarProcessing(false); fetchAll(); }, 2000); }
  };

  const handleToggleNpu = async () => {
    setNpuProcessing(true);
    const endpoint = npuStatus.online ? '/v1/npu/stop' : '/v1/npu/start';
    try { 
      const res = await fetch(endpoint, { method: 'POST' });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || 'Error al cambiar estado NPU');
      }
      showToast('success', `Se envió orden para ${npuStatus.online ? 'detener' : 'iniciar'} NPU FastFlowLM`);
    } catch (e: any) {
      showToast('error', e.message);
    }
    finally { setTimeout(() => { setNpuProcessing(false); fetchAll(); }, 3000); }
  };

  const handlePatch = async (patchId: string, action: 'approve' | 'reject') => {
    setProcessing(patchId);
    try {
      const res = await fetch(`/v1/reflection/patches/${patchId}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: action === 'reject' ? JSON.stringify({ reason: 'Rechazado desde dashboard' }) : undefined,
      });
      if (!res.ok) {
         const data = await res.json().catch(() => ({}));
         throw new Error(data.error || `El sistema rechazó la acción de ${action}`);
      }
      showToast('success', `Parche ${action === 'approve' ? 'aprobado' : 'rechazado'} correctamente`);
      fetchAll();
    } catch (e: any) {
      showToast('error', `Fallo al procesar parche: ${e.message}`);
    }
    finally { setProcessing(null); }
  };

  const level     = autonomyState?.last_status_level || 'NORMAL';
  const levelConf = LEVEL_CONFIG[level] || LEVEL_CONFIG['NORMAL'];

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">

        {/* ── Header ── */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle shadow-[0_0_30px_rgba(139,92,246,0.15)]">
              <Brain className="text-accent-primary" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">
                Autonomy Engine
              </h1>
              <p className="text-text-muted mt-1 font-medium text-sm">
                Gravity V30.0 MYTHOS — Empresa peruana autogestionada por IA
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            {/* Nivel de alerta */}
            <div className={`px-4 py-2 rounded-xl border font-black text-xs uppercase tracking-widest flex items-center gap-2
              ${levelConf.bg} ${levelConf.color} ${levelConf.border}
              ${level === 'CRÍTICO' ? 'animate-pulse' : ''}`}>
              <Activity size={14} />
              {levelConf.label}
            </div>

            {/* Botón Reflexión */}
            <button
              onClick={triggerReflection}
              disabled={triggeringReflection}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-surface border border-border-subtle text-text-muted hover:text-accent-secondary hover:border-accent-secondary/40 transition-all text-xs font-bold uppercase tracking-widest disabled:opacity-50"
            >
              <Eye size={14} className={triggeringReflection ? 'animate-spin' : ''} />
              {triggeringReflection ? 'Analizando...' : 'Auto-Reflexión'}
            </button>

            {/* Botón OODA */}
            <button
              onClick={triggerOODA}
              disabled={triggeringOODA || autonomyState?.running}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent-primary/10 border border-accent-primary/30 text-accent-primary hover:bg-accent-primary hover:text-white transition-all text-xs font-black uppercase tracking-widest disabled:opacity-50"
            >
              <Zap size={14} className={triggeringOODA ? 'animate-ping' : ''} />
              {triggeringOODA ? 'Lanzando...' : autonomyState?.running ? 'En ciclo...' : 'Forzar OODA'}
            </button>
          </div>
        </div>
        
        {/* Radar HF Control Banner */}
        <div className="flex items-center justify-between p-4 rounded-xl border bg-surface/50 border-border-subtle shadow-md flex-wrap gap-4">
          <div className="flex items-center gap-3">
             <div className={`p-2 rounded-lg ${radarOnline ? 'bg-status-success/20 text-status-success' : 'bg-status-error/20 text-status-error'}`}>
               <Radio size={20} className={radarOnline ? "animate-pulse" : ""} />
             </div>
             <div>
               <h3 className="text-sm font-bold text-text-primary">Radar de Alta Frecuencia (HF)</h3>
               <p className="text-xs text-text-muted">Escaneo global autónomo sub-minuto para urgencias.</p>
             </div>
          </div>
          <div>
            {!radarOnline ? (
              <button 
                 onClick={handleStartRadar}
                 disabled={radarProcessing}
                 className="flex items-center gap-2 px-6 py-2 rounded-xl bg-accent-primary/20 border border-accent-primary/30 text-accent-primary hover:bg-accent-primary hover:text-white transition-all text-xs font-black uppercase tracking-widest disabled:opacity-50"
               >
                 <Power size={14} className={radarProcessing ? "animate-spin" : ""} />
                 {radarProcessing ? 'INICIANDO...' : 'INICIAR RADAR'}
               </button>
            ) : (
              <button 
                 onClick={handleStopRadar}
                 disabled={radarProcessing}
                 className="flex items-center gap-2 px-6 py-2 rounded-xl bg-status-error/10 border border-status-error/30 text-status-error hover:bg-status-error/20 transition-all text-xs font-bold uppercase tracking-widest disabled:opacity-50"
               >
                 <PowerOff size={14} className={radarProcessing ? "animate-spin" : ""} />
                 {radarProcessing ? 'APAGANDO...' : 'APAGAR RADAR'}
               </button>
            )}
          </div>
        </div>

        {/* NPU AMD XDNA Banner */}
        <div className={`flex items-center justify-between p-4 rounded-xl border bg-surface/50 flex-wrap gap-4 ${
          npuStatus.online
            ? 'border-violet-500/30 shadow-[0_0_20px_rgba(139,92,246,0.1)]'
            : npuStatus.error ? 'border-status-error/20' : 'border-border-subtle'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${
              npuStatus.online ? 'bg-violet-500/20 text-violet-400' : 'bg-surface text-text-muted'
            }`}>
              <Cpu size={20} className={npuStatus.online ? 'animate-pulse' : ''} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                NPU AMD XDNA (FastFlowLM)
                {npuStatus.online && (
                  <span className="px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-400 text-[10px] font-black uppercase tracking-widest">ONLINE</span>
                )}
              </h3>
              <p className="text-xs text-text-muted">
                {npuStatus.online
                  ? `${npuStatus.models.length} modelo(s) disponible(s): ${npuStatus.models.join(', ') || 'detectando...'}`
                  : npuStatus.error || 'FastFlowLM no detectado en puerto 52625.'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {npuStatus.error && !npuStatus.online && (
              <span className="text-[10px] text-status-error font-bold px-3 py-1 rounded-lg border border-status-error/20 bg-status-error/5">
                Error de driver AMD XDNA
              </span>
            )}
            <span className={`text-[10px] font-black uppercase px-3 py-1 rounded-lg border ${
              npuStatus.online
                ? 'text-violet-400 border-violet-500/30 bg-violet-500/10'
                : 'text-text-muted border-border-subtle bg-surface'
            }`}>
              Puerto 52625
            </span>
            <button 
              onClick={handleToggleNpu}
              disabled={npuProcessing}
              className={`ml-2 px-4 py-1.5 rounded-lg font-bold text-[10px] uppercase tracking-widest transition-all disabled:opacity-50 flex items-center gap-2 ${
                npuStatus.online 
                  ? 'bg-status-error/10 text-status-error border border-status-error/20 hover:bg-status-error/20' 
                  : 'bg-violet-500 text-white hover:bg-violet-600 shadow-lg shadow-violet-500/20'
              }`}
            >
              {npuProcessing ? (
                <><RefreshCw size={12} className="animate-spin" /> PROCESANDO...</>
              ) : npuStatus.online ? (
                <><PowerOff size={12} /> DETENER NPU</>
              ) : (
                <><Cpu size={12} /> INICIAR NPU XDNA</>
              )}
            </button>
          </div>
        </div>


        {loading ? (
          <div className="py-16 text-center text-text-muted animate-pulse">Cargando estado del engine...</div>
        ) : (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard icon={<RefreshCw size={18} />} label="Ciclos OODA" value={autonomyState?.cycles_done ?? 0} color="text-accent-primary" />
              <MetricCard icon={<Target size={18} />} label="Acciones tomadas" value={autonomyState?.actions_taken ?? 0} color="text-status-success" />
              <MetricCard icon={<Clock size={18} />} label="Pendientes HITL" value={autonomyState?.actions_pending_hitl ?? 0} color="text-status-warning" />
              <MetricCard icon={<Code2 size={18} />} label="Parches pendientes" value={reflectionState?.patches_pending ?? 0} color="text-accent-secondary" />
            </div>

            {/* Budget row */}
            <div className="glass-panel p-5 rounded-2xl border border-border-subtle">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-black text-text-muted uppercase tracking-widest flex items-center gap-2">
                  <Cpu size={12} /> Presupuesto diario de autonomía
                </span>
                <span className="text-xs font-bold text-text-primary">
                  ${autonomyState?.daily_spend_usd?.toFixed(3) ?? '0.000'} /
                  ${(autonomyState?.daily_spend_usd ?? 0) + (autonomyState?.budget_remaining_usd ?? 0.50)}.50
                </span>
              </div>
              <div className="w-full bg-black/40 rounded-full h-2">
                <div
                  className="h-2 rounded-full transition-all duration-700 bg-gradient-to-r from-accent-primary to-accent-secondary"
                  style={{ width: `${Math.min(100, ((autonomyState?.daily_spend_usd ?? 0) / 0.50) * 100)}%` }}
                />
              </div>
              <div className="flex justify-between mt-2 text-[10px] text-text-muted font-bold">
                <span>Gastado: ${autonomyState?.daily_spend_usd?.toFixed(3) ?? '0.000'}</span>
                <span>Restante: ${autonomyState?.budget_remaining_usd?.toFixed(3) ?? '0.500'}</span>
              </div>
            </div>

            {/* ── Tabs ── */}
            <div className="flex gap-1 bg-surface/50 p-1 rounded-xl border border-border-subtle w-fit">
              {(['overview', 'decisions', 'patches', 'rules'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all
                    ${activeTab === tab
                      ? 'bg-accent-primary text-white shadow-md'
                      : 'text-text-muted hover:text-text-primary'}`}
                >
                  {tab === 'overview'   && 'Resumen'}
                  {tab === 'decisions'  && `Decisiones ${decisions.length > 0 ? `(${decisions.length})` : ''}`}
                  {tab === 'patches'    && `Parches ${patches.length > 0 ? `(${patches.length})` : ''}`}
                  {tab === 'rules'      && 'Reglas'}
                </button>
              ))}
            </div>

            {/* ── Tab Content ── */}

            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Última decisión */}
                {autonomyState?.last_decision ? (
                  <div className="glass-panel p-6 rounded-2xl border border-accent-primary/20 bg-accent-primary/5">
                    <div className="flex items-center gap-3 mb-4">
                      <Brain size={16} className="text-accent-primary" />
                      <h3 className="text-xs font-black text-text-muted uppercase tracking-widest">
                        Última decisión OODA
                      </h3>
                      <span className="ml-auto text-[10px] text-text-muted font-mono">
                        {autonomyState.last_decision.ts?.slice(0, 19)}
                      </span>
                    </div>
                    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest mb-3
                      ${(LEVEL_CONFIG[autonomyState.last_decision.level] || LEVEL_CONFIG['NORMAL']).bg}
                      ${(LEVEL_CONFIG[autonomyState.last_decision.level] || LEVEL_CONFIG['NORMAL']).color}
                      border ${(LEVEL_CONFIG[autonomyState.last_decision.level] || LEVEL_CONFIG['NORMAL']).border}`}>
                      <Activity size={10} />
                      {autonomyState.last_decision.level} — {autonomyState.last_decision.n_actions} acción(es)
                    </div>
                    <div className="p-4 rounded-xl bg-black/40 border border-border-subtle font-mono text-[11px] text-text-primary leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
                      {autonomyState.last_decision.plan || 'Sin plan disponible'}
                    </div>
                  </div>
                ) : (
                  <div className="glass-panel p-12 rounded-2xl border border-border-subtle flex flex-col items-center gap-4 opacity-50">
                    <Brain size={40} className="text-text-muted" />
                    <p className="text-sm font-bold uppercase tracking-widest text-text-muted">
                      Ningún ciclo OODA ejecutado aún
                    </p>
                    <p className="text-xs text-text-muted text-center max-w-xs">
                      El primer ciclo se lanzará ~60s después del arranque del servidor, o usa el botón "Forzar OODA".
                    </p>
                  </div>
                )}

                {/* Estadísticas de memoria estratégica */}
                {summary && (
                  <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
                    <h3 className="text-xs font-black text-text-muted uppercase tracking-widest mb-4 flex items-center gap-2">
                      <BarChart3 size={12} className="text-accent-secondary" /> Memoria Estratégica (30 días)
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                      <StatBox label="Decisiones" value={summary.total_decisions} />
                      <StatBox label="Tasa éxito" value={summary.success_rate_pct != null ? `${summary.success_rate_pct}%` : 'N/A'} />
                      <StatBox label="Impact avg" value={summary.avg_impact?.toFixed(2) ?? '0'} />
                      <StatBox label="Categorías activas" value={Object.keys(summary.by_category || {}).length} />
                    </div>
                    {Object.keys(summary.by_category || {}).length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-4">
                        {Object.entries(summary.by_category).map(([cat, cnt]) => (
                          <span key={cat} className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase border border-border-subtle bg-surface/60
                            ${CAT_COLORS[cat] || 'text-text-muted'}`}>
                            {cat} ×{cnt}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Self-Reflection status */}
                <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
                  <h3 className="text-xs font-black text-text-muted uppercase tracking-widest mb-4 flex items-center gap-2">
                    <Eye size={12} className="text-accent-secondary" /> Self-Reflection Engine
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <InfoRow label="Ciclos de reflexión" value={reflectionState?.cycles_done ?? 0} />
                    <InfoRow label="Problemas detectados" value={reflectionState?.issues_found ?? 0} />
                    <InfoRow label="Parches pendientes" value={reflectionState?.patches_pending ?? 0} />
                    <InfoRow label="Último análisis" value={(reflectionState?.last_run_utc ?? 'nunca').slice(0, 19)} />
                    <InfoRow label="Próximo análisis" value={(reflectionState?.next_run_utc ?? '?').slice(0, 19)} />
                    <InfoRow label="En ejecución" value={reflectionState?.running ? 'SÍ' : 'NO'} />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'decisions' && (
              <div className="space-y-3">
                {decisions.length === 0 ? (
                  <div className="glass-panel p-12 rounded-2xl border border-border-subtle flex flex-col items-center gap-4 opacity-50">
                    <TrendingUp size={40} className="text-text-muted" />
                    <p className="text-sm font-bold uppercase tracking-widest text-text-muted">Sin decisiones registradas</p>
                  </div>
                ) : decisions.map(d => {
                  const oc = OUTCOME_CONFIG[d.outcome] || OUTCOME_CONFIG['pending'];
                  return (
                    <div key={d.id} className="glass-panel p-5 rounded-2xl border border-border-subtle hover:border-accent-primary/30 transition-all group">
                      <div className="flex items-start gap-4">
                        <div className={`p-2 rounded-lg bg-surface/60 ${CAT_COLORS[d.category] || 'text-text-muted'}`}>
                          <ChevronRight size={14} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 flex-wrap mb-1">
                            <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full border border-border-subtle bg-surface/60 ${CAT_COLORS[d.category] || 'text-text-muted'}`}>
                              {d.category}
                            </span>
                            <span className={`flex items-center gap-1 text-[10px] font-black ${oc.color}`}>
                              {oc.icon} {d.outcome}
                            </span>
                            {d.impact_score !== 0 && (
                              <span className={`text-[10px] font-bold ${d.impact_score > 0 ? 'text-status-success' : 'text-status-error'}`}>
                                {d.impact_score > 0 ? '+' : ''}{d.impact_score?.toFixed(2)}
                              </span>
                            )}
                            <span className="ml-auto text-[10px] text-text-muted font-mono">{d.ts?.slice(0, 19)}</span>
                          </div>
                          <h4 className="font-bold text-sm text-text-primary leading-tight">{d.title}</h4>
                          {d.description && (
                            <p className="text-xs text-text-muted mt-1 line-clamp-2">{d.description}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {activeTab === 'patches' && (
              <div className="space-y-4">
                {patches.length === 0 ? (
                  <div className="glass-panel p-12 rounded-2xl border border-border-subtle flex flex-col items-center gap-4 opacity-50">
                    <Code2 size={40} className="text-text-muted" />
                    <p className="text-sm font-bold uppercase tracking-widest text-text-muted">Sin parches pendientes</p>
                    <p className="text-xs text-text-muted text-center max-w-xs">
                      Gravity generará propuestas de mejora de código automáticamente durante los ciclos de auto-reflexión.
                    </p>
                  </div>
                ) : patches.map(p => (
                  <div key={p.id} className="glass-panel p-6 rounded-2xl border border-accent-secondary/30 bg-accent-secondary/5 space-y-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-3 mb-1">
                          <Code2 size={14} className="text-accent-secondary" />
                          <span className="text-xs font-black text-accent-secondary uppercase tracking-widest">{p.module}</span>
                          <span className="text-[10px] text-text-muted font-mono">{p.ts?.slice(0, 19)}</span>
                        </div>
                        <p className="text-sm text-text-primary font-medium leading-relaxed">{p.issue}</p>
                        <p className="text-[10px] text-text-muted font-mono mt-1 truncate">{p.patch_file}</p>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <button
                        onClick={() => handlePatch(p.id, 'approve')}
                        disabled={processing === p.id}
                        className="flex-1 py-2.5 rounded-xl bg-status-success/10 text-status-success border border-status-success/30 font-black text-xs uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-status-success hover:text-white transition-all disabled:opacity-50"
                      >
                        <CheckCircle size={14} /> Aprobar y aplicar
                      </button>
                      <button
                        onClick={() => handlePatch(p.id, 'reject')}
                        disabled={processing === p.id}
                        className="flex-1 py-2.5 rounded-xl bg-status-error/5 text-status-error border border-status-error/20 font-black text-xs uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-status-error hover:text-white transition-all disabled:opacity-50"
                      >
                        <XCircle size={14} /> Rechazar
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'rules' && (
              <div className="glass-panel p-6 rounded-2xl border border-status-error/20 bg-status-error/5 space-y-4">
                <div className="flex items-center gap-3 mb-2">
                  <ShieldCheck size={18} className="text-status-error" />
                  <h3 className="text-sm font-black text-text-primary">Reglas Invariantes del Sistema</h3>
                </div>
                <p className="text-xs text-text-muted">
                  Estas reglas definen los límites absolutos del Autonomy Engine.
                  <span className="text-status-error font-bold"> No pueden ser modificadas por el engine bajo ninguna circunstancia.</span>
                </p>
                <div className="space-y-2 mt-4">
                  {rules.length === 0 ? (
                    <p className="text-text-muted text-sm">Cargando reglas...</p>
                  ) : rules.map((rule, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-black/30 border border-border-subtle">
                      <Lock size={12} className="text-status-error mt-0.5 shrink-0" />
                      <span className="text-xs text-text-primary font-medium">{rule}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

// ── Sub-componentes ───────────────────────────────────────────────────────────

const MetricCard = ({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: string }) => (
  <div className="glass-panel p-5 rounded-2xl border border-border-subtle flex flex-col gap-2">
    <div className={`${color} opacity-80`}>{icon}</div>
    <div className="text-2xl font-black text-text-primary">{value}</div>
    <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">{label}</div>
  </div>
);

const StatBox = ({ label, value }: { label: string; value: string | number }) => (
  <div className="flex flex-col items-center gap-1">
    <div className="text-xl font-black text-text-primary">{value}</div>
    <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest text-center">{label}</div>
  </div>
);

const InfoRow = ({ label, value }: { label: string; value: string | number }) => (
  <div className="flex flex-col gap-0.5">
    <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">{label}</span>
    <span className="text-sm font-bold text-text-primary">{value}</span>
  </div>
);
