import { useEffect, useState } from 'react';
import { Flame, Globe, Database, Code, ShieldCheck, AlertCircle, RefreshCw, Copy, Check, CheckCircle2 } from 'lucide-react';
import { showToast } from './Toast';

interface ScrapeResult {
  ok: boolean;
  url: string;
  title?: string;
  content?: string;
  source?: string;
  indexed_chunks?: number;
  memory_ingested?: boolean;
  error?: string;
}

export const Firecrawl = () => {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [url, setUrl] = useState('');
  const [crawling, setCrawling] = useState(false);
  const [autoIndex, setAutoIndex] = useState(true);
  const [result, setResult] = useState<ScrapeResult | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCrawl = async () => {
    if (!url.trim()) return;
    setCrawling(true);
    setResult(null);
    try {
      const res = await fetch('/v1/tools/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim(), ingest_memory: autoIndex })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.error || 'Servidor remoto rechazó la operación de scraping');
      }
      setResult(data);
      if (data.ok) {
        const tokenEstimate = Math.round((data.content?.length || 0) / 4);
        const memMsg = data.memory_ingested 
          ? `✓ ${data.indexed_chunks} fragmentos indexados en RAG.` 
          : 'Extracción lista (sin indexar).';
        showToast('success', `Extracción completada (${tokenEstimate} tokens). ${memMsg}`);
      } else {
        showToast('error', `Error en crawl: ${data.error || 'Sin contenido extraído'}`);
      }
    } catch (e: any) {
      showToast('error', `Fallo de conexión o extracción: ${e.message}`);
    } finally {
      setCrawling(false);
    }
  };

  const copyContent = () => {
    if (!result?.content) return;
    navigator.clipboard.writeText(result.content);
    setCopied(true);
    showToast('success', 'Contenido copiado al portapapeles');
    setTimeout(() => setCopied(false), 2000);
  };

  const fetchHealth = async () => {
    try {
      const res = await fetch('/v1/tools/firecrawl/health');
      if (res.ok) {
        const data = await res.json().catch(() => null);
        if (data) setHealth(data);
      }
    } catch (e) {} finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const iv = setInterval(fetchHealth, 10000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle shadow-[0_0_20px_rgba(249,115,22,0.1)]">
              <Flame className="text-orange-500" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Firecrawl Crawler</h1>
              <p className="text-text-muted mt-1 font-medium">Motor de web-scraping avanzado optimizado para LLMs.</p>
            </div>
          </div>
          <button 
            onClick={fetchHealth}
            className="p-2 rounded-xl bg-surface border border-border-subtle text-text-muted hover:text-text-primary transition-all"
          >
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
           
           <div className="lg:col-span-2 space-y-6">
              <div className="glass-panel p-8 rounded-2xl border border-border-subtle bg-gradient-to-br from-orange-500/5 to-transparent">
                 <div className="flex items-center justify-between mb-8">
                    <h3 className="text-sm font-black text-text-primary uppercase tracking-widest">Estado del Servicio</h3>
                    <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${health?.configured ? 'bg-status-success/10 text-status-success border-status-success/20' : 'bg-status-error/10 text-status-error border-status-error/20'}`}>
                       {health?.configured ? 'API ACTIVE' : 'FALLBACK MODE'}
                    </span>
                 </div>
                 <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Feature icon={<Globe size={18} />} label="JS Rendering" status={health?.configured ? 'Enabled' : 'Disabled'} />
                    <Feature icon={<Code size={18} />} label="Markdown Output" status="Enabled" />
                    <Feature icon={<Database size={18} />} label="Schema Extract" status={health?.configured ? 'Enabled' : 'Disabled'} />
                 </div>
                 <div className="mt-8 p-4 rounded-xl bg-black/40 border border-border-subtle font-mono text-[11px] text-orange-200">
                    {health?.message || 'Iniciando diagnóstico...'}
                 </div>
              </div>

              <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-4">
                 <h3 className="text-sm font-black text-text-primary uppercase tracking-widest">Test de Extracción</h3>
                 <div className="flex gap-2">
                    <input 
                      type="text" 
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://example.com"
                      className="flex-1 bg-surface border border-border-subtle rounded-xl px-4 py-3 text-sm text-text-primary outline-none focus:border-orange-500"
                    />
                    <button 
                      onClick={handleCrawl}
                      disabled={crawling || !url.trim()}
                      className="flex items-center gap-2 px-6 py-3 bg-orange-500 text-white font-black rounded-xl shadow-lg hover:scale-105 transition-all disabled:opacity-50"
                    >
                       {crawling ? <RefreshCw size={18} className="animate-spin" /> : <Globe size={18} />}
                       {crawling ? 'EXTRAYENDO...' : 'CRAWL'}
                    </button>
                 </div>
                 
                 <div className="flex items-center justify-between pt-1">
                    <label className="flex items-center gap-2 cursor-pointer text-xs text-text-secondary select-none">
                       <input 
                         type="checkbox" 
                         checked={autoIndex} 
                         onChange={(e) => setAutoIndex(e.target.checked)}
                         className="rounded border-border-subtle accent-orange-500 cursor-pointer"
                       />
                       <span>Indexar automáticamente en Memoria Semántica (RAG)</span>
                    </label>
                 </div>

                 {/* Visor interactivo de resultados */}
                 {result && (
                   <div className="mt-4 pt-4 border-t border-border-subtle space-y-3 animate-in fade-in duration-300">
                     <div className="flex items-center justify-between">
                       <div className="flex items-center gap-2">
                         <span className="text-xs font-bold text-text-primary truncate max-w-sm">
                           {result.title || result.url}
                         </span>
                         <span className="text-[10px] uppercase font-black px-2 py-0.5 rounded bg-surface border border-border-subtle text-orange-400">
                           {result.source || 'scraper'}
                         </span>
                         {result.memory_ingested && (
                           <span className="flex items-center gap-1 text-[10px] font-bold text-status-success bg-status-success/10 px-2 py-0.5 rounded border border-status-success/20">
                             <CheckCircle2 size={11} /> {result.indexed_chunks} chunks RAG
                           </span>
                         )}
                       </div>
                       <button
                         onClick={copyContent}
                         className="flex items-center gap-1 px-3 py-1 bg-surface border border-border-subtle hover:border-orange-500/50 rounded-lg text-xs font-medium text-text-secondary transition-all"
                       >
                         {copied ? <Check size={14} className="text-status-success" /> : <Copy size={14} />}
                         <span>{copied ? 'Copiado' : 'Copiar'}</span>
                       </button>
                     </div>
                     <div className="text-[11px] text-text-muted font-mono flex gap-4">
                       <span>Caracteres: {result.content?.length || 0}</span>
                       <span>Tokens aprox: {Math.round((result.content?.length || 0) / 4)}</span>
                     </div>
                     <pre className="p-4 rounded-xl bg-black/50 border border-border-subtle font-mono text-xs text-text-secondary max-h-72 overflow-y-auto whitespace-pre-wrap select-text leading-relaxed">
                       {result.content || (result.error ? `Error: ${result.error}` : 'Sin contenido de texto extraído.')}
                     </pre>
                   </div>
                 )}
              </div>
           </div>

           <div className="space-y-6">
              <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
                 <h3 className="text-sm font-black text-text-primary uppercase tracking-widest">Capabilities</h3>
                 <div className="space-y-4">
                    <CapRow label="PDF Parsing" ok={true} />
                    <CapRow label="Table Detection" ok={true} />
                    <CapRow label="Auth Bypass" ok={false} />
                    <CapRow label="RSS Tracking" ok={true} />
                 </div>
              </div>

              {!health?.configured && (
                <div className="p-6 rounded-2xl bg-orange-500/10 border border-orange-500/20 flex flex-col items-center text-center gap-3">
                   <AlertCircle className="text-orange-500" size={32} />
                   <div className="text-xs font-black text-orange-500 uppercase tracking-widest">API Key Requerida</div>
                   <p className="text-[10px] text-text-muted font-medium leading-relaxed">
                      Agregue su `firecrawl_api_key` en `config.yaml` para habilitar el motor de renderizado JS avanzado.
                   </p>
                </div>
              )}
           </div>

        </div>

      </div>
    </div>
  );
};

const Feature = ({ icon, label, status }: any) => (
  <div className="flex flex-col items-center gap-2">
     <div className="p-3 rounded-xl bg-surface border border-border-subtle text-orange-500">
        {icon}
     </div>
     <div className="text-[10px] font-bold text-text-muted uppercase">{label}</div>
     <div className="text-xs font-black text-text-primary">{status}</div>
  </div>
);

const CapRow = ({ label, ok }: any) => (
  <div className="flex justify-between items-center text-xs">
    <span className="text-text-muted font-bold">{label}</span>
    <div className={`flex items-center gap-1.5 font-black ${ok ? 'text-status-success' : 'text-text-muted opacity-50'}`}>
       {ok ? <ShieldCheck size={12} /> : <AlertCircle size={12} />}
       {ok ? 'YES' : 'NO'}
    </div>
  </div>
);
