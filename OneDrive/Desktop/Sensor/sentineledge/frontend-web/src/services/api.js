/**
 * src/services/api.js — All API calls to the SentinelEdge backend.
 *
 * Uses RELATIVE URLs so this works whether the app is served
 * on port 5000, 8000, or any reverse proxy — no hardcoded host/port.
 */

function adminHeaders() {
  return {
    'Content-Type': 'application/json',
    'X-Admin-Password': sessionStorage.getItem('adminPassword') || 'admin123',
  }
}

function jsonHeaders() {
  return { 'Content-Type': 'application/json' }
}

async function req(method, path, body, headers = adminHeaders()) {
  const res = await fetch(path, {          // ← relative path, no BASE_URL
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'include',
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`)
  }
  // CSV responses
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('text/csv')) return res.blob()
  return res.json()
}

// ── Core ──────────────────────────────────────────────────────────────────────
export const fetchHealth             = ()             => req('GET',  '/api/health',                   undefined, jsonHeaders())
export const fetchAlerts             = (limit = 50)   => req('GET',  `/api/alerts?limit=${limit}`,    undefined, jsonHeaders())
export const acknowledgeAlert        = (id, name)     => req('POST', `/api/alerts/${id}/acknowledge`, { acknowledged_by: name })
export const fetchSubscribers        = ()             => req('GET',  '/api/subscribers',              undefined, jsonHeaders())
export const addSubscriber           = (data)         => req('POST', '/api/subscribers',              data)
export const deleteSubscriber        = (id)           => req('DELETE',`/api/subscribers/${id}`,      undefined)
export const setSubscriberPin        = (id, pin)      => req('POST', `/api/subscribers/${id}/set-pin`,{ subscriber_id: id, pin })
export const fetchThresholds         = ()             => req('GET',  '/api/config/thresholds',        undefined, jsonHeaders())
export const updateThresholds        = (data)         => req('POST', '/api/config/thresholds',        data)
export const resetThresholds         = ()             => req('POST', '/api/config/thresholds/reset',  undefined)
export const simulateBreach          = ()             => req('POST', '/api/simulate/breach',          undefined)
export const fetchRecentReadings     = ()             => req('GET',  '/api/readings/recent',          undefined, jsonHeaders())
export const fetchAdminConfigChanges = ()             => req('GET',  '/api/admin/config-changes')
export const fetchDatabaseStats      = ()             => req('GET',  '/api/admin/database/stats')
export const createBackup            = ()             => req('POST', '/api/admin/backup')
export const verifyAdminPassword     = (password)     => req('POST', '/api/admin/verify-password',   { password }, jsonHeaders())

// ── History ───────────────────────────────────────────────────────────────────
export const fetchHistoryStats   = (date)             => req('GET',  `/api/history/stats?date=${date}`)
export const fetchHistoryAlerts  = (date)             => req('GET',  `/api/history/alerts?date=${date}`)
export const exportAlertsCsv     = (start, end)       => req('GET',  `/api/history/export/alerts?start=${start}&end=${end}`)
export const exportReadingsCsv   = (start, end)       => req('GET',  `/api/history/export/readings?start=${start}&end=${end}`)

// ── Reports ───────────────────────────────────────────────────────────────────
export const fetchDailyReports   = (days = 30)        => req('GET',  `/api/reports/daily?days=${days}`)

// ── Receipts ──────────────────────────────────────────────────────────────────
export const fetchReceipts       = (limit = 100, channel = 'all', status = 'all') =>
  req('GET', `/api/receipts?limit=${limit}&channel=${channel}&status=${status}`)

// ── Events ────────────────────────────────────────────────────────────────────
export const fetchEvents         = (limit = 100, type = 'all') =>
  req('GET', `/api/events?limit=${limit}&type=${type}`)

// ── Demo controls (DELETE BEFORE PRODUCTION) ──────────────────────────────────
export const demoCoolingRun      = ()                 => req('POST', '/api/demo/cooling-run', undefined)
export const demoReset           = ()                 => req('POST', '/api/demo/reset',       undefined)

// ── Admin utilities ───────────────────────────────────────────────────────────
export const importCsv           = (filename)         => req('POST', '/api/admin/import-csv', { filename })
