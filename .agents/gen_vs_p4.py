part4 = r"""
  // ── Métricas laterales ────────────────────────────────────────────────────
  const renderMetrics = () => (
    <div className="glass-panel p-5 rounded-2xl border border-border-subtle space-y-4">
      <h3 className="text-xs font-bold text-text-primary uppercase tracking-widest flex items-center gap-2">
        <Cpu size={13} className="text-accent-primary"/> Pipeline Metrics
      </h3>
      <div className="space-y-3">
        {[
          ['Completados', status?.history?.filter(j=>isDone(j)).length ?? 0],
          ['En Cola', status?.pending_count ?? 0],
          ['Total Historial', status?.history?.length ?? 0],
        ].map(([k,v]) => (
          <div key={k as string} className="flex justify-between items-center text-sm">
            <span className="text-text-muted">{k as string}</span>
            <span className="font-bold text-text-primary">{v as number}</span>
          </div>
        ))}
        <div className="border-t border-border-subtle pt-3 space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-text-muted flex items-center gap-1"><HardDrive size={11}/> Disco Libre</span>
            <span className="font-bold text-text-primary">{status?.disk_free_gb ? fmtSize(status.disk_free_gb) : '—'}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-text-muted">Videos ({fmtSize(status?.videos_size_gb ?? 0)})</span>
            <span className="font-bold text-text-primary">{status?.disk_pct ? `${status.disk_pct}% usado` : '—'}</span>
          </div>
          {status?.disk_pct !== undefined && (
            <div className="w-full bg-surface h-1.5 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all ${status.disk_pct > 85 ? 'bg-status-error' : status.disk_pct > 70 ? 'bg-amber-500' : 'bg-status-success'}`}
                style={{width:`${status.disk_pct}%`}}/>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // ── Configuración estimada ─────────────────────────────────────────────────
  const renderSummary = () => {
    const totalSecs = scenes * sceneDuration;
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return (
      <div className="glass-panel p-5 rounded-2xl border border-border-subtle space-y-3">
        <h3 className="text-xs font-bold text-text-primary uppercase tracking-widest flex items-center gap-2">
          <Info size={13} className="text-accent-secondary"/> Resumen de Producción
        </h3>
        <div className="space-y-2 text-xs">
          {[
            ['Duración Estimada', `~${mins}m ${secs}s`],
            ['Escenas', `${scenes} × ${sceneDuration}s`],
            ['Resolución', resolution],
            ['FPS', `${fps} fps`],
            ['Codec', codec],
            ['Calidad', quality.toUpperCase()],
            ['BGM', bgmType === 'ninguna' ? 'Sin música' : bgmType],
          ].map(([k,v]) => (
            <div key={k} className="flex justify-between">
              <span className="text-text-muted">{k}</span>
              <span className="font-bold text-text-primary font-mono text-[10px]">{v}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="h-full overflow-y-auto p-6 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-[999] px-4 py-3 rounded-xl bg-surface border border-border-subtle shadow-2xl text-sm font-bold text-text-primary animate-in slide-in-from-right-4 duration-300">
          {toast}
        </div>
      )}

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle">
              <Clapperboard className="text-accent-primary" size={26}/>
            </div>
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight text-text-primary">Video Studio</h1>
              <p className="text-text-muted text-sm mt-0.5">Pipeline cinematográfico IA — Sin límite de duración</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className={`px-3 py-1.5 rounded-xl border flex items-center gap-1.5 text-xs font-bold
              ${status?.ffmpeg_ok ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
              {status?.ffmpeg_ok ? <CheckCircle2 size={13}/> : <AlertCircle size={13}/>}
              FFMPEG {status?.ffmpeg_ok ? 'READY' : 'MISSING'}
            </div>
            <button onClick={fetchStatus} className="p-2 rounded-xl bg-surface border border-border-subtle hover:bg-card transition-colors">
              <RefreshCw size={14} className="text-text-muted"/>
            </button>
          </div>
        </div>

        {/* Layout principal */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
          {/* Columna izquierda */}
          <div className="space-y-4">
            {/* Tabs */}
            <div className="flex bg-surface rounded-xl border border-border-subtle p-1 gap-1">
              {(['create','queue','history'] as const).map(tab => (
                <button key={tab} onClick={()=>setActiveTab(tab)}
                  className={`flex-1 py-2 px-3 rounded-lg text-xs font-bold uppercase tracking-widest transition-all ${activeTab===tab ? 'bg-accent-primary text-white shadow-lg' : 'text-text-muted hover:text-text-primary'}`}>
                  {tab === 'create' ? '+ Nueva' : tab === 'queue' ? `Cola (${status?.pending_count ?? 0})` : 'Historial'}
                </button>
              ))}
            </div>

            {activeTab === 'create' && (
              <>
                {renderCreate()}
                <button onClick={createVideo} disabled={creating || !topic.trim()}
                  className="w-full py-4 rounded-xl bg-accent-primary text-white font-extrabold shadow-lg hover:scale-[1.01] active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
                  {creating ? <RefreshCw className="animate-spin" size={18}/> : <Film size={18}/>}
                  {creating ? 'ENCOLANDO PRODUCCIÓN...' : 'INICIAR PRODUCCIÓN'}
                </button>
              </>
            )}
            {activeTab === 'queue' && renderQueue()}
            {activeTab === 'history' && renderHistory()}
          </div>

          {/* Columna derecha */}
          <div className="space-y-4">
            {renderMetrics()}
            {activeTab === 'create' && renderSummary()}
          </div>
        </div>
      </div>

      {/* Modal reproductor */}
      {selectedVideo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-surface border border-border-subtle rounded-2xl overflow-hidden max-w-5xl w-full shadow-2xl">
            <div className="p-4 border-b border-border-subtle flex justify-between items-center bg-card">
              <div>
                <h3 className="font-bold text-text-primary">{selectedVideo.title || selectedVideo.topic}</h3>
                <p className="text-[10px] text-text-muted mt-0.5">
                  #{selectedVideo.id} • {selectedVideo.style} • {selectedVideo.resolution} • {selectedVideo.fps || 24}fps
                </p>
              </div>
              <button onClick={()=>setSelectedVideo(null)} className="p-2 rounded-lg bg-surface hover:text-status-error transition-colors">
                <X size={18}/>
              </button>
            </div>
            <div className="bg-black flex justify-center">
              <video ref={videoRef} controls autoPlay
                src={streamUrl(selectedVideo)}
                className="max-h-[55vh] w-full object-contain"
                style={{background:'#000'}}/>
            </div>
            <div className="p-5 bg-card border-t border-border-subtle">
              <h4 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-3">Exportar & Distribuir</h4>
              <div className="flex flex-wrap gap-3">
                <a href={downloadUrl(selectedVideo)} download target="_blank" rel="noreferrer"
                  className="flex-1 min-w-[120px] py-2.5 bg-accent-primary/10 text-accent-primary border border-accent-primary/30 font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-accent-primary hover:text-white transition-all text-sm">
                  <Download size={15}/> MP4 Master
                </a>
                <button onClick={()=>window.open('https://studio.youtube.com/','_blank')}
                  className="flex-1 min-w-[120px] py-2.5 bg-red-600/10 text-red-400 border border-red-500/30 font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-red-600 hover:text-white transition-all text-sm">
                  <MonitorPlay size={15}/> YouTube
                </button>
                <button onClick={()=>window.open('https://www.instagram.com/','_blank')}
                  className="flex-1 min-w-[120px] py-2.5 bg-pink-600/10 text-pink-400 border border-pink-500/30 font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-pink-600 hover:text-white transition-all text-sm">
                  <Camera size={15}/> Reels
                </button>
                <button onClick={()=>window.open('https://business.facebook.com/','_blank')}
                  className="flex-1 min-w-[120px] py-2.5 bg-blue-600/10 text-blue-400 border border-blue-500/30 font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-blue-600 hover:text-white transition-all text-sm">
                  <Share2 size={15}/> Facebook
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
"""

with open('F:/Gravity_AI_bridge/.agents/vs_part4.txt', 'w', encoding='utf-8') as f:
    f.write(part4)
print("Part4 written:", len(part4))
