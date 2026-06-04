import { motion } from 'framer-motion'
import { Shield, Brain } from 'lucide-react'

const TECH_STACK = [
  { category: 'Frontend', items: ['React 18', 'Vite', 'Recharts', 'Framer Motion', 'React Router', 'Lucide Icons'] },
  { category: 'Backend', items: ['Python FastAPI', 'SQLAlchemy (async)', 'SQLite', 'Pydantic v2', 'Uvicorn'] },
  { category: 'ML/AI', items: ['scikit-learn', 'Isolation Forest', 'Random Forest', 'Logistic Regression', 'pandas', 'numpy', 'joblib'] },
  { category: 'Security', items: ['JWT (python-jose)', 'bcrypt', 'CORS', 'Input validation', 'File size limits'] },
  { category: 'DevOps', items: ['Docker Compose', 'Environment variables', '.env configuration', 'Background tasks'] },
  { category: 'Datasets', items: ['Loghub (HDFS, BGL)', 'CICIDS2017', 'UNSW-NB15', 'Synthetic log generator'] },
]

export default function AboutPage() {
  return (
    <div>
      {/* Hero */}
      <motion.div
        className="card mb-6"
        style={{
          background: 'linear-gradient(135deg, rgba(0,212,255,0.05), rgba(59,130,246,0.05))',
          borderColor: 'rgba(0,212,255,0.2)',
          padding: '40px',
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
        }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div style={{ position: 'absolute', inset: 0, opacity: 0.03 }}>
          <svg width="100%" height="100%"><defs><pattern id="grid2" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#00d4ff" strokeWidth="0.5"/></pattern></defs><rect width="100%" height="100%" fill="url(#grid2)" /></svg>
        </div>
        <motion.div
          style={{ width: 72, height: 72, background: 'var(--gradient-cyan)', borderRadius: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', boxShadow: '0 0 40px rgba(0,212,255,0.3)' }}
          animate={{ boxShadow: ['0 0 20px rgba(0,212,255,0.3)', '0 0 50px rgba(0,212,255,0.5)', '0 0 20px rgba(0,212,255,0.3)'] }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          <Shield size={32} color="#000" />
        </motion.div>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, marginBottom: 8 }}>ThreatLens AI</h1>
        <p style={{ fontSize: '1.1rem', color: 'var(--cyan)', fontWeight: 600, marginBottom: 12 }}>
          Machine Learning Based Log Analysis and Threat Detection Dashboard
        </p>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', maxWidth: 700, margin: '0 auto 20px' }}>
          A full-stack AI-powered cybersecurity SIEM (Security Information and Event Management) system
          that analyzes system logs using machine learning to detect threats, anomalies, and suspicious
          activity in real time.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 12, flexWrap: 'wrap' }}>
          {['BSIT-VI', 'Cybersecurity Lab', 'Semester Project', '2024'].map(tag => (
            <span key={tag} style={{ padding: '4px 14px', background: 'var(--cyan-dim)', color: 'var(--cyan)', borderRadius: 20, fontSize: '0.8rem', fontWeight: 600, border: '1px solid var(--border)' }}>
              {tag}
            </span>
          ))}
        </div>
      </motion.div>

      {/* Problem Statement */}
      <div className="grid grid-2 mb-4">
        <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
          <div className="section-title mb-4">🎯 Problem Statement</div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            Organizations generate massive volumes of system and security logs daily. Manual analysis
            is impossible at scale. Traditional rule-based IDS systems have high false positive rates
            and miss novel attacks. This project builds an AI-powered system that automatically parses,
            analyzes, and detects threats using machine learning, replacing the need for manual log review.
          </p>
        </motion.div>
        <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}>
          <div className="section-title mb-4">✅ Objectives</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              'Automate log ingestion from multiple sources',
              'Parse and normalize heterogeneous log formats',
              'Apply ML models (Isolation Forest, Random Forest) for anomaly detection',
              'Generate actionable security alerts with severity levels',
              'Visualize threats in a professional SOC dashboard',
              'Support real-time live log simulation via WebSocket',
              'Export comprehensive security reports (PDF/CSV)',
            ].map((obj, i) => (
              <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--cyan)', flexShrink: 0, marginTop: 2 }}>▶</span>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{obj}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
      {/* Tech Stack */}
      <motion.div className="card mb-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
        <div className="section-title mb-4">
          <Brain size={14} style={{ color: 'var(--cyan)' }} /> Technology Stack
        </div>
        <div className="grid grid-3">
          {TECH_STACK.map((cat, i) => (
            <div key={i} style={{ padding: '12px 0' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--cyan)', marginBottom: 8 }}>
                {cat.category}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {cat.items.map((item, j) => (
                  <div key={j} style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    <span style={{ width: 4, height: 4, borderRadius: '50%', background: 'var(--cyan)', flexShrink: 0 }} />
                    {item}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Footer */}
      <motion.div
        style={{ textAlign: 'center', padding: '24px', fontSize: '0.8rem', color: 'var(--text-muted)' }}
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}
      >
        <Shield size={20} style={{ color: 'var(--cyan)', marginBottom: 8 }} />
        <p>ThreatLens AI — BSIT-VI Cybersecurity Lab Semester Project © 2024</p>
        <p style={{ marginTop: 4 }}>Built with FastAPI · React · scikit-learn · SQLite</p>
      </motion.div>
    </div>
  )
}
