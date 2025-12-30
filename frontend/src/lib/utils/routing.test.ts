import { describe, it, expect } from 'vitest'
import { getDefaultPathForRole, getHomePathForRole, isPathActive } from './routing'

describe('routing', () => {
  describe('getDefaultPathForRole', () => {
    it('returns /admin/users for admin role', () => {
      expect(getDefaultPathForRole('admin')).toBe('/admin/users')
    })

    it('returns /chat for user role', () => {
      expect(getDefaultPathForRole('user')).toBe('/chat')
    })

    it('returns /chat for undefined role', () => {
      expect(getDefaultPathForRole(undefined)).toBe('/chat')
    })

    it('returns /chat for unknown role', () => {
      expect(getDefaultPathForRole('unknown')).toBe('/chat')
    })
  })

  describe('getHomePathForRole', () => {
    it('returns /admin/users for admin role', () => {
      expect(getHomePathForRole('admin')).toBe('/admin/users')
    })

    it('returns /chat for user role', () => {
      expect(getHomePathForRole('user')).toBe('/chat')
    })

    it('returns /chat for undefined role', () => {
      expect(getHomePathForRole(undefined)).toBe('/chat')
    })

    it('returns /chat for unknown role', () => {
      expect(getHomePathForRole('unknown')).toBe('/chat')
    })
  })

  describe('isPathActive', () => {
    describe('chat path matching', () => {
      it('returns true when current path is exactly /chat', () => {
        expect(isPathActive('/chat', '/chat')).toBe(true)
      })

      it('returns true when current path starts with /chat/', () => {
        expect(isPathActive('/chat/123', '/chat')).toBe(true)
        expect(isPathActive('/chat/abc-def-ghi', '/chat')).toBe(true)
      })

      it('returns false when current path does not match /chat', () => {
        expect(isPathActive('/settings', '/chat')).toBe(false)
        expect(isPathActive('/chats', '/chat')).toBe(false)
        expect(isPathActive('/chat-history', '/chat')).toBe(false)
      })
    })

    describe('exact path matching', () => {
      it('returns true for exact match on non-chat paths', () => {
        expect(isPathActive('/settings', '/settings')).toBe(true)
        expect(isPathActive('/admin/users', '/admin/users')).toBe(true)
      })

      it('returns false for non-matching paths', () => {
        expect(isPathActive('/settings', '/admin/users')).toBe(false)
        expect(isPathActive('/admin/users', '/settings')).toBe(false)
      })

      it('returns false for partial matches on non-chat paths', () => {
        expect(isPathActive('/settings/profile', '/settings')).toBe(false)
        expect(isPathActive('/admin/users/123', '/admin/users')).toBe(false)
      })
    })
  })
})
