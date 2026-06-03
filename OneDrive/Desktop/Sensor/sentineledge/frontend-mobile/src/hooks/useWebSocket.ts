/**
 * useWebSocket.ts — Custom React hook wrapping the WebSocket singleton service.
 */

import { useState, useEffect, useRef } from 'react';
import { wsService, SensorReading, BreachEvent } from '../services/websocket';

interface WebSocketState {
  reading: SensorReading | null;
  breaches: BreachEvent[];
  isConnected: boolean;
  reconnectAttempt: number;
}

export function useWebSocket(): WebSocketState {
  const [reading, setReading] = useState<SensorReading | null>(null);
  const [breaches, setBreaches] = useState<BreachEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  useEffect(() => {
    wsService.setListeners({
      onReading: (r) => {
        setReading(r);
        setBreaches([]); // cleared per reading, set on breach event
      },
      onBreach: (b) => setBreaches(b),
      onConnect: () => {
        setIsConnected(true);
        setReconnectAttempt(0);
      },
      onDisconnect: () => {
        setIsConnected(false);
        setReconnectAttempt(wsService.currentAttempt);
      },
    });

    wsService.connect();

    return () => {
      wsService.setListeners({});
    };
  }, []);

  return { reading, breaches, isConnected, reconnectAttempt };
}
