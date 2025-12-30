/**
 * Internal helper to get the role-based path
 * - Admin users: /admin/users
 * - Regular users: /chat
 */
const getRoleBasedPath = (role: string | undefined): string => {
  if (role === 'admin') {
    return '/admin/users'
  }
  return '/chat'
}

/**
 * Get the default path for a user based on their role
 * Used for initial authentication redirects (after login, token refresh)
 *
 * @param role - User role ('admin' or 'user')
 * @returns The default path for the user role
 */
export const getDefaultPathForRole = (role: string | undefined): string => {
  return getRoleBasedPath(role)
}

/**
 * Get the home path for a user based on their role
 * Used for navigation links (brand/home link in navbar)
 *
 * @param role - User role ('admin' or 'user')
 * @returns The home path for the user role
 */
export const getHomePathForRole = (role: string | undefined): string => {
  return getRoleBasedPath(role)
}

/**
 * Check if a path is currently active
 * Handles special cases like /chat which should match /chat/:uuid
 *
 * @param currentPath - The current location pathname
 * @param targetPath - The path to check against
 * @returns True if the path is active
 */
export const isPathActive = (currentPath: string, targetPath: string): boolean => {
  if (targetPath === '/chat') {
    return currentPath === '/chat' || currentPath.startsWith('/chat/')
  }
  return currentPath === targetPath
}
