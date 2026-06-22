export const BRIDGE_PORT = 7860;
export const BRIDGE_BASE = typeof window !== 'undefined' 
  ? `${window.location.protocol}//${window.location.hostname}:${BRIDGE_PORT}`
  : `http://localhost:${BRIDGE_PORT}`;
