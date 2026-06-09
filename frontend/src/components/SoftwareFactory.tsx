import React, { useState, useEffect } from 'react';
import { Code2, Play, Download, AlertCircle, FileArchive, Package } from 'lucide-react';

interface Deliverable {
  filename: string;
  size: string;
  created_at: string;
}

export const SoftwareFactory: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [deliverables, setDeliverables] = useState<Deliverable[]>([]);
  const [listLoading, setListLoading] = useState(false);

  const fetchDeliverables = async () => {
    try {
      setListLoading(true);
      const res = await fetch('/v1/factory/list');
      if (res.ok) {
        const data = await res.json();
        setDeliverables(data.deliverables || []);
      }
    } catch (e) {
      console.error('Error fetching deliverables', e);
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    fetchDeliverables();
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const res = await fetch('/v1/factory/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al generar código');
      
      setSuccess(`¡Entregable generado con éxito! Nombre: ${data.filename}`);
      setPrompt('');
      fetchDeliverables();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-bg/50 overflow-hidden">
      {/* Header */}
      <div className="flex-none p-6 pb-2 border-b border-border-subtle bg-surface/50 backdrop-blur-md z-10 flex justify-between items-end">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 bg-accent-primary/10 rounded-lg text-accent-primary">
              <Code2 size={24} />
            </div>
            <h1 className="text-2xl font-bold text-text-primary">Dev Studio / Fábrica</h1>
          </div>
          <p className="text-text-muted text-sm ml-12">Programación Autónoma de Entregables (ZIP)</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 scrollbar-hide grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Panel Izquierdo: Generador */}
        <div className="flex flex-col gap-4">
          <div className="glass-card bg-card/80 border border-border-subtle rounded-xl p-6 shadow-lg">
            <h2 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
              <Play size={18} className="text-accent-primary" /> Nuevo Requerimiento
            </h2>
            <p className="text-sm text-text-muted mb-4">
              Pega aquí lo que pidió el cliente. La IA programará los scripts, creará los archivos necesarios (ej. main.py, package.json, README) y los empaquetará en un archivo .zip para ti.
            </p>
            
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full h-64 p-4 bg-bg border border-border-subtle rounded-lg text-sm text-text-primary focus:outline-none focus:border-accent-primary transition-colors mb-4 resize-none"
              placeholder="Ej: Necesito un script en Python que descargue el HTML de amazon.com usando Playwright y lo guarde en un archivo..."
              disabled={loading}
            />

            {error && (
              <div className="mb-4 p-3 bg-status-error/10 border border-status-error/30 rounded-lg flex items-center gap-3 text-status-error text-sm">
                <AlertCircle size={16} />
                <p className="font-medium">{error}</p>
              </div>
            )}

            {success && (
              <div className="mb-4 p-3 bg-status-success/10 border border-status-success/30 rounded-lg flex items-center gap-3 text-status-success text-sm">
                <Package size={16} />
                <p className="font-medium">{success}</p>
              </div>
            )}

            <button
              onClick={handleGenerate}
              disabled={loading || !prompt.trim()}
              className={`w-full flex items-center justify-center gap-2 py-3 rounded-lg font-bold transition-all ${
                loading || !prompt.trim()
                  ? 'bg-surface text-text-muted cursor-not-allowed'
                  : 'bg-accent-primary text-black hover:bg-accent-primary/90 hover:shadow-lg hover:shadow-accent-primary/20'
              }`}
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-black/20 border-t-black rounded-full animate-spin"></div>
                  Procesando e Ingenierizando...
                </>
              ) : (
                <>
                  <Code2 size={18} /> Construir Entregable (ZIP)
                </>
              )}
            </button>
          </div>
        </div>

        {/* Panel Derecho: Entregables */}
        <div className="flex flex-col gap-4">
          <div className="glass-card bg-card/80 border border-border-subtle rounded-xl p-6 shadow-lg min-h-[400px]">
            <h2 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
              <FileArchive size={18} className="text-accent-secondary" /> Historial de Entregables
            </h2>
            
            {listLoading ? (
              <div className="text-sm text-text-muted">Cargando entregables...</div>
            ) : deliverables.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center text-text-muted">
                <Package size={48} className="mb-4 opacity-20" />
                <p className="text-sm">Aún no hay entregables generados.</p>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {deliverables.map((d, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-bg border border-border-subtle rounded-lg hover:border-accent-primary/50 transition-colors">
                    <div>
                      <div className="font-medium text-text-primary">{d.filename}</div>
                      <div className="text-xs text-text-muted">{d.created_at} • {d.size}</div>
                    </div>
                    <a
                      href={`/v1/factory/download/${d.filename}`}
                      download
                      className="p-2 hover:bg-accent-primary/10 text-accent-primary rounded-lg transition-colors"
                      title="Descargar ZIP"
                    >
                      <Download size={18} />
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
