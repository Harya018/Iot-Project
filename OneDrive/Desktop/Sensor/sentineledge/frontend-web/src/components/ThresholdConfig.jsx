/**
 * ThresholdConfig.jsx — Collapsible threshold configuration panel.
 * Loads current values from GET /api/config/thresholds,
 * saves via POST /api/config/thresholds with success/error toast.
 */

import React, { useState, useEffect } from 'react';
import { fetchThresholds, updateThresholds } from '../services/api';

export default function ThresholdConfig() {
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState({
    temp_high: 38, temp_low: 22, humidity_high: 80, humidity_low: 35,
  });
  const [toast, setToast] = useState(null); // { type: 'success'|'error', msg }
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchThresholds()
      .then((data) => setValues(data))
      .catch(() => {});
  }, []);

  const showToast = (type, msg) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3000);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updateThresholds({
        temp_high: Number(values.temp_high),
        temp_low: Number(values.temp_low),
        humidity_high: Number(values.humidity_high),
        humidity_low: Number(values.humidity_low),
      });
      setValues(updated);
      showToast('success', 'Thresholds updated successfully');
    } catch (err) {
      showToast('error', `Failed to save: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const fields = [
    { key: 'temp_high', label: 'Temperature High', unit: '°C', color: 'text-danger' },
    { key: 'temp_low', label: 'Temperature Low', unit: '°C', color: 'text-warning' },
    { key: 'humidity_high', label: 'Humidity High', unit: '%', color: 'text-danger' },
    { key: 'humidity_low', label: 'Humidity Low', unit: '%', color: 'text-warning' },
  ];

  return (
    <div className="bg-card rounded-2xl ring-1 ring-white/5 overflow-hidden">
      {/* Header / toggle */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-white/5 transition-colors"
      >
        <span className="text-sm font-semibold text-text-secondary uppercase tracking-widest">
          ⚙️ Threshold Configuration
        </span>
        <svg
          className={`w-4 h-4 text-text-secondary transition-transform duration-300 ${open ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="px-6 pb-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {fields.map(({ key, label, unit, color }) => (
              <div key={key}>
                <label className={`text-xs font-medium mb-1.5 block ${color}`}>{label}</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    step="0.5"
                    value={values[key]}
                    onChange={(e) => setValues((v) => ({ ...v, [key]: e.target.value }))}
                    className="flex-1 bg-bg border border-white/10 rounded-lg px-3 py-2 text-sm
                               text-text-primary focus:outline-none focus:border-primary transition-colors"
                  />
                  <span className="text-text-secondary text-sm">{unit}</span>
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary/80 text-white font-semibold
                       text-sm transition-colors disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save Thresholds'}
          </button>

          {toast && (
            <div
              className={`text-sm px-4 py-2.5 rounded-lg font-medium
                ${toast.type === 'success'
                  ? 'bg-success/20 text-success border border-success/30'
                  : 'bg-danger/20 text-danger border border-danger/30'}`}
            >
              {toast.msg}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
