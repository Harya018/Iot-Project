/**
 * SubAdminApp.jsx — Sub-Admin Dashboard
 *
 * Identical to the main admin dashboard EXCEPT:
 *   - Settings page is hidden/inaccessible
 *   - Admin Profile page is hidden/inaccessible
 *   - Login uses name + password (admins table) instead of a passcode
 *   - After login, role is checked: 'sub' → this dashboard; 'main' → redirect to /
 *
 * Routes are prefixed with /sub-admin/*
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { Routes, Route, Navigate, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Bell, Terminal, Archive, BarChart2,
  Receipt, Monitor, Users, Activity, ClipboardList,
  Thermometer, LogOut, CheckCheck, Eye, EyeOff, ShieldAlert,
} from 'lucide-react'
import { VolumeX } from 'lucide-react'

import useWebSocket  from './hooks/useWebSocket.js'
import useAudioAlarm from './hooks/useAudioAlarm.js'
import { ToastContainer, useToast } from './components/shared/Toast.jsx'
import { fetchHealth } from './services/api.js'

// Pages visible to sub-admins (no Settings, no Admin Profile)
import DashboardPage   from './pages/DashboardPage.jsx'
import AlertsPage      from './pages/AlertsPage.jsx'
import LogsPage        from './pages/LogsPage.jsx'
import HistoryPage     from './pages/HistoryPage.jsx'
import ReportsPage     from './pages/ReportsPage.jsx'
import ReceiptsPage    from './pages/ReceiptsPage.jsx'
import MonitorPage     from './pages/MonitorPage.jsx'
import SubscribersPage from './pages/SubscribersPage.jsx'
import HealthPage      from './pages/HealthPage.jsx'
import EventsPage      from './pages/EventsPage.jsx'
import AckLogPage      from './pages/AckLogPage.jsx'

// ── Sub-Admin Login ───────────────────────────────────────────────────────────
function SubAdminLoginPage() {
  const [name,    setName]    = useState('')
  const [pwd,     setPwd]     = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [error,   setError]   = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (sessionStorage.getItem('subAdminAuthenticated') === 'true') {
      navigate('/sub-admin/dashboard', { replace: true })
    }
  }, [navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await fetch('/api/auth/admin-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), password: pwd }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail?.message || 'Invalid credentials')
        return
      }
      if (data.role === 'main') {
        // Main admin should use the main dashboard
        setError('Please use the main admin dashboard to log in as main admin.')
        return
      }
      sessionStorage.setItem('subAdminAuthenticated', 'true')
      sessionStorage.setItem('subAdminName', data.name)
      sessionStorage.setItem('subAdminToken', data.token)
      navigate('/sub-admin/dashboard', { replace: true })
    } catch {
      setError('Connection failed. Check your server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4"
         style={{ background: 'linear-gradient(135deg, #1E1B4B 0%, #2D2680 50%, #1E1B4B 100%)' }}>
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-sm">
        <div className="flex flex-col items-center mb-6">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-3"
               style={{ background: '#7c3aed15' }}>
            <ShieldAlert size={28} style={{ color: '#7c3aed' }} />
          </div>
          <h1 className="text-xl font-bold text-gray-900">Sub-Admin Login</h1>
          <p className="text-xs text-gray-500 mt-1">SentinelEdge Monitoring System</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1.5">Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              required
              placeholder="Your admin name"
              className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-400"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1.5">Password</label>
            <div className="relative">
              <input
                type={showPwd ? 'text' : 'password'}
                value={pwd}
                onChange={e => setPwd(e.target.value)}
                required
                placeholder="Your password"
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm pr-10 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-400"
              />
              <button type="button" onClick={() => setShowPwd(v => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                {showPwd ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>
          {error && (
            <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
          )}
          <button type="submit" disabled={loading}
                  className="w-full py-2.5 rounded-lg font-bold text-white text-sm disabled:opacity-50"
                  style={{ background: '#7c3aed' }}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
        <p className="text-center text-xs text-gray-400 mt-4">
          Main admin?{' '}
          <a href="/" className="text-purple-600 hover:underline">Use main dashboard</a>
        </p>
      </div>
    </div>
  )
}

// ── Sub-Admin Sidebar ─────────────────────────────────────────────────────────
const SUB_NAV = [
  { to: '/sub-admin/dashboard',   icon: LayoutDashboard, label: 'Dashboard'    },
  { to: '/sub-admin/alerts',      icon: Bell,            label: 'Alerts'        },
  { to: '/sub-admin/logs',        icon: Terminal,        label: 'Live Logs'     },
  { to: '/sub-admin/history',     icon: Archive,         label: 'History'       },
  { to: '/sub-admin/reports',     icon: BarChart2,       label: 'Reports'       },
  { to: '/sub-admin/receipts',    icon: Receipt,         label: 'Receipts'      },
  { to: '/sub-admin/monitor',     icon: Monitor,         label: 'Monitor'       },
  { to: '/sub-admin/subscribers', icon: Users,           label: 'Subscribers'   },
  { to: '/sub-admin/health',      icon: Activity,        label: 'Health'        },
  { to: '/sub-admin/events',      icon: ClipboardList,   label: 'Audit Trail'   },
  { to: '/sub-admin/ack-log',     icon: CheckCheck,      label: 'Ack Log'       },
  // ✖ No Settings, ✖ No Admin Profile
]

function SubAdminSidebar({ unreadCount }) {
  const navigate = useNavigate()
  const name = sessionStorage.getItem('subAdminName') || 'Sub-Admin'

  const handleLogout = () => {
    sessionStorage.removeItem('subAdminAuthenticated')
    sessionStorage.removeItem('subAdminName')
    sessionStorage.removeItem('subAdminToken')
    navigate('/sub-admin', { replace: true })
  }

  return (
    <aside className="sidebar" style={{ overflowY: 'auto' }}>
      <div className="px-4 py-4 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
               style={{ background: '#7C3AED' }}>
            <Thermometer size={18} className="text-white" />
          </div>
          <div className="sidebar-label overflow-hidden">
            <p className="text-white font-bold text-sm leading-tight">SentinelEdge</p>
            <p className="text-xs" style={{ color: '#A5B4FC' }}>Sub-Admin: {name}</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 py-3 space-y-0.5 px-2">
        {SUB_NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg transition-all w-full no-underline text-sm font-medium ${
                isActive ? 'text-white' : 'hover:bg-white/10'
              }`
            }
            style={({ isActive }) => ({
              background: isActive ? '#7C3AED' : undefined,
              color:      isActive ? '#fff'    : '#C7D2FE',
            })}
          >
            {({ isActive }) => (
              <>
                <Icon size={16} style={{ color: isActive ? '#fff' : '#A5B4FC', flexShrink: 0 }} />
                <span className="sidebar-label truncate">{label}</span>
                {to === '/sub-admin/alerts' && unreadCount > 0 && (
                  <span className="sidebar-label ml-auto text-xs font-bold bg-red-500 text-white rounded-full px-1.5 py-0.5 leading-none">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="px-2 py-3 border-t border-white/10 flex-shrink-0">
        <button onClick={handleLogout}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 transition-all text-left text-sm font-medium"
                style={{ color: '#C7D2FE' }}>
          <LogOut size={16} style={{ color: '#A5B4FC', flexShrink: 0 }} />
          <span className="sidebar-label">Logout</span>
        </button>
        <p className="sidebar-label text-center text-xs py-1" style={{ color: '#7C3AED' }}>v1.0.0 · Sub-Admin</p>
      </div>
    </aside>
  )
}

// ── Protected route for sub-admin ─────────────────────────────────────────────
function SubAdminProtected({ children }) {
  if (sessionStorage.getItem('subAdminAuthenticated') !== 'true') {
    return <Navigate to="/sub-admin" replace />
  }
  return children
}

// ── Layout wrapper ────────────────────────────────────────────────────────────
function SubAdminLayout({ children, connectionStatus, unreadCount }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <SubAdminSidebar unreadCount={unreadCount} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', marginLeft: 240 }}>
        <header className="flex items-center justify-between px-6 bg-white border-b border-gray-100"
                style={{ height: 64, position: 'sticky', top: 0, zIndex: 40, flexShrink: 0 }}>
          <span className="text-sm font-bold text-gray-700">Sub-Admin Dashboard</span>
          <span className={`text-xs font-bold px-2 py-1 rounded-full ${
            connectionStatus === 'LIVE' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
          }`}>
            {connectionStatus}
          </span>
        </header>
        <main style={{ flex: 1, overflowY: 'auto', padding: '24px', backgroundColor: '#F8F9FC' }}>
          {children}
        </main>
      </div>
    </div>
  )
}

// ── Root sub-admin app ────────────────────────────────────────────────────────
export default function SubAdminApp() {
  const [alertCount, setAlertCount] = useState(0)
  const [health,     setHealth]     = useState(null)
  const [thresholds, setThresholds] = useState(null)
  const { toasts, addToast, dismiss } = useToast()
  const alarm = useAudioAlarm()
  const { playAlarm } = alarm

  const handleBreach = useCallback((breach) => {
    try { playAlarm(breach?.severity) } catch {}
    addToast({ type: 'error', message: `⚠️ BREACH: ${breach?.value?.toFixed(1) ?? '—'}°C`, duration: 8000 })
  }, [playAlarm, addToast])

  const wsData = useWebSocket({ onBreach: handleBreach })
  const connectionStatus = wsData?.connectionStatus ?? 'CONNECTING'
  const { isPlaying, currentSeverity, stopAlarm } = alarm

  const loadHealth = useCallback(async () => {
    try {
      const h = await fetchHealth()
      setHealth(h)
      if (h.thresholds)
        setThresholds({ temperature: { high: h.thresholds.temp_high, low: h.thresholds.temp_low } })
    } catch {}
  }, [])

  useEffect(() => {
    loadHealth()
    const t = setInterval(loadHealth, 30000)
    return () => clearInterval(t)
  }, [loadHealth])

  const protect = (page) => (
    <SubAdminProtected>
      <SubAdminLayout connectionStatus={connectionStatus} unreadCount={alertCount}>
        {isPlaying && (
          <div className="alarm-banner" style={{ position: 'fixed', top: 0, left: 240, right: 0, zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 24px', background: '#991b1b', color: '#fff' }}>
            <span>🔴 ALARM — {currentSeverity} breach</span>
            <button onClick={stopAlarm} style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#fff', background: 'none', border: 'none', cursor: 'pointer', fontSize: 13 }}>
              <VolumeX size={15} /> Stop Alarm
            </button>
          </div>
        )}
        {page}
      </SubAdminLayout>
    </SubAdminProtected>
  )

  return (
    <>
      <Routes>
        <Route path="/sub-admin"            element={<SubAdminLoginPage />} />
        <Route path="/sub-admin/dashboard"  element={protect(<DashboardPage wsData={wsData} health={health} thresholds={thresholds} onAlertCount={setAlertCount} />)} />
        <Route path="/sub-admin/alerts"     element={protect(<AlertsPage onCountChange={setAlertCount} />)} />
        <Route path="/sub-admin/logs"       element={protect(<LogsPage />)} />
        <Route path="/sub-admin/history"    element={protect(<HistoryPage />)} />
        <Route path="/sub-admin/reports"    element={protect(<ReportsPage />)} />
        <Route path="/sub-admin/receipts"   element={protect(<ReceiptsPage />)} />
        <Route path="/sub-admin/monitor"    element={<SubAdminProtected><MonitorPage wsData={wsData} thresholds={thresholds} /></SubAdminProtected>} />
        <Route path="/sub-admin/subscribers" element={protect(<SubscribersPage />)} />
        <Route path="/sub-admin/health"     element={protect(<HealthPage />)} />
        <Route path="/sub-admin/events"     element={protect(<EventsPage />)} />
        <Route path="/sub-admin/ack-log"    element={protect(<AckLogPage wsData={wsData} />)} />
        {/* Redirect any unknown /sub-admin/* to login */}
        <Route path="/sub-admin/*"          element={<Navigate to="/sub-admin" replace />} />
      </Routes>
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </>
  )
}
