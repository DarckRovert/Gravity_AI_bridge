export interface Message {
  role: 'user' | 'system' | 'assistant';
  content: string;
}

export interface HardwareStats {
  cpu_percent: number;
  ram_percent: number;
  vram_mb?: number;
}

export interface CostStats {
  session_tokens: number;
  session_cost: number;
  daily_cost: number;
  currency: string;
}

export interface VideoStats {
  pending_count: number;
}

export interface ProviderStatus {
  name: string;
  healthy: boolean;
  models: number;
  latency_ms: number;
  category: 'local' | 'cloud';
}

export interface GravityContext {
  active_model: string | null;
  active_provider: string | null;
  hardware: HardwareStats;
  cost: CostStats;
  video: VideoStats;
  security_alerts: number;
  providers?: ProviderStatus[];
}

export type PanelId = 
  | 'jarvis'
  | 'chat'
  | 'home'
  | 'vision'
  | 'queue'
  | 'video'
  | 'imagelab'
  | 'deploy'
  | 'gameserver'
  | 'multiagent'
  | 'hardware'
  | 'cost'
  | 'watchdog'
  | 'sessions'
  | 'rag'
  | 'mcp'
  | 'tools'
  | 'tools-pro'
  | 'firecrawl'
  | 'hitl'
  | 'status'
  | 'security'
  | 'audit'
  | 'agentshield'
  | 'config'
  | 'monetization'
  | 'v2v'
  | 'obs'
  | 'bountyhunter'
  | 'softwarefactory'
  | 'infiltrator'
  | 'tinka'
  | 'youtubeanalyzer'
  | 'autonomy'
  | 'modelhub'
  | 'memorystudio'
  | 'journalist';
