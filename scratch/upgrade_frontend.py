import re

PATH = r'F:\Gravity_AI_bridge\frontend\src\components\VideoStudio.tsx'
with open(PATH, 'r', encoding='utf-8', errors='replace') as f:
    src = f.read()

# 1. Añadir nuevos estados después de const [codec, setCodec]
OLD_STATES = "  const [codec, setCodec] = useState('libx264');"
NEW_STATES = """  const [codec, setCodec] = useState('libx264');
  const [kenBurns, setKenBurns] = useState(true);
  const [introCard, setIntroCard] = useState(false);
  const [colorGrade, setColorGrade] = useState('auto');"""
src = src.replace(OLD_STATES, NEW_STATES, 1)

# 2. Añadir nuevos campos al JSON de createVideo
OLD_JSON = "          codec\n        })"
NEW_JSON = """          codec,
          ken_burns: kenBurns,
          intro_card: introCard,
          color_grade: colorGrade,
        })"""
src = src.replace(OLD_JSON, NEW_JSON, 1)

# 3. Añadir más opciones BGM
OLD_BGM_OPTS = """                             <option value="ninguna">Sin Música</option>
                             <option value="epico">Cine Épico</option>
                             <option value="documental">Documental</option>
                             <option value="synthwave">Retro / Synth</option>
                             <option value="jazz">Jazz Lounge</option>"""
NEW_BGM_OPTS = """                             <option value="ninguna">Sin Música</option>
                             <option value="epico">Cine Épico</option>
                             <option value="heroico">Heroico / Épico Orquestal</option>
                             <option value="documental">Documental / Ambient</option>
                             <option value="ambient">Ambiental Suave</option>
                             <option value="tension">Tensión / Thriller</option>
                             <option value="synthwave">Retro / Synth 80s</option>
                             <option value="lofi_beats">Lo-Fi Beats</option>
                             <option value="jazz">Jazz Lounge</option>
                             <option value="corporativo">Corporativo / Limpio</option>"""
src = src.replace(OLD_BGM_OPTS, NEW_BGM_OPTS, 1)

# 4. Insertar controles avanzados Ken Burns, Color Grade, Intro Card
# después del bloque de "Lore Persistir" (último checkbox del Render Pipeline)
OLD_LORE_END = """                      </div>

                    </div>

                  </div>
                </div>
              </div>"""

NEW_LORE_END = """                      </div>

                      {/* Efectos Cinematográficos */}
                      <div className="pt-2 space-y-2">
                        <h4 className="text-[9px] font-bold text-text-muted uppercase tracking-widest">Efectos Cinematográficos</h4>
                        <div className="grid grid-cols-1 gap-2">
                          <label className="flex items-center gap-2 cursor-pointer text-xs font-medium bg-surface/50 border border-border-subtle p-2 rounded-lg hover:border-accent-primary/50 transition-colors">
                            <input type="checkbox" checked={kenBurns} onChange={(e) => setKenBurns(e.target.checked)} className="accent-accent-primary w-4 h-4" />
                            <div className="flex-1">
                              <span className="block font-bold">Ken Burns (Zoom + Pan)</span>
                              <span className="block text-[9px] text-text-muted">Animación de cámara sobre imágenes estáticas</span>
                            </div>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer text-xs font-medium bg-surface/50 border border-border-subtle p-2 rounded-lg hover:border-accent-primary/50 transition-colors">
                            <input type="checkbox" checked={introCard} onChange={(e) => setIntroCard(e.target.checked)} className="accent-accent-primary w-4 h-4" />
                            <div className="flex-1">
                              <span className="block font-bold">Tarjeta de Intro</span>
                              <span className="block text-[9px] text-text-muted">Slide inicial con título animado (3.5s)</span>
                            </div>
                          </label>
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-[10px] text-text-muted uppercase font-bold">Color Grade</label>
                          <select value={colorGrade} onChange={(e) => setColorGrade(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-md p-2 text-xs outline-none">
                            <option value="auto">Auto (por estilo cinemático)</option>
                            <option value="none">Sin grading</option>
                          </select>
                        </div>
                      </div>

                    </div>

                  </div>
                </div>
              </div>"""

src = src.replace(OLD_LORE_END, NEW_LORE_END, 1)

# 5. Añadir botón de preview de voz junto al selector
OLD_VOICE_SEL = """                           <select value={voiceId} onChange={(e) => setVoiceId(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-md p-2 text-xs outline-none">
                             <option value="">Auto (Sistema)</option>
                             {voices.map((v) => (
                               <option key={v.id} value={v.id}>{v.name} ({v.lang})</option>
                             ))}
                           </select>"""
