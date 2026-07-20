import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Eye, Plus, Trash2, Radio, Activity, Globe, Shield,
  AlertTriangle, Users, Zap, MapPin, Search, RefreshCw, Bot,
  Network, Clock, ChevronRight, X, Wifi, WifiOff, TrendingUp,
  Server, Flag, Languages, Layers, Copy, Check, MessageSquare, Tv, Play, Mic
} from 'lucide-react';

// ── Types ─────────────────────────────────────────────────────────────────────

interface Channel {
  username: string;
  is_live: boolean;
  viewers: number;
  title: string;
  stream_url?: string;
  cdn_provider: string;
  cdn_ip: string;
  geo_country: string;
  geo_city: string;
  bot_score: number;
  engagement: number;
  interval_sec: number;
  last_check: string;
  room_id?: string;
  user_id?: string;
  codec_video?: string;
  codec_audio?: string;
  bitrate_kbps?: number;
  resolution?: string;
  fps?: number;
  error?: string;
}

interface Alert {
  id: number;
  username: string;
  ts: string;
  alert_type: string;
  severity: 'critical' | 'high' | 'warning' | 'info';
  message: string;
  acknowledged: boolean;
}

interface RadarStatus {
  running: boolean;
  channels: Channel[];
  total_channels: number;
  live_now: number;
  alerts_unread: number;
}

interface GeoReport {
  username: string;
  summary?: {
    ips_discovered: string[];
    nodes_mapped: number;
    ingest_server: string;
    streamer_location_top_candidate?: { country: string; confidence: number; based_on: string[] };
    streamer_language: string;
    streamer_language_variant: string;
    explicit_locations_in_bio: string[];
    inferred_timezone: string;
    inferred_timezone_regions: string[];
    audience_dominant_language: string;
    audience_top_regions: string[];
    offline_reason?: string;
  };
  infra_map?: { nodes: any[]; all_ips: string[]; cname_chain: string[]; ingest_server_guess: string };
  dns_chain?: { records: any[]; geo_summary: Record<string, number> };
  methodology_note?: string;
  error?: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const BOT_COLOR = (score: number) =>
  score >= 0.7 ? '#ef4444' : score >= 0.4 ? '#f59e0b' : score >= 0.2 ? '#eab308' : '#10b981';

const BOT_LABEL = (score: number) =>
  score >= 0.7 ? 'CRÍTICO' : score >= 0.4 ? 'ALTO' : score >= 0.2 ? 'MEDIO' : 'BAJO';

const SEV_COLOR: Record<string, string> = {
  critical: '#ef4444', high: '#f97316', warning: '#f59e0b', info: '#38bdf8'
};

const fmt_ts = (ts: string) => {
  try { return new Date(ts).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit', second: '2-digit' }); }
  catch { return ts; }
};

const API = (path: string) => path; // same-origin

// ── Sub-components ────────────────────────────────────────────────────────────

const Pill = ({ children, color }: { children: React.ReactNode; color?: string }) => (
  <span style={{ background: `${color}22`, color, border: `1px solid ${color}44` }}
    className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full">
    {children}
  </span>
);

const StatCard = ({ icon: Icon, label, value, sub, color }:
  { icon: any; label: string; value: string | number; sub?: string; color: string }) => (
  <div className="glass-card p-4 flex flex-col gap-1 min-w-0">
    <div className="flex items-center gap-2 text-text-muted text-xs font-semibold uppercase tracking-wider">
      <Icon size={13} style={{ color }} /> {label}
    </div>
    <div className="text-2xl font-black text-text-primary mt-1" style={{ color }}>{value}</div>
    {sub && <div className="text-[11px] text-text-muted">{sub}</div>}
  </div>
);

const BotBar = ({ score }: { score: number }) => (
  <div className="flex items-center gap-2">
    <div className="flex-1 h-1.5 rounded-full bg-card overflow-hidden">
      <div style={{ width: `${score * 100}%`, background: BOT_COLOR(score) }}
        className="h-full rounded-full transition-all duration-700" />
    </div>
    <span className="text-[10px] font-black" style={{ color: BOT_COLOR(score) }}>
      {BOT_LABEL(score)}
    </span>
  </div>
);

// ── Main Panel ────────────────────────────────────────────────────────────────

export const TikTokRadarPanel = () => {
  const [status, setStatus] = useState<RadarStatus | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);
  const [geoReport, setGeoReport] = useState<GeoReport | null>(null);
  const [geoLoading, setGeoLoading] = useState(false);
  const [isOffline, setIsOffline] = useState(false);

  // Voice Intel state
  const [voiceProfile, setVoiceProfile] = useState<any>(null);
  const [voiceTranscript, setVoiceTranscript] = useState<any[]>([]);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  // IA Suggestions state
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [sugLoading, setSugLoading] = useState(false);
  const [sugError, setSugError] = useState<string | null>(null);
  const [sugNote, setSugNote] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // HLS Video Player state
  const [showPlayer, setShowPlayer] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<any>(null);

  useEffect(() => {
    if (!showPlayer || !selectedChannel?.stream_url || !videoRef.current) {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
      return;
    }

    const loadHls = async () => {
      let HlsClass = (window as any).Hls;
      if (!HlsClass) {
        await new Promise<void>((resolve, reject) => {
          const script = document.createElement('script');
          script.src = 'https://cdn.jsdelivr.net/npm/hls.js@latest';
          script.async = true;
          script.onload = () => resolve();
          script.onerror = () => reject(new Error('No se pudo cargar el reproductor HLS.'));
          document.body.appendChild(script);
        });
        HlsClass = (window as any).Hls;
      }

      if (HlsClass.isSupported()) {
        if (hlsRef.current) {
          hlsRef.current.destroy();
        }
        const hls = new HlsClass();
        hls.loadSource(selectedChannel.stream_url!);
        hls.attachMedia(videoRef.current!);
        hlsRef.current = hls;
      } else if (videoRef.current!.canPlayType('application/vnd.apple.mpegurl')) {
        videoRef.current!.src = selectedChannel.stream_url!;
      }
    };

    loadHls().catch(err => {
      console.error(err);
      alert('Error cargando el reproductor de video HLS: ' + err.message);
    });

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
  }, [showPlayer, selectedChannel?.stream_url]);

  const fetchSuggestions = async (username: string) => {
    setSugLoading(true);
    setSugError(null);
    setSuggestions([]);
    setSugNote(null);
    try {
      const res = await fetch(API(`/v1/tiktok/chat_suggestions?user=${encodeURIComponent(username)}`));
      const data = await res.json();
      if (res.ok) {
        if (data.suggestions && data.suggestions.length > 0) {
          setSuggestions(data.suggestions);
          setSugNote(data.note);
        } else {
          setSugError(data.note || 'No hay comentarios suficientes para generar sugerencias.');
        }
      } else {
        setSugError(data.error || 'Error al obtener sugerencias de la IA.');
      }
    } catch (e: any) {
      setSugError(e.message || 'Error de red.');
    } finally {
      setSugLoading(false);
    }
  };

  const handleCopySuggestion = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // HITL Chat Controller states
  const [chatMsg, setChatMsg] = useState('');
  const [sessionCookie, setSessionCookie] = useState(() => localStorage.getItem('tiktok_session_id') || '');
  const [sendingChat, setSendingChat] = useState(false);
  const [sendResult, setSendResult] = useState<{ success?: boolean; error?: string } | null>(null);
  const [showConfig, setShowConfig] = useState(false);

  const handleSendChat = async () => {
    if (!selectedChannel || !chatMsg.trim()) return;
    setSendingChat(true);
    setSendResult(null);
    try {
      const res = await fetch(API('/v1/tiktok/send_chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user: selectedChannel.username,
          message: chatMsg,
          session_id: sessionCookie
        })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setSendResult({ success: true });
        setChatMsg('');
        setTimeout(() => setSendResult(null), 4000);
      } else {
        setSendResult({ success: false, error: data.error || 'Error al procesar el mensaje.' });
      }
    } catch (e: any) {
      setSendResult({ success: false, error: e.message || 'Error de conexión.' });
    } finally {
      setSendingChat(false);
    }
  };

  // Live Comments state
  const [liveComments, setLiveComments] = useState<any[]>([]);
  const [commentStats, setCommentStats] = useState<{ total_captured: number; toxicity_ratio: number; top_keywords: string[] } | null>(null);

