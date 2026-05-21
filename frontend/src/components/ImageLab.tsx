import { useEffect, useState } from 'react';
import { Palette, Image as ImageIcon, Sparkles, RefreshCw, Download, Sliders } from 'lucide-react';

  const ASPECT_OPTIONS = [
    { label: '1:1 Square',    width: 1024, height: 1024 },
    { label: '16:9 Wide',     width: 1344, height: 768  },
    { label: '9:16 Portrait', width: 768,  height: 1344 },
    { label: '4:3 Standard',  width: 1152, height: 896  },
    { label: '3:2 Photo',     width: 1216, height: 832  },
  ];

export const ImageLab = () => {

  const [images, setImages] = useState<any[]>([]);
  const [prompt, setPrompt] = useState('');
  const [aspect, setAspect] = useState(0);
  const [provider, setProvider] = useState('Pollinations.ai');
  const [model, setModel] = useState('flux');
  const [seed, setSeed] = useState('');
  const [enhance, setEnhance] = useState(true);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      const res = await fetch('/v1/image/lab/history');
      if (res.ok) {
        const data = await res.json();
        setImages(data.images || []);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchHistory();
    const iv = setInterval(fetchHistory, 10000);
    return () => clearInterval(iv);
  }, []);

  const generate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    try {
      const { width, height } = ASPECT_OPTIONS[aspect];
      const res = await fetch('/v1/image/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, width, height, model, enhance: enhance, provider, seed: seed.trim() || undefined })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al generar');
      await fetchHistory();
      if (data.url) setSelected(`http://localhost:7860${data.url}`);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const MODELS = ['flux', 'flux-realism', 'flux-anime', 'flux-3d', 'turbo'];

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-7xl mx-auto space-y-8">
        
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-surface border border-border-subtle">
            <Palette className="text-accent-primary" size={28} />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Image Lab</h1>
            <p className="text-text-muted mt-1 font-medium">Generación de imágenes con múltiples motores: Flux, Turbo y estilos especializados.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Generator Panel */}
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
              <h3 className="text-xs font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                <Sliders size={16} className="text-accent-primary" /> Parámetros
              </h3>
              
              <textarea
                rows={4}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe la imagen en detalle: estilo, sujeto, iluminación, composición..."
                className="w-full bg-surface border border-border-subtle rounded-xl p-4 text-sm text-text-primary outline-none focus:border-accent-primary resize-none"
              />

              <div className="space-y-4">
                <div>
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-widest block mb-2">Motor</label>
                  <select 
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="w-full bg-surface border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary outline-none mb-4"
                  >
                    <option value="Pollinations.ai">Pollinations.ai (Cloud)</option>
                    <option value="Fooocus">Fooocus (Local)</option>
                  </select>
                </div>
                {provider === 'Pollinations.ai' && (
                  <div>
                    <label className="text-[10px] font-black text-text-muted uppercase tracking-widest block mb-2">Modelo</label>
                    <select 
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      className="w-full bg-surface border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary outline-none"
                    >
                      {MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] font-black text-text-muted uppercase tracking-widest block mb-2">Relación de Aspecto</label>
                    <select value={aspect} onChange={(e) => setAspect(+e.target.value)} className="w-full bg-surface border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary outline-none">
                      {ASPECT_OPTIONS.map((opt, i) => (
                        <option key={i} value={i}>{opt.label} ({opt.width}x{opt.height})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-2">Seed (Opcional)</label>
                    <input 
                      type="text" 
                      value={seed}
                      onChange={(e) => setSeed(e.target.value.replace(/\D/g, ''))}
                      placeholder="Auto"
                      className="w-full bg-surface border border-border-subtle rounded-xl p-3 text-sm text-text-primary outline-none focus:border-accent-primary transition-all"
                    />
                  </div>
                </div>

                <div className="flex gap-4 p-4 rounded-xl bg-surface border border-border-subtle">
                  <label className="flex items-center gap-2 cursor-pointer text-sm font-bold text-text-primary">
                    <input type="checkbox" checked={enhance} onChange={(e) => setEnhance(e.target.checked)} className="accent-accent-primary w-4 h-4" />
                    Auto-Enhance (Mejora LLM)
                  </label>
                </div>

              </div>

              <button
                onClick={generate}
                disabled={loading || !prompt.trim()}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-accent-primary to-accent-secondary text-white font-black text-sm flex items-center justify-center gap-3 hover:scale-105 transition-all shadow-lg disabled:opacity-50"
              >
                {loading ? <RefreshCw className="animate-spin" size={18} /> : <Sparkles size={18} fill="currentColor" />}
                {loading ? 'GENERANDO...' : 'GENERAR CON FLUX'}
              </button>
            </div>
          </div>

          {/* Preview + Gallery */}
          <div className="lg:col-span-2 space-y-6">
            {selected ? (
              <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
                <div className="p-4 border-b border-border-subtle bg-surface/30 flex justify-between items-center">
                  <span className="text-xs font-black text-text-primary uppercase tracking-widest">Vista Previa</span>
                  <a href={selected} download className="p-2 rounded-lg bg-surface border border-border-subtle text-text-muted hover:text-accent-primary transition-all">
                    <Download size={16} />
                  </a>
                </div>
                <img src={selected} alt="Generado" className="w-full object-contain max-h-80" />
              </div>
            ) : (
              <div className="glass-panel rounded-2xl border border-border-subtle p-20 flex flex-col items-center gap-4 opacity-30">
                <ImageIcon size={48} />
                <span className="text-xs font-bold uppercase tracking-widest text-text-muted">La imagen generada aparecerá aquí</span>
              </div>
            )}

            <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
              <div className="p-4 border-b border-border-subtle bg-surface/30 flex justify-between items-center">
                <span className="text-xs font-black text-text-primary uppercase tracking-widest">Historial</span>
                <button onClick={fetchHistory} className="p-1.5 rounded-lg hover:bg-card transition-all text-text-muted">
                  <RefreshCw size={14} />
                </button>
              </div>
              <div className="grid grid-cols-4 gap-2 p-4 max-h-64 overflow-y-auto scrollbar-hide">
                {images.map((img, i) => (
                  <div key={i} className="relative group cursor-pointer" onClick={() => setSelected(`http://localhost:7860${img.url}`)}>
                    <img
                      src={`http://localhost:7860${img.url}`}
                      alt={img.name}
                      className="w-full h-20 object-cover rounded-lg border border-border-subtle group-hover:border-accent-primary transition-all"
                    />
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-all rounded-lg flex items-center justify-center">
                      <span className="text-[8px] font-bold text-white text-center px-1">{img.name}</span>
                    </div>
                  </div>
                ))}
                {images.length === 0 && (
                  <div className="col-span-4 py-8 text-center text-[10px] font-bold text-text-muted uppercase opacity-30">Sin historial</div>
                )}
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
