import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Search, Bell, Wifi, WifiOff, Sun, Shield } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const PAGE_TITLES = {
  '/dashboard': 'Security Dashboard',
  '/logs': 'Log Explorer',
  '/upload': 'Upload Logs',
  '/live-monitor': 'Live Monitor',
  '/alerts': 'Alert Management',
  '/ml-analytics': 'ML Analytics',
  '/reports': 'Reports',
  '/settings': 'Settings',
  '/about': 'About Project',
}

export default function TopBar({ alertCount = 0, isConnected = false, onSearch }) {
  const { pathname } = useLocation()
  const { user } = useAuth()
  const [search, setSearch] = useState('')

  const title = PAGE_TITLES[pathname] || 'ThreatLens AI'
  const pathAlert = pathname.startsWith('/alerts/')

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Shield size={16} style={{ color: 'var(--cyan)' }} />
          <span className="topbar-title">{title}</span>
        </div>
        {/* Live status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', background: 'var(--bg-tertiary)', borderRadius: 20, border: '1px solid var(--border-card)' }}>
          {isConnected
            ? <><span className="status-dot online"></span><span style={{ fontSize: '0.7rem', color: 'var(--low)' }}>LIVE</span></>
            : <><span className="status-dot"></span><span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>OFFLINE</span></>
          }
        </div>
      </div>

      <div className="topbar-right">
        {/* Search */}
        <div className="search-box">
          <Search size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          <input
            type="text"
            placeholder="Search logs, IPs, threats..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              onSearch?.(e.target.value)
            }}
          />
        </div>

        {/* Alert bell */}
        <div style={{ position: 'relative', cursor: 'pointer' }}>
          <Bell size={18} style={{ color: alertCount > 0 ? 'var(--critical)' : 'var(--text-muted)' }} />
          {alertCount > 0 && (
            <span style={{
              position: 'absolute', top: -6, right: -6,
              background: 'var(--critical)',
              color: 'white', fontSize: '0.6rem', fontWeight: 700,
              padding: '1px 4px', borderRadius: 10, minWidth: 16, textAlign: 'center',
            }}>
              {alertCount > 99 ? '99+' : alertCount}
            </span>
          )}
        </div>

        {/* Current time */}
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', padding: '0 8px' }}>
          {new Date().toLocaleTimeString('en-US', { hour12: false })}
        </div>

        {/* User */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="user-avatar">
            {user?.name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{user?.name || 'User'}</span>
            <span style={{ fontSize: '0.65rem', color: 'var(--cyan)' }}>{user?.role || 'analyst'}</span>
          </div>
        </div>
      </div>
    </header>
  )
}
