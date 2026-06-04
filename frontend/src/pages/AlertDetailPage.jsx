import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Shield, AlertTriangle, CheckCircle, Clock, User, MapPin, Target, Lightbulb } from 'lucide-react'
import { alertsService } from '../services/services'
import toast from 'react-hot-toast'

const STATUS_OPTIONS = ['new', 'investigating', 'resolved', 'false_positive']
const SEV_COLORS = { critical: 'var(--critical)', high: 'var(--high)', medium: 'var(--medium)', low: 'var(--low)', informational: 'var(--text-muted)' }

export default function AlertDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [alert, setAlert] = useState(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)

  useEffect(() => {
    alertsService.get(id)
      .then(r => setAlert(r.data))
      .catch(() => toast.error('Alert not found'))
      .finally(() => setLoading(false))
  }, [id])

  const updateStatus = async (newStatus) => {
    setUpdating(true)
    try {
      const res = await alertsService.updateStatus(id, newStatus)
      setAlert(res.data)
      toast.success(`Status updated to "${newStatus}"`)
    } catch {
      toast.error('Failed to update')
    } finally {
      setUpdating(false)
    }
  }

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 80 }} />)}
    </div>
  )

  if (!alert) return (
    <div className="empty-state">
      <div className="empty-state-icon">❌</div>
      <div className="empty-state-title">Alert not found</div>
    </div>
  )

  const sevColor = SEV_COLORS[alert.severity] || 'var(--text-muted)'
  const timelineSteps = [
    { label: 'Alert Created', time: alert.created_at, done: true },
    { label: 'Under Investigation', time: alert.status !== 'new' ? alert.updated_at : null, done: ['investigating', 'resolved', 'false_positive'].includes(alert.status) },
    { label: 'Resolved / Closed', time: ['resolved', 'false_positive'].includes(alert.status) ? alert.updated_at : null, done: ['resolved', 'false_positive'].includes(alert.status) },
  ]

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/alerts')}>
            <ArrowLeft size={14} /> Back
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className={`badge ${alert.severity}`}>{alert.severity}</span>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800 }}>{alert.title}</h1>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>Alert #{alert.id} · {alert.threat_type}</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {STATUS_OPTIONS.map(s => (
            <button
              key={s}
              className={`btn btn-sm ${alert.status === s ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => updateStatus(s)}
              disabled={updating || alert.status === s}
            >
              {s.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-2 gap-4">
        {/* Main details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Overview */}
          <motion.div className="card" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <div className="section-title mb-4">
              <AlertTriangle size={14} style={{ color: sevColor }} /> Threat Overview
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { label: 'Threat Type', value: alert.threat_type, icon: Target },
                { label: 'Source IP', value: alert.source_ip, icon: MapPin, mono: true, color: 'var(--cyan)' },
                { label: 'Severity', value: alert.severity?.toUpperCase(), icon: AlertTriangle, color: sevColor },
                { label: 'Status', value: alert.status?.replace('_', ' ').toUpperCase(), icon: Clock },
                { label: 'Assigned To', value: alert.assigned_to || 'Unassigned', icon: User },
              ].map(({ label, value, icon: Icon, mono, color }) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid var(--border-card)' }}>
                  <Icon size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', width: 120, flexShrink: 0 }}>{label}</span>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: color || 'var(--text-primary)', fontFamily: mono ? 'JetBrains Mono' : 'inherit' }}>
                    {value || '—'}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Description */}
          <motion.div className="card" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <div className="section-title mb-4">
              <Shield size={14} style={{ color: 'var(--cyan)' }} /> Description
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              {alert.description || 'No description available.'}
            </p>
          </motion.div>

          {/* Recommendation */}
          <motion.div className="card" style={{ borderColor: 'rgba(0,212,255,0.2)', background: 'rgba(0,212,255,0.03)' }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
            <div className="section-title mb-4">
              <Lightbulb size={14} style={{ color: 'var(--cyan)' }} /> Recommended Action
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              {alert.recommendation || 'Investigate and monitor the suspicious activity.'}
            </p>
          </motion.div>
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Risk gauge */}
          <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}>
            <div className="section-title mb-4">
              <Target size={14} style={{ color: sevColor }} /> Severity Assessment
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
              {['critical', 'high', 'medium', 'low'].map(sev => (
                <div key={sev} style={{
                  padding: 12,
                  background: alert.severity === sev ? `${SEV_COLORS[sev]}22` : 'var(--bg-tertiary)',
                  border: `1px solid ${alert.severity === sev ? SEV_COLORS[sev] : 'var(--border-card)'}`,
                  borderRadius: 8,
                  textAlign: 'center',
                }}>
                  <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: SEV_COLORS[sev] }}>{sev}</div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Timeline */}
          <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
            <div className="section-title mb-4">
              <Clock size={14} style={{ color: 'var(--cyan)' }} /> Incident Timeline
            </div>
            <div style={{ position: 'relative', paddingLeft: 20 }}>
              <div style={{ position: 'absolute', left: 7, top: 0, bottom: 0, width: 2, background: 'var(--border-card)' }} />
              {timelineSteps.map(({ label, time, done }, i) => (
                <div key={i} style={{ position: 'relative', marginBottom: 20 }}>
                  <div style={{
                    position: 'absolute', left: -20,
                    width: 14, height: 14,
                    borderRadius: '50%',
                    background: done ? 'var(--low)' : 'var(--bg-tertiary)',
                    border: `2px solid ${done ? 'var(--low)' : 'var(--border-card)'}`,
                  }} />
                  <div style={{ paddingLeft: 8 }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: done ? 'var(--text-primary)' : 'var(--text-muted)' }}>{label}</div>
                    {time && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2, fontFamily: 'JetBrains Mono' }}>
                      {new Date(time).toLocaleString()}
                    </div>}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* MITRE-inspired info */}
          <motion.div className="card" style={{ background: 'rgba(99,102,241,0.05)', borderColor: 'rgba(99,102,241,0.2)' }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25 }}>
            <div className="section-title mb-4" style={{ color: 'var(--indigo)' }}>
              🎯 MITRE ATT&CK (Conceptual)
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.8rem' }}>
              {getMitreMapping(alert.threat_type).map(({ tactic, technique }, i) => (
                <div key={i} style={{ display: 'flex', gap: 8 }}>
                  <span style={{ padding: '1px 6px', background: 'rgba(99,102,241,0.15)', borderRadius: 4, color: 'var(--indigo)', fontSize: '0.7rem', fontWeight: 600 }}>{tactic}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{technique}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}

function getMitreMapping(threatType) {
  const mappings = {
    'Brute Force': [
      { tactic: 'Credential Access', technique: 'T1110 — Brute Force' },
      { tactic: 'Persistence', technique: 'T1078 — Valid Accounts' },
    ],
    'Port Scan / Reconnaissance': [
      { tactic: 'Discovery', technique: 'T1046 — Network Service Scanning' },
      { tactic: 'Reconnaissance', technique: 'T1595 — Active Scanning' },
    ],
    'Privilege Escalation': [
      { tactic: 'Privilege Escalation', technique: 'T1548 — Abuse Elevation Control' },
      { tactic: 'Defense Evasion', technique: 'T1548.003 — Sudo Abuse' },
    ],
    'Malware-like Behavior': [
      { tactic: 'Execution', technique: 'T1059 — Command and Script Interpreter' },
      { tactic: 'C2', technique: 'T1071 — Application Layer Protocol' },
    ],
    'SQL Injection / Web Attack': [
      { tactic: 'Initial Access', technique: 'T1190 — Exploit Public-Facing App' },
      { tactic: 'Execution', technique: 'T1059 — Command Injection' },
    ],
    'Unauthorized Access': [
      { tactic: 'Initial Access', technique: 'T1078 — Valid Accounts' },
      { tactic: 'Lateral Movement', technique: 'T1021 — Remote Services' },
    ],
  }
  return mappings[threatType] || [{ tactic: 'Unknown', technique: 'Manual investigation required' }]
}
