/**
 * src/utils/time.js — IST time utilities
 * IST = UTC + 5:30
 */

const IST_OFFSET_MS = 5.5 * 60 * 60 * 1000

function toIST(isoString) {
  const d = new Date(isoString)
  return new Date(d.getTime() + IST_OFFSET_MS)
}

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun',
                'Jul','Aug','Sep','Oct','Nov','Dec']

function pad(n) { return String(n).padStart(2, '0') }

/**
 * "03 Jun 2026, 10:45:32 AM"
 */
export function utcToIST(isoString) {
  if (!isoString) return '—'
  try {
    const d = toIST(isoString)
    const day   = pad(d.getUTCDate())
    const mon   = MONTHS[d.getUTCMonth()]
    const year  = d.getUTCFullYear()
    let h       = d.getUTCHours()
    const m     = pad(d.getUTCMinutes())
    const s     = pad(d.getUTCSeconds())
    const ampm  = h >= 12 ? 'PM' : 'AM'
    h = h % 12 || 12
    return `${day} ${mon} ${year}, ${pad(h)}:${m}:${s} ${ampm}`
  } catch {
    return isoString
  }
}

/**
 * "10:45:32 AM"
 */
export function formatTime(isoString) {
  if (!isoString) return '—'
  try {
    const d = toIST(isoString)
    let h   = d.getUTCHours()
    const m = pad(d.getUTCMinutes())
    const s = pad(d.getUTCSeconds())
    const ampm = h >= 12 ? 'PM' : 'AM'
    h = h % 12 || 12
    return `${pad(h)}:${m}:${s} ${ampm}`
  } catch {
    return isoString
  }
}

/**
 * "03 Jun 2026"
 */
export function formatDate(isoString) {
  if (!isoString) return '—'
  try {
    const d   = toIST(isoString)
    const day = pad(d.getUTCDate())
    const mon = MONTHS[d.getUTCMonth()]
    const yr  = d.getUTCFullYear()
    return `${day} ${mon} ${yr}`
  } catch {
    return isoString
  }
}

/**
 * "2 minutes ago" / "just now" / "1 hour ago"
 */
export function timeAgo(isoString) {
  if (!isoString) return '—'
  try {
    const then = new Date(isoString).getTime()
    const now  = Date.now()
    const sec  = Math.floor((now - then) / 1000)
    if (sec < 10)  return 'just now'
    if (sec < 60)  return `${sec}s ago`
    if (sec < 3600) {
      const m = Math.floor(sec / 60)
      return `${m} min${m !== 1 ? 's' : ''} ago`
    }
    const h = Math.floor(sec / 3600)
    return `${h} hour${h !== 1 ? 's' : ''} ago`
  } catch {
    return '—'
  }
}

/** Current IST time as "HH:MM:SS AM/PM" */
export function nowIST() {
  return formatTime(new Date().toISOString())
}
