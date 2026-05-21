import { useEffect, useState } from 'react';
import { Settings as SettingsIcon, Save, Key, DollarSign, Brain, Globe } from 'lucide-react';

export const Settings = () => {
  const [settings, setSettings] = useState<any>({
     cost_limit_usd: 10,
     rag_enabled: true,
     model_locked: false,
     api_keys: {},
     universal_base_url: 'https://openrouter.ai/api/v1',
     universal_model: 'google/gemini-2.5-flash'
  });

  const fetchSettings = async () => {
     try {
       const res = await fetch('/v1/status'); // some settings come from status
       const cRes = await fetch('/v1/cost');
       if (res.ok && cRes.ok) {
         const sData = await res.json();
         const cData = await cRes.json();
         setSettings((prev: any) => ({
           ...prev,
           cost_limit_usd: cData.daily_limit,
           rag_enabled: sData.rag_enabled || false,
           model_locked: sData.model_locked || false,
           universal_base_url: sData.universal_base_url || 'https://openrouter.ai/api/v1',
           universal_model: sData.universal_model || 'google/gemini-2.5-flash'
         }));
       }
     } catch (e) {}
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSaveKey = async (provider: string, key: string) => {
    try {
      await fetch('/v1/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key: key })
      });
      alert(`Key para ${provider} actualizada`);
    } catch (e) { alert('Error al guardar key'); }
  };

  const handleSaveUniversalConfig = async (baseUrl: string, model: string) => {
    try {
      const res = await fetch('/v1/universal/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ universal_base_url: baseUrl, universal_model: model })
      });
      if (res.ok) {
        alert('Configuración de Universal AI guardada con éxito.');
      } else {
        alert('Error al guardar configuración de Universal AI.');
      }
    } catch (e) {
      alert('Error de conexión con el Bridge.');
    }
  };

  const toggleRag = async () => {
    try {
      const res = await fetch('/v1/rag/toggle', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSettings({ ...settings, rag_enabled: data.rag_enabled });
      }
    } catch (e) {}
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-5xl mx-auto space-y-8">
        
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-surface border border-border-subtle">
            <SettingsIcon className="text-text-primary" size={28} />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">System Settings</h1>
            <p className="text-text-muted mt-1 font-medium">Configuración de seguridad, límites de costes y comportamiento del núcleo.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
           
           <div className="space-y-6">
              <section className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
                 <h3 className="text-xs font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                    <Key size={16} className="text-accent-primary" /> API Key Management
                 </h3>
                 <div className="space-y-4">
                    <KeyInput label="OpenAI (GPT-4o/o1)" onSave={(v: string) => handleSaveKey('openai', v)} />
                    <KeyInput label="Anthropic (Claude 3.5)" onSave={(v: string) => handleSaveKey('anthropic', v)} />
                    <KeyInput label="Groq (Llama 3 70B)" onSave={(v: string) => handleSaveKey('groq', v)} />
                    <KeyInput label="Nvidia NIM (Llama 3.3)" onSave={(v: string) => handleSaveKey('nvidia', v)} />
                    <KeyInput label="OpenRouter (Universal)" onSave={(v: string) => handleSaveKey('openrouter', v)} />
                 </div>
              </section>

              <section className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6 bg-gradient-to-br from-accent-primary/5 to-transparent">
                 <h3 className="text-xs font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                    <Globe size={16} className="text-accent-primary" /> Proveedor Universal AI (OpenAI Compatible)
                 </h3>
                 <div className="space-y-4">
                    <div className="space-y-2">
                       <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Custom Base URL</div>
                       <input 
                         type="text" 
                         placeholder="https://api.yourprovider.com/v1" 
                         value={settings.universal_base_url}
                         onChange={(e) => setSettings({...settings, universal_base_url: e.target.value})}
                         className="w-full bg-surface border border-border-subtle rounded-lg px-3 py-2 text-xs text-text-primary outline-none focus:border-accent-primary" 
                       />
                    </div>
                    <div className="space-y-2">
                       <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Custom Model Name</div>
                       <input 
                         type="text" 
                         placeholder="your-model-name" 
                         value={settings.universal_model}
                         onChange={(e) => setSettings({...settings, universal_model: e.target.value})}
                         className="w-full bg-surface border border-border-subtle rounded-lg px-3 py-2 text-xs text-text-primary outline-none focus:border-accent-primary" 
                       />
                    </div>
                    <KeyInput label="API Key Seguro" onSave={(v: string) => handleSaveKey('universal', v)} />
                    <button
                      onClick={() => handleSaveUniversalConfig(settings.universal_base_url, settings.universal_model)}
                      className="w-full py-2.5 bg-accent-primary/10 text-accent-primary border border-accent-primary/20 rounded-lg text-xs font-black uppercase tracking-widest hover:bg-accent-primary hover:text-white transition-all shadow-[0_0_15px_rgba(168,85,247,0.1)]"
                    >Guardar Configuración Universal</button>
                 </div>
              </section>

              <section className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
                 <h3 className="text-xs font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                    <DollarSign size={16} className="text-status-success" /> Límites Financieros
                 </h3>
                 <div className="space-y-4">
                    <div className="flex justify-between items-center">
                       <span className="text-sm font-bold text-text-muted">Límite Diario (USD)</span>
                       <span className="text-lg font-black text-text-primary">${settings.cost_limit_usd}</span>
                    </div>
                    <input type="range" min="1" max="50" step="1" value={settings.cost_limit_usd} onChange={(e) => setSettings({...settings, cost_limit_usd: +e.target.value})} className="w-full h-1.5 bg-surface rounded-lg appearance-none cursor-pointer accent-status-success" />
                    <button
                      onClick={async () => {
                        try {
                          await fetch('/v1/cost/limit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ limit_usd: settings.cost_limit_usd }) });
                          alert('Limite guardado: $' + settings.cost_limit_usd);
                        } catch(e) { alert('Error de conexion'); }
                      }}
                      className="w-full py-2 bg-status-success/10 text-status-success border border-status-success/20 rounded-lg text-xs font-black uppercase tracking-widest hover:bg-status-success hover:text-white transition-all"
                    >Guardar Limite</button>
                 </div>
              </section>
           </div>

           <div className="space-y-6">
              <section className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
                 <h3 className="text-xs font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                    <Brain size={16} className="text-accent-secondary" /> Inteligencia & RAG
                 </h3>
                 <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 rounded-xl bg-surface border border-border-subtle">
                       <div>
                          <div className="text-sm font-bold text-text-primary">Inyección RAG Automática</div>
                          <div className="text-[10px] text-text-muted">Inyecta contexto de la base de conocimientos en cada chat.</div>
                       </div>
                       <button 
                        onClick={toggleRag}
                        className={`w-12 h-6 rounded-full transition-all relative ${settings.rag_enabled ? 'bg-status-success' : 'bg-border-subtle'}`}>
                          <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${settings.rag_enabled ? 'left-7' : 'left-1'}`}></div>
                       </button>
                    </div>
                    <div className="flex items-center justify-between p-4 rounded-xl bg-surface border border-border-subtle opacity-50">
                       <div>
                          <div className="text-sm font-bold text-text-primary">Reasoning Stripper</div>
                          <div className="text-[10px] text-text-muted">Oculta los tokens de razonamiento en la salida final.</div>
                       </div>
                       <div className="w-12 h-6 rounded-full bg-status-success relative">
                          <div className="absolute top-1 left-7 w-4 h-4 bg-white rounded-full"></div>
                       </div>
                    </div>
                 </div>
              </section>

              <section className="glass-panel p-6 rounded-2xl border border-border-subtle space-y-6">
                 <h3 className="text-xs font-black text-text-primary uppercase tracking-widest flex items-center gap-2">
                    <Globe size={16} className="text-accent-primary" /> Red & Proxy
                 </h3>
                 <div className="space-y-4">
                    <div className="flex justify-between items-center text-sm">
                       <span className="text-text-muted font-bold">Bridge Port</span>
                       <span className="font-mono text-accent-primary">7860</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                       <span className="text-text-muted font-bold">CORS Strategy</span>
                       <span className="font-mono text-status-success">WILD_OPEN (*)</span>
                    </div>
                 </div>
              </section>
           </div>

        </div>

      </div>
    </div>
  );
};

const KeyInput = ({ label, onSave }: any) => {
  const [val, setVal] = useState('');
  return (
    <div className="space-y-2">
       <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">{label}</div>
       <div className="flex gap-2">
          <input 
            type="password" 
            placeholder="sk-..." 
            value={val}
            onChange={(e) => setVal(e.target.value)}
            className="flex-1 bg-surface border border-border-subtle rounded-lg px-3 py-2 text-xs text-text-primary outline-none focus:border-accent-primary" 
          />
          <button 
            onClick={() => { onSave(val); setVal(''); }}
            className="p-2 rounded-lg bg-surface border border-border-subtle text-text-muted hover:text-accent-primary transition-all"
          >
             <Save size={16} />
          </button>
       </div>
    </div>
  );
}
