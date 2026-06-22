import { useEffect, useState } from 'react';
import { ShieldAlert, CheckCircle, XCircle, Clock, AlertTriangle, Eye, Zap, Lock } from 'lucide-react';
import { showToast } from './Toast';

export const HITLApproval = () => {
  const [pending, setPending] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);

  const fetchPending = async () => {
    try {
      const res = await fetch('/v1/hitl/pending');
      if (res.ok) {
        const data = await res.json();
        setPending(data.pending || []);
      }
    } catch (e) {} finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
    const iv = setInterval(fetchPending, 5000);
    return () => clearInterval(iv);
  }, []);

  const decide = async (id: string, action: 'approve' | 'reject') => {
    setProcessing(id);
    try {
      const res = await fetch(`/v1/hitl/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: id })
      });
      if (!res.ok) throw new Error('Fallo en la operación');
      fetchPending();
    } catch (e) {
      showToast('error', `Error al ${action === 'approve' ? 'aprobar' : 'rechazar'} la solicitud`);
    } finally {
      setProcessing(null);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-5xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle shadow-[0_0_20px_rgba(245,158,11,0.1)]">
              <ShieldAlert className="text-status-warning" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">HITL Approval</h1>
              <p className="text-text-muted mt-1 font-medium">Human-In-The-Loop: autorización obligatoria para comandos destructivos o de alto impacto.</p>
            </div>
          </div>
          <div className={`px-4 py-2 rounded-xl border font-black text-xs uppercase tracking-widest flex items-center gap-2
            ${pending.length > 0 ? 'bg-status-warning/10 text-status-warning border-status-warning/30 animate-pulse' : 'bg-status-success/10 text-status-success border-status-success/20'}`}>
            <Lock size={14} />
            {pending.length > 0 ? `${pending.length} PENDIENTE${pending.length > 1 ? 'S' : ''}` : 'OPERACIÓN LIBRE'}
          </div>
        </div>

        {loading ? (
          <div className="py-20 text-center text-text-muted animate-pulse">Cargando solicitudes pendientes...</div>
        ) : pending.length === 0 ? (
          <div className="glass-panel p-16 rounded-2xl border border-border-subtle flex flex-col items-center gap-4 opacity-50">
            <Eye className="text-status-success" size={48} />
            <p className="text-sm font-bold uppercase tracking-widest text-text-muted">No hay solicitudes de autorización pendientes</p>
          </div>
        ) : (
          <div className="space-y-6">
            {pending.map((req) => (
              <div key={req.id} className="glass-panel p-6 rounded-2xl border border-status-warning/30 bg-status-warning/5 space-y-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-xl bg-status-warning/10 text-status-warning">
                      <AlertTriangle size={24} />
                    </div>
                    <div>
                      <div className="flex items-center gap-3">
                        <h3 className="font-black text-text-primary text-lg uppercase tracking-tight">{req.action || 'Comando Crítico'}</h3>
                        <span className="px-2 py-0.5 rounded-full bg-status-warning/20 text-status-warning text-[9px] font-black uppercase tracking-widest border border-status-warning/30">
                          HIGH RISK
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-[10px] font-bold text-text-muted mt-1">
                        <span className="flex items-center gap-1"><Clock size={10} /> {req.timestamp}</span>
                        <span>Solicitado por: <span className="text-accent-primary">{req.source || 'Gravity Agent'}</span></span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-black/40 border border-border-subtle font-mono text-[11px] text-text-primary leading-relaxed">
                  {req.details || req.command || 'Sin detalles adicionales'}
                </div>

                {req.risk_level && (
                  <div className="p-3 rounded-xl bg-status-error/5 border border-status-error/20 text-[10px] font-bold text-status-error uppercase tracking-widest">
                    ⚠ Nivel de riesgo: {req.risk_level} — {req.risk_reason}
                  </div>
                )}

                <div className="flex gap-4">
                  <button
                    onClick={() => decide(req.id, 'approve')}
                    disabled={processing === req.id}
                    className="flex-1 py-3 rounded-xl bg-status-success text-white font-black flex items-center justify-center gap-2 hover:scale-105 transition-all shadow-lg shadow-status-success/20 disabled:opacity-50"
                  >
                    <CheckCircle size={18} /> APROBAR EJECUCIÓN
                  </button>
                  <button
                    onClick={() => decide(req.id, 'reject')}
                    disabled={processing === req.id}
                    className="flex-1 py-3 rounded-xl bg-status-error/10 text-status-error border border-status-error/30 font-black flex items-center justify-center gap-2 hover:bg-status-error hover:text-white transition-all disabled:opacity-50"
                  >
                    <XCircle size={18} /> RECHAZAR
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
          <h3 className="text-xs font-black text-text-muted uppercase tracking-widest mb-4 flex items-center gap-2">
            <Zap size={14} className="text-accent-secondary" /> Protocolo HITL Activo
          </h3>
          <div className="space-y-3 text-xs">
            <PolicyItem label="Auto-reject tras" value="5 minutos sin respuesta" />
            <PolicyItem label="Umbral de activación" value="Comandos que afecten archivos del sistema, APIs externas o procesos activos" />
            <PolicyItem label="Agentes sometidos a control" value="executor, coder, deploy_manager" />
          </div>
        </div>

      </div>
    </div>
  );
};

const PolicyItem = ({ label, value }: any) => (
  <div className="flex justify-between items-start gap-4 text-xs">
    <span className="text-text-muted font-bold shrink-0">{label}:</span>
    <span className="text-text-primary font-medium text-right">{value}</span>
  </div>
);
