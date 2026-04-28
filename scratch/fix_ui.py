import re

PATH = r'F:\Gravity_AI_bridge\frontend\src\components\VideoStudio.tsx'
with open(PATH, 'r', encoding='utf-8', errors='replace') as f:
    src = f.read()

# ── 1. Opciones BGM ──────────────────────────────────────────────────────────
# Buscar el select de bgm_type y reemplazar su contenido completo
BGM_PATTERN = re.compile(
    r'(<select[^>]*bgm_type[^>]*>)(.*?)(</select>)',
    re.DOTALL
)
BGM_OPTIONS = """
                             <option value="ninguna">Sin Música</option>
                             <option value="epico">Cine Épico</option>
                             <option value="heroico">Heroico / Épico Orquestal</option>
                             <option value="documental">Documental / Ambiental</option>
                             <option value="ambient">Ambiental Suave</option>
                             <option value="tension">Tensión / Thriller</option>
                             <option value="synthwave">Retro / Synth 80s</option>
                             <option value="lofi_beats">Lo-Fi Beats</option>
                             <option value="jazz">Jazz Lounge</option>
                             <option value="corporativo">Corporativo / Limpio</option>
                           """

# Buscar valor del select bgm con onChange
bgm_match = re.search(r'value=\{bgmType\}[^>]*onChange[^>]*>[^<]*(<option[^<]*<\/option>[^<]*)+<\/select>', src, re.DOTALL)
if not bgm_match:
    # Buscar alternativo
    bgm_match = re.search(r'(value=\{bgmType\}[^\n]*\n[^<]*)((?:<option[^<]*<\/option>\s*)+)(\s*<\/select>)', src, re.DOTALL)

if bgm_match:
    old = bgm_match.group(0)
    # Preservar el select tag, reemplazar solo las options
    new = re.sub(r'(?:<option[^<]*<\/option>\s*)+', BGM_OPTIONS + '\n', old, count=1)
    src = src.replace(old, new, 1)
    print("OK: opciones BGM reemplazadas via regex")
else:
    # Buscar por texto literal de alguna opción existente
    old_opts = '<option value="ninguna">Sin Música</option>'
    idx = src.find(old_opts)
    if idx != -1:
        # Encontrar el bloque de options
        end_tag = src.find('</select>', idx)
        block = src[idx:end_tag]
        src = src[:idx] + BGM_OPTIONS + src[end_tag:]
        print("OK: opciones BGM reemplazadas por bloque (idx)")
    else:
        print("WARN: no encontré el select de BGM")

# ── 2. Botón Preview Voz ─────────────────────────────────────────────────────
# Buscar después del select de voiceId
VOICE_PREVIEW_BTN = """
                           <button
                             id="btn-preview-voice"
                             onClick={async () => {
                               if (!voiceId) return;
                               try {
                                 const r = await fetch('http://localhost:7860/v1/video/preview_voice', {
                                   method: 'POST',
                                   headers: { 'Content-Type': 'application/json' },
                                   body: JSON.stringify({ voice_id: voiceId, text: 'Hola, esta es una prueba de la voz seleccionada en Gravity Studio. Sistema operativo al máximo nivel.' })
                                 });
                                 if (r.ok) {
                                   const blob = await r.blob();
                                   const url = URL.createObjectURL(blob);
                                   const audio = new Audio(url);
                                   audio.play();
                                 }
                               } catch (e) { console.error('preview_voice:', e); }
                             }}
                             disabled={!voiceId}
                             className="mt-1.5 w-full px-3 py-1.5 bg-surface/50 border border-border-subtle rounded-md text-[10px] font-bold uppercase tracking-wider text-text-muted hover:text-accent-primary hover:border-accent-primary/60 transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
                           >
                             ▶ Preview de Voz
                           </button>"""

# Buscar el select de voices y añadir el botón después de su </select>
voice_sel_pattern = re.compile(
    r'(value=\{voiceId\}[^>]*onChange[^>]*>.*?</select>)',
    re.DOTALL
)
voice_match = voice_sel_pattern.search(src)
if voice_match:
    old = voice_match.group(0)
    if 'Preview de Voz' not in old:
        src = src.replace(old, old + VOICE_PREVIEW_BTN, 1)
        print("OK: botón Preview Voz añadido")
    else:
        print("INFO: botón Preview Voz ya existe")
else:
    print("WARN: no encontré select de voiceId")

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print("DONE: VideoStudio.tsx actualizado")
