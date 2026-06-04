/**
 * src/pages/HealthPage.jsx
 * Full system health — modules, DB stats, config changes, backup.
 */
import { useState, useEffect, useCallback } from 'react'
import {
  RefreshCw, Thermometer, Database, Mail, MessageSquare,
  Wifi, CheckCircle, AlertTriangle, XCircle, Archive
} from 'lucide-react'
import { fetchHealth, fetchDatabaseStats, fetchAdminConfigChanges, createBackup } from '../services/api.js'
import { utcToIST, timeAgo } from '../utils/time.js'
import Badge from '../components/shared/Badge.jsx'
import { useToast, ToastContainer } from '../components/shared/Toast.jsx'

const MODULE_ICONS = {
  sensor:    <Thermometer   size={20} />,
  database:  <Database      size={20} />,
  email:     <Mail          size={20} />,
  sms:       <MessageSquare size={20} />,
  websocket: <Wifi          size={20} />,
}

function statusBadge(s) {
  if (!s || s === 'not_built') return { color:'gray', label:'Not Built' }
  if (s === 'ok')              return { color:'green', label:'OK' }
  if (s === 'starting')        return { color:'amber', label:'Starting' }
  if (s.startsWith('error'))   return { color:'red',   label:'Error' }
  return { color:'gray', label: s }
}

function statusIcon(s) {
  if (!s || s === 'not_built') return <Archive size={16} className="text-gray-400" />
  if (s === 'ok')              return <CheckCircle size={16} className="text-emerald-500" />
  if (s === 'starting')        return <AlertTriangle size={16} className="text-amber-500" />
  return <XCircle size={16} className="text-red-500" />
}

export default function HealthPage() {
  const { toasts, addToast, dismiss } = useToast()
  const [health,  setHealth]  = useState(null)
  const [stats,   setStats]   = useState(null)
  const [changes, setChanges] = useState([])
  const [loading, setLoading] = useState(false)
  const [backing, setBacking] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [h, s, c] = await Promise.allSettled([
        fetchHealth(), fetchDatabaseStats(), fetchAdminConfigChanges()
      ])
      if (h.status === 'fulfilled') setHealth(h.value)
      if (s.status === 'fulfilled') setStats(s.value)
      if (c.status === 'fulfilled') setChanges(c.value)
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { load(); const t = setInterval(load, 30000); return () => clearInterval(t) }, [load])

  const handleBackup = async () => {
    setBacking(true)
    try {
      const r = await createBackup()
      addToast({ type:'success', message:`✅ Backup: ${r.filename} (${r.size_mb} MB)` })
      load()
    } catch (e) { addToast({ type:'error', message:'Backup failed: ' + e.message }) }
    finally { setBacking(false) }
  }

  const modules  = health?.modules || {}
  const overall  = health?.status
  const overallBg = overall === 'ok' ? '#ECFDF5' : overall === 'degraded' ? '#FFFBEB' : '#FEF2F2'
  const overallColor = overall === 'ok' ? '#065F46' : overall === 'degraded' ? '#92400E' : '#991B1B'

  return (
    <>
      <div className="space-y-5">
        {/* Overall status banner */}
        <div
          className="card px-6 py-4 flex items-center justify-between"
          style={{ background: overallBg, border: `1px solid ${overallColor}30` }}
        >
          <div className="flex items-center gap-3">
            {overall === 'ok'
              ? <CheckCircle size={22} style={{ color: '#10B981' }} />
              : <AlertTriangle size={22} style={{ color: '#F59E0B' }} />
            }
            <div>
              <p className="font-bold" style={{ color: overallColor, fontSize: '0.95rem' }}>
                System Status: {overall?.toUpperCase() || 'UNKNOWN'}
              </p>
              <p className="text-xs" style={{ color: overallColor, opacity: 0.8 }}>
                {overall === 'ok' ? 'All systems operational' : 'One or more modules need attention'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">v{health?.version || '1.0.0'}</span>
            <button onClick={load} disabled={loading} className="btn btn-ghost btn-sm">
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* Module grid */}
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Module Status</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {['sensor','database','email','sms','websocket'].map(mod => {
              const val = modules[mod] || 'unknown'
              const sb  = statusBadge(val)
              const isError = val.startsWith('error')
              return (
                <div key={mod} className="card p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center"
                        style={{
                          background: sb.color === 'green' ? '#ECFDF5' : sb.color === 'red' ? '#FEF2F2' : '#FFFBEB',
                          color: sb.color === 'green' ? '#10B981' : sb.color === 'red' ? '#EF4444' : '#F59E0B',
                        }}
                      >
                        {MODULE_ICONS[mod]}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-800 capitalize">{mod}</p>
                        <Badge color={sb.color} label={sb.label} small />
                      </div>
                    </div>
                    {statusIcon(val)}
                  </div>
                  {isError && (
                    <p className="text-xs text-red-600 bg-red-50 rounded-lg px-2.5 py-1.5 mt-2">
                      {val.replace('error: ', '')}
                    </p>
                  )}
                  {val === 'not_built' && (
                    <p className="text-xs text-gray-400 mt-2">Module not implemented yet</p>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* DB Stats */}
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Database Statistics</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Total Readings', value: stats?.readings_count  ?? '—', icon: '📡' },
              { label: 'Total Alerts',   value: stats?.alerts_count    ?? '—', icon: '🔔' },
              { label: 'DB Size',        value: stats ? `${stats.database_size_mb} MB` : '—', icon: '💾' },
              { label: 'Backups',        value: stats?.backup_count    ?? '—', icon: '📦' },
            ].map(s => (
              <div key={s.label} className="card p-4 flex items-center gap-3">
                <span className="text-2xl">{s.icon}</span>
                <div>
                  <p className="text-lg font-bold text-gray-900">{s.value}</p>
                  <p className="text-xs text-gray-500">{s.label}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 flex justify-end">
            <button onClick={handleBackup} disabled={backing} className="btn btn-info btn-sm">
              <Database size={13} /> {backing ? 'Creating backup…' : 'Create Backup Now'}
            </button>
          </div>
        </div>

        {/* Recent config changes */}
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Recent Config Changes</h2>
          <div className="card" style={{ overflow: 'hidden' }}>
            {changes.length === 0 ? (
              <div className="py-8 text-center text-gray-400 text-sm">No configuration changes recorded.</div>
            ) : (
              <table className="data-table w-full">
                <thead><tr>
                  <th>Field</th>
                  <th>Old Value</th>
                  <th>New Value</th>
                  <th>Changed By</th>
                  <th>Time (IST)</th>
                </tr></thead>
                <tbody>
                  {changes.slice(0,20).map(c => (
                    <tr key={c.id}>
                      <td className="font-medium">{c.field_name}</td>
                      <td className="text-gray-400">{c.old_value}</td>
                      <td className="font-semibold text-purple-700">{c.new_value}</td>
                      <td className="text-gray-500">{c.changed_by}</td>
                      <td>
                        <p className="text-xs">{timeAgo(c.changed_at)}</p>
                        <p className="text-xs text-gray-400">{utcToIST(c.changed_at)}</p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </>
  )
}
