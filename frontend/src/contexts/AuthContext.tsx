import { createContext, useContext, useEffect, type ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import type { User } from '@/types/auth'
import { useAuthService } from '@/hooks/useAuthService'
import { onSessionExpired } from '@/lib/authEvents'
import { logger } from '@/lib/logger'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<User>
  logout: () => Promise<void>
  updateUser: (user: User) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const auth = useAuthService()
  const navigate = useNavigate()
  const location = useLocation()

  // Subscribe to session expired events and redirect to login
  useEffect(() => {
    // Skip if already on login page
    if (location.pathname === '/login') {
      return
    }

    return onSessionExpired(() => {
      logger.info('Session expired, redirecting to login')
      // Clear user state (auth service will handle API logout)
      auth.logout().catch(() => {
        // Ignore logout errors during session expiration
      })
      // Redirect to login with expired flag
      navigate('/login?expired=true', { replace: true })
    })
  }, [auth, navigate, location.pathname])

  const value: AuthContextType = auth

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
