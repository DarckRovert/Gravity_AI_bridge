import { useState, useEffect } from 'react';
import { Layout } from './components/Layout';
import { ChatAuditor } from './components/ChatAuditor';
import { MissionControl } from './components/MissionControl';
import { VisionStudio } from './components/VisionStudio';
import { ImageQueue } from './components/ImageQueue';
import { VideoStudio } from './components/VideoStudio';
import { V2VStudio } from './components/V2VStudio';
import { ImageLab } from './components/ImageLab';
import { OBSStudio } from './components/OBSStudio';
import { DeployManager } from './components/DeployManager';
import { GameServers } from './components/GameServers';
import { MultiAgent } from './components/MultiAgent';
import { HardwareMonitor } from './components/HardwareMonitor';
import { CostCenter } from './components/CostCenter';
import { Watchdog } from './components/Watchdog';
import { Sessions } from './components/Sessions';
import { RagIndex } from './components/RagIndex';
import { MCPServers } from './components/MCPServers';
import { Tools } from './components/Tools';
import { ToolsPro } from './components/ToolsPro';
import { Firecrawl } from './components/Firecrawl';
import { HITLApproval } from './components/HITLApproval';
import { SystemStatus } from './components/SystemStatus';
import { Security } from './components/Security';
import { AuditLog } from './components/AuditLog';
import { Settings } from './components/Settings';
import { MonetizationHub } from './components/MonetizationHub';
import { BountyHunter } from './components/BountyHunter';
import { SoftwareFactory } from './components/SoftwareFactory';
import { Infiltrator } from './components/Infiltrator';
import { ToastContainer } from './components/Toast';
import { TinkaDashboard } from './components/TinkaDashboard';
import { YouTubeAnalyzer } from './components/YouTubeAnalyzer';
import { AutonomyPanel } from './components/AutonomyPanel';
import { JournalistPanel } from './components/JournalistPanel';

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
      {renderPanel()}
      <ToastContainer />
    </Layout>
  );
}

export default App;
