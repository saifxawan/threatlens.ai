import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Search, Filter, Bell, Eye, CheckCircle, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react'
import { alertsService } from '../services/services'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

const SEVERITIES = ['', 'critical', 'high', 'medium', 'low', 'informational']
const STATUSES = ['', 'new', 'investigating', 'resolved', 'false_positive']

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')
  const size = 50
  const navigate = useNavigate()

  const fetchAlerts = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, size }
      if (severity) params.severity = severity
      if (status) params.status = status
      if (search) params.source_ip = search
      const res = await alertsService.list(params)
      setAlerts(res.data.items || [])
      setTotal(res.data.total || 0)
      setPages(res.data.pages || 1)
    } catch {
      toast.error('Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }, [page, severity, status, search])

  useEffect(() => { fetchAlerts() }, [fetchAlerts])

  useEffect(() => {
    alertsService.stats().then(r => setStats(r.data)).catch(() => {})
  }, [])

  const updateStatus = async (alertId, newStatus, e) => {
    e.stopPropagation()
    try {
      await alertsService.updateStatus(alertId, newStatus)
      toast.success(`Alert marked as ${newStatus}`)
      fetchAlerts()
    } catch {
      toast.error('Failed to update status')
    }
  }

  const SEVERITY_COLORS = { critical: 'var(--critical)', high: 'var(--high)', medium: 'var(--medium)', low: 'var(--low)', informational: 'var(--text-muted)' }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Alert Management</h1>
          <p className="page-subtitle">Investigate, triage, and resolve security alerts ({total.toLocaleString()} total)</p>
        </div>
        <button className="btn btn-ghost" onClick={fetchAlerts}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-4 mb-4">
          {[
            { label: 'Total Alerts', value: stats.total, color: 'var(--cyan)' },
            { label: 'Critical', value: stats.by_severity?.critical || 0, color: 'var(--critical)' },
            { label: 'New / Open', value: stats.by_status?.new || 0, color: 'var(--blue)' },
            { label: 'Resolved', value: stats.by_status?.resolved || 0, color: 'var(--low)' },
          ].map((s, i) => (
            <div key={i} className="card" style={{ padding: '12px 16px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{s.label}</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: s.color, marginTop: 4 }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="card mb-4">
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="search-box" style={{ flex: 1, minWidth: 200 }}>
            <Search size={14} style={{ color: 'var(--text-muted)' }} />
            <input placeholder="Filter by IP..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <select className="form-input form-select" style={{ width: 140 }} value={severity} onChange={e => setSeverity(e.target.value)}>
            <option value="">All Severity</option>
            {SEVERITIES.filter(Boolean).map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
          </select>
          <select className="form-input form-select" style={{ width: 150 }} value={status} onChange={e => setStatus(e.target.value)}>
            <option value="">All Status</option>
            {STATUSES.filter(Boolean).map(s => <option key={s} value={s}>{s.replace('_', ' ').toUpperCase()}</option>)}
          </select>
        </div>
      </div>

      {/* Alerts table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[...Array(8)].map((_, i) => <div key={i} className="skeleton" style={{ height: 52 }} />)}
          </div>
        ) : alerts.length === 0 ? (
          <div className="empty-state">
            <div style={{ fontSize: '3rem' }}>🛡️</div>
            <div className="empty-state-title">No alerts found</div>
            <div className="empty-state-desc">Upload logs or start the live simulation to generate security alerts</div>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th style={{ width: 80 }}>Severity</th>
                    <th>Title</th>
                    <th style={{ width: 160 }}>Threat Type</th>
                    <th style={{ width: 130 }}>Source IP</th>
                    <th style={{ width: 100 }}>Status</th>
                    <th style={{ width: 150 }}>Created At</th>
                    <th style={{ width: 140 }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((alert) => (
                    <motion.tr
                      key={alert.id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/alerts/${alert.id}`)}
                      whileHover={{ backgroundColor: 'rgba(0,212,255,0.03)' }}
                    >
                      <td>
                        <span className={`badge ${alert.severity}`}>{alert.severity}</span>
                      </td>
                      <td>
                        <div style={{ fontWeight: 500, fontSize: '0.875rem', color: SEVERITY_COLORS[alert.severity] || 'var(--text-primary)' }}>
                          {alert.title}
                        </div>
                        {alert.description && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 300 }}>
                            {alert.description}
                          </div>
                        )}
                      </td>
                      <td><span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{alert.threat_type}</span></td>
                      <td>{alert.source_ip ? <span className="ip-badge">{alert.source_ip}</span> : '—'}</td>
                      <td><span className={`badge ${alert.status}`}>{alert.status?.replace('_', ' ')}</span></td>
                      <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono' }}>
                        {alert.created_at ? new Date(alert.created_at).toLocaleString() : '—'}
                      </td>
                      <td onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => navigate(`/alerts/${alert.id}`)}
                            title="View Details"
                          ><Eye size={12} /></button>
                          {alert.status === 'new' && (
                            <button className="btn btn-ghost btn-sm" style={{ color: 'var(--medium)' }}
                              onClick={(e) => updateStatus(alert.id, 'investigating', e)} title="Start investigating">
                              🔍
                            </button>
                          )}
                          {alert.status !== 'resolved' && (
                            <button className="btn btn-success btn-sm"
                              onClick={(e) => updateStatus(alert.id, 'resolved', e)} title="Mark resolved">
                              <CheckCircle size={12} />
                            </button>
                          )}
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="pagination">
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginRight: 'auto' }}>
                {total.toLocaleString()} total alerts
              </span>
              <button className="page-btn" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                <ChevronLeft size={14} />
              </button>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', padding: '0 8px' }}>
                {page} / {pages}
              </span>
              <button className="page-btn" onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page === pages}>
                <ChevronRight size={14} />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
