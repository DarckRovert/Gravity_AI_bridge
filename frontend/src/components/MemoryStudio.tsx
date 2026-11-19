import React, { useState, useEffect, useMemo } from 'react';
import { BrainCircuit, Database, Network, Search, Archive, Download, Cpu } from 'lucide-react';

interface RAGStatus {
  status: string;
  chunks: number;
  size_kb: number;
}

interface GraphNode {
  id: string;
  label: string;
  type: string;
  score: number;
  hits?: number;
}

interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  weight?: number;
}

interface GraphData {
  nodes_count: number;
  edges_count: number;
  most_central_nodes: { node: string; score: number }[];
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const MemoryStudio: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'graph' | 'list'>('graph');
  const [ragStatus, setRagStatus] = useState<RAGStatus | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchGraphAndRag = async () => {
    try {
      const [ragRes, graphRes] = await Promise.all([
        fetch('/v1/rag/status').catch(() => null),
        fetch('/v1/memory/graph').catch(() => null),
      ]);

      if (ragRes && ragRes.ok) {
        const ragJson = await ragRes.json().catch(() => null);
        if (ragJson) setRagStatus(ragJson);
      }

      if (graphRes && graphRes.ok) {
        const graphJson = await graphRes.json().catch(() => null);
        if (graphJson && graphJson.nodes) {
          setGraphData(graphJson);
        }
      }
    } catch (e) {
      console.error("Failed to fetch memory data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphAndRag();
    const iv = setInterval(fetchGraphAndRag, 15000);
    return () => clearInterval(iv);
  }, []);

  const handleBackupGraph = () => {
    if (!graphData) return;
    const backupPayload = {
      timestamp: new Date().toISOString(),
      engine: "Gravity Strategic Memory V16.0 PRO",
      rag_status: ragStatus,
      knowledge_graph: graphData,
    };
    const blob = new Blob([JSON.stringify(backupPayload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gravity_knowledge_graph_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Filtrado de nodos
  const filteredNodes = useMemo(() => {
    if (!graphData?.nodes) return [];
    if (!searchTerm.trim()) return graphData.nodes;
    const term = searchTerm.toLowerCase();
    return graphData.nodes.filter(
      (n) => n.id.toLowerCase().includes(term) || n.label.toLowerCase().includes(term) || n.type.toLowerCase().includes(term)
    );
  }, [graphData, searchTerm]);

  // Layout geométrico determinista para SVG
  const nodePositions = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>();
    if (!graphData?.nodes) return map;

    const width = 860;
    const height = 560;
    const cx = width / 2;
    const cy = height / 2;

    const categories = graphData.nodes.filter((n) => n.type === 'category');
    const outcomes = graphData.nodes.filter((n) => n.type === 'outcome');
    const decisions = graphData.nodes.filter((n) => n.type === 'decision');
    const patterns = graphData.nodes.filter((n) => n.type === 'pattern');
    const others = graphData.nodes.filter((n) => !['category', 'outcome', 'decision', 'pattern'].includes(n.type));

    // Centro / Anillo 1: Categorías
    const rCat = 110;
    categories.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / (categories.length || 1);
      map.set(n.id, { x: cx + rCat * Math.cos(angle), y: cy + rCat * Math.sin(angle) });
    });

    // Anillo 2: Outcomes
    const rOut = 170;
    outcomes.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / (outcomes.length || 1) + 0.3;
      map.set(n.id, { x: cx + rOut * Math.cos(angle), y: cy + rOut * Math.sin(angle) });
    });

    // Anillo 3: Patrones
    const rPat = 230;
    patterns.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / (patterns.length || 1) + 0.6;
      map.set(n.id, { x: cx + rPat * Math.cos(angle), y: cy + rPat * Math.sin(angle) });
    });

    // Anillo 4: Decisiones y otros
    const decAndOthers = [...decisions, ...others];
    const rDec = 270;
    decAndOthers.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / (decAndOthers.length || 1) + 0.1;
      map.set(n.id, { x: cx + rDec * Math.cos(angle), y: cy + rDec * Math.sin(angle) });
    });

    return map;
  }, [graphData]);

  const getNodeColor = (type: string, id: string) => {
    if (type === 'outcome') {
      if (id === 'success') return '#10b981';
      if (id === 'failure') return '#ef4444';
      return '#f59e0b';
    }
    if (type === 'category') return '#6366f1';
    if (type === 'decision') return '#3b82f6';
    if (type === 'pattern') return '#a855f7';
    return '#64748b';
  };

  return (
    <div className="flex flex-col h-full overflow-hidden p-6 space-y-6">
      <div className="flex justify-between items-center shrink-0">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <BrainCircuit className="text-accent-primary" size={32} />
            Memory Studio
          </h1>
          <p className="text-text-muted mt-1">Knowledge Graph en tiempo real y memoria de decisiones estratégicas de Gravity.</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={handleBackupGraph}
            disabled={!graphData}
            className="flex items-center gap-2 px-4 py-2 bg-card border border-border-subtle rounded-xl hover:border-accent-primary transition-colors text-sm font-medium disabled:opacity-50"
            title="Exportar Knowledge Graph y decisiones en formato JSON"
          >
            <Download size={16} /> Respaldar Grafo
          </button>
        </div>
      </div>

      <div className="flex gap-4 shrink-0">
        <div className="flex bg-surface p-1 rounded-xl">
          <button 
            onClick={() => setActiveTab('graph')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-colors ${activeTab === 'graph' ? 'bg-card text-accent-primary shadow-sm' : 'text-text-muted hover:text-white'}`}
          >
            <Network size={16} /> Grafo Visual ({graphData?.nodes_count || 0})
          </button>
          <button 
            onClick={() => setActiveTab('list')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-colors ${activeTab === 'list' ? 'bg-card text-accent-primary shadow-sm' : 'text-text-muted hover:text-white'}`}
          >
            <Archive size={16} /> Nodos de Memoria ({filteredNodes.length})
          </button>
        </div>

        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={18} />
          <input 
            type="text" 
            placeholder="Buscar recuerdos, categorías, patrones o decisiones..." 
            className="w-full bg-card border border-border-subtle rounded-xl pl-10 pr-4 py-2 text-white focus:outline-none focus:border-accent-primary transition-colors"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="flex-1 min-h-0 relative">
        {activeTab === 'list' ? (
          <div className="h-full overflow-y-auto space-y-4 pr-2">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-accent-primary hover:bg-surface/50 transition-colors">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-3">
                    <Database className="text-status-info" size={18} />
                    <span className="font-bold text-white text-lg">Gravity Vector RAG</span>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-mono">SQLite-VSS</span>
                </div>
                <div className="text-sm mt-3 text-text-muted space-y-1">
                  <div>Fragmentos indexados: <b className="text-white">{ragStatus?.chunks || 0}</b></div>
                  <div>Peso del índice: <b className="text-white">{ragStatus?.size_kb || 0} KB</b></div>
                </div>
              </div>

              <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-accent-secondary hover:bg-surface/50 transition-colors">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-3">
                    <Cpu className="text-accent-secondary" size={18} />
                    <span className="font-bold text-white text-lg">Knowledge Graph Metrics</span>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 font-mono">NetworkX</span>
                </div>
                <div className="text-sm mt-3 text-text-muted space-y-1">
                  <div>Nodos activos: <b className="text-white">{graphData?.nodes_count || 0}</b> | Aristas: <b className="text-white">{graphData?.edges_count || 0}</b></div>
                  <div>Nodos centrales (PageRank): <b className="text-white">{graphData?.most_central_nodes?.map(m => m.node).slice(0, 3).join(', ') || 'N/A'}</b></div>
                </div>
              </div>
            </div>

            <div className="space-y-2 mt-4">
              <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider">Nodos del Grafo ({filteredNodes.length})</h3>
              {filteredNodes.length === 0 ? (
                <div className="text-center py-10 text-text-muted">
                  No se encontraron nodos coincidentes con "{searchTerm}".
                </div>
              ) : (
                filteredNodes.map((node) => (
                  <div 
                    key={node.id} 
                    className="p-4 bg-card/60 hover:bg-card border border-border-subtle rounded-xl flex items-center justify-between transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div 
                        className="w-3.5 h-3.5 rounded-full shrink-0" 
                        style={{ backgroundColor: getNodeColor(node.type, node.id) }} 
                      />
                      <div className="truncate">
                        <div className="font-bold text-white text-sm truncate">{node.label}</div>
                        <div className="text-xs text-text-muted font-mono">{node.id}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-xs uppercase font-mono px-2 py-0.5 rounded bg-surface border border-border-subtle text-text-muted">
                        {node.type}
                      </span>
                      {node.score > 0 && (
                        <span className="text-xs font-mono text-accent-primary" title="PageRank Score">
                          PR: {node.score}
                        </span>
                      )}
                      {node.hits && (
                        <span className="text-xs font-mono text-text-muted">
                          Hits: {node.hits}
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        ) : (
          <div className="h-full w-full glass-panel rounded-2xl flex flex-col relative overflow-hidden">
            {/* Leyenda */}
            <div className="absolute top-4 left-4 z-10 flex flex-wrap gap-2 bg-card/80 backdrop-blur p-2 rounded-xl border border-border-subtle text-xs">
              <div className="flex items-center gap-1.5 px-2 py-1">
                <div className="w-2.5 h-2.5 rounded-full bg-[#6366f1]" />
                <span className="text-text-muted font-medium">Categorías</span>
              </div>
              <div className="flex items-center gap-1.5 px-2 py-1">
                <div className="w-2.5 h-2.5 rounded-full bg-[#10b981]" />
                <span className="text-text-muted font-medium">Éxitos</span>
              </div>
              <div className="flex items-center gap-1.5 px-2 py-1">
                <div className="w-2.5 h-2.5 rounded-full bg-[#3b82f6]" />
                <span className="text-text-muted font-medium">Decisiones</span>
              </div>
              <div className="flex items-center gap-1.5 px-2 py-1">
                <div className="w-2.5 h-2.5 rounded-full bg-[#a855f7]" />
                <span className="text-text-muted font-medium">Patrones</span>
              </div>
            </div>

            {/* Inspector flotante al seleccionar nodo */}
            {selectedNode && (
              <div className="absolute bottom-4 right-4 z-10 max-w-sm bg-card/95 backdrop-blur border border-accent-primary/40 p-4 rounded-xl shadow-xl space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-surface border border-border-subtle" style={{ color: getNodeColor(selectedNode.type, selectedNode.id) }}>
                    {selectedNode.type}
                  </span>
                  <button onClick={() => setSelectedNode(null)} className="text-text-muted hover:text-white text-xs">Cerrar</button>
                </div>
                <div className="font-bold text-white text-sm">{selectedNode.label}</div>
                <div className="text-xs text-text-muted font-mono break-all">{selectedNode.id}</div>
                <div className="flex justify-between text-xs pt-1 border-t border-border-subtle text-text-muted">
                  <span>Centralidad PageRank: <b className="text-accent-primary">{selectedNode.score}</b></span>
                  {selectedNode.hits && <span>Hits: <b className="text-white">{selectedNode.hits}</b></span>}
                </div>
              </div>
            )}

            {/* Canvas SVG Interactivo */}
            <div className="flex-1 w-full h-full relative overflow-auto flex items-center justify-center">
              {loading ? (
                <div className="flex flex-col items-center justify-center gap-3 text-text-muted">
                  <Network className="animate-spin text-accent-primary" size={36} />
                  <span>Cargando topología de memoria...</span>
                </div>
              ) : !graphData || graphData.nodes.length === 0 ? (
                <div className="flex flex-col items-center justify-center gap-3 text-text-muted">
                  <Database size={48} className="text-text-muted/40" />
                  <span>No hay nodos en el Knowledge Graph todavía.</span>
                </div>
              ) : (
                <svg 
                  viewBox="0 0 860 560" 
                  className="w-full h-full max-h-[700px] select-none"
                >
                  <defs>
                    <radialGradient id="graphGlow" cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stopColor="#6366f1" stopOpacity="0.1" />
                      <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
                    </radialGradient>
                  </defs>

                  <rect width="860" height="560" fill="transparent" onClick={() => setSelectedNode(null)} />

                  {/* Aristas */}
                  <g className="edges">
                    {graphData.edges.map((edge, i) => {
                      const src = nodePositions.get(edge.source);
                      const tgt = nodePositions.get(edge.target);
                      if (!src || !tgt) return null;

                      const isHighlighted = selectedNode && (selectedNode.id === edge.source || selectedNode.id === edge.target);

                      return (
                        <line
                          key={`edge-${i}`}
                          x1={src.x}
                          y1={src.y}
                          x2={tgt.x}
                          y2={tgt.y}
                          stroke={isHighlighted ? "#6366f1" : "#334155"}
                          strokeWidth={isHighlighted ? 2.5 : 1}
                          strokeOpacity={isHighlighted ? 0.9 : 0.4}
                          strokeDasharray={edge.relation === 'related_to' ? '3 3' : undefined}
                        />
                      );
                    })}
                  </g>

                  {/* Vértices / Nodos */}
                  <g className="nodes">
                    {graphData.nodes.map((node) => {
                      const pos = nodePositions.get(node.id);
                      if (!pos) return null;

                      const isSelected = selectedNode?.id === node.id;
                      const matchesSearch = !searchTerm.trim() || 
                        node.id.toLowerCase().includes(searchTerm.toLowerCase()) || 
                        node.label.toLowerCase().includes(searchTerm.toLowerCase());

                      const radius = Math.min(22, Math.max(9, 9 + node.score * 70));
                      const color = getNodeColor(node.type, node.id);

                      return (
                        <g 
                          key={`node-${node.id}`} 
                          className="cursor-pointer transition-transform hover:scale-110"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedNode(node);
                          }}
                          opacity={matchesSearch ? 1 : 0.25}
                        >
                          {isSelected && (
                            <circle
                              cx={pos.x}
                              cy={pos.y}
                              r={radius + 6}
                              fill="none"
                              stroke="#6366f1"
                              strokeWidth="2"
                              strokeDasharray="4 2"
                              className="animate-spin origin-center"
                            />
                          )}
                          <circle
                            cx={pos.x}
                            cy={pos.y}
                            r={radius}
                            fill={color}
                            stroke={isSelected ? "#ffffff" : "#0f172a"}
                            strokeWidth={2}
                          />
                          <text
                            x={pos.x}
                            y={pos.y + radius + 11}
                            textAnchor="middle"
                            fill={matchesSearch ? "#e2e8f0" : "#64748b"}
                            fontSize="9"
                            fontFamily="monospace"
                            className="pointer-events-none select-none"
                          >
                            {node.label.length > 14 ? node.label.slice(0, 12) + '..' : node.label}
                          </text>
                        </g>
                      );
                    })}
                  </g>
                </svg>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
