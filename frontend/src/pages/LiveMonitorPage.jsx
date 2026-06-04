import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Radio, Play, Square, Trash2, AlertTriangle, Activity, Wifi, WifiOff, Bell } from 'lucide-react'
import { liveService, dashboardService } from '../services/services'
import { useWebSocket } from '../hooks/useWebSocket'
import toast from 'react-hot-toast'

const SEVERITY_COLORS = {
  critical: '#ef4444', high: '#f97316', medium: '#eab308',
  warning: '#eab308', info: '#64748b', low: '#22c55e',
}

function LogRow({ log, animate }) {
  const isAnomaly = log.prediction === 'anomaly'
  return (
    <motion.div
      initial={animate ? { opacity: 0, x: -10 } : false}
      animate={{ opacity: 1, x: 0 }}
      style={{
        display: 'grid',
        gridTemplateColumns: '130px 70px 120px 120px 1fr 80px 70px',
        gap: 8,
        padding: '7px 12px',
        fontSize: '0.75rem',
        fontFamily: 'JetBrains Mono, monospace',
        borderBottom: '1px solid rgba(148,163,184,0.04)',
        background: isAnomaly ? 'rgba(239,68,68,0.04)' : 'transparent',
        alignItems: 'center',
      }}
    >
      <span style={{ color: 'var(--text-muted)' }}>
        {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '—'}
      </span>
      <span style={{ padding: '1px 6px', background: 'var(--bg-tertiary)', borderRadius: 4, fontSize: '0.65rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
        {log.source}
      </span>
      <span style={{ color: 'var(--cyan)' }}>{log.source_ip || '—'}</span>
      <span style={{ color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {log.username || '—'}
      </span>
      <span style={{ color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontFamily: 'Inter, sans-serif', fontSize: '0.8rem' }}>
        {log.message}
      </span>
      <span style={{ color: SEVERITY_COLORS[log.severity] || 'var(--text-muted)', fontWeight: 700, fontSize: '0.65rem' }}>
        {(log.severity || '').toUpperCase()}
      </span>
      {isAnomaly ? (
        <span style={{ color: 'var(--critical)', fontSize: '0.65rem', fontWeight: 700 }}>⚠ THREAT</span>
      ) : (
        <span style={{ color: 'var(--low)', fontSize: '0.65rem' }}>NORMAL</span>
      )}
    </motion.div>
  )
}

function AlertNotification({ alert, onDismiss }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      style={{
        background: 'rgba(9,15,32,0.95)',
        border: `1px solid ${SEVERITY_COLORS[alert.severity] || 'var(--border)'}`,
        borderRadius: 10,
        padding: 14,
        display: 'flex',
        gap: 10,
        boxShadow: `0 4px 20px ${SEVERITY_COLORS[alert.severity] || 'transparent'}22`,
      }}
    >
      <AlertTriangle size={16} style={{ color: SEVERITY_COLORS[alert.severity], flexShrink: 0, marginTop: 2 }} />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>{alert.title}</div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 2 }}>{alert.source_ip}</div>
      </div>
      <button onClick={onDismiss} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.8rem' }}>✕</button>
    </motion.div>
  )
}

export default function LiveMonitorPage() {
  const [interval, setInterval_] = useState(1.5)
  const logContainerRef = useRef(null)

  const {
    logs,
    alerts,
    totalLogs,
    totalThreats,
    totalCritical,
    connected,
    simRunning,
    startSimulation,
    stopSimulation,
    clearLogs
  } = useWebSocket()

  const [visibleAlerts, setVisibleAlerts] = useState(() => alerts.slice(0, 5))

  // Auto-scroll logs to top (newest first)
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = 0
    }
  }, [logs.length])

  // Sync visible alerts when alerts array changes
  useEffect(() => {
    if (alerts.length > 0) {
      setVisibleAlerts(prev => {
        const newItems = alerts.filter(a => !prev.some(p => p._id === a._id))
        if (newItems.length === 0) return prev
        return [...newItems, ...prev].slice(0, 5)
      })
    } else {
      setVisibleAlerts([])
    }
  }, [alerts])

  const handleResetAndStartFromZero = async () => {
    const confirmReset = window.confirm('Are you sure you want to delete all log data and start analyzing fresh from zero?')
    if (!confirmReset) return

    const toastId = toast.loading('Wiping database and launching fresh simulation feed...')
    try {
      await dashboardService.reset(false)
      clearLogs()
      setVisibleAlerts([])
      await startSimulation(interval)
      toast.success('Database cleared! Log stream started from zero.', { id: toastId })
    } catch {
      toast.error('Failed to reset and start simulation from zero.', { id: toastId })
    }
  }

  const anomalyCount = logs.filter(l => l.prediction === 'anomaly').length
  const criticalCount = alerts.filter(a => a.severity === 'critical').length

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Radio size={24} style={{ color: simRunning ? 'var(--low)' : 'var(--text-muted)' }} />
            Live Log Monitor
          </h1>
          <p className="page-subtitle">Real-time log streaming with instant ML threat detection</p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <select className="form-input form-select" style={{ width: 150 }} value={interval} onChange={e => setInterval_(parseFloat(e.target.value))} disabled={simRunning}>
            <option value={0.5}>Fast (0.5s)</option>
            <option value={1.0}>Normal (1s)</option>
            <option value={1.5}>Default (1.5s)</option>
            <option value={3.0}>Slow (3s)</option>
          </select>
          {simRunning ? (
            <button className="btn btn-danger" onClick={stopSimulation}>
              <Square size={14} /> Stop Simulation
            </button>
          ) : (
            <>
              <button className="btn btn-primary" onClick={startSimulation}>
                <Play size={14} /> Start Simulation
              </button>
              <button className="btn btn-danger" onClick={handleResetAndStartFromZero}>
                <Play size={14} /> Reset & Start from Zero
              </button>
            </>
          )}
          <button className="btn btn-ghost btn-sm" onClick={clearLogs} title="Clear log feed">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-4 mb-4">
        {[
          { label: 'Connection', value: connected ? 'LIVE' : 'DISCONNECTED', color: connected ? 'var(--low)' : 'var(--text-muted)', icon: connected ? Wifi : WifiOff },
          { label: 'Logs Captured', value: totalLogs, color: 'var(--cyan)', icon: Activity },
          { label: 'Threats Detected', value: totalThreats, color: 'var(--high)', icon: AlertTriangle },
          { label: 'Critical Alerts', value: totalCritical, color: 'var(--critical)', icon: Bell },
        ].map(({ label, value, color, icon: Icon }) => (
          <div key={label} className="card" style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
            <Icon size={20} style={{ color }} />
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color }}>{value}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 16, alignItems: 'start' }}>
        {/* Log feed */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {/* Table header */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '130px 70px 120px 120px 1fr 80px 70px',
            gap: 8,
            padding: '10px 12px',
            background: 'var(--bg-tertiary)',
            fontSize: '0.65rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--text-muted)',
            borderBottom: '1px solid var(--border-card)',
          }}>
            <span>Time</span>
            <span>Source</span>
            <span>Source IP</span>
            <span>User</span>
            <span>Message</span>
            <span>Severity</span>
            <span>Status</span>
          </div>

          <div ref={logContainerRef} style={{ maxHeight: '70vh', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
            {logs.length === 0 ? (
              <div className="empty-state" style={{ padding: 60 }}>
                <motion.div
                  animate={simRunning ? { opacity: [0.3, 1, 0.3] } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  <Radio size={40} style={{ color: 'var(--text-muted)' }} />
                </motion.div>
                <div className="empty-state-title">{simRunning ? 'Waiting for logs...' : 'Click "Start Simulation" to begin'}</div>
              </div>
            ) : (
              <AnimatePresence initial={false}>
                {logs.map((log, idx) => (
                  <LogRow key={`${log.timestamp}-${log.source_ip}-${log.message}`} log={log} animate={idx === 0} />
                ))}
              </AnimatePresence>
            )}
          </div>
        </div>

        {/* Alert panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="card">
            <div className="section-title mb-4">
              <Bell size={14} style={{ color: 'var(--critical)' }} />
              Live Alerts ({alerts.length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <AnimatePresence>
                {visibleAlerts.map(alert => (
                  <AlertNotification
                    key={alert._id}
                    alert={alert}
                    onDismiss={() => setVisibleAlerts(prev => prev.filter(a => a._id !== alert._id))}
                  />
                ))}
              </AnimatePresence>
              {visibleAlerts.length === 0 && (
                <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  {simRunning ? '✅ No threats detected yet' : 'Start simulation to monitor alerts'}
                </div>
              )}
            </div>
          </div>

          {/* Attack legend */}
          <div className="card">
            <div className="section-title mb-4">Attack Scenarios</div>
            {[
              { name: 'Brute Force', color: 'var(--critical)', icon: '🔓' },
              { name: 'Port Scan', color: 'var(--high)', icon: '🔍' },
              { name: 'Web Attack', color: 'var(--high)', icon: '🌐' },
              { name: 'Priv. Escalation', color: 'var(--critical)', icon: '⬆️' },
              { name: 'Malware Behavior', color: 'var(--critical)', icon: '🦠' },
              { name: 'Unauth Access', color: 'var(--high)', icon: '🚫' },
            ].map(({ name, color, icon }) => (
              <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0', borderBottom: '1px solid var(--border-card)' }}>
                <span style={{ fontSize: '0.9rem' }}>{icon}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', flex: 1 }}>{name}</span>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }}></span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
