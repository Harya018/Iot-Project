/**
 * websocket.ts — Singleton WebSocket service for SentinelEdge mobile.
 *
 * Connects to ws://{serverIP}:{serverPort}/ws.
 * Auto-reconnects with exponential backoff (1 s → 2 s → 4 s … max 30 s).
 * Emits events: onReading, onBreach, onConnect, onDisconnect.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export interface SensorReading {
  temperature: number;
  humidity: number;
  timestamp: string;
}

export interface BreachEvent {
  parameter: string;
  value: number;
  threshold: number;
  direction: string;
}

export type WSEventMap = {
  onReading: (reading: SensorReading) => void;
  onBreach: (breaches: BreachEvent[]) => void;
  onConnect: () => void;
  onDisconnect: () => void;
};

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempt = 0;
  private maxDelay = 30_000;
  private listeners: Partial<WSEventMap> = {};
  private shouldReconnect = true;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  setListeners(listeners: Partial<WSEventMap>): void {
    this.listeners = listeners;
  }

  async connect(): Promise<void> {
    const ip = (await AsyncStorage.getItem('serverIp')) || '192.168.1.100';
    const port = (await AsyncStorage.getItem('serverPort')) || '8000';
    const url = `ws://${ip}:${port}/ws`;

    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }

    try {
      this.ws = new WebSocket(url);
    } catch (err) {
      console.warn('[WS] Failed to create WebSocket:', err);
      this._scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      console.log('[WS] Connected to', url);
      this.reconnectAttempt = 0;
      this.listeners.onConnect?.();
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const reading: SensorReading = {
          temperature: data.temperature,
          humidity: data.humidity,
          timestamp: data.timestamp,
        };
        this.listeners.onReading?.(reading);
        if (data.breaches && data.breaches.length > 0) {
          this.listeners.onBreach?.(data.breaches as BreachEvent[]);
        }
      } catch (err) {
        console.warn('[WS] Parse error:', err);
      }
    };

    this.ws.onerror = (err) => {
      console.warn('[WS] Error:', err);
    };

    this.ws.onclose = () => {
      console.log('[WS] Disconnected');
      this.listeners.onDisconnect?.();
      if (this.shouldReconnect) {
        this._scheduleReconnect();
      }
    };
  }

  private _scheduleReconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    const delay = Math.min(1000 * 2 ** this.reconnectAttempt, this.maxDelay);
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempt + 1})`);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempt++;
      this.connect();
    }, delay);
  }

  disconnect(): void {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
  }

  reconnect(): void {
    this.shouldReconnect = true;
    this.reconnectAttempt = 0;
    this.connect();
  }

  get currentAttempt(): number {
    return this.reconnectAttempt;
  }
}

// Singleton instance
export const wsService = new WebSocketService();
