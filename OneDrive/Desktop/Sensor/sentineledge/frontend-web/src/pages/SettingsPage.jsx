/**
 * src/pages/SettingsPage.jsx
 * Threshold config, demo controls (CSV playback), and admin info.
 */
import { useState, useEffect, useCallback } from 'react'
import { Settings2, RotateCcw, Zap, Database, Info, Server, RefreshCw, AlertTriangle } from 'lucide-react'
import {
  fetchThresholds, updateThresholds, resetThresholds,
  simulateBreach, createBackup, fetchHealth,
} from '../services/api.js'
import { utcToIST } from '../utils/time.js'
import Badge from '../components/shared/Badge.jsx'
import { useToast, ToastContainer } from '../components/shared/Toast.jsx'

// ─── API helpers for new simulate endpoints ───────────────────────────────────
const simulateDemo  = (speed) => fetch('/api/simulate/demo',  {
  method: 'POST',
  headers: {
    'Content-Type':   'application/json',
    'X-Admin-Password': sessionStorage.getItem('adminPassword') || '',
  },
  body: JSON.stringify({ speed }),
  credentials: 'include',
}).then(r => r.json())

const simulateReset = () => fetch('/api/simulate/reset', {
  method: 'POST',
  headers: { 'X-Admin-Password': sessionStorage.getItem('adminPassword') || '' },
  credentials: 'include',
}).then(r => r.json())

// ─── Speed options ────────────────────────────────────────────────────────────
const SPEED_OPTIONS = [
  { value: 10,  label: '10x faster',  desc: '~15 min per cycle'  },
  { value: 30,  label: '30x faster',  desc: '~5 min per cycle'   },
  { value: 50,  label: '50x faster',  desc: '~3 min per cycle'   },
]

