import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Search, Filter, RefreshCw, Trash2, ChevronLeft, ChevronRight, Eye } from 'lucide-react'
import { logsService } from '../services/services'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

const SEVERITY_OPTIONS = ['', 'critical', 'high', 'warning', 'info']
const SOURCE_OPTIONS = ['', 'syslog', 'apache', 'hdfs', 'csv', 'live']

export default function LogsPage() {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [severity, setSeverity] = useState('')
  const [source, setSource] = useState('')
  const [stats, setStats] = useState(null)
  const size = 50

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, size }
      if (search) params.search = search
      if (severity) params.severity = severity
      if (source) params.source = source
      const res = await logsService.list(params)
      setLogs(res.data.items || [])
      setTotal(res.data.total || 0)
      setPages(res.data.pages || 1)
    } catch {
      toast.error('Failed to load logs')
    } finally {
      setLoading(false)
    }
  }, [page, search, severity, source])

  useEffect(() => { fetchLogs() }, [fetchLogs])

  // Debounced search
  useEffect(() => {
    const t = setTimeout(() => setPage(1), 400)
    return () => clearTimeout(t)
  }, [search, severity, source])

  useEffect(() => {
    logsService.stats().then(r => setStats(r.data)).catch(() => {})
  }, [])

  const getSeverityColor = (sev) => {
    const map = { critical: 'var(--critical)', high: 'var(--high)', warning: 'var(--medium)', error: 'var(--high)', info: 'var(--text-muted)' }
    return map[sev] || 'var(--text-muted)'
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Log Explorer</h1>
          <p className="page-subtitle">Browse, search, and filter all ingested log entries ({total.toLocaleString()} total)</p>
        </div>
        <button className="btn btn-ghost" onClick={fetchLogs}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Stats row */}
      {stats && (
        <div className="grid grid-4 mb-4">
          {[
            { label: 'Total Logs', value: stats.total?.toLocaleString() },
            { label: 'Critical', value: stats.by_severity?.critical || 0, color: 'var(--critical)' },
            { label: 'High', value: stats.by_severity?.high || 0, color: 'var(--high)' },
            { label: 'Info', value: stats.by_severity?.info || 0, color: 'var(--text-secondary)' },
          ].map((s, i) => (
            <div key={i} className="card" style={{ padding: '12px 16px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{s.label}</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: s.color || 'var(--cyan)', marginTop: 4 }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <motion.div className="card mb-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="search-box" style={{ flex: 1, minWidth: 200 }}>
            <Search size={14} style={{ color: 'var(--text-muted)' }} />
            <input
              placeholder="Search IP, username, message..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className="form-input form-select"
            style={{ width: 140 }}
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
          >
            <option value="">All Severity</option>
            {SEVERITY_OPTIONS.filter(Boolean).map(s => (
              <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
            ))}
          </select>

          <select
            className="form-input form-select"
            style={{ width: 130 }}
            value={source}
            onChange={(e) => setSource(e.target.value)}
          >
            <option value="">All Sources</option>
            {SOURCE_OPTIONS.filter(Boolean).map(s => (
              <option key={s} value={s}>{s.toUpperCase()}</option>
            ))}
          </select>

          {(search || severity || source) && (
            <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setSeverity(''); setSource('') }}>
              Clear Filters
            </button>
          )}
        </div>
      </motion.div>

      {/* Logs Table */}
      <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: 8 }}>
            {[...Array(10)].map((_, i) => <div key={i} className="skeleton" style={{ height: 40 }} />)}
          </div>
        ) : logs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📋</div>
            <div className="empty-state-title">No logs found</div>
            <div className="empty-state-desc">Upload a log file or adjust your filters</div>
          </div>
        ) : (
          <>
            <div className="table-container" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
              <table>
                <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                  <tr>
                    <th>Timestamp</th>
                    <th>Source</th>
                    <th>Source IP</th>
                    <th>User</th>
                    <th>Event Type</th>
                    <th>Status</th>
                    <th>Severity</th>
                    <th>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td style={{ fontSize: '0.75rem', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        {log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}
                      </td>
                      <td>
                        <span style={{ padding: '2px 6px', background: 'var(--bg-tertiary)', borderRadius: 4, fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
                          {log.source || '—'}
                        </span>
                      </td>
                      <td>
                        {log.source_ip
                          ? <span className="ip-badge">{log.source_ip}</span>
                          : <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>—</span>
                        }
                      </td>
                      <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {log.username || '—'}
                      </td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {log.event_type?.replace(/_/g, ' ') || '—'}
                      </td>
                      <td style={{ fontFamily: 'JetBrains Mono', fontSize: '0.8rem', color: log.status_code?.startsWith('4') || log.status_code?.startsWith('5') ? 'var(--high)' : 'var(--text-muted)' }}>
                        {log.status_code || '—'}
                      </td>
                      <td>
                        <span className={`badge ${log.severity}`}>{log.severity}</span>
                      </td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: 300 }}>
                        <span className="truncate" style={{ display: 'block' }}>
                          {log.message || '—'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="pagination">
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginRight: 'auto' }}>
                Showing {((page - 1) * size) + 1}–{Math.min(page * size, total)} of {total.toLocaleString()} entries
              </span>
              <button className="page-btn" onClick={() => setPage(1)} disabled={page === 1}><ChevronLeft size={12} /><ChevronLeft size={12} /></button>
              <button className="page-btn" onClick={() => setPage(p => p - 1)} disabled={page === 1}><ChevronLeft size={14} /></button>
              {[...Array(Math.min(5, pages))].map((_, i) => {
                const p = Math.max(1, Math.min(page - 2, pages - 4)) + i
                return p <= pages ? (
                  <button key={p} className={`page-btn ${p === page ? 'active' : ''}`} onClick={() => setPage(p)}>{p}</button>
                ) : null
              })}
              <button className="page-btn" onClick={() => setPage(p => p + 1)} disabled={page === pages}><ChevronRight size={14} /></button>
              <button className="page-btn" onClick={() => setPage(pages)} disabled={page === pages}><ChevronRight size={12} /><ChevronRight size={12} /></button>
            </div>
          </>
        )}
      </motion.div>
    </div>
  )
}
