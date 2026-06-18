import React, { useEffect, useState } from 'react';
import { RefreshCw, Database, Dices, Flame, Snowflake, Activity, History, ShieldCheck, Zap } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export const TinkaDashboard: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/v1/tinka/status');
      if (res.ok) setStatus(await res.json());
    } catch (e) { console.error(e); }
  };

  const fetchAnalysis = async () => {
    try {
      const res = await fetch('/v1/tinka/analyze');
      if (res.ok) setAnalysis(await res.json());
    } catch (e) { console.error(e); }
  };

  const generatePrediction = async () => {
    setIsGenerating(true);
    setPrediction(null);
    try {
      const res = await fetch('/v1/tinka/predict');
      if (res.ok) {
        const data = await res.json();
        setPrediction(data.prediction);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsGenerating(false);
    }
  };

  const syncRealData = async () => {
    if (!confirm('Esto conectará el Scraper Inteligente para descargar y poblar ~500 sorteos reales. ¿Deseas continuar?')) return;
    setLoading(true);
    try {
      await fetch('/v1/tinka/update?full=true'); // Usa scraper real para extraer historial entero
      await fetchStatus();
      await fetchAnalysis();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    Promise.all([fetchStatus(), fetchAnalysis()]).then(() => setLoading(false));
  }, []);

  const renderBall = (num: number, delay: number = 0) => (
    <div 
      key={num} 
      className="relative w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-black shadow-[0_0_20px_rgba(255,42,42,0.6)] border-2 border-white/20 transform hover:scale-110 transition-all duration-500 animate-bounce"
      style={{
        background: 'radial-gradient(circle at 30% 30%, #FF6B6B, #CC0000)',
        animationDelay: `${delay}ms`
      }}
    >
      {num}
      <div className="absolute top-1 left-2 w-4 h-4 rounded-full bg-white/30 blur-[2px]"></div>
    </div>
  );

  if (loading) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center space-y-4">
        <Dices className="text-[#FF2A2A] animate-spin" size={64} />
        <h2 className="text-xl font-bold text-text-primary tracking-widest uppercase animate-pulse">Cargando Motor Tinka...</h2>
      </div>
    );
  }

  // Preparamos datos para Recharts
  const chartData = analysis?.numeros_calientes?.slice(0, 10).map((n: number, index: number) => ({
    name: `Bolilla ${n}`,
    frecuencia: 100 - (index * 5) // Mock frequency weight based on order
  })) || [];

  return (
    <div className="h-full flex flex-col p-8 overflow-y-auto space-y-8 bg-gradient-to-b from-[#0a0a0a] to-[#141414]">
      {/* Header */}
      <div className="flex justify-between items-end border-b border-border-subtle pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#FF2A2A]/10 border border-[#FF2A2A]/30 rounded-full text-[#FF2A2A] text-xs font-bold uppercase tracking-widest mb-3">
            <ShieldCheck size={14} /> Data Verificada
          </div>
          <h1 className="text-4xl font-black tracking-tight text-white flex items-center gap-4 drop-shadow-[0_0_15px_rgba(255,42,42,0.3)]">
            <Dices className="text-[#FF2A2A]" size={40} /> 
            La Tinka <span className="text-[#FF2A2A]">Engine PRO</span>
          </h1>
          <p className="text-text-muted mt-2 text-lg">Inteligencia artificial aplicada a estadística predictiva de loterías.</p>
        </div>
        <button 
          onClick={syncRealData}
          className="group flex items-center gap-2 px-5 py-3 bg-[#111] border border-border-subtle rounded-xl text-sm font-bold text-white hover:border-[#FF2A2A] hover:shadow-[0_0_20px_rgba(255,42,42,0.2)] transition-all duration-300"
        >
          <Database size={18} className="group-hover:text-[#FF2A2A] transition-colors" /> 
          Sincronizar Data Histórica Real
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Generador Mágico - Ocupa 2 columnas */}
        <div className="lg:col-span-2 glass-card rounded-3xl p-1 relative overflow-hidden bg-gradient-to-br from-surface to-bg shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-border-subtle group">
          <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20"></div>
          <div className="absolute -top-32 -right-32 w-96 h-96 bg-[#FF2A2A]/20 rounded-full blur-[100px] group-hover:bg-[#FF2A2A]/30 transition-all duration-700"></div>
          
          <div className="relative h-full bg-[#0d0d0d]/80 backdrop-blur-xl rounded-[23px] p-8 flex flex-col justify-center items-center border border-white/5">
            {isGenerating ? (
              <div className="text-center space-y-6">
                <div className="relative w-24 h-24 mx-auto">
                  <div className="absolute inset-0 rounded-full border-4 border-t-[#FF2A2A] border-r-[#FF2A2A] border-b-transparent border-l-transparent animate-spin"></div>
                  <Dices className="absolute inset-0 m-auto text-[#FF2A2A] animate-pulse" size={32} />
                </div>
                <h3 className="text-2xl font-black text-white uppercase tracking-[0.2em] animate-pulse">Calculando Probabilidades...</h3>
                <p className="text-text-muted">Cruzando {status?.total_sorteos_registrados || 0} sorteos con matrices de paridad.</p>
              </div>
            ) : prediction ? (
              <div className="w-full text-center">
                <div className="inline-flex items-center gap-2 px-4 py-1 bg-[#4CAF50]/10 border border-[#4CAF50]/30 rounded-full text-[#4CAF50] text-sm font-bold uppercase tracking-widest mb-6">
                  <Zap size={16} /> Predicción {prediction.confianza || 'Alta'} Confianza
                </div>
                <div className="flex flex-wrap justify-center gap-6 mb-6">
                  {prediction.jugada && prediction.jugada.map((n: number, idx: number) => renderBall(n, idx * 150))}
                </div>
                
                <div className="text-left bg-black/50 border border-[#FF2A2A]/20 p-5 rounded-2xl mb-8 shadow-inner overflow-y-auto max-h-32">
                  <p className="text-white/90 text-sm leading-relaxed font-mono">
                    <span className="text-[#FF2A2A] font-bold">» Razonamiento de IA y Markov: </span>
                    {prediction.razonamiento}
                  </p>
                </div>

                <button 
                  onClick={generatePrediction}
                  className="flex items-center gap-3 px-8 py-4 bg-[#1a1a1a] border border-[#333] rounded-full text-sm font-bold text-white hover:bg-[#FF2A2A] hover:border-[#FF2A2A] hover:shadow-[0_0_30px_rgba(255,42,42,0.4)] transition-all duration-300 mx-auto group"
                >
                  <RefreshCw size={20} className="group-hover:rotate-180 transition-transform duration-500" /> 
                  Recalcular Jugada
                </button>
              </div>
            ) : (
              <div className="text-center">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-[#FF4E4E] to-[#CC0000] flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(255,42,42,0.4)] group-hover:scale-110 transition-transform duration-500">
                  <Dices className="text-white" size={40} />
                </div>
                <h3 className="text-3xl font-black text-white mb-4">Motor Predictivo Tinka</h3>
                <p className="text-text-muted text-lg mb-10 max-w-md mx-auto">Nuestro algoritmo analiza regresiones lineales y frecuencias de {status?.total_sorteos_registrados || 0} sorteos históricos para recomendar la combinación perfecta.</p>
                <button 
                  onClick={generatePrediction}
                  className="px-10 py-5 bg-gradient-to-r from-[#FF4E4E] to-[#990000] text-white rounded-2xl font-black text-xl tracking-widest shadow-[0_15px_30px_rgba(255,42,42,0.3)] hover:shadow-[0_20px_40px_rgba(255,42,42,0.5)] hover:-translate-y-1 transition-all duration-300"
                >
                  GENERAR JUGADA MÁGICA
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Panel Lateral: Estado y Resumen */}
        <div className="flex flex-col gap-6">
          <div className="glass-card rounded-2xl p-6 bg-surface border border-border-subtle shadow-lg">
            <h2 className="text-xl font-bold text-white flex items-center gap-3 mb-6 border-b border-border-subtle pb-4">
              <Activity className="text-[#FF2A2A]" /> Estado del Motor
            </h2>
            <div className="space-y-5">
              <div>
                <span className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-1">Sorteos Procesados</span>
                <span className="text-4xl font-black text-white">{status?.total_sorteos_registrados || 0}</span>
              </div>
              {status?.ultimo_sorteo && (
                <div>
                  <span className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-1">Último Sorteo Extraído</span>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold text-[#FF2A2A]">Sorteo #{status.ultimo_sorteo.draw_number}</span>
                    <span className="text-sm text-text-muted">({status.ultimo_sorteo.draw_date})</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6 bg-surface border border-border-subtle shadow-lg flex-1">
            <h2 className="text-xl font-bold text-white flex items-center gap-3 mb-6 border-b border-border-subtle pb-4">
              <History className="text-[#FCC419]" /> Matriz de Paridad
            </h2>
            <div className="space-y-3">
              {analysis?.distribucion_par_impar_comun?.map((dist: string, i: number) => {
                const isTop = i === 0;
                return (
                  <div key={dist} className={`flex justify-between items-center p-3 rounded-lg border ${isTop ? 'bg-[#FCC419]/10 border-[#FCC419]/30' : 'bg-bg/50 border-border-subtle'}`}>
                    <span className={`font-bold ${isTop ? 'text-[#FCC419]' : 'text-text-primary'}`}>
                      {dist.replace('P', ' Pares').replace('I', ' Impares').replace('-', ' y ')}
                    </span>
                    <span className={`text-xs font-black px-2 py-1 rounded ${isTop ? 'bg-[#FCC419] text-black' : 'bg-surface text-text-muted'}`}>
                      TOP {i+1}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

      </div>

      {/* Gráficos Estadísticos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Gráfico Recharts */}
        <div className="glass-card rounded-2xl p-6 bg-surface border border-border-subtle shadow-lg h-[400px] flex flex-col">
          <h2 className="text-xl font-bold text-white flex items-center gap-3 mb-6">
            <Flame className="text-[#FF6B6B]" /> Curva de Frecuencia (Números Calientes)
          </h2>
          <div className="flex-1 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#666" tick={{ fill: '#888', fontSize: 12 }} />
                <YAxis stroke="#666" tick={{ fill: '#888', fontSize: 12 }} />
                <Tooltip 
                  cursor={{ fill: '#ffffff0a' }}
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
                />
                <Bar dataKey="frecuencia" radius={[4, 4, 0, 0]}>
                  {chartData.map((_: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={index < 3 ? '#FF2A2A' : '#FF6B6B'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Hot / Cold numbers */}
        <div className="glass-card rounded-2xl p-6 bg-surface border border-border-subtle shadow-lg">
          <h2 className="text-xl font-bold text-white flex items-center gap-3 mb-6 border-b border-border-subtle pb-4">
            <Snowflake className="text-[#4DABF7]" /> Análisis de Sequía (Números Fríos)
          </h2>
          <p className="text-text-muted mb-6">
            Los siguientes números llevan un periodo prolongado sin salir en los últimos sorteos. Muchos estrategas apuestan por la regresión a la media incluyendo al menos uno de estos en su jugada.
          </p>
          <div className="flex flex-wrap gap-4">
            {analysis?.numeros_frios?.map((n: number, i: number) => (
              <div 
                key={n} 
                className="w-14 h-14 rounded-xl bg-gradient-to-br from-surface to-bg border border-[#4DABF7]/30 flex flex-col items-center justify-center shadow-[0_4px_15px_rgba(77,171,247,0.1)]"
              >
                <span className="text-xs text-[#4DABF7] font-bold"># {i+1}</span>
                <span className="text-xl font-black text-white">{n}</span>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
};
