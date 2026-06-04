/** src/components/dashboard/StatusCard.jsx */
import { Wifi, WifiOff } from 'lucide-react'

export default function StatusCard({ isConnected, connectionStatus }) {
  const color = isConnected ? '#10B981' : '#EF4444'
  const bg    = isConnected ? '#ECFDF5' : '#FEF2F2'

  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Connection</span>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: bg }}>
          {isConnected
            ? <Wifi size={16} style={{ color }} />
            : <WifiOff size={16} style={{ color }} />
          }
        </div>
      </div>
      <div>
        <p className="text-2xl font-bold" style={{ color }}>
          {connectionStatus || 'CONNECTING'}
        </p>
        <p className="text-xs text-gray-400 mt-0.5">WebSocket stream</p>
      </div>
      <div className="flex items-center gap-1.5">
        <span
          className={`status-dot ${isConnected ? 'bg-emerald-500' : 'bg-red-500'}`}
        />
        <span className="text-xs text-gray-500">
          {isConnected ? 'Receiving live readings' : 'Attempting to reconnect…'}
        </span>
      </div>
    </div>
  )
}