  useEffect(() => {
    if (!selectedChannel || !selectedChannel.is_live) {
      setLiveComments([]);
      setCommentStats(null);
      return;
    }

    const fetchComments = async () => {
      try {
        const res = await fetch(API(`/v1/tiktok/comments?user=${encodeURIComponent(selectedChannel.username)}`));
        if (res.ok) {
          const data = await res.json();
          setLiveComments(data.comments || []);
          setCommentStats(data.stats || null);
        }
      } catch (err) {
        console.error('Error fetching comments:', err);
      }
    };

    fetchComments();
    const interval = setInterval(fetchComments, 3000);
    return () => clearInterval(interval);
  }, [selectedChannel]);

  // Watch modal
  const [watchModal, setWatchModal] = useState(false);
  const [watchUsername, setWatchUsername] = useState('');
  const [watchInterval, setWatchInterval] = useState(60);
  const [watchNotes, setWatchNotes] = useState('');
  const [watchLoading, setWatchLoading] = useState(false);

  // Probe modal
  const [probeModal, setProbeModal] = useState(false);
  const [probeTarget, setProbeTarget] = useState('');
  const [probeResult, setProbeResult] = useState<any>(null);
  const [probeLoading, setProbeLoading] = useState(false);

  const [activeTab, setActiveTab] = useState<'channels' | 'alerts' | 'geo' | 'voice'>('channels');
  const alertsEndRef = useRef<HTMLDivElement>(null);

  // Deep OSINT
  const [osintLoading, setOsintLoading] = useState(false);
  const [dossierContent, setDossierContent] = useState<string | null>(null);

  const handleDeepOsint = async (username: string) => {
    setOsintLoading(true);
    setDossierContent(null);
    try {
      const res = await fetch(API(`/v1/tiktok/deep_osint?user=${encodeURIComponent(username)}`));
      const data = await res.json().catch(() => null);
      if (res.ok) {
        if (data && data.success) setDossierContent(data.content);
        else alert(data?.error || 'Error running Deep OSINT');
      } else {
        alert(data?.error || `HTTP Error ${res.status} executing OSINT`);
      }
    } catch (e) {
      console.error(e);
      alert('Network error executing OSINT');
    } finally {
      setOsintLoading(false);
    }
  };

