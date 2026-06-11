// ─────────────────────────────────────────────
//  SentinelEdge — WebSocket Hook
//  Auto-reconnect, exponential backoff, heartbeat,
//  AppState awareness
// ─────────────────────────────────────────────
import { useState, useEffect, useRef, useCallback } from 'react';
import { AppState } from 'react-native';
import { WS_URL } from '../config/config';

const HEARTBEAT_INTERVAL = 30000;   // 30 seconds
const INITIAL_BACKOFF = 3000;       // 3 seconds
const MAX_BACKOFF = 30000;          // 30 seconds

export const useWebSocket = () => {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [temperature, setTemperature] = useState(null);
  const [alerts, setAlerts] = useState([]);

  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const heartbeatTimerRef = useRef(null);
  const backoffRef = useRef(INITIAL_BACKOFF);
  const appStateRef = useRef(AppState.currentState);
  const isMountedRef = useRef(true);
  const manuallyDisconnectedRef = useRef(false);

  // ── Clear all timers ─────────────────────────
  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  // ── Send heartbeat ping ──────────────────────
  const startHeartbeat = useCallback(() => {
    clearInterval(heartbeatTimerRef.current);
    heartbeatTimerRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, HEARTBEAT_INTERVAL);
  }, []);

  // ── Handle incoming messages ─────────────────
  const handleMessage = useCallback((event) => {
    try {
      const data = JSON.parse(event.data);
      setLastMessage(data);

      switch (data.type) {
        case 'temperature_update':
          if (data.temperature !== undefined) {
            setTemperature(data.temperature);
          }
          break;

        case 'alert':
          setAlerts((prev) => [data, ...prev]);
          break;

        case 'pong':
          // Heartbeat acknowledged — do nothing
          break;

        default:
          break;
      }
    } catch (err) {
      console.warn('[WS] Failed to parse message:', err);
    }
  }, []);

  // ── Connect to WebSocket server ──────────────
  const connect = useCallback(() => {
    if (!isMountedRef.current || manuallyDisconnectedRef.current) return;
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    console.log(`[WS] Connecting to ${WS_URL} (backoff=${backoffRef.current}ms)`);

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isMountedRef.current) return;
      console.log('[WS] Connected');
      setConnected(true);
      backoffRef.current = INITIAL_BACKOFF; // reset on success
      startHeartbeat();
    };

    ws.onmessage = handleMessage;

    ws.onerror = (error) => {
      console.warn('[WS] Error:', error.message);
    };

    ws.onclose = (event) => {
      if (!isMountedRef.current) return;
      console.log(`[WS] Closed (code=${event.code})`);
      setConnected(false);
      clearInterval(heartbeatTimerRef.current);

      if (!manuallyDisconnectedRef.current) {
        // Schedule reconnect with exponential backoff
        const delay = backoffRef.current;
        backoffRef.current = Math.min(backoffRef.current * 2, MAX_BACKOFF);
        console.log(`[WS] Reconnecting in ${delay}ms`);
        reconnectTimerRef.current = setTimeout(() => {
          if (isMountedRef.current && !manuallyDisconnectedRef.current) {
            connect();
          }
        }, delay);
      }
    };
  }, [handleMessage, startHeartbeat]);

  // ── Disconnect cleanly ───────────────────────
  const disconnect = useCallback(() => {
    manuallyDisconnectedRef.current = true;
    clearTimers();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, [clearTimers]);

  // ── AppState listener ────────────────────────
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextState) => {
      const prev = appStateRef.current;
      appStateRef.current = nextState;

      if (prev === 'active' && nextState.match(/inactive|background/)) {
        // Going to background — disconnect
        console.log('[WS] App moved to background — disconnecting');
        manuallyDisconnectedRef.current = true;
        clearTimers();
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
        setConnected(false);
      } else if (prev.match(/inactive|background/) && nextState === 'active') {
        // Returning to foreground — reconnect
        console.log('[WS] App returned to foreground — reconnecting');
        manuallyDisconnectedRef.current = false;
        backoffRef.current = INITIAL_BACKOFF;
        connect();
      }
    });

    return () => subscription.remove();
  }, [connect, clearTimers]);

  // ── Initial connection ───────────────────────
  useEffect(() => {
    isMountedRef.current = true;
    manuallyDisconnectedRef.current = false;
    connect();

    return () => {
      isMountedRef.current = false;
      clearTimers();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect, clearTimers]);

  return { connected, lastMessage, temperature, alerts };
};
