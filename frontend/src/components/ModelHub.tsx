import React, { useState, useEffect } from 'react';
import { Box, Search, Star, Cpu, Server, CheckCircle2 } from 'lucide-react';
import { showToast } from './Toast';

interface RealModel {
  id: string;
  object: string;
  owned_by: string;
}

export const ModelHub: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('All');
  const [models, setModels] = useState<RealModel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await fetch('/v1/models');
        if (!res.ok) {
           const errData = await res.json().catch(() => ({}));
           throw new Error(errData.error || 'Fallo de conexión con el repositorio de modelos');
        }
        const json = await res.json().catch(() => null);
        if (json?.data) {
          setModels(json.data);
        } else {
          throw new Error('El servidor devolvió un payload corrupto');
        }
      } catch (e: any) {
        showToast('error', `Error en Model Hub: ${e.message}`);
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
  }, []);

  const filteredModels = models.filter(m => 
    (filter === 'All' || m.owned_by === filter) &&
    m.id.toLowerCase().includes(searchTerm.toLowerCase())
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
          <button 
            onClick={() => showToast('info', 'Configuración de almacenamiento bloqueada temporalmente por el orquestador')}
            className="flex items-center gap-2 px-4 py-2 bg-card border border-border-subtle rounded-xl hover:border-accent-primary transition-colors text-sm font-medium"
          >
            <Server size={16} /> Configurar Almacenamiento
          </button>
        </div>
      </div>

      <div className="flex gap-4 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={18} />
          <input 
            type="text" 
            placeholder="Buscar modelos locales..." 
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
          <option value="All">Todos los Proveedores</option>
          {Array.from(new Set(models.map(m => m.owned_by))).map(prov => (
            <option key={prov} value={prov}>{prov}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-20 text-text-muted animate-pulse">Cargando modelos desde el Bridge...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredModels.map(model => (
            <div key={model.id} className="glass-panel p-5 rounded-2xl flex flex-col hover:border-accent-primary/50 transition-colors group">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-bold text-white group-hover:text-accent-primary transition-colors">{model.id}</h3>
                  <p className="text-sm text-text-muted">{model.owned_by}</p>
                </div>
                <div className="px-2 py-1 bg-surface rounded-md text-xs font-semibold text-text-muted border border-border-subtle">
                  LLM
                </div>
              </div>
              
              <div className="flex gap-4 text-sm mb-6 text-text-muted">
                <span className="flex items-center gap-1"><Cpu size={14} /> Activo</span>
                <span className="flex items-center gap-1 text-status-warning"><Star size={14} /> Local</span>
              </div>

              <div className="mt-auto">
                <button className="w-full py-2 bg-status-success/10 text-status-success rounded-xl font-bold flex justify-center items-center gap-2 border border-status-success/20">
                  <CheckCircle2 size={18} /> Instalado
                </button>
              </div>
            </div>
          ))}
          {filteredModels.length === 0 && (
            <div className="col-span-full text-center text-text-muted py-10">No se encontraron modelos.</div>
          )}
        </div>
      )}
    </div>
  );
};
