import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_BASE}/api`
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  const tenant = localStorage.getItem('tenant')
  if (token) {
    config.headers = config.headers ?? {}
    config.headers['Authorization'] = `Bearer ${token}`
  }
  if (tenant) {
    config.headers = config.headers ?? {}
    config.headers['X-Tenant'] = tenant
  }
  return config
})

// Capture refreshed token header for sliding sessions
api.interceptors.response.use((response) => {
  const refreshed = response.headers['x-refreshed-token'] as string | undefined
  if (refreshed) {
    localStorage.setItem('token', refreshed)
  }
  return response
}, (error) => {
  return Promise.reject(error)
})



