import { useState } from 'react';
import { Palette, Image as ImageIcon, Sparkles, RefreshCw, Download, Sliders, Wand2 } from 'lucide-react';

const PRESETS: Record<string, string> = {
  'Cyberpunk':      ', cyberpunk aesthetic, neon lights, rain-soaked streets, ultra detailed, 8k',
  'Hyper-Real':     ', hyperrealistic photography, studio lighting, DSLR, 85mm lens, sharp focus',
  'Anime':          ', anime style, vibrant colors, Studio Ghibli inspired, detailed illustration',
  'Dark Fantasy':   ', dark fantasy art, dramatic lighting, ominous atmosphere, oil painting style',
  'Vaporwave':      ', vaporwave aesthetic, pastel colors, retro 80s, synthwave, glitch art',
  'Watercolor':     ', watercolor painting, soft edges, artistic, impressionist style',
};

const MODELS = ['flux', 'flux-realism', 'flux-anime', 'flux-3d', 'turbo'];

const ASPECT_OPTIONS = [
  { label: '1:1 Square',    width: 1024, height: 1024 },
  { label: '16:9 Wide',     width: 1280, height: 720  },
  { label: '9:16 Portrait', width: 720,  height: 1280 },
  { label: '4:3 Standard',  width: 1024, height: 768  },
  { label: '3:2 Photo',     width: 1024, height: 683  },
];

export const VisionStudio = () => {
  const [prompt, setPrompt]       = useState('');
  const [provider, setProvider]   = useState('Pollinations.ai');
  const [model, setModel]         = useState('flux');
  const [aspect, setAspect]       = useState(0);
  const [negPrompt, setNegPrompt] = useState('');
  const [loading, setLoading]     = useState(false);
  const [imageUrl, setImageUrl]   = useState<string | null>(null);
  const [error, setError]         = useState<string | null>(null);

  const applyPreset = (key: string) => {
    setPrompt(prev => {
      const suffix = PRESETS[key];
      if (prev.includes(suffix)) return prev;
      return prev.trimEnd() + suffix;
    });
  };

  const generate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setImageUrl(null);
    try {
      const { width, height } = ASPECT_OPTIONS[aspect];
      const res = await fetch('http://localhost:7860/v1/image/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim(), model, width, height, negative_prompt: negPrompt, enhance: true, provider }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al generar');
      setImageUrl(`http://localhost:7860${data.url}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!imageUrl) return;
    const a = document.createElement('a');
    a.href = imageUrl;
    a.download = `gravity_vision_${Date.now()}.png`;
    a.target = '_blank';
    a.rel = 'noopener';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-7xl mx-auto space-y-8">

        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-surface border border-border-subtle">
            <Palette className="text-accent-primary" size={28} />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Vision Studio</h1>
            <p className="text-text-muted mt-1 font-medium">Generación de imágenes con Flux, motor estilístico y control total de parámetros.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Control Panel */}
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-5">
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

              {/* Presets */}
              <div>
                <label className="text-[10px] font-black text-text-muted uppercase tracking-widest block mb-2">Presets Estilísticos</label>
                <div className="flex flex-wrap gap-2">
                  {Object.keys(PRESETS).map((key) => (
                    <button
                      key={key}
                      onClick={() => applyPreset(key)}
                      className="px-3 py-1 rounded-full text-[10px] font-bold bg-surface border border-border-subtle text-text-muted hover:border-accent-primary hover:text-accent-primary transition-all"
                    >
                      {key}
                    </button>
                  ))}
                </div>
              </div>

              {/* Provider */}
              <div>
                <label className="text-[10px] font-black text-text-muted uppercase tracking-widest block mb-2">Motor Generador</label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full bg-surface border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-accent-primary"
                >
                  <option value="Pollinations.ai">Pollinations.ai (Rápido / Cloud)</option>
                  <option value="Fooocus">Fooocus (Local / HQ)</option>
                </select>
              </div>

              {/* Model */}
              {provider === 'Pollinations.ai' && (
                <div>
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-widest block mb-2">Modelo Cloud</label>
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full bg-surface border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-accent-primary"
                  >
                    {MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
              )}

              {/* Aspect Ratio */}
              <div>
                <label className="text-[10px] font-black text-text-muted uppercase tracking-widest block mb-2">Aspecto</label>
                <select
                  value={aspect}
                  onChange={(e) => setAspect(+e.target.value)}
                  className="w-full bg-surface border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-accent-primary"
                >
                  {ASPECT_OPTIONS.map((opt, i) => (
                    <option key={i} value={i}>{opt.label} ({opt.width}×{opt.height})</option>
                  ))}
                </select>
              </div>

              {/* Negative Prompt */}
              <div>
                <label className="text-[10px] font-black text-text-muted uppercase tracking-widest block mb-2">Prompt Negativo</label>
                <input
                  type="text"
                  value={negPrompt}
                  onChange={(e) => setNegPrompt(e.target.value)}
                  placeholder="blurry, low quality, watermark..."
                  className="w-full bg-surface border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary outline-none focus:border-accent-primary"
                />
              </div>

              <button
                onClick={generate}
                disabled={loading || !prompt.trim()}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-accent-primary to-accent-secondary text-white font-black text-sm flex items-center justify-center gap-3 hover:scale-105 transition-all shadow-lg disabled:opacity-50"
              >
                {loading ? <RefreshCw className="animate-spin" size={18} /> : <Sparkles size={18} fill="currentColor" />}
                {loading ? 'GENERANDO...' : 'GENERAR IMAGEN'}
              </button>
            </div>
          </div>

          {/* Preview */}
          <div className="lg:col-span-2 space-y-6">
            {error && (
              <div className="glass-panel p-4 rounded-2xl border border-status-error/40 bg-status-error/10 text-status-error text-sm font-bold">
                ⚠ {error}
              </div>
            )}

            {imageUrl ? (
              <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden">
                <div className="p-4 border-b border-border-subtle bg-surface/30 flex justify-between items-center">
                  <span className="text-xs font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                    <Wand2 size={14} className="text-accent-primary" /> Vista Previa
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={handleDownload}
                      className="p-2 rounded-lg bg-surface border border-border-subtle text-text-muted hover:text-accent-primary transition-all"
                      title="Descargar imagen"
                    >
                      <Download size={16} />
                    </button>
                  </div>
                </div>
                <img src={imageUrl} alt="Generado por Gravity Vision" className="w-full object-contain max-h-[500px]" />
                <div className="p-3 bg-surface/20 text-[10px] font-mono text-text-muted flex gap-4">
                  <span>Motor: <span className="text-accent-primary font-bold">{model}</span></span>
                  <span>Aspecto: <span className="text-accent-secondary font-bold">{ASPECT_OPTIONS[aspect].label}</span></span>
                  <span>{ASPECT_OPTIONS[aspect].width}×{ASPECT_OPTIONS[aspect].height}px</span>
                </div>
              </div>
            ) : (
              <div className="glass-panel rounded-2xl border border-border-subtle p-24 flex flex-col items-center gap-4 opacity-30">
                <ImageIcon size={56} />
                <span className="text-xs font-bold uppercase tracking-widest text-text-muted">La imagen generada aparecerá aquí</span>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};
