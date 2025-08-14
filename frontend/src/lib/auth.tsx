import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api } from './api'

type AuthUser = {
  id: number
  email: string
  full_name?: string
  is_active: boolean
  roles: string[]
  permissions: string[]
}

type AuthState = {
  user: AuthUser | null
  isLoading: boolean
  error: string | null
  hasPermission: (perm: string) => boolean
  hasAnyPermission: (perms: string[]) => boolean
}

const AuthContext = createContext<AuthState | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const tenant = localStorage.getItem('tenant')
    if (!token || !tenant) {
      setUser(null)
      return
    }
    let mounted = true
    const load = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const res = await api.get('/auth/me')
        if (!mounted) return
        setUser(res.data)
      } catch (e: any) {
        if (!mounted) return
        
        // Check if it's a session expiry or authentication error
        const errorDetail = e?.response?.data?.detail || 'Failed to load user'
        if (errorDetail.includes('Session expired') || 
            errorDetail.includes('Invalid token') || 
            e?.response?.status === 401) {
          // Clear auth and redirect to login
          localStorage.removeItem('token')
          setUser(null)
          window.location.href = '/login'
          return
        }
        
        // For other errors, just set the error but don't clear user
        setError(errorDetail)
      } finally {
        if (mounted) setIsLoading(false)
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [])

  // Idle logout after 20 minutes of inactivity
  useEffect(() => {
    const IDLE_MINUTES = Number(import.meta.env.VITE_SESSION_IDLE_MINUTES || 20)
    const IDLE_MS = IDLE_MINUTES * 60 * 1000
    let timer: number | undefined

    const clearAuth = () => {
      localStorage.removeItem('token')
      setUser(null)
      window.location.href = '/login'
    }

    const reset = () => {
      if (timer) window.clearTimeout(timer)
      timer = window.setTimeout(clearAuth, IDLE_MS)
    }

    const events = ['mousemove', 'keydown', 'scroll', 'click', 'touchstart', 'visibilitychange']
    events.forEach((evt) => window.addEventListener(evt, reset, { passive: true }))
    reset()
    return () => {
      if (timer) window.clearTimeout(timer)
      events.forEach((evt) => window.removeEventListener(evt, reset))
    }
  }, [])

  const hasPermission = (perm: string) => {
    if (!user) return false
    return user.permissions?.includes(perm)
  }

  const hasAnyPermission = (perms: string[]) => {
    if (!user) return false
    return perms.some((p) => user.permissions?.includes(p))
  }

  const value = useMemo<AuthState>(() => ({
    user,
    isLoading,
    error,
    hasPermission,
    hasAnyPermission
  }), [user, isLoading, error])

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}


