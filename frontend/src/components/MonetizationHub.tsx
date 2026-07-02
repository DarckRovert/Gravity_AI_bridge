import { useState, useEffect, useCallback } from 'react';
import {
  DollarSign, TrendingUp, Video, Globe, Share2, Tag,
  RefreshCw, CheckCircle, XCircle, Play, Square, BarChart2,
  Clock, ExternalLink, ChevronDown, ChevronUp, Zap,
  AlertTriangle, Info, Send
} from 'lucide-react';

const API = '';

interface RevenueData {
  period_days: number; total_revenue_usd: number; youtube_usd: number;
  youtube_longform_usd: number; youtube_shorts_usd: number;
  affiliate_usd: number; total_views: number; uploads: number;
  uploads_cloned: number;
  by_niche: Record<string, number>; by_lang: Record<string, number>;
  daily_avg_usd: number; monthly_proj_usd: number;
  monthly_proj_with_cloner_usd: number;
  lang_cloner_enabled_langs: string[];
  disclaimer: string;
}
interface YouTubeStatus {
  enabled: boolean; ready: boolean; oauth_configured: boolean;
  quota_limit: number; uploads_today?: number;
}
interface SchedulerStatus {
  enabled: boolean; running: boolean; jobs_queued: number; last_topic: string | null;
  last_niche: string | null; config: { enabled: boolean; videos_per_day: number; time_utc: string };
}
interface SocialEntry { enabled: boolean; configured: boolean; uploads_24h: number; setup_url: string; }
interface SocialStatus { tiktok: SocialEntry; instagram: SocialEntry; recent_log?: SocialLog[]; }
interface SocialLog { ts: string; platform: string; job_id: number; status: string; error?: string; }
interface AffiliateStatus { enabled: boolean; niches_covered: number; total_programs: number; ids_configured: string[]; }
interface LangStatus { enabled_languages: string[]; supported_languages: string[]; }
interface TimelineEntry { date: string; revenue_usd: number; }
interface TopJob { job_id: number; revenue_usd: number; views: number; niche_id: string; }

const fmt = (n: number) => `$${n.toFixed(2)}`;
const fmtK = (n: number) => n >= 1000 ? `${(n / 1000).toFixed(1)}K` : String(n);