export default function SettingsPage() {
  const { toasts, addToast, dismiss } = useToast()

  // ── Threshold state ──────────────────────────────────────────────────────────
  const [threshData, setThreshData] = useState(null)
  const [high,       setHigh]       = useState(90)
  const [low,        setLow]        = useState(38)
  const [saving,     setSaving]     = useState(false)
  const [resetting,  setResetting]  = useState(false)
  const [threshMsg,  setThreshMsg]  = useState(null)

  // ── Demo state ───────────────────────────────────────────────────────────────
  const [demoSpeed,    setDemoSpeed]    = useState(30)
  const [demoRunning,  setDemoRunning]  = useState(false)
  const [demoStatus,   setDemoStatus]   = useState(null)
  const [demoResetting,setDemoResetting]= useState(false)
  const [simulating,   setSimulating]   = useState(false)

  // ── Admin state ──────────────────────────────────────────────────────────────
  const [backing, setBacking] = useState(false)
  const [health,  setHealth]  = useState(null)

  // ── Load data ────────────────────────────────────────────────────────────────
  const loadThresholds = useCallback(async () => {
    try {
      const d = await fetchThresholds()
      setThreshData(d)
      setHigh(d.temperature?.high ?? 90)
      setLow(d.temperature?.low  ?? 38)
    } catch { /* silent */ }
  }, [])

  const loadHealth = useCallback(async () => {
    try { setHealth(await fetchHealth()) } catch { /* silent */ }
  }, [])

  useEffect(() => { loadThresholds(); loadHealth() }, [loadThresholds, loadHealth])

  // ── Threshold handlers ───────────────────────────────────────────────────────
  const handleUpdate = async (e) => {
    e.preventDefault()
    if (Number(high) <= Number(low)) {
      setThreshMsg({ type:'error', text:'High must be greater than low.' })
      return
    }
    setSaving(true); setThreshMsg(null)
    try {
      await updateThresholds({ temp_high: Number(high), temp_low: Number(low) })
      setThreshMsg({ type:'success', text:'Thresholds updated.' })
      loadThresholds()
    } catch (err) { setThreshMsg({ type:'error', text: err.message }) }
    finally { setSaving(false) }
  }

  const handleReset = async () => {
    if (!confirm('Reset to defaults (90°C / 38°C)?')) return
    setResetting(true); setThreshMsg(null)
    try {
      await resetThresholds()
      setThreshMsg({ type:'success', text:'Reset to defaults (90°C / 38°C).' })
      loadThresholds()
    } catch (err) { setThreshMsg({ type:'error', text: err.message }) }
    finally { setResetting(false) }
  }

  // ── Demo handlers ─────────────────────────────────────────────────────────────
  const handleDemoRun = async () => {
    setDemoRunning(true); setDemoStatus(null)
    try {
      const r = await simulateDemo(demoSpeed)
      const mins = r.estimated_duration_minutes ?? '—'
      setDemoStatus({
        type: 'info',
        text: `Demo started at ${demoSpeed}x speed — ~${mins} min for full cycle. `
            + `Alert fires when temperature drops to 38°C.`,
      })
      addToast({
        type: 'warning',
        message: `🔬 Demo ${demoSpeed}x — playing ${r.total_readings ?? '—'} real readings. Alert fires at 38°C.`,
      })
    } catch (err) {
      setDemoStatus({ type: 'error', text: 'Demo failed: ' + err.message })
      addToast({ type: 'error', message: 'Demo failed: ' + err.message })
    } finally { setDemoRunning(false) }
  }

  const handleDemoReset = async () => {
    setDemoResetting(true)
    try {
      await simulateReset()
      setDemoStatus({ type: 'success', text: 'Sensor reset to beginning of real data.' })
      addToast({ type: 'success', message: '✅ Sensor rewound to beginning of CSV data.' })
    } catch (err) { addToast({ type: 'error', message: 'Reset failed: ' + err.message }) }
    finally { setDemoResetting(false) }
  }

  const handleSimulateBreach = async () => {
    setSimulating(true)
    try {
      await simulateBreach()
      addToast({ type: 'warning', message: '⚡ Breach simulated — 92°C for 10 readings.' })
    } catch (err) { addToast({ type: 'error', message: 'Simulate failed: ' + err.message }) }
    finally { setSimulating(false) }
  }

  // ── Backup ────────────────────────────────────────────────────────────────────
  const handleBackup = async () => {
    setBacking(true)
    try {
      const r = await createBackup()
      addToast({ type:'success', message:`✅ Backup created: ${r.filename} (${r.size_mb} MB)` })
    } catch (err) { addToast({ type:'error', message:'Backup failed: ' + err.message }) }
    finally { setBacking(false) }
  }

  const isOverride = threshData?.source === 'runtime_override'

  // ── UI helpers ────────────────────────────────────────────────────────────────
  const Section = ({ title, icon: Icon, children }) => (
    <div className="card">
      <div className="flex items-center gap-2.5 px-5 py-4 border-b border-gray-100">
        <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center">
          <Icon size={15} className="text-purple-600" />
        </div>
        <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  )

  const StatusMsg = ({ msg }) => msg ? (
    <p className={`text-xs rounded-lg px-3 py-2 ${
      msg.type === 'success' ? 'text-emerald-700 bg-emerald-50' :
      msg.type === 'info'    ? 'text-blue-700 bg-blue-50'       :
      'text-red-700 bg-red-50'
    }`}>{msg.text}</p>
  ) : null

  // ─── Render ──────────────────────────────────────────────────────────────────
  return (
    <>
      <div className="space-y-5 max-w-2xl">

        {/* ── Section 1: Threshold Configuration ─────────────────────────── */}
        <Section title="Threshold Configuration" icon={Settings2}>
          <form onSubmit={handleUpdate} className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <Badge
                color={isOverride ? 'orange' : 'green'}
                label={isOverride ? 'Runtime Override Active' : 'Using Defaults'}
                dot={false}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-gray-600 mb-1 block">
                  High Threshold (°C) <span className="text-red-400">↑ Overheating danger</span>
                </label>
                <input className="form-input" type="number" step="0.1" min="-50" max="150"
                  value={high} onChange={e => setHigh(e.target.value)} />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 mb-1 block">
                  Low Threshold (°C) <span className="text-blue-400">↓ Machine ready</span>
                </label>
                <input className="form-input" type="number" step="0.1" min="-50" max="150"
                  value={low} onChange={e => setLow(e.target.value)} />
              </div>
            </div>

            {isOverride && threshData?.last_changed && (
              <p className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2">
                Changed {utcToIST(threshData.last_changed)}
              </p>
            )}

            <StatusMsg msg={threshMsg} />

            <p className="text-xs text-gray-400">
              Changes take effect immediately. Reset restores 90°C / 38°C defaults.
            </p>

            <div className="flex gap-2">
              <button type="submit" disabled={saving} className="btn btn-primary btn-sm flex-1">
                <Settings2 size={13} /> {saving ? 'Saving…' : 'Update Thresholds'}
              </button>
              <button type="button" onClick={handleReset} disabled={resetting} className="btn btn-ghost btn-sm">
                <RotateCcw size={13} /> {resetting ? 'Resetting…' : 'Reset to Default'}
              </button>
            </div>
          </form>
        </Section>

        {/* ── Section 2: Demo Controls ────────────────────────────────────── */}
        <Section title="Demo Controls" icon={Zap}>
          <div className="space-y-4">

            {/* Info banner */}
            <div className="rounded-xl bg-blue-50 border border-blue-200 px-4 py-3">
              <p className="text-xs font-semibold text-blue-800 mb-1">📊 Real Client Data Playback</p>
              <p className="text-xs text-blue-700 leading-relaxed">
                Normal mode plays <strong>real machine data</strong> from 9 CSV files at 1 reading/second
                (~2.5 hours for a full cooling cycle, 88°C → 38°C).
                Demo mode compresses this for presentations using the same real data.
              </p>
            </div>

            {/* Speed selector + start demo */}
            <div className="rounded-xl bg-orange-50 border border-orange-200 p-4 space-y-3">
              <div>
                <label className="text-xs font-semibold text-orange-800 block mb-2">
                  Demo Speed
                </label>
                <div className="flex gap-2">
                  {SPEED_OPTIONS.map(opt => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setDemoSpeed(opt.value)}
                      className={`flex-1 rounded-lg py-2 px-3 text-xs font-medium border transition-all ${
                        demoSpeed === opt.value
                          ? 'bg-orange-500 text-white border-orange-500'
                          : 'bg-white text-orange-700 border-orange-300 hover:bg-orange-50'
                      }`}
                    >
                      <div className="font-semibold">{opt.label}</div>
                      <div className="opacity-75 mt-0.5">{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-orange-800">Start Demo Cooling Run</p>
                  <p className="text-xs text-orange-600 mt-0.5">
                    Rewinds to first CSV reading and plays at {demoSpeed}x speed.
                    Alert fires when temperature drops to <strong>38°C</strong>.
                  </p>
                </div>
                <button
                  onClick={handleDemoRun}
                  disabled={demoRunning}
                  className="btn btn-sm flex-shrink-0 flex items-center gap-1.5"
                  style={{ background: '#F97316', color: '#fff', border: 'none' }}
                >
                  {demoRunning
                    ? <><RefreshCw size={13} className="animate-spin" /> Starting…</>
                    : '🔬 Start Demo'
                  }
                </button>
              </div>

              <StatusMsg msg={demoStatus} />
            </div>

            {/* Reset to normal */}
            <div className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 border border-gray-200">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-700">Reset to Normal</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Stop demo and rewind to first CSV reading at 1 reading/second.
                </p>
              </div>
              <button
                onClick={handleDemoReset}
                disabled={demoResetting}
                className="btn btn-ghost btn-sm flex-shrink-0 flex items-center gap-1.5"
              >
                {demoResetting
                  ? <><RefreshCw size={13} className="animate-spin" /> Resetting…</>
                  : <><RotateCcw size={13} /> Reset Sensor</>
                }
              </button>
            </div>

            {/* Simulate Breach (testing) */}
            <div className="flex items-center gap-4 p-4 rounded-xl bg-red-50 border border-red-200">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-red-700 flex items-center gap-1.5">
                  <AlertTriangle size={13} /> Simulate Breach
                  <span className="text-xs font-normal text-red-400 ml-1">(testing only)</span>
                </p>
                <p className="text-xs text-red-500 mt-0.5">
                  Forces 92°C for 10 readings — triggers the full alert pipeline.
                </p>
              </div>
              <button
                onClick={handleSimulateBreach}
                disabled={simulating}
                className="btn btn-sm flex-shrink-0 flex items-center gap-1.5"
                style={{ background: '#DC2626', color: '#fff', border: 'none' }}
              >
                {simulating
                  ? <><RefreshCw size={13} className="animate-spin" /> Firing…</>
                  : '⚡ Trigger'
                }
              </button>
            </div>

            {/* Backup */}
            <div className="flex items-center gap-4 p-4 rounded-xl bg-blue-50 border border-blue-200">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-blue-800">Create Database Backup</p>
                <p className="text-xs text-blue-600 mt-0.5">Snapshot the current database to the backups directory.</p>
              </div>
              <button onClick={handleBackup} disabled={backing}
                className="btn btn-sm flex-shrink-0 flex items-center gap-1.5"
                style={{ background: '#2563EB', color: '#fff', border: 'none' }}
              >
                {backing ? 'Backing up…' : '💾 Backup'}
              </button>
            </div>

          </div>
        </Section>

        {/* ── Section 3: Admin Info ───────────────────────────────────────── */}
        <Section title="Admin Info" icon={Info}>
          <div className="space-y-3">
            {[
              { label: 'Dashboard Passcode', value: '••••  (4 digits)', icon: '🔐' },
              { label: 'Server Host',         value: window.location.hostname, icon: <Server size={13} /> },
              { label: 'Backend Port',        value: '5000 (HTTPS)', icon: '🌐' },
              { label: 'App Version',         value: health?.version || 'v1.0.0', icon: '📦' },
              { label: 'Environment',         value: health?.environment || 'development', icon: '⚙️' },
              { label: 'Sensor Mode',         value: 'CSV Playback (real client data)', icon: '📊' },
            ].map(({ label, value, icon }) => (
              <div key={label} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span>{icon}</span>
                  <span className="font-medium">{label}</span>
                </div>
                <span className="text-xs font-semibold text-gray-700">{value}</span>
              </div>
            ))}
          </div>
        </Section>

      </div>

      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </>
  )
}
