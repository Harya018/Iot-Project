/**
 * AlertLog.jsx — Scrollable list of the 20 most recent alerts.
 *
 * Props:
 *   alerts        : array of alert objects
 *   onAcknowledge : function(id, name)
 */

import React, { useState, useCallback } from 'react';

const LEVEL_STYLES = {
  1: { badge: 'bg-warning/20 text-warning border border-warning/40', label: 'Level 1' },
  2: { badge: 'bg-orange-500/20 text-orange-400 border border-orange-500/40', label: 'Escalated' },
  3: { badge: 'bg-danger/20 text-danger border border-danger/40 animate-pulse', label: 'CRITICAL' },
};

function formatTimestamp(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return d.toLocaleString();
}

function AlertCard({ alert, onAcknowledge }) {
  const [inputName, setInputName] = useState('');
  const [showInput, setShowInput] = useState(false);
  const [loading, setLoading] = useState(false);

  const level = alert.escalation_level || 1;
  const levelStyle = LEVEL_STYLES[level] || LEVEL_STYLES[1];

  const handleAck = useCallback(async () => {
    const name = inputName.trim() || 'Admin';
    setLoading(true);
    try {
      await onAcknowledge(alert.id, name);
    } finally {
      setLoading(false);
      setShowInput(false);
    }
  }, [alert.id, inputName, onAcknowledge]);

  const directionLabel =
    alert.direction === 'high'
      ? `exceeds high threshold of ${alert.threshold}`
      : `below low threshold of ${alert.threshold}`;

  const unit = alert.parameter === 'temperature' ? '°C' : '%';

  return (
    <div
      className={`bg-bg rounded-xl p-4 ring-1 transition-all duration-300
        ${alert.acknowledged ? 'ring-white/5 opacity-60' : 'ring-danger/30'}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${levelStyle.badge}`}
            >
              {levelStyle.label}
            </span>
            <span className="text-xs text-text-secondary">{formatTimestamp(alert.timestamp)}</span>
          </div>
          <p className="mt-1.5 text-sm font-medium text-text-primary capitalize">
            {alert.parameter} &nbsp;
            <span className={alert.direction === 'high' ? 'text-danger' : 'text-warning'}>
              {alert.value}{unit}
            </span>
            &nbsp;—&nbsp;{directionLabel}{unit}
          </p>
          {alert.acknowledged && (
            <p className="mt-1 text-xs text-success">
              ✓ Acknowledged by <strong>{alert.acknowledged_by}</strong> at{' '}
              {formatTimestamp(alert.acknowledged_at)}
            </p>
          )}
        </div>
        {!alert.acknowledged && (
          <div className="flex-shrink-0">
            {!showInput ? (
              <button
                onClick={() => setShowInput(true)}
                className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-primary/20 text-primary
                           border border-primary/30 hover:bg-primary/40 transition-colors"
              >
                Acknowledge
              </button>
            ) : (
              <div className="flex gap-2 items-center">
                <input
                  type="text"
                  placeholder="Your name"
                  value={inputName}
                  onChange={(e) => setInputName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAck()}
                  className="text-xs px-2 py-1.5 rounded-lg bg-white/5 border border-white/10
                             text-text-primary placeholder-text-secondary focus:outline-none
                             focus:border-primary w-28"
                />
                <button
                  onClick={handleAck}
                  disabled={loading}
                  className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-success/20 text-success
                             border border-success/30 hover:bg-success/40 transition-colors disabled:opacity-50"
                >
                  {loading ? '…' : 'OK'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function AlertLog({ alerts, onAcknowledge }) {
  const displayed = alerts.slice(0, 20);

  return (
    <div className="bg-card rounded-2xl p-6 ring-1 ring-white/5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-widest">
          Alert Log
        </h3>
        <span className="text-xs text-text-secondary">
          {alerts.filter((a) => !a.acknowledged).length} unacknowledged
        </span>
      </div>
      {displayed.length === 0 ? (
        <div className="text-center text-text-secondary text-sm py-8">
          No alerts recorded yet
        </div>
      ) : (
        <div className="flex flex-col gap-3 max-h-80 overflow-y-auto pr-1 custom-scroll">
          {displayed.map((alert) => (
            <AlertCard key={alert.id} alert={alert} onAcknowledge={onAcknowledge} />
          ))}
        </div>
      )}
    </div>
  );
}
