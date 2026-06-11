// ─────────────────────────────────────────────
//  SentinelEdge — Hardcoded server configuration
//  No dynamic IP, no AsyncStorage, no setup screen.
// ─────────────────────────────────────────────

export const SERVER_IP = '172.20.10.2';
export const SERVER_PORT = '5000';

export const API_BASE = `http://${SERVER_IP}:${SERVER_PORT}/api`;
export const WS_URL = `ws://${SERVER_IP}:${SERVER_PORT}/ws`;
export const HEALTH_URL = `http://${SERVER_IP}:${SERVER_PORT}/api/health`;
