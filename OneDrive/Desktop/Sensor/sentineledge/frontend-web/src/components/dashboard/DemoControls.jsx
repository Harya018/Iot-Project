/**
 * src/components/dashboard/DemoControls.jsx
 * Admin-only demo and testing controls.
 */
import { useState } from 'react'
import { Zap, Database, AlertTriangle } from 'lucide-react'
import { simulateBreach, createBackup } from '../../services/api.js'
import Card from '../shared/Card.jsx'
import AdminGuard from '../shared/AdminGuard.jsx'
import Badge from '../shared/Badge.jsx'

export default function DemoControls({ isAdmin, onAdminClick, onToast }) {
  const [simulating, setSimulating] = useState(false)
  const [backing,    setBacking]    = useState(false)

  const handleSimulate = async () => {
    setSimulating(true)
    try {
      await simulateBreach()
      onToast?.({ type:'warning', message: '🌡️ Breach simulation active — temperature forced to 43°C for 10 readings.' })
    } catch (e) {
      onToast?.({ type:'error', message: 'Simulate breach failed: ' + e.message })
    } finally { setSimulating(false) }
  }

  const handleBackup = async () => {
    setBacking(true)
    try {
      const r = await createBackup()
      onToast?.({ type:'success', message: `✅ Backup created: ${r.filename} (${r.size_mb} MB)` })
    } catch (e) {
      onToast?.({ type:'error', message: 'Backup failed: ' + e.message })
    } finally { setBacking(false) }
  }

  const controls = (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {/* Simulate breach */}
        <div className="rounded-xl border border-orange-200 bg-orange-50 p-4 flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-orange-100 flex items-center justify-center">
              <Zap size={16} className="text-orange-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-orange-800">Simulate Breach</p>
              <p className="text-xs text-orange-600">Forces temp to 43°C</p>
            </div>
          </div>
          <button
            onClick={handleSimulate}
            disabled={simulating || !isAdmin}
            className="btn btn-warning w-full justify-center"
          >
            {simulating ? 'Simulating…' : '⚡ Trigger Breach'}
          </button>
        </div>

        {/* Create backup */}
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
              <Database size={16} className="text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-blue-800">Database Backup</p>
              <p className="text-xs text-blue-600">Snapshot to disk</p>
            </div>
          </div>
          <button
            onClick={handleBackup}
            disabled={backing || !isAdmin}
            className="btn btn-info w-full justify-center"
          >
            {backing ? 'Backing up…' : '💾 Create Backup'}
          </button>
        </div>
      </div>

      <div className="flex items-start gap-2 text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2.5">
        <AlertTriangle size={13} className="text-amber-500 flex-shrink-0 mt-0.5" />
        <span>
          Simulate breach forces temperature to 43°C for 10 readings, triggering all alert channels
          and the audio alarm. Use in development only.
        </span>
      </div>
    </div>
  )

  return (
    <Card
      title="Demo Controls"
      subtitle="Testing and maintenance"
      headerRight={<Badge color="amber" label="Admin Only" dot={false} />}
    >
      <AdminGuard isAdmin={isAdmin} onUnlock={onAdminClick}>
        {controls}
      </AdminGuard>
    </Card>
  )
}
