/**
 * src/components/dashboard/ThresholdConfig.jsx
 * Admin-only threshold update / reset form.
 */
import { useState, useEffect, useCallback } from 'react'
import { Settings2, RotateCcw } from 'lucide-react'
import { fetchThresholds, updateThresholds, resetThresholds } from '../../services/api.js'
import { utcToIST } from '../../utils/time.js'
import Card from '../shared/Card.jsx'
import Badge from '../shared/Badge.jsx'
import AdminGuard from '../shared/AdminGuard.jsx'

export default function ThresholdConfig({ isAdmin, onAdminClick, onChanged }) {
  const [data,    setData]    = useState(null)
  const [high,    setHigh]    = useState(40)
  const [low,     setLow]     = useState(35)
  const [saving,  setSaving]  = useState(false)
  const [resetting,setResetting]=useState(false)
  const [msg,     setMsg]     = useState(null)  // { type:'success'|'error', text }

  const load = useCallback(async () => {
    try {
      const d = await fetchThresholds()
      setData(d)
      setHigh(d.temperature?.high ?? 40)
      setLow(d.temperature?.low ?? 35)
    } catch { /* silent */ }
  }, [])

  useEffect(() => { load() }, [load])

  const handleUpdate = async (e) => {
    e.preventDefault()
    if (Number(high) <= Number(low)) {
      setMsg({ type:'error', text: 'High threshold must be greater than low.' })
      return
    }
    setSaving(true); setMsg(null)
    try {
      await updateThresholds({ temp_high: Number(high), temp_low: Number(low) })
      setMsg({ type:'success', text: 'Thresholds updated successfully.' })
      load(); onChanged?.()
    } catch (e) {
      setMsg({ type:'error', text: e.message })
    } finally { setSaving(false) }
  }

  const handleReset = async () => {
    if (!confirm('Reset thresholds to factory defaults (40°C / 35°C)?')) return
    setResetting(true); setMsg(null)
    try {
      await resetThresholds()
      setMsg({ type:'success', text: 'Thresholds reset to defaults.' })
      load(); onChanged?.()
    } catch (e) {
      setMsg({ type:'error', text: e.message })
    } finally { setResetting(false) }
  }

  const isOverride = data?.source === 'runtime_override'

  const form = (
    <form onSubmit={handleUpdate} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium text-gray-600 mb-1 block">
            High Threshold (°C) <span className="text-red-400">↑</span>
          </label>
          <input
            className="form-input"
            type="number" step="0.1" min="-50" max="150"
            value={high}
            onChange={e => setHigh(e.target.value)}
            disabled={!isAdmin}
          />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-600 mb-1 block">
            Low Threshold (°C) <span className="text-blue-400">↓</span>
          </label>
          <input
            className="form-input"
            type="number" step="0.1" min="-50" max="150"
            value={low}
            onChange={e => setLow(e.target.value)}
            disabled={!isAdmin}
          />
        </div>
      </div>

      {isOverride && data?.last_changed && (
        <p className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2">
          ⚡ Runtime override active since {utcToIST(data.last_changed)}
        </p>
      )}

      {msg && (
        <p className={`text-xs rounded-lg px-3 py-2 ${
          msg.type === 'success' ? 'text-emerald-700 bg-emerald-50' : 'text-red-700 bg-red-50'
        }`}>
          {msg.text}
        </p>
      )}

      <p className="text-xs text-gray-400">
        Changes take effect immediately. Reset restores factory defaults (40°C / 35°C).
      </p>

      {isAdmin && (
        <div className="flex gap-2 pt-1">
          <button type="submit" disabled={saving} className="btn btn-primary btn-sm flex-1">
            <Settings2 size={13} /> {saving ? 'Saving…' : 'Update Thresholds'}
          </button>
          <button
            type="button"
            onClick={handleReset}
            disabled={resetting}
            className="btn btn-ghost btn-sm"
          >
            <RotateCcw size={13} /> {resetting ? 'Resetting…' : 'Reset'}
          </button>
        </div>
      )}
    </form>
  )

  return (
    <Card
      title="Threshold Configuration"
      subtitle="Breach detection boundaries"
      headerRight={
        <Badge
          color={isOverride ? 'orange' : 'green'}
          label={isOverride ? 'Override' : 'Default'}
          dot={false}
        />
      }
    >
      <AdminGuard isAdmin={isAdmin} onUnlock={onAdminClick}>
        {form}
      </AdminGuard>
    </Card>
  )
}
