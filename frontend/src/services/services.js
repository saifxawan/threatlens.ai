import api from './api'

export const authService = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (name, email, password, role) => api.post('/auth/register', { name, email, password, role }),
  profile: () => api.get('/auth/profile'),
}

export const logsService = {
  list: (params) => api.get('/logs', { params }),
  get: (id) => api.get(`/logs/${id}`),
  stats: () => api.get('/logs/stats'),
  datasets: () => api.get('/logs/datasets'),
  upload: (file, onProgress) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/logs/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    })
  },
  delete: (id) => api.delete(`/logs/${id}`),
}

export const alertsService = {
  list: (params) => api.get('/alerts', { params }),
  get: (id) => api.get(`/alerts/${id}`),
  stats: () => api.get('/alerts/stats'),
  updateStatus: (id, status, assigned_to) =>
    api.patch(`/alerts/${id}/status`, { status, assigned_to }),
}

export const dashboardService = {
  summary: () => api.get('/dashboard/summary'),
  threatsOverTime: () => api.get('/dashboard/charts/threats-over-time'),
  severityDistribution: () => api.get('/dashboard/charts/severity-distribution'),
  topIPs: () => api.get('/dashboard/charts/top-ips'),
  attackTypes: () => api.get('/dashboard/charts/attack-types'),
  logSources: () => api.get('/dashboard/charts/log-sources'),
  hourlyActivity: () => api.get('/dashboard/charts/hourly-activity'),
  reset: (seed = true) => api.post('/dashboard/reset', null, { params: { seed } }),
}

export const mlService = {
  train: (params) => api.post('/ml/train', null, { params }),
  predict: (log_ids, model_name) => api.post('/ml/predict', log_ids, { params: { model_name } }),
  metrics: () => api.get('/ml/metrics'),
  modelInfo: () => api.get('/ml/model-info'),
  retrain: () => api.post('/ml/retrain'),
}

export const reportsService = {
  summary: () => api.get('/reports/summary'),
  exportCSV: () => api.get('/reports/export/csv', { responseType: 'blob' }),
  exportPDF: () => api.get('/reports/export/pdf', { responseType: 'blob' }),
}

export const liveService = {
  start: (interval) => api.post('/live/start', null, { params: { interval } }),
  stop: () => api.post('/live/stop'),
  status: () => api.get('/live/status'),
}
