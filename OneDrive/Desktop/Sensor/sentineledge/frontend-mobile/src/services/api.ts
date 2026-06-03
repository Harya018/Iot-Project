/**
 * api.ts — All SentinelEdge REST API calls for the mobile app.
 * Server IP and port are loaded from AsyncStorage.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export async function getServerBase(): Promise<string> {
  const ip = (await AsyncStorage.getItem('serverIp')) || '192.168.1.100';
  const port = (await AsyncStorage.getItem('serverPort')) || '8000';
  return `http://${ip}:${port}/api`;
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const base = await getServerBase();
  const res = await fetch(`${base}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${options.method || 'GET'} ${path} → ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Alert types ──────────────────────────────────────────────────────────────
export interface Alert {
  id: number;
  parameter: string;
  value: number;
  threshold: number;
  direction: string;
  timestamp: string;
  acknowledged: boolean;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  escalation_level: number;
  max_escalated: boolean;
}

export interface Thresholds {
  temp_high: number;
  temp_low: number;
  humidity_high: number;
  humidity_low: number;
}

// ── API functions ─────────────────────────────────────────────────────────────
export const fetchAlerts = (): Promise<Alert[]> =>
  apiFetch<Alert[]>('/alerts');

export const acknowledgeAlert = (id: number, name: string): Promise<unknown> =>
  apiFetch(`/alerts/${id}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({ acknowledged_by: name }),
  });

export const fetchThresholds = (): Promise<Thresholds> =>
  apiFetch<Thresholds>('/config/thresholds');

export const healthCheck = async (): Promise<boolean> => {
  try {
    await apiFetch('/health');
    return true;
  } catch {
    return false;
  }
};
