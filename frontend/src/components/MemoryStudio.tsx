import React, { useState, useEffect } from 'react';
import { BrainCircuit, Database, Network, Search, Archive } from 'lucide-react';

interface RAGStatus {
  status: string;
  chunks: number;
  size_kb: number;
}

export const MemoryStudio: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'graph' | 'list'>('graph');
  const [ragStatus, setRagStatus] = useState<RAGStatus | null>(null);

  useEffect(() => {
    const fetchRag = async () => {
      try {
        const res = await fetch('/v1/rag/status');
        if (res.ok) {
          const data = await res.json().catch(() => null);
          if (data) setRagStatus(data);
        }
      } catch (e) {
        console.error("Failed to fetch RAG status", e);
      }
    };
    fetchRag();
    const iv = setInterval(fetchRag, 15000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="flex flex-col h-full overflow-hidden p-6 space-y-6">
      <div className="flex justify-between items-center shrink-0">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <BrainCircuit className="text-accent-primary" size={32} />
            Memory Studio
          </h1>
          <p className="text-text-muted mt-1">Visualiza el Knowledge Graph y la memoria a largo plazo (RAG) de los agentes.</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-card border border-border-subtle rounded-xl hover:border-accent-primary transition-colors text-sm font-medium">
            <Database size={16} /> Respaldar Grafo
          </button>
        </div>
      </div>

      <div className="flex gap-4 shrink-0">
        <div className="flex bg-surface p-1 rounded-xl">
          <button 
            onClick={() => setActiveTab('graph')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-colors ${activeTab === 'graph' ? 'bg-card text-accent-primary shadow-sm' : 'text-text-muted hover:text-white'}`}
          >
            <Network size={16} /> Grafo Visual
          </button>
          <button 
            onClick={() => setActiveTab('list')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-colors ${activeTab === 'list' ? 'bg-card text-accent-primary shadow-sm' : 'text-text-muted hover:text-white'}`}
          >
            <Archive size={16} /> Nodos de Memoria
          </button>
        </div>

        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={18} />
          <input 
            type="text" 
            placeholder="Buscar en los recuerdos y entidades..." 
            className="w-full bg-card border border-border-subtle rounded-xl pl-10 pr-4 py-2 text-white focus:outline-none focus:border-accent-primary transition-colors"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="flex-1 min-h-0 relative">
        {activeTab === 'list' ? (
          <div className="h-full overflow-y-auto space-y-4 pr-2">
            <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-accent-primary hover:bg-surface/50 transition-colors">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-3">
                  <Database className="text-status-info" size={18} />
                  <span className="font-bold text-white text-lg">Knowledge Base (ChromaDB / FAISS)</span>
                </div>
                <span className="text-xs text-text-muted">En vivo</span>
              </div>
              <div className="text-sm mt-4 text-text-muted">
                La memoria contiene actualmente <b>{ragStatus?.chunks || 0} fragmentos</b> de conocimiento incrustados.
                <br/>Peso total del índice: {ragStatus?.size_kb || 0} KB.
              </div>
            </div>
            
            <div className="text-center text-text-muted mt-10">
              Usa la pestaña "Grafo Visual" para explorar las relaciones semánticas entre los fragmentos.
            </div>
          </div>
        ) : (
          <div className="h-full w-full glass-panel rounded-2xl flex items-center justify-center flex-col relative overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-accent-primary/5 via-bg to-bg pointer-events-none"></div>
            <Network size={64} className="text-accent-primary/40 mb-4 animate-pulse" />
            <h3 className="text-xl font-bold text-white z-10">Knowledge Graph Viewer</h3>
            <p className="text-text-muted z-10">Conectando {ragStatus?.chunks || 0} nodos semánticos...</p>
            <div className="mt-8 flex gap-4 z-10">
              <div className="px-4 py-2 bg-surface rounded-lg border border-border-subtle flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-status-info"></div>
                <span className="text-sm font-medium">Hechos (Facts)</span>
              </div>
              <div className="px-4 py-2 bg-surface rounded-lg border border-border-subtle flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-accent-secondary"></div>
                <span className="text-sm font-medium">Entidades (Entities)</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
