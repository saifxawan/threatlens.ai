import { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import { Toaster } from 'react-hot-toast'
import { alertsService } from '../services/services'
import { LiveMonitorProvider, useWebSocket } from '../hooks/useWebSocket'

function MainLayoutContent() {
  const [alertCount, setAlertCount] = useState(0)
  const { connected } = useWebSocket()

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await alertsService.stats()
        setAlertCount(res.data?.by_status?.new || 0)
      } catch (_) {}
    }
    fetchAlerts()
    const interval = setInterval(fetchAlerts, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app-container">
      <Sidebar alertCount={alertCount} />
      <TopBar alertCount={alertCount} isConnected={connected} />
      <main className="main-content">
        <div className="page-container fade-in">
          <Outlet context={{ setAlertCount }} />
        </div>
      </main>
      <Toaster
        position="bottom-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'var(--bg-tertiary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-card)',
            borderRadius: '10px',
            fontSize: '0.875rem',
          },
        }}
      />
    </div>
  )
}

export default function MainLayout() {
  return (
    <LiveMonitorProvider>
      <MainLayoutContent />
    </LiveMonitorProvider>
  )
}
