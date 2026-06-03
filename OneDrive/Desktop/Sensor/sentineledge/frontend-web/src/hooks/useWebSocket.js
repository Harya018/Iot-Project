/**
 * useWebSocket.js — Custom React hook for the SentinelEdge WebSocket stream.
 *
 * Connects to ws://{host}/ws, auto-reconnects every 3 s on disconnect,
 * and exposes the latest reading, active breaches, and connection state.
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const RECONNECT_DELAY_MS = 3000;

export function useWebSocket() {
  const [lastReading, setLastReading] = useState(null);
  const [breaches, setBreaches] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('CONNECTING'); // CONNECTING | LIVE | RECONNECTING

  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const unmountedRef = useRef(false);

  const connect = useCallback(() => {
    if (unmountedRef.current) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws`;

    setConnectionStatus('CONNECTING');

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (unmountedRef.current) return;
      setIsConnected(true);
      setConnectionStatus('LIVE');
      // Clear any pending reconnect timer
      clearTimeout(reconnectTimerRef.current);
    };

    ws.onmessage = (event) => {
      if (unmountedRef.current) return;
      try {
        const data = JSON.parse(event.data);
        setLastReading({
          temperature: data.temperature,
          humidity: data.humidity,
          timestamp: data.timestamp,
        });
        setBreaches(data.breaches || []);
      } catch (err) {
        console.error('[useWebSocket] Failed to parse message:', err);
      }
    };

    ws.onclose = () => {
      if (unmountedRef.current) return;
      setIsConnected(false);
      setConnectionStatus('RECONNECTING');
      reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
    };

    ws.onerror = (err) => {
      console.error('[useWebSocket] Error:', err);
      ws.close(); // triggers onclose → reconnect
    };
  }, []);

  useEffect(() => {
    unmountedRef.current = false;
    connect();
    return () => {
      unmountedRef.current = true;
      clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on intentional unmount
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { lastReading, breaches, isConnected, connectionStatus };
}
