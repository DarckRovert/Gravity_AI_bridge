import { useEffect, useState, useRef } from 'react';
import { Mic, Activity, Power, PowerOff, Zap, BrainCircuit, Terminal } from 'lucide-react';

interface LogEntry {
  id: string;
  type: 'stt' | 'tts' | 'system' | 'error';
  content: string;
  timestamp: Date;
}

export const JarvisPanel = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const speakTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const addLog = (type: LogEntry['type'], content: string) => {
    setLogs(prev => [...prev, { id: Math.random().toString(36).substr(2, 9), type, content, timestamp: new Date() }]);
  };

  useEffect(() => {

    const connectWS = () => {
      // Connect directly to the Sensory Bus on port 9999
      const ws = new WebSocket(`ws://${window.location.hostname}:9999`);

      ws.onopen = () => {
        setConnected(true);
        setStatus('listening');
        addLog('system', 'Neural Link established. Sensory Bus connected (Port 9999).');
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        
        // Announce dashboard presence
        ws.send(JSON.stringify({
          type: "system_status",
          payload: "Dashboard monitor joined the Sensory Net."
        }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'voice_input') {
            setStatus('thinking');
            addLog('stt', data.payload || data.text || JSON.stringify(data));
          } else if (data.type === 'voice_output') {
            setStatus('speaking');
            addLog('tts', data.payload || data.text || JSON.stringify(data));
            
            if (speakTimeoutRef.current) clearTimeout(speakTimeoutRef.current);
            speakTimeoutRef.current = setTimeout(() => setStatus('listening'), 3000); // Vuelve a escuchar después de hablar
          } else if (data.type === 'system_status') {
            addLog('system', data.payload || JSON.stringify(data));
            if (String(data.payload).includes('Escuchando')) setStatus('listening');
          } else {
            addLog('system', `[${data.type}] ` + (data.payload || JSON.stringify(data)));
          }
        } catch (e) {
          addLog('error', `Unparseable signal: ${event.data}`);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        setStatus('idle');
        addLog('error', 'Sensory Net disconnected. Attempting to reconnect in 5s...');
        reconnectTimeoutRef.current = setTimeout(connectWS, 5000);
      };

      ws.onerror = () => {
        // Will close and reconnect
      };

      wsRef.current = ws;
    };

    connectWS();

    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null; // Evitar reconexión zombie
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (speakTimeoutRef.current) {
        clearTimeout(speakTimeoutRef.current);
      }
    };
  }, []);

  // Auto-scroll to bottom of logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide bg-gradient-to-br from-bg via-bg/95 to-bg-surface/90 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className={`p-3.5 rounded-2xl bg-surface/80 border border-border-subtle shadow-xl backdrop-blur-md transition-colors ${connected ? 'border-accent-primary/50' : 'border-status-error/50'}`}>
              <BrainCircuit className={connected ? "text-accent-primary animate-pulse" : "text-status-error"} size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary bg-gradient-to-r from-text-primary via-text-primary to-accent-primary/80 bg-clip-text">
                J.A.R.V.I.S Sensory Net
              </h1>
              <p className="text-text-muted mt-1 font-medium text-sm">
                Monitoreo directo en tiempo real del bus de voz y loop cognitivo local.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className={`px-4 py-2 rounded-xl flex items-center gap-2 font-bold text-sm border shadow-lg backdrop-blur-md transition-all ${
              connected ? 'bg-accent-primary/10 border-accent-primary/30 text-accent-primary' : 'bg-status-error/10 border-status-error/30 text-status-error'
            }`}>
              {connected ? (
                <>
                  <div className="w-2 h-2 rounded-full bg-accent-primary animate-ping" />
                  Sensory Bus Online
                </>
              ) : (
                <>
                  <PowerOff size={16} />
                  Offline
                </>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Status Column */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-surface/60 backdrop-blur-md border border-border-subtle rounded-2xl p-6 shadow-xl relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent-primary/20 via-accent-primary to-accent-primary/20 opacity-50" />
              
              <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-6 flex items-center gap-2">
                <Activity size={16} /> Estado Cognitivo
              </h3>

              <div className="flex flex-col items-center justify-center py-6 gap-4">
                <div className="relative">
                  {/* Status Indicator Core */}
                  <div className={`w-24 h-24 rounded-full flex items-center justify-center border-2 shadow-[0_0_30px_rgba(0,0,0,0.5)] transition-all duration-500 ${
                    status === 'idle' ? 'bg-surface border-border-subtle text-text-muted' :
                    status === 'listening' ? 'bg-status-info/10 border-status-info text-status-info shadow-[0_0_40px_rgba(59,130,246,0.3)]' :
                    status === 'thinking' ? 'bg-status-warning/10 border-status-warning text-status-warning shadow-[0_0_40px_rgba(234,179,8,0.3)] animate-pulse' :
                    status === 'speaking' ? 'bg-accent-primary/10 border-accent-primary text-accent-primary shadow-[0_0_40px_rgba(168,85,247,0.3)]' : ''
                  }`}>
                    {status === 'idle' && <Power size={32} />}
                    {status === 'listening' && <Mic size={32} className="animate-pulse" />}
                    {status === 'thinking' && <BrainCircuit size={32} />}
                    {status === 'speaking' && <Zap size={32} className="animate-bounce" />}
                  </div>
                  
                  {/* Rotating rings when active */}
                  {status !== 'idle' && (
                    <>
                      <div className={`absolute top-[-10px] left-[-10px] right-[-10px] bottom-[-10px] border-2 rounded-full border-t-transparent border-l-transparent animate-spin duration-1000 ${
                        status === 'listening' ? 'border-status-info' :
                        status === 'thinking' ? 'border-status-warning' :
                        status === 'speaking' ? 'border-accent-primary' : ''
                      }`} />
                    </>
                  )}
                </div>
                <div className="text-xl font-extrabold capitalize tracking-wide mt-2">
                  {status === 'idle' ? 'En Espera' : 
                   status === 'listening' ? 'Escuchando...' : 
                   status === 'thinking' ? 'Procesando...' : 
                   status === 'speaking' ? 'Respondiendo' : ''}
                </div>
              </div>
            </div>
            
            <div className="bg-surface/60 backdrop-blur-md border border-border-subtle rounded-2xl p-6 shadow-xl">
               <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-4 flex items-center gap-2">
                <Terminal size={16} /> Controles
              </h3>
              <p className="text-xs text-text-muted mb-4 leading-relaxed">
                El demonio de voz VAD opera como proceso independiente. Lanza <strong>Launch_JARVIS.bat</strong> para que este panel pueda interceptar su telemetría.
              </p>
            </div>
          </div>

          {/* Logs Column */}
          <div className="lg:col-span-3 bg-[#0a0a0c] border border-border-subtle rounded-2xl shadow-2xl overflow-hidden flex flex-col min-h-[600px]">
            <div className="bg-surface/80 border-b border-border-subtle p-4 flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold">
                <Activity size={16} className="text-accent-primary" />
                <span>Flujo de Datos Neuronales</span>
              </div>
              <button 
                onClick={() => setLogs([])}
                className="text-xs px-3 py-1.5 rounded bg-surface border border-border-subtle hover:border-text-muted hover:text-text-primary transition-colors text-text-muted font-medium"
              >
                Limpiar Terminal
              </button>
            </div>

            <div className="flex-1 p-6 overflow-y-auto space-y-4 font-mono text-sm">
              {logs.length === 0 ? (
                <div className="h-full flex items-center justify-center text-text-muted/50 italic font-sans">
                  Esperando interceptaciones del bus...
                </div>
              ) : (
                logs.map(log => (
                  <div key={log.id} className="animate-in fade-in slide-in-from-left-2 duration-300">
                    <div className="flex items-start gap-3">
                      <div className="shrink-0 pt-0.5">
                        {log.type === 'stt' && <span className="text-status-info">{'>>'}</span>}
                        {log.type === 'tts' && <span className="text-accent-primary">{'<<'}</span>}
                        {log.type === 'system' && <span className="text-text-muted">{'--'}</span>}
                        {log.type === 'error' && <span className="text-status-error">{'!!'}</span>}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-baseline gap-2 mb-1">
                          <span className="text-xs text-text-muted/70">
                            {log.timestamp.toLocaleTimeString()}
                          </span>
                          <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                            log.type === 'stt' ? 'bg-status-info/20 text-status-info' :
                            log.type === 'tts' ? 'bg-accent-primary/20 text-accent-primary' :
                            log.type === 'system' ? 'bg-surface text-text-muted' :
                            log.type === 'error' ? 'bg-status-error/20 text-status-error' : ''
                          }`}>
                            {log.type === 'stt' ? 'Voz (User)' :
                             log.type === 'tts' ? 'Voz (JARVIS)' :
                             log.type === 'system' ? 'Sistema' : 'Error'}
                          </span>
                        </div>
                        <div className={`leading-relaxed whitespace-pre-wrap ${
                            log.type === 'stt' ? 'text-text-primary' :
                            log.type === 'tts' ? 'text-accent-secondary' :
                            log.type === 'system' ? 'text-text-muted' :
                            log.type === 'error' ? 'text-status-error' : ''
                        }`}>
                          {log.content}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
