/**
 * src/pages/AlertsPage.jsx
 * Full dedicated alerts page with filters and full AlertLog.
 */
import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Filter, Mail, MessageSquare, CheckCircle, XCircle, CheckCheck } from 'lucide-react'
import { fetchAlerts, acknowledgeAlert } from '../services/api.js'
import { getSeverityColor, getDirectionLabel, getSeverityLabel } from '../utils/severity.js'
import { utcToIST, timeAgo } from '../utils/time.js'
import Badge from '../components/shared/Badge.jsx'

const SEV_COLORS  = { WARNING:'amber', CRITICAL:'orange', EMERGENCY:'red' }
const escBadge = (level) => {
  if (level >= 3) return { color:'red', label:'CRITICAL ESC', pulse:true }
  if (level === 2) return { color:'orange', label:'Escalated' }
  return { color:'amber', label:'Level 1' }
}

export default function AlertsPage({ onCountChange }) {
  const [alerts,   setAlerts]   = useState([])
  const [loading,  setLoading]  = useState(false)
  const [filterAck, setFilterAck] = useState('all')   // all | unacknowledged | acknowledged
  const [filterSev, setFilterSev] = useState('all')   // all | WARNING | CRITICAL | EMERGENCY
  const [filterDate, setFilterDate] = useState('today') // today | week | all

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchAlerts(100)
      setAlerts(data)
      onCountChange?.(data.filter(a => !a.acknowledged).length)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }, [onCountChange])

  useEffect(() => { load(); const t = setInterval(load, 10000); return () => clearInterval(t) }, [load])

  const handleAck = async (alert) => {
    const name = prompt('Acknowledge as (your name):')
    if (!name?.trim()) return
    try {
      await acknowledgeAlert(alert.id, name.trim())
      setAlerts(prev => prev.map(a =>
        a.id === alert.id ? { ...a, acknowledged: true, acknowledged_by: name.trim() } : a
      ))
    } catch (e) { alert('Failed: ' + e.message) }
  }

  // Date filter
  const now = Date.now()
  const filtered = alerts.filter(a => {
    if (filterAck === 'unacknowledged' && a.acknowledged) return false
    if (filterAck === 'acknowledged'   && !a.acknowledged) return false
    if (filterSev !== 'all' && a.severity?.toUpperCase() !== filterSev) return false
    if (filterDate === 'today') {
      const diff = now - new Date(a.timestamp).getTime()
      if (diff > 86400000) return false
    }
    if (filterDate === 'week') {
      const diff = now - new Date(a.timestamp).getTime()
      if (diff > 7 * 86400000) return false
    }
    return true
  })

  const FilterBtn = ({ value, current, set, label }) => (
    <button
      onClick={() => set(value)}
      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
        current === value
          ? 'bg-purple-600 text-white shadow-sm'
          : 'bg-white text-gray-600 border border-gray-200 hover:border-purple-300'
      }`}
    >
      {label}
    </button>
  )

  return (
    <div className="space-y-5">
      {/* Header stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total', value: alerts.length, color: '#7C3AED' },
          { label: 'Unacknowledged', value: alerts.filter(a => !a.acknowledged).length, color: '#EF4444' },
          { label: 'Acknowledged', value: alerts.filter(a => a.acknowledged).length, color: '#10B981' },
        ].map(s => (
          <div key={s.label} className="card p-4 flex items-center gap-3">
            <span className="text-2xl font-bold" style={{ color: s.color }}>{s.value}</span>
            <span className="text-xs text-gray-500 font-medium">{s.label}</span>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="card px-5 py-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center gap-1.5">
            <Filter size={13} className="text-gray-400" />
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</span>
          </div>
          <div className="flex gap-1.5">
            <FilterBtn value="all"             current={filterAck} set={setFilterAck} label="All" />
            <FilterBtn value="unacknowledged"  current={filterAck} set={setFilterAck} label="Unacknowledged" />
            <FilterBtn value="acknowledged"    current={filterAck} set={setFilterAck} label="Acknowledged" />
          </div>

          <div className="flex items-center gap-1.5 ml-4">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Severity</span>
          </div>
          <div className="flex gap-1.5">
            <FilterBtn value="all"       current={filterSev} set={setFilterSev} label="All" />
            <FilterBtn value="WARNING"   current={filterSev} set={setFilterSev} label="⚠ Warning" />
            <FilterBtn value="CRITICAL"  current={filterSev} set={setFilterSev} label="🔶 Critical" />
            <FilterBtn value="EMERGENCY" current={filterSev} set={setFilterSev} label="🔴 Emergency" />
          </div>

          <div className="flex items-center gap-1.5 ml-4">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Date</span>
          </div>
          <div className="flex gap-1.5">
            <FilterBtn value="today" current={filterDate} set={setFilterDate} label="Today" />
            <FilterBtn value="week"  current={filterDate} set={setFilterDate} label="Last 7 days" />
            <FilterBtn value="all"   current={filterDate} set={setFilterDate} label="All time" />
          </div>

          <button onClick={load} disabled={loading} className="btn btn-ghost btn-sm ml-auto">
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {/* Alerts table */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <span className="text-sm font-semibold text-gray-800">
            {filtered.length} alert{filtered.length !== 1 ? 's' : ''} shown
          </span>
          <span className="text-xs text-gray-400">Auto-refreshes every 10s</span>
        </div>

        {filtered.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-16 text-gray-400">
            <CheckCircle size={36} className="text-emerald-400" />
            <p className="font-medium text-gray-500">No alerts match the current filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead><tr>
                <th>Severity</th>
                <th>Reading</th>
                <th>Direction</th>
                <th>Time (IST)</th>
                <th>Delivery</th>
                <th>Escalation</th>
                <th>Action</th>
              </tr></thead>
              <tbody>
                {filtered.map(alert => {
                  const sc = getSeverityColor(alert.severity)
                  const ds = alert.delivery_status || {}
                  const eb = escBadge(alert.escalation_level)
                  return (
                    <tr key={alert.id}>
                      <td>
                        <div className="flex items-center gap-2">
                          <span className="status-dot" style={{ background: sc.dot }} />
                          <Badge color={SEV_COLORS[alert.severity?.toUpperCase()] || 'gray'}
                                 label={getSeverityLabel(alert.severity)} small />
                        </div>
                      </td>
                      <td>
                        <span className="font-bold text-gray-800">{alert.value?.toFixed(1)}°C</span>
                        <span className="text-gray-400"> / {alert.threshold?.toFixed(1)}°C</span>
                      </td>
                      <td>
                        <span className="text-xs text-gray-500">{getDirectionLabel(alert.direction)}</span>
                      </td>
                      <td>
                        <p className="text-xs font-medium text-gray-700">{timeAgo(alert.timestamp)}</p>
                        <p className="text-xs text-gray-400">{utcToIST(alert.timestamp)}</p>
                      </td>
                      <td>
                        <div className="flex items-center gap-1">
                          {ds.email === 'sent' ? <CheckCircle size={13} className="text-emerald-500" /> : <XCircle size={13} className="text-red-400" />}
                          <Mail size={11} className="text-gray-300" />
                          {ds.sms === 'sent' ? <CheckCircle size={13} className="text-emerald-500" /> : <XCircle size={13} className="text-red-400" />}
                          <MessageSquare size={11} className="text-gray-300" />
                        </div>
                      </td>
                      <td><Badge color={eb.color} label={eb.label} pulse={eb.pulse} small /></td>
                      <td>
                        {alert.acknowledged ? (
                          <div className="flex items-center gap-1 text-emerald-600 text-xs">
                            <CheckCheck size={13} />
                            <span className="truncate max-w-[80px]">{alert.acknowledged_by || 'Acked'}</span>
                          </div>
                        ) : (
                          <button onClick={() => handleAck(alert)} className="btn btn-ghost btn-xs">Ack</button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
