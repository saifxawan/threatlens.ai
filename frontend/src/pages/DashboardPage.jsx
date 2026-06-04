import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import {
  Shield, AlertTriangle, Activity, TrendingUp,
  Database, Cpu, Zap, Target, RefreshCw, Eye, Trash2, RotateCcw, Play
} from 'lucide-react'
import { dashboardService, alertsService, liveService } from '../services/services'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

const SEVERITY_COLORS = {
  critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e',
  informational: '#64748b', unknown: '#64748b'
}

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i) => ({ opacity: 1, y: 0, transition: { delay: i * 0.08, duration: 0.4 } })
}

function MetricCard({ label, value, icon: Icon, color, suffix = '', prefix = '', loading, onClick }) {
  const isClickable = !!onClick
  return (
    <div 
      className={`metric-card ${color}`} 
      onClick={onClick}
      style={{ 
        position: 'relative', 
        overflow: 'hidden',
        cursor: isClickable ? 'pointer' : 'default',
        transition: 'all 0.2s ease'
      }}
    >
      <div className="metric-label">{label}</div>
      <div 
        className="metric-value" 
        style={{ 
          color: `var(--${color === 'cyan' ? 'cyan' : color === 'red' ? 'critical' : color === 'orange' ? 'high' : color === 'yellow' ? 'medium' : color === 'green' ? 'low' : color === 'blue' ? 'blue' : 'purple'})`,
          display: 'flex',
          alignItems: 'center',
          gap: 6
        }}
      >
        {loading ? (
          <div className="skeleton" style={{ width: 80, height: 32, display: 'inline-block' }} />
        ) : value === undefined || value === null ? (
          <span style={{ fontSize: '0.85rem', opacity: 0.6, fontWeight: 500 }}>Not Trained</span>
        ) : (
          `${prefix}${value}${suffix}`
        )}
      </div>
      <div style={{ position: 'absolute', right: 16, top: 16, opacity: 0.15 }}>
        <Icon size={32} />
      </div>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 14px', fontSize: '0.8rem' }}>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 6 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: <strong>{p.value}</strong></p>
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [threatsOverTime, setThreatsOverTime] = useState([])
  const [severityDist, setSeverityDist] = useState([])
  const [topIPs, setTopIPs] = useState([])
  const [attackTypes, setAttackTypes] = useState([])
  const [recentAlerts, setRecentAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [isResetModalOpen, setIsResetModalOpen] = useState(false)
  const [isResetting, setIsResetting] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(() => {
    const saved = localStorage.getItem('tl_dashboard_auto_refresh')
    return saved === 'true'
  })
  const [refreshing, setRefreshing] = useState(false)
  const navigate = useNavigate()

  const handleReset = async (seed) => {
    setIsResetting(true)
    const toastId = toast.loading(seed ? 'Resetting database and seeding demo data...' : 'Clearing all database tables...')
    try {
      await dashboardService.reset(seed)
      toast.success(seed ? 'Database reset and seeded successfully!' : 'All security data cleared!', { id: toastId })
      setIsResetModalOpen(false)
      fetchAll(false)
    } catch (err) {
      toast.error('Failed to reset dashboard data', { id: toastId })
    } finally {
      setIsResetting(false)
    }
  }

  const handleResetAndStartSimulation = async () => {
    setIsResetting(true)
    const toastId = toast.loading('Wiping database and preparing clean simulation...')
    try {
      await dashboardService.reset(false)
      await liveService.start(1.5)
      toast.success('Database cleared! Launching clean live log feed...', { id: toastId })
      setIsResetModalOpen(false)
      navigate('/live-monitor')
    } catch (err) {
      toast.error('Failed to start clean simulation', { id: toastId })
    } finally {
      setIsResetting(false)
    }
  }

  const fetchAll = async (silent = false) => {
    if (!silent) {
      setLoading(true)
    } else {
      setRefreshing(true)
    }
    try {
      const [sumRes, totRes, sevRes, ipsRes, attRes, alertRes] = await Promise.all([
        dashboardService.summary(),
        dashboardService.threatsOverTime(),
        dashboardService.severityDistribution(),
        dashboardService.topIPs(),
        dashboardService.attackTypes(),
        alertsService.list({ page: 1, size: 8 }),
      ])
      setSummary(sumRes.data)
      setThreatsOverTime(totRes.data.data || [])
      setSeverityDist(sevRes.data.data || [])
      setTopIPs(ipsRes.data.data || [])
      setAttackTypes(attRes.data.data || [])
      setRecentAlerts(alertRes.data.items || [])
    } catch (err) {
      if (!silent) {
        toast.error('Failed to load dashboard data')
      }
    } finally {
      if (!silent) {
        setLoading(false)
      } else {
        setRefreshing(false)
      }
    }
  }

  useEffect(() => {
    fetchAll(false)
  }, [])

  useEffect(() => {
    localStorage.setItem('tl_dashboard_auto_refresh', autoRefresh)
    let intervalId = null
    if (autoRefresh) {
      intervalId = setInterval(() => {
        fetchAll(true)
      }, 5000)
    }
    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [autoRefresh])

  const metrics = [
    { label: 'Logs Processed', value: summary?.total_logs?.toLocaleString(), icon: Database, color: 'cyan', onClick: () => navigate('/logs') },
    { label: 'Threats Detected', value: summary?.threats_detected?.toLocaleString(), icon: AlertTriangle, color: 'red', onClick: () => navigate('/alerts') },
    { label: 'Critical Alerts', value: summary?.critical_alerts?.toLocaleString(), icon: Zap, color: 'orange', onClick: () => navigate('/alerts') },
    { label: 'Anomaly Rate', value: summary?.anomaly_rate, suffix: '%', icon: TrendingUp, color: 'yellow' },
    { label: 'Active Sources', value: summary?.active_sources, icon: Activity, color: 'green', onClick: () => navigate('/logs') },
    { label: 'Model Accuracy', value: summary?.model_accuracy ? summary.model_accuracy : null, suffix: '%', icon: Cpu, color: 'blue', onClick: () => navigate('/ml-analytics') },
    { label: 'Avg Risk Score', value: summary?.avg_risk_score, suffix: '/100', icon: Target, color: 'purple' },
    { label: 'New Alerts', value: summary?.new_alerts, icon: Shield, color: 'red', onClick: () => navigate('/alerts') },
  ]

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span style={{ color: 'var(--cyan)' }}>SOC</span> Overview Dashboard
          </h1>
          <p className="page-subtitle">Real-time security monitoring and threat intelligence</p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button
            className={`btn ${autoRefresh ? 'btn-success' : 'btn-ghost'}`}
            onClick={() => {
              setAutoRefresh(prev => {
                const next = !prev
                toast.success(next ? 'Auto-refresh enabled (5s intervals)' : 'Auto-refresh disabled')
                return next
              })
            }}
            disabled={loading}
            style={{
              gap: 8,
              transition: 'all 0.2s ease',
              background: autoRefresh ? 'rgba(34, 197, 94, 0.15)' : undefined,
              borderColor: autoRefresh ? 'rgba(34, 197, 94, 0.3)' : undefined,
              color: autoRefresh ? 'var(--low)' : undefined
            }}
          >
            <Activity size={14} className={autoRefresh || refreshing ? 'pulse' : ''} />
            Auto: {autoRefresh ? 'ON' : 'OFF'}
          </button>
          <button className="btn btn-ghost" onClick={() => fetchAll(false)} disabled={loading || refreshing}>
            <RefreshCw size={14} className={loading || refreshing ? 'spin' : ''} />
            Refresh
          </button>
          <button className="btn btn-danger" onClick={() => setIsResetModalOpen(true)} disabled={loading || refreshing}>
            <Trash2 size={14} />
            Reset Data
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <motion.div
        className="grid grid-4 mb-6"
        initial="hidden"
        animate="visible"
      >
        {metrics.map((m, i) => (
          <motion.div key={m.label} custom={i} variants={cardVariants}>
            <MetricCard {...m} loading={loading} />
          </motion.div>
        ))}
      </motion.div>

      {/* Charts Row 1 */}
      <div className="grid grid-2 mb-4">
        {/* Threats Over Time */}
        <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
          <div className="section-header">
            <span className="section-title">
              <TrendingUp size={14} style={{ color: 'var(--cyan)' }} />
              Threats Over Time (7 Days)
            </span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={threatsOverTime}>
              <defs>
                <linearGradient id="gradientTotal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--cyan)" stopOpacity={0.25}/>
                  <stop offset="95%" stopColor="var(--cyan)" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="gradientCritical" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--critical)" stopOpacity={0.25}/>
                  <stop offset="95%" stopColor="var(--critical)" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="gradientHigh" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--high)" stopOpacity={0.25}/>
                  <stop offset="95%" stopColor="var(--high)" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.06)" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }} tickFormatter={v => v.slice(5)} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconSize={8} wrapperStyle={{ fontSize: '0.75rem' }} />
              <Area type="monotone" dataKey="total" stroke="#00d4ff" strokeWidth={2.5} fill="url(#gradientTotal)" name="Total Alerts" />
              <Area type="monotone" dataKey="critical" stroke="#ef4444" strokeWidth={2} fill="url(#gradientCritical)" name="Critical Threats" />
              <Area type="monotone" dataKey="high" stroke="#f97316" strokeWidth={2} fill="url(#gradientHigh)" name="High Threats" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Severity Distribution */}
        <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }}>
          <div className="section-header">
            <span className="section-title">
              <Shield size={14} style={{ color: 'var(--cyan)' }} />
              Alert Severity Distribution
            </span>
          </div>
          <div style={{ position: 'relative', width: '100%', height: 220 }}>
            <div style={{
              position: 'absolute',
              top: '43%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              pointerEvents: 'none',
            }}>
              <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>Active Alerts</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#fff', marginTop: 2, fontFamily: 'JetBrains Mono, monospace' }}>
                {severityDist.reduce((acc, curr) => acc + (curr.value || 0), 0).toLocaleString()}
              </div>
            </div>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityDist}
                  cx="50%" cy="45%"
                  innerRadius={55} outerRadius={75}
                  paddingAngle={6}
                  dataKey="value"
                  nameKey="name"
                >
                  {severityDist.map((entry, index) => (
                    <Cell key={index} fill={SEVERITY_COLORS[entry.name] || '#64748b'} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend iconSize={8} wrapperStyle={{ fontSize: '0.75rem', marginTop: -10 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-2 mb-4">
        {/* Top Suspicious IPs */}
        <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
          <div className="section-header">
            <span className="section-title">
              <Target size={14} style={{ color: 'var(--critical)' }} />
              Top Suspicious IPs
            </span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={topIPs} layout="vertical">
              <defs>
                <linearGradient id="gradientIps" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="rgba(239, 68, 68, 0.2)"/>
                  <stop offset="100%" stopColor="var(--critical)"/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.06)" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} />
              <YAxis type="category" dataKey="ip" tick={{ fontSize: 10, fill: '#00d4ff', fontFamily: 'JetBrains Mono' }} width={115} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="alerts" fill="url(#gradientIps)" radius={[0, 4, 4, 0]} name="Alerts" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Attack Categories */}
        <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.45 }}>
          <div className="section-header">
            <span className="section-title">
              <AlertTriangle size={14} style={{ color: 'var(--high)' }} />
              Attack Categories
            </span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={attackTypes}>
              <defs>
                <linearGradient id="gradientAttack" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--high)"/>
                  <stop offset="100%" stopColor="rgba(249, 115, 22, 0.2)"/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.06)" />
              <XAxis dataKey="type" tick={{ fontSize: 9, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" fill="url(#gradientAttack)" radius={[4, 4, 0, 0]} name="Count" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Recent Alerts Table */}
      <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
        <div className="section-header">
          <span className="section-title">
            <AlertTriangle size={14} style={{ color: 'var(--critical)' }} />
            Recent Security Alerts
          </span>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/alerts')}>
            <Eye size={12} /> View All
          </button>
        </div>

        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[...Array(5)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 40 }} />
            ))}
          </div>
        ) : recentAlerts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🛡️</div>
            <div className="empty-state-title">No alerts yet</div>
            <div className="empty-state-desc">Upload logs or start the live simulation to generate alerts</div>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Title</th>
                  <th>Threat Type</th>
                  <th>Source IP</th>
                  <th>Status</th>
                  <th>Time</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {recentAlerts.map((alert) => (
                  <tr key={alert.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/alerts/${alert.id}`)}>
                    <td>
                      <span className={`badge ${alert.severity}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td style={{ maxWidth: 280 }}>
                      <span className="truncate" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500 }}>
                        {alert.title}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{alert.threat_type}</span>
                    </td>
                    <td>
                      {alert.source_ip && <span className="ip-badge">{alert.source_ip}</span>}
                    </td>
                    <td>
                      <span className={`badge ${alert.status}`}>{alert.status}</span>
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono' }}>
                      {alert.created_at ? new Date(alert.created_at).toLocaleString() : '—'}
                    </td>
                    <td>
                      <Eye size={14} style={{ color: 'var(--text-muted)' }} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* Reset Modal */}
      {isResetModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(2, 8, 23, 0.85)',
          backdropFilter: 'blur(16px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="card"
            style={{
              maxWidth: 550,
              width: '90%',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              boxShadow: 'var(--shadow-critical)',
              padding: 30,
              position: 'relative'
            }}
          >
            <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
              <div style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid var(--critical)',
                borderRadius: '50%',
                padding: 12,
                color: 'var(--critical)'
              }}>
                <AlertTriangle size={28} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: 8, color: '#fff' }}>
                  Dangerous Action: Reset Database
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', lineHeight: 1.5, marginBottom: 20 }}>
                  This will completely delete all records in the database, including all processed logs, security predictions, MITRE alerts, and model training metrics. Authentication accounts will remain intact.
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 10 }}>
              {/* Option 1: Seed Demo Data */}
              <button
                className="btn"
                style={{
                  background: 'rgba(0, 212, 255, 0.1)',
                  borderColor: 'rgba(0, 212, 255, 0.3)',
                  color: 'var(--cyan)',
                  justifyContent: 'flex-start',
                  padding: '14px 20px',
                  textAlign: 'left',
                  width: '100%',
                }}
                onClick={() => handleReset(true)}
                disabled={isResetting}
              >
                <RotateCcw size={16} style={{ marginRight: 12, flexShrink: 0 }} />
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>Reset & Seed Historical Demo Data</div>
                  <div style={{ fontSize: '0.75rem', opacity: 0.7, fontWeight: 400, marginTop: 2, whiteSpace: 'normal' }}>
                    Populates dashboard with 1,000 mock events and training metrics (Default SOC state).
                  </div>
                </div>
              </button>

              {/* Option 2: Start Clean Live Simulation (Start from Zero) */}
              <button
                className="btn"
                style={{
                  background: 'rgba(34, 197, 94, 0.1)',
                  borderColor: 'rgba(34, 197, 94, 0.3)',
                  color: 'var(--low)',
                  justifyContent: 'flex-start',
                  padding: '14px 20px',
                  textAlign: 'left',
                  width: '100%',
                }}
                onClick={handleResetAndStartSimulation}
                disabled={isResetting}
              >
                <Play size={16} style={{ marginRight: 12, flexShrink: 0 }} />
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>Reset & Start Live Feed from Zero (Clean Slate)</div>
                  <div style={{ fontSize: '0.75rem', opacity: 0.7, fontWeight: 400, marginTop: 2, whiteSpace: 'normal' }}>
                    Wipes database completely, starts real-time log simulation, and redirects to monitor feed.
                  </div>
                </div>
              </button>

              {/* Option 3: Clear Database completely */}
              <button
                className="btn"
                style={{
                  background: 'rgba(239, 68, 68, 0.08)',
                  borderColor: 'rgba(239, 68, 68, 0.25)',
                  color: 'var(--critical)',
                  justifyContent: 'flex-start',
                  padding: '14px 20px',
                  textAlign: 'left',
                  width: '100%',
                }}
                onClick={() => handleReset(false)}
                disabled={isResetting}
              >
                <Trash2 size={16} style={{ marginRight: 12, flexShrink: 0 }} />
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>Wipe Database Completely (Blank slate)</div>
                  <div style={{ fontSize: '0.75rem', opacity: 0.7, fontWeight: 400, marginTop: 2, whiteSpace: 'normal' }}>
                    Clears all data. Leaves dashboard perfectly empty (0 records).
                  </div>
                </div>
              </button>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 24 }}>
              <button className="btn btn-ghost" onClick={() => setIsResetModalOpen(false)} disabled={isResetting}>
                Cancel
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
