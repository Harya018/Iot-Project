/**
 * api.js — All SentinelEdge REST API calls.
 * Server origin is derived from window.location at runtime so the
 * web app works on any LAN IP without reconfiguration.
 */

const BASE = `${window.location.protocol}//${window.location.host}/api`;

async function _fetch(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${options.method || 'GET'} ${path} → ${res.status}: ${text}`);
  }
  return res.json();
}

// ── Readings ─────────────────────────────────────────────────────────────────
export const fetchRecentReadings = () => _fetch('/readings/recent');

// ── Alerts ───────────────────────────────────────────────────────────────────
export const fetchRecentAlerts = () => _fetch('/alerts');

export const acknowledgeAlert = (id, name) =>
  _fetch(`/alerts/${id}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({ acknowledged_by: name }),
  });

// ── Subscribers ───────────────────────────────────────────────────────────────
export const fetchSubscribers = () => _fetch('/subscribers');

export const addSubscriber = (data) =>
  _fetch('/subscribers', { method: 'POST', body: JSON.stringify(data) });

export const deleteSubscriber = (id) =>
  _fetch(`/subscribers/${id}`, { method: 'DELETE' });

export const savePushSubscription = (subscriberId, subscriptionJson) =>
  _fetch(`/subscribers/${subscriberId}/push`, {
    method: 'POST',
    body: JSON.stringify({ subscription_json: subscriptionJson }),
  });

// ── Thresholds ────────────────────────────────────────────────────────────────
export const fetchThresholds = () => _fetch('/config/thresholds');

export const updateThresholds = (data) =>
  _fetch('/config/thresholds', { method: 'POST', body: JSON.stringify(data) });

// ── VAPID public key ──────────────────────────────────────────────────────────
export const getVapidPublicKey = () => _fetch('/config/vapid-public-key');

// ── Demo ──────────────────────────────────────────────────────────────────────
export const simulateBreach = () =>
  _fetch('/simulate/breach', { method: 'POST' });

// ── Health ────────────────────────────────────────────────────────────────────
export const healthCheck = () => _fetch('/health');
