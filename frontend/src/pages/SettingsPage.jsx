import { useState } from 'react'
import { motion } from 'framer-motion'
import { Settings, Shield, Cpu, Bell, Save, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    anomalyThreshold: 40,
    simulationInterval: 1.5,
    activeModel: 'isolation_forest',
    alertSeverityRules: {
      brute_force_threshold: 5,
      scan_port_threshold: 5,
      unusual_hour_start: 0,
      unusual_hour_end: 6,
    },
    notificationsEnabled: true,
    criticalAlertSound: true,
    maxLiveLogs: 200,
  })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    // In real app, call PATCH /api/settings
    await new Promise(r => setTimeout(r, 800))
    localStorage.setItem('tl_settings', JSON.stringify(settings))
    toast.success('Settings saved!')
    setSaving(false)
  }

  const update = (key, value) => setSettings(prev => ({ ...prev, [key]: value }))
  const updateNested = (parent, key, value) => setSettings(prev => ({ ...prev, [parent]: { ...prev[parent], [key]: value } }))

  const SettingRow = ({ label, desc, children }) => (
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '14px 0', borderBottom: '1px solid var(--border-card)', gap: 16 }}>
      <div>
        <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>{label}</div>
        {desc && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>{desc}</div>}
      </div>
      <div style={{ flexShrink: 0 }}>{children}</div>
    </div>
  )

  const Toggle = ({ value, onChange }) => (
    <button
      onClick={() => onChange(!value)}
      style={{
        width: 44, height: 24,
        borderRadius: 12,
        background: value ? 'var(--cyan)' : 'var(--bg-tertiary)',
        border: `2px solid ${value ? 'var(--cyan)' : 'var(--border-card)'}`,
        cursor: 'pointer',
        position: 'relative',
        transition: 'all 0.2s',
      }}
    >
      <span style={{
        position: 'absolute',
        width: 16, height: 16,
        borderRadius: '50%',
        background: value ? '#000' : 'var(--text-muted)',
        top: 2,
        left: value ? 22 : 2,
        transition: 'left 0.2s',
      }} />
    </button>
  )

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Configure detection thresholds, model selection, and system preferences</p>
        </div>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? <><RefreshCw size={14} /> Saving...</> : <><Save size={14} /> Save Changes</>}
        </button>
      </div>

      <div className="grid grid-2 gap-4">
        {/* ML Settings */}
        <motion.div className="card" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="section-title mb-4">
            <Cpu size={14} style={{ color: 'var(--cyan)' }} /> ML Detection Settings
          </div>
          <SettingRow
            label="Anomaly Risk Threshold"
            desc={`Logs with risk score ≥ ${settings.anomalyThreshold} are flagged as threats`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <input
                type="range" min={10} max={90} step={5}
                value={settings.anomalyThreshold}
                onChange={e => update('anomalyThreshold', parseInt(e.target.value))}
                style={{ width: 100, accentColor: 'var(--cyan)' }}
              />
              <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--cyan)', minWidth: 30 }}>{settings.anomalyThreshold}</span>
            </div>
          </SettingRow>
          <SettingRow
            label="Active ML Model"
            desc="Model used for threat scoring"
          >
            <select className="form-input form-select" style={{ width: 200 }} value={settings.activeModel} onChange={e => update('activeModel', e.target.value)}>
              <option value="isolation_forest">Isolation Forest (Unsupervised)</option>
              <option value="random_forest">Random Forest (Supervised)</option>
              <option value="logistic_regression">Logistic Regression (Baseline)</option>
              <option value="rule_based">Rule-Based Only</option>
            </select>
          </SettingRow>
        </motion.div>

        {/* Alert Rules */}
        <motion.div className="card" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <div className="section-title mb-4">
            <Shield size={14} style={{ color: 'var(--cyan)' }} /> Alert Rule Thresholds
          </div>
          <SettingRow
            label="Brute Force Threshold"
            desc="Number of failed logins to trigger alert"
          >
            <input type="number" className="form-input" style={{ width: 80 }} min={2} max={20}
              value={settings.alertSeverityRules.brute_force_threshold}
              onChange={e => updateNested('alertSeverityRules', 'brute_force_threshold', parseInt(e.target.value))} />
          </SettingRow>
          <SettingRow
            label="Port Scan Threshold"
            desc="Number of port events to trigger alert"
          >
            <input type="number" className="form-input" style={{ width: 80 }} min={2} max={50}
              value={settings.alertSeverityRules.scan_port_threshold}
              onChange={e => updateNested('alertSeverityRules', 'scan_port_threshold', parseInt(e.target.value))} />
          </SettingRow>
          <SettingRow
            label="Unusual Hours"
            desc="Activity during these hours is flagged"
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input type="number" className="form-input" style={{ width: 60 }} min={0} max={12}
                value={settings.alertSeverityRules.unusual_hour_start}
                onChange={e => updateNested('alertSeverityRules', 'unusual_hour_start', parseInt(e.target.value))} />
              <span style={{ color: 'var(--text-muted)' }}>to</span>
              <input type="number" className="form-input" style={{ width: 60 }} min={0} max={23}
                value={settings.alertSeverityRules.unusual_hour_end}
                onChange={e => updateNested('alertSeverityRules', 'unusual_hour_end', parseInt(e.target.value))} />
              <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>:00h</span>
            </div>
          </SettingRow>
        </motion.div>

        {/* Simulation Settings */}
        <motion.div className="card" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <div className="section-title mb-4">
            <Settings size={14} style={{ color: 'var(--cyan)' }} /> Live Simulation Settings
          </div>
          <SettingRow
            label="Simulation Speed"
            desc="Interval between generated log events"
          >
            <select className="form-input form-select" style={{ width: 160 }} value={settings.simulationInterval} onChange={e => update('simulationInterval', parseFloat(e.target.value))}>
              <option value={0.5}>Fast (0.5s)</option>
              <option value={1.0}>Normal (1.0s)</option>
              <option value={1.5}>Default (1.5s)</option>
              <option value={3.0}>Slow (3.0s)</option>
              <option value={5.0}>Very Slow (5.0s)</option>
            </select>
          </SettingRow>
          <SettingRow
            label="Max Live Log Buffer"
            desc="Maximum logs kept in live view"
          >
            <select className="form-input form-select" style={{ width: 120 }} value={settings.maxLiveLogs} onChange={e => update('maxLiveLogs', parseInt(e.target.value))}>
              <option value={100}>100 logs</option>
              <option value={200}>200 logs</option>
              <option value={500}>500 logs</option>
            </select>
          </SettingRow>
        </motion.div>

        {/* Notification Settings */}
        <motion.div className="card" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <div className="section-title mb-4">
            <Bell size={14} style={{ color: 'var(--cyan)' }} /> Notification Settings
          </div>
          <SettingRow label="Enable Notifications" desc="Show toast notifications for alerts">
            <Toggle value={settings.notificationsEnabled} onChange={v => update('notificationsEnabled', v)} />
          </SettingRow>
          <SettingRow label="Critical Alert Sound" desc="Play sound for critical alerts (if browser allows)">
            <Toggle value={settings.criticalAlertSound} onChange={v => update('criticalAlertSound', v)} />
          </SettingRow>
        </motion.div>
      </div>

      {/* About system */}
      <motion.div className="card mt-4" style={{ borderColor: 'rgba(0,212,255,0.1)', background: 'rgba(0,212,255,0.02)' }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {[
            { label: 'System Version', value: 'v1.0.0' },
            { label: 'Backend', value: 'FastAPI + Python 3.11' },
            { label: 'ML Engine', value: 'scikit-learn + joblib' },
            { label: 'Frontend', value: 'React 18 + Vite' },
            { label: 'Database', value: 'SQLite (AsyncIO)' },
            { label: 'Project Type', value: 'BSIT-VI Semester' },
          ].map(({ label, value }) => (
            <div key={label}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: 4 }}>{value}</div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
