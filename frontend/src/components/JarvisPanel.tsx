import { useEffect, useState, useRef } from 'react';
import { Mic, MicOff, Activity, Power, PowerOff, Zap, BrainCircuit, Terminal, Send, Sliders } from 'lucide-react';

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
  
  // Nuevos estados para control y monitoreo real del demonio
  const [daemonAlive, setDaemonAlive] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [threshold, setThreshold] = useState(0.003);
  const [manualText, setManualText] = useState('');
  
  const [backendOnline, setBackendOnline] = useState(false);
  const [processing, setProcessing] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const speakTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Timers del Watchdog
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const watchdogTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

        // Iniciar pings periódicos al demonio de Python
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "voice_daemon_ping" }));
          }
        }, 2000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'voice_daemon_status') {
             // El demonio está vivo y nos reporta su estado actual
             setDaemonAlive(true);
             setIsPaused(data.paused);
             setThreshold(data.threshold);
             
             // Reiniciar el contador de timeout (Watchdog)
             if (watchdogTimeoutRef.current) clearTimeout(watchdogTimeoutRef.current);
             watchdogTimeoutRef.current = setTimeout(() => {
                setDaemonAlive(false); // Si pasan 5s sin respuesta, el demonio murió
             }, 5000);

          } else if (data.type === 'voice_input') {
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
            // Ignorar los propios pings y comandos en la terminal para no hacer spam visual
            if (data.type !== 'voice_daemon_ping' && data.type !== 'voice_daemon_cmd' && data.type !== 'voice_daemon_status') {
               addLog('system', `[${data.type}] ` + (data.payload || JSON.stringify(data)));
            }
          }
        } catch (e) {
          addLog('error', `Unparseable signal: ${event.data}`);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        setDaemonAlive(false);
        setStatus('idle');
        addLog('error', 'Sensory Net disconnected. Attempting to reconnect in 5s...');
        
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        if (watchdogTimeoutRef.current) clearTimeout(watchdogTimeoutRef.current);
        
        reconnectTimeoutRef.current = setTimeout(connectWS, 5000);
      };

      ws.onerror = () => {
        // Will close and reconnect
      };

      wsRef.current = ws;
    };

    connectWS();
    
    const fetchBackendStatus = async () => {
      try {
        const res = await fetch('/v1/jarvis/status');
        if (res.ok) {
          const data = await res.json();
          setBackendOnline(data.online);
        }
      } catch (e) {}
    };
    fetchBackendStatus();
    const statusInterval = setInterval(fetchBackendStatus, 3000);

    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null; // Evitar reconexión zombie
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (speakTimeoutRef.current) clearTimeout(speakTimeoutRef.current);
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (watchdogTimeoutRef.current) clearTimeout(watchdogTimeoutRef.current);
      clearInterval(statusInterval);
    };
  }, []);

  const handleStart = async () => {
    setProcessing(true);
    try { await fetch('/v1/jarvis/start', { method: 'POST' }); }
    finally { setTimeout(() => setProcessing(false), 2000); }
  };

  const handleStop = async () => {
    setProcessing(true);
    try { await fetch('/v1/jarvis/stop', { method: 'POST' }); }
    finally { setTimeout(() => setProcessing(false), 2000); }
  };

  // Auto-scroll to bottom of logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Controlador para enviar input de texto como si fuera STT
  const sendManualInput = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualText.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    
    wsRef.current.send(JSON.stringify({
      type: "voice_input",
      text: manualText.trim()
    }));
    
    // Simulate thinking state immediately for UX feedback
    setStatus('thinking');
    addLog('stt', manualText.trim());
    
    setManualText('');
  };

  // Botón para pausar el micrófono remotamente
  const togglePause = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({
      type: "voice_daemon_cmd",
      action: isPaused ? "resume" : "pause"
    }));
  };

  // Slider para la sensibilidad de VAD
  const updateThreshold = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setThreshold(val); // Optimistic UI update
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({
      type: "voice_daemon_cmd",
      action: "set_threshold",
      value: val
    }));
  };

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
                Panel de control avanzado y telemetría bidireccional.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Server Status Badge */}
            <div className={`px-4 py-2 rounded-xl flex items-center gap-2 font-bold text-sm border shadow-lg backdrop-blur-md transition-all ${
              connected ? 'bg-accent-primary/10 border-accent-primary/30 text-accent-primary' : 'bg-status-error/10 border-status-error/30 text-status-error'
            }`}>
              {connected ? (
                <><div className="w-2 h-2 rounded-full bg-accent-primary animate-ping" /> Sensory Bus Online</>
              ) : (
                <><PowerOff size={16} /> Server Offline</>
              )}
            </div>
            
            {/* Daemon Status Badge (Watchdog) */}
            <div className={`px-4 py-2 rounded-xl flex items-center gap-2 font-bold text-sm border shadow-lg backdrop-blur-md transition-all ${
              daemonAlive ? 'bg-status-success/10 border-status-success/30 text-status-success' : 'bg-status-error/10 border-status-error/30 text-status-error'
            }`}>
              {daemonAlive ? (
                <><div className="w-2 h-2 rounded-full bg-status-success" /> Daemon Activo</>
              ) : (
                <><PowerOff size={16} /> Daemon Caído</>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Status & Controls Column */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* Cognitive State */}
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
                    status === 'listening' ? (isPaused ? 'bg-status-error/10 border-status-error text-status-error' : 'bg-status-info/10 border-status-info text-status-info shadow-[0_0_40px_rgba(59,130,246,0.3)]') :
                    status === 'thinking' ? 'bg-status-warning/10 border-status-warning text-status-warning shadow-[0_0_40px_rgba(234,179,8,0.3)] animate-pulse' :
                    status === 'speaking' ? 'bg-accent-primary/10 border-accent-primary text-accent-primary shadow-[0_0_40px_rgba(168,85,247,0.3)]' : ''
                  }`}>
                    {status === 'idle' && <Power size={32} />}
                    {status === 'listening' && (isPaused ? <MicOff size={32} /> : <Mic size={32} className="animate-pulse" />)}
                    {status === 'thinking' && <BrainCircuit size={32} />}
                    {status === 'speaking' && <Zap size={32} className="animate-bounce" />}
                  </div>
                  
                  {/* Rotating rings when active and not paused */}
                  {status !== 'idle' && !isPaused && (
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
                   status === 'listening' ? (isPaused ? 'Silenciado' : 'Escuchando...') : 
                   status === 'thinking' ? 'Procesando...' : 
                   status === 'speaking' ? 'Respondiendo' : ''}
                </div>
              </div>
            </div>
            
            {/* Remote Controls */}
            <div className="bg-surface/60 backdrop-blur-md border border-border-subtle rounded-2xl p-6 shadow-xl space-y-5">
               <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider flex items-center gap-2">
                <Sliders size={16} /> Controles Remotos
              </h3>
              
              {!backendOnline ? (
                 <div className="space-y-4">
                   <div className="p-3 bg-status-warning/10 border border-status-warning/30 rounded-xl text-xs text-status-warning/90 leading-relaxed font-medium">
                     J.A.R.V.I.S está actualmente fuera de línea.
                   </div>
                   <button 
                     onClick={handleStart}
                     disabled={processing}
                     className="w-full py-4 px-4 rounded-xl font-black uppercase tracking-widest flex items-center justify-center gap-2 transition-all bg-accent-primary/20 hover:bg-accent-primary/30 text-accent-primary border border-accent-primary/30 disabled:opacity-50 shadow-[0_0_20px_rgba(168,85,247,0.15)]"
                   >
                     <Power size={18} className={processing ? "animate-spin" : ""} />
                     {processing ? "INICIANDO..." : "INICIAR J.A.R.V.I.S"}
                   </button>
                 </div>
              ) : (
                <>
                  <button 
                     onClick={handleStop}
                     disabled={processing}
                     className="w-full mb-4 py-2 px-4 rounded-xl font-bold uppercase text-xs flex items-center justify-center gap-2 transition-all bg-status-error/10 hover:bg-status-error/20 text-status-error border border-status-error/30 disabled:opacity-50"
                   >
                     <PowerOff size={14} className={processing ? "animate-spin" : ""} />
                     {processing ? "APAGANDO..." : "APAGAR SISTEMA"}
                   </button>
                  
                  {/* Mute Button */}
                  <button 
                    onClick={togglePause}
                    className={`w-full py-3 px-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${
                      isPaused ? 'bg-status-success/20 hover:bg-status-success/30 text-status-success border border-status-success/30' : 'bg-status-error/20 hover:bg-status-error/30 text-status-error border border-status-error/30'
                    }`}
                  >
                    {isPaused ? <Mic size={18} /> : <MicOff size={18} />}
                    {isPaused ? "Reactivar Micrófono" : "Silenciar Micrófono"}
                  </button>

                  {/* Threshold Slider */}
                  <div className="space-y-3 pt-2">
                    <div className="flex justify-between text-xs font-bold text-text-muted">
                      <span>Sensibilidad (VAD)</span>
                      <span className="text-accent-primary">{threshold.toFixed(4)}</span>
                    </div>
                    <input 
                      type="range" 
                      min="0.0001" 
                      max="0.05" 
                      step="0.0001" 
                      value={threshold} 
                      onChange={updateThreshold}
                      className="w-full h-1.5 bg-bg-surface rounded-lg appearance-none cursor-pointer accent-accent-primary"
                    />
                    <p className="text-[10px] text-text-muted/60 leading-tight">
                      Aumenta si hay ruido de fondo y te interrumpe. Disminuye si le cuesta escucharte.
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Logs & Terminal Column */}
          <div className="lg:col-span-3 bg-[#0a0a0c] border border-border-subtle rounded-2xl shadow-2xl overflow-hidden flex flex-col min-h-[600px]">
            <div className="bg-surface/80 border-b border-border-subtle p-4 flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold">
                <Terminal size={16} className="text-accent-primary" />
                <span>Flujo de Datos Neuronales</span>
              </div>
              <button 
                onClick={() => setLogs([])}
                className="text-xs px-3 py-1.5 rounded bg-surface border border-border-subtle hover:border-text-muted hover:text-text-primary transition-colors text-text-muted font-medium"
              >
                Limpiar Terminal
              </button>
            </div>

            <div className="flex-1 p-6 overflow-y-auto space-y-4 font-mono text-sm pb-20">
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

            {/* Input Manual Box */}
            <div className="p-4 bg-surface/80 border-t border-border-subtle mt-auto">
              <form onSubmit={sendManualInput} className="relative flex items-center">
                 <input 
                   type="text" 
                   value={manualText}
                   onChange={e => setManualText(e.target.value)}
                   disabled={!connected}
                   placeholder="Escribe un comando manual para JARVIS..."
                   className="w-full bg-[#0a0a0c] border border-border-subtle rounded-xl py-3 pl-4 pr-12 text-sm text-text-primary placeholder:text-text-muted/50 focus:outline-none focus:border-accent-primary/50 transition-colors disabled:opacity-50"
                 />
                 <button 
                   type="submit" 
                   disabled={!manualText.trim() || !connected}
                   className="absolute right-2 p-2 rounded-lg text-text-muted hover:text-accent-primary hover:bg-accent-primary/10 disabled:opacity-50 transition-all"
                 >
                   <Send size={18} />
                 </button>
              </form>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};
