import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const superAdminApi = axios.create({
  baseURL: `${API_BASE}/api`
})

// Attach Super Admin token only. Do NOT attach X-Tenant for platform endpoints.
superAdminApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('super_admin_token')
  config.headers = config.headers ?? {}
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  // Explicitly ensure tenant header is not present
  if (config.headers['X-Tenant']) delete (config.headers as any)['X-Tenant']
  return config
})


