import React, { useState } from 'react';
import { PlayCircle, Search, Clock, Eye, Target, Brain, AlignLeft, Lightbulb, TrendingUp, AlertCircle, ThumbsUp, MessageSquare, Activity, Copy, Download, CheckCircle } from 'lucide-react';

export const YouTubeAnalyzer: React.FC = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleExportMarkdown = () => {
    if (!data) return;
    const md = `
# Análisis AI: ${data.title || 'Video'}
**Canal:** ${data.channel} | **Visualizaciones:** ${data.views}
**Engagement:** ${data.engagement_rate}% | **Hook Score:** ${data.analysis?.hook_score}/10 | **Tono:** ${data.analysis?.tone}

## Resumen Ejecutivo
${data.analysis?.summary}

## Key Takeaways
${data.analysis?.key_takeaways?.map ? data.analysis.key_takeaways.map((k: string) => `- ${k}`).join('\n') : 'N/A'}

## Estrategia de Monetización
${Array.isArray(data.analysis?.monetization_strategy) ? data.analysis.monetization_strategy.map((m: string) => `- ${m}`).join('\n') : (data.analysis?.monetization_strategy || 'N/A')}

## Capítulos Clave
${data.analysis?.timestamps?.map ? data.analysis.timestamps.map((t: any) => `- **${t.time}**: ${t.description}`).join('\n') : 'N/A'}
    `.trim();
    
    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadTxt = () => {
    if (!data) return;
    const takeaways = data.analysis?.key_takeaways?.join ? data.analysis.key_takeaways.join('\n') : 'N/A';
    const md = `ANÁLISIS AI: ${data.title}\nCANAL: ${data.channel}\nENGAGEMENT: ${data.engagement_rate}%\nHOOK SCORE: ${data.analysis?.hook_score}/10\n\nRESUMEN:\n${data.analysis?.summary || 'N/A'}\n\nTAKEAWAYS:\n${takeaways}`;
    const blob = new Blob([md], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Analysis_${(data.title || 'Video').substring(0, 20)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.includes('youtube.com/') && !url.includes('youtu.be/')) {
      setError('Por favor ingresa una URL válida de YouTube');
      return;
    }
    
    setLoading(true);
    setError(null);
    setData(null);

    try {
      const res = await fetch('/v1/youtube/analyzer/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      
      const result = await res.json();
      if (!res.ok) throw new Error(result.error || 'Error al analizar el video');
      
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const formatViews = (views: number) => {
    if (views >= 1000000) return (views / 1000000).toFixed(1) + 'M';
    if (views >= 1000) return (views / 1000).toFixed(1) + 'K';
    return views.toString();
  };

  return (
    <div className="h-full flex flex-col p-8 overflow-y-auto space-y-8 bg-gradient-to-b from-[#0a0a0a] to-[#141414]">
      {/* Header */}
      <div className="flex justify-between items-end border-b border-border-subtle pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#FF0000]/10 border border-[#FF0000]/30 rounded-full text-[#FF0000] text-xs font-bold uppercase tracking-widest mb-3">
            <PlayCircle size={14} /> AI Video Intelligence
          </div>
          <h1 className="text-4xl font-black tracking-tight text-white flex items-center gap-4 drop-shadow-[0_0_15px_rgba(255,0,0,0.3)]">
            YouTube <span className="text-[#FF0000]">Analyzer PRO</span>
          </h1>
          <p className="text-text-muted mt-2 text-lg">Descomposición y análisis cognitivo de contenido mediante DeepSeek AI.</p>
        </div>
        
        {data && !loading && (
          <div className="flex gap-3">
            <button onClick={handleExportMarkdown} className="px-4 py-2 bg-surface hover:bg-surface-hover border border-border-subtle rounded-lg text-sm font-bold text-white flex items-center gap-2 transition-colors">
              {copied ? <CheckCircle size={16} className="text-green-500" /> : <Copy size={16} />}
              {copied ? 'Copiado!' : 'Copiar MD'}
            </button>
            <button onClick={handleDownloadTxt} className="px-4 py-2 bg-[#FF0000]/10 hover:bg-[#FF0000]/20 border border-[#FF0000]/30 rounded-lg text-sm font-bold text-[#FF0000] flex items-center gap-2 transition-colors">
              <Download size={16} />
              Descargar TXT
            </button>
          </div>
        )}
      </div>

      {/* Input Section */}
      <form onSubmit={handleAnalyze} className="relative w-full max-w-3xl mx-auto">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <PlayCircle className="text-[#FF0000]" size={24} />
        </div>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Pega la URL del video de YouTube (ej. https://youtube.com/watch?v=...)"
          className="w-full pl-12 pr-32 py-4 bg-surface border border-border-subtle rounded-2xl text-white placeholder-text-muted focus:outline-none focus:border-[#FF0000] focus:ring-1 focus:ring-[#FF0000] transition-all shadow-[0_0_20px_rgba(0,0,0,0.3)] text-lg"
        />
        <button
          type="submit"
          disabled={loading || !url}
          className="absolute right-2 top-2 bottom-2 px-6 bg-[#FF0000] hover:bg-[#cc0000] disabled:bg-surface disabled:text-text-muted disabled:border disabled:border-border-subtle text-white font-bold rounded-xl transition-colors flex items-center gap-2"
        >
          {loading ? (
            <Search className="animate-spin" size={20} />
          ) : (
            <>
              <Brain size={20} />
              <span>Analizar</span>
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="max-w-3xl mx-auto w-full p-4 bg-red-500/10 border border-red-500/50 rounded-xl flex items-center gap-3 text-red-500">
          <AlertCircle size={20} />
          <p className="font-medium">{error}</p>
        </div>
      )}

      {loading && (
        <div className="flex-1 flex flex-col items-center justify-center space-y-6">
          <div className="relative w-24 h-24 mx-auto">
            <div className="absolute inset-0 rounded-full border-4 border-t-[#FF0000] border-r-[#FF0000] border-b-transparent border-l-transparent animate-spin"></div>
            <Brain className="absolute inset-0 m-auto text-[#FF0000] animate-pulse" size={32} />
          </div>
          <h3 className="text-2xl font-black text-white uppercase tracking-[0.2em] animate-pulse">Analizando Video...</h3>
          <p className="text-text-muted max-w-md text-center">Descargando metadatos, extrayendo subtítulos y consultando a la Red Neuronal para extraer insights de valor...</p>
        </div>
      )}

      {data && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 pb-10">
          {/* Metadata Card */}
          <div className="glass-card rounded-3xl p-6 bg-surface border border-border-subtle shadow-lg flex flex-col gap-6">
            <div className="rounded-xl overflow-hidden border border-white/10 relative group">
              <img src={data.thumbnail} alt="Thumbnail" className="w-full object-cover aspect-video group-hover:scale-105 transition-transform duration-500" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"></div>
              <div className="absolute bottom-3 right-3 px-2 py-1 bg-black/80 rounded border border-white/20 text-xs font-bold text-white flex items-center gap-1">
                <Clock size={12} /> {formatDuration(data.duration)}
              </div>
            </div>
            
            <div>
              <h2 className="text-xl font-bold text-white leading-tight mb-2">{data.title}</h2>
              <p className="text-[#FF0000] font-medium flex items-center gap-2">
                <Target size={16} /> {data.channel}
              </p>
            </div>

            <div className="flex items-center gap-6 mt-auto pt-4 border-t border-border-subtle">
              <div className="flex flex-col">
                <span className="text-xs text-text-muted uppercase tracking-wider font-bold mb-1">Views</span>
                <span className="text-lg font-black text-white flex items-center gap-2">
                  <Eye size={16} className="text-[#FF0000]" /> {formatViews(data.views || 0)}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-text-muted uppercase tracking-wider font-bold mb-1">Likes</span>
                <span className="text-lg font-black text-white flex items-center gap-2">
                  <ThumbsUp size={16} className="text-blue-400" /> {formatViews(data.likes || 0)}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-text-muted uppercase tracking-wider font-bold mb-1">Comments</span>
                <span className="text-lg font-black text-white flex items-center gap-2">
                  <MessageSquare size={16} className="text-green-400" /> {formatViews(data.comments || 0)}
                </span>
              </div>
            </div>

            {/* Engagement & Tone */}
            <div className="grid grid-cols-2 gap-4 mt-2">
              <div className="bg-[#0a0a0a] rounded-xl p-3 border border-border-subtle flex flex-col items-center justify-center">
                <span className="text-xs text-text-muted uppercase font-bold mb-1 flex items-center gap-1"><Activity size={12}/> Engagement</span>
                <span className="text-2xl font-black text-[#FF0000]">{data.engagement_rate || 0}%</span>
              </div>
              <div className="bg-[#0a0a0a] rounded-xl p-3 border border-border-subtle flex flex-col items-center justify-center text-center">
                <span className="text-xs text-text-muted uppercase font-bold mb-1">Tono Principal</span>
                <span className="text-sm font-bold text-white">{data.analysis?.tone || 'N/A'}</span>
              </div>
            </div>

            {/* Hook Score */}
            <div className="bg-surface rounded-xl p-4 border border-border-subtle flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-sm font-bold text-white flex items-center gap-2"><Target size={16} className="text-[#FCC419]" /> Hook Score</span>
                <span className="text-xs text-text-muted">Retención en primeros 30s</span>
              </div>
              <div className="w-12 h-12 rounded-full border-4 border-[#FCC419] flex items-center justify-center bg-[#FCC419]/10">
                <span className="font-black text-white">{data.analysis?.hook_score || 0}</span>
              </div>
            </div>
          </div>

          {/* AI Analysis Cards */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Summary */}
            <div className="glass-card rounded-2xl p-6 bg-surface border border-border-subtle shadow-lg relative overflow-hidden group">
              <div className="absolute -top-10 -right-10 w-32 h-32 bg-[#FF0000]/10 rounded-full blur-[40px] group-hover:bg-[#FF0000]/20 transition-colors"></div>
              <h3 className="text-lg font-bold text-white flex items-center gap-3 mb-4">
                <AlignLeft className="text-[#FF0000]" /> Resumen Ejecutivo AI
              </h3>
              <p className="text-text-primary text-lg leading-relaxed">
                {data.analysis?.summary}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Key Takeaways */}
              <div className="glass-card rounded-2xl p-6 bg-surface border border-border-subtle shadow-lg">
                <h3 className="text-lg font-bold text-white flex items-center gap-3 mb-4">
                  <Lightbulb className="text-[#FCC419]" /> Key Takeaways
                </h3>
                <ul className="space-y-3">
                  {data.analysis?.key_takeaways?.map((point: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3">
                      <div className="w-6 h-6 rounded-full bg-[#FCC419]/10 text-[#FCC419] flex items-center justify-center flex-shrink-0 text-sm font-bold mt-0.5">
                        {idx + 1}
                      </div>
                      <span className="text-text-primary">{point}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Monetization */}
              <div className="glass-card rounded-2xl p-6 bg-surface border border-[#4CAF50]/30 shadow-[0_0_30px_rgba(76,175,80,0.1)]">
                <h3 className="text-lg font-bold text-white flex items-center gap-3 mb-4">
                  <TrendingUp className="text-[#4CAF50]" /> Estrategia de Monetización
                </h3>
                {Array.isArray(data.analysis?.monetization_strategy) ? (
                  <ul className="space-y-3">
                    {data.analysis.monetization_strategy.map((m: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-3">
                        <div className="w-2 h-2 rounded-full bg-[#4CAF50] mt-2 flex-shrink-0 shadow-[0_0_8px_rgba(76,175,80,0.8)]"></div>
                        <span className="text-[#4ade80] font-medium leading-relaxed">{m}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-[#4ade80] font-medium leading-relaxed">
                    {data.analysis?.monetization_strategy}
                  </p>
                )}
              </div>
            </div>

            {/* Timestamps / Capítulos */}
            {data.analysis?.timestamps && data.analysis.timestamps.length > 0 && (
              <div className="glass-card rounded-2xl p-6 bg-surface border border-border-subtle shadow-lg">
                <h3 className="text-lg font-bold text-white flex items-center gap-3 mb-4">
                  <Clock className="text-blue-400" /> Capítulos Estructurados
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {data.analysis.timestamps.map((ts: any, i: number) => (
                    <div key={i} className="flex items-center gap-3 bg-[#0a0a0a] p-3 rounded-lg border border-border-subtle">
                      <span className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs font-mono font-bold rounded">{ts.time}</span>
                      <span className="text-sm text-text-primary truncate">{ts.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Raw Transcript Toggle */}
            <details className="glass-card rounded-xl border border-border-subtle group/details">
              <summary className="p-4 cursor-pointer text-text-muted hover:text-white font-bold flex items-center gap-2 select-none">
                <AlignLeft size={16} /> Ver Transcripción Extraída (Raw)
              </summary>
              <div className="p-4 pt-0 border-t border-border-subtle">
                <div className="bg-[#0a0a0a] p-4 rounded-lg h-48 overflow-y-auto text-sm text-text-muted font-mono whitespace-pre-wrap leading-relaxed">
                  {data.transcript || "No se detectó transcripción."}
                </div>
              </div>
            </details>

          </div>
        </div>
      )}
    </div>
  );
};
