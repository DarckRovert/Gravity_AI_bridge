import { useEffect, useState } from 'react';
import { Gamepad2, Play, Square, Activity, Users, Terminal, Save, Key } from 'lucide-react';

export const GameServers = () => {
  const [servers, setServers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [regUser, setRegUser] = useState('');
  const [regPass, setRegPass] = useState('');

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:7860/v1/gameserver/status');
      if (res.ok) {
        const data = await res.json();
        // El backend devuelve { servers: { id: status_obj, ... } }
        const srvList = Object.entries(data?.servers || {}).map(([id, s]) => ({
          id,
          name: (s as any).display_name,
          online: (s as any).world_alive,
          latency: (s as any).latency_ms || 0,
          players: (s as any).players_count || 0
        }));
        setServers(srvList);
      }
    } catch (e) {} finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const iv = setInterval(fetchStatus, 10000);
    return () => clearInterval(iv);
  }, []);

  const toggleServer = async (id: string, action: 'start' | 'stop') => {
    try {
      const res = await fetch(`http://localhost:7860/v1/gameserver/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server: id })
      });
      if (!res.ok) {
        const data = await res.json();
        alert(data.error || `Error al ${action} el servidor`);
      }
      fetchStatus();
    } catch (e) {
      alert(`Fallo de conexión con el puente`);
    }
  };

  const handleBackup = async () => {
    try {
      const res = await fetch('http://localhost:7860/v1/gameserver/backup', { method: 'POST' });
      const data = await res.json();
      alert(data.msg || data.error || 'Backup iniciado');
    } catch(e) {
      alert('Error ejecutando backup');
    }
  };

  const handleRegister = async () => {
    if(!regUser || !regPass) return;
    try {
      const res = await fetch('http://localhost:7860/v1/gameserver/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server: 'wow_vanilla', username: regUser, password: regPass })
      });
      const data = await res.json();
      alert(data.note || data.error || 'Proceso finalizado');
      setRegUser(''); setRegPass('');
    } catch(e) {
      alert('Error registrando cuenta');
    }
  };

  const handleCommand = async (id: string) => {
    const cmd = prompt(`Ingresa un comando de consola para ${id}:`);
    if(!cmd) return;
    try {
      const res = await fetch('http://localhost:7860/v1/gameserver/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server: id, command: cmd })
      });
      const data = await res.json();
      alert(data.result || data.error || 'Comando enviado');
    } catch(e) {
      alert('Error enviando comando');
    }
  };

  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-surface border border-border-subtle">
              <Gamepad2 className="text-accent-secondary" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">Game Servers</h1>
              <p className="text-text-muted mt-1 font-medium">Control de instancias locales de MaNGOS World of Warcraft.</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button 
              onClick={() => alert('Información: Configura el archivo realmlist.wtf dentro de tu cliente de World of Warcraft colocando: "set realmlist 127.0.0.1"')}
              className="px-4 py-2 rounded-xl bg-surface border border-border-subtle text-sm font-bold hover:bg-card transition-all"
            >
              Configurar Realmlist
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6">
          {loading ? (
            <div className="py-20 text-center text-text-muted animate-pulse">Consultando estado de los servicios...</div>
          ) : servers.map((srv) => (
            <div key={srv.id} className="glass-panel p-6 rounded-2xl border border-border-subtle flex flex-col md:flex-row gap-6 items-center">
              
              <div className="flex items-center gap-6 flex-1">
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center border-2 shadow-lg
                  ${srv.online ? 'bg-status-success/10 border-status-success text-status-success shadow-status-success/20' : 'bg-surface border-border-subtle text-text-muted'}`}>
                  <Gamepad2 size={32} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-extrabold text-text-primary">{srv.name}</h3>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-black tracking-widest uppercase
                      ${srv.online ? 'bg-status-success text-black' : 'bg-status-error/10 text-status-error border border-status-error/20'}`}>
                      {srv.online ? 'ONLINE' : 'OFFLINE'}
                    </span>
                  </div>
                  <div className="text-sm text-text-muted mt-1 font-medium flex items-center gap-4">
                    <span className="flex items-center gap-1.5"><Activity size={14} /> Latencia: {srv.latency || '--'}ms</span>
                    <span className="flex items-center gap-1.5"><Users size={14} /> Jugadores: {srv.players || 0}</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 w-full md:w-auto">
                {srv.online ? (
                  <button 
                    onClick={() => toggleServer(srv.id, 'stop')}
                    className="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 py-3 bg-status-error/10 text-status-error border border-status-error/20 rounded-xl font-bold hover:bg-status-error hover:text-white transition-all shadow-lg"
                  >
                    <Square size={16} fill="currentColor" /> Detener
                  </button>
                ) : (
                  <button 
                    onClick={() => toggleServer(srv.id, 'start')}
                    className="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 py-3 bg-status-success/10 text-status-success border border-status-success/20 rounded-xl font-bold hover:bg-status-success hover:text-white transition-all shadow-lg"
                  >
                    <Play size={16} fill="currentColor" /> Iniciar
                  </button>
                )}
                <button 
                  onClick={() => handleCommand(srv.id)}
                  className="p-3 bg-surface border border-border-subtle rounded-xl text-text-muted hover:text-text-primary transition-all"
                  title="Enviar comando a consola"
                >
                  <Terminal size={20} />
                </button>
              </div>

            </div>
          ))}
        </div>

        {/* Global Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-card p-6 border-accent-secondary/20 bg-accent-secondary/5 rounded-2xl">
            <h4 className="text-sm font-bold text-text-primary mb-4 flex items-center gap-2"><Key size={16} className="text-accent-secondary" /> Registro de Cuentas</h4>
            <div className="space-y-3">
              <input 
                type="text" placeholder="Usuario" 
                value={regUser} onChange={e => setRegUser(e.target.value)}
                className="w-full bg-card border border-border-subtle rounded-lg p-2 text-sm outline-none focus:border-accent-secondary"
              />
              <input 
                type="password" placeholder="Contraseña" 
                value={regPass} onChange={e => setRegPass(e.target.value)}
                className="w-full bg-card border border-border-subtle rounded-lg p-2 text-sm outline-none focus:border-accent-secondary"
              />
              <button 
                onClick={handleRegister}
                disabled={!regUser || !regPass}
                className="w-full py-2 bg-accent-secondary text-white text-xs font-bold rounded-lg hover:bg-accent-secondary/80 transition-all disabled:opacity-50"
              >
                Crear Cuenta Local
              </button>
            </div>
          </div>
          <div className="glass-card p-6 border-accent-primary/20 bg-accent-primary/5 rounded-2xl flex flex-col justify-between">
            <div>
              <h4 className="text-sm font-bold text-text-primary mb-4 flex items-center gap-2"><Save size={16} className="text-accent-primary" /> Auto-Backup</h4>
              <p className="text-xs text-text-muted mb-4">Base de datos de personajes sincronizada. Puedes forzar un backup manual de la base de datos SQL del servidor en cualquier momento.</p>
            </div>
            <button 
              onClick={handleBackup}
              className="w-full py-2 bg-accent-primary/10 border border-accent-primary/20 text-accent-primary text-xs font-bold rounded-lg hover:bg-accent-primary hover:text-white transition-all"
            >
              Realizar Backup Ahora
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
