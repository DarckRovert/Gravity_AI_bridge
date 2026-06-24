import React, { useState } from 'react';
import { Download, Search, Trash2, Cpu, HardDrive, ShieldCheck, Box, RefreshCw } from 'lucide-react';
import { showToast } from './Toast';

interface ModelInfo {
  id: string;
  name: string;
  size: string;
  type: string;
  status: 'installed' | 'not_installed' | 'downloading';
  progress?: number;
}

const mockModels: ModelInfo[] = [
  { id: 'llama-3-8b', name: 'Llama 3 8B Instruct', size: '4.7 GB', type: 'LLM', status: 'installed' },
  { id: 'mistral-7b', name: 'Mistral 7B v0.3', size: '4.1 GB', type: 'LLM', status: 'not_installed' },
  { id: 'nomic-embed-text', name: 'Nomic Embed Text v1.5', size: '250 MB', type: 'Embedding', status: 'installed' },
  { id: 'llava-1.5', name: 'LLaVA 1.5 Vision', size: '4.5 GB', type: 'Vision', status: 'not_installed' },
  { id: 'deepseek-coder', name: 'DeepSeek Coder 6.7B', size: '3.9 GB', type: 'Coder', status: 'not_installed' }
];

export const ModelHub: React.FC = () => {
  const [models, setModels] = useState<ModelInfo[]>(mockModels);
  const [searchTerm, setSearchTerm] = useState('');

  const handleDownload = (id: string) => {
    setModels(models.map(m => m.id === id ? { ...m, status: 'downloading', progress: 0 } : m));
    showToast('info', `Iniciando descarga de ${id}...`);
    
    // Simulate download
    let prog = 0;
    const interval = setInterval(() => {
      prog += 10;
      setModels(prev => prev.map(m => m.id === id ? { ...m, progress: prog } : m));
      if (prog >= 100) {
        clearInterval(interval);
        setModels(prev => prev.map(m => m.id === id ? { ...m, status: 'installed', progress: undefined } : m));
        showToast('success', `Modelo ${id} instalado con éxito.`);
      }
    }, 1000);
  };

  const handleDelete = (id: string) => {
    if (window.confirm(`¿Estás seguro de eliminar el modelo ${id} del almacenamiento local?`)) {
      setModels(models.map(m => m.id === id ? { ...m, status: 'not_installed' } : m));
      showToast('success', `Modelo ${id} eliminado.`);
    }
  };

  const filteredModels = models.filter(m => m.name.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div className="h-full flex flex-col p-6 animate-fade-in bg-base-900 text-text-muted overflow-hidden">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-text-base flex items-center gap-2">
            <Box className="w-6 h-6 text-primary-400" />
            Local Model Hub
          </h2>
          <p className="text-sm opacity-70">App Store interna para la descarga de IAs locales</p>
        </div>
        <div className="relative w-64">
          <Search className="w-5 h-5 absolute left-3 top-2.5 opacity-50" />
          <input 
            type="text" 
            placeholder="Buscar modelos..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-base-800 border border-base-700 rounded-lg py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-primary-500 text-text-base"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 overflow-y-auto pr-2 pb-20">
        {filteredModels.map(model => (
          <div key={model.id} className="bg-base-800 border border-base-700 rounded-xl p-5 hover:border-primary-500/50 transition-all duration-300">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-text-base">{model.name}</h3>
                <span className="text-xs bg-base-900 px-2 py-1 rounded-md mt-1 inline-block text-primary-400 font-mono">
                  {model.type}
                </span>
              </div>
              {model.status === 'installed' ? (
                <span className="flex items-center gap-1 text-green-400 text-xs font-bold bg-green-400/10 px-2 py-1 rounded">
                  <ShieldCheck className="w-3 h-3" /> LISTO
                </span>
              ) : model.status === 'downloading' ? (
                <span className="flex items-center gap-1 text-accent-400 text-xs font-bold bg-accent-400/10 px-2 py-1 rounded animate-pulse">
                  <RefreshCw className="w-3 h-3 animate-spin" /> {model.progress}%
                </span>
              ) : (
                <span className="text-xs text-base-500 font-bold bg-base-900 px-2 py-1 rounded border border-base-700">
                  NUBE
                </span>
              )}
            </div>

            <div className="flex items-center gap-4 text-sm mb-6 opacity-80">
              <span className="flex items-center gap-1"><HardDrive className="w-4 h-4" /> {model.size}</span>
              <span className="flex items-center gap-1"><Cpu className="w-4 h-4" /> GGUF</span>
            </div>

            <div className="flex justify-end gap-2">
              {model.status === 'installed' ? (
                <button onClick={() => handleDelete(model.id)} className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors" title="Eliminar modelo local">
                  <Trash2 className="w-4 h-4" />
                </button>
              ) : model.status === 'downloading' ? (
                <div className="w-full bg-base-900 rounded-full h-2 mt-2">
                  <div className="bg-accent-500 h-2 rounded-full transition-all duration-500" style={{ width: `${model.progress}%` }}></div>
                </div>
              ) : (
                <button onClick={() => handleDownload(model.id)} className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-medium transition-colors">
                  <Download className="w-4 h-4" />
                  Descargar Local
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
