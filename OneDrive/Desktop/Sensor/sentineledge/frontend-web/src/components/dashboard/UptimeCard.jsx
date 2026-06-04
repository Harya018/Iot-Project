/** src/components/dashboard/UptimeCard.jsx */
import { Clock } from 'lucide-react'

function humanUptime(seconds) {
  if (!seconds && seconds !== 0) return '—'
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (d > 0) return `${d}d ${h}h ${m}m`
  if (h > 0) return `${h}h ${m}m ${s}s`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

export default function UptimeCard({ uptimeSeconds }) {
  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Server Uptime</span>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: '#ECFDF5' }}>
          <Clock size={16} style={{ color: '#10B981' }} />
        </div>
      </div>
      <div>
        <p className="text-2xl font-bold text-emerald-600">{humanUptime(uptimeSeconds)}</p>
        <p className="text-xs text-gray-400 mt-0.5">Since last restart</p>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="status-dot bg-emerald-500" />
        <span className="text-xs text-gray-500">Server running normally</span>
      </div>
    </div>
  )
}
