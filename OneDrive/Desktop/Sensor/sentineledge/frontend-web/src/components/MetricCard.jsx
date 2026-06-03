/**
 * MetricCard.jsx — Displays a single sensor metric (temperature or humidity).
 *
 * Props:
 *   parameter  : "temperature" | "humidity"
 *   value      : number | null
 *   unit       : string  (e.g. "°C", "%")
 *   status     : "NORMAL" | "WARNING" | "CRITICAL"
 *   breach     : boolean
 *   thresholds : { high: number, low: number }
 */

import React from 'react';

const STATUS_STYLES = {
  NORMAL: {
    badge: 'bg-success/20 text-success border border-success/30',
    value: 'text-text-primary',
  },
  WARNING: {
    badge: 'bg-warning/20 text-warning border border-warning/30',
    value: 'text-warning',
  },
  CRITICAL: {
    badge: 'bg-danger/20 text-danger border border-danger/30',
    value: 'text-danger',
  },
};

const ICONS = {
  temperature: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M9 3.5a3 3 0 0 1 6 0v8.25a5.25 5.25 0 1 1-6 0V3.5z" />
    </svg>
  ),
  humidity: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M12 2.25c0 0-7.5 8.47-7.5 12.75a7.5 7.5 0 0 0 15 0C19.5 10.72 12 2.25 12 2.25z" />
    </svg>
  ),
};

export default function MetricCard({ parameter, value, unit, status, breach, thresholds }) {
  const styles = STATUS_STYLES[status] || STATUS_STYLES.NORMAL;
  const label = parameter === 'temperature' ? 'Temperature' : 'Humidity';

  return (
    <div
      className={`relative bg-card rounded-2xl p-6 flex flex-col gap-4 overflow-hidden transition-all duration-300
        ${breach ? 'ring-2 ring-danger shadow-lg shadow-danger/20 animate-pulse-border' : 'ring-1 ring-white/5'}`}
    >
      {/* Glow overlay when breaching */}
      {breach && (
        <div className="absolute inset-0 bg-danger/5 pointer-events-none rounded-2xl" />
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-text-secondary">
          {ICONS[parameter]}
          <span className="text-sm font-medium uppercase tracking-widest">{label}</span>
        </div>
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${styles.badge}`}>
          {status}
        </span>
      </div>

      {/* Main value */}
      <div className={`text-6xl font-bold tracking-tight ${styles.value} transition-colors duration-500`}>
        {value !== null && value !== undefined ? `${value}` : '--'}
        <span className="text-2xl font-medium ml-1 text-text-secondary">{unit}</span>
      </div>

      {/* Threshold info */}
      {thresholds && (
        <div className="flex items-center gap-4 text-xs text-text-secondary border-t border-white/5 pt-3">
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-danger inline-block" />
            <span>High: {thresholds.high}{unit}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-warning inline-block" />
            <span>Low: {thresholds.low}{unit}</span>
          </div>
        </div>
      )}

      <style>{`
        @keyframes pulse-border {
          0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
          50% { box-shadow: 0 0 20px 6px rgba(239,68,68,0.2); }
        }
        .animate-pulse-border {
          animation: pulse-border 1.5s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
