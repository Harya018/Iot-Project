/**
 * src/pages/SubscribersPage.jsx
 * Subscriber management — card layout, PIN set, add/delete.
 * All users are authenticated (passcode checked at login).
 */
import { useState, useEffect, useCallback } from 'react'
import { Plus, Trash2, Key, Check, Phone, Mail, ChevronDown, ChevronUp, Users } from 'lucide-react'
import { fetchSubscribers, addSubscriber, deleteSubscriber, setSubscriberPin } from '../services/api.js'
import Modal from '../components/shared/Modal.jsx'

const EMPTY_FORM = { name:'', phone:'', email:'', escalation_order:1, pin:'' }
const ORDER_META = {
  1: { label:'Primary Responder',   color:'#EF4444', bg:'#FEF2F2' },
  2: { label:'Escalation Contact',  color:'#F59E0B', bg:'#FFFBEB' },
  3: { label:'Final Escalation',    color:'#F97316', bg:'#FFF7ED' },
}

export default function SubscribersPage() {
  const [subs,     setSubs]     = useState([])
  const [loading,  setLoading]  = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [form,     setForm]     = useState(EMPTY_FORM)
  const [saving,   setSaving]   = useState(false)
  const [formErr,  setFormErr]  = useState('')

  const [pinModal,  setPinModal]  = useState(null)
  const [pinValue,  setPinValue]  = useState('')
  const [pinSaving, setPinSaving] = useState(false)
  const [pinErr,    setPinErr]    = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try { setSubs(await fetchSubscribers()) }
    catch { /* silent */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleAdd = async (e) => {
    e.preventDefault()
    setSaving(true); setFormErr('')
    try {
      await addSubscriber({
        name: form.name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim(),
        escalation_order: Number(form.escalation_order),
        ...(form.pin ? { pin: form.pin.trim() } : {}),
      })
      setForm(EMPTY_FORM); setShowForm(false); load()
    } catch (e) { setFormErr(e.message || 'Failed to add subscriber') }
    finally { setSaving(false) }
  }

  const handleDelete = async (id, name) => {
    if (!confirm(`Remove ${name} from subscribers?`)) return
    try { await deleteSubscriber(id); load() }
    catch (e) { alert('Failed: ' + e.message) }
  }

  const handleSetPin = async () => {
    if (!pinValue || !/^\d{4,6}$/.test(pinValue)) { setPinErr('PIN must be 4-6 digits'); return }
    setPinSaving(true); setPinErr('')
    try {
      await setSubscriberPin(pinModal.id, pinValue)
      setPinModal(null); setPinValue(''); load()
    } catch (e) { setPinErr(e.message || 'Failed') }
    finally { setPinSaving(false) }
  }

  return (
    <div className="space-y-5">
      {/* Page actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
            <Users size={20} className="text-purple-600" />
          </div>
          <div>
            <p className="text-sm font-bold text-gray-900">{subs.length} Subscriber{subs.length !== 1 ? 's' : ''}</p>
            <p className="text-xs text-gray-500">Alert escalation chain</p>
          </div>
        </div>
        <button onClick={() => setShowForm(v => !v)} className="btn btn-primary">
          {showForm ? <ChevronUp size={15} /> : <Plus size={15} />}
          {showForm ? 'Cancel' : 'Add Subscriber'}
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-gray-800 mb-4">New Subscriber</h3>
          <form onSubmit={handleAdd} className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500 mb-1 block font-medium">Name *</label>
              <input className="form-input" required minLength={2} placeholder="Alice"
                value={form.name} onChange={e => setForm(f => ({...f, name: e.target.value}))} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block font-medium">Phone (E.164) *</label>
              <input className="form-input" required placeholder="+919876543210"
                value={form.phone} onChange={e => setForm(f => ({...f, phone: e.target.value}))} />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-gray-500 mb-1 block font-medium">Email *</label>
              <input className="form-input" required type="email" placeholder="alice@example.com"
                value={form.email} onChange={e => setForm(f => ({...f, email: e.target.value}))} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block font-medium">Escalation Order</label>
              <select className="form-input" value={form.escalation_order}
                onChange={e => setForm(f => ({...f, escalation_order: e.target.value}))}>
                <option value={1}>1 — Primary</option>
                <option value={2}>2 — Escalation 2</option>
                <option value={3}>3 — Final</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block font-medium">Mobile PIN (4-6 digits)</label>
              <input className="form-input" placeholder="Optional" maxLength={6} pattern="\d{4,6}"
                value={form.pin} onChange={e => setForm(f => ({...f, pin: e.target.value.replace(/\D/g,'')}))} />
            </div>
            {formErr && <p className="col-span-2 text-xs text-red-600">{formErr}</p>}
            <div className="col-span-2 flex justify-end gap-2 pt-1">
              <button type="button" onClick={() => setShowForm(false)} className="btn btn-ghost btn-sm">Cancel</button>
              <button type="submit" disabled={saving} className="btn btn-primary btn-sm">
                {saving ? 'Saving…' : 'Add Subscriber'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Subscriber cards */}
      {loading && subs.length === 0 ? (
        <div className="text-center py-12 text-gray-400">Loading…</div>
      ) : subs.length === 0 ? (
        <div className="card p-12 flex flex-col items-center gap-3 text-center text-gray-400">
          <Users size={36} className="text-gray-300" />
          <p className="font-medium text-gray-500">No subscribers configured</p>
          <p className="text-xs">Add a subscriber to receive breach alerts</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {subs.map(s => {
            const om = ORDER_META[s.escalation_order] || ORDER_META[1]
            return (
              <div key={s.id} className="card p-5 flex flex-col gap-4">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-bold text-gray-900 text-base">{s.name}</p>
                    <span
                      className="inline-block mt-1 text-xs font-semibold px-2 py-0.5 rounded-full"
                      style={{ background: om.bg, color: om.color }}
                    >
                      #{s.escalation_order} · {om.label}
                    </span>
                  </div>
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-white text-sm flex-shrink-0"
                    style={{ background: om.color }}
                  >
                    {s.name.charAt(0).toUpperCase()}
                  </div>
                </div>

                {/* Contact */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs text-gray-600">
                    <Phone size={12} className="text-gray-400" />
                    <span>{s.phone}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-600">
                    <Mail size={12} className="text-gray-400" />
                    <span className="truncate">{s.email}</span>
                  </div>
                </div>

                {/* PIN status */}
                <div className="flex items-center gap-2 py-2.5 px-3 rounded-lg bg-gray-50">
                  {s.has_pin ? (
                    <>
                      <Check size={14} className="text-emerald-500" />
                      <span className="text-xs text-emerald-700 font-medium">Mobile PIN set</span>
                    </>
                  ) : (
                    <>
                      <Key size={14} className="text-gray-400" />
                      <span className="text-xs text-gray-500">No PIN configured</span>
                    </>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => { setPinModal(s); setPinValue(''); setPinErr('') }}
                    className="btn btn-ghost btn-sm flex-1"
                  >
                    <Key size={13} /> {s.has_pin ? 'Change PIN' : 'Set PIN'}
                  </button>
                  <button
                    onClick={() => handleDelete(s.id, s.name)}
                    className="btn btn-danger btn-sm"
                    title="Delete subscriber"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* PIN Modal */}
      <Modal
        isOpen={!!pinModal}
        onClose={() => setPinModal(null)}
        title={`Set PIN — ${pinModal?.name}`}
        footer={
          <>
            <button onClick={() => setPinModal(null)} className="btn btn-ghost btn-sm">Cancel</button>
            <button onClick={handleSetPin} disabled={pinSaving} className="btn btn-primary btn-sm">
              {pinSaving ? 'Saving…' : 'Set PIN'}
            </button>
          </>
        }
      >
        <p className="text-sm text-gray-600 mb-3">
          Enter a 4-6 digit numeric PIN for <strong>{pinModal?.name}</strong>.
          Used for mobile app login.
        </p>
        <input
          className="form-input text-center text-xl tracking-widest"
          type="password"
          inputMode="numeric"
          placeholder="••••"
          maxLength={6}
          value={pinValue}
          onChange={e => setPinValue(e.target.value.replace(/\D/g, ''))}
          autoFocus
        />
        {pinErr && <p className="text-xs text-red-600 mt-2">{pinErr}</p>}
      </Modal>
    </div>
  )
}
