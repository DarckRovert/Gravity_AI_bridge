part2 = r"""
  // ── RENDER JSX ──────────────────────────────────────────────────────────────
  const renderCreate = () => (
    <div className="space-y-5">
      {/* Identidad */}
      <div className="bg-surface/30 p-5 rounded-2xl border border-border-subtle space-y-4">
        <h3 className="text-[11px] font-black text-accent-primary uppercase tracking-widest flex items-center gap-2">
          <Film size={13}/> 1. Identidad de Producción
        </h3>
        <div>
          <label className="label-xs">Título del Proyecto</label>
          <input type="text" value={title} onChange={e=>setTitle(e.target.value)}
            placeholder="Ej: El Misterio del Universo..."
            className="input-field mt-1"/>
        </div>
        <div>
          <label className="label-xs">Tema / Guion Maestro</label>
          <textarea value={topic} onChange={e=>setTopic(e.target.value)}
            placeholder="Describe la historia que quieres contar..."
            className="input-field mt-1 h-24 resize-none"/>
        </div>
        <div>
          <label className="label-xs">Escenas ({scenes})</label>
          <div className="flex items-center gap-3 mt-1">
            <input type="range" min="2" max="30" value={scenes}
              onChange={e=>setScenes(+e.target.value)} className="flex-1 accent-accent-primary"/>
            <span className="text-xs font-mono text-accent-primary w-6 text-center">{scenes}</span>
          </div>
          <p className="text-[10px] text-text-muted mt-1">Sin límite de tiempo — el usuario elige la duración</p>
        </div>
      </div>

      {/* Arte */}
      <div className="bg-surface/30 p-5 rounded-2xl border border-border-subtle space-y-4">
        <h3 className="text-[11px] font-black text-accent-primary uppercase tracking-widest flex items-center gap-2">
          <Camera size={13}/> 2. Dirección de Arte
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label-xs">Estilo Visual</label>
            <select value={style} onChange={e=>setStyle(e.target.value)} className="input-field mt-1">
              {status?.styles ? Object.entries(status.styles).map(([k,v])=>(
                <option key={k} value={k}>{v as string}</option>
              )) : <option value="documental">Documental</option>}
            </select>
          </div>
          <div>
            <label className="label-xs">Resolución</label>
            <select value={resolution} onChange={e=>setResolution(e.target.value)} className="input-field mt-1">
              <option value="1920x1080">1920×1080 (Full HD 16:9)</option>
              <option value="1216x832">1216×832 (HD 16:9)</option>
              <option value="832x1216">832×1216 (9:16 Vertical)</option>
              <option value="1024x1024">1024×1024 (1:1 Cuadrado)</option>
              <option value="1280x720">1280×720 (720p)</option>
              <option value="2560x1440">2560×1440 (2K Cinemático)</option>
            </select>
          </div>
          <div>
            <label className="label-xs">Calidad de Render</label>
            <select value={quality} onChange={e=>setQuality(e.target.value)} className="input-field mt-1">
              <option value="standard">Estándar (30 steps, rápido)</option>
              <option value="hd">HD (60 steps)</option>
              <option value="4k">Cinemático 4K (120 steps)</option>
            </select>
          </div>
          <div>
            <label className="label-xs">FPS</label>
            <select value={fps} onChange={e=>setFps(+e.target.value)} className="input-field mt-1">
              <option value={24}>24 fps (Cinematográfico)</option>
              <option value={30}>30 fps (Broadcast)</option>
              <option value={60}>60 fps (Fluido)</option>
            </select>
          </div>
        </div>
        <div>
          <label className="label-xs">Duración por Escena ({sceneDuration}s)</label>
          <div className="flex items-center gap-3 mt-1">
            <input type="range" min="3" max="60" value={sceneDuration}
              onChange={e=>setSceneDuration(+e.target.value)} className="flex-1 accent-accent-primary"/>
            <span className="text-xs font-mono text-accent-primary w-8 text-center">{sceneDuration}s</span>
          </div>
          <p className="text-[10px] text-text-muted mt-1">
            Duración estimada total: ~{Math.ceil(scenes * sceneDuration / 60)} min {scenes * sceneDuration % 60}s
          </p>
        </div>
      </div>

      {/* Sonido */}
      <div className="bg-surface/30 p-5 rounded-2xl border border-border-subtle space-y-4">
        <h3 className="text-[11px] font-black text-accent-primary uppercase tracking-widest flex items-center gap-2">
          <Volume2 size={13}/> 3. Ingeniería de Sonido
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label-xs">Idioma Narración</label>
            <select value={lang} onChange={e=>setLang(e.target.value)} className="input-field mt-1">
              <option value="es">Español</option>
              <option value="en">English</option>
              <option value="pt">Português</option>
              <option value="fr">Français</option>
              <option value="de">Deutsch</option>
              <option value="it">Italiano</option>
            </select>
          </div>
          <div>
            <label className="label-xs">Voz Neuronal</label>
            <select value={voiceId} onChange={e=>setVoiceId(e.target.value)} className="input-field mt-1">
              <option value="">Auto / Sistema</option>
              <option value="es-ES-AlvaroNeural">Álvaro (ES)</option>
              <option value="es-ES-ElviraNeural">Elvira (ES)</option>
              <option value="es-MX-JorgeNeural">Jorge (MX)</option>
              <option value="es-MX-DaliaNeural">Dalia (MX)</option>
              <option value="en-US-ChristopherNeural">Christopher (US)</option>
              <option value="en-US-AriaNeural">Aria (US)</option>
              <option value="en-GB-RyanNeural">Ryan (GB)</option>
              <option value="en-GB-SoniaNeural">Sonia (GB)</option>
            </select>
          </div>
          <div>
            <label className="label-xs">Música BGM</label>
            <select value={bgmType} onChange={e=>setBgmType(e.target.value)} className="input-field mt-1">
              <option value="ninguna">Sin Música</option>
              <option value="epico">Épica / Cinemática</option>
              <option value="documental">Documental / Chill</option>
              <option value="synthwave">Retro / Synthwave</option>
              <option value="jazz">Jazz / Lounge</option>
            </select>
          </div>
          <div>
            <label className="label-xs">Velocidad Voz ({voiceSpeed})</label>
            <input type="range" min="80" max="300" step="5" value={voiceSpeed}
              onChange={e=>setVoiceSpeed(+e.target.value)} className="w-full mt-2 accent-accent-primary"/>
          </div>
        </div>
        {bgmType !== 'ninguna' && (
          <div>
            <label className="label-xs">Volumen BGM ({Math.round(bgmVolume*100)}%)</label>
            <input type="range" min="0" max="1" step="0.05" value={bgmVolume}
              onChange={e=>setBgmVolume(+e.target.value)} className="w-full mt-1 accent-accent-primary"/>
          </div>
        )}
      </div>

      {/* Post-producción avanzada */}
      <div className="bg-surface/30 rounded-2xl border border-border-subtle overflow-hidden">
        <button onClick={()=>setAdvancedOpen(!advancedOpen)}
          className="w-full flex items-center justify-between p-4 text-sm font-bold text-text-primary hover:bg-surface/50 transition-colors">
          <span className="flex items-center gap-2">
            <Settings2 size={14} className="text-accent-primary"/>
            4. Post-Producción & Técnico
          </span>
          {advancedOpen ? <ChevronUp size={14}/> : <ChevronDown size={14}/>}
        </button>
        {advancedOpen && (
          <div className="px-5 pb-5 space-y-4 border-t border-border-subtle pt-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label-xs">Codec de Video</label>
                <select value={codec} onChange={e=>setCodec(e.target.value)} className="input-field mt-1">
                  <option value="libx264">H.264 (libx264) — Máxima compat.</option>
                  <option value="libx265">H.265 (libx265) — Menor tamaño</option>
                  <option value="libvpx-vp9">VP9 — Web optimizado</option>
                </select>
              </div>
              <div className="space-y-1 pt-5">
                {[
                  ['Transiciones Fade', transitions, setTransitions],
                  ['Subtítulos Quemados', subtitles, setSubtitles],
                  ['Memoria Lore', useLore, setUseLore],
                ].map(([label, val, setter]: any) => (
                  <label key={label as string} className="flex items-center gap-2 cursor-pointer text-xs font-medium text-text-primary hover:text-accent-primary transition-colors">
                    <input type="checkbox" checked={val as boolean} onChange={e=>setter(e.target.checked)}
                      className="accent-accent-primary w-4 h-4"/>
                    {label as string}
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
"""

with open('F:/Gravity_AI_bridge/.agents/vs_part2.txt', 'w', encoding='utf-8') as f:
    f.write(part2)
print("Part2 written:", len(part2))
