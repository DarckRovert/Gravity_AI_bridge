import React, { useEffect, useState } from 'react';
import type { PanelId, GravityContext } from '../types';
import { 
  MessageSquare, Home, Palette, Image as ImageIcon, Video, Rocket, 
  Gamepad2, Bot, Cpu, DollarSign, Activity, Save, BookOpen, 
  Plug, Wrench, Zap, Bug, ShieldAlert, Wifi, Shield, FileText, Settings, Menu, Bell,
  TrendingUp
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activePanel: PanelId;
  setActivePanel: (id: PanelId) => void;
}

export const Layout: React.FC<LayoutProps> = ({ children, activePanel, setActivePanel }) => {
  const [ctx, setCtx] = useState<GravityContext | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    const fetchCtx = async () => {
      try {
        const res = await fetch('http://localhost:7860/v1/gravity/context');
        if (res.ok) setCtx(await res.json());
      } catch (e) {
        console.warn('Bridge offline or not accessible:', e);
      }
    };
    fetchCtx();
    const iv = setInterval(fetchCtx, 5000);
    return () => clearInterval(iv);
  }, []);

  const NavItem = ({ id, icon: Icon, label, badge }: { id: PanelId, icon: React.ElementType, label: string, badge?: number }) => (
    <div 
      onClick={() => setActivePanel(id)}
      className={`flex items-center gap-3 px-3 py-2.5 mb-1 rounded-lg cursor-pointer transition-all duration-200 text-sm font-medium
        ${activePanel === id 
          ? 'bg-gradient-to-r from-accent-primary/20 to-transparent text-text-primary border-l-4 border-accent-primary' 
          : 'text-text-muted hover:bg-card hover:text-text-primary'}`}
    >
      <Icon size={18} className={activePanel === id ? 'text-accent-primary' : ''} />
      <span className="flex-1">{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="bg-status-warning text-black text-[10px] font-bold px-1.5 py-0.5 rounded-full">{badge}</span>
      )}
    </div>
  );

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-bg text-text-primary">
      {/* Topbar */}
      <header className="flex items-center px-4 h-14 bg-surface backdrop-blur-xl border-b border-border-subtle shrink-0 z-20">
        <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 mr-2 hover:bg-card rounded-lg transition-colors">
          <Menu size={20} />
        </button>
        <div className="text-lg font-extrabold tracking-tight bg-gradient-to-r from-accent-primary to-accent-secondary bg-clip-text text-transparent">
          GRAVITY V13.0 PRO
        </div>
        
        <div className="flex items-center ml-auto gap-6 text-sm font-medium">
          <div className="flex items-center gap-2"><Cpu size={16} className="text-text-muted"/> <span>{ctx?.hardware.cpu_percent || '--'}% CPU</span></div>
          <div className="flex items-center gap-2"><Activity size={16} className="text-text-muted"/> <span>{ctx?.hardware.ram_percent || '--'}% RAM</span></div>
          
          {(ctx?.hardware.ram_percent || 0) > 70 && (
            <button 
              onClick={async () => {
                if(!confirm("¿Liberar RAM deteniendo motores IA?")) return;
                await fetch('http://localhost:7860/v1/ai/stop', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ provider: 'Fooocus' }) });
                window.location.reload();
              }}
              className="flex items-center gap-2 px-3 py-1 rounded-full bg-status-error/20 border border-status-error/40 text-status-error text-xs font-black animate-pulse hover:bg-status-error hover:text-white transition-all"
            >
              <Zap size={12} /> LIBERAR RAM
            </button>
          )}

          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-accent-primary/10 border border-accent-primary/30">
            <div className="w-2 h-2 rounded-full bg-accent-primary animate-blink"></div>
            <span className="text-xs font-bold text-accent-primary">BRAIN SYNC</span>
          </div>
          
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-status-success/15 border border-status-success/30">
            <div className="w-2 h-2 rounded-full bg-status-success shadow-[0_0_8px_var(--color-status-success)]"></div>
            <span className="text-xs font-bold text-status-success">ONLINE</span>
          </div>

          <button className="p-2 hover:bg-card rounded-lg transition-colors relative">
            <Bell size={18} />
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className={`${isSidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 shrink-0 border-r border-border-subtle bg-surface/50 backdrop-blur-md overflow-y-auto scrollbar-hide flex flex-col`}>
          <div className="p-4 flex-1">
            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2 px-2">Principal</div>
            <NavItem id="chat" icon={MessageSquare} label="Chat Auditor" />
            <NavItem id="home" icon={Home} label="Mission Control" />
            <NavItem id="vision" icon={Palette} label="Vision Studio" />
            <NavItem id="queue" icon={ImageIcon} label="Image Queue" />
            <NavItem id="video" icon={Video} label="Video Studio" />
            <NavItem id="imagelab" icon={Palette} label="Image Lab" />
            <NavItem id="deploy" icon={Rocket} label="Deploy" />
            <NavItem id="gameserver" icon={Gamepad2} label="Game Servers" />

            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mt-6 mb-2 px-2">IA & Sistema</div>
            <NavItem id="multiagent" icon={Bot} label="Multi-Agent" />
            <NavItem id="hardware" icon={Cpu} label="Hardware" />
            <NavItem id="cost" icon={DollarSign} label="Cost Center" />
            <NavItem id="watchdog" icon={Activity} label="Watchdog" />

            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mt-6 mb-2 px-2">Herramientas</div>
            <NavItem id="sessions" icon={Save} label="Sessions" />
            <NavItem id="rag" icon={BookOpen} label="RAG" />
            <NavItem id="mcp" icon={Plug} label="MCP Servers" />
            <NavItem id="tools" icon={Wrench} label="Tools" />
            <NavItem id="tools-pro" icon={Zap} label="Tools Pro" />
            <NavItem id="firecrawl" icon={Bug} label="Firecrawl" />

            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mt-6 mb-2 px-2">Monitoreo</div>
            <NavItem id="hitl" icon={ShieldAlert} label="HITL Approval" badge={ctx?.security_alerts} />
            <NavItem id="status" icon={Wifi} label="System Status" />
            <NavItem id="security" icon={Shield} label="Security" />
            <NavItem id="audit" icon={FileText} label="Audit Log" />
            <NavItem id="config" icon={Settings} label="Configuración" />

            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mt-6 mb-2 px-2">💰 Monetización</div>
            <NavItem id="monetization" icon={TrendingUp} label="Monetization Hub" />
          </div>

          <div className="p-4 shrink-0 border-t border-border-subtle bg-surface">
            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2">Modelo Activo</div>
            <div className="glass-card p-3 rounded-xl border border-border-subtle bg-card shadow-md">
              <div className="text-sm font-bold text-text-primary truncate">{ctx?.active_model || 'Detectando...'}</div>
              <div className="text-xs text-text-muted mt-1">{ctx?.active_provider ? `Activo: ${ctx.active_provider}` : 'Auto-Routing'}</div>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 relative overflow-hidden bg-bg/50">
          {children}
        </main>
      </div>
    </div>
  );
};
