import { useState, useEffect, lazy, Suspense } from 'react';
import { Layout } from './components/Layout';

const ChatAuditor = lazy(() => import('./components/ChatAuditor').then(m => ({ default: m.ChatAuditor })));
const MissionControl = lazy(() => import('./components/MissionControl').then(m => ({ default: m.MissionControl })));
const VisionStudio = lazy(() => import('./components/VisionStudio').then(m => ({ default: m.VisionStudio })));
const ImageQueue = lazy(() => import('./components/ImageQueue').then(m => ({ default: m.ImageQueue })));
const VideoStudio = lazy(() => import('./components/VideoStudio').then(m => ({ default: m.VideoStudio })));
const V2VStudio = lazy(() => import('./components/V2VStudio').then(m => ({ default: m.V2VStudio })));
const ImageLab = lazy(() => import('./components/ImageLab').then(m => ({ default: m.ImageLab })));
const OBSStudio = lazy(() => import('./components/OBSStudio').then(m => ({ default: m.OBSStudio })));
const DeployManager = lazy(() => import('./components/DeployManager').then(m => ({ default: m.DeployManager })));
const GameServers = lazy(() => import('./components/GameServers').then(m => ({ default: m.GameServers })));
const MultiAgent = lazy(() => import('./components/MultiAgent').then(m => ({ default: m.MultiAgent })));
const HardwareMonitor = lazy(() => import('./components/HardwareMonitor').then(m => ({ default: m.HardwareMonitor })));
const CostCenter = lazy(() => import('./components/CostCenter').then(m => ({ default: m.CostCenter })));
const Watchdog = lazy(() => import('./components/Watchdog').then(m => ({ default: m.Watchdog })));
const Sessions = lazy(() => import('./components/Sessions').then(m => ({ default: m.Sessions })));
const RagIndex = lazy(() => import('./components/RagIndex').then(m => ({ default: m.RagIndex })));
const MCPServers = lazy(() => import('./components/MCPServers').then(m => ({ default: m.MCPServers })));
const Tools = lazy(() => import('./components/Tools').then(m => ({ default: m.Tools })));
const ToolsPro = lazy(() => import('./components/ToolsPro').then(m => ({ default: m.ToolsPro })));
const Firecrawl = lazy(() => import('./components/Firecrawl').then(m => ({ default: m.Firecrawl })));
const HITLApproval = lazy(() => import('./components/HITLApproval').then(m => ({ default: m.HITLApproval })));
const SystemStatus = lazy(() => import('./components/SystemStatus').then(m => ({ default: m.SystemStatus })));
const Security = lazy(() => import('./components/Security').then(m => ({ default: m.Security })));
const AuditLog = lazy(() => import('./components/AuditLog').then(m => ({ default: m.AuditLog })));
const Settings = lazy(() => import('./components/Settings').then(m => ({ default: m.Settings })));
const MonetizationHub = lazy(() => import('./components/MonetizationHub').then(m => ({ default: m.MonetizationHub })));
const BountyHunter = lazy(() => import('./components/BountyHunter').then(m => ({ default: m.BountyHunter })));
const SoftwareFactory = lazy(() => import('./components/SoftwareFactory').then(m => ({ default: m.SoftwareFactory })));
const JarvisPanel = lazy(() => import('./components/JarvisPanel').then(m => ({ default: m.JarvisPanel })));
const Infiltrator = lazy(() => import('./components/Infiltrator').then(m => ({ default: m.Infiltrator })));
const ToastContainer = lazy(() => import('./components/Toast').then(m => ({ default: m.ToastContainer })));
const TinkaDashboard = lazy(() => import('./components/TinkaDashboard').then(m => ({ default: m.TinkaDashboard })));
const YouTubeAnalyzer = lazy(() => import('./components/YouTubeAnalyzer').then(m => ({ default: m.YouTubeAnalyzer })));
const AutonomyPanel = lazy(() => import('./components/AutonomyPanel').then(m => ({ default: m.AutonomyPanel })));
const JournalistPanel = lazy(() => import('./components/JournalistPanel').then(m => ({ default: m.JournalistPanel })));
const ModelHub = lazy(() => import('./components/ModelHub').then(m => ({ default: m.ModelHub })));
const MemoryStudio = lazy(() => import('./components/MemoryStudio').then(m => ({ default: m.MemoryStudio })));
const AgentShieldMonitor = lazy(() => import('./components/AgentShieldMonitor').then(m => ({ default: m.AgentShieldMonitor })));
const TikTokRadarPanel = lazy(() => import('./components/TikTokRadarPanel').then(m => ({ default: m.TikTokRadarPanel })));

