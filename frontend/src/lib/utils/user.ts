import type { User } from '@/types/auth'

/**
 * Get display name for a user
 * Returns name if available, otherwise email
 *
 * @param user - User object
 * @returns Display name string
 */
export const getDisplayName = (user: User): string => {
  return user.name || user.email
}

/**
 * Get avatar letter for a user
 * Returns first character of name or email, uppercased
 *
 * @param user - User object
 * @returns Single uppercase letter for avatar
 */
export const getAvatarLetter = (user: User): string => {
  return (user.name?.[0] || user.email[0] || 'U').toUpperCase()
}
