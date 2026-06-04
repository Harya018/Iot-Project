/**
 * src/components/dashboard/SubscriberManager.jsx
 * Compact subscriber table for the dashboard overview.
 * Full management is in SubscribersPage.
 */
import { useState, useEffect, useCallback } from 'react'
import { Key, Check, Users } from 'lucide-react'
import { fetchSubscribers } from '../../services/api.js'
import Card from '../shared/Card.jsx'

export default function SubscriberManager() {
  const [subs,    setSubs]    = useState([])
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try { setSubs(await fetchSubscribers()) }
    catch { /* silent */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const ORDER_LABELS = { 1:'Primary', 2:'Escalation 2', 3:'Final' }

  return (
    <Card
      title="Subscribers"
      subtitle={`${subs.length} configured`}
      noPadding
    >
      {subs.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-gray-400">
          <Users size={28} className="text-gray-300" />
          <p className="text-sm">No subscribers configured</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead><tr>
              <th>Name</th>
              <th className="hidden sm:table-cell">Phone</th>
              <th>Order</th>
              <th>PIN</th>
            </tr></thead>
            <tbody>
              {subs.map(s => (
                <tr key={s.id}>
                  <td className="font-medium">{s.name}</td>
                  <td className="hidden sm:table-cell text-gray-500">{s.phone}</td>
                  <td>
                    <span className="text-xs font-medium text-gray-600">
                      {ORDER_LABELS[s.escalation_order] || `#${s.escalation_order}`}
                    </span>
                  </td>
                  <td>
                    {s.has_pin
                      ? <Check size={14} className="text-emerald-500" />
                      : <Key size={13} className="text-gray-300" />
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}
