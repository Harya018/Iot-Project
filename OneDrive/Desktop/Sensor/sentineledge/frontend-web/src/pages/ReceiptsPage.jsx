/**
 * src/pages/ReceiptsPage.jsx
 * Proof of delivery — all notification receipts.
 */
import { useState, useEffect, useCallback } from 'react'
import { Receipt, RefreshCw, Filter, CheckCircle, XCircle, Mail, MessageSquare } from 'lucide-react'
import { fetchReceipts } from '../services/api.js'
import { utcToIST, timeAgo } from '../utils/time.js'
import Badge from '../components/shared/Badge.jsx'

export default function ReceiptsPage() {
  const [receipts, setReceipts] = useState([])
  const [loading,  setLoading]  = useState(false)
  const [channel,  setChannel]  = useState('all')
  const [status,   setStatus]   = useState('all')

  const load = useCallback(async () => {
    setLoading(true)
    try { setReceipts(await fetchReceipts(200, channel, status)) }
    catch { /* silent */ }
    finally { setLoading(false) }
  }, [channel, status])

  useEffect(() => { load() }, [load])

  const sent    = receipts.filter(r => r.success).length
  const failed  = receipts.filter(r => !r.success).length
  const rate    = receipts.length ? Math.round((sent / receipts.length) * 100) : 0
  const emailOk = receipts.filter(r => r.channel === 'email' && r.success).length
  const smsOk   = receipts.filter(r => r.channel === 'sms'   && r.success).length

  const FilterBtn = ({ value, current, set, label }) => (
    <button
      onClick={() => set(value)}
      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
        current === value
          ? 'bg-purple-600 text-white'
          : 'bg-white border border-gray-200 text-gray-600 hover:border-purple-300'
      }`}
    >
      {label}
    </button>
  )

  return (
    <div className="space-y-5">
      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Sent', value: receipts.length, icon: <Receipt size={18} />, color: '#7C3AED' },
          { label: 'Success Rate', value: `${rate}%`, icon: <CheckCircle size={18} />, color: '#10B981' },
          { label: 'Email Success', value: emailOk, icon: <Mail size={18} />, color: '#3B82F6' },
          { label: 'SMS Success', value: smsOk, icon: <MessageSquare size={18} />, color: '#F59E0B' },
        ].map(s => (
          <div key={s.label} className="card p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                 style={{ background: s.color + '15', color: s.color }}>
              {s.icon}
            </div>
            <div>
              <p className="text-xl font-bold" style={{ color: s.color }}>{s.value}</p>
              <p className="text-xs text-gray-500">{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="card px-5 py-4 flex flex-wrap gap-4 items-center">
        <Filter size={13} className="text-gray-400" />

        <div className="flex gap-1">
          <FilterBtn value="all"   current={channel} set={setChannel} label="All Channels" />
          <FilterBtn value="email" current={channel} set={setChannel} label="📧 Email" />
          <FilterBtn value="sms"   current={channel} set={setChannel} label="💬 SMS" />
        </div>

        <div className="flex gap-1">
          <FilterBtn value="all"     current={status} set={setStatus} label="All Status" />
          <FilterBtn value="success" current={status} set={setStatus} label="✅ Success" />
          <FilterBtn value="failed"  current={status} set={setStatus} label="❌ Failed" />
        </div>

        <button onClick={load} disabled={loading} className="btn btn-ghost btn-sm ml-auto">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-100">
          <span className="text-sm font-semibold text-gray-800">{receipts.length} receipts</span>
        </div>
        {receipts.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <CheckCircle size={32} className="mx-auto mb-2 text-emerald-400" />
            <p>No receipts found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead><tr>
                <th>Alert ID</th>
                <th>Alert Time (IST)</th>
                <th>Channel</th>
                <th>Subscriber</th>
                <th>Level</th>
                <th>Sent At (IST)</th>
                <th>Status</th>
                <th>Error</th>
              </tr></thead>
              <tbody>
                {receipts.map(r => (
                  <tr key={r.id}>
                    <td className="font-mono text-xs">#{r.alert_id}</td>
                    <td className="text-xs text-gray-500">{utcToIST(r.alert_time)}</td>
                    <td>
                      {r.channel === 'email'
                        ? <span className="flex items-center gap-1 text-xs"><Mail size={11} /> Email</span>
                        : <span className="flex items-center gap-1 text-xs"><MessageSquare size={11} /> SMS</span>
                      }
                    </td>
                    <td className="font-medium">{r.subscriber_name || '—'}</td>
                    <td><Badge color="gray" label={`L${r.escalation_level}`} small /></td>
                    <td className="text-xs text-gray-500">
                      <p>{utcToIST(r.sent_at)}</p>
                      <p className="text-gray-400">{timeAgo(r.sent_at)}</p>
                    </td>
                    <td>
                      {r.success
                        ? <CheckCircle size={16} className="text-emerald-500" />
                        : <XCircle    size={16} className="text-red-500" />
                      }
                    </td>
                    <td className="text-xs text-red-500 max-w-[140px] truncate" title={r.error_message}>
                      {r.error_message || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
