import { createContext, useContext, useState, useCallback } from 'react'
import { authService } from '../services/services'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('tl_user') || 'null') }
    catch { return null }
  })
  const [token, setToken] = useState(() => localStorage.getItem('tl_token') || null)

  const login = useCallback(async (email, password) => {
    const res = await authService.login(email, password)
    const { access_token, user: userData } = res.data
    localStorage.setItem('tl_token', access_token)
    localStorage.setItem('tl_user', JSON.stringify(userData))
    setToken(access_token)
    setUser(userData)
    return userData
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('tl_token')
    localStorage.removeItem('tl_user')
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
