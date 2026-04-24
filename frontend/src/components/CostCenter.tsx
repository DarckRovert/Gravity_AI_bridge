import { useEffect, useState } from 'react';
import { DollarSign, PieChart, TrendingUp, AlertTriangle, Database } from 'lucide-react';

export const CostCenter = () => {
  const [cost, setCost] = useState<any>(null);

  useEffect(() => {
    const fetchCost = async () => {
      try {
        const res = await fetch('http://localhost:7860/v1/cost');
        if (res.ok) setCost(await res.json());
      } catch (e) {}
    };
    fetchCost();
    const iv = setInterval(fetchCost, 5000);
    return () => clearInterval(iv);
  }, []);

  const Card = ({ title, value, sub, icon: Icon, color }: any) => (
    <div className="glass-card p-6 flex flex-col">
      <div className="flex justify-between items-start mb-4">
        <div className="p-2 rounded-lg bg-surface border border-border-subtle">
          <Icon size={20} className={color} />
        </div>
      </div>
      <div className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1">{title}</div>
      <div className="text-3xl font-extrabold text-text-primary">{value}</div>
      <div className="text-xs text-text-muted mt-2 font-medium">{sub}</div>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle">
              <DollarSign className="text-status-warning" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Cost Center</h1>
              <p className="text-text-muted mt-1 font-medium">Auditoría financiera de tokens y límites de consumo diario.</p>
            </div>
          </div>
          <div className="px-4 py-2 rounded-xl bg-status-warning/10 border border-status-warning/20 flex items-center gap-2">
            <AlertTriangle size={16} className="text-status-warning" />
            <span className="text-sm font-bold text-status-warning">Límite Diario: ${cost?.daily_limit || '0.00'}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card 
            title="Coste Sesión" 
            value={`$${Number(cost?.session_cost || 0).toFixed(5)}`} 
            sub={`Tokens: ${cost?.session_tokens || 0}`}
            icon={TrendingUp} color="text-accent-primary" 
          />
          <Card 
            title="Consumo Diario" 
            value={`$${Number(cost?.daily_cost || 0).toFixed(4)}`} 
            sub="Acumulado en las últimas 24h"
            icon={PieChart} color="text-accent-secondary" 
          />
          <Card 
            title="Inyectores" 
            value={Object.keys(cost?.daily_breakdown || {}).length} 
            sub="Proveedores con facturación"
            icon={Database} color="text-accent-tertiary" 
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-widest mb-6 flex items-center gap-2">
              <TrendingUp size={16} className="text-accent-primary" /> Desglose por Proveedor
            </h3>
            <div className="space-y-4">
              {cost?.daily_breakdown && Object.entries(cost.daily_breakdown).length > 0 ? (
                Object.entries(cost.daily_breakdown).map(([prov, val]: any) => (
                  <div key={prov} className="flex items-center justify-between p-4 rounded-xl bg-card border border-border-subtle hover:border-accent-primary/30 transition-all">
                    <div className="font-bold text-text-primary">{prov}</div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-accent-primary">${Number(val || 0).toFixed(5)}</div>
                      <div className="text-[10px] text-text-muted uppercase">Tokens: {cost?.session_tokens || 0}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-12 text-center text-text-muted text-sm font-medium opacity-50">
                  No hay datos de consumo registrados aún.
                </div>
              )}
            </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-border-subtle flex flex-col">
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-widest mb-6">Proyección de Gastos</h3>
            <div className="flex-1 flex flex-col items-center justify-center space-y-6">
              <div className="relative w-48 h-48 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="96" cy="96" r="80" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-surface" />
                  <circle 
                    cx="96" cy="96" r="80" stroke="currentColor" strokeWidth="12" fill="transparent" 
                    strokeDasharray={502} 
                    strokeDashoffset={502 - (502 * (Number(cost?.daily_limit) > 0 ? (Number(cost?.daily_cost) / Number(cost?.daily_limit)) : 0))}
                    className="text-status-warning transition-all duration-1000"
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-extrabold text-text-primary">{Math.round((Number(cost?.daily_limit) > 0 ? (Number(cost?.daily_cost) / Number(cost?.daily_limit)) : 0) * 100)}%</span>
                  <span className="text-[10px] text-text-muted font-bold uppercase">del límite</span>
                </div>
              </div>
              <p className="text-xs text-text-muted text-center max-w-[240px] leading-relaxed">
                Basado en el uso actual, se estima que no superarás el límite diario de <span className="text-text-primary font-bold">${cost?.daily_limit}</span>.
              </p>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