NEW_VOICE_SEL = """                           <select value={voiceId} onChange={(e) => setVoiceId(e.target.value)} className="w-full bg-surface border border-border-subtle rounded-md p-2 text-xs outline-none">
                             <option value="">Auto (Sistema)</option>
                             {voices.map((v) => (
                               <option key={v.id} value={v.id}>{v.name} ({v.lang})</option>
                             ))}
                           </select>
                           <button
                             onClick={async () => {
                               if (!voiceId) return;
                               try {
                                 const r = await fetch('http://localhost:7860/v1/video/preview_voice', {
                                   method: 'POST', headers: {'Content-Type':'application/json'},
                                   body: JSON.stringify({ voice_id: voiceId, text: 'Esta es una prueba de la voz seleccionada para Gravity Studio.' })
                                 });
                                 if (r.ok) {
                                   const blob = await r.blob();
                                   const url = URL.createObjectURL(blob);
                                   new Audio(url).play();
                                 }
                               } catch(e) {}
                             }}
                             disabled={!voiceId}
                             className="mt-1 w-full px-2 py-1.5 bg-surface border border-border-subtle rounded-md text-[10px] font-bold text-text-muted hover:text-accent-primary hover:border-accent-primary transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                             title="Escuchar preview de la voz"
                           >
                             ▶ Preview Voz
                           </button>"""
src = src.replace(OLD_VOICE_SEL, NEW_VOICE_SEL, 1)

# 6. En Master Archive, mostrar thumbnail si existe
OLD_THUMB = """                        className={`aspect-video bg-black relative flex items-center justify-center cursor-pointer transition-all ${!isReady ? 'opacity-50 pointer-events-none' : 'group-hover:bg-zinc-900'}`}"""
NEW_THUMB = """                        className={`aspect-video bg-black relative flex items-center justify-center cursor-pointer transition-all overflow-hidden ${!isReady ? 'opacity-50 pointer-events-none' : 'group-hover:bg-zinc-900'}`}"""
src = src.replace(OLD_THUMB, NEW_THUMB, 1)

OLD_PLAY_ICON = """                            <PlayCircle size={48} className="text-white/50 group-hover:text-accent-primary group-hover:scale-110 transition-all duration-300 z-20" strokeWidth={1} />"""
NEW_PLAY_ICON = """                            {job.thumbnail_path && (
                              <img src={`http://localhost:7860/v1/video/thumbnail?job_id=${job.id}`} alt="thumb" className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity" />
                            )}
                            <PlayCircle size={48} className="text-white/50 group-hover:text-accent-primary group-hover:scale-110 transition-all duration-300 z-20 relative" strokeWidth={1} />"""
src = src.replace(OLD_PLAY_ICON, NEW_PLAY_ICON, 1)

# 7. Añadir ken_burns y intro_card en los presets
OLD_PRESET_DOC = """      setDurationMode('auto');
      setResolution('1216x832');
      setTransitions(true);
    } else if (preset === 'epic_trailer') {"""
NEW_PRESET_DOC = """      setDurationMode('auto');
      setResolution('1216x832');
      setTransitions(true);
      setKenBurns(true);
      setIntroCard(false);
      setColorGrade('auto');
    } else if (preset === 'epic_trailer') {"""
src = src.replace(OLD_PRESET_DOC, NEW_PRESET_DOC, 1)

OLD_PRESET_EPIC = """      setDurationMode('manual');
      setSceneDuration(4);
      setResolution('1216x832');
      setTransitions(false);
    } else if (preset === 'tiktok_short') {"""
NEW_PRESET_EPIC = """      setDurationMode('manual');
      setSceneDuration(4);
      setResolution('1216x832');
      setTransitions(false);
      setKenBurns(false);
      setIntroCard(true);
      setColorGrade('auto');
    } else if (preset === 'tiktok_short') {"""
src = src.replace(OLD_PRESET_EPIC, NEW_PRESET_EPIC, 1)

OLD_PRESET_TIKTOK = """      setDurationMode('manual');
      setSceneDuration(3);
      setResolution('832x1216');
      setTransitions(true);
    }"""
NEW_PRESET_TIKTOK = """      setDurationMode('manual');
      setSceneDuration(3);
      setResolution('832x1216');
      setTransitions(true);
      setKenBurns(true);
      setIntroCard(false);
      setColorGrade('auto');
    }"""
src = src.replace(OLD_PRESET_TIKTOK, NEW_PRESET_TIKTOK, 1)

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print("DONE: VideoStudio.tsx actualizado")
