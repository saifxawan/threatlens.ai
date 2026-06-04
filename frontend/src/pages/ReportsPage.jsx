import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { BarChart3, Download, FileText, FileSpreadsheet, RefreshCw, Shield, AlertTriangle, Target } from 'lucide-react'
import { reportsService } from '../services/services'
import toast from 'react-hot-toast'

export default function ReportsPage() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [downloadingPDF, setDownloadingPDF] = useState(false)
  const [downloadingCSV, setDownloadingCSV] = useState(false)

  useEffect(() => {
    reportsService.summary()
      .then(r => setSummary(r.data))
      .catch(() => toast.error('Failed to load report'))
      .finally(() => setLoading(false))
  }, [])

  const downloadPDF = async () => {
    setDownloadingPDF(true)
    try {
      const res = await reportsService.exportPDF()
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.download = 'threatlens_report.pdf'
      link.click()
      URL.revokeObjectURL(url)
      toast.success('PDF report downloaded!')
    } catch {
      toast.error('PDF download failed')
    } finally {
      setDownloadingPDF(false)
    }
  }

  const downloadCSV = async () => {
    setDownloadingCSV(true)
    try {
      const res = await reportsService.exportCSV()
      const url = URL.createObjectURL(new Blob([res.data], { type: 'text/csv' }))
      const link = document.createElement('a')
      link.href = url
      link.download = 'threatlens_alerts.csv'
      link.click()
      URL.revokeObjectURL(url)
      toast.success('CSV export downloaded!')
    } catch {
      toast.error('CSV download failed')
    } finally {
      setDownloadingCSV(false)
    }
  }

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 80 }} />)}
    </div>
  )

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Security Reports</h1>
          <p className="page-subtitle">Generate and export comprehensive threat analysis reports</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-ghost" onClick={() => reportsService.summary().then(r => setSummary(r.data))}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button className="btn btn-ghost" onClick={downloadCSV} disabled={downloadingCSV}>
            <FileSpreadsheet size={14} /> {downloadingCSV ? 'Exporting...' : 'Export CSV'}
          </button>
          <button className="btn btn-primary" onClick={downloadPDF} disabled={downloadingPDF}>
            <Download size={14} /> {downloadingPDF ? 'Generating...' : 'Download PDF Report'}
          </button>
        </div>
      </div>

      {summary && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-4 mb-4">
            {[
              { label: 'Logs Analyzed', value: summary.total_logs_analyzed?.toLocaleString(), icon: BarChart3, color: 'cyan' },
              { label: 'Anomalies', value: summary.total_anomalies_detected?.toLocaleString(), icon: AlertTriangle, color: 'red' },
              { label: 'Total Alerts', value: summary.total_alerts?.toLocaleString(), icon: Shield, color: 'orange' },
              { label: 'Anomaly Rate', value: summary.total_logs_analyzed ? `${((summary.total_anomalies_detected / summary.total_logs_analyzed) * 100).toFixed(1)}%` : '—', icon: Target, color: 'yellow' },
            ].map(({ label, value, icon: Icon, color }, i) => (
              <motion.div key={i} className={`metric-card ${color}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}>
                <div className="metric-label">{label}</div>
                <div className="metric-value">{value}</div>
                <div style={{ position: 'absolute', right: 16, top: 16, opacity: 0.15 }}><Icon size={32} /></div>
              </motion.div>
            ))}
          </div>

          <div className="grid grid-2 gap-4 mb-4">
            {/* Top Suspicious IPs */}
            <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
              <div className="section-title mb-4">
                <Target size={14} style={{ color: 'var(--critical)' }} /> Top Suspicious IPs
              </div>
              {summary.top_suspicious_ips?.length ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {summary.top_suspicious_ips.map(({ ip, count }, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ width: 20, fontSize: '0.75rem', color: 'var(--text-muted)' }}>#{i + 1}</span>
                      <span className="ip-badge">{ip}</span>
                      <div style={{ flex: 1, height: 4, background: 'var(--bg-tertiary)', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ height: '100%', background: 'var(--critical)', borderRadius: 2, width: `${Math.min(100, count / summary.top_suspicious_ips[0].count * 100)}%` }} />
                      </div>
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--critical)', minWidth: 30, textAlign: 'right' }}>{count}</span>
                    </div>
                  ))}
                </div>
              ) : <div className="empty-state" style={{ padding: 30 }}><div>No suspicious IPs detected yet</div></div>}
            </motion.div>

            {/* Top Attack Types */}
            <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25 }}>
              <div className="section-title mb-4">
                <AlertTriangle size={14} style={{ color: 'var(--high)' }} /> Top Attack Categories
              </div>
              {summary.top_attack_types?.length ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {summary.top_attack_types.map(({ type, count }, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ width: 20, fontSize: '0.75rem', color: 'var(--text-muted)' }}>#{i + 1}</span>
                      <span style={{ flex: 1, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{type}</span>
                      <div style={{ width: 80, height: 4, background: 'var(--bg-tertiary)', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ height: '100%', background: 'var(--high)', borderRadius: 2, width: `${Math.min(100, count / summary.top_attack_types[0].count * 100)}%` }} />
                      </div>
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--high)', minWidth: 30, textAlign: 'right' }}>{count}</span>
                    </div>
                  ))}
                </div>
              ) : <div className="empty-state" style={{ padding: 30 }}><div>No attack types recorded yet</div></div>}
            </motion.div>
          </div>

          {/* Recommendations */}
          <motion.div className="card" style={{ borderColor: 'rgba(0,212,255,0.2)' }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
            <div className="section-title mb-4">
              <Shield size={14} style={{ color: 'var(--cyan)' }} /> Security Recommendations
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
              {summary.recommendations?.map((rec, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, padding: 12, background: 'rgba(0,212,255,0.04)', border: '1px solid rgba(0,212,255,0.1)', borderRadius: 8 }}>
                  <span style={{ fontSize: '1rem', flexShrink: 0 }}>
                    {['🔐', '🛡️', '🔒', '🌐', '🔄'][i] || '✅'}
                  </span>
                  <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{rec}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Report timestamp */}
          <div style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 16, fontFamily: 'JetBrains Mono' }}>
            Report generated: {new Date(summary.generated_at).toLocaleString()}
          </div>
        </>
      )}
    </div>
  )
}
