import React, { useState, useEffect, useRef } from 'react';
import { Target, ExternalLink, Copy, CheckCircle2, AlertCircle, RefreshCw, Trash2, Settings, Save, X, Play, Square } from 'lucide-react';
import { showToast } from './Toast';

interface Bounty {
  title: string;
  url: string;
  platform: string;
  date: string;
  description: string;
  proposal: string;
}

export const BountyHunter: React.FC = () => {
  const [bounties, setBounties] = useState<Bounty[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  
  const [bountyProfile, setBountyProfile] = useState<string>("");
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [daemonRunning, setDaemonRunning] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const previousCountRef = useRef<number>(0);

  const playDing = () => {
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioContextClass) return;
      const ctx = new AudioContextClass();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.start();
      osc.stop(ctx.currentTime + 0.5);
    } catch(e) {}
  };

  const fetchBounties = async () => {
    try {
      setLoading(true);
      const res = await fetch('/v1/bounties');
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || 'Error al obtener micro-trabajos');
      const newBounties = data.bounties || [];
      
      if (newBounties.length > previousCountRef.current && previousCountRef.current !== 0) {
        playDing();
      }
      previousCountRef.current = newBounties.length;
      
      setBounties(newBounties);
      if (data.bounty_profile && !isEditingProfile) {
        setBountyProfile(data.bounty_profile);
      }
      setError(null);
      setLastUpdate(new Date());

      const statRes = await fetch('/v1/bounties/status');
      if (statRes.ok) {
        const statData = await statRes.json();
        setDaemonRunning(statData.running);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBounties();
    const interval = setInterval(fetchBounties, 30000);
    return () => clearInterval(interval);
  }, []);

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleAction = async (url: string, action: string) => {
    setBounties(prev => prev.filter(b => b.url !== url));
    previousCountRef.current -= 1;
    try {
      const res = await fetch('/v1/bounties/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, action })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        showToast('error', errData.error || 'Error al actualizar estado del contrato');
      }
    } catch(e: any) {
      console.error(e);
      showToast('error', 'Error de red al actualizar estado');
    }
  };

  const saveProfile = async () => {
    try {
      const res = await fetch('/v1/bounties/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile: bountyProfile })
      });
      if (res.ok) {
        setIsEditingProfile(false);
        showToast('success', 'Perfil guardado con éxito');
      } else {
        const errData = await res.json().catch(() => ({}));
        showToast('error', errData.error || 'Error al guardar perfil');
      }
    } catch(e: any) {
      console.error(e);
      showToast('error', 'Error de conexión');
    }
  };

  const toggleDaemon = async () => {
    setActionLoading(true);
    try {
      const endpoint = daemonRunning ? '/v1/bounties/stop' : '/v1/bounties/start';
      const res = await fetch(endpoint, { method: 'POST' });
      if (res.ok) {
        setDaemonRunning(!daemonRunning);
        showToast('success', `Daemon ${daemonRunning ? 'detenido' : 'iniciado'} exitosamente`);
      } else {
        throw new Error("Error en servidor");
      }
    } catch(e) {
      showToast('error', 'Error al cambiar estado del daemon');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAutoApply = async (url: string, proposal: string) => {
    try {
      const res = await fetch('/v1/infiltrator/queue_bid', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, proposal })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.error || 'Error al encolar auto-apply');
      }
      showToast('info', 'Oferta enviada al Infiltrador. Revisa el Dashboard del Infiltrador para ver el progreso.');
    } catch(e: any) {
      console.error(e);
      showToast('error', e.message || 'Error: Asegúrate de que el backend esté ejecutándose.');
    }
  };

  return (
    <div className="h-full flex flex-col bg-bg/50 overflow-hidden">
      {/* Header */}
      <div className="flex-none p-6 pb-2 border-b border-border-subtle bg-surface/50 backdrop-blur-md z-10 flex justify-between items-end">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 bg-accent-primary/10 rounded-lg text-accent-primary">
              <Target size={24} />
            </div>
            <h1 className="text-2xl font-bold text-text-primary">Bounty Hunter</h1>
          </div>
          <p className="text-text-muted text-sm ml-12">Agencia Autónoma de Micro-Trabajos</p>
        </div>
        
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2 text-text-muted">
            <span className="text-xs mr-2 hidden sm:inline">Última rev: {lastUpdate.toLocaleTimeString()}</span>
            <div className={`w-2 h-2 rounded-full ${daemonRunning ? 'bg-status-success animate-pulse' : 'bg-text-muted'}`}></div>
            <span>{daemonRunning ? 'Daemon Activo' : 'Apagado'}</span>
          </div>
          <button 
            onClick={toggleDaemon}
            disabled={actionLoading}
            className={`flex items-center gap-2 px-3 py-1.5 border rounded-lg transition-colors font-bold ${
              daemonRunning 
              ? 'bg-status-error/10 text-status-error border-status-error/30 hover:bg-status-error/20'
              : 'bg-accent-primary/10 text-accent-primary border-accent-primary/30 hover:bg-accent-primary/20'
            }`}
          >
            {daemonRunning ? <><Square size={14} fill="currentColor" /> Detener Motor</> : <><Play size={14} fill="currentColor" /> Iniciar Escaneo</>}
          </button>
          <button 
            onClick={() => setIsEditingProfile(!isEditingProfile)}
            className="flex items-center gap-2 px-3 py-1.5 bg-card hover:bg-surface border border-border-subtle rounded-lg text-text-primary transition-colors"
          >
            <Settings size={14} /> Perfil
          </button>
          <button 
            onClick={fetchBounties}
            className="flex items-center gap-2 px-3 py-1.5 bg-card hover:bg-surface border border-border-subtle rounded-lg text-text-primary transition-colors"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Actualizar
          </button>
        </div>
      </div>

      {isEditingProfile && (
        <div className="flex-none p-6 border-b border-border-subtle bg-surface/30">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-sm font-bold text-text-primary">Perfil del Freelancer (Skills y Experiencia)</h3>
            <button onClick={() => setIsEditingProfile(false)} className="text-text-muted hover:text-text-primary">
              <X size={16} />
            </button>
          </div>
          <p className="text-xs text-text-muted mb-3">La IA utilizará esto como base para redactar tus propuestas de venta.</p>
          <textarea
            value={bountyProfile}
            onChange={(e) => setBountyProfile(e.target.value)}
            className="w-full h-24 p-3 bg-bg border border-border-subtle rounded-lg text-sm text-text-primary focus:outline-none focus:border-accent-primary transition-colors mb-3"
            placeholder="Ej: Eres un desarrollador web experto en React y Python con 5 años de experiencia..."
          />
          <button 
            onClick={saveProfile}
            className="flex items-center gap-2 px-4 py-2 bg-accent-primary text-black font-bold rounded-lg hover:bg-accent-primary/90 transition-colors"
          >
            <Save size={16} /> Guardar Perfil
          </button>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 scrollbar-hide">
        {error && (
          <div className="mb-6 p-4 bg-status-error/10 border border-status-error/30 rounded-xl flex items-center gap-3 text-status-error">
            <AlertCircle size={20} />
            <p className="font-medium">{error}</p>
          </div>
        )}

        {bounties.length === 0 && !loading && !error && (
          <div className="h-64 flex flex-col items-center justify-center text-text-muted">
            <Target size={48} className="mb-4 opacity-20" />
            <p className="text-lg font-medium">Buscando contratos lucrativos...</p>
            <p className="text-sm mt-2 text-center max-w-md">El demonio está rastreando en segundo plano en base a tus parámetros.</p>
          </div>
        )}

        <div className="grid gap-6">
          {bounties.map((bounty, i) => (
            <div key={i} className="glass-card bg-card/80 border border-border-subtle rounded-xl p-5 shadow-lg relative group transition-all hover:border-accent-primary/50 hover:shadow-accent-primary/10 hover:-translate-y-0.5">
              
              {/* Badge Platform */}
              <div className="absolute top-4 right-4 text-xs font-bold px-2 py-1 bg-accent-primary/10 text-accent-primary rounded uppercase tracking-wider">
                {bounty.platform}
              </div>

              <div className="pr-20">
                <a href={bounty.url} target="_blank" rel="noopener noreferrer" className="flex items-start gap-2 group/title">
                  <h3 className="text-lg font-bold text-text-primary group-hover/title:text-accent-primary transition-colors line-clamp-2">
                    {bounty.title}
                  </h3>
                  <ExternalLink size={14} className="mt-1.5 opacity-0 group-hover/title:opacity-100 transition-opacity text-accent-primary" />
                </a>
                <p className="text-xs text-text-muted mt-1">{bounty.date}</p>
              </div>

              <div className="mt-4 p-3 bg-bg/50 rounded-lg text-sm text-text-muted border border-border-subtle/50 line-clamp-3">
                {bounty.description || "Sin descripción detallada."}
              </div>

              <div className="mt-4 pt-4 border-t border-border-subtle flex items-start gap-4">
                <div className="flex-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2">Propuesta de IA Generada</div>
                  <div className="text-sm text-text-primary whitespace-pre-wrap">
                    {bounty.proposal || "Error al generar la propuesta."}
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleAction(bounty.url, 'discarded')}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg font-bold border border-border-subtle text-text-muted hover:text-status-error hover:border-status-error/50 transition-all shrink-0"
                    title="Descartar"
                  >
                    <Trash2 size={16} />
                  </button>
                  <button
                    onClick={() => handleAction(bounty.url, 'applied')}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg font-bold border border-border-subtle text-text-muted hover:text-status-success hover:border-status-success/50 transition-all shrink-0"
                    title="Marcar como Aplicado"
                  >
                    <CheckCircle2 size={16} />
                  </button>
                  <button
                    onClick={() => copyToClipboard(bounty.proposal, i)}
                    className={`shrink-0 flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all ${
                      copiedIndex === i 
                        ? 'bg-status-success text-black' 
                        : 'bg-accent-primary text-black hover:bg-accent-primary/90'
                    }`}
                  >
                    {copiedIndex === i ? <CheckCircle2 size={16} /> : <Copy size={16} />}
                    {copiedIndex === i ? 'COPIADO' : 'COPIAR PROPUESTA'}
                  </button>
                  <button
                    onClick={() => handleAutoApply(bounty.url, bounty.proposal)}
                    className="shrink-0 flex items-center gap-2 px-4 py-2 rounded-lg font-bold bg-[#FF3366] text-white hover:bg-[#FF3366]/90 transition-all"
                    title="Enviar propuesta automáticamente usando el Infiltrador"
                  >
                    <Play size={16} />
                    AUTO APLICAR
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
