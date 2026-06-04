import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  Shield, LayoutDashboard, FileText, Upload, Radio,
  Bell, Brain, BarChart3, Settings, Info,
  LogOut, Activity, ChevronRight
} from 'lucide-react'

const navItems = [
  { label: 'MAIN', type: 'section' },
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/alerts', icon: Bell, label: 'Alerts', badge: 'new_alerts' },
  { path: '/live-monitor', icon: Radio, label: 'Live Monitor' },
  { label: 'ANALYSIS', type: 'section' },
  { path: '/logs', icon: FileText, label: 'Log Explorer' },
  { path: '/upload', icon: Upload, label: 'Upload Logs' },
  { path: '/ml-analytics', icon: Brain, label: 'ML Analytics' },
  { label: 'REPORTS', type: 'section' },
  { path: '/reports', icon: BarChart3, label: 'Reports' },
  { label: 'SYSTEM', type: 'section' },
  { path: '/settings', icon: Settings, label: 'Settings' },
  { path: '/about', icon: Info, label: 'About Project' },
]

export default function Sidebar({ alertCount = 0 }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-icon">
          <Shield size={18} />
        </div>
        <div>
          <div className="logo-text">ThreatLens AI</div>
          <div className="logo-sub">SOC Dashboard v1.0</div>
        </div>
      </div>

      {/* Navigation */}
      <div className="sidebar-nav">
        {navItems.map((item, idx) => {
          if (item.type === 'section') {
            return (
              <div key={idx} className="sidebar-section-label">{item.label}</div>
            )
          }

          const Icon = item.icon
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={16} className="nav-icon" />
              <span>{item.label}</span>
              {item.badge === 'new_alerts' && alertCount > 0 && (
                <span className="nav-badge">{alertCount > 99 ? '99+' : alertCount}</span>
              )}
            </NavLink>
          )
        })}
      </div>

      {/* User section */}
      <div style={{
        borderTop: '1px solid var(--border-card)',
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
      }}>
        <div className="user-avatar" style={{ width: 32, height: 32, fontSize: '0.75rem' }}>
          {user?.name?.[0]?.toUpperCase() || 'U'}
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {user?.name || 'User'}
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            {user?.role || 'analyst'}
          </div>
        </div>
        <button
          onClick={handleLogout}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 4 }}
          title="Logout"
        >
          <LogOut size={14} />
        </button>
      </div>
    </nav>
  )
}
