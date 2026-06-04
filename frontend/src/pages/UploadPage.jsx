import { useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, CheckCircle, AlertCircle, Loader, Database, Clock, X, RefreshCw } from 'lucide-react'
import { logsService } from '../services/services'
import toast from 'react-hot-toast'

const ACCEPTED_TYPES = ['.csv', '.txt', '.log', '.json']

function ProgressBar({ value, color = 'var(--cyan)' }) {
  return (
    <div style={{ width: '100%', height: 6, background: 'var(--bg-tertiary)', borderRadius: 3, overflow: 'hidden', marginTop: 8 }}>
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.4 }}
        style={{ height: '100%', background: color, borderRadius: 3 }}
      />
    </div>
  )
}

export default function UploadPage() {
  const [dragOver, setDragOver] = useState(false)
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [datasets, setDatasets] = useState([])
  const [loadingDatasets, setLoadingDatasets] = useState(false)
  const pollRef = useRef(null)

  const fetchDatasets = useCallback(async () => {
    setLoadingDatasets(true)
    try {
      const res = await logsService.datasets()
      setDatasets(res.data || [])
    } catch {} finally {
      setLoadingDatasets(false)
    }
  }, [])

  // FIX: use useEffect (not useState) to fetch on mount
  useEffect(() => { fetchDatasets() }, [fetchDatasets])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const dropped = Array.from(e.dataTransfer.files)
    addFiles(dropped)
  }, [])

  const handleFileInput = (e) => addFiles(Array.from(e.target.files))

  const addFiles = (newFiles) => {
    const valid = newFiles.filter(f => ACCEPTED_TYPES.some(ext => f.name.toLowerCase().endsWith(ext)))
    if (valid.length < newFiles.length) toast.error('Some files skipped — only CSV, TXT, LOG, JSON allowed')
    setFiles(prev => [...prev, ...valid.map(f => ({ file: f, status: 'pending', progress: 0, result: null }))])
  }

  const removeFile = (idx) => setFiles(prev => prev.filter((_, i) => i !== idx))

  const uploadAll = async () => {
    if (!files.length) return
    setUploading(true)
    const pending = files.filter(f => f.status === 'pending')

    for (let i = 0; i < pending.length; i++) {
      const item = pending[i]
      const idx = files.findIndex(f => f.file.name === item.file.name && f.status === 'pending')

      setFiles(prev => prev.map((f, j) => j === idx ? { ...f, status: 'uploading', progress: 0 } : f))

      try {
        const res = await logsService.upload(item.file, (e) => {
          if (e.total) {
            setFiles(prev => prev.map((f, j) => j === idx ? { ...f, progress: Math.round((e.loaded / e.total) * 100) } : f))
          }
        })
        setFiles(prev => prev.map((f, j) => j === idx ? { ...f, status: 'done', progress: 100, result: res.data } : f))
        toast.success(`${item.file.name} uploaded! ML analysis running...`)
      } catch (err) {
        setFiles(prev => prev.map((f, j) => j === idx ? { ...f, status: 'error', error: err.response?.data?.detail || 'Upload failed' } : f))
        toast.error(`Failed to upload ${item.file.name}`)
      }
    }

    setUploading(false)
    fetchDatasets()
    // Poll for processing status every 3 seconds for up to 60s
    if (pollRef.current) clearInterval(pollRef.current)
    let polls = 0
    pollRef.current = setInterval(async () => {
      polls++
      await fetchDatasets()
      if (polls >= 20) clearInterval(pollRef.current)
    }, 3000)
  }

  const getStatusColor = (status) => ({
    pending: 'var(--text-muted)',
    uploading: 'var(--cyan)',
    done: 'var(--low)',
    error: 'var(--critical)',
  }[status] || 'var(--text-muted)')

  const getStatusIcon = (status) => ({
    pending: <Clock size={14} />,
    uploading: <Loader size={14} className="spin" />,
    done: <CheckCircle size={14} />,
    error: <AlertCircle size={14} />,
  }[status])

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  const getStatusBadge = (status) => {
    const map = {
      pending: { bg: 'var(--info-dim)', color: 'var(--text-muted)', label: 'Pending' },
      processing: { bg: 'rgba(59,130,246,0.15)', color: 'var(--blue)', label: 'Processing' },
      completed: { bg: 'var(--low-dim)', color: 'var(--low)', label: 'Completed' },
      failed: { bg: 'var(--critical-dim)', color: 'var(--critical)', label: 'Failed' },
    }
    const s = map[status] || map.pending
    return <span style={{ padding: '2px 8px', borderRadius: 12, fontSize: '0.7rem', fontWeight: 700, background: s.bg, color: s.color }}>{s.label}</span>
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Upload Log Files</h1>
          <p className="page-subtitle">Upload CSV, TXT, LOG, or JSON files for ML analysis. Supports syslog, Apache, HDFS, and custom formats.</p>
        </div>
      </div>

      <div className="grid grid-2 gap-4">
        {/* Drop zone */}
        <div>
          <motion.div
            className={`dropzone ${dragOver ? 'active' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input').click()}
            whileHover={{ scale: 1.01 }}
          >
            <input id="file-input" type="file" hidden multiple accept=".csv,.txt,.log,.json" onChange={handleFileInput} />
            <motion.div
              animate={{ y: dragOver ? -5 : 0 }}
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}
            >
              <div style={{
                width: 64, height: 64,
                background: dragOver ? 'var(--cyan-dim)' : 'var(--bg-tertiary)',
                borderRadius: 16,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: `2px solid ${dragOver ? 'var(--cyan)' : 'var(--border-card)'}`,
                transition: 'all 0.2s',
              }}>
                <Upload size={28} style={{ color: dragOver ? 'var(--cyan)' : 'var(--text-muted)' }} />
              </div>
              <div>
                <p style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '1rem' }}>
                  {dragOver ? 'Drop files here!' : 'Drag & Drop log files here'}
                </p>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: 4 }}>
                  or click to browse — CSV, TXT, LOG, JSON
                </p>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                {ACCEPTED_TYPES.map(ext => (
                  <span key={ext} style={{ padding: '3px 10px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-card)', borderRadius: 6, fontSize: '0.75rem', fontFamily: 'JetBrains Mono', color: 'var(--cyan)' }}>
                    {ext}
                  </span>
                ))}
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Max file size: 50 MB</p>
            </motion.div>
          </motion.div>

          {/* File queue */}
          <AnimatePresence>
            {files.length > 0 && (
              <motion.div className="card mt-4" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <div className="section-header">
                  <span className="section-title"><FileText size={14} /> Upload Queue ({files.length})</span>
                  <button className="btn btn-primary btn-sm" onClick={uploadAll} disabled={uploading || files.every(f => f.status !== 'pending')}>
                    {uploading ? <><Loader size={12} className="spin" /> Uploading...</> : <><Upload size={12} /> Upload All</>}
                  </button>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {files.map((item, idx) => (
                    <motion.div key={idx} className="card-glass" style={{ padding: 12 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <FileText size={16} style={{ color: 'var(--cyan)', flexShrink: 0 }} />
                        <div style={{ flex: 1, overflow: 'hidden' }}>
                          <div style={{ fontSize: '0.85rem', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {item.file.name}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{formatSize(item.file.size)}</div>
                        </div>
                        <span style={{ color: getStatusColor(item.status) }}>{getStatusIcon(item.status)}</span>
                        {item.status === 'pending' && (
                          <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }} onClick={() => removeFile(idx)}>
                            <X size={14} />
                          </button>
                        )}
                      </div>
                      {item.status === 'uploading' && <ProgressBar value={item.progress} />}
                      {item.status === 'done' && item.result && (
                        <div style={{ marginTop: 8, fontSize: '0.75rem', color: 'var(--low)' }}>
                          ✅ Dataset ID: {item.result.id} — Processing in background...
                        </div>
                      )}
                      {item.status === 'error' && (
                        <div style={{ marginTop: 8, fontSize: '0.75rem', color: 'var(--critical)' }}>
                          ❌ {item.error}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Supported formats info + dataset history */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <div className="section-title mb-4">
              <Database size={14} style={{ color: 'var(--cyan)' }} />
              Supported Log Formats
            </div>
            {[
              { fmt: 'Syslog', desc: 'Linux system logs (auth.log, syslog)', example: 'Jan 15 12:34:56 host sshd: ...' },
              { fmt: 'Apache/Nginx', desc: 'Combined log format web server logs', example: '192.168.1.1 - - [15/Jan/2024...] "GET /"' },
              { fmt: 'HDFS Logs', desc: 'Hadoop Distributed File System logs', example: '081109 203518 3 INFO dfs.DataNode...' },
              { fmt: 'CSV', desc: 'Any CSV with timestamp/ip/message columns', example: 'timestamp,source_ip,event_type,...' },
            ].map(({ fmt, desc, example }) => (
              <div key={fmt} style={{ padding: '10px 0', borderBottom: '1px solid var(--border-card)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ padding: '1px 8px', background: 'var(--cyan-dim)', color: 'var(--cyan)', borderRadius: 4, fontSize: '0.7rem', fontWeight: 700 }}>{fmt}</span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{desc}</span>
                </div>
                <code style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono' }}>{example}</code>
              </div>
            ))}
          </div>

          {/* Dataset history */}
          <div className="card">
            <div className="section-header">
              <span className="section-title"><Database size={14} style={{ color: 'var(--cyan)' }} /> Dataset History</span>
              <button className="btn btn-ghost btn-sm" onClick={fetchDatasets}><RefreshCw size={12} /></button>
            </div>
            {loadingDatasets ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[...Array(3)].map((_, i) => <div key={i} className="skeleton" style={{ height: 48 }} />)}
              </div>
            ) : datasets.length === 0 ? (
              <div className="empty-state" style={{ padding: 30 }}>
                <div style={{ fontSize: '2rem' }}>📁</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No datasets uploaded yet</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {datasets.slice(0, 8).map((ds) => (
                  <div key={ds.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0', borderBottom: '1px solid var(--border-card)' }}>
                    <FileText size={14} style={{ color: 'var(--cyan)', flexShrink: 0 }} />
                    <div style={{ flex: 1, overflow: 'hidden' }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {ds.original_name || ds.file_name}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {ds.processed_rows}/{ds.total_rows} rows · {new Date(ds.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    {getStatusBadge(ds.upload_status)}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


