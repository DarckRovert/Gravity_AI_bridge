import React, { useState } from 'react';
import { Database, Search, Plus, Trash2, Edit2, Share2, BrainCircuit } from 'lucide-react';
import { showToast } from './Toast';

interface MemoryNode {
  id: string;
  entity: string;
  relation: string;
  target: string;
  source: string;
  confidence: number;
}

const mockMemories: MemoryNode[] = [
  { id: 'mem-1', entity: 'Usuario', relation: 'PREFIERE_MODELO', target: 'Llama 3 8B', source: 'Conversacion_V16_3', confidence: 0.98 },
  { id: 'mem-2', entity: 'GravityAI', relation: 'CORRE_EN_PUERTO', target: '7860', source: 'System_Init', confidence: 1.00 },
  { id: 'mem-3', entity: 'Fooocus CPU', relation: 'TIENE_FALLBACK', target: 'Pollinations.ai', source: 'Fallback_Engine', confidence: 0.95 },
  { id: 'mem-4', entity: 'Memory Guard', relation: 'MONITOREA_RAM', target: 'psutil', source: 'Core_Guard', confidence: 0.99 },
  { id: 'mem-5', entity: 'Agente Periodístico', relation: 'REDACTA_CON', target: 'JournalistPanel', source: 'News_Daemon', confidence: 0.92 }
];

export const MemoryStudio: React.FC = () => {
  const [memories, setMemories] = useState<MemoryNode[]>(mockMemories);
  const [searchTerm, setSearchTerm] = useState('');
  const [newEntity, setNewEntity] = useState('');
  const [newRelation, setNewRelation] = useState('');
  const [newTarget, setNewTarget] = useState('');

  const handleAddMemory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEntity || !newRelation || !newTarget) {
      showToast('Por favor, rellena todos los campos de la relación.', 'error');
      return;
    }
    const newMem: MemoryNode = {
      id: `mem-${Date.now()}`,
      entity: newEntity,
      relation: newRelation.toUpperCase(),
      target: newTarget,
      source: 'Manual_Insertion',
      confidence: 1.00
    };
    setMemories([newMem, ...memories]);
    setNewEntity('');
    setNewRelation('');
    setNewTarget('');
    showToast('Nueva relación consolidada en el grafo de memoria.', 'success');
  };

  const handleDelete = (id: string) => {
    if (window.confirm('¿Deseas purgar esta relación de la memoria de largo plazo?')) {
      setMemories(memories.filter(m => m.id !== id));
      showToast('Relación de memoria purgada.', 'success');
    }
  };

  const filteredMemories = memories.filter(m => 
    m.entity.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.relation.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.target.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col p-6 animate-fade-in bg-base-900 text-text-muted overflow-hidden">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-text-base flex items-center gap-2">
            <BrainCircuit className="w-6 h-6 text-accent-400" />
            Memory Studio
          </h2>
          <p className="text-sm opacity-70">Visualizador y editor del Knowledge Graph de largo plazo</p>
        </div>
        <div className="relative w-64">
          <Search className="w-5 h-5 absolute left-3 top-2.5 opacity-50" />
          <input 
            type="text" 
            placeholder="Buscar relaciones..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-base-800 border border-base-700 rounded-lg py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-accent-500 text-text-base"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        {/* Formulario de Inyección de Memoria */}
        <div className="lg:col-span-1 bg-base-800 border border-base-700 rounded-xl p-5 h-fit">
          <h3 className="text-lg font-semibold text-text-base mb-4 flex items-center gap-2">
            <Plus className="w-5 h-5 text-accent-400" />
            Consolidar Nueva Relación
          </h3>
          <form onSubmit={handleAddMemory} className="space-y-4">
            <div>
              <label className="text-xs uppercase tracking-wider block mb-1">Entidad Origen</label>
              <input 
                type="text" 
                placeholder="Ej. Usuario, Gravity, ComfyUI" 
                value={newEntity}
                onChange={(e) => setNewEntity(e.target.value)}
                className="w-full bg-base-900 border border-base-700 rounded-lg p-2.5 text-sm focus:outline-none focus:border-accent-500 text-text-base"
              />
            </div>
            <div>
              <label className="text-xs uppercase tracking-wider block mb-1">Relación (Predicado)</label>
              <input 
                type="text" 
                placeholder="Ej. PREFIERE, CONTIENE, USA" 
                value={newRelation}
                onChange={(e) => setNewRelation(e.target.value)}
                className="w-full bg-base-900 border border-base-700 rounded-lg p-2.5 text-sm focus:outline-none focus:border-accent-500 text-text-base"
              />
            </div>
            <div>
              <label className="text-xs uppercase tracking-wider block mb-1">Entidad Destino</label>
              <input 
                type="text" 
                placeholder="Ej. AMD GPU, Puerto 8188" 
                value={newTarget}
                onChange={(e) => setNewTarget(e.target.value)}
                className="w-full bg-base-900 border border-base-700 rounded-lg p-2.5 text-sm focus:outline-none focus:border-accent-500 text-text-base"
              />
            </div>
            <button type="submit" className="w-full py-2.5 rounded-lg bg-accent-600 hover:bg-accent-500 text-white font-medium transition-colors flex items-center justify-center gap-2">
              <Database className="w-4 h-4" />
              Consolidar en Grafo
            </button>
          </form>
        </div>

        {/* Listado de Relaciones */}
        <div className="lg:col-span-2 bg-base-800 border border-base-700 rounded-xl p-5 flex flex-col min-h-0">
          <h3 className="text-lg font-semibold text-text-base mb-4 flex items-center justify-between">
            <span>Explorador de Tripletas RAG</span>
            <span className="text-xs opacity-50">{filteredMemories.length} registradas</span>
          </h3>

          <div className="flex-1 overflow-y-auto pr-1 space-y-3">
            {filteredMemories.map(mem => (
              <div key={mem.id} className="bg-base-900 border border-base-700 rounded-lg p-4 flex items-center justify-between hover:border-accent-500/30 transition-all">
                <div className="flex flex-col gap-1.5 flex-1 pr-4">
                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    <span className="font-semibold text-text-base bg-base-800 px-2 py-0.5 rounded border border-base-700">{mem.entity}</span>
                    <span className="text-xs text-accent-400 font-mono font-bold">---({mem.relation})---&gt;</span>
                    <span className="font-semibold text-text-base bg-base-800 px-2 py-0.5 rounded border border-base-700">{mem.target}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs opacity-60">
                    <span>Origen: <span className="font-mono">{mem.source}</span></span>
                    <span>Confianza: <span className="text-green-400 font-bold">{Math.round(mem.confidence * 100)}%</span></span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button onClick={() => handleDelete(mem.id)} className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors" title="Borrar de la memoria">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