  // ── Data fetching ───────────────────────────────────────────────────────────
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(API('/v1/tiktok/status'));
      if (res.ok) { setStatus(await res.json()); setIsOffline(false); }
      else setIsOffline(true);
    } catch { setIsOffline(true); }
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch(API('/v1/tiktok/alerts?limit=50'));
      if (res.ok) { const d = await res.json(); setAlerts(d.alerts || []); }
    } catch {}
  }, []);

  const fetchGeo = useCallback(async (username: string) => {
    setGeoLoading(true);
    setGeoReport(null);
    try {
      const res = await fetch(API(`/v1/tiktok/geo?user=${encodeURIComponent(username)}`));
      if (res.ok) setGeoReport(await res.json());
      else setGeoReport({ username, error: `HTTP ${res.status}` });
    } catch (e: any) {
      setGeoReport({ username, error: e.message });
    } finally { setGeoLoading(false); }
  }, []);

  const fetchVoiceTranscript = useCallback(async (username: string) => {
    try {
      const resTrans = await fetch(API(`/v1/tiktok/audio_transcript?user=${encodeURIComponent(username)}`));
      if (resTrans.ok) {
        const d = await resTrans.json();
        setVoiceTranscript(d.transcript || []);
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  const fetchPsychProfile = useCallback(async (username: string) => {
    setVoiceLoading(true);
    setVoiceError(null);
    try {
      const resProf = await fetch(API(`/v1/tiktok/psychological_profile?user=${encodeURIComponent(username)}`));
      if (resProf.ok) {
        const d2 = await resProf.json();
        if (d2.profile) setVoiceProfile(d2.profile);
        else setVoiceError(d2.error || 'No profile generated');
      } else {
        try {
          const d2 = await resProf.json();
          setVoiceError(d2.error || `Error ${resProf.status}`);
        } catch {
          setVoiceError(`Error de servidor (${resProf.status})`);
        }
      }
    } catch (e: any) {
      setVoiceError(e.message);
    } finally {
      setVoiceLoading(false);
    }
  }, []);

  const fetchVoiceIntel = useCallback(async (username: string) => {
    fetchVoiceTranscript(username);
    fetchPsychProfile(username);
  }, [fetchVoiceTranscript, fetchPsychProfile]);

  useEffect(() => {
    fetchStatus(); fetchAlerts();
    const iv1 = setInterval(fetchStatus, 5000);
    const iv2 = setInterval(fetchAlerts, 8000);
    return () => { clearInterval(iv1); clearInterval(iv2); };
  }, [fetchStatus, fetchAlerts]);

  useEffect(() => {
    let interval: any;
    if (activeTab === 'voice' && selectedChannel) {
      interval = setInterval(() => {
        fetchVoiceTranscript(selectedChannel.username);
      }, 5000); // Faster audio transcript updates without LLM cost
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeTab, selectedChannel, fetchVoiceTranscript]);

  useEffect(() => {
    // Reset state when switching channel or tab to prevent showing stale data
    setVoiceTranscript([]);
    setVoiceProfile(null);
    setVoiceError(null);
    setDossierContent(null);
    
    if (activeTab === 'voice' && selectedChannel) {
      fetchVoiceIntel(selectedChannel.username);
    }
  }, [selectedChannel, activeTab, fetchVoiceIntel]);

  // ── Actions ─────────────────────────────────────────────────────────────────
  const handleWatch = async () => {
    if (!watchUsername.trim()) return;
    setWatchLoading(true);
    
    // Extraer usuario si el input es una URL completa (soporta tiktok.com/@user y tiktok.com/live/@user)
    let finalUsername = watchUsername.trim();
    if (finalUsername.includes('tiktok.com/')) {
      const match = finalUsername.match(/@([a-zA-Z0-9_.-]+)/);
      if (match && match[1]) {
        finalUsername = match[1];
      }
    }
    finalUsername = finalUsername.replace('@', '').split('?')[0].split('/')[0];

    try {
      const res = await fetch(API('/v1/tiktok/watch'), {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: finalUsername, interval_sec: watchInterval, notes: watchNotes }),
      });
      if (res.ok) { setWatchModal(false); setWatchUsername(''); setWatchNotes(''); fetchStatus(); }
    } finally { setWatchLoading(false); }
  };

  const handleUnwatch = async (username: string) => {
    if (!confirm(`¿Dejar de monitorear @${username}?`)) return;
    await fetch(API('/v1/tiktok/unwatch'), {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    });
    fetchStatus();
    if (selectedChannel?.username === username) setSelectedChannel(null);
  };

  const handleProbe = async () => {
    if (!probeTarget.trim()) return;
    setProbeLoading(true); setProbeResult(null);

    let finalTarget = probeTarget.trim();
    if (finalTarget.includes('tiktok.com/')) {
      const match = finalTarget.match(/@([a-zA-Z0-9_.-]+)/);
      if (match && match[1]) {
        finalTarget = match[1];
      }
    }
    finalTarget = finalTarget.replace('@', '').split('?')[0].split('/')[0];

    try {
      const res = await fetch(API(`/v1/tiktok/probe?user=${encodeURIComponent(finalTarget)}&action=probe`));
      if (res.ok) setProbeResult(await res.json());
    } finally { setProbeLoading(false); }
  };

  const handleSelectChannel = (ch: Channel) => {
    setSelectedChannel(ch);
    setActiveTab('channels');
    setSuggestions([]);
    setSugError(null);
    setSugNote(null);
    setCopiedIndex(null);
    setLiveComments([]);
    setCommentStats(null);
    setShowPlayer(false);
    setChatMsg('');
    setSendResult(null);
    setDossierContent(null);
  };

  const handleGeoChannel = (username: string) => {
    setActiveTab('geo');
    fetchGeo(username);
  };

  const handleVoiceChannel = (username: string) => {
    setActiveTab('voice');
    fetchVoiceIntel(username);
  };

  // ── Render ───────────────────────────────────────────────────────────────────
  const channels = status?.channels ?? [];
  const liveChannels = channels.filter(c => c.is_live);
  const unreadAlerts = alerts.filter(a => !a.acknowledged).length;

  return (
    <div className="flex flex-col h-full overflow-hidden p-4 gap-4">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: 'linear-gradient(135deg,#ee1d52,#69c9d0)', boxShadow: '0 0 24px #ee1d5255' }}>
            <Radio size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-black text-text-primary leading-none">TikTok Radar</h1>
            <p className="text-xs text-text-muted mt-0.5">GTLIS — Live Intelligence Suite · White-Hat OSINT</p>
          </div>
          {isOffline
            ? <Pill color="#ef4444"><WifiOff size={9} className="inline mr-1" />Offline</Pill>
            : <Pill color="#10b981"><Wifi size={9} className="inline mr-1" />Online</Pill>}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => { fetchStatus(); fetchAlerts(); }}
            className="p-2 rounded-xl glass-card hover:border-accent-primary/40 transition-all text-text-muted hover:text-accent-primary">
            <RefreshCw size={15} />
          </button>
          <button onClick={() => setProbeModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all"
            style={{ background: 'linear-gradient(135deg,#6d28d9,#4f46e5)', boxShadow: '0 0 16px #6d28d933' }}>
            <Search size={14} /> Probe Rápido
          </button>
          <button onClick={() => setWatchModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all"
            style={{ background: 'linear-gradient(135deg,#ee1d52,#69c9d0)', boxShadow: '0 0 16px #ee1d5244' }}>
            <Plus size={14} /> Monitorear
          </button>
        </div>
      </div>

      {/* ── Stats Row ───────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 shrink-0">
        <StatCard icon={Eye} label="Canales" value={status?.total_channels ?? '--'} sub="en watchlist" color="#a78bfa" />
        <StatCard icon={Radio} label="En Vivo" value={liveChannels.length} sub="ahora mismo" color="#10b981" />
        <StatCard icon={AlertTriangle} label="Alertas" value={unreadAlerts} sub="sin leer" color="#f59e0b" />
        <StatCard icon={Bot} label="Bot Avg" value={channels.length ? `${Math.round(channels.reduce((s, c) => s + c.bot_score, 0) / channels.length * 100)}%` : '--'} sub="score promedio" color="#38bdf8" />
      </div>

      {/* ── Main Layout ─────────────────────────────────────────────────────── */}
      <div className="flex flex-1 gap-3 overflow-hidden min-h-0">

        {/* ── Channel List ──────────────────────────────────────────────────── */}
        <div className="w-72 shrink-0 flex flex-col gap-2 overflow-y-auto pr-1 scrollbar-hide">
          {channels.length === 0 ? (
            <div className="glass-card p-6 flex flex-col items-center gap-3 text-center">
              <Eye size={32} className="text-text-muted opacity-40" />
              <p className="text-text-muted text-sm">Sin canales monitoreados.</p>
              <button onClick={() => setWatchModal(true)}
                className="text-xs text-accent-primary font-bold hover:underline">+ Agregar canal</button>
            </div>
          ) : channels.map(ch => (
            <div key={ch.username} onClick={() => handleSelectChannel(ch)}
              className={`glass-card p-3 cursor-pointer transition-all duration-300 group
                ${selectedChannel?.username === ch.username ? 'border-accent-primary/50 shadow-[0_0_20px_rgba(167,139,250,0.15)]' : 'hover:border-border-subtle/80'}`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {ch.is_live
                    ? <span className="w-2 h-2 rounded-full bg-status-error animate-pulse shadow-[0_0_8px_#ef4444]" />
                    : <span className="w-2 h-2 rounded-full bg-text-muted opacity-40" />}
                  <span className="text-sm font-bold text-text-primary truncate max-w-[120px]">@{ch.username}</span>
                </div>
                <button onClick={(e) => { e.stopPropagation(); handleUnwatch(ch.username); }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-status-error/20 text-text-muted hover:text-status-error transition-all">
                  <Trash2 size={12} />
                </button>
              </div>

              {ch.is_live && (
                <p className="text-[11px] text-text-muted truncate mb-2">🎙 {ch.title || 'Sin título'}</p>
              )}

              <div className="grid grid-cols-2 gap-1 text-[11px] text-text-muted mb-2">
                <span className="flex items-center gap-1"><Users size={9} />{ch.viewers.toLocaleString()}</span>
                <span className="flex items-center gap-1"><Globe size={9} />{ch.geo_country || '??'} {ch.geo_city ? `· ${ch.geo_city}` : ''}</span>
              </div>

              <BotBar score={ch.bot_score} />

              <div className="flex gap-1 mt-2">
                <button onClick={(e) => { e.stopPropagation(); handleVoiceChannel(ch.username); }}
                  className="flex-1 flex items-center justify-center gap-1 py-1 rounded-lg text-[10px] font-bold
                    bg-accent-tertiary/10 text-accent-tertiary hover:bg-accent-tertiary/20 transition-all">
                  <Mic size={9} /> VOZ
                </button>
                <button onClick={(e) => { e.stopPropagation(); handleGeoChannel(ch.username); }}
                  className="flex-1 flex items-center justify-center gap-1 py-1 rounded-lg text-[10px] font-bold
                    bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/20 transition-all">
                  <MapPin size={9} /> GEO
                </button>
                <button onClick={(e) => { e.stopPropagation(); setProbeTarget(ch.username); setProbeModal(true); }}
                  className="flex-1 flex items-center justify-center gap-1 py-1 rounded-lg text-[10px] font-bold
                    bg-accent-secondary/10 text-accent-secondary hover:bg-accent-secondary/20 transition-all">
                  <Search size={9} /> PROBE
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* ── Right Panel ───────────────────────────────────────────────────── */}
        <div className="flex-1 flex flex-col gap-3 overflow-hidden min-w-0">

          {/* Tabs */}
          <div className="flex gap-1 glass-card p-1 rounded-xl shrink-0 w-fit">
            {([
              { id: 'channels', icon: Layers, label: 'Detalle' },
              { id: 'alerts', icon: AlertTriangle, label: `Alertas${unreadAlerts > 0 ? ` (${unreadAlerts})` : ''}` },
              { id: 'voice', icon: Mic, label: 'Intel de Voz' },
              { id: 'geo', icon: Globe, label: 'Geo Intel' },
            ] as const).map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all
                  ${activeTab === tab.id ? 'bg-accent-primary text-white shadow-[0_0_12px_rgba(167,139,250,0.4)]' : 'text-text-muted hover:text-text-primary'}`}>
                <tab.icon size={12} />{tab.label}
              </button>
            ))}
          </div>

          {/* ── Tab: Detalle de Canal ─────────────────────────────────────── */}
          {activeTab === 'channels' && (
            <div className="flex-1 overflow-y-auto scrollbar-hide">
              {!selectedChannel ? (
                <div className="h-full flex flex-col items-center justify-center gap-3 text-text-muted">
                  <Eye size={40} className="opacity-20" />
                  <p className="text-sm">Selecciona un canal para ver el detalle</p>
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  {/* Header del canal */}
                  <div className="glass-card p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          {selectedChannel.is_live && (
                            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black"
                              style={{ background: '#ef444422', color: '#ef4444', border: '1px solid #ef444444' }}>
                              <span className="w-1.5 h-1.5 rounded-full bg-status-error animate-pulse" />
                              EN VIVO
                            </span>
                          )}
                          <h2 className="text-xl font-black">@{selectedChannel.username}</h2>
                        </div>
                        {selectedChannel.title && (
                          <p className="text-sm text-text-muted">{selectedChannel.title}</p>
                        )}
                        <div className="flex items-center gap-3 mt-1.5">
                          {selectedChannel.room_id && (
                            <span className="text-[10px] font-mono text-text-muted bg-surface px-1.5 py-0.5 rounded border border-border-subtle">
                              Room: {selectedChannel.room_id}
                            </span>
                          )}
                          {selectedChannel.user_id && (
                            <span className="text-[10px] font-mono text-status-warning bg-surface px-1.5 py-0.5 rounded border border-border-subtle">
                              UID: {selectedChannel.user_id}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {selectedChannel.is_live && selectedChannel.stream_url && (
                          <button onClick={() => setShowPlayer(!showPlayer)}
                            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all
                              ${showPlayer ? 'bg-status-success text-white shadow-[0_0_12px_#10b98144]' : 'bg-status-error text-white shadow-[0_0_12px_#ef444444]'}`}>
                            <Tv size={12} />
                            {showPlayer ? 'Cerrar Player' : 'Ver Directo'}
                          </button>
                        )}
                        <button onClick={() => handleDeepOsint(selectedChannel.username)}
                          disabled={osintLoading}
                          className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50"
                          style={{ background: 'linear-gradient(135deg,#ef4444,#dc2626)', boxShadow: '0 0 12px #ef444444' }}>
                          {osintLoading ? <RefreshCw size={12} className="animate-spin" /> : <Shield size={12} />}
                          OSINT Profundo
                        </button>
                        <button onClick={() => handleGeoChannel(selectedChannel.username)}
                          className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all"
                          style={{ background: 'linear-gradient(135deg,#6d28d9,#0ea5e9)', boxShadow: '0 0 12px #6d28d933' }}>
                          <MapPin size={12} /> Geo Intel Completo
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* HLS Video Stream Player */}
                  {showPlayer && selectedChannel.is_live && selectedChannel.stream_url && (
                    <div className="glass-card p-4 border border-status-success/20 bg-card/10">
                      <div className="flex items-center gap-2 mb-3 text-sm font-bold text-status-success">
                        <Tv size={15} /> Reproductor de Video en Vivo (HLS Stream)
                      </div>
                      <div className="relative rounded-xl overflow-hidden bg-black border border-border-subtle aspect-video shadow-2xl">
                        <video
                          ref={videoRef}
                          controls
                          autoPlay
                          playsInline
                          className="w-full h-full object-contain"
                        />
                      </div>
                    </div>
                  )}
                  {/* Error Notification */}
                  {selectedChannel.error && (
                    <div className="glass-card p-3 mb-4 border border-status-error/30 bg-status-error/5">
                      <div className="flex items-start gap-2">
                        <AlertTriangle size={16} className="text-status-error mt-0.5 shrink-0" />
                        <p className="text-sm text-status-error font-mono leading-snug">{selectedChannel.error}</p>
                      </div>
                    </div>
                  )}

                  {/* Métricas del stream */}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    <StatCard icon={Users} label="Viewers" value={selectedChannel.viewers.toLocaleString()} color="#38bdf8" />
                    <StatCard icon={Globe} label="CDN País" value={selectedChannel.geo_country || 'N/A'} sub={selectedChannel.geo_city} color="#a78bfa" />
                    <StatCard icon={Server} label="CDN" value={selectedChannel.cdn_provider || 'unknown'} sub={selectedChannel.cdn_ip} color="#6ee7b7" />
                    <StatCard icon={TrendingUp} label="Engagement" value={`${(selectedChannel.engagement || 0).toFixed(1)}%`} color="#f59e0b" />
                    <StatCard icon={Clock} label="Intervalo" value={`${selectedChannel.interval_sec}s`} sub="polling cadencia" color="#94a3b8" />
                    <StatCard icon={Activity} label="Bot Score" value={`${Math.round(selectedChannel.bot_score * 100)}%`} sub={BOT_LABEL(selectedChannel.bot_score)} color={BOT_COLOR(selectedChannel.bot_score)} />
                  </div>

                  {/* Bot Score bar */}
                  <div className="glass-card p-4">
                    <div className="flex items-center gap-2 mb-3 text-sm font-bold">
                      <Bot size={15} className="text-accent-primary" /> Análisis de Bots
                    </div>
                    <div className="flex items-center gap-3 mb-2">
                      <div className="flex-1 h-3 rounded-full bg-card overflow-hidden">
                        <div style={{ width: `${selectedChannel.bot_score * 100}%`, background: `linear-gradient(90deg, ${BOT_COLOR(selectedChannel.bot_score)}, ${BOT_COLOR(selectedChannel.bot_score)}88)` }}
                          className="h-full rounded-full transition-all duration-700 shadow-lg" />
                      </div>
                      <span className="text-lg font-black" style={{ color: BOT_COLOR(selectedChannel.bot_score) }}>
                        {Math.round(selectedChannel.bot_score * 100)}%
                      </span>
                    </div>
                    <div className="grid grid-cols-4 gap-2 text-center text-[10px] font-bold text-text-muted">
                      {['BAJO\n0-20%', 'MEDIO\n20-40%', 'ALTO\n40-70%', 'CRÍTICO\n70%+'].map((l, i) => {
                        const thresholds = [0, 0.2, 0.4, 0.7];
                        const active = selectedChannel.bot_score >= thresholds[i] && (i === 3 || selectedChannel.bot_score < thresholds[i + 1]);
                        return (
                          <div key={i} className={`py-1.5 rounded-lg ${active ? 'text-white' : ''}`}
                            style={active ? { background: BOT_COLOR(selectedChannel.bot_score), boxShadow: `0 0 12px ${BOT_COLOR(selectedChannel.bot_score)}66` } : {}}>
                            {l.split('\n').map((t, j) => <div key={j}>{t}</div>)}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* IA Copilot suggestions card */}
                  {selectedChannel.is_live && (
                    <div className="glass-card p-4 border border-accent-primary/20 bg-accent-primary/5">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2 text-sm font-bold text-accent-primary">
                          <MessageSquare size={15} /> Copiloto IA (Sugerencias de Chat)
                        </div>
                        <button
                          onClick={() => fetchSuggestions(selectedChannel.username)}
                          disabled={sugLoading}
                          className="px-3 py-1 text-[11px] font-bold rounded-lg bg-accent-primary text-white hover:bg-accent-primary/80 transition-all disabled:opacity-50"
                        >
                          {sugLoading ? 'Generando...' : suggestions.length > 0 ? 'Regenerar' : 'Generar Sugerencias'}
                        </button>
                      </div>

                      {suggestions.length === 0 && !sugLoading && !sugError && (
                        <p className="text-xs text-text-muted italic">
                          Presiona "Generar Sugerencias" para analizar los comentarios recientes en vivo y producir opciones de respuesta.
                        </p>
                      )}

                      {sugLoading && (
                        <div className="flex items-center gap-2 text-xs text-text-muted py-2">
                          <RefreshCw size={12} className="animate-spin text-accent-primary" />
                          <span>Analizando chat y redactando respuestas...</span>
                        </div>
                      )}

                      {sugError && (
                        <p className="text-xs text-status-error bg-status-error/10 p-2 rounded-lg border border-status-error/20">
                          ⚠️ {sugError}
                        </p>
                      )}

                      {suggestions.length > 0 && (
                        <div className="flex flex-col gap-2">
                          {suggestions.map((sug, idx) => {
                            const labels = ['Cordial / Saludo', 'Informativo', 'Pregunta de Engagement'];
                            const labelColors = ['text-accent-secondary', 'text-accent-tertiary', 'text-accent-primary'];
                            return (
                              <div key={idx} 
                                onClick={() => setChatMsg(sug)}
                                className="bg-card rounded-xl p-3 border border-border-subtle flex flex-col gap-2 relative group cursor-pointer hover:border-accent-tertiary/40 hover:bg-accent-tertiary/5 transition-all text-left"
                                title="Haga clic para editar en la consola de abajo"
                              >
                                <div className="flex items-center justify-between">
                                  <span className={`text-[10px] font-black uppercase tracking-wider ${labelColors[idx]}`}>
                                    {labels[idx]}
                                  </span>
                                  <button
                                    onClick={(e) => { e.stopPropagation(); handleCopySuggestion(sug, idx); }}
                                    className="p-1 rounded-lg hover:bg-surface text-text-muted hover:text-text-primary transition-all animate-none"
                                    title="Copiar respuesta"
                                  >
                                    {copiedIndex === idx ? <Check size={12} className="text-status-success" /> : <Copy size={12} />}
                                  </button>
                                </div>
                                <p className="text-xs text-text-primary pr-6 font-medium leading-relaxed">
                                  {sug}
                                </p>
                              </div>
                            );
                          })}
                          {sugNote && (
                            <p className="text-[10px] text-text-muted italic mt-1">
                              ℹ️ {sugNote}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* HITL Chat Controller Panel */}
                  {selectedChannel.is_live && (
                    <div className="glass-card p-4 border border-accent-tertiary/20 bg-card/20 flex flex-col gap-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-sm font-bold text-accent-tertiary">
                          <MessageSquare size={15} /> Consola de Respuesta (HITL Chat Controller)
                        </div>
                        <button
                          onClick={() => setShowConfig(!showConfig)}
                          className="p-1 rounded-lg hover:bg-surface text-text-muted hover:text-text-primary transition-all text-[11px] font-bold flex items-center gap-1"
                          title="Configurar Cookie de Sesión de TikTok"
                        >
                          ⚙️ {showConfig ? 'Ocultar Config' : 'Configurar Cookie'}
                        </button>
                      </div>

                      {/* Config panel */}
                      {showConfig && (
                        <div className="p-3 bg-background/95 rounded-xl border border-border-subtle flex flex-col gap-2">
                          <p className="text-[10px] text-text-muted leading-relaxed">
                            Para enviar mensajes automatizados, ingresa tu cookie <code className="bg-surface px-1 py-0.5 rounded text-accent-primary">sessionid</code> de TikTok.
                            Las credenciales se guardan localmente en tu navegador.
                          </p>
                          <div className="flex gap-2">
                            <input
                              type="password"
                              placeholder="sessionid (ej: 7f76de8f...)"
                              value={sessionCookie}
                              onChange={(e) => {
                                setSessionCookie(e.target.value);
                                localStorage.setItem('tiktok_session_id', e.target.value);
                              }}
                              className="flex-1 px-3 py-1.5 rounded-lg bg-surface border border-border-subtle text-xs text-text-primary focus:border-accent-primary outline-none font-mono"
                            />
                            {sessionCookie && (
                              <button
                                onClick={() => {
                                  setSessionCookie('');
                                  localStorage.removeItem('tiktok_session_id');
                                }}
                                className="px-2 py-1.5 rounded-lg bg-status-error/15 text-status-error text-[10px] font-bold hover:bg-status-error/25 transition-all"
                              >
                                Limpiar
                              </button>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Chat text composer */}
                      <div className="flex flex-col gap-2">
                        <textarea
                          placeholder="Selecciona una sugerencia de arriba para insertarla aquí, o escribe tu respuesta manual..."
                          value={chatMsg}
                          onChange={(e) => setChatMsg(e.target.value)}
                          className="w-full h-20 p-2.5 rounded-xl bg-background border border-border-subtle text-xs text-text-primary focus:border-accent-tertiary outline-none resize-none font-medium leading-relaxed text-left"
                        />

                        {sendResult && (
                          <div className={`p-2 rounded-lg text-xs border ${
                            sendResult.success 
                              ? 'bg-status-success/10 border-status-success/20 text-status-success' 
                              : 'bg-status-error/10 border-status-error/20 text-status-error'
                          }`}>
                            {sendResult.success 
                              ? '✓ Mensaje enviado exitosamente al chat en vivo.' 
                              : `⚠️ Error al enviar: ${sendResult.error}`
                            }
                          </div>
                        )}

                        <div className="flex gap-2">
                          <button
                            onClick={handleSendChat}
                            disabled={sendingChat || !chatMsg.trim()}
                            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold bg-accent-tertiary text-white hover:bg-accent-tertiary/80 transition-all disabled:opacity-40"
                          >
                            {sendingChat ? (
                              <>
                                <RefreshCw size={12} className="animate-spin" />
                                Enviando...
                              </>
                            ) : (
                              <>
                                <Play size={12} />
                                Enviar al Chat
                              </>
                            )}
                          </button>
                          
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(chatMsg);
                              window.open(`https://www.tiktok.com/@${selectedChannel.username}/live`, '_blank');
                            }}
                            disabled={!chatMsg.trim()}
                            className="px-3 py-2 rounded-xl text-xs font-bold border border-border-subtle bg-surface hover:bg-surface-hover text-text-primary transition-all flex items-center gap-1 disabled:opacity-40"
                            title="Copia el mensaje y abre el chat de TikTok en el navegador para pegarlo manualmente"
                          >
                            <Copy size={12} /> Copiar y Abrir Live
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Live chat comments stream & analysis */}
                  {selectedChannel.is_live && (
                    <div className="glass-card p-4 border border-accent-secondary/20 bg-card/20">
                      <div className="flex items-center justify-between mb-3 text-sm font-bold text-accent-secondary">
                        <div className="flex items-center gap-2">
                          <TrendingUp size={15} /> Monitor de Chat y Sentimiento en Vivo
                        </div>
                        {commentStats && (
                          <span className="text-[10px] bg-card px-2 py-0.5 rounded border border-border-subtle text-text-muted">
                            Capturados: {commentStats.total_captured}
                          </span>
                        )}
                      </div>

                      {/* Mini metrics cards */}
                      {commentStats && (
                        <div className="grid grid-cols-2 gap-2 mb-3">
                          <div className="bg-card p-2.5 rounded-xl border border-border-subtle text-xs">
                            <div className="text-[9px] text-text-muted uppercase mb-0.5">Tasa de Toxicidad</div>
                            <div className="font-bold font-mono text-sm mt-0.5" style={{ color: commentStats.toxicity_ratio > 0.1 ? '#ef4444' : '#10b981' }}>
                              {Math.round(commentStats.toxicity_ratio * 100)}%
                            </div>
                          </div>
                          <div className="bg-card p-2.5 rounded-xl border border-border-subtle text-xs">
                            <div className="text-[9px] text-text-muted uppercase mb-0.5">Keywords Top</div>
                            <div className="font-bold truncate text-accent-secondary text-sm mt-0.5">
                              {commentStats.top_keywords.length > 0 ? commentStats.top_keywords.join(', ') : 'Analizando...'}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Chat feed box */}
                      <div className="bg-background/80 p-3 rounded-xl border border-border-subtle h-48 overflow-y-auto font-mono text-[11px] leading-relaxed flex flex-col gap-1.5 scrollbar-hide">
                        {liveComments.length === 0 ? (
                          <p className="text-text-muted italic my-auto text-center">
                            Esperando comentarios de la transmisión en vivo...
                          </p>
                        ) : (
                          liveComments.map((c, i) => (
                            <div key={i} className="flex gap-1.5 items-start border-b border-border-subtle/30 pb-1">
                              <span className="text-accent-primary font-bold shrink-0">@{c.user_id}:</span>
                              <span className="text-text-primary break-all">{c.text}</span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}

                  {/* CDN Info */}
                  <div className="glass-card p-4">
                    <div className="flex items-center gap-2 mb-3 text-sm font-bold">
                      <Network size={15} className="text-accent-secondary" /> Infraestructura de Red
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      {[
                        ['Proveedor CDN', selectedChannel.cdn_provider || '—'],
                        ['IP CDN Edge', selectedChannel.cdn_ip || '—'],
                        ['Ubicación del Nodo', selectedChannel.geo_city ? `${selectedChannel.geo_city}, ${selectedChannel.geo_country}` : (selectedChannel.geo_country || '—')],
                        ['Resolución de Video', selectedChannel.resolution || '—'],
                        ['Tasa de Cuadros (FPS)', selectedChannel.fps ? `${selectedChannel.fps} FPS` : '—'],
                        ['Ancho de Banda (Bitrate)', selectedChannel.bitrate_kbps ? `${selectedChannel.bitrate_kbps} Kbps` : '—'],
                        ['Códecs de Transmisión', selectedChannel.codec_video ? `V: ${selectedChannel.codec_video} / A: ${selectedChannel.codec_audio}` : '—'],
                      ].map(([k, v]) => (
                        <div key={k} className="bg-card rounded-xl p-3">
                          <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">{k}</div>
                          <div className="font-bold text-text-primary text-sm font-mono">{v}</div>
                        </div>
                      ))}
                    </div>
                    <p className="text-[10px] text-text-muted mt-3 italic">
                      ℹ️ Estos IPs son del servidor CDN de entrega (ByteDance/TikTok), no del streamer ni de los viewers.
                    </p>
                  </div>

                  {selectedChannel.error && (
                    <div className="glass-card p-3 border border-status-error/30 bg-status-error/5">
                      <p className="text-xs text-status-error font-mono">{selectedChannel.error}</p>
                    </div>
                  )}

                  {/* Dossier OSINT Viewer */}
                  {dossierContent && (
                    <div className="glass-card p-4 mt-2 border-accent-primary/30">
                      <div className="flex items-center gap-2 mb-3 text-sm font-bold text-status-error">
                        <Shield size={15} /> Intelligence Dossier Generado
                      </div>
                      <div className="bg-background/80 p-4 rounded-lg border border-border-subtle max-h-96 overflow-y-auto font-mono text-xs whitespace-pre-wrap text-text-primary">
                        {dossierContent}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ── Tab: Alertas ──────────────────────────────────────────────── */}
          {activeTab === 'alerts' && (
            <div className="flex-1 overflow-y-auto scrollbar-hide flex flex-col gap-2" ref={alertsEndRef}>
              {alerts.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center gap-3 text-text-muted">
                  <Shield size={40} className="opacity-20" />
                  <p className="text-sm">Sin alertas registradas</p>
                </div>
              ) : alerts.map(alert => (
                <div key={alert.id} className={`glass-card p-3 border-l-4 transition-all`}
                  style={{ borderLeftColor: SEV_COLOR[alert.severity] }}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Pill color={SEV_COLOR[alert.severity]}>{alert.severity}</Pill>
                        <span className="text-xs font-bold text-accent-primary">@{alert.username}</span>
                        <span className="text-[10px] text-text-muted ml-auto">{fmt_ts(alert.ts)}</span>
                      </div>
                      <p className="text-sm text-text-primary">{alert.message}</p>
                      <p className="text-[10px] text-text-muted mt-1 font-mono">{alert.alert_type}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── Tab: Geo Intel ────────────────────────────────────────────── */}
          {activeTab === 'geo' && (
            <div className="flex-1 overflow-y-auto scrollbar-hide">
              {/* Buscador rápido */}
              <div className="flex gap-2 mb-3 shrink-0">
                <input value={probeTarget} onChange={e => setProbeTarget(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && fetchGeo(probeTarget.replace('@', ''))}
                  placeholder="@handle o username..."
                  className="flex-1 px-4 py-2 rounded-xl bg-card border border-border-subtle text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-primary/50 transition-all" />
                <button onClick={() => fetchGeo(probeTarget.replace('@', ''))}
                  disabled={geoLoading || !probeTarget.trim()}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
                  style={{ background: 'linear-gradient(135deg,#6d28d9,#0ea5e9)' }}>
                  {geoLoading ? <RefreshCw size={14} className="animate-spin" /> : <MapPin size={14} />}
                  Analizar
                </button>
              </div>

              {geoLoading && (
                <div className="glass-card p-8 flex flex-col items-center gap-3 text-text-muted">
                  <RefreshCw size={28} className="animate-spin text-accent-primary" />
                  <p className="text-sm">Ejecutando inteligencia geográfica…</p>
                  <p className="text-xs opacity-60">Resolviendo DNS · Geo-IP · Análisis de idioma · Inferencia de timezone</p>
                </div>
              )}

              {geoReport && !geoReport.error && !geoLoading && (
                <div className="flex flex-col gap-3">

                  {/* Feedback Offline Elegante */}
                  {geoReport.summary?.offline_reason && (
                    <div className="glass-card p-5 border border-status-warning/40 bg-status-warning/5" style={{ boxShadow: '0 0 24px rgba(245, 158, 11, 0.1)' }}>
                      <div className="flex items-center gap-2 mb-2 text-status-warning font-bold text-sm">
                        <AlertTriangle size={18} /> OSINT Limitations: Target Offline
                      </div>
                      <p className="text-sm text-text-muted leading-relaxed">
                        {geoReport.summary.offline_reason}
                      </p>
                    </div>
                  )}

                  {/* Candidate de ubicación */}
                  {geoReport.summary?.streamer_location_top_candidate && (
                    <div className="glass-card p-4" style={{ border: '1px solid #6d28d944', boxShadow: '0 0 24px #6d28d922' }}>
                      <div className="flex items-center gap-2 mb-3 text-sm font-bold text-accent-primary">
                        <Flag size={15} /> Top Candidato — Ubicación del Streamer
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-3xl font-black text-text-primary">
                            {geoReport.summary.streamer_location_top_candidate.country}
                          </div>
                          <div className="text-sm text-text-muted mt-1">
                            {geoReport.summary.inferred_timezone} ·
                            Idioma: <span className="text-accent-secondary font-bold">
                              {geoReport.summary.streamer_language?.toUpperCase()}
                              {geoReport.summary.streamer_language_variant ? ` (${geoReport.summary.streamer_language_variant})` : ''}
                            </span>
                          </div>
                          {geoReport.summary.explicit_locations_in_bio?.length > 0 && (
                            <div className="text-xs text-status-success mt-1 font-bold">
                              📍 Explícito en bio: {geoReport.summary.explicit_locations_in_bio.join(', ')}
                            </div>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="text-4xl font-black" style={{ color: '#10b981' }}>
                            {Math.round((geoReport.summary.streamer_location_top_candidate.confidence || 0) * 100)}%
                          </div>
                          <div className="text-xs text-text-muted">confianza</div>
                        </div>
                      </div>
                      {/* Metodología */}
                      {geoReport.summary.streamer_location_top_candidate.based_on?.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-border-subtle">
                          <div className="text-[10px] text-text-muted uppercase tracking-wider mb-2 font-bold">Metodología de triangulación</div>
                          <div className="flex flex-col gap-1">
                            {geoReport.summary.streamer_location_top_candidate.based_on.map((m: any, i: number) => (
                              <div key={i} className="flex items-start gap-2 text-xs text-text-muted">
                                <ChevronRight size={11} className="text-accent-primary shrink-0 mt-0.5" />
                                <span>{m}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Timezone & Audiencia */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="glass-card p-4">
                      <div className="flex items-center gap-2 mb-3 text-xs font-bold text-text-muted uppercase tracking-wider">
                        <Clock size={12} /> Timezone Inferida
                      </div>
                      <div className="text-2xl font-black text-accent-secondary">{geoReport.summary?.inferred_timezone || '—'}</div>
                      <div className="text-xs text-text-muted mt-2">
                        {(geoReport.summary?.inferred_timezone_regions || []).slice(0, 3).join(' · ') || '—'}
                      </div>
                    </div>
                    <div className="glass-card p-4">
                      <div className="flex items-center gap-2 mb-3 text-xs font-bold text-text-muted uppercase tracking-wider">
                        <Languages size={12} /> Audiencia Geo
                      </div>
                      <div className="text-2xl font-black text-accent-tertiary">
                        {(geoReport.summary?.audience_dominant_language || '—').toUpperCase()}
                      </div>
                      <div className="text-xs text-text-muted mt-2">
                        {(geoReport.summary?.audience_top_regions || []).slice(0, 3).join(' · ') || '—'}
                      </div>
                    </div>
                  </div>

                  {/* IPs descubiertos */}
                  {(geoReport.summary?.ips_discovered?.length ?? 0) > 0 && (
                    <div className="glass-card p-4">
                      <div className="flex items-center gap-2 mb-3 text-sm font-bold">
                        <Network size={15} className="text-accent-secondary" /> IPs Descubiertos en la Cadena CDN
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {(geoReport.summary?.ips_discovered || []).map((ip: any, i: number) => (
                          <span key={i} className="font-mono text-xs px-2 py-1 rounded-lg"
                            style={{ background: '#0ea5e922', color: '#38bdf8', border: '1px solid #0ea5e933' }}>
                            {ip}
                          </span>
                        ))}
                      </div>
                      {geoReport.summary?.ingest_server && (
                        <div className="mt-3 flex items-center gap-2 text-xs">
                          <Server size={11} className="text-status-warning" />
                          <span className="text-text-muted">Servidor de ingesta inferido:</span>
                          <span className="font-mono text-status-warning font-bold">{geoReport.summary.ingest_server}</span>
                        </div>
                      )}
                      <p className="text-[10px] text-text-muted mt-3 italic">
                        ⚠️ {geoReport.methodology_note}
                      </p>
                    </div>
                  )}

                  {/* DNS Chain */}
                  {geoReport.dns_chain?.records && geoReport.dns_chain.records.length > 0 && (
                    <div className="glass-card p-4">
                      <div className="flex items-center gap-2 mb-3 text-sm font-bold">
                        <Layers size={15} className="text-accent-primary" /> Cadena DNS Completa
                      </div>
                      
                      {geoReport.dns_chain?.geo_summary && Object.keys(geoReport.dns_chain.geo_summary).length > 0 && (
                        <div className="mb-4 pt-3 border-t border-border-subtle">
                          <div className="text-[10px] text-text-muted uppercase tracking-wider mb-2 font-bold">Regiones CDN Mapeadas</div>
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(geoReport.dns_chain.geo_summary).map(([country, count]) => (
                              <div key={country} className="flex items-center gap-1.5 bg-card px-2 py-1 rounded border border-border-subtle text-xs">
                                <Flag size={10} className="text-text-muted" />
                                <span className="font-bold">{country}</span>
                                <span className="text-[10px] text-text-muted">({count as number})</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-text-muted uppercase tracking-wider text-[10px]">
                              <th className="text-left py-1 pr-4">Tipo</th>
                              <th className="text-left py-1 pr-4">Valor</th>
                              <th className="text-left py-1 pr-4">País</th>
                              <th className="text-left py-1">ISP / Org</th>
                            </tr>
                          </thead>
                          <tbody>
                            {geoReport.dns_chain.records.slice(0, 12).map((r: any, i: number) => (
                              <tr key={i} className="border-t border-border-subtle">
                                <td className="py-1.5 pr-4">
                                  <Pill color={r.record_type === 'A' ? '#38bdf8' : r.record_type === 'CNAME' ? '#a78bfa' : '#6ee7b7'}>{r.record_type}</Pill>
                                </td>
                                <td className="py-1.5 pr-4 font-mono text-text-primary">{r.value}</td>
                                <td className="py-1.5 pr-4 text-text-muted">{r.geo_country || '—'}</td>
                                <td className="py-1.5 text-text-muted truncate max-w-[150px]">{r.isp || '—'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {geoReport.error && (
                    <div className="glass-card p-4 border border-status-error/30">
                      <p className="text-sm text-status-error font-mono">{geoReport.error}</p>
                    </div>
                  )}
                </div>
              )}

              {!geoReport && !geoLoading && (
                <div className="h-full flex flex-col items-center justify-center gap-4 text-text-muted">
                  <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                    style={{ background: 'linear-gradient(135deg,#6d28d911,#0ea5e911)', border: '1px solid #6d28d933' }}>
                    <MapPin size={28} className="text-accent-primary opacity-60" />
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-bold text-text-primary mb-1">Geo Intelligence Engine</p>
                    <p className="text-xs">Ingresa un handle para triangular la ubicación</p>
                    <p className="text-xs opacity-60 mt-1">DNS · CDN Mapping · Idioma · Timezone · Hashtags</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Tab: Voice Intel ────────────────────────────────────────────── */}
          {activeTab === 'voice' && (
            <div className="flex-1 overflow-y-auto scrollbar-hide">
              {!selectedChannel ? (
                <div className="h-full flex flex-col items-center justify-center gap-3 text-text-muted">
                  <Mic size={40} className="opacity-20" />
                  <p className="text-sm">Selecciona un canal para analizar su voz</p>
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-bold flex items-center gap-2">
                      <Mic size={16} className="text-accent-tertiary" /> 
                      Análisis Psicológico y Conductual
                    </h3>
                    <button onClick={() => fetchVoiceIntel(selectedChannel.username)}
                      disabled={voiceLoading}
                      className="p-1.5 rounded-lg hover:bg-card text-text-muted hover:text-accent-primary transition-all">
                      <RefreshCw size={14} className={voiceLoading ? 'animate-spin' : ''} />
                    </button>
                  </div>

                  {voiceError && (
                    <div className="glass-card p-3 border border-status-error/30">
                      <p className="text-sm text-status-error">{voiceError}</p>
                    </div>
                  )}

                  {!voiceProfile && voiceLoading ? (
                    <div className="glass-card p-8 flex flex-col items-center justify-center gap-3">
                      <div className="w-8 h-8 rounded-full border-2 border-accent-tertiary/30 border-t-accent-tertiary animate-spin" />
                      <p className="text-sm text-text-muted animate-pulse">Generando perfil de {selectedChannel.username}...</p>
                    </div>
                  ) : voiceProfile ? (
                    <div className="flex flex-col gap-3">
                      {voiceProfile.raw_analysis ? (
                        <div className="glass-card p-4 border border-status-warning/30">
                          <h4 className="text-xs font-bold text-status-warning mb-2">Análisis Crudo (Formato Inesperado)</h4>
                          <p className="text-sm text-text-primary whitespace-pre-wrap font-mono text-[10px]">
                            {voiceProfile.raw_analysis}
                          </p>
                        </div>
                      ) : (
                        <>
                          {/* KPI Row */}
                          <div className="grid grid-cols-2 gap-3">
                            <div className="glass-card p-3 flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-accent-tertiary/10 flex items-center justify-center">
                                <Activity size={18} className="text-accent-tertiary" />
                              </div>
                              <div>
                                <p className="text-[10px] text-text-muted font-bold uppercase tracking-wider">Arquetipo</p>
                                <p className="text-sm font-black capitalize text-text-primary">{voiceProfile.archetype || 'Desconocido'}</p>
                              </div>
                            </div>
                            <div className="glass-card p-3 flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-status-warning/10 flex items-center justify-center">
                                <TrendingUp size={18} className="text-status-warning" />
                              </div>
                              <div>
                                <p className="text-[10px] text-text-muted font-bold uppercase tracking-wider">Emoción Dominante</p>
                                <p className="text-sm font-black capitalize text-text-primary">{voiceProfile.dominant_emotion || 'Neutra'}</p>
                              </div>
                            </div>
                          </div>

                          {/* Detalles Extendidos */}
                          <div className="glass-card p-4">
                            <h4 className="text-[10px] text-text-muted uppercase tracking-wider font-bold mb-3">Evaluación de Comportamiento</h4>
                            
                            <div className="grid grid-cols-3 gap-4 mb-4">
                              <div>
                                <div className="flex justify-between text-xs mb-1">
                                  <span className="text-text-muted">Nivel de Estrés</span>
                                  <span className="font-bold">{((voiceProfile.stress_level || 0) * 100).toFixed(0)}%</span>
                                </div>
                                <div className="h-1.5 w-full bg-card rounded-full overflow-hidden">
                                  <div className="h-full bg-status-error rounded-full" style={{ width: `${Math.min(100, Math.max(0, (voiceProfile.stress_level || 0) * 100))}%` }} />
                                </div>
                              </div>
                              <div>
                                <div className="flex justify-between text-xs mb-1">
                                  <span className="text-text-muted">Índice Sarcasmo</span>
                                  <span className="font-bold">{((voiceProfile.sarcasm_index || 0) * 100).toFixed(0)}%</span>
                                </div>
                                <div className="h-1.5 w-full bg-card rounded-full overflow-hidden">
                                  <div className="h-full bg-accent-secondary rounded-full" style={{ width: `${Math.min(100, Math.max(0, (voiceProfile.sarcasm_index || 0) * 100))}%` }} />
                                </div>
                              </div>
                              <div>
                                <div className="flex justify-between text-xs mb-1">
                                  <span className="text-text-muted">Vulnerabilidad</span>
                                  <span className="font-bold">{((voiceProfile.vulnerability_score || 0) * 100).toFixed(0)}%</span>
                                </div>
                                <div className="h-1.5 w-full bg-card rounded-full overflow-hidden">
                                  <div className="h-full bg-accent-tertiary rounded-full" style={{ width: `${Math.min(100, Math.max(0, (voiceProfile.vulnerability_score || 0) * 100))}%` }} />
                                </div>
                              </div>
                            </div>

                            <div className="space-y-3">
                              <div>
                                <p className="text-xs text-text-muted font-bold mb-1">Motivación</p>
                                <p className="text-sm text-text-primary capitalize">{voiceProfile.engagement_drive || 'N/A'}</p>
                              </div>
                              <div>
                                <p className="text-xs text-text-muted font-bold mb-1">Estilo de Comunicación</p>
                                <p className="text-sm text-text-primary capitalize">{voiceProfile.communication_style || 'N/A'}</p>
                              </div>
                              <div>
                                <p className="text-xs text-text-muted font-bold mb-1">Congruencia con Audiencia</p>
                                <p className="text-sm text-text-primary capitalize">{voiceProfile.audience_congruence || 'N/A'}</p>
                              </div>
                            </div>
                          </div>

                          {/* Análisis de Discurso Forense */}
                          <div className="glass-card p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                              <h4 className="text-[10px] text-status-warning uppercase tracking-wider font-bold mb-2">Distorsiones Cognitivas</h4>
                              {voiceProfile.cognitive_distortions && voiceProfile.cognitive_distortions.length > 0 ? (
                                <div className="flex flex-wrap gap-1.5">
                                  {voiceProfile.cognitive_distortions.map((d: string, idx: number) => (
                                    <span key={idx} className="text-[10px] px-2 py-0.5 rounded-full bg-status-warning/10 text-status-warning border border-status-warning/20">
                                      {d}
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-[11px] text-text-muted italic">Ninguna detectada</p>
                              )}
                            </div>
                            
                            <div>
                              <h4 className="text-[10px] text-accent-secondary uppercase tracking-wider font-bold mb-2">Tácticas de Persuasión</h4>
                              {voiceProfile.persuasion_techniques && voiceProfile.persuasion_techniques.length > 0 ? (
                                <div className="flex flex-wrap gap-1.5">
                                  {voiceProfile.persuasion_techniques.map((t: string, idx: number) => (
                                    <span key={idx} className="text-[10px] px-2 py-0.5 rounded-full bg-accent-secondary/10 text-accent-secondary border border-accent-secondary/20">
                                      {t}
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-[11px] text-text-muted italic">Ninguna detectada</p>
                              )}
                            </div>

                            <div>
                              <h4 className="text-[10px] text-accent-tertiary uppercase tracking-wider font-bold mb-2">Mecanismos de Defensa</h4>
                              {voiceProfile.defense_mechanisms && voiceProfile.defense_mechanisms.length > 0 ? (
                                <div className="flex flex-wrap gap-1.5">
                                  {voiceProfile.defense_mechanisms.map((m: string, idx: number) => (
                                    <span key={idx} className="text-[10px] px-2 py-0.5 rounded-full bg-accent-tertiary/10 text-accent-tertiary border border-accent-tertiary/20">
                                      {m}
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-[11px] text-text-muted italic">Ninguno detectado</p>
                              )}
                            </div>
                          </div>

                          <div className="glass-card p-4">
                            <h4 className="text-[10px] text-text-muted uppercase tracking-wider font-bold mb-2">Señales Psicológicas</h4>
                            <ul className="list-disc list-inside text-sm text-text-primary space-y-1">
                              {(voiceProfile.psychological_signals || []).map((s: string, i: number) => (
                                <li key={i} className="pl-1">{s}</li>
                              ))}
                            </ul>
                          </div>

                          <div className="glass-card p-4 border-l-2 border-accent-tertiary">
                            <h4 className="text-[10px] text-accent-tertiary uppercase tracking-wider font-bold mb-2">Resumen</h4>
                            <p className="text-sm text-text-primary italic">"{voiceProfile.summary || 'Sin resumen disponible.'}"</p>
                          </div>
                        </>
                      )}
                    </div>
                  ) : null}

                  {/* Transcripción raw */}
                  <div className="glass-card p-4 mt-2">
                    <h4 className="text-xs font-bold mb-3 flex items-center gap-2">
                      <MessageSquare size={14} className="text-text-muted" /> Transcripción Reciente
                    </h4>
                    <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto scrollbar-hide pr-2">
                      {voiceTranscript.length === 0 ? (
                        <p className="text-xs text-text-muted italic">No se ha capturado voz todavía.</p>
                      ) : (
                        voiceTranscript.slice(-20).map((line, i) => (
                          <div key={i} className="flex items-start gap-2 text-xs py-0.5 border-b border-border-subtle/10 last:border-0">
                            <span className="text-[9px] text-text-muted font-mono whitespace-nowrap pt-0.5">
                              {new Date(line.timestamp_ms).toLocaleTimeString('es')}
                            </span>
                            <span className="text-text-primary">
                              {line.speaker && (
                                <span className={`font-bold mr-1.5 ${
                                  line.speaker === 'Streamer' ? 'text-accent-primary' : 
                                  line.speaker === 'Invitado 1' ? 'text-accent-secondary' : 
                                  line.speaker === 'Invitado 2' ? 'text-accent-tertiary' : 
                                  line.speaker === 'Moderador' ? 'text-status-warning' : 'text-text-muted italic'
                                }`}>
                                  [{line.speaker}]:
                                </span>
                              )}
                              {line.text}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Modal: Watch ──────────────────────────────────────────────────────── */}
      {watchModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-card p-6 w-full max-w-md rounded-2xl border border-accent-primary/30 shadow-[0_0_40px_rgba(167,139,250,0.2)]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-black">Agregar Canal a Watchlist</h3>
              <button onClick={() => setWatchModal(false)} className="p-1.5 rounded-lg hover:bg-card text-text-muted hover:text-text-primary transition-all">
                <X size={16} />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-xs text-text-muted uppercase tracking-wider font-bold mb-1 block">Handle TikTok</label>
                <input value={watchUsername} onChange={e => setWatchUsername(e.target.value)}
                  placeholder="@usuario o usuario"
                  className="w-full px-4 py-2.5 rounded-xl bg-bg border border-border-subtle text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-primary/60 transition-all" />
              </div>
              <div>
                <label className="text-xs text-text-muted uppercase tracking-wider font-bold mb-1 block">
                  Intervalo de polling — {watchInterval}s
                </label>
                <input type="range" min={15} max={300} step={15} value={watchInterval}
                  onChange={e => setWatchInterval(+e.target.value)}
                  className="w-full accent-violet-500" />
                <div className="flex justify-between text-[10px] text-text-muted mt-1">
                  <span>15s (intensivo)</span><span>5min (pasivo)</span>
                </div>
              </div>
              <div>
                <label className="text-xs text-text-muted uppercase tracking-wider font-bold mb-1 block">Notas (opcional)</label>
                <input value={watchNotes} onChange={e => setWatchNotes(e.target.value)}
                  placeholder="Motivo del monitoreo..."
                  className="w-full px-4 py-2.5 rounded-xl bg-bg border border-border-subtle text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-primary/60 transition-all" />
              </div>
              <button onClick={handleWatch} disabled={watchLoading || !watchUsername.trim()}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-black text-sm transition-all disabled:opacity-50"
                style={{ background: 'linear-gradient(135deg,#ee1d52,#69c9d0)', boxShadow: '0 0 20px #ee1d5244' }}>
                {watchLoading ? <RefreshCw size={14} className="animate-spin" /> : <Eye size={14} />}
                Iniciar Monitoreo
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Probe ──────────────────────────────────────────────────────── */}
      {probeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-card p-6 w-full max-w-xl rounded-2xl border border-accent-secondary/30 shadow-[0_0_40px_rgba(56,189,248,0.15)]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-black flex items-center gap-2">
                <Search size={18} className="text-accent-secondary" /> Probe Rápido
              </h3>
              <button onClick={() => { setProbeModal(false); setProbeResult(null); }}
                className="p-1.5 rounded-lg hover:bg-card text-text-muted hover:text-text-primary transition-all">
                <X size={16} />
              </button>
            </div>
            <div className="flex gap-2 mb-4">
              <input value={probeTarget} onChange={e => setProbeTarget(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleProbe()}
                placeholder="@handle TikTok"
                className="flex-1 px-4 py-2.5 rounded-xl bg-bg border border-border-subtle text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-secondary/50 transition-all" />
              <button onClick={handleProbe} disabled={probeLoading || !probeTarget.trim()}
                className="px-4 py-2.5 rounded-xl font-bold text-sm disabled:opacity-50 transition-all"
                style={{ background: 'linear-gradient(135deg,#0ea5e9,#6d28d9)' }}>
                {probeLoading ? <RefreshCw size={14} className="animate-spin" /> : <Zap size={14} />}
              </button>
            </div>

            {probeLoading && (
              <div className="flex items-center gap-2 text-text-muted text-sm py-4">
                <RefreshCw size={16} className="animate-spin text-accent-secondary" /> Analizando canal…
              </div>
            )}

            {probeResult && (
              <div className="flex flex-col gap-3 max-h-96 overflow-y-auto scrollbar-hide">
                {/* Live status */}
                {probeResult.live_snapshot && (
                  <div className="bg-card rounded-xl p-3 border border-border-subtle">
                    <div className="flex items-center gap-2 mb-2 text-xs font-bold text-text-muted uppercase tracking-wider">
                      <Radio size={11} /> Stream Status
                    </div>
                    {probeResult.live_snapshot.error && (
                      <div className="flex items-start gap-2 p-2 mb-3 rounded-lg border border-status-error/30 bg-status-error/5">
                        <AlertTriangle size={14} className="text-status-error mt-0.5 shrink-0" />
                        <p className="text-xs text-status-error font-mono leading-snug">{probeResult.live_snapshot.error}</p>
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div><span className="text-text-muted">Estado: </span>
                        <span className={`font-bold ${probeResult.live_snapshot.is_live ? 'text-status-error' : 'text-text-muted'}`}>
                          {probeResult.live_snapshot.is_live ? '🔴 EN VIVO' : '⚫ Offline'}
                        </span>
                      </div>
                      <div><span className="text-text-muted">Viewers: </span>
                        <span className="font-bold text-accent-secondary">{probeResult.live_snapshot.viewers?.toLocaleString() || '—'}</span>
                      </div>
                      <div className="col-span-2"><span className="text-text-muted">Título: </span>
                        <span className="font-medium">{probeResult.live_snapshot.title || '—'}</span>
                      </div>
                      <div><span className="text-text-muted">Room ID: </span>
                        <span className="font-mono text-[10px] text-text-primary">{probeResult.live_snapshot.room_id || '—'}</span>
                      </div>
                      <div><span className="text-text-muted">User ID: </span>
                        <span className="font-mono text-[10px] text-status-warning">{probeResult.live_snapshot.user_id || '—'}</span>
                      </div>
                      <div><span className="text-text-muted">CDN: </span>
                        <span className="font-mono text-xs text-accent-primary">{probeResult.live_snapshot.cdn_provider || '—'}</span>
                      </div>
                      <div><span className="text-text-muted">Bot: </span>
                        <span className="font-bold" style={{ color: BOT_COLOR(probeResult.live_snapshot.bot_score || 0) }}>
                          {Math.round((probeResult.live_snapshot.bot_score || 0) * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Raw JSON toggle */}
                <details className="bg-card rounded-xl p-3 border border-border-subtle">
                  <summary className="text-xs font-bold text-text-muted uppercase tracking-wider cursor-pointer hover:text-text-primary transition-colors">
                    Ver JSON completo
                  </summary>
                  <pre className="text-[10px] font-mono text-accent-secondary mt-2 overflow-auto max-h-48 scrollbar-hide whitespace-pre-wrap">
                    {JSON.stringify(probeResult, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
