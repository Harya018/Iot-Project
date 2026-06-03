/**
 * Dashboard.jsx — Main admin dashboard layout.
 *
 * Composes all child components and wires up WebSocket, audio alarm,
 * Web Push registration, and alert auto-refresh.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import MetricCard from './MetricCard';
import LiveChart from './LiveChart';
import AlertLog from './AlertLog';
import ThresholdConfig from './ThresholdConfig';
import SubscriberManager from './SubscriberManager';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAudioAlarm } from '../hooks/useAudioAlarm';
import {
  fetchRecentAlerts,
  fetchRecentReadings,
  fetchThresholds,
  acknowledgeAlert,
  getVapidPublicKey,
  savePushSubscription,
  fetchSubscribers,
  simulateBreach,
} from '../services/api';

const STATUS_COLORS = {
  LIVE: 'bg-success text-success',
  CONNECTING: 'bg-warning text-warning',
  RECONNECTING: 'bg-danger text-danger',
};

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

export default function Dashboard() {
  const { lastReading, breaches, isConnected, connectionStatus } = useWebSocket();
  const { playAlarm, stopAlarm } = useAudioAlarm();

  const [readings, setReadings] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [thresholds, setThresholds] = useState(null);
  const [demoMode, setDemoMode] = useState(false);
  const prevBreachRef = useRef(false);

  // Seed chart with historical readings on mount
  useEffect(() => {
    fetchRecentReadings().then(setReadings).catch(() => {});
    fetchRecentAlerts().then(setAlerts).catch(() => {});
    fetchThresholds().then(setThresholds).catch(() => {});

    // Check if demo mode is on via health check or server flag
    fetch('/api/health')
      .then((r) => r.json())
      .then(() => {
        // We detect DEMO_MODE via the readings drift pattern — just note it
        // The backend sends a DEMO_MODE indicator via config endpoint if needed
      })
      .catch(() => {});
  }, []);

  // Append new readings from WebSocket
  useEffect(() => {
    if (!lastReading) return;
    setReadings((prev) => {
      const next = [...prev, lastReading];
      return next.length > 60 ? next.slice(-60) : next;
    });
  }, [lastReading]);

  // Play alarm when breaches change
  useEffect(() => {
    const hasBreach = breaches.length > 0;
    if (hasBreach && !prevBreachRef.current) {
      playAlarm(1);
    } else if (!hasBreach && prevBreachRef.current) {
      stopAlarm();
    }
    prevBreachRef.current = hasBreach;
  }, [breaches, playAlarm, stopAlarm]);

  // Auto-refresh alerts every 10 s
  useEffect(() => {
    const timer = setInterval(() => {
      fetchRecentAlerts().then(setAlerts).catch(() => {});
    }, 10_000);
    return () => clearInterval(timer);
  }, []);

  // Register Web Push on mount
  useEffect(() => {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;

    const registerPush = async () => {
      try {
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') return;

        const { vapid_public_key } = await getVapidPublicKey();
        if (!vapid_public_key) return;

        const reg = await navigator.serviceWorker.register('/sw.js');
        await navigator.serviceWorker.ready;

        const sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(vapid_public_key),
        });

        // Try to find own subscriber and register
        const subs = await fetchSubscribers();
        if (subs.length > 0) {
          await savePushSubscription(subs[0].id, JSON.stringify(sub.toJSON()));
        }
      } catch (err) {
        console.warn('[Push] Registration failed:', err);
      }
    };

    registerPush();
  }, []);

  const handleAcknowledge = useCallback(async (id, name) => {
    await acknowledgeAlert(id, name);
    const updated = await fetchRecentAlerts();
    setAlerts(updated);
  }, []);

  const handleSimulateBreach = async () => {
    await simulateBreach();
  };

  // Determine metric status
  const getStatus = (param, value) => {
    if (!thresholds || value === null || value === undefined) return 'NORMAL';
    if (param === 'temperature') {
      if (value > thresholds.temp_high || value < thresholds.temp_low) return 'CRITICAL';
    } else {
      if (value > thresholds.humidity_high || value < thresholds.humidity_low) return 'CRITICAL';
    }
    return 'NORMAL';
  };

  const tempBreach = breaches.some((b) => b.parameter === 'temperature');
  const humBreach = breaches.some((b) => b.parameter === 'humidity');
  const tempStatus = getStatus('temperature', lastReading?.temperature);
  const humStatus = getStatus('humidity', lastReading?.humidity);

  const unackCount = alerts.filter((a) => !a.acknowledged).length;

  return (
    <div className="min-h-screen bg-bg text-text-primary font-sans">
      {/* DEMO MODE Banner */}
      {demoMode && (
        <div className="bg-warning/90 text-black text-center text-sm font-semibold py-2 px-4">
          ⚠️ DEMO MODE ACTIVE — Temperature is cycling automatically to trigger threshold breaches
        </div>
      )}

      {/* Active breach banner */}
      {breaches.length > 0 && (
        <div className="bg-danger text-white text-center text-sm font-bold py-2.5 px-4 animate-pulse">
          🚨 THRESHOLD BREACH DETECTED — {breaches.map((b) =>
            `${b.parameter} ${b.value}${b.parameter === 'temperature' ? '°C' : '%'}`
          ).join(', ')}
        </div>
      )}

      {/* Header */}
      <header className="border-b border-white/5 px-4 sm:px-8 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary/20 border border-primary/30
                            flex items-center justify-center text-xl">
              🛡️
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-text-primary">SentinelEdge</h1>
              <p className="text-xs text-text-secondary">Local IoT Alert System</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {unackCount > 0 && (
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-danger/20 text-danger border border-danger/30">
                {unackCount} unacknowledged
              </span>
            )}

            <button
              onClick={handleSimulateBreach}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-warning/20 text-warning
                         border border-warning/30 hover:bg-warning/40 transition-colors"
            >
              Simulate Breach
            </button>

            <div className={`flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full
              border ${connectionStatus === 'LIVE'
                ? 'bg-success/10 text-success border-success/30'
                : connectionStatus === 'CONNECTING'
                  ? 'bg-warning/10 text-warning border-warning/30'
                  : 'bg-danger/10 text-danger border-danger/30'}`}
            >
              <span className={`w-2 h-2 rounded-full ${
                connectionStatus === 'LIVE' ? 'bg-success animate-pulse' :
                connectionStatus === 'CONNECTING' ? 'bg-warning' : 'bg-danger'
              }`} />
              {connectionStatus}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-8 py-6 space-y-6">
        {/* Metric cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <MetricCard
            parameter="temperature"
            value={lastReading?.temperature ?? null}
            unit="°C"
            status={tempStatus}
            breach={tempBreach}
            thresholds={thresholds ? { high: thresholds.temp_high, low: thresholds.temp_low } : null}
          />
          <MetricCard
            parameter="humidity"
            value={lastReading?.humidity ?? null}
            unit="%"
            status={humStatus}
            breach={humBreach}
            thresholds={thresholds ? { high: thresholds.humidity_high, low: thresholds.humidity_low } : null}
          />
        </div>

        {/* Live chart */}
        <LiveChart readings={readings} thresholds={thresholds} />

        {/* Alert log */}
        <AlertLog alerts={alerts} onAcknowledge={handleAcknowledge} />

        {/* Collapsible panels */}
        <ThresholdConfig />
        <SubscriberManager />
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-4 px-8 text-center text-xs text-text-secondary">
        SentinelEdge v1.0.0 — Local network only — Zero cloud dependencies
      </footer>
    </div>
  );
}
