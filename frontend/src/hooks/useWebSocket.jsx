import { useState, useEffect, useRef, useCallback, createContext, useContext } from 'react'
import { liveService } from '../services/services'
import toast from 'react-hot-toast'
import { useLocation } from 'react-router-dom'

const LiveMonitorContext = createContext(null)

export function LiveMonitorProvider({ children }) {
  const [logs, setLogs] = useState([])
  const [alerts, setAlerts] = useState([])
  const [totalLogs, setTotalLogs] = useState(0)
  const [totalThreats, setTotalThreats] = useState(0)
  const [totalCritical, setTotalCritical] = useState(0)
  const [connected, setConnected] = useState(false)
  const [simRunning, setSimRunning] = useState(false)
  const wsRef = useRef(null)

  const location = useLocation()
  const pathRef = useRef(location.pathname)

  useEffect(() => {
    pathRef.current = location.pathname
  }, [location.pathname])

  const getLimit = () => {
    try {
      const s = JSON.parse(localStorage.getItem('tl_settings') || '{}')
      return s.maxLiveLogs || 200
    } catch {
      return 200
    }
  }

  const connect = useCallback(() => {
    // Prevent double connections if already active
    if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
      return
    }

    const token = localStorage.getItem('tl_token')
    let wsUrl;
    const envApiUrl = import.meta.env.VITE_API_URL;
    if (envApiUrl) {
      const protocol = envApiUrl.startsWith('https') ? 'wss' : 'ws';
      const hostPath = envApiUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
      wsUrl = `${protocol}://${hostPath}/live/ws/logs`;
    } else {
      wsUrl = 'ws://localhost:8000/api/live/ws/logs';
    }
    if (token) {
      wsUrl += `${wsUrl.includes('?') ? '&' : '?'}token=${token}`
    }

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)
      ws.onclose = () => setConnected(false)
      ws.onerror = () => setConnected(false)

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'log') {
            const limit = getLimit()
            setLogs((prev) => [msg.data, ...prev].slice(0, limit))
            setTotalLogs((c) => c + 1)
            if (msg.data.prediction === 'anomaly') {
              setTotalThreats((t) => t + 1)
            }
          } else if (msg.type === 'alert') {
            // Generate unique local ID if missing
            const newAlert = { ...msg.data, receivedAt: Date.now(), _id: Math.random() }
            setAlerts((prev) => [newAlert, ...prev].slice(0, 100))

            // Only show toast alerts if we are on the /live-monitor page
            const currentPath = pathRef.current
            const shouldShowToast = currentPath === '/live-monitor'

            if (shouldShowToast) {
              if (msg.data.severity === 'critical') {
                setTotalCritical((c) => c + 1)
                toast.error(`🚨 CRITICAL: ${msg.data.title}`, { duration: 6000 })
              } else if (msg.data.severity === 'high') {
                toast(`⚠️ HIGH: ${msg.data.title}`, { duration: 4000 })
              }
            } else {
              // Still update the critical count in global state even if toast is silenced
              if (msg.data.severity === 'critical') {
                setTotalCritical((c) => c + 1)
              }
            }
          }
        } catch (_) {}
      }
    } catch (_) {}
  }, [])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
  }, [])

  const clearData = useCallback(() => {
    setLogs([])
    setAlerts([])
    setTotalLogs(0)
    setTotalThreats(0)
    setTotalCritical(0)
  }, [])

  // Global Start/Stop wrapper methods
  const startSimulation = useCallback(async (interval) => {
    try {
      await liveService.start(interval)
      setSimRunning(true)
      connect()
      toast.success('Live simulation started!')
    } catch {
      toast.error('Failed to start simulation')
    }
  }, [connect])

  const stopSimulation = useCallback(async () => {
    try {
      await liveService.stop()
      setSimRunning(false)
      disconnect()
      toast('Simulation stopped', { icon: '⏹️' })
    } catch {
      toast.error('Failed to stop simulation')
    }
  }, [disconnect])

  // Initial status sync on mount/login
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await liveService.status()
        if (res.data?.running) {
          setSimRunning(true)
          connect()
        }
      } catch (_) {}
    }

    if (localStorage.getItem('tl_token')) {
      checkStatus()
    }
  }, [connect])

  // Always clean up raw socket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const value = {
    logs,
    alerts,
    totalLogs,
    totalThreats,
    totalCritical,
    connected,
    connect,
    disconnect,
    clearLogs: clearData,
    simRunning,
    setSimRunning,
    startSimulation,
    stopSimulation
  }

  return (
    <LiveMonitorContext.Provider value={value}>
      {children}
    </LiveMonitorContext.Provider>
  )
}

export function useWebSocket() {
  const context = useContext(LiveMonitorContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a LiveMonitorProvider')
  }
  return context
}
