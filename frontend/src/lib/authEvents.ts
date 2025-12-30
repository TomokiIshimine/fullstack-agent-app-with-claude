/**
 * Authentication event system for global auth state changes
 *
 * Provides a simple event-based mechanism for handling authentication
 * events across the application without tight coupling between components.
 */

/**
 * Authentication event types
 */
export const AUTH_EVENTS = {
  /** Fired when a 401 response indicates session has expired */
  SESSION_EXPIRED: 'auth:session-expired',
} as const

/**
 * Emit a session expired event to notify listeners that the user's
 * session has expired and they need to re-authenticate.
 *
 * This is typically called from the API client when a 401 response
 * is received.
 *
 * @example
 * ```typescript
 * // In API client
 * if (response.status === 401) {
 *   emitSessionExpired()
 * }
 * ```
 */
export function emitSessionExpired(): void {
  window.dispatchEvent(new CustomEvent(AUTH_EVENTS.SESSION_EXPIRED))
}

/**
 * Subscribe to session expired events.
 *
 * Returns a cleanup function that should be called when the
 * subscriber is unmounted.
 *
 * @param callback - Function to call when session expires
 * @returns Cleanup function to unsubscribe
 *
 * @example
 * ```typescript
 * // In AuthContext
 * useEffect(() => {
 *   return onSessionExpired(() => {
 *     logout()
 *     navigate('/login?expired=true')
 *   })
 * }, [logout, navigate])
 * ```
 */
export function onSessionExpired(callback: () => void): () => void {
  const handler = () => callback()
  window.addEventListener(AUTH_EVENTS.SESSION_EXPIRED, handler)
  return () => window.removeEventListener(AUTH_EVENTS.SESSION_EXPIRED, handler)
}
