import React, { useState } from 'react';
import { Box, Search, Download, Star, Zap, Cpu, Server, CheckCircle2 } from 'lucide-react';

const DUMMY_MODELS = [
  { id: 'llama-3-8b', name: 'Llama 3 (8B)', provider: 'Meta', size: '4.7 GB', type: 'LLM', downloads: '1.2M', status: 'installed' },
  { id: 'mistral-7b', name: 'Mistral 7B Instruct', provider: 'Mistral AI', size: '4.1 GB', type: 'LLM', downloads: '890K', status: 'available' },
  { id: 'phi-3-mini', name: 'Phi-3 Mini', provider: 'Microsoft', size: '2.3 GB', type: 'LLM', downloads: '500K', status: 'available' },
  { id: 'stable-diffusion-xl', name: 'SDXL 1.0', provider: 'Stability AI', size: '6.5 GB', type: 'Vision', downloads: '2.1M', status: 'downloading' },
  { id: 'nomic-embed-text', name: 'Nomic Embed', provider: 'Nomic', size: '1.2 GB', type: 'Embedding', downloads: '340K', status: 'installed' },
];

export const ModelHub: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('All');

  const filteredModels = DUMMY_MODELS.filter(m => 
    (filter === 'All' || m.type === filter) &&
    m.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <Box className="text-accent-primary" size={32} />
            Model Hub
          </h1>
          <p className="text-text-muted mt-1">Descubre, descarga y gestiona modelos de Inteligencia Artificial locales.</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-card border border-border-subtle rounded-xl hover:border-accent-primary transition-colors text-sm font-medium">
            <Server size={16} /> Configurar Almacenamiento
          </button>
        </div>
      </div>

      <div className="flex gap-4 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={18} />
          <input 
            type="text" 
            placeholder="Buscar modelos por nombre, proveedor o tipo..." 
            className="w-full bg-card border border-border-subtle rounded-xl pl-10 pr-4 py-3 text-white focus:outline-none focus:border-accent-primary transition-colors"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select 
          className="bg-card border border-border-subtle rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent-primary"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="All">Todos los Tipos</option>
          <option value="LLM">LLM (Texto)</option>
          <option value="Vision">Visión / Imagen</option>
          <option value="Embedding">Embeddings</option>
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredModels.map(model => (
          <div key={model.id} className="glass-panel p-5 rounded-2xl flex flex-col hover:border-accent-primary/50 transition-colors group">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-bold text-white group-hover:text-accent-primary transition-colors">{model.name}</h3>
                <p className="text-sm text-text-muted">{model.provider}</p>
              </div>
              <div className="px-2 py-1 bg-surface rounded-md text-xs font-semibold text-text-muted border border-border-subtle">
                {model.type}
              </div>
            </div>
            
            <div className="flex gap-4 text-sm mb-6 text-text-muted">
              <span className="flex items-center gap-1"><Cpu size={14} /> {model.size}</span>
              <span className="flex items-center gap-1"><Download size={14} /> {model.downloads}</span>
              <span className="flex items-center gap-1 text-status-warning"><Star size={14} /> Destacado</span>
            </div>

            <div className="mt-auto">
              {model.status === 'installed' && (
                <button className="w-full py-2 bg-status-success/10 text-status-success rounded-xl font-bold flex justify-center items-center gap-2 border border-status-success/20">
                  <CheckCircle2 size={18} /> Instalado
                </button>
              )}
              {model.status === 'available' && (
                <button className="w-full py-2 bg-accent-primary hover:bg-accent-secondary text-white rounded-xl font-bold flex justify-center items-center gap-2 transition-colors">
                  <Download size={18} /> Descargar
                </button>
              )}
              {model.status === 'downloading' && (
                <div className="w-full bg-card rounded-xl p-2 border border-accent-primary/30 relative overflow-hidden">
                  <div className="absolute inset-0 bg-accent-primary/20 w-3/4 animate-pulse"></div>
                  <div className="relative text-center text-accent-primary font-bold text-sm flex justify-center items-center gap-2">
                    <Zap size={14} className="animate-bounce" /> Descargando... 75%
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
