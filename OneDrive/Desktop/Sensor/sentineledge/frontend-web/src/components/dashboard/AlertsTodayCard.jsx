/** src/components/dashboard/AlertsTodayCard.jsx */
import { Bell } from 'lucide-react'

export default function AlertsTodayCard({ count }) {
  const hasAlerts = count > 0
  const color = hasAlerts ? '#F59E0B' : '#10B981'
  const bg    = hasAlerts ? '#FFFBEB' : '#ECFDF5'

  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Alerts Today</span>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: bg }}>
          <Bell size={16} style={{ color }} />
        </div>
      </div>
      <div>
        <p className="text-2xl font-bold" style={{ color }}>{count ?? '—'}</p>
        <p className="text-xs text-gray-400 mt-0.5">
          {hasAlerts ? 'Breach events today' : 'All clear today'}
        </p>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="status-dot" style={{ background: color }} />
        <span className="text-xs text-gray-500">
          {hasAlerts ? `${count} alert${count !== 1 ? 's' : ''} fired` : 'No alerts today'}
        </span>
      </div>
    </div>
  )
}