import type { PanelId } from './types';

function App() {
  const [activePanel, setActivePanel] = useState<PanelId>('home');

  useEffect(() => {
    const handleNav = (e: any) => {
      if (e.detail) setActivePanel(e.detail as PanelId);
    };
    window.addEventListener('navigate-panel', handleNav);
    return () => window.removeEventListener('navigate-panel', handleNav);
  }, []);

  const renderPanel = () => {
    switch (activePanel) {
      case 'home': return <MissionControl />;
      case 'chat': return <ChatAuditor />;
      case 'vision': return <VisionStudio />;
      case 'queue': return <ImageQueue />;
      case 'video': return <VideoStudio />;
      case 'v2v': return <V2VStudio />;
      case 'obs': return <OBSStudio />;
      case 'imagelab': return <ImageLab />;
      case 'deploy': return <DeployManager />;
      case 'gameserver': return <GameServers />;
      case 'multiagent': return <MultiAgent />;
      case 'hardware': return <HardwareMonitor />;
      case 'cost': return <CostCenter />;
      case 'watchdog': return <Watchdog />;
      case 'sessions': return <Sessions />;
      case 'rag': return <RagIndex />;
      case 'mcp': return <MCPServers />;
      case 'tools': return <Tools />;
      case 'tools-pro': return <ToolsPro />;
      case 'firecrawl': return <Firecrawl />;
      case 'hitl': return <HITLApproval />;
      case 'status': return <SystemStatus />;
      case 'security': return <Security />;
      case 'agentshield': return <AgentShieldMonitor />;
      case 'audit': return <AuditLog />;
      case 'config': return <Settings />;
      case 'monetization': return <MonetizationHub />;
      case 'bountyhunter': return <BountyHunter />;
      case 'softwarefactory': return <SoftwareFactory />;
      case 'infiltrator': return <Infiltrator />;
      case 'tinka': return <TinkaDashboard />;
      case 'youtubeanalyzer': return <YouTubeAnalyzer />;
      case 'autonomy': return <AutonomyPanel />;
      case 'journalist': return <JournalistPanel />;
      case 'modelhub': return <ModelHub />;
      case 'memorystudio': return <MemoryStudio />;
      case 'jarvis': return <JarvisPanel />;
      case 'tiktokradar': return <TikTokRadarPanel />;
      default:
        return (
          <div className="flex items-center justify-center h-full text-text-muted text-lg font-medium">
            Módulo {activePanel} no encontrado
          </div>
        );
    }
  };

  return (
    <Layout activePanel={activePanel} setActivePanel={setActivePanel}>
      <Suspense fallback={
        <div className="flex items-center justify-center h-full text-text-muted/60 animate-pulse">
          <div className="flex flex-col items-center">
            <div className="w-8 h-8 rounded-full border-4 border-t-accent-primary border-r-accent-primary border-b-border-primary border-l-border-primary animate-spin mb-4" />
            <span className="text-sm font-medium">Cargando módulo...</span>
          </div>
        </div>
      }>
        {renderPanel()}
      </Suspense>
      <Suspense fallback={null}>
        <ToastContainer />
      </Suspense>
    </Layout>
  );
}

export default App;
