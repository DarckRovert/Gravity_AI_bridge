import { useEffect, useState } from 'react';
import { BookOpen, Search, FileText, Database, Upload, RefreshCw, CheckCircle2 } from 'lucide-react';
import { showToast } from './Toast';

export const RagIndex = () => {
  const [status, setStatus] = useState<any>(null);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/v1/rag/status');
      if (res.ok) {
        const data = await res.json().catch(() => null);
        if (data) setStatus(data);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`/v1/rag/search?query=${encodeURIComponent(query)}`);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || 'El backend RAG rechazó la consulta');
      }
      const data = await res.json().catch(() => null);
      if (data) {
        setResults(data.results || []);
      } else {
        throw new Error('Respuesta corrupta de la base vectorial');
      }
    } catch (e: any) {
      showToast('error', `Fallo de RAG: ${e.message}`);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle">
              <BookOpen className="text-accent-secondary" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">RAG Index</h1>
              <p className="text-text-muted mt-1 font-medium">Memoria de largo plazo mediante vectorización de documentos (Retrieval Augmented Generation).</p>
            </div>
          </div>
          <div className="flex gap-3">
            <label className="flex items-center gap-2 px-4 py-2 bg-accent-secondary text-white rounded-xl text-sm font-bold hover:scale-105 transition-all cursor-pointer shadow-lg">
              <Upload size={16} /> Indexar PDF/TXT
              <input
                type="file"
                accept=".pdf,.txt,.md,.docx"
                multiple
                className="hidden"
                onChange={async (e) => {
                  const files = Array.from(e.target.files || []);
                  if (!files.length) return;
                  const fd = new FormData();
                  files.forEach(f => fd.append('files', f));
                  try {
                    const res = await fetch('/v1/rag/ingest', { method: 'POST', body: fd });
                    const data = await res.json().catch(() => ({}));
                    if (!res.ok) {
                      throw new Error(data.error || 'Fallo en vectorización del documento');
                    }
                    if (data.ok || data.indexed) { 
                      showToast('success', `✅ ${data.indexed || files.length} documento(s) indexados correctamente.`); 
                      fetchStatus(); 
                    } else {
                      throw new Error(data.error || 'Respuesta inválida del servidor RAG');
                    }
                  } catch (err: any) { 
                    showToast('error', `❌ Error de Indexación: ${err.message}`); 
                  }
                  e.target.value = '';
                }}
              />
            </label>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          <div className="lg:col-span-1 space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
              <h3 className="text-xs font-bold text-text-primary uppercase tracking-widest flex items-center gap-2">
                <Database size={16} className="text-accent-secondary" /> Estadísticas del Índice
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-text-muted">Documentos</span>
                  <span className="font-bold text-text-primary">{status?.doc_count || 0}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-text-muted">Chuncks (Vectores)</span>
                  <span className="font-bold text-accent-secondary">{status?.chunk_count || 0}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-text-muted">Tamaño Total</span>
                  <span className="font-bold text-text-primary">{status?.size_mb || 0} MB</span>
                </div>
                <div className="pt-4 border-t border-border-subtle">
                  <div className={`flex items-center gap-2 text-xs font-bold ${status?.online ? 'text-status-success' : 'text-text-muted'}`}>
                    <CheckCircle2 size={14} /> Sistema {status?.online ? 'Online' : 'Vacío'}
                  </div>
                </div>
              </div>
            </div>

            <button 
              onClick={() => showToast('info', 'Edita el archivo config.yaml o añade PDFs a la carpeta local _rag_sources/ para actualizar el índice.')}
              className="w-full py-4 rounded-2xl bg-card border border-border-subtle text-text-muted hover:text-text-primary hover:border-accent-secondary transition-all flex items-center justify-center gap-2 text-sm font-bold group"
            >
              <RefreshCw size={16} className="group-hover:rotate-180 transition-transform duration-500" /> Re-indexar Base de Datos
            </button>
          </div>

          <div className="lg:col-span-3 space-y-6">
            
            {/* Search Bar */}
            <div className="glass-panel p-2 rounded-2xl border border-border-subtle flex items-center gap-2 bg-surface/50 focus-within:border-accent-secondary transition-all shadow-xl">
              <div className="pl-4 text-text-muted"><Search size={20} /></div>
              <input 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Consultar en la memoria semántica..." 
                className="flex-1 bg-transparent border-none text-text-primary p-4 outline-none font-medium"
              />
              <button 
                onClick={handleSearch}
                disabled={searching || !query.trim()}
                className="px-6 py-3 bg-accent-secondary text-white rounded-xl font-bold shadow-lg hover:scale-105 transition-all disabled:opacity-50"
              >
                {searching ? <RefreshCw className="animate-spin" size={20} /> : 'BUSCAR'}
              </button>
            </div>

            {/* Results Area */}
            <div className="glass-panel rounded-2xl border border-border-subtle overflow-hidden min-h-[400px]">
              <div className="p-6 border-b border-border-subtle bg-surface/30">
                <h3 className="font-bold text-text-primary flex items-center gap-2"><FileText size={18} className="text-accent-primary" /> Resultados Semánticos</h3>
              </div>
              
              <div className="p-6 space-y-6">
                {results.length > 0 ? results.map((res, i) => (
                  <div key={i} className="p-5 rounded-2xl bg-card border border-border-subtle space-y-3 animate-in fade-in slide-in-from-left-4 duration-500" style={{ animationDelay: `${i * 100}ms` }}>
                    <div className="flex justify-between items-start">
                      <div className="text-xs font-bold text-accent-secondary uppercase tracking-widest">{res.source || 'Documento'}</div>
                      <div className="text-[10px] bg-accent-secondary/10 text-accent-secondary px-2 py-0.5 rounded-full border border-accent-secondary/20 font-bold">Similitud: {Math.round(res.score * 100)}%</div>
                    </div>
                    <p className="text-sm text-text-primary leading-relaxed">{res.content}</p>
                    <div className="flex gap-2 pt-2">
                      <button onClick={() => showToast('info', res.content)} className="text-[10px] font-bold text-text-muted hover:text-accent-secondary transition-colors uppercase tracking-widest flex items-center gap-1"><Search size={10} /> Ver contexto completo</button>
                    </div>
                  </div>
                )) : (
                  <div className="flex flex-col items-center justify-center py-24 text-text-muted gap-4 opacity-30">
                    <Search size={48} />
                    <p className="text-sm font-bold uppercase tracking-widest">Ingresa una consulta para buscar en el RAG</p>
                  </div>
                )}
              </div>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
};
