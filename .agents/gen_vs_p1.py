part1 = r"""import { useEffect, useState, useRef, useCallback } from 'react';
import {
  Video, Film, PlayCircle, Clock, CheckCircle2, AlertCircle, Plus, RefreshCw,
  X, Share2, Camera, MonitorPlay, Download, Play, Trash2, Pause, Square,
  Settings2, Clapperboard, Volume2, VolumeX, HardDrive, Layers,
  ChevronDown, ChevronUp, Info, Cpu, Timer, List, Eye
} from 'lucide-react';

// ── Tipos ─────────────────────────────────────────────────────────────────────
interface VideoJob {
  id: number;
  topic: string;
  title: string;
  style: string;
  n_scenes: number;
  status: string;
  progress: number;
  current_step: string;
  output_path: string;
  created_at: string;
  finished_at: string;
  resolution: string;
  quality: string;
  fps: number;
  scene_duration: number;
  bgm_type: string;
  narration_lang: string;
}

interface VideoStatus {
  pending_count: number;
  pending_jobs: VideoJob[];
  current_job: VideoJob | null;
  history: VideoJob[];
  ffmpeg_ok: boolean;
  styles: Record<string, string>;
  disk_free_gb?: number;
  disk_total_gb?: number;
  disk_used_gb?: number;
  disk_pct?: number;
  videos_size_gb?: number;
}

const API = 'http://localhost:7860';

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmtSize(gb: number): string {
  if (gb < 0.01) return `${(gb * 1024).toFixed(0)} MB`;
  return `${gb.toFixed(2)} GB`;
}

function statusColor(s: string): string {
  const l = s?.toLowerCase();
  if (l === 'done' || l === 'completed') return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
  if (l === 'running') return 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30';
  if (l === 'pending') return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
  if (l === 'deleted') return 'bg-surface text-text-muted border-border-subtle';
  return 'bg-red-500/15 text-red-400 border-red-500/30';
}

// ── Componente principal ──────────────────────────────────────────────────────
export const VideoStudio = () => {
  // Estado global
  const [status, setStatus] = useState<VideoStatus | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<VideoJob | null>(null);
  const [creating, setCreating] = useState(false);
  const [toast, setToast] = useState('');
  const [activeTab, setActiveTab] = useState<'create'|'queue'|'history'>('create');
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Parámetros de producción — Identidad
  const [title, setTitle]   = useState('');
  const [topic, setTopic]   = useState('');
  const [scenes, setScenes] = useState(6);

  // Dirección de Arte
  const [style, setStyle]         = useState('documental');
  const [resolution, setResolution] = useState('1216x832');
  const [quality, setQuality]     = useState('hd');
  const [fps, setFps]             = useState(24);
  const [codec, setCodec]         = useState('libx264');

  // Ingeniería de Sonido
  const [lang, setLang]           = useState('es');
  const [voiceId, setVoiceId]     = useState('');
  const [voiceSpeed, setVoiceSpeed] = useState(150);
  const [bgmType, setBgmType]     = useState('ninguna');
  const [bgmVolume, setBgmVolume] = useState(0.10);

  // Post-producción
  const [transitions, setTransitions] = useState(true);
  const [subtitles, setSubtitles]     = useState(true);
  const [useLore, setUseLore]         = useState(true);
  const [sceneDuration, setSceneDuration] = useState(8);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3500); };

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/v1/video/status`);
      if (res.ok) setStatus(await res.json());
    } catch (_) {}
  }, []);

  useEffect(() => {
    fetchStatus();
    const iv = setInterval(fetchStatus, 4000);
    return () => clearInterval(iv);
  }, [fetchStatus]);

  const createVideo = async () => {
    if (!topic.trim()) return;
    setCreating(true);
    try {
      const res = await fetch(`${API}/v1/video/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic, title, n_scenes: scenes, style,
          voice_speed: voiceSpeed, voice_id: voiceId,
          narration_lang: lang, transitions, resolution,
          subtitles, bgm_type: bgmType, quality, use_lore: useLore,
          fps, scene_duration: sceneDuration, bgm_volume: bgmVolume, codec,
        })
      });
      const data = await res.json();
      if (res.ok) {
        showToast(`✓ Job #${data.job_id} encolado`);
        setTopic(''); setTitle('');
        setActiveTab('queue');
        fetchStatus();
      } else {
        showToast(`✗ ${data.error}`);
      }
    } catch (e) {
      showToast('✗ Error de conexión con el servidor');
    } finally {
      setCreating(false);
    }
  };

  const cancelJob = async (jobId: number) => {
    try {
      await fetch(`${API}/v1/video/cancel`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: jobId })
      });
      fetchStatus();
      showToast('Job cancelado');
    } catch (_) { showToast('Error al cancelar'); }
  };

  const deleteJob = async (jobId: number) => {
    if (!confirm(`¿Eliminar producción #${jobId} y todos sus archivos?`)) return;
    try {
      const res = await fetch(`${API}/v1/video/delete`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: jobId })
      });
      const data = await res.json();
      showToast(data.ok ? `✓ Producción #${jobId} eliminada` : `✗ ${data.errors?.[0] || 'Error'}`);
      fetchStatus();
    } catch (_) { showToast('Error al eliminar'); }
  };

  const streamUrl = (job: VideoJob) => {
    const fname = job.output_path?.split(/[/\\]/).pop() || '';
    return `${API}/v1/video/stream?path=${encodeURIComponent(fname)}`;
  };

  const downloadUrl = (job: VideoJob) => {
    const fname = job.output_path?.split(/[/\\]/).pop() || '';
    return `${API}/v1/video/download?file=${encodeURIComponent(fname)}`;
  };

  const isDone = (j: VideoJob) => ['done','completed'].includes(j.status?.toLowerCase());
"""

with open('F:/Gravity_AI_bridge/.agents/vs_part1.txt', 'w', encoding='utf-8') as f:
    f.write(part1)
print("Part1 written:", len(part1))
