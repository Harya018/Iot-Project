/**
 * src/pages/DashboardPage.jsx
 * Home overview — stat cards, live chart, mini alert preview.
 * Wrapped in an ErrorBoundary to surface crashes instead of blank screen.
 */
import { Component } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import TemperatureCard  from '../components/dashboard/TemperatureCard.jsx'
import StatusCard       from '../components/dashboard/StatusCard.jsx'
import AlertsTodayCard  from '../components/dashboard/AlertsTodayCard.jsx'
import UptimeCard       from '../components/dashboard/UptimeCard.jsx'
import LiveChart        from '../components/dashboard/LiveChart.jsx'
import MiniAlertLog     from '../components/dashboard/MiniAlertLog.jsx'

/* ── Error boundary ── catches any render crash and shows a readable message ── */
class ErrorBoundary extends Component {
  state = { error: null }
  static getDerivedStateFromError(error) { return { error } }
  render() {
    if (this.state.error) {
      return (
        <div style={{
          padding: 24, color: '#991B1B', background: '#FEF2F2',
          borderRadius: 12, margin: 24, fontFamily: 'monospace', fontSize: 13,
        }}>
          <strong>Dashboard render error:</strong>
          <pre style={{ marginTop: 8, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {this.state.error.message}
          </pre>
          <button
            onClick={() => this.setState({ error: null })}
            style={{ marginTop: 12, padding: '6px 16px', background: '#7C3AED', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer' }}
          >
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

/* ── Dashboard page ─────────────────────────────────────────────────────────── */
export default function DashboardPage({ wsData, health, thresholds, onAlertCount }) {
  // Defensive destructure — all values have safe defaults
  const lastReading     = wsData?.lastReading     ?? null
  const readings        = wsData?.readings        ?? []
  const isConnected     = wsData?.isConnected     ?? false
  const connectionStatus= wsData?.connectionStatus?? 'CONNECTING'

  const navigate = useNavigate()

  return (
    <ErrorBoundary>
      <div className="space-y-5">
        {/* Row 1 — Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <TemperatureCard reading={lastReading} thresholds={thresholds} />
          <StatusCard isConnected={isConnected} connectionStatus={connectionStatus} />
          <AlertsTodayCard count={health?.alerts_today ?? 0} />
          <UptimeCard uptimeSeconds={health?.uptime_seconds ?? null} />
        </div>

        {/* Row 2 — Live chart */}
        <LiveChart readings={readings} thresholds={thresholds} />

        {/* Row 3 — Mini alert preview */}
        <div className="card">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <div>
              <h3 className="text-sm font-semibold text-gray-800">Recent Alerts</h3>
              <p className="text-xs text-gray-500 mt-0.5">Last 5 breach events</p>
            </div>
            <button
              onClick={() => navigate('/alerts')}
              className="flex items-center gap-1.5 text-xs font-semibold text-purple-600 hover:text-purple-700"
            >
              View all alerts <ArrowRight size={13} />
            </button>
          </div>
          <div className="p-5">
            <MiniAlertLog limit={5} onCountChange={onAlertCount} />
          </div>
        </div>
      </div>
    </ErrorBoundary>
  )
}