const Badge = ({ ok, yes, no }: { ok: boolean; yes: string; no: string }) => (
  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold border
    ${ok ? 'bg-status-success/15 text-status-success border-status-success/30'
         : 'bg-status-error/15 text-status-error border-status-error/30'}`}>
    {ok ? <CheckCircle size={9}/> : <XCircle size={9}/>}{ok ? yes : no}
  </span>
);

const KPI = ({ label, value, sub, icon: I, color }: { label: string; value: string; sub?: string; icon: React.ElementType; color: string }) => (
  <div className="glass-card p-4 rounded-xl border border-border-subtle bg-card">
    <div className="flex items-center justify-between mb-1">
      <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">{label}</span>
      <I size={15} className={color}/>
    </div>
    <div className={`text-2xl font-black ${color}`}>{value}</div>
    {sub && <div className="text-[10px] text-text-muted mt-0.5">{sub}</div>}
  </div>
);

const Bar = ({ v, max, color = '#6366f1' }: { v: number; max: number; color?: string }) => (
  <div className="h-1.5 rounded-full bg-border-subtle overflow-hidden">
    <div className="h-full rounded-full transition-all duration-500"
      style={{ width: `${max > 0 ? Math.min((v / max) * 100, 100) : 0}%`, backgroundColor: color }}/>
  </div>
);

const Sec = ({ id, title, icon: I, open, toggle, children }: {
  id: string; title: string; icon: React.ElementType;
  open: boolean; toggle: (id: string) => void; children: React.ReactNode;
}) => (
  <div className="border border-border-subtle rounded-xl overflow-hidden">
    <button onClick={() => toggle(id)}
      className="w-full flex items-center gap-3 px-4 py-3 bg-surface hover:bg-card transition-colors text-left">
      <I size={15} className="text-accent-primary"/>
      <span className="font-bold text-sm flex-1">{title}</span>
      {open ? <ChevronUp size={13}/> : <ChevronDown size={13}/>}
    </button>
    {open && <div className="p-4 bg-bg/60 space-y-3">{children}</div>}
  </div>
);

const Row2 = ({ label, value, mono }: { label: string; value: React.ReactNode; mono?: boolean }) => (
  <div className="flex items-center justify-between p-2.5 bg-surface rounded-lg">
    <span className={`text-xs text-text-muted`}>{label}</span>
    <span className={`text-xs font-bold ${mono ? 'font-mono text-accent-primary' : ''}`}>{value}</span>
  </div>
);

export const MonetizationHub = () => {
  const [revenue, setRevenue]     = useState<RevenueData | null>(null);
  const [yt, setYt]               = useState<YouTubeStatus | null>(null);
  const [sched, setSched]         = useState<SchedulerStatus | null>(null);
  const [social, setSocial]       = useState<SocialStatus | null>(null);
  const [aff, setAff]             = useState<AffiliateStatus | null>(null);
  const [lang, setLang]           = useState<LangStatus | null>(null);
  const [timeline, setTimeline]   = useState<TimelineEntry[]>([]);
  const [topJobs, setTopJobs]     = useState<TopJob[]>([]);
  const [loading, setLoading]     = useState(true);
  const [open, setOpen]           = useState<string>('youtube');
  const [authUrl, setAuthUrl]     = useState('');
  const [msg, setMsg]             = useState('');
  const [cloneJobId, setCloneJobId] = useState('');
  const [cloneLangs, setCloneLangs] = useState('en');
  const [distJobId, setDistJobId]   = useState('');

  const toggle = (id: string) => setOpen(p => p === id ? '' : id);

  const fetchAll = useCallback(async () => {
    const [r1, r2, r3, r4, r5, r6, r7, r8] = await Promise.allSettled([
      fetch(`${API}/v1/revenue/summary?days=30`).then(r => r.ok ? r.json().catch(() => null) : null),
      fetch(`${API}/v1/youtube/status`).then(r => r.ok ? r.json().catch(() => null) : null),
      fetch(`${API}/v1/scheduler/status`).then(r => r.ok ? r.json().catch(() => null) : null),
      fetch(`${API}/v1/social/status`).then(r => r.ok ? r.json().catch(() => null) : null),
      fetch(`${API}/v1/affiliates/status`).then(r => r.ok ? r.json().catch(() => null) : null),
      fetch(`${API}/v1/language/status`).then(r => r.ok ? r.json().catch(() => null) : null),
      fetch(`${API}/v1/revenue/timeline?days=14`).then(r => r.ok ? r.json().catch(() => []) : []),
      fetch(`${API}/v1/revenue/top`).then(r => r.ok ? r.json().catch(() => []) : []),
    ]);
    if (r1.status === 'fulfilled' && r1.value) setRevenue(r1.value);
    if (r2.status === 'fulfilled' && r2.value) setYt(r2.value);
    if (r3.status === 'fulfilled' && r3.value) setSched(r3.value);
    if (r4.status === 'fulfilled' && r4.value) setSocial(r4.value);
    if (r5.status === 'fulfilled' && r5.value) setAff(r5.value);
    if (r6.status === 'fulfilled' && r6.value) setLang(r6.value);
    if (r7.status === 'fulfilled' && r7.value) setTimeline(Array.isArray(r7.value) ? r7.value : []);
    if (r8.status === 'fulfilled' && r8.value) setTopJobs(Array.isArray(r8.value) ? r8.value : []);
    setLoading(false);
  }, []);

  useEffect(() => { fetchAll(); const iv = setInterval(fetchAll, 15000); return () => clearInterval(iv); }, [fetchAll]);

  const post = async (url: string, body: object) => {
    try {
      const r = await fetch(`${API}${url}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const data = await r.json().catch(() => ({}));
      return r.ok ? { ok: true, ...data } : { ok: false, error: data.error || 'Fallo de operación' };
    } catch (e: any) { return { ok: false, error: e.message || 'Error de conexión' }; }
  };

  const triggerScheduler = async () => {
    setMsg('Encolando...');
    const d = await post('/v1/scheduler/trigger', {});
    setMsg(d.ok ? `✅ Job #${d.job_id} encolado: "${d.topic}"` : `❌ ${d.error}`);
    fetchAll();
  };

  const toggleScheduler = async () => {
    setMsg('Cambiando estado...');
    const endpoint = sched?.running ? '/v1/content/stop' : '/v1/content/start';
    const d = await post(endpoint, {});
    setMsg(d.ok ? `✅ Daemon ${sched?.running ? 'detenido' : 'iniciado'} exitosamente` : `❌ ${d.error}`);
    fetchAll();
  };

  const getAuthUrl = async () => {
    const d = await post('/v1/youtube/auth/exchange', {});
    if (!d.ok) {
      try {
        const r = await fetch(`${API}/v1/youtube/auth/url`);
        const j = await r.json().catch(() => ({}));
        if (j.ok) setAuthUrl(j.auth_url);
      } catch (e) {}
    }
  };

  const triggerClone = async () => {
    if (!cloneJobId) return;
    setMsg('Clonando...');
    const langs = cloneLangs.split(',').map(l => l.trim()).filter(Boolean);
    const d = await post('/v1/language/clone', { job_id: parseInt(cloneJobId), languages: langs });
    setMsg(d.ok ? `✅ Clonación iniciada para job #${cloneJobId}` : `❌ ${d.error}`);
  };

  const triggerDist = async () => {
    if (!distJobId) return;
    setMsg('Distribuyendo...');
    const d = await post('/v1/social/distribute', { job_id: parseInt(distJobId) });
    setMsg(d.ok ? `✅ Distribución iniciada para job #${distJobId}` : `❌ ${d.error}`);
  };

  const maxTl  = Math.max(...timeline.map(t => t.revenue_usd), 0.01);
  const maxNich = Math.max(...Object.values(revenue?.by_niche ?? {}), 0.01);

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <RefreshCw size={22} className="animate-spin text-accent-primary"/>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto scrollbar-hide p-5 space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-black bg-gradient-to-r from-accent-primary to-accent-secondary bg-clip-text text-transparent">
            💰 Monetization Hub
          </h1>
          <p className="text-[11px] text-text-muted mt-0.5">Ingresos autónomos · actualización cada 15s</p>
        </div>
        <button onClick={fetchAll} className="p-2 hover:bg-card rounded-lg transition-colors"><RefreshCw size={14}/></button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KPI label="Ingresos 30d"       value={fmt(revenue?.total_revenue_usd ?? 0)}  sub={`Long-form ${fmt(revenue?.youtube_longform_usd ?? 0)} · Shorts ${fmt(revenue?.youtube_shorts_usd ?? 0)}`} icon={DollarSign} color="text-status-success"/>
        <KPI label="Proyección mensual" value={fmt(revenue?.monthly_proj_usd ?? 0)}   sub={(revenue?.monthly_proj_with_cloner_usd ?? 0) > (revenue?.monthly_proj_usd ?? 0) ? `Con Cloner: ${fmt(revenue?.monthly_proj_with_cloner_usd ?? 0)}` : `Promedio ${fmt(revenue?.daily_avg_usd ?? 0)}/día`} icon={TrendingUp} color="text-accent-primary"/>
        <KPI label="Videos publicados"  value={String(revenue?.uploads ?? 0)}         sub={`${revenue?.uploads_cloned ?? 0} clones de idioma`} icon={BarChart2} color="text-status-warning"/>
        <KPI label="Afiliados 30d"      value={fmt(revenue?.affiliate_usd ?? 0)}      sub="Comisiones CPA inyectadas" icon={Tag}        color="text-purple-400"/>
      </div>

      {/* Mensaje de acción */}
      {msg && (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold border
          ${msg.startsWith('✅') ? 'bg-status-success/10 border-status-success/30 text-status-success'
          : msg.startsWith('❌') ? 'bg-status-error/10 border-status-error/30 text-status-error'
          : 'bg-accent-primary/10 border-accent-primary/30 text-accent-primary'}`}>
          <Info size={12}/>{msg}
          <button onClick={() => setMsg('')} className="ml-auto opacity-60 hover:opacity-100"><XCircle size={11}/></button>
        </div>
      )}

      {/* Timeline */}
      {timeline.length > 0 && (
        <div className="glass-card p-4 rounded-xl border border-border-subtle bg-card">
          <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted mb-3">Ingresos diarios — 14 días</div>
          <div className="flex items-end gap-1 h-20">
            {timeline.map(t => (
              <div key={t.date} className="flex-1 flex flex-col items-center gap-1 group relative">
                <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-surface text-[9px] px-1 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 border border-border-subtle">
                  {t.date.slice(5)}: {fmt(t.revenue_usd)}
                </div>
                <div className="w-full rounded-t transition-all duration-300"
                  style={{ height: `${Math.max((t.revenue_usd / maxTl) * 64, 3)}px`,
                    backgroundColor: t.revenue_usd > 0 ? '#6366f1' : '#1f2937' }}/>
                <span className="text-[7px] text-text-muted">{t.date.slice(5)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Desglose por fuente y por idioma */}
      {revenue && (
        <div className="grid grid-cols-2 gap-3">
          {/* YouTube Long-form vs Shorts */}
          <div className="glass-card p-3 rounded-xl border border-border-subtle bg-card space-y-2">
            <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted">YouTube — Fuente</div>
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-text-muted">Long-form</span>
                <span className="font-bold text-accent-primary">{fmt(revenue.youtube_longform_usd)}</span>
              </div>
              <Bar v={revenue.youtube_longform_usd} max={Math.max(revenue.youtube_longform_usd, revenue.youtube_shorts_usd, 0.01)} color="#6366f1"/>
              <div className="flex justify-between items-center text-xs">
                <span className="text-text-muted">Shorts</span>
                <span className="font-bold text-purple-400">{fmt(revenue.youtube_shorts_usd)}</span>
              </div>
              <Bar v={revenue.youtube_shorts_usd} max={Math.max(revenue.youtube_longform_usd, revenue.youtube_shorts_usd, 0.01)} color="#a855f7"/>
              <div className="flex justify-between items-center text-xs">
                <span className="text-text-muted">Afiliados CPA</span>
                <span className="font-bold text-status-success">{fmt(revenue.affiliate_usd)}</span>
              </div>
              <Bar v={revenue.affiliate_usd} max={Math.max(revenue.youtube_longform_usd, revenue.affiliate_usd, 0.01)} color="#22c55e"/>
            </div>
          </div>

          {/* Por idioma */}
          <div className="glass-card p-3 rounded-xl border border-border-subtle bg-card space-y-2">
            <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted">Ingresos por idioma</div>
            {Object.keys(revenue.by_lang ?? {}).length > 0
              ? Object.entries(revenue.by_lang).sort(([,a],[,b]) => b-a).map(([lg, v]) => (
                <div key={lg}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-text-muted uppercase font-bold">{lg}</span>
                    <span className="font-bold text-accent-primary">{fmt(v)}</span>
                  </div>
                  <Bar v={v} max={Math.max(...Object.values(revenue.by_lang), 0.01)} color="#6366f1"/>
                </div>
              ))
              : <div className="text-[10px] text-text-muted italic">Sin datos aún. Los ingresos aparecen tras el primer upload.</div>
            }
            {(revenue.lang_cloner_enabled_langs ?? []).length > 0 && (
              <div className="pt-1 border-t border-border-subtle text-[10px] text-text-muted">
                <span className="text-status-success font-bold">Cloner activo:</span>{' '}
                {revenue.lang_cloner_enabled_langs.join(' · ').toUpperCase()}
                {' '}→ proj. {fmt(revenue.monthly_proj_with_cloner_usd)}/mes
              </div>
            )}
          </div>
        </div>
      )}

      {/* YouTube */}
      <Sec id="youtube" title="YouTube — Monetización AdSense" icon={Video} open={open==='youtube'} toggle={toggle}>
        <div className="grid grid-cols-2 gap-2">
          <Row2 label="Auto-upload" value={<Badge ok={yt?.enabled??false} yes="Activo" no="Inactivo"/>}/>
          <Row2 label="OAuth 2.0"   value={<Badge ok={yt?.oauth_configured??false} yes="Configurado" no="Pendiente"/>}/>
          <Row2 label="Quota hoy"   value={`${yt?.uploads_today??0} / ${yt?.quota_limit??5}`} mono/>
          <Row2 label="Sistema"     value={<Badge ok={yt?.ready??false} yes="Listo" no="Configurar"/>}/>
        </div>
        {!yt?.oauth_configured && (
          <div className="space-y-2">
            <button onClick={getAuthUrl}
              className="w-full py-2 px-4 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-colors flex items-center justify-center gap-2">
              <Video size={12}/> Obtener URL de Autorización OAuth
            </button>
            {authUrl && (
              <a href={authUrl} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-accent-primary hover:underline break-all">
                <ExternalLink size={10}/>{authUrl.slice(0, 80)}…
              </a>
            )}
          </div>
        )}
        {!yt?.enabled && (
          <div className="p-2.5 bg-status-warning/10 border border-status-warning/30 rounded-lg text-[10px] text-text-muted">
            <AlertTriangle size={10} className="inline mr-1 text-status-warning"/>
            Activa en <code className="bg-surface px-1 rounded">config.yaml → youtube.enabled: true</code>
          </div>
        )}
      </Sec>

      {/* Scheduler */}
      <Sec id="scheduler" title="Content Scheduler — Producción Autónoma" icon={Clock} open={open==='scheduler'} toggle={toggle}>
        <div className="grid grid-cols-2 gap-2">
          <Row2 label="Config (yaml)"       value={<Badge ok={sched?.config?.enabled??false} yes="Activa" no="Pausada"/>}/>
          <Row2 label="Daemon Backend"      value={<Badge ok={sched?.running??false} yes="Corriendo" no="Detenido"/>}/>
          <Row2 label="Videos/día"   value={String(sched?.config?.videos_per_day??2)} mono/>
          <Row2 label="Hora UTC"     value={sched?.config?.time_utc??'--'} mono/>
          <Row2 label="Jobs en cola" value={String(sched?.jobs_queued??0)} mono/>
        </div>
        {sched?.last_topic && (
          <div className="p-2.5 bg-surface rounded-lg mt-2">
            <div className="text-[10px] text-text-muted mb-0.5">Último topic generado</div>
            <div className="text-xs font-bold truncate">{sched.last_topic}</div>
            {sched.last_niche && <div className="text-[10px] text-text-muted">Nicho: {sched.last_niche}</div>}
          </div>
        )}
        <div className="flex gap-2 mt-2">
          <button onClick={toggleScheduler}
            className={`flex-1 py-2 px-4 rounded-lg text-white text-xs font-bold transition-colors flex items-center justify-center gap-2 ${
              sched?.running ? 'bg-status-error hover:bg-status-error/80' : 'bg-status-success hover:bg-status-success/80'
            }`}>
            {sched?.running ? <><Square size={12}/> Detener Motor Continuo</> : <><Play size={12}/> Iniciar Motor Continuo</>}
          </button>
          <button onClick={triggerScheduler}
            className="flex-1 py-2 px-4 rounded-lg bg-accent-primary hover:bg-accent-secondary text-white text-xs font-bold transition-colors flex items-center justify-center gap-2">
            <Play size={12}/> Encolar Video (1-vez)
          </button>
        </div>
      </Sec>

      {/* Language Cloner */}
      <Sec id="lang" title="Language Cloner — Multiplicador de Ingresos" icon={Globe} open={open==='lang'} toggle={toggle}>
        <div className="p-2.5 bg-surface rounded-lg">
          <div className="text-[10px] text-text-muted mb-1.5">Idiomas habilitados (Automático)</div>
          <div className="flex gap-1.5 flex-wrap">
            {(lang?.enabled_languages??[]).length > 0
              ? lang!.enabled_languages.map(l => (
                  <span key={l} className="px-2 py-0.5 bg-accent-primary/20 text-accent-primary rounded text-xs font-bold uppercase">{l}</span>
                ))
              : <span className="text-xs text-text-muted italic">Sin idiomas activos en config.yaml</span>
            }
          </div>
        </div>
        <div className="p-2.5 bg-status-success/10 border border-status-success/30 rounded-lg text-[10px] text-text-muted">
          <Zap size={10} className="inline mr-1 text-status-success"/>
          Canal EN tiene CPM $8–15 USD (5× más que ES). 2 videos/día → +$60/mes estimado.
        </div>
        
        <div className="space-y-3 pt-2">
          <div className="text-[10px] text-text-muted font-bold uppercase tracking-widest border-b border-border-subtle pb-1">Clonación Manual a 1-Click</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[10px] text-text-muted ml-1">1. Seleccionar Video</label>
              <select 
                value={cloneJobId} 
                onChange={e => setCloneJobId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-bg border border-border-subtle rounded-lg focus:border-accent-primary outline-none"
              >
                <option value="">-- Elige un Job reciente --</option>
                {topJobs.map(j => (
                  <option key={j.job_id} value={j.job_id}>Job #{j.job_id} ({j.niche_id})</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-text-muted ml-1">2. Seleccionar Idiomas</label>
              <div className="flex gap-1 flex-wrap">
                {['en', 'pt', 'fr', 'de', 'it'].map(lg => {
                  const active = cloneLangs.split(',').map(x=>x.trim()).includes(lg);
                  return (
                    <button 
                      key={lg}
                      onClick={() => {
                        let arr = cloneLangs.split(',').map(x=>x.trim()).filter(Boolean);
                        if(active) arr = arr.filter(x => x !== lg);
                        else arr.push(lg);
                        setCloneLangs(arr.join(','));
                      }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase transition-all ${
                        active 
                          ? 'bg-accent-primary text-white border-transparent' 
                          : 'bg-surface text-text-muted border border-border-subtle hover:border-accent-primary/50'
                      }`}
                    >
                      {lg}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
          <button 
            onClick={triggerClone}
            disabled={!cloneJobId || !cloneLangs}
            className={`w-full py-2.5 rounded-lg text-xs font-bold transition-colors flex items-center justify-center gap-2 ${
              !cloneJobId || !cloneLangs 
                ? 'bg-surface text-text-muted cursor-not-allowed' 
                : 'bg-accent-primary hover:bg-accent-secondary text-white shadow-lg shadow-accent-primary/20'
            }`}
          >
            <Send size={14}/> Lanzar Multiplicador de Ingresos
          </button>
        </div>
      </Sec>

      {/* Social */}
      <Sec id="social" title="Distribución Social — TikTok & Instagram" icon={Share2} open={open==='social'} toggle={toggle}>
        {(['tiktok','instagram'] as const).map(p => (
          <div key={p} className="flex items-center justify-between p-2.5 bg-surface rounded-lg">
            <div>
              <div className="text-sm font-bold capitalize">{p}</div>
              <div className="text-[10px] text-text-muted">{social?.[p]?.uploads_24h??0} uploads hoy</div>
            </div>
            <div className="flex gap-1.5">
              <Badge ok={social?.[p]?.configured??false} yes="Configurado" no="Sin creds"/>
              <Badge ok={social?.[p]?.enabled??false} yes="ON" no="OFF"/>
            </div>
          </div>
        ))}
        <div className="space-y-2">
          <div className="text-[10px] text-text-muted font-bold uppercase">Distribuir Short Manualmente</div>
          <div className="flex gap-2">
            <input value={distJobId} onChange={e => setDistJobId(e.target.value)}
              placeholder="Job ID" type="number"
              className="flex-1 px-2 py-1.5 text-xs bg-surface border border-border-subtle rounded-lg focus:border-accent-primary outline-none"/>
            <button onClick={triggerDist}
              className="px-3 py-1.5 bg-accent-primary hover:bg-accent-secondary text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-1">
              <Send size={11}/> Distribuir
            </button>
          </div>
        </div>
        {(social?.recent_log??[]).length > 0 && (
          <div>
            <div className="text-[10px] text-text-muted font-bold uppercase mb-1.5">Últimas distribuciones</div>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {(social!.recent_log!).slice(-8).reverse().map((l, i) => (
                <div key={i} className="flex items-center gap-2 text-[10px] p-1.5 bg-surface rounded">
                  <span className={l.status==='uploaded' ? 'text-status-success' : l.status==='dry_run' ? 'text-status-warning' : 'text-status-error'}>
                    {l.status==='uploaded' ? '✓' : l.status==='dry_run' ? '○' : '✗'}
                  </span>
                  <span className="font-bold capitalize">{l.platform}</span>
                  <span className="text-text-muted">Job #{l.job_id}</span>
                  <span className="ml-auto text-text-muted">{l.ts.slice(5,16)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="p-2.5 bg-surface rounded-lg text-[10px] text-text-muted space-y-0.5">
          <div>TikTok: <code className="bg-bg px-1 rounded">_integrations/tiktok_creds.json</code></div>
          <div>Instagram: <code className="bg-bg px-1 rounded">_integrations/instagram_creds.json</code></div>
        </div>
      </Sec>

      {/* Afiliados */}
      <Sec id="aff" title="Programa de Afiliados — CPA" icon={Tag} open={open==='aff'} toggle={toggle}>
        <div className="grid grid-cols-3 gap-2">
          <div className="p-2.5 bg-surface rounded-lg text-center">
            <div className="text-xl font-black text-accent-primary">{aff?.niches_covered??0}</div>
            <div className="text-[10px] text-text-muted">Nichos</div>
          </div>
          <div className="p-2.5 bg-surface rounded-lg text-center">
            <div className="text-xl font-black text-purple-400">{aff?.total_programs??0}</div>
            <div className="text-[10px] text-text-muted">Programas</div>
          </div>
          <div className="p-2.5 bg-surface rounded-lg text-center">
            <div className="text-xl font-black text-status-success">{aff?.ids_configured?.length??0}</div>
            <div className="text-[10px] text-text-muted">IDs config</div>
          </div>
        </div>
        <Row2 label="Inyección automática" value={<Badge ok={aff?.enabled??false} yes="Activa" no="Inactiva"/>}/>
        {(aff?.ids_configured??[]).length > 0 && (
          <div className="flex gap-1.5 flex-wrap">
            {aff!.ids_configured.map(id => (
              <span key={id} className="px-1.5 py-0.5 bg-surface border border-border-subtle rounded text-[10px] text-text-muted">{id}</span>
            ))}
          </div>
        )}
        <div className="text-[10px] text-text-muted">
          Activar: <code className="bg-surface px-1 rounded">config.yaml → affiliates.enabled: true</code>
        </div>
      </Sec>

      {/* Top Jobs */}
      {topJobs.length > 0 && (
        <Sec id="top" title="Top Videos por Ingreso Estimado" icon={TrendingUp} open={open==='top'} toggle={toggle}>
          <div className="space-y-1.5">
            {topJobs.slice(0,8).map((j, i) => (
              <div key={j.job_id} className="flex items-center gap-2 p-2 bg-surface rounded-lg">
                <span className="text-[10px] font-black text-text-muted w-4">#{i+1}</span>
                <div className="flex-1">
                  <div className="text-xs font-bold">Job #{j.job_id}</div>
                  <div className="text-[10px] text-text-muted">{j.niche_id||'—'} · {fmtK(j.views)} vistas</div>
                </div>
                <span className="text-xs font-black text-status-success">{fmt(j.revenue_usd)}</span>
              </div>
            ))}
          </div>
        </Sec>
      )}

      {/* Revenue por Nicho */}
      {revenue && Object.keys(revenue.by_niche).length > 0 && (
        <Sec id="niches" title="Ingresos por Nicho" icon={BarChart2} open={open==='niches'} toggle={toggle}>
          <div className="space-y-2.5">
            {Object.entries(revenue.by_niche).sort(([,a],[,b])=>b-a).map(([n,v]) => (
              <div key={n}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-text-muted capitalize">{n.replace(/_/g,' ')}</span>
                  <span className="font-bold text-status-success">{fmt(v)}</span>
                </div>
                <Bar v={v} max={maxNich} color="#22c55e"/>
              </div>
            ))}
          </div>
        </Sec>
      )}

      {/* Disclaimer */}
      <p className="text-[9px] text-text-muted text-center pb-2 opacity-60">
        {revenue?.disclaimer ?? 'Ingresos estimados basados en CPM histórico. No representan pagos reales de AdSense.'}
      </p>
    </div>
  );
};
