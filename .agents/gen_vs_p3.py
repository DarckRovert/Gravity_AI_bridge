part3 = r"""
  const renderQueue = () => (
    <div className="space-y-4">
      {status?.current_job ? (
        <div className="glass-panel p-6 rounded-2xl border-accent-primary/40 bg-accent-primary/5 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10"><Film size={80}/></div>
          <div className="relative z-10 space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <div className="text-[10px] font-bold text-accent-primary uppercase tracking-widest flex items-center gap-2 mb-1">
                  <span className="w-2 h-2 rounded-full bg-accent-primary animate-ping"/>
                  EN PROCESO — ID #{status.current_job.id}
                </div>
                <h3 className="text-xl font-black text-text-primary">{status.current_job.topic}</h3>
              </div>
              <div className="text-4xl font-black text-accent-primary">{status.current_job.progress}%</div>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] font-bold text-text-muted uppercase">
                <span>{status.current_job.current_step}</span>
              </div>
              <div className="w-full bg-surface h-2 rounded-full overflow-hidden border border-border-subtle">
                <div className="h-full bg-accent-primary transition-all duration-1000 shadow-[0_0_10px_rgba(99,102,241,0.5)]"
                  style={{width:`${status.current_job.progress}%`}}/>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="glass-panel p-8 rounded-2xl border-dashed border-border-subtle text-center text-text-muted flex flex-col items-center gap-2">
          <Clock size={36} className="opacity-20"/>
          <p className="font-medium text-sm">No hay producciones activas</p>
        </div>
      )}
      {status?.pending_jobs && status.pending_jobs.length > 0 && (
        <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
          <div className="p-4 border-b border-border-subtle bg-surface/30 flex items-center gap-2">
            <List size={15} className="text-accent-secondary"/>
            <span className="font-bold text-text-primary text-sm">Cola Pendiente ({status.pending_count})</span>
          </div>
          <div className="divide-y divide-border-subtle">
            {status.pending_jobs.map(job => (
              <div key={job.id} className="flex items-center justify-between p-4 hover:bg-card transition-colors">
                <div>
                  <div className="font-bold text-sm text-text-primary">#{job.id} — {job.title || job.topic}</div>
                  <div className="text-[10px] text-text-muted">{job.style} • {job.n_scenes} escenas</div>
                </div>
                <div className="flex gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${statusColor(job.status)}`}>{job.status}</span>
                  <button onClick={()=>cancelJob(job.id)}
                    className="p-1.5 rounded-lg bg-surface border border-border-subtle text-status-error hover:bg-status-error hover:text-white transition-all"
                    title="Cancelar"><Square size={13}/></button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderHistory = () => (
    <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-surface/90 text-[10px] uppercase font-bold text-text-muted sticky top-0 z-10">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Producción</th>
              <th className="px-4 py-3">Detalles</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle">
            {(status?.history || []).map(job => (
              <tr key={job.id} className="hover:bg-card transition-colors group">
                <td className="px-4 py-3 font-mono text-xs text-text-muted">#{job.id}</td>
                <td className="px-4 py-3">
                  <div className="font-bold text-text-primary">{job.title || job.topic}</div>
                  <div className="text-[10px] text-text-muted mt-0.5 truncate max-w-[180px]">{job.topic}</div>
                </td>
                <td className="px-4 py-3 text-[10px] text-text-muted space-y-0.5">
                  <div>{job.style} • {job.n_scenes} esc • {job.resolution}</div>
                  <div>{job.quality?.toUpperCase()} • {job.fps || 24}fps • {job.narration_lang?.toUpperCase()}</div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${statusColor(job.status)}`}>
                    {job.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1.5">
                    <button disabled={!isDone(job)}
                      onClick={()=>isDone(job) && setSelectedVideo(job)}
                      className={`p-1.5 rounded-lg border transition-all ${isDone(job) ? 'bg-surface border-border-subtle text-accent-primary hover:bg-accent-primary hover:text-white cursor-pointer' : 'opacity-30 cursor-not-allowed bg-surface border-border-subtle text-text-muted'}`}
                      title="Reproducir"><Play size={13} fill="currentColor"/></button>
                    <a href={isDone(job) ? downloadUrl(job) : '#'} download
                      className={`p-1.5 rounded-lg border transition-all ${isDone(job) ? 'bg-surface border-border-subtle text-accent-secondary hover:bg-accent-secondary hover:text-white' : 'opacity-30 pointer-events-none bg-surface border-border-subtle text-text-muted'}`}
                      title="Descargar MP4"><Download size={13}/></a>
                    <button onClick={()=>deleteJob(job.id)}
                      className="p-1.5 rounded-lg bg-surface border border-border-subtle text-status-error hover:bg-status-error hover:text-white cursor-pointer transition-all"
                      title="Eliminar"><Trash2 size={13}/></button>
                  </div>
                </td>
              </tr>
            ))}
            {(!status?.history || status.history.length === 0) && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-text-muted text-sm">Sin historial de producciones</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
"""

with open('F:/Gravity_AI_bridge/.agents/vs_part3.txt', 'w', encoding='utf-8') as f:
    f.write(part3)
print("Part3 written:", len(part3))
