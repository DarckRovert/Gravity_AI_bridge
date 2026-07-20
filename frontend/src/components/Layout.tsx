import React, { useEffect, useState } from 'react';
import type { PanelId, GravityContext } from '../types';
import { 
  MessageSquare, Home, Palette, Image as ImageIcon, Video, Rocket, 
  Gamepad2, Bot, Cpu, DollarSign, Activity, Save, BookOpen, 
  Plug, Wrench, Zap, Bug, ShieldAlert, Wifi, Shield, FileText, Settings, Menu, Bell,
  TrendingUp, Video as VideoIcon, Radio, Target, Code2, Ghost,
  Dices, PlayCircle, Brain, Newspaper, Box, BrainCircuit, Lock, Mic
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
        const res = await fetch('/v1/gravity/context');
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
      <header className="flex items-center px-6 h-16 bg-surface/80 backdrop-blur-2xl border-b border-border-subtle shrink-0 z-20 shadow-[0_4px_30px_rgba(0,0,0,0.1)]">
        <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 mr-4 hover:bg-card rounded-xl transition-all duration-300 hover:shadow-[0_0_15px_rgba(129,140,248,0.2)]">
          <Menu size={22} className="text-accent-primary" />
        </button>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg overflow-hidden bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center shadow-[0_0_20px_rgba(192,132,252,0.4)]">
            <img 
              src="/gravity_logo.png" 
              alt="Gravity Logo" 
              className="w-full h-full object-cover"
              onError={(e) => {
                // Fallback si la imagen no existe
                e.currentTarget.style.display = 'none';
                e.currentTarget.parentElement?.classList.add('fallback-icon');
              }}
            />
            <Bot size={18} className="text-white hidden [.fallback-icon_&]:block" />
          </div>
          <div className="text-xl font-black tracking-tighter bg-gradient-to-r from-white via-accent-primary to-accent-secondary bg-clip-text text-transparent drop-shadow-sm">
            GRAVITY <span className="font-light opacity-80">V30.0 MYTHOS</span>
          </div>
        </div>
        
        <div className="hidden md:flex items-center ml-auto gap-6 text-sm font-medium">
          <div className="flex items-center gap-2"><Cpu size={16} className="text-text-muted"/> <span>{ctx?.hardware.cpu_percent || '--'}% CPU</span></div>
          <div className="flex items-center gap-2"><Activity size={16} className="text-text-muted"/> <span>{ctx?.hardware.ram_percent || '--'}% RAM</span></div>
          
          {(ctx?.hardware.ram_percent || 0) > 70 && (
            <button 
              onClick={async () => {
                if(!confirm("¿Liberar RAM deteniendo motores IA?")) return;
                await fetch('/v1/ai/stop', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ provider: 'Fooocus' }) });
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

          <button className="p-2 hover:bg-card rounded-lg transition-colors relative md:hidden ml-auto">
            <Bell size={18} />
          </button>
        </div>
        <button className="hidden md:block p-2 hover:bg-card rounded-lg transition-colors relative ml-4">
          <Bell size={18} />
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden relative p-4 gap-4">
        {/* Sidebar */}
        <aside className={`${isSidebarOpen ? 'w-64' : 'w-0 opacity-0'} absolute md:relative z-40 h-full transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] shrink-0 glass-panel rounded-2xl flex flex-col`}>
          <div className="p-4 flex-1 overflow-y-auto scrollbar-hide">
            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2 px-2">Principal</div>
            <NavItem id="chat" icon={MessageSquare} label="Chat Auditor" />
            <NavItem id="home" icon={Home} label="Mission Control" />
            <NavItem id="vision" icon={Palette} label="Vision Studio" />
            <NavItem id="queue" icon={ImageIcon} label="Image Queue" />
            <NavItem id="video" icon={Video} label="Video Studio" />
            <NavItem id="v2v" icon={VideoIcon} label="V2V Live Studio" />
            <NavItem id="obs" icon={Radio} label="OBS Studio" />
            <NavItem id="imagelab" icon={Palette} label="Image Lab" />
            <NavItem id="deploy" icon={Rocket} label="Deploy" />
            <NavItem id="gameserver" icon={Gamepad2} label="Game Servers" />

            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mt-6 mb-2 px-2">IA & Sistema</div>
            <NavItem id="jarvis" icon={Mic} label="J.A.R.V.I.S Sensory Net" />
            <NavItem id="tiktokradar" icon={Radio} label="TikTok Radar" />
            <NavItem id="tinka" icon={Dices} label="La Tinka Engine" />
            <NavItem id="multiagent" icon={Bot} label="Multi-Agent" />
            <NavItem id="hardware" icon={Cpu} label="Hardware" />
            <NavItem id="cost" icon={DollarSign} label="Cost Center" />
            <NavItem id="watchdog" icon={Activity} label="Watchdog" />
            <NavItem id="modelhub" icon={Box} label="Model Hub" />
            <NavItem id="autonomy" icon={Brain} label="Autonomy Engine" badge={(ctx as any)?.autonomy_patches} />

            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mt-6 mb-2 px-2">Herramientas</div>
            <NavItem id="sessions" icon={Save} label="Sessions" />
            <NavItem id="rag" icon={BookOpen} label="RAG" />
            <NavItem id="memorystudio" icon={BrainCircuit} label="Memory Studio" />
            <NavItem id="mcp" icon={Plug} label="MCP Servers" />
            <NavItem id="tools" icon={Wrench} label="Tools" />
            <NavItem id="tools-pro" icon={Zap} label="Tools Pro" />
            <NavItem id="firecrawl" icon={Bug} label="Firecrawl" />

            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mt-6 mb-2 px-2">Monitoreo</div>
            <NavItem id="hitl" icon={ShieldAlert} label="HITL Approval" badge={ctx?.security_alerts} />
            <NavItem id="status" icon={Wifi} label="System Status" />
            <NavItem id="security" icon={Shield} label="Security" />
            <NavItem id="agentshield" icon={Lock} label="AgentShield" />
            <NavItem id="audit" icon={FileText} label="Audit Log" />
            <NavItem id="config" icon={Settings} label="Configuración" />

            <div className="text-[11px] font-bold uppercase tracking-wider text-text-muted mt-6 mb-2 px-2">💰 Monetización</div>
            <NavItem id="youtubeanalyzer" icon={PlayCircle} label="YouTube Analyzer" />
            <NavItem id="monetization" icon={TrendingUp} label="Monetization Hub" />
            <NavItem id="bountyhunter" icon={Target} label="Bounty Hunter" />
            <NavItem id="softwarefactory" icon={Code2} label="Dev Studio / Fábrica" />
            <NavItem id="infiltrator" icon={Ghost} label="Infiltrador (AGI)" />
            <NavItem id="journalist" icon={Newspaper} label="El Periodista" />
            <NavItem id="tiktokradar" icon={Radio} label="TikTok Radar (GTLIS)" />
          </div>

          <div className="p-4 shrink-0 border-t border-border-subtle bg-surface/30 rounded-b-2xl">
            <div className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-3 flex items-center gap-2">
              <Activity size={12} className="text-accent-tertiary" /> Modelo Activo
            </div>
            <div className="relative group overflow-hidden rounded-xl border border-border-subtle bg-card/50 p-3 transition-all duration-300 hover:border-accent-primary/50 hover:shadow-[0_0_20px_rgba(129,140,248,0.15)]">
              <div className="absolute inset-0 bg-gradient-to-r from-accent-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative z-10">
                <div className="text-sm font-bold text-text-primary truncate drop-shadow-md">{ctx?.active_model || 'Detectando...'}</div>
                <div className="text-xs text-text-muted mt-1 font-medium">{ctx?.active_provider ? `Activo: ${ctx.active_provider}` : 'Auto-Routing'}</div>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 relative overflow-hidden glass-panel rounded-2xl">
          {children}
        </main>
      </div>
    </div>
  );
};
