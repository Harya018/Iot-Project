/**
 * src/hooks/useLogStream.js
 *
 * Connects to the /ws/logs endpoint on the CURRENT page host.
 * Uses wss: when page is https:, ws: when page is http:.
 * Works on any port or IP — no hardcoded localhost.
 *
 * Streams live backend log lines to the admin dashboard.
 * Supports pause/resume and keyword + level filtering.
 */
import { useState, useEffect, useRef, useCallback } from 'react'

const MAX_LINES = 1000

/** Derive the correct WebSocket URL from the current page location. */
function getLogWsUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host     = window.location.host   // includes port if non-standard
  return `${protocol}//${host}/ws/logs`
}

export default function useLogStream() {
  const [lines,       setLines]       = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [isPaused,    setIsPaused]    = useState(false)
  const [filter,      setFilter]      = useState('')
  const [levelFilter, setLevelFilter] = useState('all')

  const wsRef      = useRef(null)
  const mountedRef = useRef(true)
  const pausedRef  = useRef(false)
  const retryTimer = useRef(null)

  const connect = useCallback(() => {
    if (!mountedRef.current) return
    try {
      const ws = new WebSocket(getLogWsUrl())
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) return
        setIsConnected(true)
      }

      ws.onmessage = (e) => {
        if (!mountedRef.current || pausedRef.current) return
        const line = e.data
        if (!line?.trim()) return
        setLines(prev => {
          const next = [...prev, line]
          return next.length > MAX_LINES ? next.slice(-MAX_LINES) : next
        })
      }

      ws.onclose = () => {
        if (!mountedRef.current) return
        setIsConnected(false)
        retryTimer.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()
    } catch { /* silent */ }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    connect()
    return () => {
      mountedRef.current = false
      clearTimeout(retryTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  const togglePause = useCallback(() => {
    setIsPaused(prev => {
      pausedRef.current = !prev
      return !prev
    })
  }, [])

  const clearLines = useCallback(() => setLines([]), [])

  // Apply filters for display
  const filteredLines = lines.filter(line => {
    if (filter && !line.toLowerCase().includes(filter.toLowerCase())) return false
    if (levelFilter !== 'all') {
      const up = levelFilter.toUpperCase()
      if (!line.includes(`[${up}]`) && !line.includes(up)) return false
    }
    return true
  })

  return {
    lines: filteredLines,
    rawLines: lines,
    isConnected,
    isPaused,
    filter,
    levelFilter,
    setFilter,
    setLevelFilter,
    togglePause,
    clearLines,
  }
}
